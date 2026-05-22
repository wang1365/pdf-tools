import dearpygui.dearpygui as dpg


def build_page(app) -> None:
    with dpg.group(tag="tool_compress"):
        app.page_header("PDF 压缩", "压缩页面内容流并清理重复对象，输出新的 PDF 文件。")
        app.file_row("输入 PDF", "compress_pdf_text", "compress_pdf")
        dpg.add_text("输出 PDF")
        dpg.add_input_text(tag="compress_output", width=-1)
        app.primary_button("开始压缩", app.run_compress, tag="compress_run")
