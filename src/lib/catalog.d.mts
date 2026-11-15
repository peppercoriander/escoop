import type { Song, SiteData, Selection, Character, Group, Unit } from '../types';
export function createSelection(): Selection;
export function primarySection(song: Song, site: SiteData): { group: Group; unit: Unit | null };
export function selectSongs(site: SiteData, selection: Selection): Song[];
export function visibleMembers(site: SiteData, selection: Selection, expandedUnitIds?: string[]): Character[];
