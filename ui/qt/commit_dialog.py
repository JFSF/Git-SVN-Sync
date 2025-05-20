#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QTreeWidget, QTreeWidgetItem, QTextEdit, QComboBox,
                            QGroupBox, QDialogButtonBox, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont

from utils.helpers import suggest_commit_message, format_commit_message


class CommitDialog(QDialog):
    """Diálogo para commit usando Qt6 com seleção por checkboxes"""
    
    def __init__(self, parent=None, files=None, commit_templates=None):
        super().__init__(parent)
        
        self.files = files if files else []
        self.commit_templates = commit_templates if commit_templates else []
        
        # Variáveis para resultado
        self.selected_files = []
        self.commit_message = ""
        
        # Configurar janela
        self.setWindowTitle("Commit Changes")
        self.setMinimumSize(700, 500)
        
        # Criar widgets
        self.create_widgets()
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # ==========================================================
        # Área de seleção de arquivos
        # ==========================================================
        files_group = QGroupBox("Modified Files")
        files_layout = QVBoxLayout(files_group)
        
        # Botões de ação para arquivos
        file_actions = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_files)
        file_actions.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all_files)
        file_actions.addWidget(deselect_all_btn)
        
        file_actions.addStretch()
        files_layout.addLayout(file_actions)
        
        # TreeWidget para arquivos com checkboxes
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderLabels(["", "Status", "File Path"])
        self.files_tree.setColumnWidth(0, 30)  # Coluna de checkbox
        self.files_tree.setColumnWidth(1, 100) # Coluna de status
        self.files_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.files_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        files_layout.addWidget(self.files_tree)
        
        # Adicionar arquivos à treeview com checkboxes
        status_types = {
            "M": "Modified",
            "A": "Added",
            "D": "Deleted",
            "R": "Renamed",
            "?": "Untracked",
            "C": "Conflict"
        }
        
        for file_info in self.files:
            file_path = file_info.get('path', '')
            
            # Determinar tipo de status
            status_type = file_info.get('type', '?')
            status = status_types.get(status_type, status_type)
            
            # Criar item com checkbox
            item = QTreeWidgetItem(["", status, file_path])
            item.setCheckState(0, Qt.CheckState.Checked)  # Marcar por padrão
            
            # Definir ícone com base no status (simulado)
            # Em uma implementação real, você usaria ícones apropriados
            if status_type == "M":
                item.setForeground(1, Qt.GlobalColor.blue)
            elif status_type == "A":
                item.setForeground(1, Qt.GlobalColor.green)
            elif status_type == "D":
                item.setForeground(1, Qt.GlobalColor.red)
            elif status_type == "?":
                item.setForeground(1, Qt.GlobalColor.gray)
                
            self.files_tree.addTopLevelItem(item)
        
        main_layout.addWidget(files_group)
        
        # ==========================================================
        # Área de mensagem de commit
        # ==========================================================
        message_group = QGroupBox("Commit Message")
        message_layout = QVBoxLayout(message_group)
        
        # Template selector e sugestão
        template_layout = QHBoxLayout()
        
        # Template selector
        if self.commit_templates:
            template_layout.addWidget(QLabel("Use Template:"))
            
            self.template_combo = QComboBox()
            template_layout.addWidget(self.template_combo)
            
            # Adicionar opção vazia e templates
            self.template_combo.addItem("")
            for template in self.commit_templates:
                self.template_combo.addItem(template["name"])
            
            self.template_combo.currentTextChanged.connect(self.on_template_selected)
        
        # Botão de sugestão automática
        suggest_btn = QPushButton("Suggest Message")
        suggest_btn.clicked.connect(self.suggest_message)
        template_layout.addWidget(suggest_btn)
        
        template_layout.addStretch()
        message_layout.addLayout(template_layout)
        
        # Campo de texto para mensagem
        self.message_text = QTextEdit()
        self.message_text.setMinimumHeight(100)
        
        # Adicionar dica de placeholder para mensagem
        placeholder_font = self.message_text.font()
        placeholder_font.setItalic(True)
        self.message_text.setFont(placeholder_font)
        self.message_text.setPlaceholderText("Enter commit message here. First line is the summary, " 
                                          "followed by a blank line and detailed description if needed.")
        
        message_layout.addWidget(self.message_text)
        
        # Estatísticas da mensagem
        self.stats_label = QLabel("0 characters, 0 lines")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        message_layout.addWidget(self.stats_label)
        
        # Conectar eventos para atualizar estatísticas
        self.message_text.textChanged.connect(self.update_message_stats)
        
        main_layout.addWidget(message_group)
        
        # ==========================================================
        # Botões de ação
        # ==========================================================
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                     QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Commit")
        button_box.accepted.connect(self.on_commit)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def select_all_files(self):
        """Seleciona todos os arquivos na treeview"""
        for i in range(self.files_tree.topLevelItemCount()):
            item = self.files_tree.topLevelItem(i)
            item.setCheckState(0, Qt.CheckState.Checked)
    
    def deselect_all_files(self):
        """Desmarca todos os arquivos na treeview"""
        for i in range(self.files_tree.topLevelItemCount()):
            item = self.files_tree.topLevelItem(i)
            item.setCheckState(0, Qt.CheckState.Unchecked)
    
    def update_message_stats(self):
        """Atualiza estatísticas da mensagem de commit"""
        text = self.message_text.toPlainText()
        char_count = len(text)
        line_count = len(text.split('\n'))
        
        # Mostrar estatísticas
        self.stats_label.setText(f"{char_count} characters, {line_count} lines")
        
        # Alertar se a primeira linha for muito longa (melhor prática para Git)
        lines = text.split('\n')
        if lines and len(lines[0]) > 50:
            self.stats_label.setStyleSheet("color: orange")
            self.stats_label.setText(f"{char_count} characters, {line_count} lines - First line too long (should be under 50 chars)")
        else:
            self.stats_label.setStyleSheet("")
    
    def on_template_selected(self, template_name):
        """Preenche o campo de mensagem com o template selecionado"""
        if not template_name:
            return
        
        # Buscar o template correspondente
        template_content = None
        for template in self.commit_templates:
            if template["name"] == template_name:
                template_content = template["template"]
                break
        
        if template_content:
            # Limpar texto atual
            self.message_text.clear()
            
            # Inserir template
            self.message_text.setText(template_content)
    
    def suggest_message(self):
        """Sugere uma mensagem de commit com base nos arquivos selecionados"""
        selected_files = self.get_selected_files_info()
        
        if selected_files:
            # Usar helper para gerar sugestão
            suggested_message = suggest_commit_message(selected_files)
            
            # Preencher campo de mensagem se estiver vazio
            if not self.message_text.toPlainText().strip():
                self.message_text.setText(suggested_message)
            else:
                # Perguntar se deseja substituir ou mesclar
                reply = QMessageBox.question(
                    self, "Suggestion Available", 
                    f"Replace current message with suggestion:\n\n{suggested_message}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.message_text.setText(suggested_message)
        else:
            QMessageBox.information(self, "No Files Selected", "Please select files to generate a suggestion.")
    
    def get_selected_files_info(self):
        """Obtém informações dos arquivos selecionados"""
        selected_files = []
        
        for i in range(self.files_tree.topLevelItemCount()):
            item = self.files_tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                file_path = item.text(2)
                status = item.text(1)
                
                # Mapear status de volta para código
                type_code = "?"
                if status == "Modified":
                    type_code = "M"
                elif status == "Added":
                    type_code = "A"
                elif status == "Deleted":
                    type_code = "D"
                elif status == "Renamed":
                    type_code = "R"
                elif status == "Untracked":
                    type_code = "?"
                elif status == "Conflict":
                    type_code = "C"
                
                selected_files.append({
                    "path": file_path,
                    "type": type_code,
                    "tracked": type_code != "?"
                })
        
        return selected_files
    
    def on_commit(self):
        """Processa o commit quando o usuário clica em 'Commit'"""
        # Verificar se há arquivos selecionados
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.critical(self, "Error", "No files selected for commit")
            return
        
        # Obter mensagem de commit
        commit_message = self.message_text.toPlainText().strip()
        if not commit_message:
            QMessageBox.critical(self, "Error", "Commit message cannot be empty")
            return
            
        # Verificar primeira linha da mensagem (melhor prática Git)
        first_line = commit_message.split('\n')[0]
        if len(first_line) > 72:
            reply = QMessageBox.warning(
                self, "Long Commit Message", 
                "The first line of your commit message is very long. \n"
                "Best practices suggest keeping it under 50 characters.\n\n"
                "Do you want to continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Definir resultado e fechar
        self.selected_files = selected_files
        self.commit_message = commit_message
        self.accept()
    
    def get_selected_files(self):
        """Obtém lista de caminhos dos arquivos selecionados"""
        selected_paths = []
        
        for i in range(self.files_tree.topLevelItemCount()):
            item = self.files_tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                file_path = item.text(2)
                selected_paths.append(file_path)
        
        return selected_paths
    
    def get_commit_message(self):
        """Retorna a mensagem de commit"""
        return self.commit_message