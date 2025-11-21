#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Recursos da aplicação: ícones, estilos e temas
"""

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QPixmap, QPainter
from PyQt6.QtWidgets import QApplication

# Ícones usando caracteres Unicode (Emoji e símbolos especiais)
# Compatível com todos os sistemas sem precisar de arquivos externos
ICON_CHARS = {
    "refresh": "🔄",
    "commit": "💾",
    "sync": "🔃",
    "diff": "📊",
    "settings": "⚙️",
    "branch": "🌿",
    "git": "📦",
    "svn": "📁",
    "add": "➕",
    "delete": "🗑️",
    "edit": "✏️",
    "task": "📋",
    "search": "🔍",
    "save": "💾",
    "close": "❌",
    "success": "✅",
    "warning": "⚠️",
    "error": "❌",
    "info": "ℹ️"
}


def create_text_icon(text, size=24, color=None):
    """
    Cria um QIcon a partir de texto (emoji ou caractere)

    Args:
        text: Texto/emoji a ser renderizado
        size: Tamanho do ícone
        color: Cor do texto (opcional)

    Returns:
        QIcon com o texto renderizado
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    font = QFont()
    font.setPixelSize(int(size * 0.8))
    painter.setFont(font)

    if color:
        painter.setPen(color)

    # Desenhar texto centrado
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
    painter.end()

    return QIcon(pixmap)


def get_icon(name, size=24):
    """
    Retorna um ícone pelo nome usando caracteres Unicode

    Args:
        name: Nome do ícone (veja ICON_CHARS)
        size: Tamanho do ícone em pixels

    Returns:
        QIcon com o caractere renderizado
    """
    char = ICON_CHARS.get(name, "•")
    return create_text_icon(char, size)

def apply_theme(app, theme_name="system"):
    """
    Aplica um tema visual à aplicação
    
    Args:
        app: QApplication onde o tema será aplicado
        theme_name: Nome do tema ("system", "light", "dark")
    """
    if theme_name == "system":
        # Usar o tema do sistema
        app.setStyle("Fusion")
        return
        
    elif theme_name == "light":
        # Tema claro personalizado
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        
    elif theme_name == "dark":
        # Tema escuro personalizado
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        
        # Cores para widgets desabilitados
        palette.setColor(QPalette.ColorRole.Disabled, QPalette.ColorRole.Text, QColor(150, 150, 150))
        palette.setColor(QPalette.ColorRole.Disabled, QPalette.ColorRole.ButtonText, QColor(150, 150, 150))
        
    else:
        # Tema padrão
        app.setStyle("Fusion")
        return
    
    # Aplicar a paleta definida
    app.setPalette(palette)
    app.setStyle("Fusion")

def apply_stylesheet(app):
    """
    Aplica uma folha de estilo (CSS) à aplicação
    
    Args:
        app: QApplication onde o estilo será aplicado
    """
    # Estilo moderno e aprimorado
    stylesheet = """
    QMainWindow, QDialog {
        background-color: palette(window);
    }

    QGroupBox {
        border: 2px solid #3498db;
        border-radius: 8px;
        margin-top: 1.5ex;
        font-weight: bold;
        padding: 15px;
        background-color: palette(base);
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        background-color: palette(window);
        color: #3498db;
    }

    QPushButton {
        padding: 8px 16px;
        border-radius: 5px;
        border: 1px solid #95a5a6;
        background-color: #ecf0f1;
        font-weight: 500;
    }

    QPushButton:hover {
        background-color: #3498db;
        color: white;
        border: 1px solid #2980b9;
    }

    QPushButton:pressed {
        background-color: #2980b9;
    }

    QPushButton:default {
        background-color: #3498db;
        color: white;
        border: 2px solid #2980b9;
    }

    QTreeWidget, QListWidget, QTextEdit, QLineEdit, QSpinBox {
        border: 2px solid #bdc3c7;
        border-radius: 5px;
        padding: 4px;
        background-color: palette(base);
    }

    QTreeWidget:focus, QListWidget:focus, QTextEdit:focus, QLineEdit:focus {
        border: 2px solid #3498db;
    }

    QTreeWidget::item:selected {
        background-color: #3498db;
        color: white;
    }

    QTreeWidget::item:hover {
        background-color: #ecf0f1;
    }

    QTabWidget::pane {
        border: 2px solid #bdc3c7;
        border-radius: 5px;
        padding: 8px;
        background-color: palette(window);
    }

    QTabBar::tab {
        padding: 8px 20px;
        margin-right: 2px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        background-color: #ecf0f1;
    }

    QTabBar::tab:selected {
        font-weight: bold;
        background-color: #3498db;
        color: white;
    }

    QTabBar::tab:hover:!selected {
        background-color: #bdc3c7;
    }

    QSplitter::handle {
        background-color: #95a5a6;
        width: 2px;
        height: 2px;
    }

    QSplitter::handle:hover {
        background-color: #3498db;
    }

    QStatusBar {
        border-top: 2px solid #bdc3c7;
        background-color: #ecf0f1;
        padding: 4px;
    }

    QMenuBar {
        background-color: palette(window);
        border-bottom: 1px solid #bdc3c7;
    }

    QMenuBar::item:selected {
        background-color: #3498db;
        color: white;
    }

    QMenu {
        border: 1px solid #bdc3c7;
        border-radius: 5px;
    }

    QMenu::item:selected {
        background-color: #3498db;
        color: white;
    }

    QCheckBox, QRadioButton {
        spacing: 8px;
    }

    QCheckBox::indicator, QRadioButton::indicator {
        width: 18px;
        height: 18px;
    }

    QCheckBox::indicator:checked, QRadioButton::indicator:checked {
        background-color: #3498db;
        border: 2px solid #2980b9;
    }
    """
    
    app.setStyleSheet(stylesheet)

def setup_application_style(app, theme="system"):
    """
    Configura o estilo visual completo da aplicação
    
    Args:
        app: QApplication a ser configurada
        theme: Nome do tema ("system", "light", "dark")
    """
    # Aplicar tema (paleta de cores)
    apply_theme(app, theme)
    
    # Aplicar folha de estilo
    apply_stylesheet(app)
    
    # Configurar fonte padrão
    font = QFont("Segoe UI", 9)  # Windows
    if app.platformName() == "cocoa":  # macOS
        font = QFont("SF Pro Text", 13)
    elif app.platformName() == "xcb":  # Linux
        font = QFont("Noto Sans", 10)
    
    app.setFont(font)