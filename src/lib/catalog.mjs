import { matchesSong, createFilterState } from './song-data.mjs';

export const createSelection = () => ({ ...createFilterState(), groupIds: [] });

export function primarySection(song, site) {
  for (const group of site.groups) {
    const unitId = group.unitIds.find(id => song.unitIds.includes(id));
    if (unitId) return { group, unit: site.units.find(unit => unit.id === unitId) };
  }
  return { group: site.groups.find(group => group.id === 'group_other'), unit: null };
}

export function selectSongs(site, selection) {
  const groupByUnit = new Map(site.groups.flatMap(group => group.unitIds.map(id => [id, group.id])));
  const order = new Map(site.groups.flatMap(group => [...group.unitIds, group.id]).map((id, i) => [id, i]));
  return site.songs.filter(song => {
    const groups = new Set(song.unitIds.length ? song.unitIds.map(id => groupByUnit.get(id)) : ['group_other']);
    return selection.groupIds.every(id => groups.has(id)) && matchesSong(song, selection);
  }).sort((a, b) => {
    const left = primarySection(a, site), right = primarySection(b, site);
    return order.get(left.unit?.id ?? left.group.id) - order.get(right.unit?.id ?? right.group.id);
  });
}

export function visibleMembers(site, selection, expandedUnitIds = []) {
  const unitIds = new Set([...expandedUnitIds, ...site.groups.filter(g => selection.groupIds.includes(g.id)).flatMap(g => g.unitIds)]);
  // Keep selected members visible when their unit is deselected, so every active filter can be removed.
  const ids = new Set([...site.units.filter(u => unitIds.has(u.id)).flatMap(u => u.characterIds), ...selection.characterIds]);
  return [...ids].map(id => site.characters.find(c => c.id === id));
}
