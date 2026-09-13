def get_stylesheet(theme: str = "dark", font_size: int = 11) -> str:
    """Génère la feuille de style QSS compacte et moderne selon le thème et la taille de police"""
    fs = font_size
    fs_small = max(8, fs - 2)
    fs_header = fs + 2
    
    if theme == "light":
        bg_main = "#f8f9fa"
        bg_card = "#ffffff"
        bg_alt = "#f1f3f5"
        border_color = "#dee2e6"
        text_primary = "#212529"
        text_muted = "#6c757d"
        accent_blue = "#0d6efd"
        accent_hover = "#0b5ed7"
        accent_green = "#198754"
        accent_gold = "#b58105"
        table_header = "#e9ecef"
        table_select = "#e7f1ff"
    elif theme == "midnight":
        bg_main = "#0b132b"
        bg_card = "#1c2541"
        bg_alt = "#131d36"
        border_color = "#3a506b"
        text_primary = "#ffffff"
        text_muted = "#8d99ae"
        accent_blue = "#48cae4"
        accent_hover = "#00b4d8"
        accent_green = "#06d6a0"
        accent_gold = "#ffd166"
        table_header = "#1e2a4a"
        table_select = "#25345d"
    else: # default: dark moderne
        bg_main = "#121418"
        bg_card = "#1a1d24"
        bg_alt = "#20242d"
        border_color = "#2b303c"
        text_primary = "#f0f2f5"
        text_muted = "#8a94a6"
        accent_blue = "#3b82f6"
        accent_hover = "#2563eb"
        accent_green = "#10b981"
        accent_gold = "#f59e0b"
        table_header = "#242933"
        table_select = "#2d3545"

    return f"""
    * {{
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
        font-size: {fs}px;
        color: {text_primary};
    }}

    QMainWindow, QDialog {{
        background-color: {bg_main};
    }}

    /* Sticky Menu Toolbar */
    #TopBar {{
        background-color: {bg_card};
        border-bottom: 2px solid {border_color};
        padding: 4px 8px;
    }}

    #LogoLabel {{
        font-size: {fs_header}px;
        font-weight: bold;
        color: {accent_green};
        padding-right: 12px;
    }}

    /* Boutons */
    QPushButton {{
        background-color: {bg_alt};
        border: 1px solid {border_color};
        border-radius: 4px;
        padding: 5px 12px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {border_color};
        border-color: {accent_blue};
    }}
    QPushButton:pressed {{
        background-color: {accent_blue};
        color: #ffffff;
    }}

    /* Boutons actifs / filtres */
    QPushButton#FilterActive {{
        background-color: {accent_blue};
        color: #ffffff;
        border-color: {accent_blue};
    }}

    QPushButton#BtnRefresh {{
        background-color: {accent_green};
        color: #ffffff;
        border: none;
        font-weight: bold;
    }}
    QPushButton#BtnRefresh:hover {{
        background-color: #059669;
    }}

    QPushButton#BtnSettings {{
        padding: 5px 8px;
        font-size: {fs_header}px;
    }}

    /* Champs de texte et Combos */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {bg_alt};
        border: 1px solid {border_color};
        border-radius: 4px;
        padding: 4px 8px;
        color: {text_primary};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border-color: {accent_blue};
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 4px;
    }}

    /* Tableau des cotes */
    QTableWidget {{
        background-color: {bg_card};
        alternate-background-color: {bg_alt};
        border: 1px solid {border_color};
        border-radius: 6px;
        gridline-color: {border_color};
        selection-background-color: {table_select};
        selection-color: {text_primary};
    }}

    QHeaderView::section {{
        background-color: {table_header};
        color: {text_muted};
        padding: 6px 8px;
        border: none;
        border-right: 1px solid {border_color};
        border-bottom: 1px solid {border_color};
        font-weight: 600;
        font-size: {fs_small}px;
        text-transform: uppercase;
    }}

    /* Badges et cotes */
    .badge-surebet {{
        background-color: rgba(16, 185, 129, 0.2);
        color: {accent_green};
        border: 1px solid {accent_green};
        border-radius: 3px;
        padding: 2px 6px;
        font-weight: bold;
    }}

    .badge-value {{
        background-color: rgba(245, 158, 11, 0.2);
        color: {accent_gold};
        border: 1px solid {accent_gold};
        border-radius: 3px;
        padding: 2px 6px;
        font-weight: bold;
    }}

    .badge-live {{
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid #ef4444;
        border-radius: 3px;
        padding: 2px 6px;
        font-weight: bold;
    }}

    /* Scrollbars compactes */
    QScrollBar:vertical {{
        background: {bg_main};
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {border_color};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {text_muted};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* Status Bar */
    QStatusBar {{
        background-color: {bg_card};
        border-top: 1px solid {border_color};
        color: {text_muted};
        font-size: {fs_small}px;
        padding: 2px 8px;
    }}
    """
