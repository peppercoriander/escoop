import type { Song, SongRow, SiteData, Selection, Character } from '../types';
export function createSelection(): Selection;
export function positionOptions(site: SiteData): SiteData['combinationOptions'];
export interface CatalogState { selection: Selection; expandedUnitIds: string[] }
export function createCatalogState(): CatalogState;
export function toggleCatalogState(site: SiteData, previous: CatalogState, field: keyof Selection, value: string): CatalogState;
export function toggleSelection(previous: Selection, field: keyof Selection, value: string): Selection;
export function selectSongs(site: SiteData, selection: Selection): Song[];
export function selectSongRows(site: SiteData, selection: Selection): SongRow[];
export function visibleMembers(site: SiteData, selection: Selection, expandedUnitIds?: string[]): Character[];
