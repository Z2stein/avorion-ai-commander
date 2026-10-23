"""Passive, stdlib-only M1 file-IPC bridge scaffold.

The AC|1|... ASCII records and append-only paths are provisional. This program
does not load Avorion, install files, issue ship commands, or imply runtime proof.
It caps total records in each direction at the maximum normal 50-PROBE run
(one handshake record plus two records per cycle) plus up to five additional
records, for a maximum of 106 records per direction. The cap is aggregate and
does not track negative records separately. This bridge does not inject
malformed, duplicate, or replay cases; a separate injector and isolated
verification are still needed for the full M1 rejection criteria.
"""

from __future__ import annotations

import argparse
from collections import deque
import math
import os
import re
import secrets
import sys
import time
from pathlib import Path


PROTOCOL_TAG = "AC"
PROTOCOL_VERSION = "1"
MAX_RECORD_BYTES = 512
MAX_LOG_BYTES = 64 * 1024
MAX_PROBES = 50
MAX_NEGATIVE_RECORDS = 5
MAX_RECORDS_PER_DIRECTION = 2 * MAX_PROBES + 1 + MAX_NEGATIVE_RECORDS
MAX_SEQUENCE = MAX_PROBES
MIN_POLL_INTERVAL = 0.01
MAX_POLL_INTERVAL = 1.0
MIN_PROBE_INTERVAL = 0.1
MAX_PROBE_INTERVAL = 5.0
MIN_TIMEOUT = 0.1
MAX_TIMEOUT = 5.0
SESSION_RE = re.compile(r"^[0-9a-f]{32}$")
WIRE_DECIMAL_RE = re.compile(r"^-?[0-9]+(?:\.[0-9]+)?$")
ERROR_CODES = {
    "invalid_entity",
    "invalid_session",
    "malformed_record",
    "state_unavailable",
    "unexpected_sequence",
    "unknown_type",
}
INBOX_NAME = "mod-to-bridge.log"
OUTBOX_NAME = "bridge-to-mod.log"


class BridgeError(RuntimeError):
    """Raised for malformed or out-of-order provisional protocol records."""


def encode_record(record_type: str, *fields: object) -> bytes:
    values = [PROTOCOL_TAG, PROTOCOL_VERSION, record_type]
    values.extend(str(field) for field in fields)
    for value in values:
        if "|" in value or "\n" in value or "\r" in value or "\x00" in value:
            raise BridgeError("record field contains a reserved delimiter")
    try:
        record = ("|".join(values) + "\n").encode("ascii")
    except UnicodeEncodeError as exc:
        raise BridgeError("record is not ASCII") from exc
    if len(record) > MAX_RECORD_BYTES:
        raise BridgeError("record exceeds the provisional size limit")
    return record


def append_record(path: Path, record_type: str, *fields: object) -> None:
    # Append mode and flush/close visibility are assumptions pending isolated validation.
    payload = encode_record(record_type, *fields)
    current_size = path.stat().st_size if path.exists() else 0
    if current_size + len(payload) > MAX_LOG_BYTES:
        raise BridgeError("outbox byte limit reached; refusing further writes")
    with path.open("ab") as stream:
        stream.write(payload)
        stream.flush()


def read_complete_records(path: Path, offset: int) -> tuple[list[str], int]:
    """Read LF- or CRLF-terminated records, leaving an incomplete tail for the next poll."""
    try:
        with path.open("rb") as stream:
            stream.seek(offset)
            chunk = stream.read(MAX_LOG_BYTES + 1)
    except FileNotFoundError:
        return [], offset

    if offset + len(chunk) > MAX_LOG_BYTES:
        raise BridgeError("incoming log exceeds the provisional 64 KiB limit")

    last_newline = chunk.rfind(b"\n")
    if last_newline < 0:
        return [], offset

    complete_bytes = chunk[: last_newline + 1]
    lines = complete_bytes[:-1].split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    decoded: list[str] = []
    for line in lines:
        crlf_terminated = line.endswith(b"\r")
        if crlf_terminated:
            # One CR immediately before LF belongs to the separator. Any other
            # CR remains in the record and is rejected by parse_record().
            line = line[:-1]
        terminator_bytes = 2 if crlf_terminated else 1
        if len(line) + terminator_bytes > MAX_RECORD_BYTES:
            raise BridgeError("incoming record exceeds the provisional size limit")
        try:
            decoded.append(line.decode("ascii"))
        except UnicodeDecodeError as exc:
            raise BridgeError("incoming record is not ASCII") from exc
    return decoded, offset + len(complete_bytes)


