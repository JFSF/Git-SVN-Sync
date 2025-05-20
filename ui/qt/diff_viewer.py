#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QTextEdit, QSplitter, QToolBar, QWidget, QTabWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter, QTextCursor

class DiffHighlighter(QSyntaxHighlighter):
    """Highlighter para destacar diferenças em texto"""
    
    def __init__(self, parent=None, mode="diff"):
        super().__init__(parent)
        self.mode = mode  # diff, added, removed
        
        # Formatos para diferenças
        self.addition_format = QTextCharFormat()
        self.addition_format.setBackground(QColor("#ccffcc"))  # Light green
        
        self.deletion_format = QTextCharFormat()
        self.deletion_format.setBackground(QColor("#ffcccc"))  # Light red
        
        self.header_format = QTextCharFormat()
        self.header_format.setForeground(QColor("#555599"))  # Blue-ish
        self.header_format.setFontWeight(QFont.Weight.Bold)
    
    def highlightBlock(self, text):
        """Aplica destaque baseado no conteúdo da linha"""
        if not text:
            return
            
        if self.mode == "diff":
            # Formato unificado
            if text.startswith('+'):
                self.setFormat(0, len(text), self.addition_format)
            elif text.startswith('-'):
                self.setFormat(0, len(text), self.deletion_format)
            elif text.startswith('@@') and text.endswith('@@'):
                self.setFormat(0, len(text), self.header_format)
            elif text.startswith('diff ') or text.startswith('index '):
                self.setFormat(0, len(text), self.header_format)
        
        elif self.mode == "added":
            # Todo o conteúdo é marcado como adicionado
            self.setFormat(0, len(text), self.addition_format)
            
        elif self.mode == "removed":
            # Todo o conteúdo é marcado como removido
            self.setFormat(0, len(text), self.deletion_format)


