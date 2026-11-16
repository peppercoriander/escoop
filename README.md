# ESCOOP · 协力站位表

按公司、组合、成员与站位筛选歌曲的静态网页。默认按公司、组合顺序展示全部歌曲，多选条件采用 AND，RESET 清除全部选择。

## 本地预览

```powershell
npm ci
npm run dev
```

打开 http://127.0.0.1:4175。前端使用 React + TypeScript + Vite，样式采用 CSS Modules。页面使用 Noto Sans JP，字体通过 Google Fonts 加载。

当前 Codex 环境若没有全局 npm，可用 `node .tools/package/bin/npm-cli.js` 替代命令中的 `npm`；`.tools` 仅为本机工具，不提交到仓库。

## 更新与验证

只维护 `data/source`，然后执行：

```powershell
python scripts/prepare_data.py
python scripts/prepare_data.py --check
python -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.mjs
npm run build
node scripts/build-site.mjs
```

网页入口是 `index.html`，组件位于 `src/App.tsx`，样式位于 `src/App.module.css`。`npm run build` 先校验数据和 TypeScript，再输出 `dist`，可通过 `npm run preview` 预览。Vite 使用相对基础路径，兼容 GitHub 用户主页和仓库子路径。

GitHub Pages 目标地址为 `https://peppercoriander.github.io/escoop/`，仓库为 `peppercoriander/escoop`。在仓库 Settings → Pages 中选择 GitHub Actions，提交到 `main` 后由 `.github/workflows/pages.yml` 自动校验、测试、构建并发布；也可在 Actions 中手动运行工作流。修改 CSV 后请先运行上面的数据生成命令，再提交维护源及生成结果。

`sites/escoop/dist` 是独立的 Sites 私有发布副本，`sites/escoop/.openai/hosting.json` 保存该私有站点身份；该目录不加入 GitHub 仓库。

## 操作方式

- 各组合歌单按 `data/source/song_placements.csv` 的独立序号显示。合作曲可以在多个分区出现；选择公司／组合只显示相应分区，结果计数按唯一歌曲统计。
- 点击公司图标筛选公司；点击组合图标直接筛选对应歌单，同时显示成员，再次点击取消该组合筛选。
- 选择成员时自动清除公司和组合条件，只按成员筛选；站位筛选仍独立叠加。切回公司或组合时清除成员条件。
- 成员与站位支持 AND 多选；具体成员筛选排除所有含通用数字站位的歌曲，仅匹配已录入固定人物。
- 取消公司或组合时，成员菜单同步更新；取消最后一项后清空。选择成员导致公司／组合条件自动清除时，保留当前成员菜单供继续多选。
- 手机可收起整个筛选区，已选条件与 RESET 仍可见。
- RESET 悬浮在右下角，可拖动改变位置。拖动不重置，点击松开后清除所有筛选并将页面回到左上角；刷新页面恢复按钮初始位置。
- 结果表格随整页滚动，不创建内嵌横向或纵向滚动窗口；窄屏通过页面横向滚动查看后续位置。
- 按钮和表格字号比初版增大约 25%，外边距、内边距与间隙缩小约 20%。
- 公司／组合按钮再缩至原来的 80%；窄屏时统一按比例继续缩小，保持同样的五行布局，不换行。站位按钮仍可换行。
- 歌曲表格维持字号，单元格上下内边距进一步缩小 80%，取消固定数据行高。
- RESET 改为灰蓝底白字。已移除品牌页头、宣传文案、页脚、独立收录数量、颜色图例及表格说明。

## 颜色与数据

- 歌曲和成员颜色分别取组合、人物配置；合作曲保留等分底色。
- 在 `data/source/song_releases.csv` 填写实装日期（YYYY-MM-DD）。按日本时间，空白／未来日期的固定成员格显示白底成员色文字，实装当天及之后显示成员色底白字。已发布日期跨天自动生效；修改 CSV 后仍需生成数据、构建并发布。
- Other 默认使用 `#004D99`。7 首特殊歌曲底色由 `data/source/display.json` 的 `song_background_overrides` 按稳定歌曲 ID 维护。
- 站位信息白底，数字按次数规则着色，不再显示图例。
- 未录入的组合显示「待录入」，明确没有的显示「无」。人物空格与自由站位保持独立语义。

数据接口详见 [data/WEBSITE_DATA.md](data/WEBSITE_DATA.md)。
