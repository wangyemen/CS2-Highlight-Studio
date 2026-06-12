"""
暗色游戏主题 - Cyber Midnight
所有 QSS 样式的集中管理
"""

# ═══════════════════════════════════════════
#  色彩系统
# ═══════════════════════════════════════════

COLORS = {
    # 背景层级
    "bg_base":      "#060a10",
    "bg_primary":   "#0b1120",
    "bg_surface":   "#111a2e",
    "bg_elevated":  "#162038",
    "bg_hover":     "#1c2a4a",
    "bg_active":    "#223352",

    # 边框
    "border":       "#1a2744",
    "border_light": "#243456",

    # 主色调
    "accent":       "#00b4ff",
    "accent_dim":   "rgba(0, 180, 255, 0.15)",
    "accent_glow":  "rgba(0, 180, 255, 0.3)",

    # 功能色
    "green":        "#00e68a",
    "green_dim":    "rgba(0, 230, 138, 0.15)",
    "red":          "#ff3b5c",
    "red_dim":      "rgba(255, 59, 92, 0.15)",
    "orange":       "#ff9f43",
    "orange_dim":   "rgba(255, 159, 67, 0.15)",
    "purple":       "#8b5cf6",
    "purple_dim":   "rgba(139, 92, 246, 0.15)",

    # 文字
    "text":         "#e8edf5",
    "text_sec":     "#8b99b0",
    "text_muted":   "#4a5c78",
}


