#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import difflib
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QTextEdit, QSplitter, QMessageBox, QDialogButtonBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter, QTextCursor


class DiffHighlighter(QSyntaxHighlighter):
    """Highlighter para destacar diferenças em texto"""
    
    def __init__(self, parent=None, mode="conflict"):
        super().__init__(parent)
        self.mode = mode  # conflict, git, svn
        
        # Formatos para diferenças
        self.addition_format = QTextCharFormat()
        self.addition_format.setBackground(QColor("#ccffcc"))
        
        self.deletion_format = QTextCharFormat()
        self.deletion_format.setBackground(QColor("#ffcccc"))
        
        self.conflict_format = QTextCharFormat()
        self.conflict_format.setBackground(QColor("#ffffcc"))
        
        self.marker_format = QTextCharFormat()
        self.marker_format.setForeground(QColor("#aa00aa"))
        self.marker_format.setFontWeight(700)  # Bold
    
    def highlightBlock(self, text):
        """Destaca o bloco de texto de acordo com o modo"""
        if self.mode == "conflict":
            # Destacar áreas de conflito
            if text.startswith("<<<<<<< GIT") or text.startswith("=======") or text.startswith(">>>>>>> SVN"):
                self.setFormat(0, len(text), self.marker_format)
            elif text.startswith("+"):
                self.setFormat(0, len(text), self.addition_format)
            elif text.startswith("-"):
                self.setFormat(0, len(text), self.deletion_format)
        
        elif self.mode == "git":
            # Destacar conteúdo Git
            self.setFormat(0, len(text), self.deletion_format)
            
        elif self.mode == "svn":
            # Destacar conteúdo SVN
            self.setFormat(0, len(text), self.addition_format)


