#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import signal
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtGui import QPixmap, QFont, QPainter, QLinearGradient, QColor, QPen
from PyQt6.QtCore import Qt, QTimer, QRect

from utils.dependency_checker import check_dependencies
from utils.config_manager import ConfigManager
from ui.qt.main_window import MainWindow
from ui.qt.resources import setup_application_style


def create_splash_screen():
    """Cria um splash screen moderno e atraente"""
    width, height = 500, 350
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Criar gradiente de fundo
    gradient = QLinearGradient(0, 0, 0, height)
    gradient.setColorAt(0.0, QColor("#2c3e50"))  # Azul escuro
    gradient.setColorAt(1.0, QColor("#34495e"))  # Azul acinzentado
    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, width, height, 10, 10)

    # Desenhar borda sutil
    painter.setPen(QPen(QColor("#3498db"), 2))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(1, 1, width-2, height-2, 10, 10)

    # Desenhar ícones Git e SVN (emojis grandes)
    icon_font = QFont("Segoe UI Emoji", 48)
    painter.setFont(icon_font)
    painter.setPen(QColor("#ecf0f1"))

    # Git icon
    painter.drawText(QRect(80, 60, 100, 100), Qt.AlignmentFlag.AlignCenter, "📦")

    # Sync arrows
    painter.drawText(QRect(210, 60, 80, 100), Qt.AlignmentFlag.AlignCenter, "🔃")

    # SVN icon
    painter.drawText(QRect(320, 60, 100, 100), Qt.AlignmentFlag.AlignCenter, "📁")

    # Título
    title_font = QFont("Segoe UI", 28, QFont.Weight.Bold)
    painter.setFont(title_font)
    painter.setPen(QColor("#ecf0f1"))
    painter.drawText(QRect(0, 180, width, 40), Qt.AlignmentFlag.AlignCenter, "Git-SVN Sync")

    # Subtítulo
    subtitle_font = QFont("Segoe UI", 12)
    painter.setFont(subtitle_font)
    painter.setPen(QColor("#bdc3c7"))
    painter.drawText(QRect(0, 220, width, 30), Qt.AlignmentFlag.AlignCenter,
                    "Seamless Repository Synchronization")

    # Versão
    version_font = QFont("Segoe UI", 9)
    painter.setFont(version_font)
    painter.setPen(QColor("#95a5a6"))
    painter.drawText(QRect(0, 280, width, 20), Qt.AlignmentFlag.AlignCenter, "Version 1.0.0")

    painter.end()
    return pixmap


def main():
    """Função principal da aplicação"""
    # Configurar signal handler para saída limpa
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Inicializar aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Git-SVN Sync Tool")
    app.setApplicationVersion("1.0.0")
    
    # Exibir splash screen moderno
    splash_pixmap = create_splash_screen()
    splash = QSplashScreen(splash_pixmap)
    splash.setWindowFlag(Qt.WindowType.FramelessWindowHint)
    splash.show()
    splash.showMessage("Loading application...",
                     Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                     Qt.GlobalColor.white)
    app.processEvents()
    
    # Carregar configurações
    try:
        config = ConfigManager()
        
        # Aplicar tema e estilo conforme configurações
        theme = config.get("ui.theme", "system")
        setup_application_style(app, theme)
        
    except Exception as e:
        splash.close()
        QMessageBox.critical(None, "Error", f"Failed to load configuration: {str(e)}")
        return 1
    
    # Verificar dependências
    dependencies_met, missing = check_dependencies()
    
    # Pausar brevemente para exibir a splash screen
    QTimer.singleShot(1000, lambda: initialize_main_window(app, splash, config, dependencies_met, missing))
    
    # Configurar saída limpa
    app.aboutToQuit.connect(lambda: prepare_exit(app))
    
    # Iniciar loop de eventos
    return app.exec()


def initialize_main_window(app, splash, config, dependencies_met, missing):
    """Inicializa a janela principal após exibir a splash screen"""
    try:
        # Criar e mostrar janela principal
        window = MainWindow(config)
        
        # Ocultar splash screen e mostrar a janela principal
        splash.finish(window)
        window.show()
        
        # Mostrar aviso de dependências faltantes
        if not dependencies_met:
            window.show_dependency_warning(missing)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        QMessageBox.critical(None, "Error", f"An unexpected error occurred: {str(e)}")
        sys.exit(1)


def prepare_exit(app):
    """Prepara uma saída limpa da aplicação"""
    # Processar eventos pendentes
    app.processEvents()


if __name__ == "__main__":
    sys.exit(main())