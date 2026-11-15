import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createSelection, selectSongs, visibleMembers } from '../src/lib/catalog.mjs';
import { matchesSong, encodeAssetPath } from '../src/lib/song-data.mjs';

const site = JSON.parse(readFileSync(new URL('../data/normalized/site_data.json', import.meta.url)));
const unit = name => site.units.find(u => u.name === name);
test('initial state and reset return every song once', () => {
  const state = createSelection();
  state.combinations.push('12');
  const songs = selectSongs(site, createSelection());
  assert.equal(songs.length, 333);
  assert.equal(new Set(songs.map(s => s.id)).size, 333);
  assert.equal(songs[0].unitIds[0], site.groups[0].unitIds[0]);
});
test('unit AND filters find collaborations without duplicate rows', () => {
  const units = [unit('Trickstar').id, unit('fine').id];
  const result = selectSongs(site, { ...createSelection(), unitIds: units });
  assert.ok(result.some(s => s.title === 'Crossing×Heart'));
  assert.ok(result.every(s => units.every(id => s.unitIds.includes(id))));
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
test('expanding a unit reveals members without adding a song filter', () => {
  const state = createSelection();
  assert.equal(visibleMembers(site, state, [unit('fine').id]).length, 4);
  assert.equal(selectSongs(site, state).length, 333);
  assert.deepEqual(state.unitIds, []);
});
test('combination filters match exact tokens and all requested values', () => {
  const song = { unitIds: [], positions: [], combinations: [{ value: '123' }] };
  assert.equal(matchesSong(song, { combinations: ['12'] }), false);
  const result = selectSongs(site, { ...createSelection(), combinations: ['12', '34'] });
  assert.ok(result.length);
  assert.ok(result.every(s => ['12', '34'].every(value => s.combinations.some(c => c.value === value))));
});
test('free slots accept distinct members but empty slots do not', () => {
  const song = { unitIds: [], positions: [{ kind: 'fixed', characterId: 'a' }, { kind: 'free' }, { kind: 'empty' }], combinations: [] };
  assert.equal(matchesSong(song, { characterIds: ['a', 'b', 'b'] }), true);
  assert.equal(matchesSong(song, { characterIds: ['a', 'b', 'c'] }), false);
});
test('all seven custom Other song colors survive data generation', () => {
  for (const [title, color] of [['Genuine Revelation', '#FFD7A0'], ['Dawning Angels', '#FFD7A0'], ['圣少年游戯', '#8C2346'], ['We\'ll be"Knights"', '#305DAA'], ['Crush of Judgment', '#305DAA'], ['Death Game Holic', '#64368F'], ['ROCK ROAR', '#64368F']]) {
    assert.equal(site.songs.find(s => s.title === title).backgroundCss, color);
  }
  assert.ok(site.songs.find(s => s.title === 'Crossing×Heart').backgroundCss.startsWith('linear-gradient'));
});
test('literal percent signs in logo filenames remain intact', () => {
  assert.equal(encodeAssetPath('images/other/Jin_%26_Akiomi_logo_cropped.webp'), 'images/other/Jin_%2526_Akiomi_logo_cropped.webp');
});
