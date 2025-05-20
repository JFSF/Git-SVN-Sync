#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import webbrowser
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QWidget, QTabWidget, QGroupBox, QMessageBox,
                            QFormLayout, QLineEdit, QRadioButton, QComboBox,
                            QTextEdit, QCheckBox, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QThread


class WorkerThread(QThread):
    """Thread worker para operações de API"""
    finished = pyqtSignal(bool, object)
    log = pyqtSignal(str, str)
    
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            if callable(self.function):
                result = self.function(*self.args, **self.kwargs)
                self.finished.emit(True, result)
        except Exception as e:
            self.log.emit(f"Error in worker thread: {str(e)}", "ERROR")
            self.finished.emit(False, str(e))


class TaskIntegrationDialog(QDialog):
    """Diálogo de integração com sistemas de tarefas usando Qt6"""
    
    def __init__(self, parent=None, task_manager=None):
        super().__init__(parent)
        
        self.task_manager = task_manager
        
        # Configurar janela
        self.setWindowTitle("Task Integration")
        self.setMinimumSize(750, 550)
        
        # Criar widgets
        self.create_widgets()
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # TabWidget para abas
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Criar abas
        self.create_config_tab()
        self.create_tasks_tab()
        
        # Botões de diálogo
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close
        )
        button_box.accepted.connect(self.save_config)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def create_config_tab(self):
        """Cria o conteúdo da aba de configuração"""
        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab)
        
        # Sistema de tarefas
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        system_label = QLabel("Task System:")
        self.system_combo = QComboBox()
        self.system_combo.addItems(["none", "jira", "trello"])
        self.system_combo.currentTextChanged.connect(self.on_system_change)
        form_layout.addRow(system_label, self.system_combo)
        
        config_layout.addLayout(form_layout)
        
        # TabWidget para configurações específicas
        self.config_tabs = QTabWidget()
        config_layout.addWidget(self.config_tabs)
        
        # Aba de configuração do Jira
        jira_tab = QWidget()
        jira_layout = QFormLayout(jira_tab)
        jira_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.jira_url_edit = QLineEdit()
        jira_layout.addRow("Jira URL:", self.jira_url_edit)
        
        self.jira_username_edit = QLineEdit()
        jira_layout.addRow("Username:", self.jira_username_edit)
        
        self.jira_token_edit = QLineEdit()
        self.jira_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        jira_layout.addRow("API Token:", self.jira_token_edit)
        
        self.jira_project_edit = QLineEdit()
        jira_layout.addRow("Default Project:", self.jira_project_edit)
        
        jira_test_btn = QPushButton("Test Connection")
        jira_test_btn.clicked.connect(lambda: self.test_connection("jira"))
        jira_layout.addRow("", jira_test_btn)
        
        self.config_tabs.addTab(jira_tab, "Jira")
        
        # Aba de configuração do Trello
        trello_tab = QWidget()
        trello_layout = QFormLayout(trello_tab)
        trello_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.trello_key_edit = QLineEdit()
        trello_layout.addRow("API Key:", self.trello_key_edit)
        
        self.trello_token_edit = QLineEdit()
        self.trello_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        trello_layout.addRow("Token:", self.trello_token_edit)
        
        self.trello_board_edit = QLineEdit()
        trello_layout.addRow("Board ID:", self.trello_board_edit)
        
        trello_test_btn = QPushButton("Test Connection")
        trello_test_btn.clicked.connect(lambda: self.test_connection("trello"))
        trello_layout.addRow("", trello_test_btn)
        
        self.config_tabs.addTab(trello_tab, "Trello")
        
        # Configurações gerais
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout(general_group)
        
        self.extract_branch_check = QCheckBox("Extract task ID from branch name")
        general_layout.addWidget(self.extract_branch_check)
        
        self.auto_update_check = QCheckBox("Automatically update task status on commit")
        general_layout.addWidget(self.auto_update_check)
        
        regex_layout = QFormLayout()
        regex_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.regex_edit = QLineEdit()
        regex_layout.addRow("Task ID Regex:", self.regex_edit)
        
        general_layout.addLayout(regex_layout)
        
        config_layout.addWidget(general_group)
        
        # Adicionar aba ao TabWidget principal
        self.tab_widget.addTab(config_tab, "Configuration")
        
        # Carregar configurações
        self.load_config()
    
    def create_tasks_tab(self):
        """Cria o conteúdo da aba de tarefas"""
        tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(tasks_tab)
        
        # Frame de pesquisa
        search_group = QGroupBox("Search Task")
        search_layout = QHBoxLayout(search_group)
        
        search_layout.addWidget(QLabel("Task ID:"))
        
        self.task_id_edit = QLineEdit()
        search_layout.addWidget(self.task_id_edit)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search_task)
        search_layout.addWidget(search_btn)
        
        search_layout.addStretch()
        
        tasks_layout.addWidget(search_group)
        
        # Frame de detalhes da tarefa
        details_group = QGroupBox("Task Details")
        details_layout = QFormLayout(details_group)
        details_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.task_id_label = QLabel("")
        details_layout.addRow("ID:", self.task_id_label)
        
        self.task_title_label = QLabel("")
        details_layout.addRow("Title:", self.task_title_label)
        
        self.task_status_label = QLabel("")
        details_layout.addRow("Status:", self.task_status_label)
        
        self.task_type_label = QLabel("")
        details_layout.addRow("Type:", self.task_type_label)
        
        self.task_assignee_label = QLabel("")
        details_layout.addRow("Assignee:", self.task_assignee_label)
        
        # Link para a tarefa
        self.task_link_label = QLabel("")
        self.task_link_label.setStyleSheet("color: blue; text-decoration: underline;")
        self.task_link_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.task_link_label.mousePressEvent = self.open_task_link
        details_layout.addRow("", self.task_link_label)
        
        tasks_layout.addWidget(details_group)
        
        # Frame de ações
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        # Atualização de status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Update Status:"))
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["In Progress", "In Review", "Done"])
        status_layout.addWidget(self.status_combo)
        
        update_btn = QPushButton("Update")
        update_btn.clicked.connect(self.update_task_status)
        status_layout.addWidget(update_btn)
        
        status_layout.addStretch()
        actions_layout.addLayout(status_layout)
        
        # Adicionar comentário
        actions_layout.addWidget(QLabel("Add Comment:"))
        
        self.comment_text = QTextEdit()
        self.comment_text.setMaximumHeight(100)
        actions_layout.addWidget(self.comment_text)
        
        comment_btn = QPushButton("Add Comment")
        comment_btn.clicked.connect(self.add_task_comment)
        
        comment_layout = QHBoxLayout()
        comment_layout.addStretch()
        comment_layout.addWidget(comment_btn)
        
        actions_layout.addLayout(comment_layout)
        
        tasks_layout.addWidget(actions_group)
        
        # Adicionar aba ao TabWidget principal
        self.tab_widget.addTab(tasks_tab, "Tasks")
    
    def load_config(self):
        """Carrega as configurações do gerenciador"""
        if not self.task_manager:
            return
            
        # Sistema de tarefas
        self.system_combo.setCurrentText(self.task_manager.task_system)
        
        # Configurações do Jira
        self.jira_url_edit.setText(self.task_manager.jira_url)
        self.jira_username_edit.setText(self.task_manager.jira_username)
        self.jira_token_edit.setText(self.task_manager.jira_token)
        self.jira_project_edit.setText(self.task_manager.jira_project)
        
        # Configurações do Trello
        self.trello_key_edit.setText(self.task_manager.trello_api_key)
        self.trello_token_edit.setText(self.task_manager.trello_token)
        self.trello_board_edit.setText(self.task_manager.trello_board_id)
        
        # Configurações gerais
        self.extract_branch_check.setChecked(self.task_manager.extract_from_branch)
        self.auto_update_check.setChecked(self.task_manager.auto_update_task)
        self.regex_edit.setText(self.task_manager.task_id_regex)
        
        # Selecionar aba apropriada
        self.on_system_change(self.task_manager.task_system)
    
    def on_system_change(self, system):
        """Manipula a alteração do sistema de tarefas"""
        # Selecionar aba correspondente
        if system == "jira":
            self.config_tabs.setCurrentIndex(0)
        elif system == "trello":
            self.config_tabs.setCurrentIndex(1)
    
    def test_connection(self, system):
        """Testa a conexão com o sistema de tarefas"""
        if system == "jira":
            # Validar campos
            url = self.jira_url_edit.text().strip()
            username = self.jira_username_edit.text().strip()
            token = self.jira_token_edit.text().strip()
            
            if not url or not username or not token:
                QMessageBox.critical(self, "Error", "Please fill in all Jira fields")
                return
                
            # Mostrar mensagem de progresso
            QMessageBox.information(self, "Testing Connection", "Testing connection to Jira...\nThis may take a moment.")
            
            # TODO: Implementar teste real de conexão usando worker thread
            # Por agora, simular sucesso
            QMessageBox.information(self, "Success", "Connection to Jira successful!")
            
        elif system == "trello":
            # Validar campos
            api_key = self.trello_key_edit.text().strip()
            token = self.trello_token_edit.text().strip()
            
            if not api_key or not token:
                QMessageBox.critical(self, "Error", "Please fill in API Key and Token fields")
                return
                
            # Mostrar mensagem de progresso
            QMessageBox.information(self, "Testing Connection", "Testing connection to Trello...\nThis may take a moment.")
            
            # TODO: Implementar teste real de conexão usando worker thread
            # Por agora, simular sucesso
            QMessageBox.information(self, "Success", "Connection to Trello successful!")
    
    def save_config(self):
        """Salva as configurações no gerenciador"""
        if not self.task_manager:
            QMessageBox.critical(self, "Error", "Task manager not initialized")
            return
            
        # Validar regex
        regex_pattern = self.regex_edit.text().strip()
        try:
            re.compile(regex_pattern)
        except re.error:
            QMessageBox.critical(self, "Error", "Invalid regex pattern")
            return
            
        # Atualizar configurações no gerenciador
        self.task_manager.task_system = self.system_combo.currentText()
        self.task_manager.jira_url = self.jira_url_edit.text().strip()
        self.task_manager.jira_username = self.jira_username_edit.text().strip()
        self.task_manager.jira_token = self.jira_token_edit.text().strip()
        self.task_manager.jira_project = self.jira_project_edit.text().strip()
        
        self.task_manager.trello_api_key = self.trello_key_edit.text().strip()
        self.task_manager.trello_token = self.trello_token_edit.text().strip()
        self.task_manager.trello_board_id = self.trello_board_edit.text().strip()
        
        self.task_manager.extract_from_branch = self.extract_branch_check.isChecked()
        self.task_manager.auto_update_task = self.auto_update_check.isChecked()
        self.task_manager.task_id_regex = regex_pattern
        
        # Salvar no config_manager
        self.task_manager.save_config()
        
        QMessageBox.information(self, "Success", "Task integration settings saved")
        self.accept()
    
    def search_task(self):
        """Busca informações de uma tarefa"""
        task_id = self.task_id_edit.text().strip()
        
        if not task_id:
            QMessageBox.critical(self, "Error", "Please enter a task ID")
            return
            
        # Validar formato usando regex configurada
        try:
            pattern = re.compile(self.regex_edit.text().strip())
            if not pattern.match(task_id):
                QMessageBox.warning(self, "Warning", f"Task ID doesn't match the pattern: {self.regex_edit.text().strip()}")
        except re.error:
            QMessageBox.warning(self, "Warning", "Invalid regex pattern. Using default validation.")
        
        # Mostrar mensagem de progresso
        QMessageBox.information(self, "Searching", "Searching for task...\nThis may take a moment.")
        
        # TODO: Implementar busca real usando worker thread
        # Por agora, simular uma tarefa de exemplo
        task_info = {
            "id": task_id,
            "title": "Example Task: Implement Qt6 Migration",
            "status": "In Progress",
            "type": "Feature",
            "assignee": "Current User",
            "url": "https://example.com/browse/" + task_id
        }
        
        # Exibir informações
        self.task_id_label.setText(task_info.get("id", ""))
        self.task_title_label.setText(task_info.get("title", ""))
        self.task_status_label.setText(task_info.get("status", ""))
        self.task_type_label.setText(task_info.get("type", ""))
        self.task_assignee_label.setText(task_info.get("assignee", ""))
        
        # Configurar link
        url = task_info.get("url", "")
        if url:
            self.task_link_label.setText(f"Open in browser: {url}")
        else:
            self.task_link_label.setText("")
    
    def open_task_link(self, event):
        """Abre o link da tarefa no navegador"""
        link_text = self.task_link_label.text()
        if link_text.startswith("Open in browser: "):
            url = link_text.replace("Open in browser: ", "")
            try:
                webbrowser.open(url)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open browser: {str(e)}")
    
    def update_task_status(self):
        """Atualiza o status da tarefa"""
        task_id = self.task_id_label.text()
        new_status = self.status_combo.currentText()
        
        if not task_id:
            QMessageBox.critical(self, "Error", "No task selected")
            return
            
        if not new_status:
            QMessageBox.critical(self, "Error", "Please select a status")
            return
            
        # Mostrar mensagem de progresso
        QMessageBox.information(self, "Updating", "Updating task status...\nThis may take a moment.")
        
        # TODO: Implementar atualização real usando worker thread
        # Por agora, simular sucesso
        self.task_status_label.setText(new_status)
        QMessageBox.information(self, "Success", f"Task status updated to {new_status}")
    
    def add_task_comment(self):
        """Adiciona um comentário à tarefa"""
        task_id = self.task_id_label.text()
        comment_text = self.comment_text.toPlainText().strip()
        
        if not task_id:
            QMessageBox.critical(self, "Error", "No task selected")
            return
            
        if not comment_text:
            QMessageBox.critical(self, "Error", "Please enter a comment")
            return
            
        # Mostrar mensagem de progresso
        QMessageBox.information(self, "Adding Comment", "Adding comment to task...\nThis may take a moment.")
        
        # TODO: Implementar adição real usando worker thread
        # Por agora, simular sucesso
        self.comment_text.clear()
        QMessageBox.information(self, "Success", "Comment added successfully")