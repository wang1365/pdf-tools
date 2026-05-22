import dearpygui.dearpygui as dpg


def build_page(app) -> None:
    with dpg.group(tag="tool_merge"):
        app.page_header("PDF 合并", "按列表顺序合并多个 PDF 文件。")
        app.secondary_button("添加 PDF", lambda *args: app.open_file_dialog("merge_add"), width=110)
        dpg.add_listbox(tag="merge_list", items=[], num_items=5, width=-1)
        with dpg.group(horizontal=True):
            app.secondary_button("移除选中", app.merge_remove, width=110)
            app.secondary_button("上移", lambda *args: app.merge_move(-1), width=80)
            app.secondary_button("下移", lambda *args: app.merge_move(1), width=80)
        dpg.add_text("输出 PDF")
        dpg.add_input_text(tag="merge_output", width=-1)
        app.primary_button("开始合并", app.run_merge, tag="merge_run")
