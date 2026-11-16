import { matchesSong, createFilterState } from './song-data.mjs';

export const createSelection = () => ({ ...createFilterState(), groupIds: [] });

/** Only formations entirely within positions 1–5 appear in the menu. */
export const positionOptions = site => site.combinationOptions.filter(option =>
  option.positions.length > 0 && option.positions.every(position => position >= 1 && position <= 5));

/** Company, unit and member selections are alternative ways to choose performers. */
export function toggleSelection(previous, field, value) {
  const values = previous[field].includes(value)
    ? previous[field].filter(id => id !== value) : [...previous[field], value];
  const next = { ...previous, [field]: values };
  if (field === 'characterIds') { next.groupIds = []; next.unitIds = []; }
  if (field === 'unitIds') { next.groupIds = []; next.characterIds = []; }
  if (field === 'groupIds') { next.unitIds = []; next.characterIds = []; }
  return next;
}

export const createCatalogState = () => ({ selection: createSelection(), expandedUnitIds: [] });

/** Refresh the member menu from the new company/unit selection, not browsing history. */
export function toggleCatalogState(site, previous, field, value) {
  const selection = toggleSelection(previous.selection, field, value);
  const expandedUnitIds = field === 'unitIds' ? [...selection.unitIds]
    : field === 'groupIds' ? site.groups.filter(g => selection.groupIds.includes(g.id)).flatMap(g => g.unitIds)
    : previous.expandedUnitIds;
  return { selection, expandedUnitIds };
}

export function selectSongs(site, selection) {
  const groupByUnit = new Map(site.groups.flatMap(group => group.unitIds.map(id => [id, group.id])));
  return site.songs.filter(song => {
    const groups = new Set(song.unitIds.length ? song.unitIds.map(id => groupByUnit.get(id)) : ['group_other']);
    return selection.groupIds.every(id => groups.has(id)) && matchesSong(song, selection);
  });
}

/** Filter unique songs first, then expand only their visible, independently ordered placements. */
export function selectSongRows(site, selection) {
  const songs = new Map(selectSongs(site, selection).map(song => [song.id, song]));
  const units = new Map(site.units.map(unit => [unit.id, unit]));
  const sections = new Map(site.groups.flatMap(group => [
    ...group.unitIds.map(id => [id, { group, unit: units.get(id) }]),
    [group.id, { group, unit: null }],
  ]));
  const order = new Map([...sections.keys()].map((id, index) => [id, index]));
  return site.songPlacements.filter(placement => {
    if (!songs.has(placement.songId)) return false;
    if (selection.unitIds.length && !selection.unitIds.includes(placement.sectionId)) return false;
    const section = sections.get(placement.sectionId);
    return !selection.groupIds.length || selection.groupIds.includes(section.group.id);
  }).map(placement => ({
    song: songs.get(placement.songId), section: sections.get(placement.sectionId),
    sectionId: placement.sectionId, sortOrder: placement.sortOrder,
  })).sort((a, b) => order.get(a.sectionId) - order.get(b.sectionId) || a.sortOrder - b.sortOrder);
}

export function visibleMembers(site, selection, expandedUnitIds = []) {
  const unitIds = new Set([...expandedUnitIds, ...site.groups.filter(g => selection.groupIds.includes(g.id)).flatMap(g => g.unitIds)]);
  // Keep selected members visible when their unit is deselected, so every active filter can be removed.
  const ids = new Set([...site.units.filter(u => unitIds.has(u.id)).flatMap(u => u.characterIds), ...selection.characterIds]);
  return [...ids].map(id => site.characters.find(c => c.id === id));
}
