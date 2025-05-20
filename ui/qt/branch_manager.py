#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QListWidget, QWidget, QGroupBox, QMessageBox,
                            QFormLayout, QLineEdit, QCheckBox, QDialogButtonBox,
                            QSplitter, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QThread


class WorkerThread(QThread):
    """Thread worker para operações Git"""
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


class BranchManagerDialog(QDialog):
    """Diálogo de gerenciamento de branches usando Qt6"""
    
    def __init__(self, parent=None, git_manager=None, logger=None):
        super().__init__(parent)
        
        self.git_manager = git_manager
        self.logger = logger
        
        # Variáveis
        self.current_branch = None
        self.local_branches = []
        self.remote_branches = []
        
        # Configurar diálogo
        self.setWindowTitle("Branch Manager")
        self.setMinimumSize(700, 500)
        
        # Criar widgets
        self.create_widgets()
        
        # Atualizar lista de branches
        self.refresh_branches()
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Splitter para duas colunas
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Branches locais
        local_widget = QWidget()
        local_layout = QVBoxLayout(local_widget)
        
        local_label = QLabel("Local Branches")
        local_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        local_layout.addWidget(local_label)
        
        self.local_list = QListWidget()
        self.local_list.itemSelectionChanged.connect(self.on_local_branch_select)
        local_layout.addWidget(self.local_list)
        
        # Branches remotas
        remote_widget = QWidget()
        remote_layout = QVBoxLayout(remote_widget)
        
        remote_label = QLabel("Remote Branches")
        remote_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        remote_layout.addWidget(remote_label)
        
        self.remote_list = QListWidget()
        self.remote_list.itemSelectionChanged.connect(self.on_remote_branch_select)
        remote_layout.addWidget(self.remote_list)
        
        # Adicionar widgets ao splitter
        splitter.addWidget(local_widget)
        splitter.addWidget(remote_widget)
        
        # Adicionar splitter ao layout
        main_layout.addWidget(splitter)
        
        # Frame de informações da branch atual
        current_group = QGroupBox("Current Branch")
        current_layout = QFormLayout(current_group)
        
        self.current_branch_label = QLabel("...")
        current_layout.addRow("Branch:", self.current_branch_label)
        
        self.current_status_label = QLabel("...")
        current_layout.addRow("Status:", self.current_status_label)
        
        main_layout.addWidget(current_group)
        
        # Frame de ações
        actions_layout = QHBoxLayout()
        
        # Ações para branches locais
        local_actions = QGroupBox("Local Branch Actions")
        local_actions_layout = QVBoxLayout(local_actions)
        
        self.checkout_btn = QPushButton("Checkout Selected")
        self.checkout_btn.clicked.connect(self.checkout_selected_branch)
        local_actions_layout.addWidget(self.checkout_btn)
        
        self.create_branch_btn = QPushButton("Create New Branch")
        self.create_branch_btn.clicked.connect(self.create_new_branch)
        local_actions_layout.addWidget(self.create_branch_btn)
        
        self.delete_branch_btn = QPushButton("Delete Selected")
        self.delete_branch_btn.clicked.connect(self.delete_selected_branch)
        local_actions_layout.addWidget(self.delete_branch_btn)
        
        actions_layout.addWidget(local_actions)
        
        # Ações para branches remotas
        remote_actions = QGroupBox("Remote Branch Actions")
        remote_actions_layout = QVBoxLayout(remote_actions)
        
        self.checkout_remote_btn = QPushButton("Checkout Remote")
        self.checkout_remote_btn.clicked.connect(self.checkout_remote_branch)
        remote_actions_layout.addWidget(self.checkout_remote_btn)
        
        self.pull_btn = QPushButton("Pull from Remote")
        self.pull_btn.clicked.connect(self.pull_from_remote)
        remote_actions_layout.addWidget(self.pull_btn)
        
        self.push_btn = QPushButton("Push to Remote")
        self.push_btn.clicked.connect(self.push_to_remote)
        remote_actions_layout.addWidget(self.push_btn)
        
        actions_layout.addWidget(remote_actions)
        
        main_layout.addLayout(actions_layout)
        
        # Botões de ação
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_branches)
        button_box.addButton(refresh_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def refresh_branches(self):
        """Atualiza a lista de branches locais e remotas"""
        if not self.git_manager:
            return
            
        self.logger.log("Fetching branches...")
        
        # Iniciar thread para obter branches
        worker = WorkerThread(self.git_manager.get_branches)
        worker.finished.connect(self._on_branches_fetched)
        worker.log.connect(self.logger.log)
        worker.start()
        
        # Também atualizar status do Git
        status_worker = WorkerThread(self.git_manager.get_status)
        status_worker.finished.connect(self._on_status_fetched)
        status_worker.log.connect(self.logger.log)
        status_worker.start()
    
    @pyqtSlot(bool, object)
    def _on_branches_fetched(self, success, result):
        """Callback quando branches são obtidas"""
        if success and isinstance(result, tuple) and len(result) == 2:
            # Descompactar resultado
            self.local_branches, self.remote_branches = result
            
            # Atualizar listbox de branches locais
            self.local_list.clear()
            self.local_list.addItems(self.local_branches)
            
            # Atualizar listbox de branches remotas
            self.remote_list.clear()
            self.remote_list.addItems(self.remote_branches)
            
            # Destacar branch atual se conhecida
            if self.current_branch and self.current_branch in self.local_branches:
                # Encontrar e selecionar o item
                items = self.local_list.findItems(self.current_branch, Qt.MatchFlag.MatchExactly)
                if items:
                    self.local_list.setCurrentItem(items[0])
    
    @pyqtSlot(bool, object)
    def _on_status_fetched(self, success, result):
        """Callback quando status é obtido"""
        if success and isinstance(result, dict) and result.get("valid", False):
            # Atualizar informações da branch atual
            if "branch" in result:
                self.current_branch = result["branch"]
                self.current_branch_label.setText(self.current_branch)
                self.current_status_label.setText(result.get("status", "Unknown"))
    
    def on_local_branch_select(self):
        """Manipula a seleção de uma branch local"""
        # Limpar seleção na lista de branches remotas
        self.remote_list.clearSelection()
    
    def on_remote_branch_select(self):
        """Manipula a seleção de uma branch remota"""
        # Limpar seleção na lista de branches locais
        self.local_list.clearSelection()
    
    def get_selected_local_branch(self):
        """Obtém a branch local selecionada"""
        items = self.local_list.selectedItems()
        if not items:
            QMessageBox.information(self, "Info", "No local branch selected")
            return None
        
        return items[0].text()
    
    def get_selected_remote_branch(self):
        """Obtém a branch remota selecionada"""
        items = self.remote_list.selectedItems()
        if not items:
            QMessageBox.information(self, "Info", "No remote branch selected")
            return None
        
        return items[0].text()
    
    def checkout_selected_branch(self):
        """Faz checkout da branch local selecionada"""
        branch_name = self.get_selected_local_branch()
        if not branch_name:
            return
        
        # Verificar se é a branch atual
        if branch_name == self.current_branch:
            QMessageBox.information(self, "Info", f"Already on branch '{branch_name}'")
            return
        
        # Fazer checkout
        self.logger.log(f"Checking out branch '{branch_name}'...")
        
        try:
            worker = WorkerThread(self.git_manager.repo.git.checkout, branch_name)
            worker.finished.connect(lambda success, result: self._on_checkout_completed(success, result, branch_name))
            worker.log.connect(self.logger.log)
            worker.start()
        except Exception as e:
            self.logger.log(f"Error checking out branch: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Error checking out branch: {str(e)}")
    
    @pyqtSlot(bool, object, str)
    def _on_checkout_completed(self, success, result, branch_name):
        """Callback quando checkout é concluído"""
        if success:
            self.logger.log(f"Switched to branch '{branch_name}'", "SUCCESS")
            self.refresh_branches()
        else:
            error_message = str(result) if result else "Unknown error"
            self.logger.log(f"Error checking out branch: {error_message}", "ERROR")
            QMessageBox.critical(self, "Error", f"Error checking out branch: {error_message}")
    
    def create_new_branch(self):
        """Cria uma nova branch"""
        # Abrir diálogo para entrada de nome
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Branch")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Form para nome da branch
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        name_edit = QLineEdit()
        form_layout.addRow("New Branch Name:", name_edit)
        
        checkout_check = QCheckBox("Checkout new branch after creation")
        checkout_check.setChecked(True)
        form_layout.addRow("", checkout_check)
        
        layout.addLayout(form_layout)
        
        # Botões de ação
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Exibir diálogo e processar resultado
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            checkout = checkout_check.isChecked()
            
            # Validar nome
            if not name:
                QMessageBox.critical(self, "Error", "Branch name cannot be empty")
                return
            
            # Validar formato
            if not re.match(r'^[a-zA-Z0-9_\-./]+$', name):
                QMessageBox.critical(self, "Error", "Invalid branch name. Use only letters, numbers, underscores, hyphens, dots, and slashes.")
                return
            
            # Verificar se já existe
            if name in self.local_branches:
                QMessageBox.critical(self, "Error", f"Branch '{name}' already exists")
                return
            
            # Criar branch
            self.logger.log(f"Creating branch '{name}'...")
            
            worker = WorkerThread(self.git_manager.create_branch, name, checkout)
            worker.finished.connect(lambda success, result: self._on_branch_created(success, result, name))
            worker.log.connect(self.logger.log)
            worker.start()
    
    @pyqtSlot(bool, object, str)
    def _on_branch_created(self, success, result, branch_name):
        """Callback quando branch é criada"""
        if success:
            self.logger.log(f"Branch '{branch_name}' created successfully", "SUCCESS")
            self.refresh_branches()
        else:
            error_message = result[1] if isinstance(result, tuple) and len(result) > 1 else str(result)
            self.logger.log(f"Error creating branch: {error_message}", "ERROR")
            QMessageBox.critical(self, "Error", f"Error creating branch: {error_message}")
    
    def delete_selected_branch(self):
        """Remove a branch local selecionada"""
        branch_name = self.get_selected_local_branch()
        if not branch_name:
            return
        
        # Verificar se é a branch atual
        if branch_name == self.current_branch:
            QMessageBox.critical(self, "Error", "Cannot delete the currently checked out branch")
            return
        
        # Confirmar exclusão
        if QMessageBox.question(
            self, "Confirm Delete", f"Delete branch '{branch_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        
        # Deletar branch
        self.logger.log(f"Deleting branch '{branch_name}'...")
        
        try:
            worker = WorkerThread(self.git_manager.repo.git.branch, "-d", branch_name)
            worker.finished.connect(lambda success, result: self._on_branch_deleted(success, result, branch_name))
            worker.log.connect(self.logger.log)
            worker.start()
        except Exception as e:
            self.logger.log(f"Error deleting branch: {str(e)}", "ERROR")
            self._handle_delete_error(branch_name, str(e))
    
    @pyqtSlot(bool, object, str)
    def _on_branch_deleted(self, success, result, branch_name):
        """Callback quando branch é deletada"""
        if success:
            self.logger.log(f"Branch '{branch_name}' deleted", "SUCCESS")
            self.refresh_branches()
        else:
            error_message = str(result) if result else "Unknown error"
            self.logger.log(f"Error deleting branch: {error_message}", "ERROR")
            self._handle_delete_error(branch_name, error_message)
    
    def _handle_delete_error(self, branch_name, error_message):
        """Trata erros na exclusão de branch"""
        # Verificar se é erro de branch não mesclada
        if "not fully merged" in error_message:
            # Perguntar se deseja forçar exclusão
            if QMessageBox.question(
                self, "Force Delete", 
                f"Branch '{branch_name}' is not fully merged. Force delete?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
                try:
                    worker = WorkerThread(self.git_manager.repo.git.branch, "-D", branch_name)
                    worker.finished.connect(lambda success, result: self._on_force_delete_completed(success, result, branch_name))
                    worker.log.connect(self.logger.log)
                    worker.start()
                except Exception as e:
                    self.logger.log(f"Error force deleting branch: {str(e)}", "ERROR")
                    QMessageBox.critical(self, "Error", f"Error force deleting branch: {str(e)}")
        else:
            QMessageBox.critical(self, "Error", f"Error deleting branch: {error_message}")
    
    @pyqtSlot(bool, object, str)
    def _on_force_delete_completed(self, success, result, branch_name):
        """Callback quando force delete é concluído"""
        if success:
            self.logger.log(f"Branch '{branch_name}' force deleted", "SUCCESS")
            self.refresh_branches()
        else:
            error_message = str(result) if result else "Unknown error"
            self.logger.log(f"Error force deleting branch: {error_message}", "ERROR")
            QMessageBox.critical(self, "Error", f"Error force deleting branch: {error_message}")
    
    def checkout_remote_branch(self):
        """Faz checkout de uma branch remota"""
        remote_branch = self.get_selected_remote_branch()
        if not remote_branch:
            return
        
        # Remover prefixo 'origin/'
        if '/' in remote_branch:
            remote_name, branch_name = remote_branch.split('/', 1)
        else:
            branch_name = remote_branch
        
        # Verificar se já existe localmente
        if branch_name in self.local_branches:
            # Perguntar se deseja fazer checkout da versão local
            if QMessageBox.question(
                self, "Local Branch Exists", 
                f"A local branch '{branch_name}' already exists. Checkout the local branch?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
                self.checkout_local_branch(branch_name)
            return
        
        # Criar branch de rastreamento
        self.logger.log(f"Creating tracking branch for '{remote_branch}'...")
        
        try:
            worker = WorkerThread(self.git_manager.repo.git.checkout, '-b', branch_name, remote_branch)
            worker.finished.connect(lambda success, result: self._on_remote_checkout_completed(success, result, branch_name, remote_branch))
            worker.log.connect(self.logger.log)
            worker.start()
        except Exception as e:
            self.logger.log(f"Error checking out remote branch: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Error checking out remote branch: {str(e)}")
    
    def checkout_local_branch(self, branch_name):
        """Faz checkout de uma branch local"""
        try:
            worker = WorkerThread(self.git_manager.repo.git.checkout, branch_name)
            worker.finished.connect(lambda success, result: self._on_checkout_completed(success, result, branch_name))
            worker.log.connect(self.logger.log)
            worker.start()
        except Exception as e:
            self.logger.log(f"Error checking out branch: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Error checking out branch: {str(e)}")
    
    @pyqtSlot(bool, object, str, str)
    def _on_remote_checkout_completed(self, success, result, branch_name, remote_branch):
        """Callback quando checkout de remote é concluído"""
        if success:
            self.logger.log(f"Switched to new branch '{branch_name}' tracking '{remote_branch}'", "SUCCESS")
            self.refresh_branches()
        else:
            error_message = str(result) if result else "Unknown error"
            self.logger.log(f"Error checking out remote branch: {error_message}", "ERROR")
            QMessageBox.critical(self, "Error", f"Error checking out remote branch: {error_message}")
    
    def pull_from_remote(self):
        """Puxa alterações da branch remota para a branch atual"""
        # Verificar se há uma branch atual
        if not self.current_branch:
            QMessageBox.critical(self, "Error", "No active branch")
            return
        
        self.logger.log(f"Pulling changes from remote for branch '{self.current_branch}'...")
        
        try:
            worker = WorkerThread(self.git_manager.repo.git.pull)
            worker.finished.connect(self._on_pull_completed)
            worker.log.connect(self.logger.log)
            worker.start()
        except Exception as e:
            self.logger.log(f"Error pulling from remote: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Error pulling from remote: {str(e)}")
    
    @pyqtSlot(bool, object)
    def _on_pull_completed(self, success, result):
        """Callback quando pull é concluído"""
        if success:
            self.logger.log("Pull completed successfully", "SUCCESS")
            self.refresh_branches()
        else:
            error_message = str(result) if result else "Unknown error"
            self.logger.log(f"Error pulling from remote: {error_message}", "ERROR")
            QMessageBox.critical(self, "Error", f"Error pulling from remote: {error_message}")
    
    def push_to_remote(self):
        """Envia alterações da branch atual para a branch remota"""
        # Verificar se há uma branch atual
        if not self.current_branch:
            QMessageBox.critical(self, "Error", "No active branch")
            return
        
        # Verificar se a branch remota existe
        remote_branch = f"origin/{self.current_branch}"
        
        if remote_branch in self.remote_branches:
            # Branch remota existe - push normal
            self.logger.log(f"Pushing changes to remote for branch '{self.current_branch}'...")
            
            try:
                worker = WorkerThread(self.git_manager.repo.git.push)
                worker.finished.connect(self._on_push_completed)
                worker.log.connect(self.logger.log)
                worker.start()
            except Exception as e:
                self.logger.log(f"Error pushing to remote: {str(e)}", "ERROR")
                QMessageBox.critical(self, "Error", f"Error pushing to remote: {str(e)}")
        else:
            # Branch remota não existe - definir upstream
            self.logger.log(f"Setting up remote branch for '{self.current_branch}'...")
            
            try:
                worker = WorkerThread(self.git_manager.repo.git.push, '--set-upstream', 'origin', self.current_branch)
                worker.finished.connect(self._on_push_completed)
                worker.log.connect(self.logger.log)
                worker.start()
            except Exception as e:
                self.logger.log(f"Error pushing to remote: {str(e)}", "ERROR")
                QMessageBox.critical(self, "Error", f"Error pushing to remote: {str(e)}")
    
    @pyqtSlot(bool, object)
    def _on_push_completed(self, success, result):
        """Callback quando push é concluído"""
        if success:
            self.logger.log("Push completed successfully", "SUCCESS")
            self.refresh_branches()
        else:
            error_message = str(result) if result else "Unknown error"
            self.logger.log(f"Error pushing to remote: {error_message}", "ERROR")
            QMessageBox.critical(self, "Error", f"Error pushing to remote: {error_message}")