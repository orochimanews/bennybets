import pytest
from PyQt6.QtWidgets import QApplication
from bennybets.core.settings import AppSettings
from bennybets.ui.main_window import MainWindow

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_main_window_init(qapp):
    settings = AppSettings(auto_refresh_interval=0)
    window = MainWindow(settings=settings, auto_load=False)
    assert window.windowTitle().startswith("BennyBets")
    assert window.table_widget is not None
    assert window.combo_sport.count() >= 3
    window.close()