class DiffViewer(QDialog):
    """Visualizador de diferenças usando Qt6"""
    
    def __init__(self, parent=None, title=None, file_path=None, diff_data=None, mode="side-by-side"):
        """
        Inicializa o visualizador de diferenças
        
        Args:
            parent: Widget pai
            title: Título da janela
            file_path: Caminho do arquivo
            diff_data: Dados de diferença (dict com 'type', 'content' e 'diff')
            mode: Modo de visualização ('side-by-side' ou 'unified')
        """
        super().__init__(parent)
        
        self.title = title or "Diff Viewer"
        self.setWindowTitle(self.title)
        self.setMinimumSize(800, 600)
        
        self.file_path = file_path
        self.diff_data = diff_data or {"type": "diff", "content": None, "diff": ""}
        self.mode = mode
        
        # Widgets
        self.original_text = None  # QTextEdit para conteúdo original
        self.modified_text = None  # QTextEdit para conteúdo modificado
        self.unified_text = None   # QTextEdit para visualização unificada
        
        # Criar interface
        self.create_ui()
        
        # Exibir diferenças
        self.display_diff()
    
    def create_ui(self):
        """Cria a interface do visualizador"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Barra de ferramentas
        toolbar = QToolBar()
        
        # Botões de modo de visualização
        side_by_side_btn = QPushButton("Side by Side")
        side_by_side_btn.setCheckable(True)
        side_by_side_btn.setChecked(self.mode == "side-by-side")
        side_by_side_btn.clicked.connect(lambda: self.change_mode("side-by-side"))
        toolbar.addWidget(side_by_side_btn)
        
        unified_btn = QPushButton("Unified")
        unified_btn.setCheckable(True)
        unified_btn.setChecked(self.mode == "unified")
        unified_btn.clicked.connect(lambda: self.change_mode("unified"))
        toolbar.addWidget(unified_btn)
        
        # Adicionar barra de ferramentas ao layout
        main_layout.addWidget(toolbar)
        
        # Container para o conteúdo do diff
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Criar layout baseado no modo atual
        if self.mode == "side-by-side":
            self.create_side_by_side_view()
        else:
            self.create_unified_view()
        
        main_layout.addWidget(self.content_widget)
    
    def create_side_by_side_view(self):
        """Cria a visualização lado a lado"""
        # Limpar layout
        self.clear_content_layout()
        
        # Splitter para dois painéis
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Painel esquerdo (original)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_label = QLabel("Original")
        left_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(left_label)
        
        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.original_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.original_text.setFont(QFont("Monospace", 10))
        left_layout.addWidget(self.original_text)
        
        # Painel direito (modificado)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_label = QLabel("Modified")
        right_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(right_label)
        
        self.modified_text = QTextEdit()
        self.modified_text.setReadOnly(True)
        self.modified_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.modified_text.setFont(QFont("Monospace", 10))
        right_layout.addWidget(self.modified_text)
        
        # Adicionar painéis ao splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # Definir tamanhos iguais
        splitter.setSizes([1, 1])
        
        # Adicionar ao layout de conteúdo
        self.content_layout.addWidget(splitter)
        
        # Sincronizar rolagem
        self.sync_scrollbars()
    
    def create_unified_view(self):
        """Cria a visualização unificada"""
        # Limpar layout
        self.clear_content_layout()
        
        # Criar painel único
        self.unified_text = QTextEdit()
        self.unified_text.setReadOnly(True)
        self.unified_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.unified_text.setFont(QFont("Monospace", 10))
        
        # Adicionar ao layout de conteúdo
        self.content_layout.addWidget(self.unified_text)
    
    def clear_content_layout(self):
        """Limpa o layout de conteúdo"""
        # Remover todos os widgets do layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def sync_scrollbars(self):
        """Sincroniza os scrollbars entre os painéis original e modificado"""
        if not self.original_text or not self.modified_text:
            return
            
        # Conectar os scrollbars
        original_vsb = self.original_text.verticalScrollBar()
        modified_vsb = self.modified_text.verticalScrollBar()
        
        original_vsb.valueChanged.connect(modified_vsb.setValue)
        modified_vsb.valueChanged.connect(original_vsb.setValue)
    
    def change_mode(self, mode):
        """Muda o modo de visualização"""
        if mode == self.mode:
            return
            
        self.mode = mode
        
        # Recriar a visualização
        if mode == "side-by-side":
            self.create_side_by_side_view()
        else:
            self.create_unified_view()
            
        # Atualizar conteúdo
        self.display_diff()
    
    def display_diff(self):
        """Exibe as diferenças no modo atual"""
        if not self.diff_data:
            return
            
        diff_type = self.diff_data.get("type", "diff")
        
        if diff_type == "new_file":
            # Arquivo novo - mostrar apenas conteúdo
            content = self.diff_data.get("content", "")
            
            if self.mode == "side-by-side":
                # Lado a lado - original vazio, modificado com conteúdo
                if self.original_text and self.modified_text:
                    self.original_text.clear()
                    self.original_text.setPlainText("(New File)")
                    
                    self.modified_text.clear()
                    self.modified_text.setPlainText(content)
                    
                    # Aplicar highlighter
                    modified_highlighter = DiffHighlighter(self.modified_text.document(), "added")
            else:
                # Unificado - mostrar cabeçalho e conteúdo
                if self.unified_text:
                    self.unified_text.clear()
                    self.unified_text.setPlainText(f"--- /dev/null\n+++ {self.file_path}\n\n{content}")
                    
                    # Aplicar highlighter
                    unified_highlighter = DiffHighlighter(self.unified_text.document(), "diff")
        
        elif diff_type == "diff":
            # Arquivo modificado - processar diff
            diff_text = self.diff_data.get("diff", "")
            
            if self.mode == "side-by-side":
                # Processar diff para visualização lado a lado
                self._process_side_by_side(diff_text)
            else:
                # Visualização unificada
                if self.unified_text:
                    self.unified_text.clear()
                    self.unified_text.setPlainText(diff_text)
                    
                    # Aplicar highlighter
                    unified_highlighter = DiffHighlighter(self.unified_text.document(), "diff")
    
    def _process_side_by_side(self, diff_text):
        """Processa o diff para visualização lado a lado"""
        if not self.original_text or not self.modified_text:
            return
            
        self.original_text.clear()
        self.modified_text.clear()
        
        # Processamento simplificado do diff para visualização lado a lado
        original_lines = []
        modified_lines = []
        
        # Implementação simplificada - para um parser completo, seria necessário mais código
        header_pattern = re.compile(r'^@@\s+-(\d+),\d+\s+\+(\d+),\d+\s+@@')
        
        for line in diff_text.split('\n'):
            if line.startswith('@@'):
                # Cabeçalho de seção
                match = header_pattern.match(line)
                if match:
                    original_lines.append(f"Line {match.group(1)}...")
                    modified_lines.append(f"Line {match.group(2)}...")
            elif line.startswith('-'):
                # Linha removida
                original_lines.append(line[1:])
            elif line.startswith('+'):
                # Linha adicionada
                modified_lines.append(line[1:])
            elif line.startswith(' '):
                # Linha sem alteração
                original_lines.append(line[1:])
                modified_lines.append(line[1:])
            elif not line.startswith(('diff', 'index', '---', '+++')):
                # Ignorar linhas de cabeçalho do diff
                original_lines.append(line)
                modified_lines.append(line)
        
        # Definir texto nos painéis
        self.original_text.setPlainText('\n'.join(original_lines))
        self.modified_text.setPlainText('\n'.join(modified_lines))
        
        # Aplicar highlighters
        original_highlighter = DiffHighlighter(self.original_text.document(), "removed")
        modified_highlighter = DiffHighlighter(self.modified_text.document(), "added")