#!/usr/bin/env python3
"""Keep Ninja's task log, forwarding diagnostics to BitBake as they arrive."""

import argparse
import os
import re
import stat
import subprocess
import sys


PROGRESS = re.compile(r"^\[\s*\d+/\d+\](?:\s|$)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fifo", required=True)
    parser.add_argument("--task-log", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        parser.error("a build command is required")

    # Fail before starting Ninja if live reporting is unavailable. Do not
    # accidentally write diagnostic events to a regular file or wait for a
    # nonexistent FIFO reader. BitBake opens its FIFO before running this task.
    try:
        if not stat.S_ISFIFO(os.stat(args.fifo).st_mode):
            raise OSError("live log channel is not a FIFO")
        fd = os.open(args.fifo, os.O_WRONLY | os.O_NONBLOCK)
    except OSError as exc:
        print(f"Chromium live logging unavailable: {exc}", file=sys.stderr)
        return 1

    os.set_blocking(fd, True)
    with os.fdopen(fd, "wb", buffering=0) as events:
        def emit(level, message):
            # NUL frames BitBake messages. Compiler text must not introduce a
            # second event; unlike the shell bbplain helper, do not interpret
            # backslashes or percent escapes in diagnostics.
            message = message.replace("\0", "\ufffd")
            packet = f"{level} {message}\0".encode("utf-8", errors="replace")
            view = memoryview(packet)
            while view:
                written = events.write(view)
                view = view[written:]

        emit("bbplain", "DD Chromium: starting " + command[0])
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as exc:
            emit("bberror", f"DD Chromium: cannot start build: {exc}")
            return 127

        with process:
            try:
                for line in process.stdout:
                    print(line, end="", flush=True)
                    if line.strip() and not PROGRESS.match(line):
                        emit("bbplain", "DD Chromium: " + line.rstrip("\r\n"))
                status = process.wait()
            except BaseException:
                process.terminate()
                raise

        if status:
            result = status if status > 0 else 128 - status
            detail = f"signal {-status}" if status < 0 else f"exit status {status}"
            message = (
                f"DD Chromium: Ninja failed with {detail}; "
                f"full task log: {args.task_log}"
            )
            print(message, flush=True)
            # bberror marks the failure as already reported. In this pinned
            # BitBake, TaskFailed.errprinted then prevents the enormous
            # duplicate task-log dump without changing global log policy.
            emit("bberror", message)
            return result
        emit("bbplain", "DD Chromium: Ninja completed successfully")
        return 0


if __name__ == "__main__":
    sys.exit(main())
