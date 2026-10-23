"""Inject a bounded AC|1 fault sequence into the Lua probe's file inbox.

This source-only tool does not start Avorion, create directories or channel files,
clear data, or issue game commands. Runtime behavior remains unverified.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
import math
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import time


PROTOCOL_TAG = "AC"
PROTOCOL_VERSION = "1"
INBOX_NAME = "bridge-to-mod.log"
OUTBOX_NAME = "mod-to-bridge.log"
MAX_RECORD_BYTES = 512
MAX_LOG_BYTES = 64 * 1024
MAX_PROBES = 50
MAX_NEGATIVE_RECORDS = 5
MAX_RECORDS_PER_DIRECTION = 1 + (2 * MAX_PROBES) + MAX_NEGATIVE_RECORDS
MIN_TIMEOUT = 0.1
MAX_TIMEOUT = 5.0
DEFAULT_MAX_RUNTIME = 600.0
MIN_MAX_RUNTIME = 1.0
MAX_MAX_RUNTIME = 900.0
MIN_POLL_INTERVAL = 0.01
MAX_POLL_INTERVAL = 1.0
TAIL_FINAL_READ_MARGIN = 0.01
SESSION_RE = re.compile(r"^[0-9a-f]{32}$")
DECIMAL_RE = re.compile(r"^-?[0-9]+(?:\.[0-9]+)?$")
RESPONSE_LENGTHS = {"HELLO_ACK": 4, "STATE": 14, "ACKED": 5, "ERROR": 6}


class InjectorError(RuntimeError):
    """Raised when a file, protocol, safety, or time limit is violated."""


@dataclass(frozen=True)
class NegativeCase:
    name: str
    sequence: str
    code: str
    record_factory: Callable[[], bytes]


def _is_junction(path: Path) -> bool:
    check = getattr(path, "is_junction", None)
    return bool(check()) if check is not None else False


def _reject_redirect_components(path: Path) -> None:
    if ".." in path.parts:
        raise InjectorError("path containing '..' is refused")

    current = Path(path.anchor)
    for part in path.parts[1:]:
        if part in {"", "."}:
            continue
        current = current / part
        if current.is_symlink() or _is_junction(current):
            raise InjectorError("symbolic links and junctions are refused in the selected path")


def resolve_moddata_dir(value: str) -> tuple[Path, tuple[int, int]]:
    requested = Path(value).expanduser()
    if not requested.is_absolute():
        requested = Path.cwd() / requested
    requested = Path(os.path.abspath(requested))
    _reject_redirect_components(requested)

    try:
        directory = requested.resolve(strict=True)
        directory_stat = directory.stat(follow_symlinks=False)
    except OSError as exc:
        raise InjectorError("--moddata-dir must be an existing accessible directory") from exc

    if not stat.S_ISDIR(directory_stat.st_mode) or directory != requested:
        raise InjectorError("--moddata-dir must be a real directory without path redirects")

    identity = (directory_stat.st_dev, directory_stat.st_ino)
    return directory, identity


def _check_directory(directory: Path, identity: tuple[int, int]) -> None:
    _reject_redirect_components(directory)
    try:
        resolved = directory.resolve(strict=True)
        current = directory.stat(follow_symlinks=False)
    except OSError as exc:
        raise InjectorError("selected moddata directory disappeared or became inaccessible") from exc

    if resolved != directory or not stat.S_ISDIR(current.st_mode):
        raise InjectorError("selected moddata directory changed or became a path redirect")
    if (current.st_dev, current.st_ino) != identity:
        raise InjectorError("selected moddata directory identity changed")


def _channel_stat(
    directory: Path,
    directory_identity: tuple[int, int],
    path: Path,
    expected_identity: tuple[int, int] | None = None,
) -> os.stat_result:
    _check_directory(directory, directory_identity)
    if path.parent != directory:
        raise InjectorError("channel path escaped the selected moddata directory")

    try:
        if path.is_symlink() or _is_junction(path):
            raise InjectorError("channel symlinks and junctions are refused")
        resolved = path.resolve(strict=True)
        channel_stat = path.stat(follow_symlinks=False)
    except FileNotFoundError as exc:
        raise InjectorError(f"required channel file is missing: {path.name}") from exc
    except OSError as exc:
        raise InjectorError(f"cannot inspect channel file: {path.name}") from exc

    if resolved != path or resolved.parent != directory:
        raise InjectorError("channel file resolves outside the selected moddata directory")
    if not stat.S_ISREG(channel_stat.st_mode) or channel_stat.st_nlink != 1:
        raise InjectorError("channel files must be regular, non-hard-linked files")
    identity = (channel_stat.st_dev, channel_stat.st_ino)
    if expected_identity is not None and identity != expected_identity:
        raise InjectorError(f"channel file identity changed: {path.name}")
    return channel_stat


def _open_verified(
    directory: Path,
    directory_identity: tuple[int, int],
    path: Path,
    expected_identity: tuple[int, int],
    mode: str,
):
    before = _channel_stat(directory, directory_identity, path, expected_identity)
    flags = os.O_RDONLY if mode == "rb" else os.O_RDWR
    flags |= getattr(os, "O_BINARY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise InjectorError(f"cannot open existing channel file: {path.name}") from exc

    try:
        opened = os.fstat(descriptor)
        after_path = path.stat(follow_symlinks=False)
        opened_identity = (opened.st_dev, opened.st_ino)
        before_identity = (before.st_dev, before.st_ino)
        after_identity = (after_path.st_dev, after_path.st_ino)
        if (
            opened_identity != expected_identity
            or before_identity != expected_identity
            or after_identity != expected_identity
            or not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
        ):
            raise InjectorError(f"channel file changed while opening: {path.name}")
        return os.fdopen(descriptor, mode)
    except BaseException:
        os.close(descriptor)
        raise


def encode_record(record_type: str, *fields: object) -> bytes:
    values = [PROTOCOL_TAG, PROTOCOL_VERSION, record_type]
    values.extend(str(field) for field in fields)
    for value in values:
        if "|" in value or "\n" in value or "\r" in value or "\x00" in value:
            raise InjectorError("attempted to encode a reserved record delimiter")
    try:
        record = ("|".join(values) + "\n").encode("ascii")
    except UnicodeEncodeError as exc:
        raise InjectorError("record contains non-ASCII text") from exc
    if len(record) > MAX_RECORD_BYTES:
        raise InjectorError("record exceeds the 512-byte limit")
    return record


class Channels:
    """Use only the two existing files directly inside the selected directory."""

    def __init__(self, directory: Path, directory_identity: tuple[int, int]) -> None:
        self.directory = directory
        self.directory_identity = directory_identity
        self.inbox = directory / INBOX_NAME
        self.outbox = directory / OUTBOX_NAME

        inbox_stat = _channel_stat(directory, directory_identity, self.inbox)
        outbox_stat = _channel_stat(directory, directory_identity, self.outbox)
        if inbox_stat.st_size != 0 or outbox_stat.st_size != 0:
            raise InjectorError("both existing channel files must be empty; no file is cleared")

        self.inbox_identity = (inbox_stat.st_dev, inbox_stat.st_ino)
        self.outbox_identity = (outbox_stat.st_dev, outbox_stat.st_ino)
        self.inbox_contents = b""
        self.inbox_record_count = 0
        self.outbox_seen = b""
        self.outbox_tail = bytearray()
        self.outbox_record_count = 0

    def append_inbox_record(self, record: bytes) -> None:
        if (
            not record.endswith(b"\n")
            or record.count(b"\n") != 1
            or len(record) > MAX_RECORD_BYTES
            or not record.isascii()
            or b"\r" in record
            or b"\x00" in record
        ):
            raise InjectorError("refusing an incomplete or oversized input record")
        if self.inbox_contents and not self.inbox_contents.endswith(b"\n"):
            raise InjectorError("cannot append a complete record while an input tail is open")
        self._append_inbox_bytes(record, completed_records=1)

    def append_inbox_fragment(self, fragment: bytes) -> None:
        """Append one bounded ASCII fragment without LF for the M1 tail probe."""
        if (
            not fragment
            or not fragment.isascii()
            or b"\n" in fragment
            or b"\r" in fragment
            or b"\x00" in fragment
        ):
            raise InjectorError("refusing an invalid or empty incomplete input fragment")
        if self.inbox_contents and not self.inbox_contents.endswith(b"\n"):
            raise InjectorError("only one incomplete input fragment may be open")
        if len(fragment) + 1 > MAX_RECORD_BYTES:
            raise InjectorError("incomplete input tail exceeds the record limit")
        self._append_inbox_bytes(fragment, completed_records=0)

    def finish_inbox_fragment(self) -> None:
        """Append LF to the one open fragment, completing exactly one record."""
        if not self.inbox_contents or self.inbox_contents.endswith(b"\n"):
            raise InjectorError("there is no incomplete input fragment to finish")
        if self.inbox_record_count >= MAX_RECORDS_PER_DIRECTION:
            raise InjectorError("inbox record limit reached")
        self._append_inbox_bytes(b"\n", completed_records=1)

    def _append_inbox_bytes(self, data: bytes, *, completed_records: int) -> None:
        if self.inbox_record_count + completed_records > MAX_RECORDS_PER_DIRECTION:
            raise InjectorError("inbox record limit reached")
        if len(self.inbox_contents) + len(data) > MAX_LOG_BYTES:
            raise InjectorError("inbox byte limit reached")
        with _open_verified(
            self.directory,
            self.directory_identity,
            self.inbox,
            self.inbox_identity,
            "r+b",
        ) as stream:
            current = stream.read(MAX_LOG_BYTES + 1)
            if current != self.inbox_contents:
                raise InjectorError("inbox changed outside this injector; refusing to append")
            stream.seek(0, os.SEEK_END)
            written = stream.write(data)
            if written != len(data):
                raise InjectorError("short inbox write; partial data is preserved for review")
            stream.flush()

        self.inbox_contents += data
        self.inbox_record_count += completed_records

    def read_outbox_records(self) -> list[str]:
        with _open_verified(
            self.directory,
            self.directory_identity,
            self.outbox,
            self.outbox_identity,
            "rb",
        ) as stream:
            contents = stream.read(MAX_LOG_BYTES + 1)

        if len(contents) > MAX_LOG_BYTES:
            raise InjectorError("outbox byte limit reached")
        if len(contents) < len(self.outbox_seen) or not contents.startswith(self.outbox_seen):
            raise InjectorError("outbox was truncated or changed; refusing to continue")

        newly_read = contents[len(self.outbox_seen) :]
        self.outbox_seen = contents
        self.outbox_tail.extend(newly_read)
        records: list[str] = []

        while True:
            newline = self.outbox_tail.find(b"\n")
            if newline < 0:
                break
            raw = bytes(self.outbox_tail[:newline])
            del self.outbox_tail[: newline + 1]
            crlf_terminated = raw.endswith(b"\r")
            if crlf_terminated:
                line_bytes = raw[:-1]
                terminator_bytes = 2
            else:
                line_bytes = raw
                terminator_bytes = 1
            if len(line_bytes) + terminator_bytes > MAX_RECORD_BYTES:
                raise InjectorError("outbox record exceeds the 512-byte limit")
            if b"\r" in line_bytes or b"\x00" in line_bytes:
                raise InjectorError("outbox contains CR or NUL")
            try:
                line = line_bytes.decode("ascii")
            except UnicodeDecodeError as exc:
                raise InjectorError("outbox contains non-ASCII bytes") from exc
            self.outbox_record_count += 1
            if self.outbox_record_count > MAX_RECORDS_PER_DIRECTION:
                raise InjectorError("outbox record limit reached")
            records.append(line)

        if len(self.outbox_tail) + 1 > MAX_RECORD_BYTES:
            raise InjectorError("incomplete outbox tail exceeds the record limit")
        return records

    def ensure_no_unexpected_output(self) -> None:
        records = self.read_outbox_records()
        if records or self.outbox_tail:
            raise InjectorError("unexpected or incomplete extra outbox record")


class LuaProtocolInjector:
    def __init__(
        self,
        channels: Channels,
        expected_ship_id: str,
        timeout: float,
        poll_interval: float,
        max_runtime: float = DEFAULT_MAX_RUNTIME,
    ) -> None:
        self.channels = channels
        self.expected_ship_id = expected_ship_id
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_runtime = max_runtime
        self.run_deadline: float | None = None
        self.session = secrets.token_hex(16)

    def _check_run_deadline(self, context: str = "") -> float:
        if self.run_deadline is None:
            raise InjectorError("run deadline has not been started")
        remaining = self.run_deadline - time.monotonic()
        if remaining <= 0:
            suffix = f" {context}" if context else ""
            raise InjectorError(f"total run deadline expired{suffix}")
        return remaining

    def _append_inbox_record(self, record: bytes) -> None:
        self._check_run_deadline("before inbox append")
        self.channels.append_inbox_record(record)
        self._check_run_deadline("during inbox append")

    def _append_inbox_fragment(self, fragment: bytes) -> None:
        self._check_run_deadline("before inbox append")
        self.channels.append_inbox_fragment(fragment)
        self._check_run_deadline("during inbox append")

    def _finish_inbox_fragment(self) -> None:
        self._check_run_deadline("before inbox append")
        self.channels.finish_inbox_fragment()
        self._check_run_deadline("during inbox append")

    def _ensure_no_unexpected_output(self) -> None:
        self._check_run_deadline("before outbox read")
        self.channels.ensure_no_unexpected_output()
        self._check_run_deadline("during outbox read")

    def _receive(self, expected_type: str) -> list[str]:
        wait_deadline = time.monotonic() + self.timeout
        if self.run_deadline is None:
            raise InjectorError("run deadline has not been started")
        deadline = min(wait_deadline, self.run_deadline)
        while True:
            now = time.monotonic()
            if now >= self.run_deadline:
                self._check_run_deadline(f"while waiting for {expected_type}")
            if now >= wait_deadline:
                raise InjectorError(f"timeout waiting for {expected_type}")
            records = self.channels.read_outbox_records()
            now = time.monotonic()
            if now >= self.run_deadline:
                self._check_run_deadline(f"while waiting for {expected_type}")
            if now >= wait_deadline:
                raise InjectorError(f"timeout waiting for {expected_type}")
            if records:
                if len(records) != 1 or self.channels.outbox_tail:
                    raise InjectorError("unexpected additional or partial outbox record")
                fields = self._parse_response(records[0])
                if fields[2] != expected_type:
                    if fields[2] == "ERROR":
                        raise InjectorError("Lua returned an unexpected ERROR record")
                    raise InjectorError(f"expected {expected_type}, received {fields[2]}")
                return fields
            remaining = deadline - now
            if remaining <= 0:
                if deadline >= self.run_deadline:
                    self._check_run_deadline(f"while waiting for {expected_type}")
                raise InjectorError(f"timeout waiting for {expected_type}")
            time.sleep(min(self.poll_interval, remaining))

    def _expect_no_output(self) -> None:
        """Poll for silence and complete a final read before the per-wait boundary."""
        wait_deadline = time.monotonic() + self.timeout
        if self.run_deadline is None:
            raise InjectorError("run deadline has not been started")
        deadline = min(wait_deadline, self.run_deadline)
        run_deadline_limits_window = self.run_deadline <= wait_deadline
        while True:
            now = time.monotonic()
            if now >= self.run_deadline:
                self._check_run_deadline("during tail silence window")
            if now >= wait_deadline:
                raise InjectorError("timeout during tail silence window")
            self._require_no_output_before_tail_completion()
            now = time.monotonic()
            if now >= self.run_deadline:
                self._check_run_deadline("during tail silence window")
            if now > wait_deadline:
                raise InjectorError("timeout during tail silence window")
            remaining = deadline - now

            final_read_margin = min(self.poll_interval, TAIL_FINAL_READ_MARGIN)
            if not run_deadline_limits_window and remaining <= final_read_margin + 1e-9:
                # The read just completed within the last margin. Let the
                # silence interval reach its boundary without starting another
                # synchronous read that could overrun the individual timeout.
                while now < wait_deadline:
                    time.sleep(wait_deadline - now)
                    now = time.monotonic()
                    if now >= self.run_deadline:
                        self._check_run_deadline("during tail silence window")
                return

            sleep_budget = remaining
            if not run_deadline_limits_window:
                # Wake with a small margin so the last read can finish before
                # the per-wait deadline.
                sleep_budget -= final_read_margin
            if sleep_budget <= 0:
                raise InjectorError("timeout during tail silence window")
            time.sleep(min(self.poll_interval, sleep_budget))

    def _require_no_output_before_tail_completion(self) -> None:
        self._check_run_deadline("before outbox read")
        records = self.channels.read_outbox_records()
        self._check_run_deadline("during outbox read")
        if records or self.channels.outbox_tail:
            raise InjectorError("Lua produced output before the incomplete input tail was completed")

    @staticmethod
    def _parse_response(line: str) -> list[str]:
        fields = line.split("|")
        if len(fields) < 3 or fields[0] != PROTOCOL_TAG or fields[1] != PROTOCOL_VERSION:
            raise InjectorError("Lua returned a malformed AC|1 record")
        expected_length = RESPONSE_LENGTHS.get(fields[2])
        if expected_length is None or len(fields) != expected_length:
            raise InjectorError("Lua returned an unknown response type or wrong field count")
        return fields

    def _expect_session_and_sequence(self, fields: list[str], expected_type: str, seq: str) -> None:
        if fields[2] != expected_type or fields[3] != self.session or fields[4] != seq:
            raise InjectorError(f"{expected_type} does not match the active session and sequence")

    def _validate_state(self, fields: list[str], sequence: int) -> None:
        self._expect_session_and_sequence(fields, "STATE", str(sequence))
        ship_id = fields[5]
        if ship_id != self.expected_ship_id:
            raise InjectorError("STATE ship_id does not match --expected-ship-id; ACK was not sent")
        if not ship_id or any(ord(char) < 0x21 or ord(char) > 0x7E for char in ship_id):
            raise InjectorError("STATE ship_id is not a printable ASCII token")
        if fields[10] not in {"0", "1"}:
            raise InjectorError("STATE shield_active is not 0 or 1")

        numeric_fields = fields[6:10] + fields[11:14]
        values: list[float] = []
        for value in numeric_fields:
            if not DECIMAL_RE.fullmatch(value):
                raise InjectorError("STATE contains a value outside the finite decimal grammar")
            number = float(value)
            if not math.isfinite(number):
                raise InjectorError("STATE contains a non-finite number")
            values.append(number)
        if any(value < 0 for value in values[:4]):
            raise InjectorError("STATE durability and shield values must be nonnegative")

    def _expect_error(self, sequence: str, code: str) -> None:
        fields = self._receive("ERROR")
        if fields[3] != self.session or fields[4] != sequence or fields[5] != code:
            raise InjectorError("Lua ERROR did not match the expected session, sequence, and code")

    def run(self) -> None:
        if not MIN_MAX_RUNTIME <= self.max_runtime <= MAX_MAX_RUNTIME:
            raise InjectorError("max runtime is outside its supported bounds")
        self.run_deadline = time.monotonic() + self.max_runtime
        self._append_inbox_record(encode_record("HELLO", self.session))
        hello_ack = self._receive("HELLO_ACK")
        if hello_ack[3] != self.session:
            raise InjectorError("HELLO_ACK has a foreign session")
        print("HELLO_ACK confirmed")

        self._ensure_no_unexpected_output()
        negative_records_sent = 0
        for sequence in range(1, MAX_PROBES + 1):
            self._ensure_no_unexpected_output()
            if sequence == 1:
                probe = encode_record("PROBE", self.session, sequence)
                self._append_inbox_fragment(probe[:-1])
                self._expect_no_output()
                self._finish_inbox_fragment()
            else:
                self._append_inbox_record(encode_record("PROBE", self.session, sequence))

            state = self._receive("STATE")
            self._validate_state(state, sequence)
            self._ensure_no_unexpected_output()

            if sequence == 1:
                # There is still one open probe: seq=2 must wait until ACKED 1.
                self._append_inbox_record(encode_record("PROBE", self.session, 2))
                self._expect_error("2", "unexpected_sequence")
                negative_records_sent += 1
                self._ensure_no_unexpected_output()
                print("ERROR confirmed: PROBE 2 before ACK 1 -> unexpected_sequence")

            self._append_inbox_record(encode_record("ACK", self.session, sequence))
            acked = self._receive("ACKED")
            self._expect_session_and_sequence(acked, "ACKED", str(sequence))
            self._ensure_no_unexpected_output()
            print(f"Roundtrip {sequence}/{MAX_PROBES} confirmed")

        foreign_session = "0" * 32
        if foreign_session == self.session:
            foreign_session = "1" * 32
        cases = (
            NegativeCase(
                "wrong protocol version",
                "0",
                "malformed_record",
                lambda: (f"AC|2|PROBE|{self.session}|2\n").encode("ascii"),
            ),
            NegativeCase(
                "foreign-session PROBE",
                "0",
                "invalid_session",
                lambda: encode_record("PROBE", foreign_session, 2),
            ),
            NegativeCase(
                "unknown type",
                "0",
                "unknown_type",
                lambda: (f"AC|1|ACTION|{self.session}|2\n").encode("ascii"),
            ),
            NegativeCase(
                "repeated ACK",
                "1",
                "unexpected_sequence",
                lambda: encode_record("ACK", self.session, 1),
            ),
        )
        if negative_records_sent + len(cases) > MAX_NEGATIVE_RECORDS:
            raise InjectorError("internal negative-case list exceeds the Lua limit")

        for case in cases:
            self._ensure_no_unexpected_output()
            self._append_inbox_record(case.record_factory())
            self._expect_error(case.sequence, case.code)
            negative_records_sent += 1
            print(f"ERROR confirmed: {case.name} -> {case.code}")

        if negative_records_sent != MAX_NEGATIVE_RECORDS:
            raise InjectorError("internal negative-case plan does not use the fixed five-record budget")
        self._ensure_no_unexpected_output()
        self._check_run_deadline("before reporting success")
        print(f"PASS: {MAX_PROBES} valid probe cycles and five representative Lua negative/replay cases")


def bounded_float(value: str, minimum: float, maximum: float, label: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{label} must be a number") from exc
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise argparse.ArgumentTypeError(f"{label} must be between {minimum} and {maximum}")
    return number


def positive_ship_id(value: str) -> str:
    if (
        not 1 <= len(value) <= 128
        or "|" in value
        or any(ord(char) < 0x21 or ord(char) > 0x7E for char in value)
    ):
        raise argparse.ArgumentTypeError("ship ID must be 1-128 printable ASCII characters")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run 50 bounded AC|1 Lua-inbox probe cycles and five representative negative cases."
    )
    parser.add_argument(
        "--moddata-dir",
        required=True,
        help="explicit existing isolated moddata directory containing both empty channel files",
    )
    parser.add_argument(
        "--expected-ship-id",
        required=True,
        type=positive_ship_id,
        help="ship ID independently verified by the caller; STATE must match before ACK",
    )
    parser.add_argument(
        "--timeout",
        type=lambda value: bounded_float(value, MIN_TIMEOUT, MAX_TIMEOUT, "timeout"),
        default=5.0,
    )
    parser.add_argument(
        "--max-runtime",
        type=lambda value: bounded_float(value, MIN_MAX_RUNTIME, MAX_MAX_RUNTIME, "max runtime"),
        default=DEFAULT_MAX_RUNTIME,
        help=(
            "maximum total monotonic run time in seconds (default: 600; "
            "allowed: 1-900); every response wait and silence window is capped by the remaining budget"
        ),
    )
    parser.add_argument(
        "--poll-interval",
        type=lambda value: bounded_float(value, MIN_POLL_INTERVAL, MAX_POLL_INTERVAL, "poll interval"),
        default=0.1,
    )
    args = parser.parse_args(argv)
    if args.poll_interval > args.timeout:
        parser.error("--poll-interval must not exceed --timeout")

    try:
        directory, directory_identity = resolve_moddata_dir(args.moddata_dir)
        channels = Channels(directory, directory_identity)
        LuaProtocolInjector(
            channels,
            args.expected_ship_id,
            args.timeout,
            args.poll_interval,
            args.max_runtime,
        ).run()
    except (InjectorError, OSError) as exc:
        print(f"injector stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
