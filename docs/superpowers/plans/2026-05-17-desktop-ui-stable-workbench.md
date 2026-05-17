# PDF Tools 桌面端稳定工作台实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 将 PySide6 桌面端优化为政企工具风的稳定工作台，并保持现有 PDF 处理行为不变。

**架构：** 保留 `QMainWindow + QListWidget + QStackedWidget` 主结构，新增共享主题和 UI 组件，逐步迁移授权页与各 PDF 工具页。业务线程、授权服务和转换逻辑不做重写。

**技术栈：** Python 3.12、PySide6、pytest、pypdf、pdf2docx、PyMuPDF、python-pptx。

---

## 文件结构

- 新建 `pdf_tools/theme.py`：集中定义桌面端全局 QSS、颜色、窗口尺寸辅助函数。
- 新建 `pdf_tools/ui_components.py`：共享页面标题、分区容器、拖拽文件区、路径行、操作行、状态标签等组件。
- 修改 `pdf_tools/gui.py`：应用全局主题，优化主窗口尺寸、侧边栏和页面名称。
- 修改 `pdf_tools/auth_ui.py`：把授权中心改成状态卡片式布局。
- 修改 `pdf_tools/pages/*.py`：迁移到共享组件，修复界面中文文案乱码，保持原有线程和交互。
- 新建 `tests/test_ui_components.py`：验证共享组件的纯逻辑和可实例化行为。

---

### 任务 1：新增共享 UI 组件与测试

**文件：**
- 新建：`pdf_tools/theme.py`
- 新建：`pdf_tools/ui_components.py`
- 新建：`tests/test_ui_components.py`

- [ ] **步骤 1：写失败测试**

```python
from pathlib import Path

from PySide6.QtWidgets import QApplication

from pdf_tools.ui_components import DropArea, format_file_size


def test_format_file_size_uses_human_readable_units():
    assert format_file_size(1) == "1 B"
    assert format_file_size(1536) == "1.50 KB"
    assert format_file_size(2 * 1024 * 1024) == "2.00 MB"


def test_drop_area_displays_selected_file(tmp_path):
    app = QApplication.instance() or QApplication([])
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    widget = DropArea()
    widget.update_file(Path(pdf))

    assert "sample.pdf" in widget.text()
    assert "8 B" in widget.text()
```

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m pytest tests/test_ui_components.py -v`

预期：失败，原因是 `pdf_tools.ui_components` 尚不存在。

- [ ] **步骤 3：实现 `theme.py` 和 `ui_components.py`**

实现内容：

- `get_app_stylesheet()`
- `recommended_window_size(screen_size)`
- `format_file_size(size)`
- `DropArea`
- `create_page_header(title, description)`
- `Section`
- `PathSelectorRow`
- `ActionRow`
- `StatusLabel`

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m pytest tests/test_ui_components.py -v`

预期：通过。

---

### 任务 2：优化主窗口外壳

**文件：**
- 修改：`pdf_tools/gui.py`

- [ ] **步骤 1：写主窗口实例化测试**

在 `tests/test_ui_components.py` 追加：

```python
def test_main_window_uses_readable_navigation_labels():
    app = QApplication.instance() or QApplication([])

    from pdf_tools.gui import MainWindow

    window = MainWindow()
    labels = [window.nav.item(i).text() for i in range(window.nav.count())]

    assert labels[0] == "授权中心"
    assert "PDF 合并" in labels
    assert "PDF 转图片" in labels
```

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m pytest tests/test_ui_components.py::test_main_window_uses_readable_navigation_labels -v`

预期：失败，原因是当前导航文案乱码或样式未迁移。

- [ ] **步骤 3：修改 `gui.py`**

实现内容：

- 使用 `get_app_stylesheet()`
- 使用 `recommended_window_size()`
- 主内容边距调整为政企工作台风格。
- 侧边栏固定宽度约 210。
- 导航文案全部改为简体中文。

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m pytest tests/test_ui_components.py::test_main_window_uses_readable_navigation_labels -v`

预期：通过。

---

### 任务 3：迁移授权中心

**文件：**
- 修改：`pdf_tools/auth_ui.py`

- [ ] **步骤 1：写授权页实例化测试**

在 `tests/test_ui_components.py` 追加：

