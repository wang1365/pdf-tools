import dearpygui.dearpygui as dpg


def build_page(app) -> None:
    with dpg.group(tag="tool_encrypt"):
        app.page_header("PDF 加密", "为 PDF 添加打开密码，生成加密后的副本。")
        app.file_row("输入 PDF", "encrypt_pdf_text", "encrypt_pdf")
        dpg.add_text("密码")
        dpg.add_input_text(tag="encrypt_password", password=True, width=-1)
        dpg.add_text("输出 PDF")
        dpg.add_input_text(tag="encrypt_output", width=-1)
        app.primary_button("开始加密", app.run_encrypt, tag="encrypt_run")
