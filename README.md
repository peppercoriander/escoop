# ESCOOP · 歌曲站位检索

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
node --test tests/catalog.test.mjs
npm run build
node scripts/build-site.mjs
```

网页入口是 `index.html`，组件位于 `src/App.tsx`，样式位于 `src/App.module.css`。`npm run build` 先校验数据和 TypeScript，再输出 `dist`，可通过 `npm run preview` 预览。Vite 使用相对基础路径，兼容 GitHub 用户主页和仓库子路径。

`.github/workflows/pages.yml` 已配置数据校验、测试、构建和 GitHub Pages 发布；需在仓库 Settings → Pages 中选择 GitHub Actions。此任务未推送 GitHub。`sites/escoop/dist` 是 Sites 静态发布副本，`sites/escoop/.openai/hosting.json` 保存私有站点身份；该目录不加入原仓库。

## 操作方式

- 点击公司图标筛选公司；点击组合图标展开／收起成员，不改变组合筛选。
- 组合右上角的「＋」单独添加组合筛选，选中后显示「✓」。
- 成员与站位支持 AND 多选；即使收起组合，已选成员仍保留取消入口。
- 手机可收起整个筛选区，已选条件与 RESET 仍可见。
- 结果表格内可上下与横向滚动，表头和歌曲名称列固定。

## 颜色与数据

- 歌曲和成员颜色分别取组合、人物配置；合作曲保留等分底色。
- Other 默认使用 `#004D99`。7 首特殊歌曲底色由 `data/source/display.json` 的 `song_background_overrides` 按稳定歌曲 ID 维护。
- 站位信息白底，数字按次数规则着色；图例从同一份规则生成。
- 未录入的组合显示「待录入」，明确没有的显示「无」。人物空格与自由站位保持独立语义。

数据接口详见 [data/WEBSITE_DATA.md](data/WEBSITE_DATA.md)。
