import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createSelection, selectSongs, selectSongRows, visibleMembers, toggleSelection, createCatalogState, toggleCatalogState, positionOptions } from '../src/lib/catalog.mjs';
import { matchesSong, encodeAssetPath } from '../src/lib/song-data.mjs';

const site = JSON.parse(readFileSync(new URL('../data/normalized/site_data.json', import.meta.url)));
const unit = name => site.units.find(u => u.name === name);
test('initial state and reset return every song once', () => {
  const state = createSelection();
  state.combinations.push('12');
  const songs = selectSongs(site, createSelection());
  assert.equal(songs.length, site.songs.length);
  assert.deepEqual(new Set(songs.map(s => s.id)), new Set(site.songs.map(s => s.id)));
  assert.equal(songs[0].unitIds[0], site.groups[0].unitIds[0]);
});
test('unit AND filters find collaborations without duplicate rows', () => {
  const units = [unit('Trickstar').id, unit('fine').id];
  const result = selectSongs(site, { ...createSelection(), unitIds: units });
  assert.ok(result.some(s => s.title === 'Crossing×Heart'));
  assert.ok(result.every(s => units.every(id => s.unitIds.includes(id))));
});

test('all placements render while song counts remain unique', () => {
  const rows = selectSongRows(site, createSelection());
  assert.equal(rows.length, site.songPlacements.length);
  assert.equal(new Set(rows.map(row => row.song.id)).size, site.songs.length);
  assert.equal(new Set(rows.map(row => `${row.sectionId}:${row.song.id}`)).size, rows.length);
  const crossing = rows.filter(row => row.song.title === 'Crossing×Heart');
  assert.deepEqual(crossing.map(row => row.section.unit.name), ['fine', 'Trickstar']);
  assert.equal(crossing[0].song, crossing[1].song);
  for (const row of rows) assert.equal(row.section.unit?.id ?? row.section.group.id, row.sectionId);
});

test('every section follows the user order, regardless of CSV row order', () => {
  const reversed = { ...site, songPlacements: [...site.songPlacements].reverse() };
  const rows = selectSongRows(reversed, createSelection());
  const sections = [...new Set(rows.map(row => row.sectionId))];
  const expectedSections = site.groups.flatMap(group => [...group.unitIds, group.id]).filter(id => sections.includes(id));
  assert.deepEqual(sections, expectedSections);
  for (const id of sections) {
    const expected = site.songPlacements.filter(p => p.sectionId === id).sort((a,b) => a.sortOrder - b.sortOrder);
    assert.deepEqual(rows.filter(row => row.sectionId === id).map(row => row.song.id), expected.map(p => p.songId));
  }
  const trickstar = rows.filter(row => row.sectionId === unit('Trickstar').id).map(row => row.song.title);
  assert.equal(trickstar.indexOf('Crossing×Heart'), trickstar.indexOf('虹色のSeasons') + 1);
});

test('a placement edit moves a collaboration within one section only', () => {
  const fine = unit('fine').id;
  const crossing = site.songs.find(s => s.title === 'Crossing×Heart').id;
  const changed = { ...site, songPlacements: site.songPlacements.map(p => p.songId === crossing && p.sectionId === fine ? { ...p, sortOrder: 99999 } : p) };
  const originalRows = selectSongRows(site, createSelection());
  const changedRows = selectSongRows(changed, createSelection());
  assert.equal(changedRows.filter(row => row.sectionId === fine).at(-1).song.id, crossing);
  const otherRows = rows => rows.filter(row => row.sectionId !== fine).map(row => `${row.sectionId}:${row.song.id}`);
  assert.deepEqual(otherRows(changedRows), otherRows(originalRows));
});

test('unit and company filters show only selected sections and preserve AND matching', () => {
  for (const u of site.units) {
    const selection = { ...createSelection(), unitIds: [u.id] };
    const rows = selectSongRows(site, selection);
    assert.ok(rows.every(row => row.sectionId === u.id));
    assert.deepEqual(new Set(rows.map(row => row.song.id)), new Set(selectSongs(site, selection).map(song => song.id)));
  }
  const selection = { ...createSelection(), unitIds: [unit('fine').id, unit('Trickstar').id] };
  const rows = selectSongRows(site, selection);
  assert.equal(rows.length, 2);
  assert.equal(new Set(rows.map(row => row.song.id)).size, 1);
  assert.ok(rows.every(row => row.song.title === 'Crossing×Heart'));
  for (const group of site.groups) {
    const state = { ...createSelection(), groupIds: [group.id] };
    const groupRows = selectSongRows(site, state);
    assert.ok(groupRows.length);
    assert.ok(groupRows.every(row => row.section.group.id === group.id));
    assert.deepEqual(new Set(groupRows.map(row => row.song.id)), new Set(selectSongs(site, state).map(song => song.id)));
  }
});

