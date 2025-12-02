import sys
from PySide6.QtWidgets import QApplication
from .gui import MainWindow

def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
