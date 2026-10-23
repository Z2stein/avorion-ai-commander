"""Offline AC|1 bridge tests using a fault-injecting file peer.

These tests launch only the Python bridge and a local fake peer. All channel
files live in a temporary directory; Avorion and its save data are untouched.
They verify Python-side behavior only, not the Lua mod or Avorion file I/O.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "bridge" / "probe_bridge.py"
SHIP_ID = "offline-test-ship"
SHARED_DEADLINE_TIMEOUT = 1.5
SHARED_DEADLINE_STAGE_DELAY = 1.0


def alternate_session(session: str) -> str:
    first = "0" if session[0] != "0" else "1"
    return first + session[1:]


class ScriptedFilePeer:
    """Fake Mod peer that can inject malformed, duplicate, and replay records."""

    def __init__(self, directory: Path, scenario: str) -> None:
        self.inbox = directory / "mod-to-bridge.log"
        self.outbox = directory / "bridge-to-mod.log"
        self.scenario = scenario
        self.stop_event = threading.Event()
        self.failure: BaseException | None = None
        self.thread = threading.Thread(target=self._run, name="ac1-fake-peer", daemon=True)

    def __enter__(self) -> ScriptedFilePeer:
        self.thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.stop_event.set()
        self.thread.join(timeout=1.0)

    def _write(self, records: list[bytes]) -> None:
        with self.inbox.open("ab") as stream:
            for record in records:
                stream.write(record)
            stream.flush()

    @staticmethod
    def _record(record_type: str, *fields: object) -> bytes:
        return ("|".join(["AC", "1", record_type, *(str(field) for field in fields)]) + "\n").encode("ascii")

    def _state(self, session: str, sequence: str) -> bytes:
        if self.scenario == "foreign-state-session":
            session = alternate_session(session)
        ship_id = "different-ship" if self.scenario == "wrong-ship-id" else SHIP_ID
        durability = "NaN" if self.scenario == "nonfinite-state" else "100"
        return self._record(
            "STATE",
            session,
            sequence,
            ship_id,
            durability,
            "100",
            "25",
            "50",
            "1",
            "-1.5",
            "0",
            "2.25",
        )

    def _handle(self, line: bytes) -> None:
        fields = line.decode("ascii").split("|")
        record_type = fields[2] if len(fields) > 2 else ""
        if record_type == "HELLO":
            session = fields[3]
            if self.scenario == "timeout-hello":
                return
            if self.scenario == "malformed-hello":
                self._write([self._record("HELLO_ACK", session, "unexpected")])
                return
            if self.scenario == "foreign-hello-session":
                session = alternate_session(session)
            self._write([self._record("HELLO_ACK", session)])
            return

        if record_type == "PROBE":
            session, sequence = fields[3], fields[4]
            if self.scenario == "timeout-state":
                return
            if self.scenario == "shared-roundtrip-deadline":
                time.sleep(SHARED_DEADLINE_STAGE_DELAY)
            if self.scenario == "malformed-record":
                self._write([b"not-an-AC-record\n"])
                return
            state = self._state(session, sequence)
            records = [state, state] if self.scenario == "duplicate-state" else [state]
            self._write(records)
            return

        if record_type == "ACK":
            session, sequence = fields[3], fields[4]
            if self.scenario == "shared-roundtrip-deadline":
                time.sleep(SHARED_DEADLINE_STAGE_DELAY)
            if self.scenario == "replayed-acked-sequence" and sequence != "1":
                sequence = "1"
            acked = self._record("ACKED", session, sequence)
            records = [acked, acked] if self.scenario == "duplicate-acked" else [acked]
            self._write(records)

    def _run(self) -> None:
        offset = 0
        partial = b""
        try:
            while not self.stop_event.is_set():
                if self.outbox.exists():
                    with self.outbox.open("rb") as stream:
                        stream.seek(offset)
                        chunk = stream.read()
                    offset += len(chunk)
                    partial += chunk
                    while b"\n" in partial:
                        line, partial = partial.split(b"\n", 1)
                        self._handle(line)
                self.stop_event.wait(0.005)
        except BaseException as exc:  # surfaced to the test thread after the child exits
            self.failure = exc


class ProbeBridgeOfflineTests(unittest.TestCase):
    def run_bridge(
        self, scenario: str, *, cycles: int = 1, timeout: float = 0.5
    ) -> tuple[subprocess.CompletedProcess[str], str]:
        with tempfile.TemporaryDirectory(prefix="ac1-offline-") as temp:
            directory = Path(temp)
            peer = ScriptedFilePeer(directory, scenario)
            with peer:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(BRIDGE),
                        "--moddata-dir",
                        str(directory),
                        "--expected-ship-id",
                        SHIP_ID,
                        "--cycles",
                        str(cycles),
                        "--probe-interval",
                        "0.1",
                        "--poll-interval",
                        "0.01",
                        "--timeout",
                        str(timeout),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=3.0,
                    check=False,
                )
            if peer.failure is not None:
                raise AssertionError("fake file peer failed") from peer.failure
            outbound = (directory / "bridge-to-mod.log").read_text(encoding="ascii")
            return result, outbound

    def test_rejects_expected_ship_id_with_record_delimiter(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ac1-offline-") as temp:
            directory = Path(temp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(BRIDGE),
                    "--moddata-dir",
                    str(directory),
                    "--expected-ship-id",
                    "ship|id",
                    "--poll-interval",
                    "0.01",
                    "--timeout",
                    "0.1",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=3.0,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("printable ASCII token without '|'", result.stderr)

    def test_valid_two_cycle_handshake(self) -> None:
        result, outbound = self.run_bridge("valid", cycles=2)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("STATE seq=1 ship_id=offline-test-ship", result.stdout)
        self.assertIn("STATE seq=2 ship_id=offline-test-ship", result.stdout)
        self.assertEqual(outbound.count("|PROBE|"), 2)
        self.assertEqual(outbound.count("|ACK|"), 2)

    def test_rejects_foreign_hello_session(self) -> None:
        result, outbound = self.run_bridge("foreign-hello-session")
        self.assertEqual(result.returncode, 1)
        self.assertIn("foreign session", result.stderr)
        self.assertNotIn("|PROBE|", outbound)

    def test_rejects_foreign_state_session(self) -> None:
        result, outbound = self.run_bridge("foreign-state-session")
        self.assertEqual(result.returncode, 1)
        self.assertIn("foreign session", result.stderr)
        self.assertNotIn("|ACK|", outbound)

    def test_rejects_wrong_field_count(self) -> None:
        result, _ = self.run_bridge("malformed-hello")
        self.assertEqual(result.returncode, 1)
        self.assertIn("unexpected record type or field count", result.stderr)

    def test_rejects_malformed_record(self) -> None:
        result, _ = self.run_bridge("malformed-record")
        self.assertEqual(result.returncode, 1)
        self.assertIn("bad protocol tag", result.stderr)

    def test_rejects_duplicate_state_replay(self) -> None:
        result, _ = self.run_bridge("duplicate-state")
        self.assertEqual(result.returncode, 1)
        self.assertIn("expected ACKED, received STATE", result.stderr)

    def test_rejects_duplicate_trailing_acked(self) -> None:
        result, _ = self.run_bridge("duplicate-acked")
        self.assertEqual(result.returncode, 1)
        self.assertIn("unexpected trailing record", result.stderr)

    def test_rejects_old_sequence_replay(self) -> None:
        result, _ = self.run_bridge("replayed-acked-sequence", cycles=2)
        self.assertEqual(result.returncode, 1)
        self.assertIn("response sequence does not match", result.stderr)

    def test_checks_expected_ship_id_before_ack(self) -> None:
        result, outbound = self.run_bridge("wrong-ship-id")
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not match --expected-ship-id", result.stderr)
        self.assertNotIn("|ACK|", outbound)

    def test_rejects_nonfinite_state_number(self) -> None:
        result, _ = self.run_bridge("nonfinite-state")
        self.assertEqual(result.returncode, 1)
        self.assertIn("finite ASCII-decimal grammar", result.stderr)

    def test_fails_closed_when_hello_times_out(self) -> None:
        result, _ = self.run_bridge("timeout-hello")
        self.assertEqual(result.returncode, 1)
        self.assertIn("timeout waiting for HELLO_ACK", result.stderr)

    def test_fails_closed_when_state_times_out(self) -> None:
        result, outbound = self.run_bridge("timeout-state")
        self.assertEqual(result.returncode, 1)
        self.assertIn("timeout waiting for STATE", result.stderr)
        self.assertNotIn("|ACK|", outbound)

    def test_state_and_acked_share_one_roundtrip_deadline(self) -> None:
        result, outbound = self.run_bridge(
            "shared-roundtrip-deadline", timeout=SHARED_DEADLINE_TIMEOUT
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("timeout waiting for ACKED", result.stderr)
        self.assertIn("|ACK|", outbound)


if __name__ == "__main__":
    unittest.main()
