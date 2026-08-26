"""Verify that built distributions contain the runtime notification logo."""

import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path


class PackageDataTests(unittest.TestCase):
    """Check package data in the artifacts users actually install."""

    def test_distributions_include_logo_only(self):
        """Keep the runtime logo and omit the editable-install marker."""
        project_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as output_directory:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "build",
                    "--sdist",
                    "--wheel",
                    "--outdir",
                    output_directory,
                    project_root,
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            wheel = next(Path(output_directory).glob("*.whl"))
            sdist = next(Path(output_directory).glob("*.tar.gz"))

            with zipfile.ZipFile(wheel) as archive:
                wheel_files = set(archive.namelist())
            with tarfile.open(sdist) as archive:
                sdist_files = set(archive.getnames())

        self.assertIn("lnxlink/logo.png", wheel_files)
        self.assertNotIn("lnxlink/edit.txt", wheel_files)
        self.assertTrue(
            any(
                name.endswith(
                    (".dist-info/LICENSE.md", ".dist-info/licenses/LICENSE.md")
                )
                for name in wheel_files
            )
        )

        self.assertTrue(any(name.endswith("/lnxlink/logo.png") for name in sdist_files))
        self.assertFalse(
            any(name.endswith("/lnxlink/edit.txt") for name in sdist_files)
        )
        self.assertTrue(any(name.endswith("/LICENSE.md") for name in sdist_files))


if __name__ == "__main__":
    unittest.main()
