# AGENTS.md

本文件是 Codex 在 `pdf-tools` 项目中的初始化与协作说明。

## 语言与文档要求

- 与本项目相关的说明、设计文档、实施计划、测试记录、提交说明草稿、评审反馈和交付总结一律使用中文生成。
- 代码标识符、命令、文件路径、第三方库名称和错误原文可保留英文。
- 面向用户的界面文案应使用简体中文，避免出现乱码或中英混杂的占位文案。

## 项目概览

`pdf-tools` 是一个 Python PDF 工具项目，包含命令行入口和 PySide6 桌面端入口。

- CLI 入口：`pdf-tools`，对应 `pdf_tools.__main__:main`
- GUI 入口：`pdf-tools-gui`，对应 `pdf_tools.gui_main:main`
- 核心转换能力：`pdf_tools/converter.py`
- 桌面端主窗口：`pdf_tools/gui.py`
- 桌面端功能页：`pdf_tools/pages/`

## 常用命令

安装依赖：

```bash
uv sync
```

或：

```bash
pip install -e .
```

运行命令行工具：

```bash
pdf-tools input.pdf -o output.docx --overwrite
```

运行桌面端：

```bash
pdf-tools-gui
```

或：

```bash
python -m pdf_tools.gui_main
```

运行测试：

```bash
pytest
```

## 开发约定

- 优先保持现有 PySide6 架构，不引入新的 UI 框架，除非用户明确要求。
- 修改桌面端界面时，应保持政企工具风：克制、稳定、清晰、低噪音。
- 新增或调整页面时，优先复用共享 UI 组件，避免继续复制各页面中的重复控件逻辑。
- PDF 处理逻辑应与界面层解耦，耗时任务继续放在线程中执行，避免阻塞主界面。
- 不要改动与当前任务无关的功能、文案或格式。
- 如果工作区已有未跟踪或未提交文件，默认视为用户已有工作，不要擅自删除或回退。

## 文档位置

- 设计文档放在 `docs/superpowers/specs/`。
- 实施计划、验证记录或其他项目资料也应使用中文撰写。
