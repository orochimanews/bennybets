from typing import List, Optional, Dict
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMenu
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QColor, QFont, QBrush

from bennybets.core.models import AggregatedEvent, OpportunityType

MAX_DISPLAY_ROWS = 250
DEFAULT_BOOKMAKERS = ["Winamax", "Betclic", "Unibet", "Genybet", "PokerStars", "PMU", "Bwin"]

class OddsTableWidget(QTableWidget):
    """
    Tableau haute performance utilisant des QTableWidgetItem natifs.
    Support dynamique de tous les bookmakers configurés (Winamax, Betclic, Unibet, Genybet, PokerStars, etc.).
    Rendu instantané, zéro fuite mémoire, 100% réactif.
    """

    match_selected = pyqtSignal(AggregatedEvent)

    COL_STATUS = 0
    COL_MATCH = 1

    def __init__(self, bookmakers: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self.displayed_events: List[AggregatedEvent] = []
        self.bookmakers: List[str] = list(bookmakers) if bookmakers else list(DEFAULT_BOOKMAKERS)
        self._setup_table()

    @property
    def col_best(self) -> int:
        return 2 + len(self.bookmakers)

    @property
    def col_opportunity(self) -> int:
        return 3 + len(self.bookmakers)

    @property
    def col_actions(self) -> int:
        return 4 + len(self.bookmakers)

    def set_bookmakers(self, bookmakers: List[str]):
        if self.bookmakers != bookmakers:
            self.bookmakers = list(bookmakers)
            self._setup_table()

    def _setup_table(self):
        headers = ["Statut", "Événement (Compétition)"]
        for bk in self.bookmakers:
            headers.append(f"{bk} (1 | N | 2)")
        headers.extend(["Meilleures Cotes", "Opportunité", "Action"])

        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setShowGrid(True)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(36)

        header = self.horizontalHeader()
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_MATCH, QHeaderView.ResizeMode.Stretch)
        for i in range(len(self.bookmakers)):
            header.setSectionResizeMode(2 + i, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.col_best, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.col_opportunity, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.col_actions, QHeaderView.ResizeMode.ResizeToContents)

        try:
            self.cellClicked.disconnect()
        except TypeError:
            pass
        try:
            self.cellDoubleClicked.disconnect()
        except TypeError:
            pass
        try:
            self.customContextMenuRequested.disconnect()
        except TypeError:
            pass

        self.cellClicked.connect(self._on_cell_clicked)
        self.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def load_events(
        self,
        events: List[AggregatedEvent],
        filter_text: str = "",
        only_live: bool = False,
        only_surebet: bool = False,
        only_value: bool = False,
        bookmakers: Optional[List[str]] = None
    ):
        if bookmakers is not None and bookmakers != self.bookmakers:
            self.set_bookmakers(bookmakers)

        filter_lower = filter_text.strip().lower()

        filtered: List[AggregatedEvent] = []
        for ev in events:
            if only_live and not ev.is_live:
                continue
            if only_surebet and not ev.has_surebet:
                continue
            if only_value and not ev.has_value_bet:
                continue
            if filter_lower:
                match_str = f"{ev.home_team} {ev.away_team} {ev.competition}".lower()
                if filter_lower not in match_str:
                    continue
            filtered.append(ev)

        # Plafond intelligent pour garantir 60 FPS constants
        self.displayed_events = filtered[:MAX_DISPLAY_ROWS]

        # Désactiver les updates graphiques pendant le remplissage pour vitesse maximale
        self.setUpdatesEnabled(False)
        self.setRowCount(len(self.displayed_events))

        font_bold = QFont()
        font_bold.setBold(True)

        for row, ev in enumerate(self.displayed_events):
            # 0. Statut
            if ev.is_live:
                score_part = f" ({ev.score})" if ev.score else ""
                item_status = QTableWidgetItem(f"⚡ LIVE{score_part}")
                item_status.setForeground(QColor("#ef4444"))
                item_status.setFont(font_bold)
            else:
                time_str = ev.start_time.strftime("%d/%m %H:%M") if ev.start_time else "À venir"
                item_status = QTableWidgetItem(time_str)
                item_status.setForeground(QColor("#8a94a6"))
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_status.setFlags(item_status.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, self.COL_STATUS, item_status)

            # 1. Match & Compétition
            comp_txt = f"  [{ev.competition}]" if ev.competition else ""
            item_match = QTableWidgetItem(f"{ev.home_team} vs {ev.away_team}{comp_txt}")
            item_match.setToolTip(f"{ev.title}\nCompétition : {ev.competition}\nDouble-cliquez pour ouvrir les détails")
            item_match.setFlags(item_match.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, self.COL_MATCH, item_match)

            # 2..2+N-1 Colonnes Bookmakers
            for i, bk in enumerate(self.bookmakers):
                self._set_bookmaker_item(row, 2 + i, ev, bk)

            # Meilleures Cotes
            self._set_best_odds_item(row, self.col_best, ev)

            # Opportunités
            self._set_opportunity_item(row, self.col_opportunity, ev)

            # Action
            item_action = QTableWidgetItem("📊 Détails ↗")
            item_action.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_action.setForeground(QColor("#3b82f6"))
            item_action.setFont(font_bold)
            item_action.setToolTip("Cliquez pour ouvrir le comparatif complet et le calculateur de mise")
            item_action.setFlags(item_action.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, self.col_actions, item_action)

        self.setUpdatesEnabled(True)

    def _set_bookmaker_item(self, row: int, col: int, ev: AggregatedEvent, bk_name: str):
        bk_ev = ev.bookmaker_events.get(bk_name)
        if not bk_ev:
            item = QTableWidgetItem("—")
            item.setForeground(QColor("#4b5563"))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, col, item)
            return

        mkt = bk_ev.markets.get("1N2") or bk_ev.markets.get("12")
        if not mkt:
            item = QTableWidgetItem("—")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, col, item)
            return

        o1 = mkt.outcomes.get("1")
        on = mkt.outcomes.get("N")
        o2 = mkt.outcomes.get("2")

        parts = []
        parts.append(f"1: {o1.value:.2f}" if o1 else "1: -")
        if on:
            parts.append(f"N: {on.value:.2f}")
        parts.append(f"2: {o2.value:.2f}" if o2 else "2: -")

        text = " | ".join(parts)
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setToolTip(f"Cotes {bk_name} : {text}\nCliquez pour ouvrir sur le site de {bk_name}")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, col, item)

    def _set_best_odds_item(self, row: int, col: int, ev: AggregatedEvent):
        best_mkt = ev.best_odds.get("1N2") or ev.best_odds.get("12")
        if not best_mkt:
            item = QTableWidgetItem("—")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, col, item)
            return

        o1 = best_mkt.get("1")
        on = best_mkt.get("N")
        o2 = best_mkt.get("2")

        parts = []
        if o1: parts.append(f"1: {o1.value:.2f} ({o1.bookmaker[:3]})")
        if on: parts.append(f"N: {on.value:.2f} ({on.bookmaker[:3]})")
        if o2: parts.append(f"2: {o2.value:.2f} ({o2.bookmaker[:3]})")

        text = " | ".join(parts)
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setForeground(QColor("#f59e0b"))
        font_bold = QFont()
        font_bold.setBold(True)
        item.setFont(font_bold)
        item.setToolTip(f"Meilleures cotes combinées : {text}")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, col, item)

    def _set_opportunity_item(self, row: int, col: int, ev: AggregatedEvent):
        if ev.has_surebet:
            surebets = [op for op in ev.opportunities if op.op_type == OpportunityType.SUREBET]
            max_profit = max(op.profit_margin for op in surebets) if surebets else 0.0
            item = QTableWidgetItem(f"🔥 SUREBET +{max_profit:.1f}%")
            item.setForeground(QColor("#10b981"))
            item.setBackground(QBrush(QColor(16, 185, 129, 45)))
            font_bold = QFont()
            font_bold.setBold(True)
            item.setFont(font_bold)
            item.setToolTip(f"Arbitrage mathématique garanti ! Bénéfice net : +{max_profit:.2f}%")
        elif ev.has_value_bet:
            val_bets = [op for op in ev.opportunities if op.op_type == OpportunityType.VALUE_BET]
            max_spread = max(op.profit_margin for op in val_bets) if val_bets else 0.0
            item = QTableWidgetItem(f"💎 DÉCALAGE +{max_spread:.0f}%")
            item.setForeground(QColor("#f59e0b"))
            item.setBackground(QBrush(QColor(245, 158, 11, 40)))
            font_bold = QFont()
            font_bold.setBold(True)
            item.setFont(font_bold)
            item.setToolTip(f"Gros décalage de cote détecté (+{max_spread:.1f}% au-dessus de la médiane)")
        else:
            item = QTableWidgetItem("—")
            item.setForeground(QColor("#4b5563"))

        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, col, item)

    def _on_cell_clicked(self, row: int, col: int):
        if not (0 <= row < len(self.displayed_events)):
            return

        ev = self.displayed_events[row]

        # Clic sur une colonne de bookmaker -> ouvrir directement le lien du match !
        if 2 <= col < 2 + len(self.bookmakers):
            bk_name = self.bookmakers[col - 2]
            bk_ev = ev.bookmaker_events.get(bk_name)
            if bk_ev and bk_ev.url:
                QDesktopServices.openUrl(QUrl(bk_ev.url))
            elif bk_ev:
                default_urls = {
                    "Winamax": "https://www.winamax.fr/paris-sportifs",
                    "Betclic": "https://www.betclic.fr",
                    "Unibet": "https://www.unibet.fr",
                    "Genybet": "https://sport.genybet.fr/football",
                    "PokerStars": "https://www.pokerstarssports.fr/sports/football",
                    "PMU": "https://paris-sportifs.pmu.fr",
                    "Bwin": "https://sports.bwin.fr",
                }
                QDesktopServices.openUrl(QUrl(default_urls.get(bk_name, "")))
        elif col == self.col_best:
            # Clic sur "Meilleures Cotes" -> ouvrir directement le match sur le bookmaker de la meilleure cote
            best_mkt = ev.best_odds.get("1N2") or ev.best_odds.get("12")
            if best_mkt:
                best_odd = max(best_mkt.values(), key=lambda o: o.value, default=None)
                if best_odd and best_odd.url:
                    QDesktopServices.openUrl(QUrl(best_odd.url))
                    return
                elif best_odd:
                    bk_ev = ev.bookmaker_events.get(best_odd.bookmaker)
                    if bk_ev and bk_ev.url:
                        QDesktopServices.openUrl(QUrl(bk_ev.url))
                        return
            self.match_selected.emit(ev)
        elif col in (self.col_actions, self.COL_MATCH):
            self.match_selected.emit(ev)

    def _on_cell_double_clicked(self, row: int, col: int):
        if 0 <= row < len(self.displayed_events):
            self.match_selected.emit(self.displayed_events[row])

    def _show_context_menu(self, pos):
        """Menu contextuel au clic droit pour accéder directement aux pages de chaque bookmaker"""
        item = self.itemAt(pos)
        if not item:
            return
        row = item.row()
        if not (0 <= row < len(self.displayed_events)):
            return
        ev = self.displayed_events[row]

        menu = QMenu(self)
        
        # Options directes pour ouvrir chaque bookmaker présent pour ce match
        has_bk_link = False
        for bk_name, bk_ev in ev.bookmaker_events.items():
            if bk_ev and bk_ev.url:
                action = menu.addAction(f"Ouvrir sur {bk_name} (Page du match) ↗")
                action.triggered.connect(lambda checked, u=bk_ev.url: QDesktopServices.openUrl(QUrl(u)))
                has_bk_link = True

        if has_bk_link:
            menu.addSeparator()

        action_details = menu.addAction("📊 Voir comparatif complet & calculateur de mise")
        action_details.triggered.connect(lambda: self.match_selected.emit(ev))

        menu.exec(self.viewport().mapToGlobal(pos))