def parse_record(line: str) -> tuple[str, list[str]]:
    if "\r" in line or "\x00" in line:
        raise BridgeError("CR and NUL are forbidden in records")
    fields = line.split("|")
    if len(fields) < 3 or fields[0] != PROTOCOL_TAG or fields[1] != PROTOCOL_VERSION:
        raise BridgeError("bad protocol tag, version, or field count")

    record_type = fields[2]
    expected_lengths = {
        "HELLO_ACK": 4,
        "STATE": 14,
        "ACKED": 5,
        "ERROR": 6,
    }
    expected_length = expected_lengths.get(record_type)
    if expected_length is None or len(fields) != expected_length:
        raise BridgeError(f"unexpected record type or field count: {record_type}")
    return record_type, fields


def parse_sequence(value: str) -> int:
    if not value.isascii() or not value.isdecimal():
        raise BridgeError("sequence is not a decimal integer")
    sequence = int(value)
    if not 1 <= sequence <= MAX_SEQUENCE:
        raise BridgeError("sequence is outside the provisional range")
    return sequence


def parse_state(fields: list[str], session: str, sequence: int) -> dict[str, str | float | bool | int]:
    if fields[3] != session or parse_sequence(fields[4]) != sequence:
        raise BridgeError("STATE does not match the outstanding probe")

    ship_id = fields[5]
    if not ship_id or len(ship_id) > 128 or any(ord(char) < 0x21 or ord(char) > 0x7E for char in ship_id):
        raise BridgeError("ship_id is empty or not a printable ASCII token")

    if fields[10] not in {"0", "1"}:
        raise BridgeError("shield_active must be 0 or 1")

    numeric_values: list[float] = []
    for value in fields[6:10] + fields[11:14]:
        if not WIRE_DECIMAL_RE.fullmatch(value):
            raise BridgeError("STATE contains a value outside the finite ASCII-decimal grammar")
        try:
            number = float(value)
        except ValueError as exc:
            raise BridgeError("STATE contains a non-numeric field") from exc
        if not math.isfinite(number):
            raise BridgeError("STATE contains a non-finite number")
        numeric_values.append(number)

    if any(value < 0 for value in numeric_values[:4]):
        raise BridgeError("durability and shield values must be nonnegative")

    return {
        "sequence": sequence,
        "ship_id": ship_id,
        "durability": numeric_values[0],
        "max_durability": numeric_values[1],
        "shield_durability": numeric_values[2],
        "shield_max_durability": numeric_values[3],
        "shield_active": fields[10] == "1",
        "x": numeric_values[4],
        "y": numeric_values[5],
        "z": numeric_values[6],
    }


