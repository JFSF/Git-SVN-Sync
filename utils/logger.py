#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont
from PyQt6.QtCore import Qt

class LogManager:
    """Gerenciador de log adaptado para Qt6 com estilos personalizados"""
    
    def __init__(self, log_widget=None, log_file=None):
        """Inicializa o gerenciador de log"""
        self.log_widget = log_widget
        self.log_file = log_file
        
        # Cores personalizadas para diferentes níveis de log
        self.log_colors = {
            "INFO": QColor("#000000"),     # Preto
            "SUCCESS": QColor("#008800"),  # Verde
            "WARNING": QColor("#FF8800"),  # Amarelo/Laranja
            "ERROR": QColor("#FF0000"),    # Vermelho
            "DEBUG": QColor("#888888")     # Cinza
        }
        
        # Formatos de texto para diferentes níveis de log
        self.text_formats = {}
        
        # Configurar formatos de texto se o widget estiver disponível
        if self.log_widget:
            self.setup_text_tags()
    
    def setup_text_tags(self):
        """Configura os formatos de texto para diferentes níveis de log"""
        # INFO - Normal
        info_format = QTextCharFormat()
        info_format.setForeground(self.log_colors["INFO"])
        self.text_formats["INFO"] = info_format
        
        # SUCCESS - Verde negrito
        success_format = QTextCharFormat()
        success_format.setForeground(self.log_colors["SUCCESS"])
        success_format.setFontWeight(QFont.Weight.Bold)  # Negrito
        self.text_formats["SUCCESS"] = success_format
        
        # WARNING - Amarelo itálico
        warning_format = QTextCharFormat()
        warning_format.setForeground(self.log_colors["WARNING"])
        warning_format.setFontItalic(True)  # Itálico
        self.text_formats["WARNING"] = warning_format
        
        # ERROR - Vermelho normal
        error_format = QTextCharFormat()
        error_format.setForeground(self.log_colors["ERROR"])
        self.text_formats["ERROR"] = error_format
        
        # DEBUG - Cinza pequeno
        debug_format = QTextCharFormat()
        debug_format.setForeground(self.log_colors["DEBUG"])
        debug_format.setFontPointSize(8)  # Fonte menor
        self.text_formats["DEBUG"] = debug_format
    
    def log(self, message, level="INFO"):
        """Registra uma mensagem com nível específico"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        # Registrar no widget se disponível
        if self.log_widget and isinstance(self.log_widget, QTextEdit):
            self._append_to_widget(formatted_message, level)
        
        # Registrar no arquivo se configurado
        if self.log_file:
            self._append_to_file(formatted_message)
        
        # Sempre imprimir no console
        print(formatted_message)
    
    def _append_to_widget(self, message, level="INFO"):
        """Adiciona uma mensagem ao widget de log com formatação"""
        # Obter o cursor e formatar o texto
        cursor = self.log_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Certificar que temos o formato correto para o nível
        if level not in self.text_formats:
            self.setup_text_tags()
        
        # Aplicar o formato para este nível
        format = self.text_formats.get(level, self.text_formats["INFO"])
        
        # Inserir o texto formatado
        cursor.insertText(message + "\n", format)
        
        # Rolar para a última linha
        self.log_widget.setTextCursor(cursor)
        self.log_widget.ensureCursorVisible()
    
    def _append_to_file(self, message):
        """Adiciona uma mensagem ao arquivo de log"""
        try:
            # Criar diretório se não existir
            if self.log_file:
                os.makedirs(os.path.dirname(os.path.abspath(self.log_file)), exist_ok=True)
                
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(message + "\n")
        except Exception as e:
            print(f"Error writing to log file: {str(e)}")
    
    def clear_widget(self):
        """Limpa o widget de log"""
        if self.log_widget and isinstance(self.log_widget, QTextEdit):
            self.log_widget.clear()
    
    def set_log_file(self, file_path):
        """Define o arquivo para registro de log"""
        self.log_file = file_path
        
        # Criar diretório se não existir
        if file_path:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Adicionar cabeçalho ao arquivo
            try:
                with open(file_path, 'a', encoding='utf-8') as f:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] === Log Session Started ===\n")
            except Exception as e:
                print(f"Error initializing log file: {str(e)}")