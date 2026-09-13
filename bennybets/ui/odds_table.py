from typing import List, Optional
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QAbstractItemView
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QColor, QFont, QCursor

from bennybets.core.models import AggregatedEvent, OpportunityType

class OddsTableWidget(QTableWidget):
    """Tableau compact et interactif affichant la comparaison des cotes en direct (Winamax, Betclic, Unibet)"""

    match_selected = pyqtSignal(AggregatedEvent)

    COL_STATUS = 0
    COL_MATCH = 1
    COL_WINAMAX = 2
    COL_BETCLIC = 3
    COL_UNIBET = 4
    COL_BEST = 5
    COL_OPPORTUNITY = 6
    COL_ACTIONS = 7

    def __init__(self, parent=None):
        super().__init__(parent)
        self.events: List[AggregatedEvent] = []
        self._setup_table()

    def _setup_table(self):
        headers = [
            "Statut",
            "Événement / Compétition",
            "Winamax (1 | N | 2)",
            "Betclic (1 | N | 2)",
            "Unibet (1 | N | 2)",
            "Meilleures Cotes",
            "Opportunité",
            "Action"
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(46)

        header = self.horizontalHeader()
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_MATCH, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_WINAMAX, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_BETCLIC, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_UNIBET, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_BEST, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_OPPORTUNITY, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_ACTIONS, QHeaderView.ResizeMode.ResizeToContents)

        self.cellDoubleClicked.connect(self._on_cell_double_clicked)

    def load_events(self, events: List[AggregatedEvent], filter_text: str = "", only_live: bool = False, only_surebet: bool = False, only_value: bool = False):
        self.events = events
        self.setRowCount(0)

        filter_lower = filter_text.strip().lower()

        filtered = []
        for ev in events:
            if only_live and not ev.is_live:
                continue
            if only_surebet and not ev.has_surebet:
                continue
            if only_value and not ev.has_value_bet:
                continue
            if filter_lower:
                match_name = f"{ev.home_team} {ev.away_team} {ev.competition}".lower()
                if filter_lower not in match_name:
                    continue
            filtered.append(ev)

        self.setRowCount(len(filtered))

        for row, ev in enumerate(filtered):
            self._set_status_cell(row, ev)
            self._set_match_cell(row, ev)
            self._set_bookmaker_cell(row, self.COL_WINAMAX, ev, "Winamax")
            self._set_bookmaker_cell(row, self.COL_BETCLIC, ev, "Betclic")
            self._set_bookmaker_cell(row, self.COL_UNIBET, ev, "Unibet")
            self._set_best_odds_cell(row, ev)
            self._set_opportunity_cell(row, ev)
            self._set_action_cell(row, ev)

    def _set_status_cell(self, row: int, ev: AggregatedEvent):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        if ev.is_live:
            lbl = QLabel("⚡ LIVE")
            lbl.setStyleSheet("color: #ef4444; font-weight: bold; background: rgba(239, 68, 68, 0.15); border-radius: 3px; padding: 2px 4px;")
            layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            if ev.score:
                lbl_score = QLabel(ev.score)
                lbl_score.setStyleSheet("font-weight: bold; color: #f59e0b;")
                layout.addWidget(lbl_score, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            time_str = ev.start_time.strftime("%d/%m %H:%M") if ev.start_time else "À venir"
            lbl = QLabel(time_str)
            lbl.setStyleSheet("color: #8a94a6; font-size: 10px;")
            layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setCellWidget(row, self.COL_STATUS, widget)

    def _set_match_cell(self, row: int, ev: AggregatedEvent):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        lbl_title = QLabel(f"<b>{ev.home_team}</b> <span style='color:#6c757d;'>vs</span> <b>{ev.away_team}</b>")
        lbl_title.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(lbl_title)

        comp_text = ev.competition if ev.competition else f"{len(ev.bookmaker_events)} bookmaker(s)"
        lbl_comp = QLabel(comp_text)
        lbl_comp.setStyleSheet("color: #8a94a6; font-size: 10px;")
        layout.addWidget(lbl_comp)

        self.setCellWidget(row, self.COL_MATCH, widget)

    def _set_bookmaker_cell(self, row: int, col: int, ev: AggregatedEvent, bookmaker_name: str):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        bk_ev = ev.bookmaker_events.get(bookmaker_name)
        if not bk_ev:
            lbl_none = QLabel("—")
            lbl_none.setStyleSheet("color: #4b5563;")
            layout.addWidget(lbl_none, alignment=Qt.AlignmentFlag.AlignCenter)
            self.setCellWidget(row, col, widget)
            return

        mkt = bk_ev.markets.get("1N2") or bk_ev.markets.get("12")
        if not mkt:
            lbl_none = QLabel("—")
            layout.addWidget(lbl_none, alignment=Qt.AlignmentFlag.AlignCenter)
            self.setCellWidget(row, col, widget)
            return

        outcomes = ["1", "N", "2"] if "N" in mkt.outcomes else ["1", "2"]
        for out in outcomes:
            odd_obj = mkt.outcomes.get(out)
            val_str = f"{odd_obj.value:.2f}" if odd_obj else "—"
            btn_odd = QPushButton(f"{out}: {val_str}")
            btn_odd.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_odd.setToolTip(f"Ouvrir {bookmaker_name} pour parier sur {out} à cote {val_str}")
            btn_odd.setStyleSheet("""
                QPushButton {
                    padding: 2px 5px;
                    font-size: 10px;
                    border: 1px solid #374151;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                    color: white;
                    border-color: #3b82f6;
                }
            """)
            if odd_obj and odd_obj.url:
                url_to_open = odd_obj.url
                btn_odd.clicked.connect(lambda checked, u=url_to_open: QDesktopServices.openUrl(QUrl(u)))
            layout.addWidget(btn_odd)

        self.setCellWidget(row, col, widget)

    def _set_best_odds_cell(self, row: int, ev: AggregatedEvent):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        best_mkt = ev.best_odds.get("1N2") or ev.best_odds.get("12")
        if not best_mkt:
            lbl_none = QLabel("—")
            layout.addWidget(lbl_none, alignment=Qt.AlignmentFlag.AlignCenter)
            self.setCellWidget(row, self.COL_BEST, widget)
            return

        outcomes = ["1", "N", "2"] if "N" in best_mkt else ["1", "2"]
        for out in outcomes:
            odd_obj = best_mkt.get(out)
            if odd_obj:
                val_str = f"{odd_obj.value:.2f}"
                btn_best = QPushButton(f"{out}: {val_str}")
                btn_best.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_best.setToolTip(f"Meilleure cote : {odd_obj.value:.2f} chez {odd_obj.bookmaker}")
                btn_best.setStyleSheet("""
                    QPushButton {
                        padding: 2px 5px;
                        font-size: 10px;
                        font-weight: bold;
                        color: #f59e0b;
                        border: 1px solid #d97706;
                        background: rgba(245, 158, 11, 0.1);
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #d97706;
                        color: white;
                    }
                """)
                if odd_obj.url:
                    url_to_open = odd_obj.url
                    btn_best.clicked.connect(lambda checked, u=url_to_open: QDesktopServices.openUrl(QUrl(u)))
                layout.addWidget(btn_best)

        self.setCellWidget(row, self.COL_BEST, widget)

    def _set_opportunity_cell(self, row: int, ev: AggregatedEvent):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        if ev.has_surebet:
            surebets = [op for op in ev.opportunities if op.op_type == OpportunityType.SUREBET]
            max_profit = max(op.profit_margin for op in surebets) if surebets else 0.0
            lbl = QLabel(f"🔥 SUREBET +{max_profit:.1f}%")
            lbl.setStyleSheet("background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; border-radius: 4px; padding: 3px 6px; font-weight: bold; font-size: 10px;")
            lbl.setToolTip(f"Arbitrage garanti avec +{max_profit:.2f}% de ROI !")
            layout.addWidget(lbl)
        elif ev.has_value_bet:
            val_bets = [op for op in ev.opportunities if op.op_type == OpportunityType.VALUE_BET]
            max_spread = max(op.profit_margin for op in val_bets) if val_bets else 0.0
            lbl = QLabel(f"💎 DÉCALAGE +{max_spread:.0f}%")
            lbl.setStyleSheet("background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; border-radius: 4px; padding: 3px 6px; font-weight: bold; font-size: 10px;")
            lbl.setToolTip(f"Cote décalée (+{max_spread:.1f}% par rapport à la médiane)")
            layout.addWidget(lbl)
        else:
            lbl = QLabel("—")
            lbl.setStyleSheet("color: #4b5563;")
            layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setCellWidget(row, self.COL_OPPORTUNITY, widget)

    def _set_action_cell(self, row: int, ev: AggregatedEvent):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        btn_calc = QPushButton("📊 Détails")
        btn_calc.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_calc.setStyleSheet("""
            QPushButton {
                padding: 3px 6px;
                font-size: 10px;
                border: 1px solid #4b5563;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #3b82f6;
                color: white;
                border-color: #3b82f6;
            }
        """)
        btn_calc.clicked.connect(lambda: self.match_selected.emit(ev))
        layout.addWidget(btn_calc)

        self.setCellWidget(row, self.COL_ACTIONS, widget)

    def _on_cell_double_clicked(self, row: int, col: int):
        if 0 <= row < len(self.events):
            self.match_selected.emit(self.events[row])
