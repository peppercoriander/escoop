/** A song is one result, with ordered unit membership and global positions. */
export function matchesSong(song, {unitIds = [], characterIds = [], combinations = []} = {}) {
  const units = new Set(song.unitIds);
  if (![...new Set(unitIds)].every(id => units.has(id))) return false;
  const fixed = new Set(song.positions.filter(p => p.kind === 'fixed').map(p => p.characterId));
  // Generic numbered formations are excluded only when filtering specific members.
  if (characterIds.length && song.positions.some(p => p.kind === 'free')) return false;
  if (![...new Set(characterIds)].every(id => fixed.has(id))) return false;
  const present = new Set(song.combinations.map(item => item.value));
  return [...new Set(combinations)].every(value => present.has(value));
}

export function filterSongs(songs, filters = {}) {
  // Input is site_data.json: already unique, so a multi-unit song cannot duplicate results.
  return songs.filter(song => matchesSong(song, filters));
}

export function songCellStyle(song) {
  // Hard color stops retain ordered bands with 45-degree slash boundaries.
  return {background: song.backgroundCss};
}

/** Calendar dates use Japan time, independently of the viewer's local timezone. */
export function tokyoDate(now = new Date()) {
  return new Date(now.getTime() + 9 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

export function millisecondsUntilTokyoMidnight(now = new Date()) {
  const day = 24 * 60 * 60 * 1000;
  return day - ((now.getTime() + 9 * 60 * 60 * 1000) % day);
}

export function isSongReleased(releaseDate, today = tokyoDate()) {
  return Boolean(releaseDate && releaseDate <= today);
}

export function characterCellStyle(position, charactersById, display, released) {
  const character = charactersById.get(position.characterId);
  return position.kind === 'fixed' && character ? {
    backgroundColor: released ? character.color : '#FFFFFF',
    color: released ? display.characterTextColor : character.color,
    fontFamily: display.characterFontFamily,
    ...(!released && { textShadow: 'none' }),
  } : {};
}

/** Use for initial state and RESET; each call owns fresh selection arrays. */
export function createFilterState() {
  return {unitIds: [], characterIds: [], combinations: []};
}

/** Paths contain literal percent signs; resolve this result against the deployment base URL. */
export function encodeAssetPath(path) {
  return path.split('/').map(segment => encodeURIComponent(segment)).join('/');
}
