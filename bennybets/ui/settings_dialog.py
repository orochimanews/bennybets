import os
import tempfile
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
    QTabWidget, QWidget, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QPixmap, QPainter, QColor, QPen

from bennybets.core.settings import AppSettings


def _ensure_checkbox_icons():
    """Génère les icônes de case à cocher haute visibilité sur fond noir"""
    tmpdir = tempfile.gettempdir()
    on_path = os.path.join(tmpdir, "bb_cb_on_v1.png").replace("\\", "/")
    off_path = os.path.join(tmpdir, "bb_cb_off_v1.png").replace("\\", "/")

    if not (os.path.exists(on_path) and os.path.exists(off_path)):
        # Case cochée (vert émeraude avec coche blanche nette)
        pix_on = QPixmap(18, 18)
        pix_on.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix_on)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor("#10b981"))
        p.setPen(QPen(QColor("#10b981"), 1))
        p.drawRoundedRect(1, 1, 16, 16, 3, 3)
        p.setPen(QPen(QColor("#ffffff"), 2.2))
        p.drawLine(4, 9, 7, 13)
        p.drawLine(7, 13, 14, 5)
        p.end()
        pix_on.save(on_path)

        # Case décochée (contour visible gris clair sur fond sombre)
        pix_off = QPixmap(18, 18)
        pix_off.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix_off)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor("#161920"))
        p.setPen(QPen(QColor("#4b5563"), 1.5))
        p.drawRoundedRect(1, 1, 16, 16, 3, 3)
        p.end()
        pix_off.save(off_path)

    return on_path, off_path


