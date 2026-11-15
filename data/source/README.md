# 唯一维护源

只修改本目录的 **9 张 CSV 和 display.json**。`data/normalized`、网页 JSON、Excel 均为生成结果，不能作为第二套维护源。

| 文件 | 维护内容 |
|---|---|
| groups.csv | 公司／Other：名称、代表色、logo、菜单行顺序 |
| units.csv | 组合：名称、代表色、logo、公司归属、公司内显示顺序；父组合只作资料保留 |
| characters.csv | 唯一人物简称、代表色；不需要全名或图标 |
| character_units.csv | 组合成员关系及组内显示顺序；同一人物可属于多个组合 |
| songs.csv | 唯一歌曲名称、ID，以及 `combination_raw` 数字组合原始重复序列 |
| positions.csv | 已知站位：歌曲 ID、位置编号、人物 ID／自由对象、对应分类标签 |
| song_labels.csv | 每首歌曲唯一的组合／分类配置及 `tag_order` 顺序 |
| labels.csv | 分类 ID 与组合的映射，以及 Other 标签的名称 |
| frequency_colors.csv | 数字组合出现次数对应的文字色 |
| display.json | 人物统一字体和文字色；`song_background_overrides` 按歌曲 ID 配置特殊歌曲底色 |

## 补录方法

1. 在 `songs.csv` 查歌曲 ID；填 `combination_raw` 原始序列。名称、原文在同一行，更名不改变 ID。
2. 在 `positions.csv` 添加／修改实际位置，只保存已知位置；没有录入的歌曲无需填十行空白。
3. 从仓库根目录运行：

```powershell
python scripts/prepare_data.py
python scripts/prepare_data.py --check
```

CSV 使用 UTF-8 BOM；Excel 中请保存为 CSV UTF-8，保留英文表头与 ID，数字组合原文按文本保存。新增实体使用不重复且稳定的 ID。新增歌曲还需在 `song_labels.csv` 设置有序标签；站位与原文可以稍后补录。

## 字段规则

- `positions.position` 为 1–10，同一歌曲同一位置只有一行；程序补齐未提供的格子为空白。不要在维护源保存 `empty` 行。
- `slot_type=fixed` 时填写人物 ID；`free` 时人物 ID 留空，以位置编号显示，可容纳任意人物。未录入的位置不算自由对象。
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

完整页面数据接口和生成策略见 [网站数据接口](../WEBSITE_DATA.md)。测试：`python -m unittest discover -s tests -p 'test_*.py'` 和 `node --test tests/song-data.test.mjs`。