class FileBridge:
    def __init__(
        self,
        directory: Path,
        expected_ship_id: str,
        poll_interval: float,
        timeout: float,
        resume_after_hello: bool = False,
    ) -> None:
        self.directory = directory
        self.inbox = directory / INBOX_NAME
        self.outbox = directory / OUTBOX_NAME
        self.expected_ship_id = expected_ship_id
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.session = ""
        self.inbox_offset = 0
        self.inbox_record_count = 0
        self.outbox_record_count = 0
        self.pending_records: deque[str] = deque()
        self._resume_snapshot: tuple[bytes, bytes] | None = None

        if resume_after_hello:
            self._resume_exact_hello_handshake()
        else:
            self.session = secrets.token_hex(16)
            # Reusing append-only logs would replay stale sessions. Never clear or rotate them.
            for path in (self.inbox, self.outbox):
                if path.exists() and path.stat().st_size != 0:
                    raise BridgeError(
                        f"{path.name} is non-empty; use fresh empty files in the approved isolated test directory"
                    )

    def _resume_exact_hello_handshake(self) -> None:
        """Resume only the exact one-record HELLO/matching HELLO_ACK state.

        Repeated snapshots detect ordinary changes; they do not lock out a
        concurrent writer. Resume requires an exclusive bridge writer.
        """
        first_snapshot = (
            self._read_stable_file(self.outbox),
            self._read_stable_file(self.inbox),
        )
        second_snapshot = (
            self._read_stable_file(self.outbox),
            self._read_stable_file(self.inbox),
        )
        if first_snapshot != second_snapshot:
            raise BridgeError("IPC files changed while checking resume preconditions")
        outbox_bytes, inbox_bytes = second_snapshot

        hello_match = re.fullmatch(rb"AC\|1\|HELLO\|([0-9a-f]{32})\n", outbox_bytes)
        if hello_match is None:
            raise BridgeError("resume requires bridge-to-mod.log to contain exactly one LF HELLO record")

        session_bytes = hello_match.group(1)
        expected_ack_lf = b"AC|1|HELLO_ACK|" + session_bytes + b"\n"
        expected_ack_crlf = b"AC|1|HELLO_ACK|" + session_bytes + b"\r\n"
        if inbox_bytes not in {expected_ack_lf, expected_ack_crlf}:
            raise BridgeError("resume requires exactly one matching HELLO_ACK and no other inbox bytes")

        self.session = session_bytes.decode("ascii")
        self.inbox_offset = len(inbox_bytes)
        self.inbox_record_count = 1
        self.outbox_record_count = 1
        self._resume_snapshot = second_snapshot

    @staticmethod
    def _read_stable_file(path: Path) -> bytes:
        try:
            with path.open("rb") as stream:
                size_before = os.fstat(stream.fileno()).st_size
                if size_before > MAX_LOG_BYTES:
                    raise BridgeError("IPC file exceeds the provisional 64 KiB limit")
                contents = stream.read(MAX_LOG_BYTES + 1)
                size_after = os.fstat(stream.fileno()).st_size
        except FileNotFoundError as exc:
            raise BridgeError("resume requires one existing HELLO and HELLO_ACK record") from exc
        if size_before != size_after or len(contents) != size_after:
            raise BridgeError("IPC file changed while checking resume preconditions")
        return contents

    def _verify_resume_snapshot(self) -> None:
        # This is a final change check, not a lock against concurrent writers.
        if self._resume_snapshot is None:
            return
        current_snapshot = (
            self._read_stable_file(self.outbox),
            self._read_stable_file(self.inbox),
        )
        if current_snapshot != self._resume_snapshot:
            raise BridgeError("IPC files changed after resume preflight; refusing to append PROBE")

    def append(self, record_type: str, *fields: object) -> None:
        if self.outbox_record_count >= MAX_RECORDS_PER_DIRECTION:
            raise BridgeError("outbox record limit reached; refusing further writes")
        append_record(self.outbox, record_type, *fields)
        self.outbox_record_count += 1

    def wait_for(
        self,
        expected_type: str,
        sequence: int | None = None,
        deadline: float | None = None,
    ) -> list[str]:
        if deadline is None:
            deadline = time.monotonic() + self.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break

            if not self.pending_records:
                lines, self.inbox_offset = read_complete_records(self.inbox, self.inbox_offset)
                self.inbox_record_count += len(lines)
                if self.inbox_record_count > MAX_RECORDS_PER_DIRECTION:
                    raise BridgeError("inbox record limit reached; refusing further reads")
                self.pending_records.extend(lines)

            if not self.pending_records:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                time.sleep(min(self.poll_interval, remaining))
                continue

            line = self.pending_records.popleft()
            if time.monotonic() >= deadline:
                self.pending_records.appendleft(line)
                break

            record_type, fields = parse_record(line)
            if fields[3] != self.session:
                raise BridgeError("peer returned a record for a foreign session")
            if record_type == "ERROR":
                if fields[5] not in ERROR_CODES:
                    raise BridgeError("peer sent an unknown ERROR enum")
                raise BridgeError(f"peer rejected probe ({fields[5]})")
            if record_type != expected_type:
                raise BridgeError(f"expected {expected_type}, received {record_type}")
            if expected_type in {"ACKED", "STATE"} and parse_sequence(fields[4]) != sequence:
                raise BridgeError("response sequence does not match the outstanding probe")
            return fields
        raise BridgeError(f"timeout waiting for {expected_type}")

    def ensure_no_trailing_records(self) -> None:
        """Fail on extra data already buffered or visible at the final read boundary."""
        if self.pending_records:
            raise BridgeError("unexpected trailing record after final ACKED")

        lines, self.inbox_offset = read_complete_records(self.inbox, self.inbox_offset)
        self.inbox_record_count += len(lines)
        if self.inbox_record_count > MAX_RECORDS_PER_DIRECTION:
            raise BridgeError("inbox record limit reached after final ACKED")
        if lines:
            raise BridgeError("unexpected trailing record after final ACKED")

        # A non-LF-terminated tail is not a record yet, but fail closed at end of run.
        if self.inbox.exists() and self.inbox.stat().st_size > self.inbox_offset:
            raise BridgeError("incomplete trailing data after final ACKED")

    def run(self, cycles: int, probe_interval: float) -> None:
        if self.outbox_record_count == 0:
            self.append("HELLO", self.session)
            self.wait_for("HELLO_ACK")
            print(f"HELLO_ACK session={self.session}")
        else:
            self._verify_resume_snapshot()
            print(f"resuming after HELLO_ACK session={self.session}")

        for sequence in range(1, cycles + 1):
            started_at = time.monotonic()
            probe_deadline = started_at + self.timeout
            # One deadline covers PROBE append, STATE, validation, ACK, and ACKED.
            self.append("PROBE", self.session, sequence)
            state_fields = self.wait_for("STATE", sequence, deadline=probe_deadline)
            state = parse_state(state_fields, self.session, sequence)
            if state["ship_id"] != self.expected_ship_id:
                raise BridgeError("STATE ship_id does not match --expected-ship-id")
            if time.monotonic() >= probe_deadline:
                raise BridgeError("probe roundtrip deadline expired before ACK")
            self.append("ACK", self.session, sequence)
            self.wait_for("ACKED", sequence, deadline=probe_deadline)
            if time.monotonic() > probe_deadline:
                raise BridgeError("probe roundtrip exceeded the shared deadline")
            print(
                "STATE "
                f"seq={sequence} ship_id={state['ship_id']} "
                f"durability={state['durability']}/{state['max_durability']} "
                f"shield={state['shield_durability']}/{state['shield_max_durability']} "
                f"active={int(bool(state['shield_active']))} "
                f"translation=({state['x']},{state['y']},{state['z']}) ACKED"
            )

            # The 1 Hz cadence is a proposed value, not a measured requirement.
            delay = probe_interval - (time.monotonic() - started_at)
            if sequence < cycles and delay > 0:
                time.sleep(delay)

        # This catches duplicates/foreign records already visible in the final read.
        self.ensure_no_trailing_records()


