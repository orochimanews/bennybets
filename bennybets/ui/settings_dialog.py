from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
    QTabWidget, QWidget, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

from bennybets.core.settings import AppSettings

class SettingsDialog(QDialog):
    """Boîte de dialogue des paramètres personnalisables et persistants"""

    settings_applied = pyqtSignal(AppSettings)

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Paramètres BennyBets")
        self.setMinimumSize(520, 420)
        self.resize(560, 460)
        self._setup_ui()

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

        # Sources personnalisées
        lbl_custom = QLabel("<b>Sources d'adresses et événements personnalisés :</b>")
        sources_layout.addWidget(lbl_custom)

        self.list_custom = QListWidget()
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
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.setStyleSheet("background: #10b981; color: white; font-weight: bold;")
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
        self.settings.enabled_providers = enabled_bk

        # Sauvegarder sur disque
        self.settings.save()
        self.settings_applied.emit(self.settings)
        self.accept()
