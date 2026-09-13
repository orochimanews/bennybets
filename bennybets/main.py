import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from bennybets.core.settings import AppSettings
from bennybets.ui.main_window import MainWindow

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )

    # Configuration High DPI Qt
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("BennyBets")
    app.setOrganizationName("BennyBets")

    settings = AppSettings.load()
    window = MainWindow(settings=settings)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
