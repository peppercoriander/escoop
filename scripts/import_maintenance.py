"""Validate maintenance.xlsx + song_placements.csv, then generate CSV and website data.

Uses only Python's standard library. Blank song IDs are filled after validation.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import posixpath
import re
import tempfile
import uuid
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
from zipfile import ZipFile, BadZipFile

import prepare_data

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
SHEETS = {
    'groups': '公司', 'units': '组合', 'characters': '人物',
    'character_units': '组合成员', 'labels': '标签', 'frequency_colors': '次数颜色',
}
SONG_HEADERS = ['song_id', '歌曲名称', '实装日期', '数字组合原文', '标签（按顺序，用 | 分隔）'] + [
    f'{n}号位' for n in range(1, 11)] + [f'{n}号位标签' for n in range(1, 11)] + ['特殊底色']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def string_text(element):
    # Phonetic guides (rPh) in Japanese Excel cells are not displayed values.
    return ''.join(child.text or '' for child in element.findall('s:t', NS) + element.findall('s:r/s:t', NS))


def read_workbook(path):
    """Read literal worksheet values, retaining cell types and row numbers.

    Formulas are deliberately rejected, including cached results. This prevents
    importing stale formulas from a workbook that Excel has not recalculated.
    """
    try:
        archive = ZipFile(path)
    except (BadZipFile, FileNotFoundError) as error:
        raise ValueError(f'无法读取维护表 {path}: {error}') from error
    with archive:
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        props = workbook.find('s:workbookPr', NS)
        date1904 = props is not None and props.get('date1904') in ('1', 'true')
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {r.get('Id'): r.get('Target') for r in rels if r.get('TargetMode') != 'External'}
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = [string_text(item) for item in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        result = {}
        for sheet in workbook.findall('s:sheets/s:sheet', NS):
            name = sheet.get('name')
            if name not in {*SHEETS.values(), '歌曲', '显示设置'}:
                continue
            target = targets[sheet.get(REL)]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            xml = ET.fromstring(archive.read(target))
            require(xml.find('s:mergeCells', NS) is None, f'「{name}」不可合并数据单元格')
            rows = []
            for row in xml.findall('s:sheetData/s:row', NS):
                cells = {}
                row_number = int(row.get('r'))
                for cell in row.findall('s:c', NS):
                    address = cell.get('r')
                    require(cell.find('s:f', NS) is None, f'「{name}」{address}: 请填值，不要使用公式')
                    column = re.fullmatch(r'([A-Z]+)[0-9]+', address)[1]
                    index = 0
                    for letter in column:
                        index = index * 26 + ord(letter) - 64
                    kind = cell.get('t', 'n')
                    value = cell.findtext('s:v', default='', namespaces=NS)
                    if kind == 's':
                        value = strings[int(value)]
                    elif kind == 'inlineStr':
                        inline = cell.find('s:is', NS)
                        value = string_text(inline) if inline is not None else ''
                    elif kind in ('b', 'e'):
                        raise ValueError(f'「{name}」{address}: 不支持布尔值或错误值 {value!r}')
                    if value != '':
                        cells[index - 1] = (value, kind)
                if cells:
                    rows.append((row_number, cells))
            require(name not in result, f'重复工作表: {name}')
            result[name] = rows
        return result, date1904


def sheet_records(workbook, name, headers):
    require(name in workbook, f'缺少工作表「{name}」')
    rows = workbook[name]
    expected = {n: h for n, h in enumerate(headers)}
    require(rows and rows[0][0] == 1 and {n: v[0] for n, v in rows[0][1].items()} == expected,
            f'「{name}」第 1 行表头应为: ' + ', '.join(headers))
    records = []
    for row_number, cells in rows[1:]:
        require(all(n < len(headers) for n in cells), f'「{name}」第 {row_number} 行有多余列')
        record = {h: cells.get(n, ('', 's'))[0].strip() for n, h in enumerate(headers)}
        if not any(record.values()):
            continue
        record['_row'] = row_number
        record['_types'] = {h: cells.get(n, ('', 's'))[1] for n, h in enumerate(headers)}
        records.append(record)
    return records


def reference_lookup(rows, id_key, name_key, kind):
    lookup = defaultdict(set)
    for row in rows:
        identifier = row[id_key]
        require(re.fullmatch(r'[A-Za-z0-9_-]+', identifier), f'{kind}: ID 不能为空且只能含字母、数字、_、-: {identifier!r}')
        lookup[identifier].add(identifier)
        if row[name_key]:
            lookup[row[name_key]].add(identifier)

    def resolve(value, context, optional=False):
        if not value and optional:
            return ''
        matches = lookup.get(value, set())
        require(len(matches) == 1, f'{context}: {kind} {value!r} 不存在或名称重复，请填写唯一名称或 ID')
        return next(iter(matches))
    return resolve


def csv_bytes(headers, rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, headers, extrasaction='ignore', lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8-sig')


def release_date(value, kind, date1904, context):
    if not value:
        return ''
    if kind == 'n':
        serial = float(value)
        require(math.isfinite(serial) and serial.is_integer() and 0 <= serial < 2958466,
                f'{context}: 实装日期必须是日期，不能含时间')
        require(date1904 or serial != 60, f'{context}: Excel 的 1900-02-29 不是真实日期')
        epoch = date(1904, 1, 1) if date1904 else date(1899, 12, 31)
        try:
            return (epoch + timedelta(days=int(serial) - (not date1904 and serial > 60))).isoformat()
        except OverflowError:
            raise ValueError(f'{context}: 实装日期超出范围') from None
    if kind == 'd':
        require(re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}(?:T00:00:00(?:\.0+)?Z?)?', value),
                f'{context}: 实装日期不能含时间或时区偏移')
        value = value[:10]
    require(re.fullmatch(r'[0-9]{4}([-/])[0-9]{2}\1[0-9]{2}', value),
            f'{context}: 实装日期应为 YYYY-MM-DD 或 YYYY/MM/DD')
    try:
        return date.fromisoformat(value.replace('/', '-')).isoformat()
    except ValueError:
        raise ValueError(f'{context}: 无效实装日期 {value!r}') from None


def workbook_sources(path):
    workbook, date1904 = read_workbook(path)
    tables = {key: sheet_records(workbook, name, prepare_data.INPUTS[key][1].split())
              for key, name in SHEETS.items()}
    group_ref = reference_lookup(tables['groups'], 'group_id', 'name', '公司')
    unit_ref = reference_lookup(tables['units'], 'unit_id', 'name', '组合')
    character_ref = reference_lookup(tables['characters'], 'character_id', 'display_name', '人物')
    for key in ('groups', 'units', 'characters'):
        for row in tables[key]:
            row['background_color'] = row['background_color'].upper()
    for row in tables['units']:
        context = f'「组合」第 {row["_row"]} 行'
        row['group_id'] = group_ref(row['group_id'], context)
        row['parent_unit_id'] = unit_ref(row['parent_unit_id'], context, True)
    for row in tables['character_units']:
        context = f'「组合成员」第 {row["_row"]} 行'
        row['unit_id'] = unit_ref(row['unit_id'], context)
        row['character_id'] = character_ref(row['character_id'], context)
    units = {r['unit_id']: r for r in tables['units']}
    for row in tables['labels']:
        row['unit_id'] = unit_ref(row['unit_id'], f'「标签」第 {row["_row"]} 行', True)
    label_ref = reference_lookup([
        {**r, 'resolved_name': units[r['unit_id']]['name'] if r['unit_id'] else r['name']}
        for r in tables['labels']], 'label_id', 'resolved_name', '标签')
    for row in tables['frequency_colors']:
        row['font_color'] = row['font_color'].upper()
    settings = sheet_records(workbook, '显示设置', ['key', 'value'])
    require(len(settings) == 2 and {r['key'] for r in settings} == {'character_font_family', 'character_text_color'},
            '「显示设置」必须各包含一条 character_font_family 和 character_text_color')
    display = {r['key']: r['value'] for r in settings}
    display['character_text_color'] = display['character_text_color'].upper()
    display['song_background_overrides'] = {}
    tables['songs'], tables['song_labels'], tables['positions'] = [], [], []
    song_rows = sheet_records(workbook, '歌曲', SONG_HEADERS)
    allocated = {row['song_id'] for row in song_rows if row['song_id']}
    assigned = {}
    for row in song_rows:
        sid = row['song_id']
        context = f'「歌曲」第 {row["_row"]} 行（{row["歌曲名称"] or sid}）'
        if not sid:
            sid = 'song_' + uuid.uuid4().hex[:12]
            while sid in allocated:
                sid = 'song_' + uuid.uuid4().hex[:12]
            allocated.add(sid)
            assigned[row['_row']] = sid
        require(re.fullmatch(r'[A-Za-z0-9_-]+', sid), f'{context}: song_id 只能含字母、数字、_、-')
        tables['songs'].append(dict(song_id=sid, title=row['歌曲名称'], combination_raw=row['数字组合原文'],
                                   release_date=release_date(row['实装日期'], row['_types']['实装日期'], date1904, context)))
        raw_labels = row[SONG_HEADERS[4]].replace('｜', '|').split('|')
        require(all(item.strip() for item in raw_labels), f'{context}: 标签必填，多个标签用 | 分隔，不能有空项')
        for order, value in enumerate(raw_labels, 1):
            tables['song_labels'].append(dict(song_id=sid, label_id=label_ref(value.strip(), context), tag_order=order))
        for n in range(1, 11):
            performer, label = row[f'{n}号位'], row[f'{n}号位标签']
            require(performer or not label, f'{context}: {n}号位为空，不能填写该位置的标签')
            if not performer:
                continue
            free = performer in ('自由', 'free')
            tables['positions'].append(dict(song_id=sid, position=n,
                character_id='' if free else character_ref(performer, f'{context} {n}号位'),
                slot_type='free' if free else 'fixed', label_id=label_ref(label, context, True)))
        if row['特殊底色']:
            display['song_background_overrides'][sid] = row['特殊底色'].upper()
    require(bool(tables['songs']), '「歌曲」没有任何歌曲，请检查工作表内容')
    result = {f'{key}.csv': csv_bytes(prepare_data.INPUTS[key][1].split(), rows) for key, rows in tables.items()}
    result['display.json'] = prepare_data.json_bytes(display)
    return result, assigned


def fill_workbook_ids(content, assigned):
    """Patch only blank ID cells, keeping all other XLSX parts and XML intact.

    Do not reserialize the entire worksheet with ElementTree: that would rename
    namespace prefixes referenced by Excel extension metadata (mc:Ignorable).
    """
    with ZipFile(io.BytesIO(content)) as source:
        workbook = ET.fromstring(source.read('xl/workbook.xml'))
        rels = ET.fromstring(source.read('xl/_rels/workbook.xml.rels'))
        sheet = next(s for s in workbook.findall('s:sheets/s:sheet', NS) if s.get('name') == '歌曲')
        target = next(r.get('Target') for r in rels if r.get('Id') == sheet.get(REL))
        target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
        original_xml = source.read(target).decode('utf-8')
        changed = set()
        prefix = r'(?:[\w.-]+:)?'
        row_pattern = rf'<(?P<tag>{prefix}row)\b(?P<attrs>[^>]*)>(?P<body>.*?)</(?P=tag)>'

        def replace_row(match):
            number = re.search(r'\br=[\"\']([0-9]+)[\"\']', match['attrs'])
            if number is None or int(number[1]) not in assigned:
                return match[0]
            row_number = int(number[1])
            sid = assigned[row_number]
            cell_prefix = match['tag'][:-3]
            address = f'A{row_number}'
            body = match['body']
            found = False

            def new_cell(attrs):
                attrs = re.sub(r'\s+t=[\"\'][^\"\']*[\"\']', '', attrs).rstrip(' /')
                return (f'<{cell_prefix}c{attrs} t="inlineStr"><{cell_prefix}is>'
                        f'<{cell_prefix}t>{escape(sid)}</{cell_prefix}t></{cell_prefix}is></{cell_prefix}c>')

            def replace_cell(cell):
                nonlocal found
                if not re.search(rf'\br=[\"\']{address}[\"\']', cell['attrs']):
                    return cell[0]
                require(not found, f'歌曲 {address}: 重复单元格')
                found = True
                return new_cell(cell['attrs'])

            cell_pattern = rf'<(?P<tag>{prefix}c)\b(?P<attrs>[^>]*?)(?:\s*/>|>.*?</(?P=tag)>)'
            body = re.sub(cell_pattern, replace_cell, body, flags=re.DOTALL)
            if not found:
                body = new_cell(f' r="{address}"') + body
            changed.add(row_number)
            return f'<{match["tag"]}{match["attrs"]}>{body}</{match["tag"]}>'

        updated_xml = re.sub(row_pattern, replace_row, original_xml, flags=re.DOTALL)
        require(changed == set(assigned), '无法定位所有待回填 ID 的歌曲行')
        result = io.BytesIO()
        with ZipFile(result, 'w') as output:
            output.comment = source.comment
            for entry in source.infolist():
                output.writestr(entry, updated_xml.encode('utf-8') if entry.filename == target else source.read(entry.filename))
        return result.getvalue()


def fill_placement_ids(content, songs):
    """Use an exact, unique title only for rows whose song_id is blank."""
    reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig'), newline=''))
    headers = prepare_data.INPUTS['song_placements'][1].split()
    require(reader.fieldnames == headers, f'song_placements.csv: expected headers {headers}')
    rows = list(reader)
    by_title = defaultdict(list)
    for song in songs:
        by_title[song['title']].append(song['song_id'])
    count = 0
    for number, row in enumerate(rows, 2):
        require(None not in row and all(v is not None for v in row.values()), f'song_placements.csv 第 {number} 条记录格式不正确')
        if row['song_id'].strip():
            continue
        matches = by_title[row['title'].strip()]
        require(len(matches) == 1, f'song_placements.csv 第 {number} 条记录: 歌名 {row["title"]!r} 不存在或不唯一，无法填写 song_id')
        row['song_id'] = matches[0]
        count += 1
    return csv_bytes(headers, rows) if count else content


def prepare(source):
    """Validate everything in a temporary directory before touching live files."""
    try:
        workbook_content = (source / 'maintenance.xlsx').read_bytes()
    except FileNotFoundError as error:
        raise ValueError(f'无法读取维护表 {source / "maintenance.xlsx"}') from error
    files, assigned = workbook_sources(io.BytesIO(workbook_content))
    songs = list(csv.DictReader(io.StringIO(files['songs.csv'].decode('utf-8-sig'))))
    original_placements = (source / 'song_placements.csv').read_bytes()
    placements = fill_placement_ids(original_placements, songs)
    with tempfile.TemporaryDirectory(prefix='escoop-validate-') as directory:
        stage = Path(directory)
        for name, content in {**files, 'song_placements.csv': placements}.items():
            (stage / name).write_bytes(content)
        outputs = prepare_data.build(stage)
    if assigned:
        files['maintenance.xlsx'] = fill_workbook_ids(workbook_content, assigned)
        # Validate the patched archive before committing it alongside generated data.
        roundtrip, pending = workbook_sources(io.BytesIO(files['maintenance.xlsx']))
        require(not pending and all(roundtrip[name] == data for name, data in files.items() if name != 'maintenance.xlsx'),
                '回填 ID 后工作簿校验不一致')
    if placements != original_placements:
        files['song_placements.csv'] = placements
    return files, outputs


def write_transaction(changes):
    """Stage replacements; roll back earlier files if a later replacement fails."""
    staged, originals, replaced = {}, {}, []
    try:
        for path, content in changes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                # Detect Excel's write lock before any generated file is changed.
                with path.open('r+b') as stream:
                    originals[path] = stream.read()
            else:
                originals[path] = None
            fd, temporary = tempfile.mkstemp(prefix='.maintenance-', dir=path.parent)
            staged[path] = Path(temporary)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(content)
        for path, temporary in staged.items():
            os.replace(temporary, path)
            replaced.append(path)
    except OSError as error:
        for path in reversed(replaced):
            if originals[path] is None:
                path.unlink()
            else:
                staged[path].write_bytes(originals[path])
                os.replace(staged[path], path)
        raise OSError('无法更新生成文件；请保存并关闭占用相关文件的 Excel 等程序后重试。' + str(error)) from error
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)


def sync(source=prepare_data.SOURCE, output=prepare_data.OUT, check=False):
    files, outputs = prepare(source)
    changes = {}
    for root, content_map in ((source, files), (output, outputs)):
        for name, content in content_map.items():
            path = root / name
            before = path.read_bytes() if path.exists() else None
            if before is not None and root == source and path.suffix != '.xlsx':
                before = before.replace(b'\r\n', b'\n')
            if before != content:
                changes[path] = content
    require(not check or not changes,
            '生成文件尚未同步，请运行 python scripts/import_maintenance.py: ' + ', '.join(str(p) for p in changes))
    if not check:
        write_transaction(changes)
    return {'mode': 'check' if check else 'import', 'changed_files': len(changes),
            'songs': json.loads(outputs['validation.json'])['table_counts']['songs']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate workbook and detect stale outputs without writing')
    args = parser.parse_args()
    try:
        print(json.dumps(sync(check=args.check), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, ET.ParseError) as error:
        parser.exit(1, f'导入失败: {error}\n')


if __name__ == '__main__':
    main()
