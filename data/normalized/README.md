# 生成数据（不要直接编辑）

唯一维护入口为 [data/source](../source/README.md)。运行 `python scripts/prepare_data.py` 生成；`--check` 校验源数据及输出是否最新。

- **site_data.json**：网页唯一需要加载的数据文件，含公司菜单、组合成员、人物颜色、26 个实际站位选项、333 个唯一歌曲实体及 357 条 `songPlacements` 展示关系。
- **song_placements.csv**：从维护源生成的排序核对视图；只编辑 `data/source/song_placements.csv`，不要编辑本目录副本。
- **songs.csv**：歌曲核对视图，包含统一为 `YYYY-MM-DD` 的 `release_date`；网页日期字段仍为 `songs[].releaseDate`。只编辑 `data/source/songs.csv`，不再生成独立日期表。
- **dataset.json + CSV**：便于核对和导出 Excel 的完整生成表。网页无需加载这些核对文件。
- **validation.json / issues.csv**：生成校验汇总及仍待补充的数据。
- **combination_options.csv**：自动汇总的站位选项、对应位置数组、可命中歌曲数和菜单顺序；不手工维护。

公司与组合菜单顺序从 groups／units 表生成，已移除独立布局 JSON 和重复菜单表。旧名称别名表不再需要。数字组合原文已并入维护源 songs.csv；此处 song_combination_sources.csv 仅为按歌曲查看原文和状态的生成视图。

生成时统计次数、匹配文字色、生成歌曲分色；站位格通过人物 ID 取人物色，不保存每首歌一份重复人物颜色。未提供位置自动补齐到十格。固定／自由／空白语义保持独立。

目前仍待录入 26 首站位、237 首组合原文，另缺四家公司代表色。详情见 [网站数据接口](../WEBSITE_DATA.md)。Excel 为查看快照，不自动读回修改。
