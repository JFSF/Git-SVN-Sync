#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import signal
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QTimer

from utils.dependency_checker import check_dependencies
from utils.config_manager import ConfigManager
from ui.qt.main_window import MainWindow
from ui.qt.resources import setup_application_style


def main():
    """Função principal da aplicação"""
    # Configurar signal handler para saída limpa
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Inicializar aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Git-SVN Sync Tool")
    app.setApplicationVersion("1.0.0")
    
    # Exibir splash screen
    splash_pixmap = QPixmap(400, 300)
    splash_pixmap.fill(Qt.GlobalColor.white)
    splash = QSplashScreen(splash_pixmap)
    splash.showMessage("Loading Git-SVN Sync Tool...", 
                     Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom,
                     Qt.GlobalColor.black)
    splash.show()
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