test('member and position filters apply to every displayed placement', () => {
  const selection = { ...createSelection(), characterIds: [unit('fine').characterIds[0]], combinations: ['25'] };
  const rows = selectSongRows(site, selection);
  assert.ok(rows.length);
  assert.ok(rows.every(row => matchesSong(row.song, selection)));
  assert.ok(rows.every(row => row.song.positions.every(p => p.kind !== 'free')));
  const crossing = rows.filter(row => row.song.title === 'Crossing×Heart');
  assert.equal(crossing.length, 2);
  assert.deepEqual(selectSongRows(site, { ...createSelection(), combinations: ['not-a-position'] }), []);
});
test('company and Other filters include their correct songs', () => {
  for (const group of site.groups) {
    const result = selectSongs(site, { ...createSelection(), groupIds: [group.id] });
    assert.ok(result.length);
    assert.ok(result.every(s => s.unitIds.some(id => group.unitIds.includes(id)) || (!s.unitIds.length && group.id === 'group_other')));
  }
});
test('members deduplicate across units and stay removable after unit deselection', () => {
  const state = { ...createSelection(), unitIds: [unit('Eden').id, unit('Adam').id] };
  assert.equal(visibleMembers(site, state, state.unitIds).length, 4);
  state.characterIds = [unit('Adam').characterIds[0]];
  state.unitIds = [];
  assert.equal(visibleMembers(site, state)[0].id, state.characterIds[0]);
});
test('selecting a unit icon immediately shows its playlist and members', () => {
  const state = toggleSelection(createSelection(), 'unitIds', unit('fine').id);
  assert.equal(visibleMembers(site, state, [unit('fine').id]).length, 4);
  assert.equal(selectSongs(site, state).length, 21);
  assert.ok(selectSongs(site, state).every(song => song.unitIds.includes(unit('fine').id)));
});
test('selecting a member clears company and unit constraints but preserves station choices', () => {
  const before = { ...createSelection(), groupIds: [site.groups[0].id], unitIds: [unit('fine').id], combinations: ['12'] };
  const member = unit('fine').characterIds[0];
  const state = toggleSelection(before, 'characterIds', member);
  assert.deepEqual(state, { groupIds: [], unitIds: [], characterIds: [member], combinations: ['12'] });
  const expectedIds = site.songs.filter(song => matchesSong(song, { characterIds: [member], combinations: ['12'] })).map(song => song.id).sort();
  assert.deepEqual(selectSongs(site, state).map(song => song.id).sort(), expectedIds);
  assert.deepEqual(before.unitIds, [unit('fine').id]);
});
test('switching back to a unit removes member filters, and clicking again deselects it', () => {
  const memberState = { ...createSelection(), characterIds: [unit('Knights').characterIds[0]] };
  const state = toggleSelection(memberState, 'unitIds', unit('fine').id);
  assert.deepEqual(state.characterIds, []);
  assert.equal(selectSongs(site, state).length, 21);
  const resetSongs = selectSongs(site, toggleSelection(state, 'unitIds', unit('fine').id));
  assert.equal(resetSongs.length, site.songs.length);
  assert.deepEqual(new Set(resetSongs.map(song => song.id)), new Set(site.songs.map(song => song.id)));
});
test('combination filters match exact tokens and all requested values', () => {
  const song = { unitIds: [], positions: [], combinations: [{ value: '123' }] };
  assert.equal(matchesSong(song, { combinations: ['12'] }), false);
  const result = selectSongs(site, { ...createSelection(), combinations: ['12', '34'] });
  assert.ok(result.length);
  assert.ok(result.every(s => ['12', '34'].every(value => s.combinations.some(c => c.value === value))));
});

