# 网站数据接口

现有数据可支持两个筛选器、结果表格及 RESET。维护数据和页面数据分开：人工维护 `data/source`，程序生成 `data/normalized/site_data.json`，网页只加载后者。

## 需求与数据的对应

| 页面所需数据 | 唯一维护位置 | 网页读取位置 |
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
| 站位选项 | 不重复维护，从实际录入内容生成 | combinationOptions：value、positions、songCount |

## 两种“站位”分开处理

人物站位是 `1 号位是谁、2 号位是谁……`，维护在 positions.csv。数字组合原文是 `12,12,34……`，维护在歌曲表；重复次数决定数字组合文字色。这两类数据相关，但不互相替代。

推荐在**数据生成／发布时计算**数字组合的去重、次数、文字色和歌曲分色。333 首歌也足够在浏览器实时计算，但没有必要让每次访问都重复解析原文。浏览器只负责响应筛选、按 ID 取人物色并渲染结果。更新原文后重新生成即可，不手工维护“原文”和“带色结果”两份数据。

## 页面如何读取

1. 按 `groups` 数组逐行显示公司／Other 图标，沿 `unitIds` 显示右侧组合。COSMIC 直接显示六组，不多展开一层。
2. 选组合后读取该组合的 `characterIds`，在 `characters` 中查简称与颜色。同一人物 ID 跨组合复用，已选人物按 ID 去重。
3. 筛选器 2 直接显示 `combinationOptions`。当前为 26 个已知选项，按涉及位置数量、数字值排序；新增原文后自动增加选项。`songCount` 是未施加其他条件时的命中歌曲数。
4. 使用 `filterSongs(site.songs, selection)` 得到结果。组合、人物和数字组合多选全部采用 AND；人物和数字组合各自匹配整首歌曲，不要求选中的人物正好位于所选数字组合中。
5. 初始化或 RESET 时执行 `selection = createFilterState()`。菜单是否展开等临时 UI 状态也在页面重置，不需要数据库表。

```javascript
import {
  createFilterState, filterSongs, characterCellStyle,
  songCellStyle, encodeAssetPath,
} from '../src/lib/song-data.mjs';

let selection = createFilterState();
const unitsById = new Map(site.units.map(u => [u.id, u]));
const charactersById = new Map(site.characters.map(c => [c.id, c]));
const results = filterSongs(site.songs, selection);
// 人物格：characterCellStyle(position, charactersById, site.display)
// 歌曲格：songCellStyle(song)
// 图片地址：new URL(encodeAssetPath(unit.iconPath), deploymentBaseUrl).href
// RESET：selection = createFilterState()
```

`deploymentBaseUrl` 指向网站的静态资源根目录，兼容部署到仓库子路径。图片文件名中的 `%21`、`%26` 是真实字符，必须按路径段编码为 `%2521`、`%2526`；不要先解码文件名。

## 保留的业务约束

- 一首歌一个稳定 ID、一套有序组合配置；合作曲单独选择任一所属组合都能命中同一结果。
- Adam 为凪／茨、Eve 为日和／纯；六首子组合歌曲不会自动带上 Eden 标签。
- 固定人物、自由对象、未录入空格分开。自由对象可容纳额外不同人物，空格不可。
- 数字组合完整匹配，12 不匹配 123。当前编号语法只能表达位置 1–9；涉及第 10 位前需扩展。
- 周年曲等 Other 标签保留，用于歌曲分类和颜色来源，不作为额外组合菜单。四人月是 AKATSUKI 子组合，归 Rhythm Link，菜单直接显示在 AKATSUKI 后；颜色为 #962828，使用 New_AKATSUKI_ES_Logo.webp。
- AKATSUKI 的成员是敬、紅、颯馬；四人月的成员是敬、紅、颯馬、維吹。四人月歌曲不自动继承 AKATSUKI 标签，沿用 Adam／Eve 的独立筛选规则。
- 四人月包括《百花繚乱、紅月夜（2025Ver.）》《天翔KAGETSU》《炎纏焔踊千変万火》《LOUDEST BUGS》《CIVIL WAR》及《明鏡流水》；最后一首站位尚未提供。CIVIL WAR 保留四人月与 Crazy:B 的八人合作站位及左右分色。
- 合作曲按表演标签顺序等分颜色；两组合为左右各半。人物格仍用人物色，Noto Sans JP 白字。

## 已剔除与待补

已移除旧别名表、重复的菜单布局表／JSON、空的单位／人物独立文字色字段、重复的标签名称与公司字段、独立的歌曲原文维护表，以及 2,097 行空白占位。待补清单也去除了无实际用途的旧来源行号、回复栏和重复提示。

保留九张维护 CSV；站位源只有 1,233 个已知位置，网页仍输出 3,330 格。生成的 CSV／dataset 与 Excel 是核对视图，不是额外维护源，也无需随网页一起下载。

仍缺四家公司代表色；26 首歌的站位、237 首歌的数字组合原文正在录入。这些不阻止搭建页面。页面实现时还需加载字体，并用 CSS 做桌面／手机适配；响应式列数不属于业务数据，不再单独存一份布局表。