class ConflictResolver(QDialog):
    """Resolvedor de conflitos usando Qt6"""
    
    def __init__(self, parent=None, file_path=None, working_dir=None, git_manager=None, svn_manager=None, logger=None):
        super().__init__(parent)
        
        self.file_path = file_path
        self.working_dir = working_dir
        self.git_manager = git_manager
        self.svn_manager = svn_manager
        self.logger = logger
        
        # Estado para guardar resultado
        self.result = None  # pode ser "git", "svn", "merged", ou None (cancelado)
        self.merged_content = None
        
        # Conteúdo dos arquivos
        self.git_content = None
        self.svn_content = None
        self.base_content = None
        self.current_content = None
        
        # Configurar janela
        self.setWindowTitle(f"Resolve Conflict: {file_path}")
        self.setMinimumSize(900, 700)
        
        # Obter conteúdo dos arquivos
        self._load_file_versions()
        
        # Criar widgets
        self.create_widgets()
        
        # Exibir diferenças
        self.load_diff()
    
    def _load_file_versions(self):
        """Carrega as diferentes versões do arquivo"""
        file_full_path = os.path.join(self.working_dir, self.file_path)
        
        try:
            # Versão local/atual
            with open(file_full_path, 'r', encoding='utf-8', errors='replace') as f:
                self.current_content = f.read()
            
            # Versão Git (versão HEAD)
            try:
                if self.git_manager and self.git_manager.repo:
                    git_content = self.git_manager.repo.git.show(f"HEAD:{self.file_path}")
                    self.git_content = git_content
                else:
                    self.git_content = "Git content not available"
            except Exception as e:
                self.logger.log(f"Error getting Git version: {str(e)}", "ERROR")
                self.git_content = "Error: Git content not available"
            
            # Versão SVN (versão do repositório)
            try:
                if self.svn_manager and self.svn_manager.is_svn_repo():
                    # Usar SVN cat para obter a versão do repositório
                    import subprocess
                    process = subprocess.run(
                        ["svn", "cat", self.file_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=self.working_dir
                    )
                    
                    if process.returncode == 0:
                        self.svn_content = process.stdout
                    else:
                        self.svn_content = "SVN content not available"
                else:
                    self.svn_content = "SVN content not available"
            except Exception as e:
                self.logger.log(f"Error getting SVN version: {str(e)}", "ERROR")
                self.svn_content = "Error: SVN content not available"
            
            # Versão base (versão ancestral comum)
            # Para simplificar, usamos uma das versões
            self.base_content = self.git_content
            
        except Exception as e:
            self.logger.log(f"Error loading file versions: {str(e)}", "ERROR")
    
    def create_widgets(self):
        """Cria os widgets do resolvedor de conflitos"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Splitter horizontal para três painéis
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Painel Git
        git_widget = QVBoxLayout()
        git_container = QWidget()
        git_container.setLayout(git_widget)
        
        git_label = QLabel("Git Version")
        git_label.setStyleSheet("font-weight: bold;")
        git_widget.addWidget(git_label)
        
        self.git_text = QTextEdit()
        self.git_text.setReadOnly(True)
        self.git_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.git_text.setFont(QFont("Monospace", 10))
        
        # Aplicar highlighter
        self.git_highlighter = DiffHighlighter(self.git_text.document(), "git")
        
        git_widget.addWidget(self.git_text)
        
        # Painel SVN
        svn_widget = QVBoxLayout()
        svn_container = QWidget()
        svn_container.setLayout(svn_widget)
        
        svn_label = QLabel("SVN Version")
        svn_label.setStyleSheet("font-weight: bold;")
        svn_widget.addWidget(svn_label)
        
        self.svn_text = QTextEdit()
        self.svn_text.setReadOnly(True)
        self.svn_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.svn_text.setFont(QFont("Monospace", 10))
        
        # Aplicar highlighter
        self.svn_highlighter = DiffHighlighter(self.svn_text.document(), "svn")
        
        svn_widget.addWidget(self.svn_text)
        
        # Painel de Mesclagem
        merged_widget = QVBoxLayout()
        merged_container = QWidget()
        merged_container.setLayout(merged_widget)
        
        merged_label = QLabel("Merged Result")
        merged_label.setStyleSheet("font-weight: bold;")
        merged_widget.addWidget(merged_label)
        
        self.merged_text = QTextEdit()
        self.merged_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.merged_text.setFont(QFont("Monospace", 10))
        
        # Aplicar highlighter
        self.merged_highlighter = DiffHighlighter(self.merged_text.document(), "conflict")
        
        merged_widget.addWidget(self.merged_text)
        
        # Adicionar painéis ao splitter
        splitter.addWidget(git_container)
        splitter.addWidget(svn_container)
        splitter.addWidget(merged_container)
        
        # Definir tamanhos iniciais
        splitter.setSizes([300, 300, 300])
        
        main_layout.addWidget(splitter)
        
        # Botões de escolha/ação
        action_layout = QHBoxLayout()
        
        # Botões de escolha
        use_git_btn = QPushButton("Use Git Version")
        use_git_btn.clicked.connect(self.use_git_version)
        action_layout.addWidget(use_git_btn)
        
        use_svn_btn = QPushButton("Use SVN Version")
        use_svn_btn.clicked.connect(self.use_svn_version)
        action_layout.addWidget(use_svn_btn)
        
        auto_merge_btn = QPushButton("Auto-Merge")
        auto_merge_btn.clicked.connect(self.auto_merge)
        action_layout.addWidget(auto_merge_btn)
        
        action_layout.addStretch()
        
        # Botões de ação
        save_btn = QPushButton("Save Merged")
        save_btn.clicked.connect(self.save_merged)
        action_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.cancel)
        action_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(action_layout)
    
    def load_diff(self):
        """Carrega o conteúdo nos painéis de texto"""
        # Limpar e desabilitar textos
        self.git_text.setReadOnly(False)
        self.svn_text.setReadOnly(False)
        self.merged_text.setReadOnly(False)
        
        self.git_text.clear()
        self.svn_text.clear()
        self.merged_text.clear()
        
        # Inserir conteúdo nos painéis Git e SVN
        if self.git_content:
            self.git_text.setText(self.git_content)
        
        if self.svn_content:
            self.svn_text.setText(self.svn_content)
        
        # Desabilitar edição apenas após inserir texto
        self.git_text.setReadOnly(True)
        self.svn_text.setReadOnly(True)
        
        # Criar mesclagem inicial
        self.auto_merge()
    
    def use_git_version(self):
        """Usa a versão Git como resultado final"""
        self.merged_text.clear()
        self.merged_text.setText(self.git_content)
        self.merged_content = self.git_content
        self.result = "git"
    
    def use_svn_version(self):
        """Usa a versão SVN como resultado final"""
        self.merged_text.clear()
        self.merged_text.setText(self.svn_content)
        self.merged_content = self.svn_content
        self.result = "svn"
    
    def auto_merge(self):
        """Tenta realizar uma mesclagem automática"""
        if not self.git_content or not self.svn_content or not self.base_content:
            QMessageBox.warning(self, "Warning", "Missing content for one or more versions")
            return
            
        # Dividir conteúdo em linhas
        git_lines = self.git_content.splitlines()
        svn_lines = self.svn_content.splitlines()
        base_lines = self.base_content.splitlines()
        
        # Usar o algoritmo de três vias
        merged_lines = []
        has_conflicts = False
        
        # Comparar base com Git e SVN
        git_matcher = difflib.SequenceMatcher(None, base_lines, git_lines)
        svn_matcher = difflib.SequenceMatcher(None, base_lines, svn_lines)
        
        git_opcodes = git_matcher.get_opcodes()
        svn_opcodes = svn_matcher.get_opcodes()
        
        # Mapear alterações em relação à base
        git_changes = {}
        svn_changes = {}
        
        for tag, i1, i2, j1, j2 in git_opcodes:
            if tag != 'equal':
                for i in range(i1, i2):
                    git_changes[i] = (tag, j1, j2)
        
        for tag, i1, i2, j1, j2 in svn_opcodes:
            if tag != 'equal':
                for i in range(i1, i2):
                    svn_changes[i] = (tag, j1, j2)
        
        # Construir resultado mesclado
        for i, base_line in enumerate(base_lines):
            git_change = git_changes.get(i)
            svn_change = svn_changes.get(i)
            
            if git_change and not svn_change:
                # Apenas Git alterou esta linha
                tag, j1, j2 = git_change
                if tag == 'replace' or tag == 'delete':
                    # Usar versão do Git (ou remover)
                    if j1 < j2:
                        merged_lines.extend(git_lines[j1:j2])
                elif tag == 'insert':
                    # Não deveria acontecer com uma única linha
                    pass
            
            elif svn_change and not git_change:
                # Apenas SVN alterou esta linha
                tag, j1, j2 = svn_change
                if tag == 'replace' or tag == 'delete':
                    # Usar versão do SVN (ou remover)
                    if j1 < j2:
                        merged_lines.extend(svn_lines[j1:j2])
                elif tag == 'insert':
                    # Não deveria acontecer com uma única linha
                    pass
            
            elif git_change and svn_change:
                # Ambos alteraram - possível conflito
                git_tag, git_j1, git_j2 = git_change
                svn_tag, svn_j1, svn_j2 = svn_change
                
                if git_tag == 'delete' and svn_tag == 'delete':
                    # Ambos removeram - sem conflito
                    pass
                else:
                    # Conflito - adicionar marcadores
                    merged_lines.append("<<<<<<< GIT")
                    if git_j1 < git_j2:
                        merged_lines.extend(git_lines[git_j1:git_j2])
                    merged_lines.append("=======")
                    if svn_j1 < svn_j2:
                        merged_lines.extend(svn_lines[svn_j1:svn_j2])
                    merged_lines.append(">>>>>>> SVN")
                    has_conflicts = True
            
            else:
                # Nenhum alterou - usar linha base
                merged_lines.append(base_line)
        
        # Exibir resultado mesclado
        self.merged_text.clear()
        merged_content = "\n".join(merged_lines)
        self.merged_text.setText(merged_content)
        
        # Destacar conflitos
        if has_conflicts:
            self._highlight_conflicts()
            self.logger.log(f"Merge conflicts found in {self.file_path}", "WARNING")
        else:
            self.logger.log(f"Auto-merge successful for {self.file_path}", "SUCCESS")
        
        self.merged_content = merged_content
        self.result = "merged" if not has_conflicts else None
    
    def _highlight_conflicts(self):
        """Destaca as áreas de conflito no texto mesclado"""
        # O highlighter já deve lidar com isso automaticamente
        pass
    
    def save_merged(self):
        """Salva o resultado mesclado"""
        self.merged_content = self.merged_text.toPlainText()
        
        if "<<<<<<< GIT" in self.merged_content:
            if QMessageBox.question(
                self, "Save With Conflicts", 
                "The merged result still contains conflict markers. Save anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) != QMessageBox.StandardButton.Yes:
                return
        
        self.result = "merged"
        self.accept()
    
    def cancel(self):
        """Cancela a resolução de conflito"""
        self.result = None
        self.reject()