```python
def test_auth_page_has_clear_action_buttons():
    app = QApplication.instance() or QApplication([])

    from pdf_tools.auth_ui import AuthPage

    page = AuthPage()

    assert page.bind_btn.text() == "生成在线绑定码"
    assert page.open_confirm_btn.text() == "打开网页确认"
    assert page.import_btn.text() == "导入离线 License"
    assert page.refresh_btn.text() == "刷新状态"
```

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m pytest tests/test_ui_components.py::test_auth_page_has_clear_action_buttons -v`

预期：失败，原因是当前按钮文案乱码。

- [ ] **步骤 3：修改 `auth_ui.py`**

实现内容：

- 使用 `create_page_header`、`Section`、`StatusLabel`。
- 状态、设备指纹、绑定码分区展示。
- 按钮文案修复为简体中文。
- 保留现有授权函数与轮询逻辑。

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m pytest tests/test_ui_components.py::test_auth_page_has_clear_action_buttons -v`

预期：通过。

---

### 任务 4：迁移 PDF 工具页

**文件：**
- 修改：`pdf_tools/pages/pdf_merge.py`
- 修改：`pdf_tools/pages/pdf_split.py`
- 修改：`pdf_tools/pages/pdf_compress.py`
- 修改：`pdf_tools/pages/pdf_encrypt.py`
- 修改：`pdf_tools/pages/pdf_to_word.py`
- 修改：`pdf_tools/pages/pdf_to_ppt.py`
- 修改：`pdf_tools/pages/pdf_to_image.py`
- 修改：`pdf_tools/pages/pdf_to_excel.py`

- [ ] **步骤 1：写页面实例化测试**

在 `tests/test_ui_components.py` 追加：

```python
def test_pdf_pages_expose_clear_primary_actions():
    app = QApplication.instance() or QApplication([])

    from pdf_tools.pages.pdf_compress import PdfCompressPage
    from pdf_tools.pages.pdf_encrypt import PdfEncryptPage
    from pdf_tools.pages.pdf_merge import PdfMergePage
    from pdf_tools.pages.pdf_split import PdfSplitPage
    from pdf_tools.pages.pdf_to_word import PdfToWordPage

    assert PdfMergePage().merge_btn.text() == "开始合并"
    assert PdfSplitPage().split_btn.text() == "开始分割"
    assert PdfCompressPage().compress_btn.text() == "开始压缩"
    assert PdfEncryptPage().encrypt_btn.text() == "开始加密"
    assert PdfToWordPage().convert_btn.text() == "开始转换"
```

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m pytest tests/test_ui_components.py::test_pdf_pages_expose_clear_primary_actions -v`

预期：失败，原因是当前主按钮文案乱码。

- [ ] **步骤 3：迁移单文件输入页面**

实现内容：

- 使用共享 `DropArea`。
- 使用 `Section` 包装输入、参数、输出区域。
- 使用 `PathSelectorRow` 或统一的水平行。
- 使用 `ActionRow` 放置进度条、状态文本和主按钮。
- 修复所有用户可见中文文案。

- [ ] **步骤 4：迁移合并页面**

实现内容：

- 文件列表区域放在“输入文件”分区。
- 保留添加、移除、上移、下移逻辑。
- 输出路径分区和底部操作区使用统一样式。
- 主按钮为“开始合并”。

- [ ] **步骤 5：运行页面测试确认通过**

运行：`python -m pytest tests/test_ui_components.py::test_pdf_pages_expose_clear_primary_actions -v`

预期：通过。

---

### 任务 5：整体验证

**文件：**
- 检查全部改动文件。

- [ ] **步骤 1：运行 Python 编译检查**

运行：`python -m compileall pdf_tools tests`

预期：退出码 0。

- [ ] **步骤 2：运行测试**

运行：`python -m pytest`

预期：全部测试通过。若环境缺少 pytest，记录无法运行的原因。

- [ ] **步骤 3：检查 Git 状态**

运行：`git status --short`

预期：只包含本次计划相关文件，以及用户已有的 `.superpowers/` 临时文件。

---

## 自检

- 设计文档要求的主窗口、授权中心、共享组件、工具页一致性、中文文案和验证步骤均有对应任务。
- 不修改官网项目。
- 不新增 PDF 处理能力。
- 不替换 PySide6 架构。
