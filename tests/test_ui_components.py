import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QFrame

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


def test_main_window_uses_readable_navigation_labels():
    app = QApplication.instance() or QApplication([])

    from pdf_tools.gui import MainWindow

    window = MainWindow()
    labels = [window.nav.item(i).text() for i in range(window.nav.count())]

    assert labels[0] == "授权中心"
    assert "PDF 合并" in labels
    assert "PDF 转图片" in labels


def test_auth_page_has_clear_action_buttons():
    app = QApplication.instance() or QApplication([])

    from pdf_tools.auth_ui import AuthPage

    page = AuthPage()

    assert page.bind_btn.text() == "生成在线绑定码"
    assert page.open_confirm_btn.text() == "打开网页确认"
    assert page.import_btn.text() == "导入离线 License"
    assert page.refresh_btn.text() == "刷新状态"


def test_auth_page_uses_status_sections():
    app = QApplication.instance() or QApplication([])

    from pdf_tools.auth_ui import AuthPage

    page = AuthPage()
    sections = page.findChildren(QFrame, "Section")

    assert len(sections) >= 3


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


def test_pdf_pages_use_unified_sections():
    app = QApplication.instance() or QApplication([])

    from pdf_tools.pages.pdf_compress import PdfCompressPage
    from pdf_tools.pages.pdf_merge import PdfMergePage
    from pdf_tools.pages.pdf_to_excel import PdfToExcelPage

    assert len(PdfMergePage().findChildren(QFrame, "Section")) >= 2
    assert len(PdfCompressPage().findChildren(QFrame, "Section")) >= 2
    assert len(PdfToExcelPage().findChildren(QFrame, "Section")) >= 1
