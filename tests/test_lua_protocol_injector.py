"""Offline deadline tests for the source-only Lua protocol injector."""

from __future__ import annotations

from contextlib import ExitStack
import unittest
from unittest.mock import patch

from bridge import lua_protocol_injector as injector_module


class FakeClock:
    def __init__(
        self,
        start: float = 100.0,
        *,
        sleep_overrun_call: int | None = None,
        sleep_overrun: float = 0.0,
    ) -> None:
        self.now = start
        self.sleeps: list[float] = []
        self.sleep_overrun_call = sleep_overrun_call
        self.sleep_overrun = sleep_overrun

    def monotonic(self) -> float:
        return self.now

    def sleep(self, duration: float) -> None:
        self.sleeps.append(duration)
        self.now += duration
        if len(self.sleeps) == self.sleep_overrun_call:
            self.now += self.sleep_overrun


class FakeChannels:
    def __init__(
        self,
        clock: FakeClock,
        *,
        response_at: float | None = None,
        response: str | None = None,
        append_delay: float = 0.0,
        read_delay: float = 0.0,
        read_delay_call: int | None = None,
    ) -> None:
        self.clock = clock
        self.response_at = response_at
        self.response = response
        self.append_delay = append_delay
        self.read_delay = read_delay
        self.read_delay_call = read_delay_call
        self.outbox_tail = b""
        self.appended: list[bytes] = []
        self.read_count = 0
        self.read_completed_at: list[float] = []

    def append_inbox_record(self, record: bytes) -> None:
        self.appended.append(record)
        self.clock.now += self.append_delay

    def append_inbox_fragment(self, fragment: bytes) -> None:
        self.appended.append(fragment)

    def finish_inbox_fragment(self) -> None:
        pass

    def read_outbox_records(self) -> list[str]:
        self.read_count += 1
        if self.read_delay_call is None or self.read_count == self.read_delay_call:
            self.clock.now += self.read_delay
        self.read_completed_at.append(self.clock.now)
        if (
            self.response is not None
            and self.response_at is not None
            and self.clock.now >= self.response_at
        ):
            response, self.response = self.response, None
            return [response]
        return []

    def ensure_no_unexpected_output(self) -> None:
        if self.read_outbox_records():
            raise injector_module.InjectorError("unexpected fake output")


