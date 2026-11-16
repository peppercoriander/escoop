import test from 'node:test';
import assert from 'node:assert/strict';
import { tokyoDate, millisecondsUntilTokyoMidnight, isSongReleased, characterCellStyle } from '../src/lib/song-data.mjs';

test('release dates are inclusive of today; blank and future dates are unreleased', () => {
  const today = '2026-11-16';
  for (const value of [null, undefined, '', '2026-11-17', '2027-01-01']) assert.equal(isSongReleased(value, today), false);
  for (const value of ['2026-11-16', '2026-11-15', '2024-02-29']) assert.equal(isSongReleased(value, today), true);
});

test('Japan midnight flips the release state even while UTC is still the previous day', () => {
  const before = new Date('2026-11-15T14:59:59.999Z');
  const after = new Date('2026-11-15T15:00:00.000Z');
  assert.equal(tokyoDate(before), '2026-11-15');
  assert.equal(tokyoDate(after), '2026-11-16');
  assert.equal(isSongReleased('2026-11-16', tokyoDate(before)), false);
  assert.equal(isSongReleased('2026-11-16', tokyoDate(after)), true);
  assert.equal(millisecondsUntilTokyoMidnight(before), 1);
  assert.equal(millisecondsUntilTokyoMidnight(after), 86400000);
  assert.equal(tokyoDate(new Date('2026-12-31T15:00:00Z')), '2027-01-01');
  assert.equal(tokyoDate(new Date('2024-02-28T15:00:00Z')), '2024-02-29');
});

test('fixed member cells invert only their background and foreground before release', () => {
  const characters = new Map([['member', { color: '#305DAA' }]]);
  const display = { characterTextColor: '#FFFFFF', characterFontFamily: 'Noto Sans JP' };
  const position = { kind: 'fixed', characterId: 'member' };
  const unreleased = characterCellStyle(position, characters, display, false);
  assert.equal(unreleased.backgroundColor, '#FFFFFF');
  assert.equal(unreleased.color, '#305DAA');
  assert.equal(unreleased.fontFamily, 'Noto Sans JP');
  assert.equal(unreleased.textShadow, 'none');
  const released = characterCellStyle(position, characters, display, true);
  assert.equal(released.backgroundColor, '#305DAA');
  assert.equal(released.color, '#FFFFFF');
  for (const kind of ['empty', 'free']) {
    assert.deepEqual(characterCellStyle({ kind }, characters, display, false), {});
    assert.deepEqual(characterCellStyle({ kind }, characters, display, true), {});
  }
});
