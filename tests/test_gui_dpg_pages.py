import unittest
import importlib.util
from pathlib import Path


if importlib.util.find_spec("dearpygui") is None:
    raise unittest.SkipTest("dearpygui is not installed")

from pdf_tools import gui_dpg
from pdf_tools.authorization import AuthorizationResult


class GuiDpgPageTests(unittest.TestCase):
    def test_pdf_to_ppt_page_module_is_not_shadowed_by_converter_function(self):
        self.assertTrue(hasattr(gui_dpg.pdf_to_ppt_page, "build_page"))
        self.assertTrue(callable(gui_dpg.pdf_to_ppt))

    def test_gui_main_loads_when_pyinstaller_executes_file_entrypoint(self):
        gui_main_path = Path(__file__).resolve().parents[1] / "pdf_tools" / "gui_main.py"
        spec = importlib.util.spec_from_file_location("gui_main", gui_main_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader

        spec.loader.exec_module(module)

        self.assertTrue(callable(module.main))

    def test_authorization_summary_does_not_expose_user_id(self):
        summary = gui_dpg.get_authorization_summary(
            AuthorizationResult(
                True,
                "ok",
                "offline",
                {
                    "edition": "pro",
                    "user_id": "user-1",
                    "expires_at": "2026-05-24T00:00:00Z",
                },
            )
        )

        self.assertNotIn("user", summary)