class LuaProtocolInjectorDeadlineTests(unittest.TestCase):
    def make_injector(
        self,
        clock: FakeClock,
        channels: FakeChannels,
        *,
        timeout: float = 1.0,
        poll_interval: float = 0.1,
        max_runtime: float = 0.25,
    ) -> injector_module.LuaProtocolInjector:
        result = injector_module.LuaProtocolInjector(
            channels,
            expected_ship_id="offline-test-ship",
            timeout=timeout,
            poll_interval=poll_interval,
            max_runtime=max_runtime,
        )
        result.run_deadline = clock.now + max_runtime
        return result

    def patched_clock(self, clock: FakeClock) -> ExitStack:
        stack = ExitStack()
        stack.enter_context(patch.object(injector_module.time, "monotonic", clock.monotonic))
        stack.enter_context(patch.object(injector_module.time, "sleep", clock.sleep))
        return stack

    def test_response_wait_is_capped_by_remaining_run_budget(self) -> None:
        clock = FakeClock()
        channels = FakeChannels(clock)
        injector = self.make_injector(clock, channels)

        with self.patched_clock(clock), self.assertRaisesRegex(
            injector_module.InjectorError, "total run deadline expired while waiting for HELLO_ACK"
        ):
            injector._receive("HELLO_ACK")

        self.assertAlmostEqual(clock.now, 100.25)
        self.assertLessEqual(max(clock.sleeps), 0.1)
        self.assertAlmostEqual(sum(clock.sleeps), 0.25)

    def test_tail_silence_window_is_capped_by_remaining_run_budget(self) -> None:
        clock = FakeClock()
        channels = FakeChannels(clock)
        injector = self.make_injector(clock, channels)

        with self.patched_clock(clock), self.assertRaisesRegex(
            injector_module.InjectorError, "total run deadline expired during tail silence window"
        ):
            injector._expect_no_output()

        self.assertAlmostEqual(clock.now, 100.25)
        self.assertAlmostEqual(sum(clock.sleeps), 0.25)

    def test_final_tail_read_accepts_fast_read_and_rejects_slow_read(self) -> None:
        fast_clock = FakeClock()
        fast_channels = FakeChannels(fast_clock)
        fast_injector = self.make_injector(
            fast_clock, fast_channels, timeout=1.0, poll_interval=0.25, max_runtime=2.0
        )

        with self.patched_clock(fast_clock):
            fast_injector._expect_no_output()

        self.assertEqual(fast_channels.read_count, 5)
        self.assertLess(fast_channels.read_completed_at[-1], 101.0)
        self.assertAlmostEqual(fast_clock.now, 101.0)

        scheduler_clock = FakeClock(sleep_overrun_call=5, sleep_overrun=0.02)
        scheduler_channels = FakeChannels(scheduler_clock)
        scheduler_injector = self.make_injector(
            scheduler_clock,
            scheduler_channels,
            timeout=1.0,
            poll_interval=0.25,
            max_runtime=2.0,
        )

        with self.patched_clock(scheduler_clock):
            scheduler_injector._expect_no_output()

        self.assertEqual(scheduler_channels.read_count, 5)
        self.assertLess(scheduler_channels.read_completed_at[-1], 101.0)
        self.assertAlmostEqual(scheduler_clock.now, 101.02)

        clock = FakeClock()
        channels = FakeChannels(clock, read_delay=0.02, read_delay_call=5)
        injector = self.make_injector(
            clock, channels, timeout=1.0, poll_interval=0.25, max_runtime=2.0
        )

        with self.patched_clock(clock), self.assertRaisesRegex(
            injector_module.InjectorError, "timeout during tail silence window"
        ):
            injector._expect_no_output()

        self.assertEqual(channels.read_count, 5)
        self.assertGreater(clock.now, 101.0)

    def test_per_response_timeout_still_applies_when_run_budget_is_longer(self) -> None:
        clock = FakeClock()
        channels = FakeChannels(clock)
        injector = self.make_injector(
            clock, channels, timeout=0.2, poll_interval=0.05, max_runtime=2.0
        )

        with self.patched_clock(clock), self.assertRaisesRegex(
            injector_module.InjectorError, "timeout waiting for HELLO_ACK"
        ):
            injector._receive("HELLO_ACK")

        self.assertAlmostEqual(clock.now, 100.2)
        self.assertLessEqual(sum(clock.sleeps), 0.2 + 1e-9)

    def test_response_arriving_during_a_slow_read_after_timeout_is_rejected(self) -> None:
        clock = FakeClock()
        session = "b" * 32
        channels = FakeChannels(
            clock,
            response_at=100.0,
            response=f"AC|1|HELLO_ACK|{session}",
            read_delay=0.25,
        )
        injector = self.make_injector(
            clock, channels, timeout=0.2, poll_interval=0.05, max_runtime=2.0
        )
        injector.session = session

        with self.patched_clock(clock), self.assertRaisesRegex(
            injector_module.InjectorError, "timeout waiting for HELLO_ACK"
        ):
            injector._receive("HELLO_ACK")

    def test_budget_is_shared_across_successive_waits(self) -> None:
        clock = FakeClock()
        session = "a" * 32
        channels = FakeChannels(
            clock,
            response_at=100.1,
            response=f"AC|1|HELLO_ACK|{session}",
        )
        injector = self.make_injector(
            clock, channels, timeout=1.0, poll_interval=0.05, max_runtime=0.15
        )
        injector.session = session

        with self.patched_clock(clock):
            response = injector._receive("HELLO_ACK")
            self.assertEqual(response[2], "HELLO_ACK")
            with self.assertRaisesRegex(
                injector_module.InjectorError, "total run deadline expired during tail silence window"
            ):
                injector._expect_no_output()

        self.assertAlmostEqual(clock.now, 100.15)

    def test_run_stops_if_an_append_consumes_the_total_budget(self) -> None:
        clock = FakeClock()
        channels = FakeChannels(clock, append_delay=1.1)
        injector = self.make_injector(clock, channels, max_runtime=1.0)
        injector.run_deadline = None

        with self.patched_clock(clock), self.assertRaisesRegex(
            injector_module.InjectorError, "total run deadline expired during inbox append"
        ):
            injector.run()

        self.assertEqual(len(channels.appended), 1)
        self.assertEqual(channels.read_count, 0)

    def test_max_runtime_cli_value_is_bounded(self) -> None:
        self.assertEqual(
            injector_module.bounded_float(
                "600",
                injector_module.MIN_MAX_RUNTIME,
                injector_module.MAX_MAX_RUNTIME,
                "max runtime",
            ),
            600.0,
        )
        for value in ("0.9", "900.1", "nan", "inf"):
            with self.subTest(value=value), self.assertRaises(injector_module.argparse.ArgumentTypeError):
                injector_module.bounded_float(
                    value,
                    injector_module.MIN_MAX_RUNTIME,
                    injector_module.MAX_MAX_RUNTIME,
                    "max runtime",
                )


if __name__ == "__main__":
    unittest.main()