class SettingsDialog(QDialog):
    """Boîte de dialogue des paramètres avec fond noir et écriture blanche haute lisibilité"""

    settings_applied = pyqtSignal(AppSettings)

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Paramètres BennyBets")
        self.setMinimumSize(580, 500)
        self.resize(620, 540)
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        tabs = QTabWidget()

        # Onglet 1 : Apparence & Style
        tab_appearance = QWidget()
        app_layout = QVBoxLayout(tab_appearance)
        app_layout.setSpacing(12)

        # Taille de police
        font_box = QHBoxLayout()
        lbl_font = QLabel("Taille de la police de caractère :")
        self.spin_font = QSpinBox()
        self.spin_font.setRange(9, 18)
        self.spin_font.setValue(self.settings.font_size)
        self.spin_font.setSuffix(" px")
        font_box.addWidget(lbl_font)
        font_box.addWidget(self.spin_font)
        font_box.addStretch()
        app_layout.addLayout(font_box)

        # Thème de couleur
        theme_box = QHBoxLayout()
        lbl_theme = QLabel("Thème et style visuel :")
        self.combo_theme = QComboBox()
        self.combo_theme.addItem("Dark Moderne (Sombre)", "dark")
        self.combo_theme.addItem("Midnight Blue (Bleu Nuit)", "midnight")
        self.combo_theme.addItem("Light (Clair & Épuré)", "light")
        
        # Sélection du thème courant
        idx = self.combo_theme.findData(self.settings.theme)
        if idx != -1:
            self.combo_theme.setCurrentIndex(idx)
        theme_box.addWidget(lbl_theme)
        theme_box.addWidget(self.combo_theme)
        theme_box.addStretch()
        app_layout.addLayout(theme_box)

        app_layout.addStretch()
        tabs.addTab(tab_appearance, "🎨 Apparence")

        # Onglet 2 : Actualisation & Détection
        tab_scanner = QWidget()
        scan_layout = QVBoxLayout(tab_scanner)
        scan_layout.setSpacing(12)

        # Intervalle d'auto-refresh
        refresh_box = QHBoxLayout()
        lbl_refresh = QLabel("Actualisation automatique en direct :")
        self.combo_refresh = QComboBox()
        self.combo_refresh.addItem("Désactivé (Manuel uniquement)", 0)
        self.combo_refresh.addItem("Toutes les 10 secondes (Ultra rapide)", 10)
        self.combo_refresh.addItem("Toutes les 30 secondes (Recommandé)", 30)
        self.combo_refresh.addItem("Toutes les 60 secondes", 60)
        
        idx_ref = self.combo_refresh.findData(self.settings.auto_refresh_interval)
        if idx_ref != -1:
            self.combo_refresh.setCurrentIndex(idx_ref)
        refresh_box.addWidget(lbl_refresh)
        refresh_box.addWidget(self.combo_refresh)
        refresh_box.addStretch()
        scan_layout.addLayout(refresh_box)

        # Seuil Value Bet
        value_box = QHBoxLayout()
        lbl_value = QLabel("Seuil d'anomalie de cote (Value Bet) :")
        self.spin_value_thresh = QDoubleSpinBox()
        self.spin_value_thresh.setRange(2.0, 50.0)
        self.spin_value_thresh.setValue(self.settings.value_bet_threshold)
        self.spin_value_thresh.setSuffix(" % d'écart")
        value_box.addWidget(lbl_value)
        value_box.addWidget(self.spin_value_thresh)
        value_box.addStretch()
        scan_layout.addLayout(value_box)

        # Mise par défaut du calculateur
        stake_box = QHBoxLayout()
        lbl_stake = QLabel("Mise de référence par défaut :")
        self.spin_stake = QDoubleSpinBox()
        self.spin_stake.setRange(5.0, 10000.0)
        self.spin_stake.setValue(self.settings.default_total_stake)
        self.spin_stake.setPrefix("€ ")
        stake_box.addWidget(lbl_stake)
        stake_box.addWidget(self.spin_stake)
        stake_box.addStretch()
        scan_layout.addLayout(stake_box)

        scan_layout.addStretch()
        tabs.addTab(tab_scanner, "⚡ Scanner & Alertes")

        # Onglet 3 : Bookmakers & Sources
        tab_sources = QWidget()
        sources_layout = QVBoxLayout(tab_sources)
        sources_layout.setSpacing(10)

        # Bookmakers natifs
        lbl_bk = QLabel("<b>Bookmakers français surveillés :</b>")
        sources_layout.addWidget(lbl_bk)
        
        self.chk_winamax = QCheckBox("Winamax (Flux réel cotes & live)")
        self.chk_winamax.setChecked("Winamax" in self.settings.enabled_providers)
        sources_layout.addWidget(self.chk_winamax)

        self.chk_betclic = QCheckBox("Betclic (Flux réel cotes & live)")
        self.chk_betclic.setChecked("Betclic" in self.settings.enabled_providers)
        sources_layout.addWidget(self.chk_betclic)

        self.chk_unibet = QCheckBox("Unibet (Flux réel cotes & live)")
        self.chk_unibet.setChecked("Unibet" in self.settings.enabled_providers)
        sources_layout.addWidget(self.chk_unibet)

        self.chk_genybet = QCheckBox("Genybet (Réseau Sportnco - Flux réel)")
        self.chk_genybet.setChecked("Genybet" in self.settings.enabled_providers)
        sources_layout.addWidget(self.chk_genybet)

        self.chk_pokerstars = QCheckBox("PokerStars Sports (Flux réel cotes)")
        self.chk_pokerstars.setChecked("PokerStars" in self.settings.enabled_providers)
        sources_layout.addWidget(self.chk_pokerstars)

        self.chk_pmu = QCheckBox("PMU Sport (Cotes & live)")
        self.chk_pmu.setChecked("PMU" in self.settings.enabled_providers)
        sources_layout.addWidget(self.chk_pmu)

        self.chk_bwin = QCheckBox("Bwin (Cotes & live)")
        self.chk_bwin.setChecked("Bwin" in self.settings.enabled_providers)
        sources_layout.addWidget(self.chk_bwin)

        # Sources personnalisées
        lbl_custom = QLabel("<b>Sources d'adresses et événements personnalisés :</b>")
        sources_layout.addWidget(lbl_custom)

        self.list_custom = QListWidget()
        self.list_custom.setMaximumHeight(85)
        self._populate_custom_sources()
        sources_layout.addWidget(self.list_custom)

        # Formulaire ajout source
        add_form = QHBoxLayout()
        self.txt_source_name = QLineEdit()
        self.txt_source_name.setPlaceholderText("Nom (ex: MonFlux)")
        self.txt_source_url = QLineEdit()
        self.txt_source_url.setPlaceholderText("URL JSON (ex: https://... ou file://...)")
        btn_add_source = QPushButton("Ajouter")
        btn_add_source.clicked.connect(self._add_custom_source)
        add_form.addWidget(self.txt_source_name)
        add_form.addWidget(self.txt_source_url)
        add_form.addWidget(btn_add_source)
        sources_layout.addLayout(add_form)

        btn_remove_source = QPushButton("Supprimer la source sélectionnée")
        btn_remove_source.clicked.connect(self._remove_custom_source)
        sources_layout.addWidget(btn_remove_source, alignment=Qt.AlignmentFlag.AlignRight)

        tabs.addTab(tab_sources, "🌐 Sources & Bookmakers")

        layout.addWidget(tabs)

        # Boutons Enregistrer / Annuler
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Enregistrer les paramètres")
        btn_save.setObjectName("BtnSave")
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.clicked.connect(self._save_settings)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

    def _populate_custom_sources(self):
        self.list_custom.clear()
        for src in self.settings.custom_sources:
            item = QListWidgetItem(f"{src.get('name')} -> {src.get('url')}")
            self.list_custom.addItem(item)

    def _add_custom_source(self):
        name = self.txt_source_name.text().strip()
        url = self.txt_source_url.text().strip()
        if not name or not url:
            QMessageBox.warning(self, "Champs requis", "Veuillez saisir un nom et une adresse URL valide.")
            return

        self.settings.custom_sources.append({
            "name": name,
            "url": url,
            "sport": "football",
            "enabled": True
        })
        self.txt_source_name.clear()
        self.txt_source_url.clear()
        self._populate_custom_sources()

    def _remove_custom_source(self):
        row = self.list_custom.currentRow()
        if 0 <= row < len(self.settings.custom_sources):
            del self.settings.custom_sources[row]
            self._populate_custom_sources()

    def _save_settings(self):
        # Mettre à jour l'objet settings
        self.settings.font_size = self.spin_font.value()
        self.settings.theme = self.combo_theme.currentData()
        self.settings.auto_refresh_interval = self.combo_refresh.currentData()
        self.settings.value_bet_threshold = self.spin_value_thresh.value()
        self.settings.default_total_stake = self.spin_stake.value()

        # Bookmakers
        enabled_bk = []
        if self.chk_winamax.isChecked():
            enabled_bk.append("Winamax")
        if self.chk_betclic.isChecked():
            enabled_bk.append("Betclic")
        if self.chk_unibet.isChecked():
            enabled_bk.append("Unibet")
        if self.chk_genybet.isChecked():
            enabled_bk.append("Genybet")
        if self.chk_pokerstars.isChecked():
            enabled_bk.append("PokerStars")
        if self.chk_pmu.isChecked():
            enabled_bk.append("PMU")
        if self.chk_bwin.isChecked():
            enabled_bk.append("Bwin")
        self.settings.enabled_providers = enabled_bk

        # Sauvegarder sur disque
        self.settings.save()
        self.settings_applied.emit(self.settings)
        self.accept()

    def _apply_styling(self):
        """Applique le style fond noir intégrale avec typographie blanche contrastée"""
        on_path, off_path = _ensure_checkbox_icons()
        fs = self.settings.font_size
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #000000;
            }}
            QWidget {{
                background-color: #000000;
                color: #ffffff;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                font-size: {fs}px;
            }}
            QLabel {{
                background-color: transparent;
                color: #ffffff;
                font-size: {fs}px;
            }}
            QTabWidget {{
                background-color: #000000;
            }}
            QTabWidget::pane {{
                border: 1px solid #282d37;
                background-color: #0a0c10;
                border-radius: 6px;
                top: -1px;
                padding: 10px;
            }}
            QTabBar::tab {{
                background-color: #14171d;
                color: #9ca3af;
                border: 1px solid #282d37;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 4px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: #0a0c10;
                color: #ffffff;
                border-top: 2px solid #10b981;
                border-bottom: 1px solid #0a0c10;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #1e232d;
                color: #ffffff;
            }}
            QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {{
                background-color: #161920;
                border: 1px solid #363c4a;
                border-radius: 4px;
                padding: 5px 8px;
                color: #ffffff;
                font-size: {fs}px;
            }}
            QLineEdit {{
                placeholder-text-color: #9ca3af;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QLineEdit:focus {{
                border-color: #10b981;
                background-color: #1a1e26;
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 18px;
                border-left: 1px solid #363c4a;
                border-bottom: 1px solid #363c4a;
                background-color: #222733;
                border-top-right-radius: 4px;
            }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 18px;
                border-left: 1px solid #363c4a;
                background-color: #222733;
                border-bottom-right-radius: 4px;
            }}
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: #2e3546;
            }}
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid #ffffff;
            }}
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #ffffff;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 22px;
                border-left: 1px solid #363c4a;
                background-color: #222733;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }}
            QComboBox::down-arrow {{
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #ffffff;
            }}
            QComboBox QAbstractItemView {{
                background-color: #161920;
                color: #ffffff;
                border: 1px solid #363c4a;
                selection-background-color: #10b981;
                selection-color: #ffffff;
                padding: 4px;
                outline: none;
            }}
            QListWidget {{
                background-color: #161920;
                border: 1px solid #363c4a;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px;
            }}
            QListWidget::item {{
                color: #ffffff;
                padding: 4px 6px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: #2563eb;
                color: #ffffff;
            }}
            QCheckBox {{
                background-color: transparent;
                color: #ffffff;
                spacing: 8px;
                font-size: {fs}px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            QCheckBox::indicator:unchecked {{
                image: url({off_path});
            }}
            QCheckBox::indicator:checked {{
                image: url({on_path});
            }}
            QPushButton {{
                background-color: #1e222b;
                border: 1px solid #363c4a;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px 14px;
                font-weight: 500;
                font-size: {fs}px;
            }}
            QPushButton:hover {{
                background-color: #2b303d;
                border-color: #4b5563;
            }}
            QPushButton#BtnSave {{
                background-color: #10b981;
                border: none;
                color: #ffffff;
                font-weight: bold;
            }}
            QPushButton#BtnSave:hover {{
                background-color: #059669;
            }}
        """)
