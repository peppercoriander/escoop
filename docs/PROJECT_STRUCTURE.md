# 项目目录说明

```text
escoop/
├─ README.md                  仓库介绍，由用户维护
├─ update.md                  更新日志，最新条目放最上方
├─ preview.bat                双击更新数据并启动本地预览
├─ AGENTS.md                  Agent 开发约定
├─ docs/                      开发、维护及目录说明
├─ data/
│  ├─ source/                 人工维护的 CSV 和 display.json
│  ├─ normalized/             生成的数据，随源数据一起提交
│  └─ WEBSITE_DATA.md         数据接口说明
├─ images/                    公司和组合图标
├─ src/                       网页代码与样式
├─ scripts/                   数据生成和 Sites 打包脚本
├─ tests/                     数据和筛选逻辑测试
├─ .github/workflows/         GitHub Pages 自动发布
├─ index.html                 网页入口
├─ package.json               依赖与运行命令
├─ package-lock.json          锁定依赖版本
├─ tsconfig.json              TypeScript 配置
└─ vite.config.ts             网页构建配置
```

## 本地保留、不提交的目录

| 目录 | 用途 | 清理方式 |
| --- | --- | --- |
| `node_modules/` | 已安装的前端依赖 | 可重装，但删除后需先运行 `npm ci` 才能预览 |
| `dist/` | 最近一次网页构建结果 | 可删除，`npm run build` 会重新生成 |
| `.tools/` | 本机 npm 工具和旧表格导出脚本 | 保留 `package/` 和 `bin/`，本机未全局安装 npm 时需要使用 |
| `.preview/` | 临时截图及调试资料 | 可删除，需要时重新生成 |
| `outputs/` | 历史 Excel 导出和核对资料 | 本地归档，不作为数据维护源 |
| `sites/` | Sites 私有站点副本、身份配置和独立 Git 历史 | 保留 `escoop/`；旧的根目录打包文件可清理 |

Python 的 `__pycache__/`、Vite 缓存、日志及操作系统临时文件也不提交。

`data/normalized/` 虽然可重新生成，但当前发布流程会校验它与源数据是否一致，因此仍需要加入 Git。修改数据时只编辑 `data/source/`，运行 `python scripts/prepare_data.py` 后将源文件与生成结果一起提交。

本地预览和发布步骤见 [DEVELOPMENT.md](DEVELOPMENT.md)。
