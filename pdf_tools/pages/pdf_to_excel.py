import dearpygui.dearpygui as dpg


def build_page(app) -> None:
    with dpg.group(tag="tool_excel"):
        app.page_header("PDF 转 Excel", "该功能入口已保留，后续接入表格识别实现。")
        dpg.add_text("暂未实现", color=(100, 116, 139))
