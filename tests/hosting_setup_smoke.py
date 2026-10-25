"""Exercise the setup script's actual IAM retry function without Google access."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / 'scripts/setup-firebase-github.sh').read_text()
RETRY = 'retry_iam() {' + SCRIPT.split('retry_iam() {', 1)[1].split("\nprintf 'Configuring", 1)[0]


class RetryChecks(unittest.TestCase):
    def run_case(self, failures, message, expected_attempts, expected_status):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            counter = folder / 'count'
            counter.write_text('0')
            command = folder / 'iam-command'
            command.write_text('''#!/bin/sh
count=$(cat "$COUNTER")
count=$((count + 1))
printf '%s' "$count" > "$COUNTER"
if [ "$count" -le "$FAILURES" ]; then
  printf '%s\\n' "$ERROR_MESSAGE" >&2
  exit 7
fi
printf 'success\\n'
''')
            command.chmod(0o755)
            # Skip real delays in tests only.
            delay = folder / 'sleep'
            delay.write_text('#!/bin/sh\nexit 0\n')
            delay.chmod(0o755)
            result = subprocess.run(
                ['bash', '-c', 'set -euo pipefail\n' + RETRY + '\nretry_iam iam-command\n'],
                env={**os.environ, 'PATH': str(folder) + ':' + os.environ['PATH'],
                     'COUNTER': str(counter), 'FAILURES': str(failures), 'ERROR_MESSAGE': message},
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, expected_status, result.stderr)
            self.assertEqual(int(counter.read_text()), expected_attempts)
            if expected_status == 0:
                self.assertEqual(result.stdout, 'success\n')

    def test_ready_account(self):
        self.run_case(0, '', 1, 0)

    def test_service_account_propagation(self):
        self.run_case(2, 'INVALID_ARGUMENT: Service account deployer does not exist.', 3, 0)

    def test_pool_propagation(self):
        self.run_case(1, 'NOT_FOUND: Workload identity pool not found.', 2, 0)

    def test_permission_errors_stop_immediately(self):
        self.run_case(10, 'PERMISSION_DENIED: caller lacks permission', 1, 7)

    def test_retries_are_bounded(self):
        self.run_case(10, 'Service account deployer does not exist.', 6, 7)


if __name__ == '__main__':
    unittest.main()
