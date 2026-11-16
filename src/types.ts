export interface Position { position: number; characterId: string | null; label: string; kind: 'fixed' | 'free' | 'empty'; unitId: string | null }
export interface Combination { value: string; count: number; color: string }
export interface Song { id: string; title: string; unitIds: string[]; labelIds: string[]; unitConfig: string; positions: Position[]; combinations: Combination[]; backgroundCss: string; colors: string[]; combinationStatus: string }
export interface Character { id: string; name: string; color: string }
export interface Unit { id: string; name: string; color: string; iconPath: string; characterIds: string[] }
export interface Group { id: string; name: string; color: string | null; iconPath: string; unitIds: string[] }
export interface Selection { groupIds: string[]; unitIds: string[]; characterIds: string[]; combinations: string[] }
export interface SongPlacement { songId: string; sectionId: string; sortOrder: number }
export interface SongRow { song: Song; sectionId: string; sortOrder: number; section: { group: Group; unit: Unit | null } }
export interface SiteData {
  display: { characterFontFamily: string; characterTextColor: string };
  groups: Group[]; units: Unit[]; characters: Character[]; songs: Song[];
  songPlacements: SongPlacement[];
  combinationOptions: { value: string; positions: number[]; songCount: number }[];
  frequencyColors: { minCount: number; maxCount: number | null; color: string }[];
}
