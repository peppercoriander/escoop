"""Build disposable site data solely from the corrected tables in data/source.

No legacy import, title patch, membership patch, or inferred formation ordering.
Run normally to generate; --check validates inputs and detects stale outputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/source'
OUT = ROOT / 'data/normalized'
INPUTS = {
    'groups': ('公司与Other', 'group_id name kind icon_path sort_order background_color'),
    'units': ('Unit', 'unit_id name background_color icon_path group_id parent_unit_id kind sort_order'),
    'characters': ('人物', 'character_id display_name background_color'),
    'character_units': ('人物Unit关系', 'character_id unit_id sort_order'),
    'songs': ('歌曲', 'song_id title combination_raw'),
    'labels': ('分类', 'label_id unit_id name'),
    'song_labels': ('歌曲分类顺序', 'song_id label_id tag_order'),
    'positions': ('歌曲站位', 'song_id position character_id slot_type label_id'),
    'frequency_colors': ('次数颜色规则', 'min_count max_count font_color name'),
}
NUMBERS = {'sort_order', 'row_order', 'tag_order', 'position', 'min_count', 'max_count'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(rows, *keys):
    values = [tuple(r[k] for k in keys) for r in rows]
    require(len(values) == len(set(values)), f'Duplicate key: {keys}')


def index(rows, key):
    unique(rows, key)
    require(all(r[key] for r in rows), f'Empty key: {key}')
    return {r[key]: r for r in rows}


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def build(source=SOURCE):
    tables, schemas = {}, {}
    for key, (sheet, columns) in INPUTS.items():
        columns = columns.split()
        with (source / f'{key}.csv').open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            require(reader.fieldnames == columns, f'{key}: expected headers {columns}')
            rows = list(reader)
        for row in rows:
            require(None not in row and all(v is not None for v in row.values()), f'{key}: invalid CSV row')
            required = {'character_units': ['character_id', 'unit_id'], 'song_labels': ['song_id', 'label_id'],
                        'positions': ['song_id']}.get(key, [])
            require(all(row[field] for field in required), f'{key}: missing relationship key')
            for field in NUMBERS.intersection(columns):
                row[field] = int(row[field]) if row[field] else None
                require(row[field] is not None or field == 'max_count', f'{key}: empty {field}')
        tables[key] = rows
        schemas[key] = {'sheet_name': sheet, 'columns': columns}
    display = json.loads((source / 'display.json').read_text(encoding='utf-8'))
    require(bool(display['character_font_family']), 'Missing character font')
    require(re.fullmatch(r'#[0-9A-F]{6}', display['character_text_color']), 'Invalid text color')
    groups = index(tables['groups'], 'group_id')
    units = index(tables['units'], 'unit_id')
    chars = index(tables['characters'], 'character_id')
    songs = index(tables['songs'], 'song_id')
    overrides = display.get('song_background_overrides', {})
    require(all(sid in songs and re.fullmatch(r'#[0-9A-F]{6}', color)
                for sid, color in overrides.items()), 'Invalid song background override')
    labels = index(tables['labels'], 'label_id')
    combinations = {sid:dict(song_id=sid, raw_text=song.pop('combination_raw')) for sid,song in songs.items()}
    schemas['songs']['columns'].remove('combination_raw')
    unique(tables['songs'], 'title')
    unique(tables['characters'], 'display_name')
    unique(tables['units'], 'name')
    unique(tables['groups'], 'sort_order')
    unique(tables['units'], 'group_id', 'sort_order')
    unique(tables['character_units'], 'character_id', 'unit_id')
    unique(tables['character_units'], 'unit_id', 'sort_order')
    unique(tables['song_labels'], 'song_id', 'label_id')
    unique(tables['song_labels'], 'song_id', 'tag_order')
    unique(tables['positions'], 'song_id', 'position')
    for table in tables.values():
        for row in table:
            for key, lookup in [('song_id', songs), ('unit_id', units), ('character_id', chars), ('group_id', groups), ('label_id', labels)]:
                require(not row.get(key) or row[key] in lookup, f'Unknown {key}: {row.get(key)}')
    for row in tables['songs']:
        require(bool(row['title'].strip()), 'Empty song title')
    for row in tables['groups'] + tables['units'] + tables['characters']:
        for field in ['background_color', 'text_color']:
            value = row.get(field)
            require(not value or re.fullmatch(r'#[0-9A-F]{6}', value), f'Invalid {field}: {value}')
    for unit in units.values():
        require(bool(unit['background_color']) and unit['group_id'] in groups, f'Incomplete unit: {unit["name"]}')
        parent = unit['parent_unit_id']
        require(not parent or (parent in units and parent != unit['unit_id'] and
                not units[parent]['parent_unit_id'] and units[parent]['group_id'] == unit['group_id']), 'Invalid parent unit')
    for label in labels.values():
        if label['unit_id']:
            unit = units[label['unit_id']]
            require(not label['name'], 'Unit label names are derived; leave name blank')
            label['name'] = unit['name']
            label['group_id'] = unit['group_id']
            label['kind'] = unit['kind']
        else:
            require(bool(label['name']), 'Other labels need a name')
            label['group_id'] = 'group_other'
            label['kind'] = 'category' if label['name'] == groups['group_other']['name'] else 'other_tag'
    unique([label for label in labels.values() if label['unit_id']], 'unit_id')
    schemas['labels']['columns'] += ['kind', 'group_id']
    assets = [r['icon_path'] for r in tables['groups'] + tables['units']]
    for asset in assets:
        require(bool(asset) and (ROOT / asset).is_file(), f'Missing logo: {asset}')
    for character in chars.values():
        require(bool(character['display_name']) and bool(character['background_color']), 'Incomplete character')
        character['text_color'] = display['character_text_color']
        character['font_family'] = display['character_font_family']
    schemas['characters']['columns'] += ['text_color', 'font_family']

    menu_rows = []
    for group in sorted(groups.values(), key=lambda r: r['sort_order']):
        ids = [u['unit_id'] for u in sorted(units.values(), key=lambda u: u['sort_order']) if u['group_id'] == group['group_id']]
        menu_rows.append({'group_id': group['group_id'], 'unit_ids': ids})
    for row in tables['character_units']:
        require(row['character_id'] in chars and row['unit_id'] in units and row['sort_order'] > 0, 'Invalid member relationship')
    require(all(r['sort_order'] > 0 for r in tables['groups'] + tables['units']), 'Menu order must be positive')
    rules = sorted(tables['frequency_colors'], key=lambda r: r['min_count'])
    expected = 1
    for i, rule in enumerate(rules):
        require(rule['min_count'] == expected, 'Frequency rules must be contiguous')
        require(re.fullmatch(r'#[0-9A-F]{6}', rule['font_color']), 'Invalid frequency color')
        maximum = rule['max_count']
        require((maximum is None and i == len(rules)-1) or
                (maximum is not None and maximum >= expected and i < len(rules)-1), 'Invalid frequency interval')
        expected = maximum + 1 if maximum is not None else None
    require(bool(rules) and expected is None, 'Frequency rules need an open final interval')
    positions, tags = defaultdict(list), defaultdict(list)
    for row in tables['positions']:
        positions[row['song_id']].append(row)
    for row in tables['song_labels']:
        tags[row['song_id']].append(row)
    original_positions = tables['positions']
    tables['positions'] = []
    tables['song_combination_sources'] = list(combinations.values())
    schemas['song_combination_sources'] = {'sheet_name':'歌曲组合来源', 'columns':['song_id', 'raw_text', 'status']}
    for key, sheet, columns in [
        ('song_units', '歌曲Unit关系', 'song_id unit_id unit_order tag_order'),
        ('combination_counts', '站位组合次数', 'song_id combination count first_seen_order font_color'),
        ('song_color_bands', '歌曲分色', 'song_id band_order unit_id label_id color start_percent end_percent'),
        ('combination_options', '站位选项', 'value positions song_count sort_order'),
        ('issues', '待补充', 'kind entity_id source_file detail'),
    ]:
        tables[key] = []
        schemas[key] = {'sheet_name': sheet, 'columns': columns.split()}
    schemas['positions']['columns'] = 'song_id position character_id display_name slot_type unit_id label_id'.split()
    schemas['songs']['columns'] += 'unit_config formation_kind position_count layout_status combination_status background_css'.split()

    def issue(kind, sid, file, detail):
        tables['issues'].append(dict(kind=kind, entity_id=sid,
            source_file=f'data/source/{file}.csv', detail=detail))

    for group in groups.values():
        if not group['background_color']:
            issue('missing_group_color', group['group_id'], 'groups', f'{group["name"]} 的代表色尚未提供；网页可先使用中性样式。')

    site_songs = []
    for sid, song in songs.items():
        ordered_tags = sorted(tags[sid], key=lambda r: r['tag_order'])
        require(bool(ordered_tags) and [r['tag_order'] for r in ordered_tags] == list(range(1, len(ordered_tags)+1)), f'Invalid tag order: {song["title"]}')
        lids = [r['label_id'] for r in ordered_tags]
        uids = list(dict.fromkeys(labels[lid]['unit_id'] for lid in lids if labels[lid]['unit_id']))
        for lid in lids:
            uid = labels[lid]['unit_id']
            if uid:
                require(not any(r['song_id'] == sid and r['unit_id'] == uid for r in tables['song_units']), 'Repeated unit tag')
                tables['song_units'].append(dict(song_id=sid, unit_id=uid, unit_order=uids.index(uid)+1, tag_order=lids.index(lid)+1))
        supplied = positions[sid]
        require(all(1 <= p['position'] <= 10 and p['slot_type'] in ('fixed', 'free') for p in supplied), f'Only filled positions 1–10 belong in the source: {song["title"]}')
        by_position = {p['position']:p for p in supplied}
        slots = [by_position.get(n, dict(song_id=sid, position=n, character_id='', slot_type='empty', label_id='')) for n in range(1,11)]
        for p in slots:
            require(p['slot_type'] in ('fixed', 'free', 'empty'), 'Unknown slot type')
            require(bool(p['character_id']) == (p['slot_type'] == 'fixed'), 'Fixed slots need a character; other slots must not have one')
            require(not p['label_id'] or p['label_id'] in lids, f'Position tag outside song: {song["title"]}')
            require(p['slot_type'] != 'empty' or not p['label_id'], 'Empty slot cannot own a tag')
            p['display_name'] = chars[p['character_id']]['display_name'] if p['character_id'] else str(p['position']) if p['slot_type'] == 'free' else ''
            p['unit_id'] = labels[p['label_id']]['unit_id'] if p['label_id'] else ''
        fixed = [p['character_id'] for p in slots if p['character_id']]
        require(len(fixed) == len(set(fixed)), f'Duplicate performer: {song["title"]}')
        filled = [p for p in slots if p['slot_type'] != 'empty']
        free = sum(p['slot_type'] == 'free' for p in filled)
        formation = 'unknown' if not filled else 'free' if free == len(filled) else 'mixed' if free else 'fixed'
        layout_status = 'complete' if filled else 'missing_positions'
        if not filled:
            issue('missing_positions', sid, 'positions', f'《{song["title"]}》站位正在录入。')
        tables['positions'].extend(slots)
        tokens = [t for t in re.split(r'[\s,，]+', combinations[sid]['raw_text'].strip()) if t]
        require('无' not in tokens or tokens == ['无'], f'Cannot mix 无 with combinations: {song["title"]}')
        counts = Counter()
        first = {}
        for token_index, token in enumerate(tokens, 1):
            if token in ('无', '?', '？'):
                continue
            require(re.fullmatch(r'[1-9]{2,}', token) and len(set(token)) == len(token), f'Invalid combination {token}: {song["title"]}')
            require(all(slots[int(d)-1]['slot_type'] != 'empty' for d in token), f'Combination references empty position: {song["title"]}')
            first.setdefault(token, token_index)
            counts[token] += 1
        status = 'missing' if not tokens else 'none' if tokens == ['无'] else 'partial' if any(t in ('?', '？') for t in tokens) else 'recorded'
        combinations[sid]['status'] = status
        if status in ('missing', 'partial'):
            issue('missing_combinations' if status == 'missing' else 'uncertain_combinations', sid, 'songs',
                  f'《{song["title"]}》' + ('数字组合原始序列正在录入。' if status == 'missing' else '原文含问号。'))
        counted = []
        for token, count in counts.items():
            color = next(r['font_color'] for r in rules if r['min_count'] <= count and (r['max_count'] is None or count <= r['max_count']))
            counted.append(dict(song_id=sid, combination=token, count=count, first_seen_order=first[token], font_color=color))
        tables['combination_counts'].extend(counted)
        parents = {units[uid]['parent_unit_id'] for uid in uids}
        leaf = [lid for lid in lids if labels[lid]['unit_id'] and labels[lid]['unit_id'] not in parents]
        assigned = {p['label_id'] for p in filled if p['label_id']}
        color_labels = [lid for lid in lids if lid in leaf or (lid in assigned and not labels[lid]['unit_id'])]
        if not color_labels:
            color_labels = [next((lid for lid in lids if labels[lid]['kind'] == 'category'), lids[0])]
        bands = []
        for i, lid in enumerate(color_labels):
            label = labels[lid]
            uid = label['unit_id']
            color = overrides.get(sid) or (units[uid]['background_color'] if uid else groups[label['group_id']]['background_color'])
            require(bool(color), f'Missing song color: {song["title"]}')
            bands.append(dict(song_id=sid, band_order=i+1, unit_id=uid, label_id=lid, color=color,
                              start_percent=100*i/len(color_labels), end_percent=100*(i+1)/len(color_labels)))
        tables['song_color_bands'].extend(bands)
        css = bands[0]['color'] if len(bands) == 1 else 'linear-gradient(135deg, ' + ', '.join(f"{b['color']} {b['start_percent']:g}%, {b['color']} {b['end_percent']:g}%" for b in bands) + ')'
        config = ', '.join(labels[lid]['name'] for lid in lids)
        song.update(unit_config=config, formation_kind=formation, position_count=len(filled), layout_status=layout_status, combination_status=status, background_css=css)
        site_songs.append(dict(id=sid, title=song['title'], unitIds=uids, labelIds=lids, unitConfig=config,
            positions=[dict(position=p['position'], characterId=p['character_id'] or None, label=p['display_name'], kind=p['slot_type'], unitId=p['unit_id'] or None) for p in slots],
            combinations=[dict(value=c['combination'], count=c['count'], color=c['font_color']) for c in counted],
            backgroundCss=css, colors=[b['color'] for b in bands], formationKind=formation, layoutStatus=layout_status, combinationStatus=status))
    option_counts = Counter(c['combination'] for c in tables['combination_counts'])
    for order, token in enumerate(sorted(option_counts, key=lambda token:(len(token), int(token))), 1):
        tables['combination_options'].append(dict(value=token, positions=json.dumps([int(d) for d in token]),
                                                 song_count=option_counts[token], sort_order=order))
    summary = {
        'table_counts': {k:len(v) for k,v in tables.items()},
        'combination_status': dict(Counter(r['status'] for r in tables['song_combination_sources'])),
        'issue_counts': dict(Counter(r['kind'] for r in tables['issues'])),
        'free_position_cells': sum(p['slot_type'] == 'free' for p in original_positions),
        'formation_kinds': dict(Counter(s['formation_kind'] for s in songs.values())),
        'split_color_songs': sum(len(s['colors']) > 1 for s in site_songs),
        'distinct_combinations': len({c['combination'] for c in tables['combination_counts']}),
        'characters_with_color_and_unit': sum(any(r['character_id'] == cid for r in tables['character_units']) for cid in chars),
        'multi_unit_characters': sum(n > 1 for n in Counter(r['character_id'] for r in tables['character_units']).values()),
        'verified_logo_files': len(assets),
        'validation': 'Canonical source keys, relationships, ordered positions, combination counts and logos verified.',
    }
    site = dict(schemaVersion=3,
        display=dict(characterFontFamily=display['character_font_family'], characterTextColor=display['character_text_color']),
        groups=[dict(id=r['group_id'], name=groups[r['group_id']]['name'], color=groups[r['group_id']]['background_color'] or None,
                     iconPath=groups[r['group_id']]['icon_path'], unitIds=r['unit_ids']) for r in menu_rows],
        units=[dict(id=u['unit_id'], name=u['name'], color=u['background_color'], iconPath=u['icon_path'],
                    characterIds=[r['character_id'] for r in sorted(tables['character_units'], key=lambda r:r['sort_order']) if r['unit_id']==u['unit_id']]) for u in units.values()],
        characters=[dict(id=c['character_id'], name=c['display_name'], color=c['background_color']) for c in chars.values()],
        frequencyColors=[dict(minCount=r['min_count'], maxCount=r['max_count'], color=r['font_color']) for r in rules],
        combinationOptions=[dict(value=r['value'], positions=json.loads(r['positions']), songCount=r['song_count']) for r in tables['combination_options']],
        songs=site_songs)
    inputs = [f'{k}.csv' for k in INPUTS] + ['display.json']
    payload = dict(schema_version=6, maintenance_source='data/source',
        source_sha256={f'data/source/{name}':hashlib.sha256((source / name).read_bytes()).hexdigest() for name in inputs},
        display=display, summary=summary, schemas=schemas, tables=tables)
    outputs = {'dataset.json':json_bytes(payload), 'validation.json':json_bytes(summary),
               'site_data.json':json_bytes(site)}
    for key, rows in tables.items():
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fieldnames=schemas[key]['columns'])
        writer.writeheader()
        writer.writerows(rows)
        outputs[f'{key}.csv'] = stream.getvalue().encode('utf-8-sig')
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate and check generated outputs without writing')
    args = parser.parse_args()
    outputs = build()
    stale = [name for name, content in outputs.items() if not (OUT / name).exists() or (OUT / name).read_bytes() != content]
    if args.check:
        require(not stale, 'Generated outputs need rebuilding: ' + ', '.join(stale))
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for name in stale:
            (OUT / name).write_bytes(outputs[name])
    print(json.dumps({'mode':'check' if args.check else 'build', 'changed_files':len(stale),
                      'summary':json.loads(outputs['validation.json'])}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
