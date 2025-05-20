#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QListWidget, QTextEdit, QWidget, QGroupBox, QMessageBox,
                            QFormLayout, QLineEdit, QDialogButtonBox, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal


class CommitTemplateDialog(QDialog):
    """Diálogo para gerenciamento de templates de commit usando Qt6"""
    
    template_updated = pyqtSignal()  # Sinal emitido quando um template é atualizado
    
    def __init__(self, parent=None, template_manager=None):
        super().__init__(parent)
        
        self.template_manager = template_manager
        
        # Configurar janela
        self.setWindowTitle("Commit Templates")
        self.setMinimumSize(700, 500)
        
        # Criar widgets
        self.create_widgets()
        
        # Carregar templates existentes
        self.load_templates()
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Splitter horizontal para lista e edição
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Painel esquerdo - Lista de templates
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_label = QLabel("Available Templates")
        left_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        left_layout.addWidget(left_label)
        
        self.templates_list = QListWidget()
        self.templates_list.itemSelectionChanged.connect(self.on_template_select)
        left_layout.addWidget(self.templates_list)
        
        # Botões para gerenciar templates
        buttons_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self.on_new_template)
        buttons_layout.addWidget(self.new_btn)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.on_edit_template)
        self.edit_btn.setEnabled(False)
        buttons_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.on_delete_template)
        self.delete_btn.setEnabled(False)
        buttons_layout.addWidget(self.delete_btn)
        
        buttons_layout.addStretch()
        left_layout.addLayout(buttons_layout)
        
        # Painel direito - Edição de template
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Formulário para nome e conteúdo do template
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        template_name_label = QLabel("Template Name:")
        template_name_label.setStyleSheet("font-weight: bold;")
        self.name_edit = QLineEdit()
        form_layout.addRow(template_name_label, self.name_edit)
        
        template_content_label = QLabel("Template Content:")
        template_content_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(template_content_label)
        
        self.template_text = QTextEdit()
        right_layout.addWidget(self.template_text)
        
        # Adicionar formulário ao layout
        right_layout.insertLayout(0, form_layout)
        
        # Ajuda sobre placeholders
        help_group = QGroupBox("Placeholder Help")
        help_layout = QVBoxLayout(help_group)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(120)
        help_text.setText("Available placeholders:\n"
                         "{description} - Brief description of changes\n"
                         "{issue_number} - Issue or ticket number\n"
                         "{reason} - Reason for changes\n"
                         "{author} - Commit author\n\n"
                         "Use placeholders like {name} in your template.")
        help_layout.addWidget(help_text)
        
        right_layout.addWidget(help_group)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.on_save_template)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        button_layout.addStretch()
        right_layout.addLayout(button_layout)
        
        # Adicionar painéis ao splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Definir proporções iniciais
        splitter.setSizes([200, 500])
        
        # Adicionar splitter ao layout principal
        main_layout.addWidget(splitter)
        
        # Botões de diálogo
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def load_templates(self):
        """Carrega templates na listbox"""
        if not self.template_manager:
            return
            
        self.templates_list.clear()
        
        for template in self.template_manager.get_templates():
            self.templates_list.addItem(template["name"])
    
    def on_template_select(self):
        """Manipula a seleção de um template"""
        if not self.templates_list.selectedItems():
            # Nenhum item selecionado
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            return
        
        # Obter template selecionado
        template_name = self.templates_list.currentItem().text()
        template = None
        
        for t in self.template_manager.get_templates():
            if t["name"] == template_name:
                template = t
                break
        
        if not template:
            return
            
        # Atualizar campos
        self.name_edit.setText(template["name"])
        self.template_text.setText(template["template"])
        
        # Habilitar botões
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
    
    def on_new_template(self):
        """Cria um novo template"""
        # Limpar seleção atual
        self.templates_list.clearSelection()
        
        # Limpar campos
        self.name_edit.clear()
        self.template_text.clear()
        
        # Focar no campo de nome
        self.name_edit.setFocus()
        
        # Atualizar estados dos botões
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.save_btn.setEnabled(True)
    
    def on_edit_template(self):
        """Habilita edição de um template"""
        # Já está habilitado pela seleção
        self.name_edit.setFocus()
    
    def on_delete_template(self):
        """Remove um template"""
        if not self.templates_list.selectedItems():
            return
            
        template_name = self.templates_list.currentItem().text()
        
        # Confirmar exclusão
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Delete template '{template_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # Encontrar índice do template
        index = -1
        for i, template in enumerate(self.template_manager.get_templates()):
            if template["name"] == template_name:
                index = i
                break
                
        if index >= 0:
            # Deletar template
            self.template_manager.delete_template(index)
            
            # Recarregar lista
            self.load_templates()
            
            # Limpar campos
            self.name_edit.clear()
            self.template_text.clear()
            
            # Desabilitar botões
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            
            # Emitir sinal de atualização
            self.template_updated.emit()
    
    def on_save_template(self):
        """Salva um template novo ou editado"""
        # Validar campos
        name = self.name_edit.text().strip()
        template_content = self.template_text.toPlainText().strip()
        
        if not name or not template_content:
            QMessageBox.critical(self, "Error", "Name and template content are required")
            return
            
        # Verificar se está editando ou criando novo
        editing = False
        index = -1
        
        if self.templates_list.selectedItems():
            selected_name = self.templates_list.currentItem().text()
            for i, template in enumerate(self.template_manager.get_templates()):
                if template["name"] == selected_name:
                    index = i
                    editing = True
                    break
        
        # Salvar template
        if editing and index >= 0:
            self.template_manager.update_template(index, name, template_content)
        else:
            self.template_manager.add_template(name, template_content)
            
        # Recarregar lista
        self.load_templates()
        
        # Selecionar o template salvo
        items = self.templates_list.findItems(name, Qt.MatchFlag.MatchExactly)
        if items:
            self.templates_list.setCurrentItem(items[0])
            
        # Emitir sinal de atualização
        self.template_updated.emit()
        
        # Mostrar mensagem de sucesso
        QMessageBox.information(self, "Success", "Template saved successfully")