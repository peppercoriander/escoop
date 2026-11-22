# 网站数据接口

现有数据可支持两个筛选器、结果表格及 RESET。维护数据和页面数据分开：人工维护 `data/source/maintenance.xlsx` 和 `song_placements.csv`，导入脚本拆分其余 CSV 与 display.json，再生成 `data/normalized/site_data.json`，网页只加载后者。

## 需求与数据的对应

下表列出生成后的 CSV 接口；对应的人工维护位置均为工作簿内的同名资料页，展示顺序 CSV 除外。工作簿「歌曲」页同时生成 songs、song_labels、positions 及特殊底色配置。详见 [数据维护说明](source/README.md)。

| 页面所需数据 | 数据接口位置 | 网页读取位置 |
|---|---|---|
| 组合 → 人物 | character_units.csv | units[].characterIds |
| 组合 → 颜色 | units.csv | units[].color |
| 人物 → 颜色 | characters.csv | characters[].color |
| 公司／Other → 颜色 | groups.csv | groups[].color；未提供为 null |
| 公司／Other → 组合 | units.csv 的 group_id 与 sort_order | groups[].unitIds（已排好序） |
| 公司／组合 → 图片 | groups.csv、units.csv 的 icon_path | groups／units 的 iconPath |
| 歌曲 → 人物站位 | positions.csv | songs[].positions，输出固定十格 |
| 歌曲 → 数字组合原始序列 | songs.csv 的 combination_raw | 不发给网页；生成时处理 |
| 歌曲 → 处理后数字组合 | 不重复维护 | songs[].combinations：value、count、color |
| 歌曲 → 颜色配置 | song_labels.csv 的有序组合配置，颜色取组合／Other | songs[].backgroundCss、colors |
| 歌曲 → 展示分区与顺序 | song_placements.csv 的 song_id、section_id、sort_order | songPlacements[].songId、sectionId、sortOrder |
| 歌曲 → 实装日期 | songs.csv 的 release_date，支持 YYYY-MM-DD 或 YYYY/MM/DD | songs[].releaseDate：统一为 YYYY-MM-DD 字符串或 null |
| 站位选项 | 不重复维护，从实际录入内容生成 | combinationOptions：value、positions、songCount |
| 特殊歌曲底色 | display.json 的 song_background_overrides（歌曲 ID → HEX） | 已合并到 songs[].backgroundCss、colors |
| 次数颜色规则 | frequency_colors.csv | songs[].combinations[].color（保留 frequencyColors 接口，页面不显示图例） |

## 两种“站位”分开处理

人物站位是 `1 号位是谁、2 号位是谁……`，维护在工作簿「歌曲」页的 1–10 号位列，导入生成 positions.csv。数字组合原文是 `12,12,34……`，在同一页的「数字组合原文」列维护；重复次数决定数字组合文字色。这两类数据相关，但不互相替代。

推荐在**数据生成／发布时计算**数字组合的去重、次数、文字色和歌曲分色。几百首歌也足够在浏览器实时计算，但没有必要让每次访问都重复解析原文。浏览器只负责响应筛选、按 ID 取人物色并渲染结果。更新原文后重新生成即可，不手工维护“原文”和“带色结果”两份数据。

## 页面如何读取

1. 按 `groups` 数组逐行显示公司／Other 图标，沿 `unitIds` 显示右侧组合。COSMIC 直接显示六组，不多展开一层。
2. 点击组合图标直接筛选组合歌单并显示成员，读取该组合的 `characterIds`，在 `characters` 中查简称与颜色。选择成员时清空 `groupIds` 与 `unitIds`；切回公司或组合时清空成员条件。站位条件独立保留。同一人物 ID 跨组合复用，已选人物按 ID 去重。
   公司或组合取消时，成员菜单从仍选中的公司／组合重建；没有剩余项则清空。选择成员导致公司／组合自动取消时，保留当前成员菜单以便继续多选。
3. 筛选器 2 从 `combinationOptions` 中只显示完全由 1–5 号位组成的选项，按涉及位置数量、数字值排序；包含 6–10 号位的选项不显示，歌曲原始数据保留。`songCount` 是未施加其他条件时的命中歌曲数。
4. `selectSongs(site, selection)` 筛选唯一歌曲；`selectSongRows(site, selection)` 再按 `songPlacements` 展开为分区展示行。组合、人物和数字组合多选全部采用 AND；人物和数字组合各自匹配整首歌曲，不要求选中的人物正好位于所选数字组合中。选择公司／组合后只显示相应分区，未选公司／组合时显示所有配置位置。分区顺序仍按公司／组合菜单，区内按 `sortOrder` 数值升序，结果数量按歌曲 ID 去重。
5. 初始化或 RESET 时执行 `selection = createFilterState()`。菜单等临时 UI 状态也重置，页面回到左上角。RESET 为可拖拽悬浮按钮，刷新后恢复右下角初始位置，不需要数据库表。

