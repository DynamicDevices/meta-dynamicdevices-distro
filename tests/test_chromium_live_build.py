"""Local fixtures only: no BitBake task or Chromium build is executed."""

import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import unittest


HELPER = (
    Path(__file__).resolve().parents[1]
    / "recipes-browser/chromium/chromium-ozone-wayland/chromium-live-build.py"
)


class LiveBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fifo = Path(self.temp.name) / "events"
        os.mkfifo(self.fifo)
        self.reader = os.open(self.fifo, os.O_RDWR | os.O_NONBLOCK)
        self.addCleanup(os.close, self.reader)

    def command(self, code):
        return [
            sys.executable, str(HELPER), "--fifo", str(self.fifo),
            "--task-log", "temp/log.do_compile", "--",
            sys.executable, "-c", code,
        ]

    def events(self):
        chunks = []
        while True:
            try:
                chunks.append(os.read(self.reader, 65536))
            except BlockingIOError:
                break
        return b"".join(chunks).decode().split("\0")[:-1]

    def run_fixture(self, code):
        result = subprocess.run(
            self.command(code), capture_output=True, text=True, timeout=10,
        )
        return result, self.events()

    def test_progress_stays_in_log_but_diagnostic_is_live(self):
        result, events = self.run_fixture(
            "import sys; print('[1/2] CXX sample.cc'); "
            "print('sample.cc:3: error: missing name', file=sys.stderr); "
            "sys.exit(7)"
        )
        self.assertEqual(result.returncode, 7)
        self.assertIn("[1/2] CXX sample.cc", result.stdout)
        self.assertFalse(any("[1/2]" in event for event in events))
        self.assertTrue(any("error: missing name" in event for event in events))
        self.assertTrue(events[-1].startswith("bberror "))
        self.assertIn("exit status 7", events[-1])

    def test_success_does_not_emit_error(self):
        result, events = self.run_fixture("print('[1/1] LINK chrome')")
        self.assertEqual(result.returncode, 0)
        self.assertFalse(any(event.startswith("bberror ") for event in events))

    def test_signal_is_reported_and_remains_failure(self):
        result, events = self.run_fixture(
            "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"
        )
        self.assertEqual(result.returncode, 128 + signal.SIGTERM)
        self.assertIn("signal 15", events[-1])

    def test_diagnostic_precedes_build_exit(self):
        process = subprocess.Popen(
            self.command(
                "import sys; print('fatal error: fixture', flush=True); "
                "sys.stdin.readline()"
            ), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
        )
        self.addCleanup(lambda: process.poll() is None and process.kill())
        received = b""
        while b"fatal error: fixture" not in received:
            ready, _, _ = select.select([self.reader], [], [], 5)
            self.assertTrue(ready, "diagnostic was not forwarded live")
            received += os.read(self.reader, 65536)
        self.assertIsNone(process.poll(), "diagnostic arrived only after exit")
        process.communicate("finish\n", timeout=5)
        self.assertEqual(process.returncode, 0)

    def test_nul_and_backslashes_cannot_inject_fifo_events(self):
        result, events = self.run_fixture(
            "import sys; sys.stdout.write('error: \\x00bberror fake \\\\n 100%\\n')"
        )
        self.assertEqual(result.returncode, 0)
        self.assertFalse(any(event.startswith("bberror ") for event in events))
        self.assertTrue(any("\ufffdbberror fake" in event for event in events))
        self.assertTrue(any("\\n 100%" in event for event in events))

    def test_missing_fifo_fails_before_starting_child(self):
        self.fifo.unlink()
        marker = Path(self.temp.name) / "should-not-exist"
        result = subprocess.run(
            self.command(f"open({str(marker)!r}, 'w').close()"),
            capture_output=True, text=True, timeout=5,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
