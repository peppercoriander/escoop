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


class ReleaseDateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'source'
        shutil.copytree(ROOT / 'data/source', self.source)
        self.path = self.source / 'song_releases.csv'
        with self.path.open(encoding='utf-8-sig', newline='') as stream:
            self.rows = list(csv.DictReader(stream))

    def write(self):
        with self.path.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, ['song_id', 'title', 'release_date'])
            writer.writeheader()
            writer.writerows(self.rows)

    def build(self):
        self.write()
        return prepare_data.build(self.source)

    def test_dates_remain_dates_and_source_is_not_rewritten(self):
        values = ['2024-02-29', '2026-11-16', '2099-12-31', '']
        for row, value in zip(self.rows, values):
            row['release_date'] = value
        self.write()
        before = self.path.read_bytes()
        site = json.loads(prepare_data.build(self.source)['site_data.json'])
        dates = {song['id']: song['releaseDate'] for song in site['songs']}
        for row, value in zip(self.rows, values):
            self.assertEqual(dates[row['song_id']], value or None)
        self.assertEqual(before, self.path.read_bytes())

    def test_missing_record_is_unknown_date(self):
        missing = self.rows.pop(0)['song_id']
        site = json.loads(self.build()['site_data.json'])
        self.assertIsNone(next(s for s in site['songs'] if s['id'] == missing)['releaseDate'])

    def test_invalid_dates_rejected(self):
        for value in ['2026-02-29', '2026-11-31', '2026-13-01', '2026/11/16', '2026-1-1', '2026-11-16T00:00:00', '0000-01-01']:
            with self.subTest(value=value):
                self.rows[0]['release_date'] = value
                with self.assertRaisesRegex(ValueError, 'Invalid release date'):
                    self.build()

    def test_duplicate_song_rejected(self):
        self.rows.append(dict(self.rows[0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate key'):
            self.build()

    def test_unknown_song_rejected(self):
        self.rows[0]['song_id'] = 'unknown_song'
        with self.assertRaisesRegex(ValueError, 'Unknown song_id'):
            self.build()

    def test_reference_title_cannot_rename_song(self):
        self.rows[0]['title'] = 'reference-only'
        payload = json.loads(self.build()['dataset.json'])
        self.assertNotEqual(payload['tables']['song_releases'][0]['title'], 'reference-only')


if __name__ == '__main__':
    unittest.main()
