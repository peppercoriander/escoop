# 唯一维护源

只修改本目录的 **10 张 CSV 和 display.json**。`data/normalized`、网页 JSON、Excel 均为生成结果，不能作为第二套维护源。

`song_placements.csv` 已接入数据生成器和网页，用于维护每首歌在各分区中的独立顺序。运行 `prepare_data.py` 只读取维护源，不会覆盖你编辑的 CSV。

## 歌曲展示位置

- 每行代表一首歌在一个分区中的展示位置；合作曲在每个实际所属组合下各有一行。没有 Unit 的歌曲放入 `group_other`。
- `song_id` 和 `section_id` 为关联键，请保留。`title`、`section_name` 仅为阅读辅助列，歌名和分区名称仍由原歌曲表／组合表维护。
- 修改 `sort_order` 调整该分区内的顺序，正整数、越小越靠前；同一分区请勿使用重复序号。初始按现有歌曲表顺序，以 10 递增，每个分区单独从 10 开始。
- 仅移动文件中的行不会改变显示顺序；请修改 `sort_order`。同一首歌在不同分区的序号互不影响。
- 例如，将 Trickstar 中《Crossing×Heart》的序号设为介于《虹色のSeasons》和下一首歌之间的数值，即可让它紧接《虹色のSeasons》显示；fine 中的序号不受影响。具体序号以维护表为准。
- 每首歌至少保留一个展示位置；同一歌曲与分区不可重复。分区应为歌曲所属 Unit，或无 Unit 歌曲使用 `group_other`。生成时校验关联键、正整数序号、分区内重复序号及遗漏歌曲。
- 无公司／组合条件时，符合成员／站位条件的歌曲在所有配置分区展示。选择公司／组合后，只显示所选范围的分区；歌曲自身的多选 AND 筛选规则不变。结果计数按歌曲 ID 去重。
- Excel 工作簿是这张 CSV 的编辑便利副本。二者只选一份编辑；若编辑工作簿，完成后将该工作表另存为 CSV UTF-8，替换 `data/source/song_placements.csv`，或交由后续步骤同步。不要同时维护两份不同的顺序。

## 当前已接入的维护文件

| 文件 | 维护内容 |
|---|---|
| groups.csv | 公司／Other：名称、代表色、logo、菜单行顺序 |
| units.csv | 组合：名称、代表色、logo、公司归属、公司内显示顺序；父组合只作资料保留 |
| characters.csv | 唯一人物简称、代表色；不需要全名或图标 |
| character_units.csv | 组合成员关系及组内显示顺序；同一人物可属于多个组合 |
| songs.csv | 唯一歌曲名称、ID、`combination_raw` 数字组合原始重复序列，以及 `release_date` 实装日期 |
| song_placements.csv | 歌曲展示分区与独立排序；title、section_name 仅供识别 |
| positions.csv | 已知站位：歌曲 ID、位置编号、人物 ID／自由对象、对应分类标签 |
| song_labels.csv | 每首歌曲唯一的组合／分类配置及 `tag_order` 顺序 |
| labels.csv | 分类 ID 与组合的映射，以及 Other 标签的名称 |
| frequency_colors.csv | 数字组合出现次数对应的文字色 |
| display.json | 人物统一字体和文字色；`song_background_overrides` 按歌曲 ID 配置特殊歌曲底色 |

## 歌曲实装日期

- 在 `songs.csv` 的 `release_date` 列填写 `YYYY-MM-DD` 或 `YYYY/MM/DD`，例如 `2026-11-16` 或 `2026/11/16`；生成数据统一为 `YYYY-MM-DD`，不会改写源 CSV；不填写则留空，不需要写「无」。
- 歌曲表每首歌一行，表头为 `song_id,title,combination_raw,release_date`。实装日期已按歌曲 ID 从原 `song_releases.csv` 合并，今后只维护 `songs.csv`，不再使用独立日期表。
- 合作曲各分区共用同一日期；保留 `song_id`，`title` 是歌曲名称的唯一维护列，日期留空视为未知，不猜测缺失日期。
- 网页按日本时间（`Asia/Tokyo`）的当天日期比较，实装日期早于或等于今天时，固定成员格显示成员色底、白字；空白或未来日期则显示白底、成员色文字。通用数字站位与未录入空格保持原样。
- 日期不会影响筛选、歌曲数量、分区顺序、歌曲格底色或站位次数颜色。
- CSV 修改后仍需运行 `python scripts/prepare_data.py`，再构建、发布；日期已发布后，跨天配色由浏览器自动判断，不必每天重建。已打开页面会在日本时间午夜或重新切回页面时更新。
- 生成器校验真实日历日期、格式、重复歌曲和未知 ID，不会覆盖源表。

