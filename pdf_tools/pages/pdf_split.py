import dearpygui.dearpygui as dpg


def build_page(app) -> None:
    with dpg.group(tag="tool_split"):
        app.page_header("PDF 分割", "按固定页数将一个 PDF 拆分为多个文件。")
        app.file_row("输入 PDF", "split_pdf_text", "split_pdf")
        app.dir_row("输出文件夹", "split_out_dir")
        dpg.add_text("输出前缀")
        dpg.add_input_text(tag="split_prefix", width=-1)
        dpg.add_input_int(label="每份页数", tag="split_pages", default_value=10, min_value=1, min_clamped=True, width=180)
        app.primary_button("开始分割", app.run_split, tag="split_run")