test('position menu excludes 6–10 without removing source options or songs', () => {
  const options = ['12', '15', '16', '56', '123', '345', '10'].map((value, i) => ({ value, positions: i === 6 ? [1, 10] : [...value].map(Number) }));
  assert.deepEqual(positionOptions({ combinationOptions: options }).map(o => o.value), ['12', '15', '123', '345']);
  assert.equal(options.length, 7);
  assert.ok(positionOptions(site).length > 0);
  assert.ok(positionOptions(site).every(o => /^[1-5]+$/.test(o.value)));
  assert.ok(site.combinationOptions.some(o => o.positions.some(p => p > 5)));
});
test('generic and mixed formations never participate in specific-member filtering', () => {
  const song = { unitIds: [], positions: [{ kind: 'fixed', characterId: 'a' }, { kind: 'free' }, { kind: 'empty' }], combinations: [] };
  assert.equal(matchesSong(song, { characterIds: ['a'] }), false);
  assert.equal(matchesSong(song, { characterIds: ['b'] }), false);
  assert.equal(matchesSong(song, { characterIds: ['a', 'b', 'c'] }), false);
  assert.equal(matchesSong(song), true);
  const fixedSong = { ...song, positions: [{ kind: 'fixed', characterId: 'a' }, { kind: 'empty' }] };
  assert.equal(matchesSong(fixedSong, { characterIds: ['a', 'a'] }), true);
  assert.equal(matchesSong(fixedSong, { characterIds: ['a', 'b'] }), false);
});
test('real generic songs remain visible without members but are excluded with members', () => {
  const result = selectSongs(site, { ...createSelection(), characterIds: [unit('fine').characterIds[0]] });
  assert.ok(result.length > 0);
  assert.ok(result.every(song => song.positions.every(position => position.kind !== 'free')));
  assert.ok(selectSongs(site, createSelection()).some(song => song.positions.some(position => position.kind === 'free')));
});
test('deselecting units refreshes members and clears the menu after the last selection', () => {
  let state = toggleCatalogState(site, createCatalogState(), 'unitIds', unit('fine').id);
  state = toggleCatalogState(site, state, 'unitIds', unit('Trickstar').id);
  assert.equal(visibleMembers(site, state.selection, state.expandedUnitIds).length, 8);
  state = toggleCatalogState(site, state, 'unitIds', unit('fine').id);
  assert.deepEqual(visibleMembers(site, state.selection, state.expandedUnitIds).map(c => c.id), unit('Trickstar').characterIds);
  state = toggleCatalogState(site, state, 'unitIds', unit('Trickstar').id);
  assert.deepEqual(visibleMembers(site, state.selection, state.expandedUnitIds), []);
});
test('switching to a company and deselecting it removes the old unit menu', () => {
  let state = toggleCatalogState(site, createCatalogState(), 'unitIds', unit('fine').id);
  state = toggleCatalogState(site, state, 'groupIds', site.groups[1].id);
  assert.deepEqual(state.expandedUnitIds, site.groups[1].unitIds);
  state = toggleCatalogState(site, state, 'groupIds', site.groups[1].id);
  assert.deepEqual(visibleMembers(site, state.selection, state.expandedUnitIds), []);
});
test('selecting members preserves the current menu for additional member choices', () => {
  let state = toggleCatalogState(site, createCatalogState(), 'unitIds', unit('fine').id);
  state = toggleCatalogState(site, state, 'characterIds', unit('fine').characterIds[0]);
  assert.deepEqual(state.selection.unitIds, []);
  assert.equal(visibleMembers(site, state.selection, state.expandedUnitIds).length, 4);
});
test('all seven custom Other song colors survive data generation', () => {
  for (const [title, color] of [['Genuine Revelation', '#FFD7A0'], ['Dawning Angels', '#FFD7A0'], ['圣少年游戯', '#8C2346'], ['We\'ll be"Knights"', '#305DAA'], ['Crush of Judgment', '#305DAA'], ['Death Game Holic', '#64368F'], ['ROCK ROAR', '#64368F']]) {
    assert.equal(site.songs.find(s => s.title === title).backgroundCss, color);
  }
  assert.ok(site.songs.find(s => s.title === 'Crossing×Heart').backgroundCss.startsWith('linear-gradient(135deg,'));
});
test('literal percent signs in logo filenames remain intact', () => {
  assert.equal(encodeAssetPath('images/other/Jin_%26_Akiomi_logo_cropped.webp'), 'images/other/Jin_%2526_Akiomi_logo_cropped.webp');
});