## 补录方法

1. 在 `songs.csv` 查歌曲 ID；填 `combination_raw` 原始序列和 `release_date` 实装日期。名称、原文、日期在同一行，更名不改变 ID。
2. 在 `positions.csv` 添加／修改实际位置，只保存已知位置；没有录入的歌曲无需填十行空白。
3. 从仓库根目录运行：

```powershell
python scripts/prepare_data.py
python scripts/prepare_data.py --check
```

CSV 使用 UTF-8 BOM；Excel 中请保存为 CSV UTF-8，保留英文表头与 ID，数字组合原文按文本保存。新增实体使用不重复且稳定的 ID。新增歌曲还需在 `song_labels.csv` 设置有序标签，并在 `song_placements.csv` 添加展示位置；站位与原文可以稍后补录。生成、构建并发布后，网页才会应用维护源的修改。

## 字段规则

- `positions.position` 为 1–10，同一歌曲同一位置只有一行；程序补齐未提供的格子为空白。不要在维护源保存 `empty` 行。
- `slot_type=fixed` 时填写人物 ID；`free` 时人物 ID 留空，以位置编号显示通用站位。含通用站位的歌曲不参与具体成员筛选；未选成员时仍展示。未录入的位置不算通用站位。
- `label_id` 可留空；已有归属应保留。填写时必须是该歌曲的标签，用于区分合作曲的表演片段与颜色来源。
- 合作曲直接填写全局站位，例如 Crossing×Heart 的 `北 星 真 毛 英 涉 桃 弓`；程序不按成员名单猜测站位。
- `combination_raw` 保留重复，例如 `12,12,24,13`；空白为仍在录入，`无` 为明确没有。支持空格、中英文逗号。组合编号只能指向已提供的位置。
- 当前组合语法使用单数字 1–9；如需涉及第 10 位，必须先扩展语法，不能直接写 `10`。
- `labels.unit_id` 有值时，名称、分类、公司由组合表推导，源表 `name` 留空；无值时填写 Other 标签名称。周年曲等标签保留，不作为额外组合按钮。四人月属于 AKATSUKI 子组合，已有独立 Unit、成员、颜色与图标，不再归 Other。
- `song_labels.tag_order` 从 1 连续排列，有意义且不可按字母重排。
- `units.sort_order` 是公司内菜单顺序。COSMIC 依次为 Eden、Adam、Eve、Valkyrie、2wink、Crazy:B，不需要第二份布局表。
- Rhythm Link 依次为 UNDEAD、Ra*bits、AKATSUKI、四人月、MELLOW DEAR US。AKATSUKI 成员为敬、紅、颯馬；四人月为敬、紅、颯馬、維吹，颜色 #962828。六首四人月歌曲仅归子组合，不自动继承父组合标签；《明鏡流水》站位后补。
- `frequency_colors` 区间连续；最后一个上限空白表示无上限。默认 1 蓝、2 绿、3 橙、4+ 红。

## 当前待补

26 首站位、237 首数字组合原文仍在录入。四家公司代表色尚未提供，`background_color` 留空；Other 为 `#004D99`。缺色不阻止页面使用 logo 和中性背景，不会伪造代表色。

人物名称与颜色统一维护；共享人物跨组合复用，陣与門可以同色。默认白字仅用于人物格，数字组合的次数配色不受影响。Noto Sans JP 的实际字体加载留给网页实现。

完整页面数据接口和生成策略见 [网站数据接口](../WEBSITE_DATA.md)。测试：`python -m unittest discover -s tests -p 'test_*.py'` 和 `node --test tests/*.test.mjs`。
