import unittest


from pdf_tools import gui_dpg


class GuiDpgPageTests(unittest.TestCase):
    def test_pdf_to_ppt_page_module_is_not_shadowed_by_converter_function(self):
        self.assertTrue(hasattr(gui_dpg.pdf_to_ppt_page, "build_page"))
        self.assertTrue(callable(gui_dpg.pdf_to_ppt))
