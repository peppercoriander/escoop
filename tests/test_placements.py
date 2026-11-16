import csv
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_data', ROOT / 'scripts/prepare_data.py')
prepare_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_data)


class PlacementValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'source'
        shutil.copytree(ROOT / 'data/source', self.source)
        self.path = self.source / 'song_placements.csv'
        with self.path.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            self.headers = reader.fieldnames
            self.rows = list(reader)

    def write(self):
        with self.path.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, self.headers)
            writer.writeheader()
            writer.writerows(self.rows)

    def assertInvalid(self, message):
        self.write()
        with self.assertRaisesRegex(ValueError, message):
            prepare_data.build(self.source)

    def test_import_preserves_manual_orders_and_never_rewrites_source(self):
        before = self.path.read_bytes()
        output = prepare_data.build(self.source)
        site = json.loads(output['site_data.json'])
        expected = {(r['song_id'], r['section_id']): int(r['sort_order']) for r in self.rows}
        actual = {(r['songId'], r['sectionId']): r['sortOrder'] for r in site['songPlacements']}
        self.assertEqual(actual, expected)
        self.assertEqual(self.path.read_bytes(), before)

    def test_reference_names_do_not_override_canonical_names(self):
        self.rows[0]['title'] = 'reference-only title'
        self.rows[0]['section_name'] = 'reference-only section'
        self.write()
        dataset = json.loads(prepare_data.build(self.source)['dataset.json'])
        normalized = next(r for r in dataset['tables']['song_placements'] if r['song_id'] == self.rows[0]['song_id'] and r['section_id'] == self.rows[0]['section_id'])
        self.assertNotEqual(normalized['title'], self.rows[0]['title'])
        self.assertNotEqual(normalized['section_name'], self.rows[0]['section_name'])

    def test_duplicate_song_section_rejected(self):
        self.rows.append({**self.rows[0], 'sort_order': '99999'})
        self.assertInvalid('Duplicate key')

    def test_duplicate_numeric_order_rejected(self):
        self.rows[1]['sort_order'] = '0' + self.rows[0]['sort_order']
        self.assertInvalid('Duplicate key')

    def test_unknown_section_rejected(self):
        self.rows[0]['section_id'] = 'unknown_unit'
        self.assertInvalid('Unknown placement section')

    def test_negative_order_rejected(self):
        self.rows[0]['sort_order'] = '-1'
        self.assertInvalid('Placement order must be positive')

    def test_missing_song_placement_rejected(self):
        sid = self.rows[0]['song_id']
        self.rows = [r for r in self.rows if r['song_id'] != sid]
        self.assertInvalid('Songs missing placements')

    def test_unrelated_unit_placement_rejected(self):
        self.rows[0]['section_id'] = 'group_other'
        self.rows[0]['sort_order'] = '99999'
        self.assertInvalid('Placement outside song membership')


if __name__ == '__main__':
    unittest.main()
