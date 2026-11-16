import { Fragment, useEffect, useMemo, useState } from 'react';
import { encodeAssetPath, characterCellStyle, songCellStyle, isSongReleased } from './lib/song-data.mjs';
import { createCatalogState, toggleCatalogState, selectSongRows, visibleMembers, positionOptions } from './lib/catalog.mjs';
import FloatingReset from './FloatingReset';
import useTokyoDate from './useTokyoDate';
import type { Group, Selection, SiteData, Unit } from './types';
import styles from './App.module.css';

const cn = (...names: string[]) => names.map(name => styles[name] || '').join(' ');
const asset = (path: string) => `${import.meta.env.BASE_URL}${encodeAssetPath(path)}`;

function Catalog({ site }: { site: SiteData }) {
  const today = useTokyoDate();
  const [catalogState, setCatalogState] = useState(createCatalogState);
  const { selection, expandedUnitIds } = catalogState;
  const [collapsed, setCollapsed] = useState(false);
  const characters = useMemo(() => new Map(site.characters.map(c => [c.id, c])), [site]);
  const units = useMemo(() => new Map(site.units.map(u => [u.id, u])), [site]);
  const rows = useMemo(() => selectSongRows(site, selection), [site, selection]);
  const songCount = new Set(rows.map(row => row.song.id)).size;
  const members = visibleMembers(site, selection, expandedUnitIds);
  const labels = [
    ...site.groups.filter(g => selection.groupIds.includes(g.id)).map(g => g.name),
    ...site.units.filter(u => selection.unitIds.includes(u.id)).map(u => u.name),
    ...selection.characterIds.map(id => characters.get(id)!.name),
    ...selection.combinations.map(value => `站位 ${value}`),
  ];

  function toggle(field: keyof Selection, value: string) {
    setCatalogState(previous => toggleCatalogState(site, previous, field, value));
  }
  function selectUnit(id: string) {
    toggle('unitIds', id);
  }
  function reset() {
    setCatalogState(createCatalogState());
    setCollapsed(false);
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }
  function logo(item: Group | Unit) {
    return <img src={asset(item.iconPath)} alt={item.name} />;
  }

  let previousSection = '';
  return <>
    <section className={cn('filters')} aria-label="歌曲筛选">
      <div className={cn('mobile-filter-toggle')}><span>筛选条件</span><button type="button" aria-expanded={!collapsed} aria-controls="filter-controls" onClick={() => setCollapsed(!collapsed)}>{collapsed ? '展开筛选 ＋' : '收起筛选 −'}</button></div>
      <div id="filter-controls" className={collapsed ? cn('collapsed-controls') : undefined}>
        <section className={cn('filter-section')} aria-labelledby="filter-one-title">
          <div className={cn('section-heading')}><h2 id="filter-one-title"><span className={cn('step')}>01</span> 公司 / 组合 / 成员</h2></div>
          <div className={cn('unit-menu')}>
            {site.groups.map(group => <div className={cn('company-row')} key={group.id}>
              <button type="button" className={cn('logo-button', 'company-button')} aria-label={group.name} aria-pressed={selection.groupIds.includes(group.id)} title={`筛选 ${group.name}`} onClick={() => toggle('groupIds', group.id)}>{logo(group)}</button>
              <div className={cn('unit-list')} role="group" aria-label={`${group.name} 组合`}>
                {group.unitIds.map(id => {
                  const unit = units.get(id)!;
                  const expanded = expandedUnitIds.includes(id), selected = selection.unitIds.includes(id);
                  return <div className={cn('unit-item')} key={id}>
                    <button type="button" className={cn('logo-button')} aria-label={unit.name} aria-pressed={selected} aria-expanded={expanded} aria-controls="member-menu" title={`筛选 ${unit.name} 歌曲并显示成员`} onClick={() => selectUnit(id)}>{logo(unit)}</button>
                  </div>;
                })}
              </div>
            </div>)}
          </div>
          <div className={cn('members-area')}><div className={cn('member-label')}>组合成员 {members.length > 0 && <span>{members.length} 位成员 · 点击筛选</span>}</div>
            <div id="member-menu" className={cn('member-menu')}>{members.map(character => <button type="button" key={character.id} className={cn('member-chip')} style={{ backgroundColor: character.color }} aria-label={`成员 ${character.name}`} aria-pressed={selection.characterIds.includes(character.id)} onClick={() => toggle('characterIds', character.id)}>{character.name}</button>)}</div>
          </div>
        </section>
        <section className={cn('filter-section', 'positions-section')} aria-labelledby="filter-two-title">
          <div className={cn('section-heading')}><h2 id="filter-two-title"><span className={cn('step')}>02</span> 贴贴</h2></div>
          <div className={cn('position-menu')}>{positionOptions(site).map(option => <button type="button" key={option.value} className={cn('position-button')} aria-label={`站位 ${option.value}`} aria-pressed={selection.combinations.includes(option.value)} title={`${option.value} · ${option.songCount} 首歌曲`} onClick={() => toggle('combinations', option.value)}>{option.value}</button>)}</div>
        </section>
      </div>
      <div className={cn('filter-footer')}><div id="selection-summary" className={cn('selection-summary')}>{labels.length ? `已选：${labels.join(' / ')}` : '未设置筛选 · 显示全部歌曲'}</div></div>
    </section>
    <section className={cn('results')} aria-labelledby="results-title">
      <div className={cn('results-toolbar')}><h2 id="results-title">歌曲一览 <span id="result-count" role="status" aria-live="polite">{songCount} / {site.songs.length}</span></h2></div>
      <div className={cn('table-container')} role="region" aria-label="歌曲站位结果表格" hidden={!rows.length}>
        <table><caption className={cn('sr-only')}>处理后的站位信息、歌曲名及按位置排列的成员信息</caption><colgroup><col className={cn('combination-column')} /><col className={cn('song-column')} /><col span={10} className={cn('member-column')} /></colgroup><thead><tr><th rowSpan={2} scope="col">站位信息</th><th className={cn('sticky-song-heading')} rowSpan={2} scope="col">歌曲名</th><th colSpan={10} scope="colgroup">成员信息</th></tr><tr>{Array.from({ length: 10 }, (_, i) => <th key={i} scope="col">{i + 1}</th>)}</tr></thead>
          <tbody>{rows.map(({ song, section, sectionId }) => {
            const released = isSongReleased(song.releaseDate, today);
            const isNew = previousSection !== sectionId;
            previousSection = sectionId;
            return <Fragment key={`${sectionId}:${song.id}`}>
              {isNew && <tr className={cn('group-heading')}><th colSpan={12}>{section.group.name}{section.unit && ` / ${section.unit.name}`}</th></tr>}
              <tr className={cn('song-row')} data-song-id={song.id} data-section-id={sectionId}>
                <td className={cn('combination-cell')}>{song.combinations.map(combo => <span key={combo.value} className={cn('combination', selection.combinations.includes(combo.value) ? 'is-match' : '')} style={{ color: combo.color }} title={`${combo.value} · 出现 ${combo.count} 次`} aria-label={`${combo.value} · 出现 ${combo.count} 次`}>{combo.value}</span>)}{(!song.combinations.length || song.combinationStatus === 'partial') && <span className={cn('pending')}>{song.combinationStatus === 'none' ? '无' : song.combinationStatus === 'partial' ? '部分待确认' : '待录入'}</span>}</td>
                <td className={cn('song-cell')} style={songCellStyle(song)} title={`${song.title} · ${song.unitConfig}`}>{song.title}</td>
                {song.positions.map(position => {
                  const label = `${position.position} 号位 · ${position.kind === 'empty' ? '未录入' : position.kind === 'free' ? '自由站位' : position.label}`;
                  return <td key={position.position} className={cn('character-cell', position.kind)} style={characterCellStyle(position, characters, site.display, released)} title={label} aria-label={label}>{position.kind === 'empty' ? '' : position.label}</td>;
                })}
              </tr>
            </Fragment>;
          })}</tbody>
        </table>
      </div>
      {!rows.length && <div id="empty-state" className={cn('empty-state')}><span aria-hidden="true">∅</span><h3>没有符合条件的歌曲</h3><p>试着减少一个筛选条件，或重置后重新选择。</p><button id="empty-reset" className={cn('reset')} type="button" onClick={reset}>↺ RESET</button></div>}
    </section>
    <FloatingReset onReset={reset} />
  </>;
}

export default function App() {
  const [site, setSite] = useState<SiteData | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${import.meta.env.BASE_URL}data/normalized/site_data.json`, { signal: controller.signal })
      .then(response => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); })
      .then(setSite).catch(reason => { if (reason.name !== 'AbortError') setError(true); });
    return () => controller.abort();
  }, []);
  return <>
    <main>
      <div className={cn('page-heading')}><div><h1>协力站位表<span className={cn('heading-dot')}>.</span></h1></div></div>
      {site ? <Catalog site={site} /> : <div id="loading" role="status">{error ? '资料加载失败，请刷新页面重试。' : '正在加载歌曲资料…'}</div>}
    </main>
  </>;
}
