# English Naming and Structure

## Scope

These instructions apply to this directory and its descendants, including the data workbook, generated exports, and supporting scripts. Follow explicit user instructions if they override these rules.

## Required Language

Use English for all authored names, identifiers, and structural or explanatory text, including:

- File and directory names.
- Variables, constants, functions, classes, modules, and configuration keys.
- Database tables, spreadsheet tables, worksheets, named ranges, and chart names.
- Column headers, field names, schema properties, and generated status values.
- Titles, legends, comments, documentation, validation messages, and maintenance notes.

Use meaningful English words rather than transliterations of non-English structural names. Prefer `snake_case` for data files, table names, and fields; follow the existing English naming convention for code identifiers.

Examples: `normalized_data_tables.xlsx`, `Songs`, `Characters`, `CharacterUnits`, `song_id`, `character_id`, `background_color`, and `missing_positions`.

## Source Content Exception

Only source data content may retain its original language. Preserve original song titles, character names, unit names, company names, and other supplied data values exactly unless the user requests a correction.

Do not translate, romanize, or otherwise rewrite source values merely to make them English. Generated headers and explanations surrounding those values must still be English.

## Existing Artifacts and Integrity

When an existing artifact is next edited or regenerated, bring its filename and authored structure into compliance with these rules. Update affected builders, formulas, links, and references together so renaming does not break the workflow. Avoid leaving a competing copy under the obsolete filename.

Preserve stable entity IDs, source values, relationships, row order where meaningful, formation positions, counts, and colors. A naming cleanup must not change business data or filtering behavior.

The authoritative maintenance source remains `data/source` at the repository root. This workbook and other exports are generated views, not additional maintenance sources.

## Verification

Before delivering a changed artifact, verify that filenames, worksheet and table names, headers, and generated metadata comply with the English-language rule. Check updated references and confirm that source content and relationships remain intact. For workbook changes, inspect the affected sheets and verify the exported file.
