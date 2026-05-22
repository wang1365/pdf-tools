import dearpygui.dearpygui as dpg


def build_page(app) -> None:
    with dpg.group(tag="tool_word"):
        app.page_header("PDF 转 Word", "将 PDF 转换为 DOCX 文档，可指定页码范围。")
        app.file_row("输入 PDF", "word_pdf_text", "word_pdf")
        app.dir_row("输出文件夹", "word_out_dir")
        dpg.add_text("输出文件名")
        dpg.add_input_text(tag="word_file", width=-1)
        with dpg.group(horizontal=True):
            dpg.add_input_int(label="起始页", tag="word_start", default_value=0, min_value=0, min_clamped=True, width=180)
            dpg.add_input_int(label="结束页（0 表示全部）", tag="word_end", default_value=0, min_value=0, min_clamped=True, width=220)
        dpg.add_checkbox(label="覆盖已存在文件", tag="word_overwrite", default_value=False)
        app.primary_button("开始转换", app.run_word, tag="word_run")
