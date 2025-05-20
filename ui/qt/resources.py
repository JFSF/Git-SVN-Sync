#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Recursos da aplicação: ícones, estilos e temas
"""

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor
from PyQt6.QtWidgets import QApplication

# Definições de ícones - usar FontAwesome ou outro pacote de ícones
# Esta é uma versão minimalista com nomes e caminhos simulados

ICONS = {
    "refresh": ":/icons/refresh.png",
    "commit": ":/icons/commit.png",
    "sync": ":/icons/sync.png",
    "diff": ":/icons/diff.png",
    "settings": ":/icons/settings.png",
    "branch": ":/icons/branch.png",
    "git": ":/icons/git.png",
    "svn": ":/icons/svn.png",
    "add": ":/icons/add.png",
    "delete": ":/icons/delete.png",
    "edit": ":/icons/edit.png",
    "task": ":/icons/task.png",
    "search": ":/icons/search.png",
    "save": ":/icons/save.png",
    "close": ":/icons/close.png"
}

def get_icon(name, size=24):
    """
    Retorna um ícone pelo nome
    
    Como os ícones reais não estão disponíveis nessa implementação,
    esta função retorna um QIcon vazio.
    Em uma implementação real, os ícones seriam carregados de arquivos
    ou de um resource file compilado com Qt Resource Compiler (rcc).
    """
    # Em uma implementação real, seria algo como:
    # return QIcon(ICONS.get(name, ""))
    
    # Para esta demonstração, retornar um ícone vazio
    return QIcon()

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
    # Estilo básico para melhorar a aparência
    stylesheet = """
    QMainWindow, QDialog {
        background-color: palette(window);
    }
    
    QGroupBox {
        border: 1px solid palette(shadow);
        border-radius: 5px;
        margin-top: 1ex;
        font-weight: bold;
        padding: 10px;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 3px;
        background-color: palette(window);
    }
    
    QPushButton {
        padding: 6px 12px;
        border-radius: 3px;
        border: 1px solid palette(shadow);
    }
    
    QPushButton:hover {
        background-color: palette(highlight);
        color: palette(highlighted-text);
    }
    
    QTreeWidget, QListWidget, QTextEdit, QLineEdit {
        border: 1px solid palette(shadow);
        border-radius: 3px;
    }
    
    QTabWidget::pane {
        border: 1px solid palette(shadow);
        border-radius: 3px;
        padding: 5px;
    }
    
    QTabBar::tab {
        padding: 5px 15px;
    }
    
    QTabBar::tab:selected {
        font-weight: bold;
        border-bottom: 2px solid palette(highlight);
    }
    
    QLabel[styleClass="title"] {
        font-weight: bold;
        font-size: 14px;
    }
    
    QLabel[styleClass="link"] {
        color: palette(link);
        text-decoration: underline;
    }
    
    QSplitter::handle {
        background-color: palette(mid);
    }
    
    QStatusBar {
        border-top: 1px solid palette(shadow);
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