import type { CSSProperties } from 'react';
import type { Song, Selection, Position, Character, SiteData } from '../types';
export function matchesSong(song: Song, filters?: Partial<Selection>): boolean;
export function filterSongs(songs: Song[], filters?: Partial<Selection>): Song[];
export function songCellStyle(song: Song): CSSProperties;
export function characterCellStyle(position: Position, characters: Map<string, Character>, display: SiteData['display']): CSSProperties;
export function createFilterState(): Omit<Selection, 'groupIds'>;
export function encodeAssetPath(path: string): string;
