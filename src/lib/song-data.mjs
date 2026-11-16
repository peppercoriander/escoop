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

export function characterCellStyle(position, charactersById, display) {
  const character = charactersById.get(position.characterId);
  return position.kind === 'fixed' && character ? {
    backgroundColor: character.color,
    color: display.characterTextColor,
    fontFamily: display.characterFontFamily,
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