def get_stylesheet() -> str:
    """生成完整的 QSS 样式表"""
    C = COLORS

    return f"""
    /* ═══════════════════════════════════════════
       全局基础
       ═══════════════════════════════════════════ */
    * {{
        font-family: "Outfit", "Microsoft YaHei", sans-serif;
        font-size: 13px;
        color: {C['text']};
    }}

    QMainWindow, QWidget#centralWidget {{
        background-color: {C['bg_base']};
    }}

    /* ═══════════════════════════════════════════
       滚动条
       ═══════════════════════════════════════════ */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {C['border']};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {C['border_light']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
    }}
    QScrollBar::handle:horizontal {{
        background: {C['border']};
        border-radius: 4px;
        min-width: 30px;
    }}

    /* ═══════════════════════════════════════════
       按钮
       ═══════════════════════════════════════════ */
    QPushButton {{
        background-color: {C['bg_elevated']};
        border: 1px solid {C['border']};
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {C['bg_hover']};
        border-color: {C['border_light']};
    }}
    QPushButton:pressed {{
        background-color: {C['bg_active']};
    }}
    QPushButton:disabled {{
        color: {C['text_muted']};
        background-color: {C['bg_surface']};
    }}

    QPushButton#accentBtn {{
        background-color: {C['accent']};
        color: {C['bg_base']};
        border: none;
        font-weight: 600;
        font-size: 14px;
        padding: 10px 28px;
        border-radius: 8px;
    }}
    QPushButton#accentBtn:hover {{
        background-color: #33c3ff;
    }}
    QPushButton#accentBtn:pressed {{
        background-color: #0090cc;
    }}

    QPushButton#dangerBtn {{
        background-color: {C['red_dim']};
        color: {C['red']};
        border: 1px solid rgba(255, 59, 92, 0.3);
    }}
    QPushButton#dangerBtn:hover {{
        background-color: rgba(255, 59, 92, 0.25);
    }}

    QPushButton#successBtn {{
        background-color: {C['green_dim']};
        color: {C['green']};
        border: 1px solid rgba(0, 230, 138, 0.3);
    }}
    QPushButton#successBtn:hover {{
        background-color: rgba(0, 230, 138, 0.25);
    }}

    /* ═══════════════════════════════════════════
       输入框
       ═══════════════════════════════════════════ */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {C['bg_primary']};
        border: 1px solid {C['border']};
        border-radius: 6px;
        padding: 8px 12px;
        color: {C['text']};
        font-size: 13px;
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:on {{
        border-color: {C['accent']};
    }}
    QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
        border-color: {C['border_light']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {C['bg_elevated']};
        border: 1px solid {C['border']};
        selection-background-color: {C['bg_active']};
        selection-color: {C['accent']};
        border-radius: 6px;
    }}

    /* ═══════════════════════════════════════════
       标签
       ═══════════════════════════════════════════ */
    QLabel {{
        color: {C['text']};
        background: transparent;
    }}
    QLabel#heading {{
        font-family: "Exo 2", "Microsoft YaHei", sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: {C['text']};
    }}
    QLabel#subheading {{
        font-size: 14px;
        color: {C['text_sec']};
    }}
    QLabel#muted {{
        color: {C['text_muted']};
        font-size: 12px;
    }}
    QLabel#accentLabel {{
        color: {C['accent']};
        font-weight: 600;
    }}

    /* ═══════════════════════════════════════════
       列表和表格
       ═══════════════════════════════════════════ */
    QListWidget, QTreeWidget, QTableWidget {{
        background-color: {C['bg_primary']};
        border: 1px solid {C['border']};
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }}
    QListWidget::item, QTreeWidget::item, QTableWidget::item {{
        padding: 10px 12px;
        border-radius: 6px;
    }}
    QListWidget::item:hover, QTreeWidget::item:hover {{
        background-color: {C['bg_hover']};
    }}
    QListWidget::item:selected, QTreeWidget::item:selected {{
        background-color: {C['accent_dim']};
        color: {C['accent']};
    }}

    QHeaderView::section {{
        background-color: {C['bg_surface']};
        color: {C['text_sec']};
        border: none;
        border-bottom: 1px solid {C['border']};
        padding: 8px 12px;
        font-weight: 600;
        font-size: 12px;
    }}

    /* ═══════════════════════════════════════════
       分组框
       ═══════════════════════════════════════════ */
    QGroupBox {{
        background-color: {C['bg_surface']};
        border: 1px solid {C['border']};
        border-radius: 10px;
        margin-top: 12px;
        padding: 16px;
        padding-top: 20px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 16px;
        padding: 0 8px;
        color: {C['text_sec']};
    }}

    /* ═══════════════════════════════════════════
       进度条
       ═══════════════════════════════════════════ */
    QProgressBar {{
        background-color: {C['bg_primary']};
        border: none;
        border-radius: 6px;
        height: 10px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {C['accent']},
            stop:1 {C['purple']}
        );
        border-radius: 6px;
    }}

    /* ═══════════════════════════════════════════
       工具提示
       ═══════════════════════════════════════════ */
    QToolTip {{
        background-color: {C['bg_elevated']};
        color: {C['text']};
        border: 1px solid {C['border']};
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 12px;
    }}

    /* ═══════════════════════════════════════════
       Tab Widget
       ═══════════════════════════════════════════ */
    QTabWidget::pane {{
        border: 1px solid {C['border']};
        border-radius: 8px;
        background: {C['bg_primary']};
    }}
    QTabBar::tab {{
        background: {C['bg_surface']};
        color: {C['text_sec']};
        border: 1px solid {C['border']};
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 8px 20px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: {C['bg_primary']};
        color: {C['accent']};
    }}
    QTabBar::tab:hover {{
        background: {C['bg_elevated']};
    }}

    /* ═══════════════════════════════════════════
       拖放区域
       ═══════════════════════════════════════════ */
    QWidget#dropZone {{
        border: 2px dashed {C['border']};
        border-radius: 12px;
        background-color: {C['bg_surface']};
    }}
    QWidget#dropZone:hover {{
        border-color: {C['accent']};
        background-color: {C['accent_dim']};
    }}

    /* ═══════════════════════════════════════════
       文本编辑框
       ═══════════════════════════════════════════ */
    QTextEdit, QPlainTextEdit {{
        background-color: {C['bg_primary']};
        border: 1px solid {C['border']};
        border-radius: 8px;
        padding: 8px;
        color: {C['text']};
        font-family: "JetBrains Mono", "Consolas", monospace;
        font-size: 12px;
    }}
    """
