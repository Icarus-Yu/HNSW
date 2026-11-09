"""Integration checks for moving the experiment between Windows and Linux."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent


class HeaderPortability(unittest.TestCase):
    def exercise(self, newline, change=False):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            shutil.copyfile(ROOT / 'prepare_variant.py', work / 'prepare_variant.py')
            vendor = work / 'vendor/hnswlib/hnswlib'
            vendor.mkdir(parents=True)
            original = (ROOT / 'vendor/hnswlib/hnswlib/hnswalg.h').read_text(encoding='utf-8')
            if change:
                original = original.replace('max_elements_{0}', 'max_elements_{1}', 1)
            before = original.replace('\n', newline).encode('utf-8')
            (vendor / 'hnswalg.h').write_bytes(before)
            result = subprocess.run([sys.executable, str(work / 'prepare_variant.py')],
                                    capture_output=True, text=True)
            self.assertEqual((vendor / 'hnswalg.h').read_bytes(), before)
            if change:
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Expected unmodified hnswlib', result.stderr)
                self.assertFalse((work / 'build/valid/hnswlib/hnswalg.h').exists())
            else:
                self.assertEqual(result.returncode, 0, result.stderr)
                generated = (work / 'build/valid/hnswlib/hnswalg.h').read_text(encoding='utf-8')
                self.assertIn('valid_neighbors.reserve(maxM0_)', generated)
                self.assertIn('HNSW_PREFETCH_STRIDE', generated)

    def test_linux_lf(self):
        self.exercise('\n')

    def test_windows_crlf(self):
        self.exercise('\r\n')

    def test_modified_source_is_rejected(self):
        self.exercise('\n', change=True)


if __name__ == '__main__':
    unittest.main()
