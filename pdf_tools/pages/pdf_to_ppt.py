import dearpygui.dearpygui as dpg


def build_page(app) -> None:
    with dpg.group(tag="tool_ppt"):
        app.page_header("PDF 转 PPT", "将 PDF 每页渲染为图片并放入 PPTX 幻灯片。")
        app.file_row("输入 PDF", "ppt_pdf_text", "ppt_pdf")
        dpg.add_text("输出 PPTX")
        dpg.add_input_text(tag="ppt_output", width=-1)
        dpg.add_input_int(label="渲染 DPI", tag="ppt_dpi", default_value=150, min_value=72, max_value=600, min_clamped=True, max_clamped=True, width=180)
        app.primary_button("开始转换", app.run_ppt, tag="ppt_run")
