import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_data', ROOT / 'scripts/prepare_data.py')
prepare_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_data)


class PortableDataTests(unittest.TestCase):
    def test_lf_and_crlf_sources_generate_identical_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            shutil.copytree(ROOT / 'data/source', source)
            files = list(source.glob('*.csv')) + [source / 'display.json']
            for path in files:
                path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n'))
            lf_outputs = prepare_data.build(source)
            for path in files:
                path.write_bytes(path.read_bytes().replace(b'\n', b'\r\n'))
            self.assertEqual(lf_outputs, prepare_data.build(source))
            for name, content in lf_outputs.items():
                self.assertNotIn(b'\r\n', content, name)


if __name__ == '__main__':
    unittest.main()