```javascript
import {
  createFilterState, filterSongs, characterCellStyle,
  songCellStyle, encodeAssetPath, isSongReleased,
} from '../src/lib/song-data.mjs';

let selection = createFilterState();
const unitsById = new Map(site.units.map(u => [u.id, u]));
const charactersById = new Map(site.characters.map(c => [c.id, c]));
const results = filterSongs(site.songs, selection);
// 人物格：characterCellStyle(position, charactersById, site.display, isSongReleased(song.releaseDate))
// 歌曲格：songCellStyle(song)
// 图片地址：new URL(encodeAssetPath(unit.iconPath), deploymentBaseUrl).href
// RESET：selection = createFilterState()
```

实际页面通过 `catalog.mjs` 的 `createSelection()` 和 `selectSongRows()` 处理公司筛选与分区展示；上面的底层辅助函数仅筛选唯一歌曲。`songPlacements` 是展示关系，不重复存储歌名、成员和颜色。维护表中的 `title`、`section_name` 是识别列，生成时从权威歌曲表和分区表解析名称，不反向覆盖维护源。

实装状态不在构建时固化。`releaseDate` 保留日期或 null，页面按日本时间（Asia/Tokyo）的当前日期比较；早于／等于今天使用成员色底白字，空白／晚于今天使用白底成员色文字。只影响固定成员格；通用数字和空格无对应成员色，保持原样。页面跨日本午夜及重新获得焦点／可见时刷新日期，不需要每日构建。

`deploymentBaseUrl` 指向网站的静态资源根目录，兼容部署到仓库子路径。图片文件名中的 `%21`、`%26` 是真实字符，必须按路径段编码为 `%2521`、`%2526`；不要先解码文件名。

## 保留的业务约束

- 一首歌一个稳定 ID、一套有序组合配置；合作曲在各配置分区有独立展示位置，共用同一首歌的数据。歌曲计数不因展示位置增加而增加。
- Adam 为凪／茨、Eve 为日和／纯；六首子组合歌曲不会自动带上 Eden 标签。
- 固定人物、通用数字站位、未录入空格分开。具体成员筛选仅匹配固定人物；有任何 `free` 通用站位的歌曲（包括固定人物与通用站位混合的歌曲）在成员筛选时整体排除。未选成员时仍正常显示，空格也不会匹配人物。
- 数字组合完整匹配，12 不匹配 123。当前编号语法只能表达位置 1–9；涉及第 10 位前需扩展。
- 周年曲等 Other 标签保留，用于歌曲分类和颜色来源，不作为额外组合菜单。四人月是 AKATSUKI 子组合，归 Rhythm Link，菜单直接显示在 AKATSUKI 后；颜色为 #962828，使用 New_AKATSUKI_ES_Logo.webp。
- AKATSUKI 的成员是敬、紅、颯馬；四人月的成员是敬、紅、颯馬、維吹。四人月歌曲不自动继承 AKATSUKI 标签，沿用 Adam／Eve 的独立筛选规则。
- 四人月包括《百花繚乱、紅月夜（2025Ver.）》《天翔KAGETSU》《炎纏焔踊千変万火》《LOUDEST BUGS》《CIVIL WAR》及《明鏡流水》；最后一首站位尚未提供。CIVIL WAR 保留四人月与 Crazy:B 的八人合作站位及斜切分色。
- 合作曲按表演标签顺序等分颜色；两组合各占一半，分界线为 45° 的 `/` 方向斜切。人物格仍用人物色，Noto Sans JP 白字。

## 已剔除与待补

已移除旧别名表、重复的菜单布局表／JSON、空的单位／人物独立文字色字段、重复的标签名称与公司字段、独立的歌曲原文维护表，以及 2,097 行空白占位。待补清单也去除了无实际用途的旧来源行号、回复栏和重复提示。

当前维护源为一份工作簿与一张展示顺序 CSV；其余九张 CSV 和 display.json 自动生成。每首歌曲生成固定十个站位格，分区展示记录通过歌曲 ID 关联；当前数量以 data/normalized/validation.json 为准。生成的 CSV／dataset 与历史 Excel 导出只是核对视图；maintenance.xlsx 则是当前维护源。这些文件无需随网页一起下载。

仍缺四家公司代表色；部分歌曲的站位与数字组合原文仍在录入，具体待补项见 data/normalized/issues.csv。页面已加载 Noto Sans JP 并适配桌面／手机，表格在窄屏等比缩放至默认显示到第 5 号位，6–10 号位通过整页横向滑动查看；未录入数据保留空缺提示。公司按钮采用中性背景，不推测公司代表色。
