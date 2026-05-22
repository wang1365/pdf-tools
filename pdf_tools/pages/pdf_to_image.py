import dearpygui.dearpygui as dpg


def build_page(app) -> None:
    with dpg.group(tag="tool_image"):
        app.page_header("PDF 转图片", "导出每页图片，或生成一张纵向拼接长图。")
        app.file_row("输入 PDF", "image_pdf_text", "image_pdf")
        app.dir_row("输出文件夹", "image_out_dir")
        with dpg.group(horizontal=True):
            dpg.add_combo(["png", "jpg", "jpeg"], label="格式", tag="image_format", default_value="png", width=150)
            dpg.add_input_int(label="DPI", tag="image_dpi", default_value=150, min_value=72, max_value=600, min_clamped=True, max_clamped=True, width=160)
        dpg.add_radio_button(["逐页导出", "合并为长图"], tag="image_mode", default_value="逐页导出")
        dpg.add_text("长图文件名")
        dpg.add_input_text(tag="image_single_name", width=-1)
        app.primary_button("开始转换", app.run_image, tag="image_run")
