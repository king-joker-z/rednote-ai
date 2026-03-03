# 🔥 RedNote AI

> AI-powered Xiaohongshu (小红书) content automation for AI/Tech creators

**从 AI 热点追踪 → 爆文风格仿写 → 配图生成 → 人工审核 → 一键发布**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)

## ✨ Features

- 📡 **多源热点抓取** - Twitter/X、Arxiv、GitHub Trending、ProductHunt、RSS
- 🧠 **智能内容分析** - 热点识别、打分排序、爆文风格提取
- ✍️ **爆文风格生成** - 学习小红书爆款套路，生成高互动内容
- 🎨 **自动配图** - 封面图 + 内页图，支持多种 AI 绘图后端
- 👀 **人工审核** - Web 控制台预览、编辑、选择发布
- 📤 **一键发布** - 小红书自动化发布，支持定时
- 🧩 **Skill 沉淀** - 高质量 prompt/模板可复用，越用越强

## 🏗️ Architecture

```
rednote-ai/
├── sources/          # 信息源抓取
├── analyze/          # 内容分析
├── generate/         # 内容生成
├── assets/           # 素材管理
├── publish/          # 发布模块
├── web/              # Web 控制台
├── skills/           # 可复用 Skill
└── config/           # 配置文件
```

## 🚀 Quick Start

```bash
# 克隆项目
git clone https://github.com/king-joker-z/rednote-ai.git
cd rednote-ai

# 安装依赖
pip install -e .

# 配置
cp config/config.example.yaml config/config.yaml
# 编辑 config.yaml 填入 API keys

# 运行
rednote-ai fetch      # 抓取热点
rednote-ai generate   # 生成内容
rednote-ai web        # 启动 Web 控制台
```

## 🔌 Supported AI Backends

| 用途 | 支持的模型 |
|------|-----------|
| 文案生成 | Claude 3.5, GPT-4o, 文心一言, 通义千问, GLM-4 |
| 图片生成 | Midjourney, DALL-E 3, Stable Diffusion, 即梦 |
| 热点分析 | GPT-4o-mini, Claude Haiku, GLM-4-Flash |

## 📖 Documentation

- [安装指南](docs/installation.md)
- [配置说明](docs/configuration.md)
- [信息源配置](docs/sources.md)
- [Skill 开发](docs/skills.md)
- [API 文档](docs/api.md)

## 🎯 Roadmap

- [x] 项目初始化
- [ ] Phase 1: 核心抓取 + 生成
- [ ] Phase 2: Web 控制台 + 配图
- [ ] Phase 3: 自动发布 + Skill 沉淀

## 🤝 Contributing

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

**⚠️ 免责声明**: 本工具仅供学习研究，请遵守小红书平台规则，合理使用。
