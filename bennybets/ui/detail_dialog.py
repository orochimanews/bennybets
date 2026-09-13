from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDoubleSpinBox, QGroupBox,
    QHeaderView, QWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QCursor

from bennybets.core.models import AggregatedEvent, OpportunityType, Odd

class MatchDetailDialog(QDialog):
    """Modale détaillée d'un match avec comparateur et calculateur de mise Surebet"""

    def __init__(self, event: AggregatedEvent, default_stake: float = 100.0, parent=None):
        super().__init__(parent)
        self.event = event
        self.default_stake = default_stake
        self.setWindowTitle(f"Détails & Cotes : {event.title}")
        self.setMinimumSize(640, 480)
        self.resize(720, 540)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # En-tête
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        title_lbl = QLabel(f"<h2 style='margin:0; color:#10b981;'>{self.event.home_team} <span style='color:#8a94a6;'>vs</span> {self.event.away_team}</h2>")
        title_lbl.setTextFormat(Qt.TextFormat.RichText)
        header_layout.addWidget(title_lbl)

        info_parts = []
        if self.event.is_live:
            score_str = f" [Score: {self.event.score}]" if self.event.score else ""
            info_parts.append(f"<span style='color:#ef4444; font-weight:bold;'>⚡ LIVE EN DIRECT{score_str}</span>")
        elif self.event.start_time:
            info_parts.append(f"Heure de début: {self.event.start_time.strftime('%d/%m/%Y à %H:%M')}")
        if self.event.competition:
            info_parts.append(f"Compétition: <b>{self.event.competition}</b>")

        info_lbl = QLabel(" • ".join(info_parts))
        info_lbl.setTextFormat(Qt.TextFormat.RichText)
        info_lbl.setStyleSheet("color: #8a94a6; font-size: 11px;")
        header_layout.addWidget(info_lbl)
        layout.addWidget(header_widget)

        # Section 1 : Comparatif des bookmakers
        comp_group = QGroupBox("Comparatif des cotes par bookmaker (Marché 1N2)")
        comp_layout = QVBoxLayout(comp_group)
        comp_layout.setContentsMargins(8, 12, 8, 8)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Bookmaker", "Cote 1 (Domicile)", "Cote N (Nul)", "Cote 2 (Extérieur)", "Accès Direct"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setRowCount(len(self.event.bookmaker_events))

        for row, (bk_name, bk_event) in enumerate(self.event.bookmaker_events.items()):
            table.setItem(row, 0, QTableWidgetItem(bk_name))

            mkt = bk_event.markets.get("1N2") or bk_event.markets.get("12")
            o1 = mkt.outcomes.get("1") if mkt else None
            on = mkt.outcomes.get("N") if mkt else None
            o2 = mkt.outcomes.get("2") if mkt else None

            table.setItem(row, 1, QTableWidgetItem(f"{o1.value:.2f}" if o1 else "—"))
            table.setItem(row, 2, QTableWidgetItem(f"{on.value:.2f}" if on else "—"))
            table.setItem(row, 3, QTableWidgetItem(f"{o2.value:.2f}" if o2 else "—"))

            btn_open = QPushButton(f"Ouvrir {bk_name} ↗")
            btn_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_open.setStyleSheet("padding: 2px 8px; font-size: 11px; background: #2563eb; color: white; border: none; border-radius: 3px;")
            if bk_event.url:
                url_to_open = bk_event.url
                btn_open.clicked.connect(lambda checked, u=url_to_open: QDesktopServices.openUrl(QUrl(u)))
            table.setCellWidget(row, 4, btn_open)

        comp_layout.addWidget(table)
        layout.addWidget(comp_group)

        # Section 2 : Calculateur de Surebet / Arbitrage
        calc_group = QGroupBox("Calculateur d'Arbitrage (Surebet) & Répartition des Mises")
        calc_layout = QVBoxLayout(calc_group)
        calc_layout.setContentsMargins(8, 12, 8, 8)

        # Barre de saisie de mise totale
        stake_bar = QHBoxLayout()
        lbl_stake = QLabel("Mise Totale (€) :")
        lbl_stake.setStyleSheet("font-weight: bold;")
        self.spin_stake = QDoubleSpinBox()
        self.spin_stake.setRange(1.0, 100000.0)
        self.spin_stake.setValue(self.default_stake)
        self.spin_stake.setPrefix("€ ")
        self.spin_stake.setSingleStep(10.0)
        self.spin_stake.valueChanged.connect(self._recalculate_stakes)
        stake_bar.addWidget(lbl_stake)
        stake_bar.addWidget(self.spin_stake)
        stake_bar.addStretch()

        self.lbl_arbitrage_status = QLabel("")
        stake_bar.addWidget(self.lbl_arbitrage_status)
        calc_layout.addLayout(stake_bar)

        # Tableau des mises calculées
        self.table_stakes = QTableWidget()
        self.table_stakes.setColumnCount(6)
        self.table_stakes.setHorizontalHeaderLabels([
            "Issue", "Bookmaker", "Meilleure Cote", "Mise Recommandée", "Gain Brut Potentiel", "Parier"
        ])
        self.table_stakes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_stakes.verticalHeader().setVisible(False)
        calc_layout.addWidget(self.table_stakes)

        layout.addWidget(calc_group)

        # Bouton fermer
        btn_close = QPushButton("Fermer")
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

        # Calcul initial
        self._recalculate_stakes()

    def _recalculate_stakes(self):
        total_stake = self.spin_stake.value()
        best_mkt = self.event.best_odds.get("1N2") or self.event.best_odds.get("12")
        if not best_mkt:
            self.table_stakes.setRowCount(0)
            self.lbl_arbitrage_status.setText("<span style='color:#8a94a6;'>Pas assez de cotes disponibles.</span>")
            return

        outcomes = ["1", "N", "2"] if "N" in best_mkt else ["1", "2"]
        valid_odds = [best_mkt[k] for k in outcomes if k in best_mkt and best_mkt[k].value > 1.0]

        if len(valid_odds) < len(outcomes):
            self.table_stakes.setRowCount(0)
            self.lbl_arbitrage_status.setText("<span style='color:#8a94a6;'>Cotes incomplètes sur ce marché.</span>")
            return

        inv_sum = sum(1.0 / o.value for o in valid_odds)
        roi_percent = (1.0 / inv_sum - 1.0) * 100.0

        if inv_sum < 1.0:
            net_profit = total_stake * (roi_percent / 100.0)
            self.lbl_arbitrage_status.setText(
                f"<span style='color:#10b981; font-weight:bold; font-size:12px;'>"
                f"🔥 SUREBET GARANTI : Gain net de +{net_profit:.2f}€ (+{roi_percent:.2f}%)</span>"
            )
        else:
            loss_percent = abs(roi_percent)
            self.lbl_arbitrage_status.setText(
                f"<span style='color:#8a94a6;'>"
                f"Marge globale du marché : {inv_sum*100:.1f}% (Pas d'arbitrage garanti actuellement)</span>"
            )

        self.table_stakes.setRowCount(len(valid_odds))
        for row, odd in enumerate(valid_odds):
            # Calcul proportionnel de la mise
            stake = round(total_stake / (inv_sum * odd.value), 2)
            payout = round(stake * odd.value, 2)

            self.table_stakes.setItem(row, 0, QTableWidgetItem(f"{odd.outcome} ({odd.label})"))
            self.table_stakes.setItem(row, 1, QTableWidgetItem(odd.bookmaker))
            self.table_stakes.setItem(row, 2, QTableWidgetItem(f"{odd.value:.2f}"))
            self.table_stakes.setItem(row, 3, QTableWidgetItem(f"{stake:.2f} €"))
            self.table_stakes.setItem(row, 4, QTableWidgetItem(f"{payout:.2f} €"))

            btn_bet = QPushButton(f"Parier ({odd.bookmaker}) ↗")
            btn_bet.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_bet.setStyleSheet("padding: 2px 8px; font-size: 11px; background: #10b981; color: white; border: none; border-radius: 3px;")
            if odd.url:
                url_to_open = odd.url
                btn_bet.clicked.connect(lambda checked, u=url_to_open: QDesktopServices.openUrl(QUrl(u)))
            self.table_stakes.setCellWidget(row, 5, btn_bet)