def bounded_float(value: str, minimum: float, maximum: float, label: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{label} must be a number") from exc
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise argparse.ArgumentTypeError(f"{label} must be between {minimum} and {maximum}")
    return number


def probe_interval_value(value: str) -> float:
    return bounded_float(value, MIN_PROBE_INTERVAL, MAX_PROBE_INTERVAL, "probe interval")


def poll_interval_value(value: str) -> float:
    return bounded_float(value, MIN_POLL_INTERVAL, MAX_POLL_INTERVAL, "poll interval")


def timeout_value(value: str) -> float:
    return bounded_float(value, MIN_TIMEOUT, MAX_TIMEOUT, "timeout")


def positive_int(value: str) -> int:
    number = int(value)
    if not 1 <= number <= MAX_PROBES:
        raise argparse.ArgumentTypeError(f"must be between 1 and {MAX_SEQUENCE}")
    return number


def printable_ascii_token(value: str) -> str:
    if (
        not 1 <= len(value) <= 128
        or "|" in value
        or any(ord(char) < 0x21 or ord(char) > 0x7E for char in value)
    ):
        raise argparse.ArgumentTypeError(
            "ship ID must be a 1-128 character printable ASCII token without '|'"
        )
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the passive Avorion M1 file probe scaffold.")
    parser.add_argument(
        "--moddata-dir",
        required=True,
        type=Path,
        help="explicit, pre-existing IPC directory with absent/empty channel files; never created or cleared",
    )
    parser.add_argument(
        "--expected-ship-id",
        required=True,
        type=printable_ascii_token,
        help="ship ID independently verified by the caller; STATE must match before ACK",
    )
    parser.add_argument("--cycles", type=positive_int, default=50)
    parser.add_argument("--probe-interval", type=probe_interval_value, default=1.0)
    parser.add_argument("--poll-interval", type=poll_interval_value, default=0.1)
    parser.add_argument("--timeout", type=timeout_value, default=5.0)
    parser.add_argument(
        "--resume-after-hello",
        action="store_true",
        help="resume only from exactly one LF HELLO and its matching LF/CRLF HELLO_ACK; never clears files",
    )
    args = parser.parse_args(argv)
    if args.poll_interval > args.timeout:
        parser.error("--poll-interval must not exceed --timeout")

    directory = args.moddata_dir.expanduser().resolve()
    if not directory.is_dir():
        parser.error("--moddata-dir must name an existing directory")

    try:
        FileBridge(
            directory,
            args.expected_ship_id,
            args.poll_interval,
            args.timeout,
            resume_after_hello=args.resume_after_hello,
        ).run(args.cycles, args.probe_interval)
    except (BridgeError, OSError) as exc:
        print(f"bridge stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
