import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import security_check  # noqa: E402


class SecurityPathTests(unittest.TestCase):
    def test_private_paths_are_detected_but_public_sample_is_allowed(self):
        self.assertIsNotNone(security_check.private_path_reason(Path("profile/facts.md")))
        self.assertIsNotNone(
            security_check.private_path_reason(Path("resume-optimizer/profile/facts.md"))
        )
        self.assertIsNotNone(security_check.private_path_reason(Path("docs/research/notes.md")))
        self.assertIsNotNone(security_check.private_path_reason(Path("jobs/example.json")))
        self.assertIsNone(security_check.private_path_reason(Path("jobs/job.txt")))
        self.assertIsNone(security_check.private_path_reason(Path("profile/facts.example.md")))


if __name__ == "__main__":
    unittest.main()
