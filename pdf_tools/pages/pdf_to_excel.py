from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..ui_components import Section, StatusLabel, create_page_header


class PdfToExcelPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        layout.addWidget(create_page_header("PDF 转 Excel", "该能力尚未实现，后续会接入表格识别与导出流程。"))

        section = Section("当前状态")
        status = StatusLabel("暂未实现。当前版本不会执行 PDF 转 Excel 操作。")
        section.body.addWidget(status)
        layout.addWidget(section)
        layout.addStretch(1)
