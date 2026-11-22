import csv
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import import_maintenance as maintenance

S = '{' + maintenance.NS['s'] + '}'


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'source'
        self.output = Path(self.temp.name) / 'normalized'
        shutil.copytree(ROOT / 'data/source', self.source)
        shutil.copytree(ROOT / 'data/normalized', self.output)
        self.book = self.source / 'maintenance.xlsx'
        self.original = self.book.read_bytes()

    def edit_xml(self, member, change):
        with ZipFile(self.book) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        xml = ET.fromstring(files[member])
        change(xml)
        files[member] = ET.tostring(xml, encoding='utf-8', xml_declaration=True)
        with ZipFile(self.book, 'w', ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)

    def set_cell(self, address, value, kind='inlineStr', sheet='sheet1', formula=False):
        def change(xml):
            cell = xml.find(f'.//{S}c[@r="{address}"]')
            if cell is None:
                row_number = ''.join(c for c in address if c.isdigit())
                row = xml.find(f'.//{S}row[@r="{row_number}"]')
                if row is None:
                    row = ET.SubElement(xml.find(f'{S}sheetData'), S + 'row', r=row_number)
                cell = ET.SubElement(row, S + 'c', r=address)
            cell.clear()
            cell.set('r', address)
            cell.set('t', kind)
            if formula:
                ET.SubElement(cell, S + 'f').text = '1+1'
            if kind == 'inlineStr':
                ET.SubElement(ET.SubElement(cell, S + 'is'), S + 't').text = str(value)
            else:
                ET.SubElement(cell, S + 'v').text = str(value)
        self.edit_xml('xl/worksheets/' + sheet + '.xml', change)

    def snapshot(self):
        return {str(p): p.read_bytes() for folder in (self.source, self.output)
                for p in folder.iterdir() if p.name != 'maintenance.xlsx'}

    def sync(self, check=False):
        return maintenance.sync(self.source, self.output, check)

    def site(self):
        return json.loads((self.output / 'site_data.json').read_text(encoding='utf-8'))

    def first_id(self):
        rows, _ = maintenance.read_workbook(self.book)
        return rows['歌曲'][1][1][0][0]

    def test_initial_migration_and_repeat_import_preserve_website_and_inputs(self):
        before = self.site()
        placements = (self.source / 'song_placements.csv').read_bytes()
        self.sync()
        self.assertEqual(before, self.site())
        self.assertEqual(self.book.read_bytes(), self.original)
        self.assertEqual((self.source / 'song_placements.csv').read_bytes(), placements)
        self.assertEqual(self.sync()['changed_files'], 0)
        self.assertEqual(self.sync(check=True)['changed_files'], 0)

    def test_new_song_with_placements_and_members_imports(self):
        row = 1000  # Intentionally outside the Excel table: appended rows must be read.
        values = {'A': 'song_test_new', 'B': 'Maintenance test song', 'C': '2026/11/22',
                  'D': '12,12', 'E': 'fine', 'F': '英', 'G': '涉', 'P': 'fine', 'Q': 'fine'}
        for column, value in values.items():
            self.set_cell(f'{column}{row}', value)
        site = self.site()
        fine = next(u for u in site['units'] if u['name'] == 'fine')['id']
        with (self.source / 'song_placements.csv').open('a', encoding='utf-8', newline='') as stream:
            csv.writer(stream).writerow(['song_test_new', 'Maintenance test song', fine, 'fine', 99999])
        self.sync()
        new = next(s for s in self.site()['songs'] if s['id'] == 'song_test_new')
        self.assertEqual(len(self.site()['songs']), len(site['songs']) + 1)
        self.assertEqual(new['releaseDate'], '2026-11-22')
        self.assertEqual([p['label'] for p in new['positions'][:2]], ['英', '涉'])
        self.assertEqual(new['combinations'][0]['count'], 2)
        self.assertEqual(new['combinations'][0]['color'], '#65AB31')

    def add_song_without_id(self, title='Automatic ID song'):
        for column, value in {'B': title, 'E': 'fine | Trickstar', 'F': '英', 'P': 'fine'}.items():
            self.set_cell(f'{column}1000', value)
        with (self.source / 'song_placements.csv').open('a', encoding='utf-8', newline='') as stream:
            for name in ('fine', 'Trickstar'):
                uid = next(u['id'] for u in self.site()['units'] if u['name'] == name)
                csv.writer(stream).writerow(['', title, uid, name, 99999])

    def test_blank_ids_are_filled_once_and_survive_rename(self):
        self.add_song_without_id()
        original_book = self.book.read_bytes()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, '尚未同步'):
            self.sync(check=True)
        self.assertEqual(original_book, self.book.read_bytes())
        self.assertEqual(before, self.snapshot())
        self.sync()
        song = next(s for s in self.site()['songs'] if s['title'] == 'Automatic ID song')
        sid = song['id']
        self.assertRegex(sid, r'^song_[0-9a-f]{12}$')
        workbook, _ = maintenance.read_workbook(self.book)
        record = next(r for r in maintenance.sheet_records(workbook, '歌曲', maintenance.SONG_HEADERS) if r['_row'] == 1000)
        self.assertEqual(record['song_id'], sid)
        with (self.source / 'song_placements.csv').open(encoding='utf-8-sig', newline='') as stream:
            placements = [r for r in csv.DictReader(stream) if r['title'] == 'Automatic ID song']
        self.assertEqual([p['song_id'] for p in placements], [sid, sid])
        self.assertEqual(self.sync()['changed_files'], 0)
        self.set_cell('B1000', 'Renamed automatic song')
        self.sync()
        self.assertEqual(next(s['id'] for s in self.site()['songs'] if s['title'] == 'Renamed automatic song'), sid)

    def test_id_backfill_preserves_all_other_workbook_parts(self):
        self.add_song_without_id()
        before = self.book.read_bytes()
        self.sync()
        with ZipFile(io.BytesIO(before)) as original, ZipFile(self.book) as after:
            self.assertEqual(original.namelist(), after.namelist())
            for name in original.namelist():
                if name != 'xl/worksheets/sheet1.xml':
                    self.assertEqual(original.read(name), after.read(name), name)
        # An existing blank, styled ID cell must retain its style too.
        sample = b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1000"><c r="A1000" s="11"/><c r="B1000" t="inlineStr"><is><t>Test</t></is></c></row></sheetData></worksheet>'
        self.edit_xml('xl/worksheets/sheet1.xml', lambda xml: None)
        with ZipFile(self.book) as archive:
            members = {n: archive.read(n) for n in archive.namelist()}
        members['xl/worksheets/sheet1.xml'] = sample
        blob = io.BytesIO()
        with ZipFile(blob, 'w') as archive:
            for name, value in members.items(): archive.writestr(name, value)
        patched = maintenance.fill_workbook_ids(blob.getvalue(), {1000: 'song_test'})
        with ZipFile(io.BytesIO(patched)) as archive:
            sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        self.assertEqual(sheet.find(f'.//{S}c[@r="A1000"]').get('s'), '11')

    def test_invalid_new_song_does_not_fill_ids_or_change_outputs(self):
        self.add_song_without_id()
        self.set_cell('F1000', '不存在的人物')
        before = self.snapshot()
        workbook_before = self.book.read_bytes()
        with self.assertRaisesRegex(ValueError, '人物'):
            self.sync()
        self.assertEqual(before, self.snapshot())
        self.assertEqual(workbook_before, self.book.read_bytes())

    def test_nonempty_placement_ids_are_not_changed_by_title(self):
        self.add_song_without_id()
        path = self.source / 'song_placements.csv'
        path.write_bytes(path.read_bytes().replace(b',Automatic ID song,', b'unknown_song,Automatic ID song,', 1))
        workbook_before = self.book.read_bytes()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'Unknown song_id'):
            self.sync()
        self.assertEqual(before, self.snapshot())
        self.assertEqual(workbook_before, self.book.read_bytes())

    def test_unmatched_placement_title_does_not_fill_ids(self):
        self.add_song_without_id()
        path = self.source / 'song_placements.csv'
        path.write_bytes(path.read_bytes().replace(b',Automatic ID song,', b',Wrong title,', 1))
        with self.assertRaisesRegex(ValueError, '无法填写 song_id'):
            self.sync()

    def test_backfill_rolls_back_sources_and_outputs_if_commit_fails(self):
        self.add_song_without_id()
        before = self.snapshot()
        workbook_before = self.book.read_bytes()
        real_replace = maintenance.os.replace
        def fail_site(src, dest):
            if dest == self.output / 'site_data.json':
                raise PermissionError('test lock')
            return real_replace(src, dest)
        with patch.object(maintenance.os, 'replace', side_effect=fail_site):
            with self.assertRaises(OSError): self.sync()
        self.assertEqual(before, self.snapshot())
        self.assertEqual(workbook_before, self.book.read_bytes())

    def test_song_removal_requires_removing_placement_then_removes_all_relations(self):
        sid = self.first_id()
        def remove(xml):
            data = xml.find(f'{S}sheetData')
            data.remove(data.find(f'{S}row[@r="2"]'))
        self.edit_xml('xl/worksheets/sheet1.xml', remove)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'Unknown song_id'):
            self.sync()
        self.assertEqual(before, self.snapshot())
        path = self.source / 'song_placements.csv'
        lines = path.read_bytes().splitlines(keepends=True)
        path.write_bytes(b''.join(line for line in lines if not line.startswith(sid.encode() + b',')))
        self.sync()
        for folder in (self.source, self.output):
            for path in folder.iterdir():
                if path.suffix in ('.csv', '.json'):
                    self.assertNotIn(sid.encode(), path.read_bytes(), str(path))

    def test_dictionary_and_display_edits_are_used(self):
        self.set_cell('C2', '#123456', sheet='sheet4')  # 人物
        self.set_cell('B3', '#010203', sheet='sheet8')  # 显示设置
        self.sync()
        site = self.site()
        self.assertEqual(site['characters'][0]['color'], '#123456')
        self.assertEqual(site['display']['characterTextColor'], '#010203')

    def test_free_and_unknown_positions_are_distinct(self):
        self.set_cell('D2', '')
        self.set_cell('F2', '自由')
        self.set_cell('G2', '')
        self.set_cell('Q2', '')
        self.sync()
        song = next(s for s in self.site()['songs'] if s['id'] == self.first_id())
        self.assertEqual(song['formationKind'], 'mixed')
        self.assertEqual([p['kind'] for p in song['positions'][:2]], ['free', 'empty'])

    def test_collaboration_label_order_and_position_ownership_are_preserved(self):
        baseline = self.site()
        self.sync()
        names = ['Crossing×Heart', 'CIVIL WAR']
        for title in names:
            before = next(s for s in baseline['songs'] if s['title'] == title)
            after = next(s for s in self.site()['songs'] if s['title'] == title)
            self.assertEqual(before, after)

    def test_excel_serial_dates_and_1904_epoch(self):
        for use1904, serial in [(False, 46348), (True, 44886)]:
            self.book.write_bytes(self.original)
            if use1904:
                def set_epoch(xml):
                    props = xml.find(f'{S}workbookPr')
                    if props is None:
                        props = ET.SubElement(xml, S + 'workbookPr')
                    props.set('date1904', '1')
                self.edit_xml('xl/workbook.xml', set_epoch)
            self.set_cell('C2', serial, kind='n')
            self.sync()
            self.assertEqual(self.site()['songs'][0]['releaseDate'], '2026-11-22')

    def test_shared_rich_text_ignores_japanese_phonetic_guides(self):
        # Excel may add furigana without changing the displayed name.
        with ZipFile(self.book) as archive:
            shared = ET.fromstring(archive.read('xl/sharedStrings.xml'))
        index = len(shared)
        def add_ruby(xml):
            item = ET.SubElement(xml, S + 'si')
            run = ET.SubElement(item, S + 'r')
            ET.SubElement(run, S + 't').text = '英'
            ruby = ET.SubElement(item, S + 'rPh', sb='0', eb='1')
            ET.SubElement(ruby, S + 't').text = 'エイ'
        self.edit_xml('xl/sharedStrings.xml', add_ruby)
        self.set_cell('F2', index, kind='s')
        self.sync()
        self.assertEqual(self.site()['songs'][0]['positions'][0]['label'], '英')

    def test_missing_workbook_is_not_replaced_with_generated_csv(self):
        self.book.unlink()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, '无法读取维护表'):
            self.sync()
        self.assertEqual(before, self.snapshot())

    def test_numeric_dates_reject_excel_leap_bug_and_time_fraction(self):
        for value in ['60', '46348.5', '20261122']:
            self.book.write_bytes(self.original)
            self.set_cell('C2', value, kind='n')
            with self.assertRaisesRegex(ValueError, '日期'):
                self.sync()

    def test_names_and_ids_can_both_reference_members_and_labels(self):
        sid = self.first_id()
        original = next(s for s in self.site()['songs'] if s['id'] == sid)
        self.set_cell('F2', original['positions'][0]['characterId'])
        self.set_cell('E2', original['labelIds'][0])
        self.set_cell('P2', original['labelIds'][0])
        self.sync()
        self.assertEqual(original, next(s for s in self.site()['songs'] if s['id'] == sid))

    def test_invalid_data_does_not_change_any_generated_file(self):
        cases = [('F2', '不存在的人物', '人物'), ('C2', '2026/02/30', '实装日期'),
                 ('E2', 'fine | fine', 'Duplicate'), ('G2', '英', 'Duplicate performer'),
                 ('A2', '', 'song_id'), ('P2', 'Trickstar', 'Position tag outside song'),
                 ('Z2', '#invalid', 'Invalid song background'), ('E2', 'fine |', '空项')]
        for address, value, message in cases:
            with self.subTest(address=address, value=value):
                self.book.write_bytes(self.original)
                self.set_cell(address, value)
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, message):
                    self.sync()
                self.assertEqual(before, self.snapshot())

    def test_formulas_and_changed_headers_are_rejected(self):
        for address, formula in [('B2', True), ('B1', False)]:
            self.book.write_bytes(self.original)
            self.set_cell(address, '2', kind='n', formula=formula)
            with self.assertRaisesRegex(ValueError, '公式|表头'):
                self.sync()

    def test_check_detects_workbook_changes_without_writing(self):
        self.set_cell('B2', 'Renamed song')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, '尚未同步'):
            self.sync(check=True)
        self.assertEqual(before, self.snapshot())
        self.sync()
        self.assertEqual(self.site()['songs'][0]['title'], 'Renamed song')
        self.assertEqual(self.sync(check=True)['changed_files'], 0)

    def test_check_detects_direct_edits_to_generated_csv(self):
        path = self.source / 'songs.csv'
        path.write_bytes(path.read_bytes().replace(b'RAINBOW CIRCUS', b'Manual CSV edit'))
        with self.assertRaisesRegex(ValueError, '尚未同步'):
            self.sync(check=True)
        self.sync()
        self.assertNotIn(b'Manual CSV edit', path.read_bytes())

    def test_failed_write_rolls_back_earlier_replacements(self):
        first, second = self.source / 'songs.csv', self.source / 'song_labels.csv'
        original = {first: first.read_bytes(), second: second.read_bytes()}
        real_replace = maintenance.os.replace
        calls = 0
        def fail_second(src, dest):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise PermissionError('test lock')
            return real_replace(src, dest)
        with patch.object(maintenance.os, 'replace', side_effect=fail_second):
            with self.assertRaises(OSError):
                maintenance.write_transaction({first: b'changed', second: b'changed'})
        self.assertEqual(original, {p: p.read_bytes() for p in original})
        self.assertFalse(list(self.source.glob('.maintenance-*')))


if __name__ == '__main__':
    unittest.main()
