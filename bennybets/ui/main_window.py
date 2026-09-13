from datetime import datetime
from typing import List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QStatusBar, QMessageBox,
    QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor, QIcon, QCloseEvent

from bennybets.core.models import AggregatedEvent, Sport, OpportunityType
from bennybets.core.settings import AppSettings
from bennybets.ui.theme import get_stylesheet
from bennybets.ui.worker import OddsFetchWorker
from bennybets.ui.odds_table import OddsTableWidget
from bennybets.ui.detail_dialog import MatchDetailDialog
from bennybets.ui.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    """Fenêtre principale stabilisée et haute performance de BennyBets"""

    def __init__(self, settings: Optional[AppSettings] = None, auto_load: bool = True):
        super().__init__()
        self.settings = settings or AppSettings.load()
        self.current_sport = Sport.FOOTBALL
        self.all_events: List[AggregatedEvent] = []
        self.worker: Optional[OddsFetchWorker] = None
        
        # Filtres actifs
        self.filter_live = False
        self.filter_surebet = False
        self.filter_value = False

        # Timer de debounce pour la recherche
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(250)
        self.search_timer.timeout.connect(self._refresh_table_view)

        self.setWindowTitle("BennyBets — Comparateur de Cotes & Détecteur d'Arbitrage")
        self.setMinimumSize(1020, 620)
        self.resize(1240, 740)

        self._setup_ui()
        self._apply_theme()
        self._setup_auto_refresh()

        if auto_load:
            self.refresh_odds()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Barre supérieure sticky (TopBar)
        topbar = QWidget()
        topbar.setObjectName("TopBar")
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.setSpacing(10)

        # Logo épuré
        lbl_logo = QLabel("⚡ BennyBets")
        lbl_logo.setObjectName("LogoLabel")
        top_layout.addWidget(lbl_logo)

        # Sélecteur de Sport
        self.combo_sport = QComboBox()
        self.combo_sport.addItem("⚽ Football", Sport.FOOTBALL)
        self.combo_sport.addItem("🎾 Tennis", Sport.TENNIS)
        self.combo_sport.addItem("🏀 Basketball", Sport.BASKETBALL)
        self.combo_sport.currentIndexChanged.connect(self._on_sport_changed)
        top_layout.addWidget(self.combo_sport)

        lbl_sep1 = QLabel("|")
        lbl_sep1.setStyleSheet("color: #374151; padding: 0 4px;")
        top_layout.addWidget(lbl_sep1)

        # Boutons filtres
        self.btn_filter_all = QPushButton("Tous")
        self.btn_filter_all.setObjectName("FilterActive")
        self.btn_filter_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_filter_all.clicked.connect(self._filter_all)
        top_layout.addWidget(self.btn_filter_all)

        self.btn_filter_live = QPushButton("⚡ Live")
        self.btn_filter_live.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_filter_live.setToolTip("Afficher uniquement les matchs en direct")
        self.btn_filter_live.clicked.connect(self._toggle_filter_live)
        top_layout.addWidget(self.btn_filter_live)

        self.btn_filter_surebet = QPushButton("🔥 Surebets")
        self.btn_filter_surebet.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_filter_surebet.setToolTip("Afficher uniquement les arbitrages avec profit garanti")
        self.btn_filter_surebet.clicked.connect(self._toggle_filter_surebet)
        top_layout.addWidget(self.btn_filter_surebet)

        self.btn_filter_value = QPushButton("💎 Décalages")
        self.btn_filter_value.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_filter_value.setToolTip("Afficher les grosses anomalies de cotes")
        self.btn_filter_value.clicked.connect(self._toggle_filter_value)
        top_layout.addWidget(self.btn_filter_value)

        lbl_sep2 = QLabel("|")
        lbl_sep2.setStyleSheet("color: #374151; padding: 0 4px;")
        top_layout.addWidget(lbl_sep2)

        # Barre de recherche rapide avec debounce
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Filtrer un match, club, ligue...")
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.textChanged.connect(self._on_search_text_changed)
        top_layout.addWidget(self.txt_search, stretch=1)

        # Bouton Actualiser
        self.btn_refresh = QPushButton("🔄 Actualiser")
        self.btn_refresh.setObjectName("BtnRefresh")
        self.btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_refresh.clicked.connect(self.refresh_odds)
        top_layout.addWidget(self.btn_refresh)

        # Bouton Paramètres ⚙️
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setObjectName("BtnSettings")
        self.btn_settings.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_settings.setToolTip("Paramètres (police, thème, sources)")
        self.btn_settings.clicked.connect(self._open_settings)
        top_layout.addWidget(self.btn_settings)

        main_layout.addWidget(topbar)

        # 2. Tableau principal natif ultra-rapide
        self.table_widget = OddsTableWidget(bookmakers=self.settings.enabled_providers)
        self.table_widget.match_selected.connect(self._show_match_details)
        main_layout.addWidget(self.table_widget, stretch=1)

        # 3. Barre d'état
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Initialisation de BennyBets...")

    def _apply_theme(self):
        qss = get_stylesheet(theme=self.settings.theme, font_size=self.settings.font_size)
        self.setStyleSheet(qss)

    def _setup_auto_refresh(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_odds)
        self._update_timer_interval()

    def _update_timer_interval(self):
        sec = self.settings.auto_refresh_interval
        if sec > 0:
            self.timer.start(sec * 1000)
        else:
            self.timer.stop()

    def refresh_odds(self):
        # Empêcher tout double lancement
        if self.worker and self.worker.isRunning():
            return

        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("⏳ Analyse...")
        self.status_bar.showMessage(f"Récupération des flux cotes en direct ({self.current_sport.value})...")

        self.worker = OddsFetchWorker(sport=self.current_sport, settings=self.settings)
        self.worker.data_loaded.connect(self._on_data_loaded)
        self.worker.status_message.connect(self.status_bar.showMessage)
        self.worker.error_message.connect(self._on_worker_error)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_data_loaded(self, events: List[AggregatedEvent]):
        self.all_events = events
        self._refresh_table_view()

        surebets_count = sum(1 for e in events if e.has_surebet)
        values_count = sum(1 for e in events if e.has_value_bet)
        now_str = datetime.now().strftime("%H:%M:%S")

        msg = (
            f"Dernière actualisation à {now_str} • "
            f"{len(events)} matchs analysés • "
            f"🔥 {surebets_count} Surebet(s) garanti(s) • "
            f"💎 {values_count} Décalage(s) important(s)"
        )
        self.status_bar.showMessage(msg)

    def _on_worker_error(self, err_msg: str):
        self.status_bar.showMessage(f"Alerte : {err_msg}")

    def _on_worker_finished(self):
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("🔄 Actualiser")

    def _on_search_text_changed(self, text: str):
        # Redémarrer le debounce pour fluidité parfaite
        self.search_timer.start()

    def _refresh_table_view(self):
        self.table_widget.load_events(
            events=self.all_events,
            filter_text=self.txt_search.text(),
            only_live=self.filter_live,
            only_surebet=self.filter_surebet,
            only_value=self.filter_value,
            bookmakers=self.settings.enabled_providers
        )

    def _on_sport_changed(self, index: int):
        self.current_sport = self.combo_sport.currentData()
        self.refresh_odds()

    def _filter_all(self):
        self.filter_live = False
        self.filter_surebet = False
        self.filter_value = False
        self._reset_filter_buttons()
        self.btn_filter_all.setObjectName("FilterActive")
        self._reapply_widget_style(self.btn_filter_all)
        self._refresh_table_view()

    def _toggle_filter_live(self):
        self.filter_live = not self.filter_live
        self._update_filter_button_state(self.btn_filter_live, self.filter_live)
        self._refresh_table_view()

    def _toggle_filter_surebet(self):
        self.filter_surebet = not self.filter_surebet
        self._update_filter_button_state(self.btn_filter_surebet, self.filter_surebet)
        self._refresh_table_view()

    def _toggle_filter_value(self):
        self.filter_value = not self.filter_value
        self._update_filter_button_state(self.btn_filter_value, self.filter_value)
        self._refresh_table_view()

    def _reset_filter_buttons(self):
        for btn in [self.btn_filter_all, self.btn_filter_live, self.btn_filter_surebet, self.btn_filter_value]:
            btn.setObjectName("")
            self._reapply_widget_style(btn)

    def _update_filter_button_state(self, btn: QPushButton, is_active: bool):
        self.btn_filter_all.setObjectName("")
        self._reapply_widget_style(self.btn_filter_all)
        btn.setObjectName("FilterActive" if is_active else "")
        self._reapply_widget_style(btn)

    def _reapply_widget_style(self, widget: QWidget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _show_match_details(self, event: AggregatedEvent):
        dialog = MatchDetailDialog(
            event=event,
            default_stake=self.settings.default_total_stake,
            parent=self
        )
        dialog.exec()

    def _open_settings(self):
        dialog = SettingsDialog(settings=self.settings, parent=self)
        dialog.settings_applied.connect(self._on_settings_applied)
        dialog.exec()

    def _on_settings_applied(self, updated_settings: AppSettings):
        self.settings = updated_settings
        self.table_widget.set_bookmakers(self.settings.enabled_providers)
        self._apply_theme()
        self._update_timer_interval()
        self.refresh_odds()

    def closeEvent(self, event: QCloseEvent):
        # Arrêt sécurisé du timer et du worker thread
        self.timer.stop()
        self.search_timer.stop()
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(500)
        event.accept()
