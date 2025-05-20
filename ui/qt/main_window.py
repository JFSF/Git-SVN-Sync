def cleanup_threads(self):
        """Remove threads finalizadas da lista de threads ativas"""
        self.active_threads = [t for t in self.active_threads if t.isRunning()]#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from threading import Thread
from datetime import datetime

from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QToolBar, QStatusBar, QFileDialog,
                             QTreeWidget, QTreeWidgetItem, QTextEdit, QSplitter, QMessageBox,
                             QTabWidget, QMenu, QMenuBar, QComboBox, QHeaderView, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, QThread
from PyQt6.QtGui import QIcon, QAction, QFont, QColor, QTextCharFormat

from utils.logger import LogManager
from core.git_manager import GitManager
from core.svn_manager import SVNManager
from core.sync_manager import SyncManager
from ui.qt.commit_dialog import CommitDialog
from ui.qt.settings_dialog import SettingsDialog
from ui.qt.diff_viewer import DiffViewer
from ui.qt.branch_manager import BranchManagerDialog
from ui.qt.conflict_resolver import ConflictResolver
from ui.qt.commit_template_dialog import CommitTemplateDialog
from ui.qt.task_integration_dialog import TaskIntegrationDialog
from features.commit_templates import CommitTemplateManager
from features.task_integration import TaskIntegrationManager
from features.auto_sync import AutoSyncManager
from ui.qt.resources import get_icon, setup_application_style


class WorkerThread(QThread):
    """Thread worker para operações de longa duração"""
    finished = pyqtSignal(bool, object)
    log = pyqtSignal(str, str)
    
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.running = True
    
    def run(self):
        try:
            if callable(self.function) and self.running:
                result = self.function(*self.args, **self.kwargs)
                if self.running:
                    self.finished.emit(True, result)
        except Exception as e:
            if self.running:
                self.log.emit(f"Error in worker thread: {str(e)}", "ERROR")
                self.finished.emit(False, str(e))
    
    def stop(self):
        """Para a execução da thread"""
        self.running = False


class MainWindow(QMainWindow):
    """Janela principal da aplicação usando Qt6"""
    
    def __init__(self, config_manager):
        super().__init__()
        
        self.config = config_manager
        
        # Configurar variáveis
        self.git_repo_url = self.config.get('git_repo_url', '')
        self.svn_repo_url = self.config.get('svn_repo_url', '')
        self.local_working_copy = self.config.get('local_working_copy', '')
        
        # Rastrear threads ativas
        self.active_threads = []
        
        # Configurar janela principal
        self.setWindowTitle("Git-SVN Sync Tool")
        self.setMinimumSize(900, 650)
        
        # Inicializar o logger e outros gerenciadores
        self.setup_managers()
        
        # Criar a interface
        self.create_ui()
        
        # Atualizar estado inicial
        self.update_status()
    
    def setup_managers(self):
        """Inicializa todos os gerenciadores e serviços"""
        # Criar widget de log primeiro (para poder inicializar o logger)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        # Inicializar o logger
        log_file = self.config.get("logging.log_file_path", "") 
        if self.config.get("logging.enable_file_logging", False) and log_file:
            self.logger = LogManager(self.log_text, log_file)
        else:
            self.logger = LogManager(self.log_text)
        
        # Gerenciadores de repositório
        if self.local_working_copy:
            self.git_manager = GitManager(self.local_working_copy, self.logger)
            self.svn_manager = SVNManager(self.local_working_copy, self.logger)
            
            # Gerenciador de sincronização
            self.sync_manager = SyncManager(
                self.git_manager, 
                self.svn_manager, 
                self.logger, 
                self.config
            )
        else:
            self.git_manager = None
            self.svn_manager = None
            self.sync_manager = None
        
        # Gerenciador de templates de commit
        self.template_manager = CommitTemplateManager(self.config)
        
        # Gerenciador de integração com sistemas de tarefas
        self.task_manager = TaskIntegrationManager(self.config, self.logger)
        
        # Gerenciador de sincronização automática
        if self.git_manager and self.svn_manager:
            self.auto_sync_manager = AutoSyncManager(self.sync_manager, self.config, self.logger)
            if self.config.get("auto_sync.enabled", False):
                self.auto_sync_manager.start()
        else:
            self.auto_sync_manager = None
    
    def create_ui(self):
        """Cria a interface da janela principal"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Painel de status do repositório
        self.create_status_panel(main_layout)
        
        # Criar barra de ferramentas
        self.create_toolbar(main_layout)
        
        # Splitter para painéis de arquivos e log
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(content_splitter)
        
        # Painel de arquivos
        files_panel = self.create_files_panel()
        content_splitter.addWidget(files_panel)
        
        # Painel de log
        log_panel = self.create_log_panel()
        content_splitter.addWidget(log_panel)
        
        # Definir tamanhos iniciais dos painéis (proporções)
        content_splitter.setSizes([500, 400])
        
        # Criar menu principal
        self.create_menu()
        
        # Criar barra de status
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
    
    def create_status_panel(self, main_layout):
        """Cria o painel de status do repositório"""
        status_group = QGroupBox("Repository Status")
        status_layout = QVBoxLayout(status_group)
        
        # Layout em grade para informações de status
        form_layout = QHBoxLayout()
        
        # Coluna esquerda: Git e SVN
        left_col = QVBoxLayout()
        
        # Git Status
        git_layout = QHBoxLayout()
        git_layout.addWidget(QLabel("Git Repository:"))
        self.git_status_label = QLabel("Not initialized")
        git_layout.addWidget(self.git_status_label)
        git_layout.addStretch()
        left_col.addLayout(git_layout)
        
        # SVN Status
        svn_layout = QHBoxLayout()
        svn_layout.addWidget(QLabel("SVN Repository:"))
        self.svn_status_label = QLabel("Not initialized")
        svn_layout.addWidget(self.svn_status_label)
        svn_layout.addStretch()
        left_col.addLayout(svn_layout)
        
        form_layout.addLayout(left_col)
        
        # Coluna direita: Working Copy e Auto-Sync
        right_col = QVBoxLayout()
        
        # Working copy
        wc_layout = QHBoxLayout()
        wc_layout.addWidget(QLabel("Working Copy:"))
        self.working_copy_label = QLabel("Not set")
        wc_layout.addWidget(self.working_copy_label)
        wc_layout.addStretch()
        right_col.addLayout(wc_layout)
        
        # Auto-sync status
        sync_layout = QHBoxLayout()
        sync_layout.addWidget(QLabel("Auto-Sync:"))
        self.auto_sync_label = QLabel("Disabled")
        sync_layout.addWidget(self.auto_sync_label)
        sync_layout.addStretch()
        right_col.addLayout(sync_layout)
        
        form_layout.addLayout(right_col)
        
        status_layout.addLayout(form_layout)
        
        # Adicionar painel de status ao layout principal
        main_layout.addWidget(status_group)
    
    def create_toolbar(self, main_layout):
        """Cria a barra de ferramentas principal"""
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Botão de atualizar status
        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.setIcon(get_icon("refresh"))
        refresh_btn.clicked.connect(self.update_status)
        toolbar_layout.addWidget(refresh_btn)
        
        # Botão de commit
        commit_btn = QPushButton("Commit Changes")
        commit_btn.setIcon(get_icon("commit"))
        commit_btn.clicked.connect(self.open_commit_dialog)
        toolbar_layout.addWidget(commit_btn)
        
        # Botão de sincronização
        sync_btn = QPushButton("Sync Repos")
        sync_btn.setIcon(get_icon("sync"))
        sync_btn.clicked.connect(self.start_sync_repos)
        toolbar_layout.addWidget(sync_btn)
        
        # Botão para visualizar diferenças
        diff_btn = QPushButton("View Diff")
        diff_btn.setIcon(get_icon("diff"))
        diff_btn.clicked.connect(self.show_diff_for_selected)
        toolbar_layout.addWidget(diff_btn)
        
        # Separador
        toolbar_layout.addSpacing(20)
        
        # Seletor de branch
        toolbar_layout.addWidget(QLabel("Branch:"))
        self.branch_combo = QComboBox()
        self.branch_combo.setMinimumWidth(150)
        self.branch_combo.currentIndexChanged.connect(self.on_branch_selected)
        toolbar_layout.addWidget(self.branch_combo)
        
        # Espaço flexível no final
        toolbar_layout.addStretch()
        
        # Adicionar barra de ferramentas ao layout principal
        main_layout.addWidget(toolbar_widget)
    
    def create_files_panel(self):
        """Cria o painel de arquivos modificados"""
        files_group = QGroupBox("Modified Files")
        files_layout = QVBoxLayout(files_group)
        
        # Barra de ferramentas dos arquivos
        files_toolbar = QHBoxLayout()
        
        refresh_files_btn = QPushButton("Refresh")
        refresh_files_btn.clicked.connect(self.refresh_files_list)
        files_toolbar.addWidget(refresh_files_btn)
        
        commit_selected_btn = QPushButton("Commit Selected")
        commit_selected_btn.clicked.connect(lambda: self.open_commit_dialog(self.get_selected_files()))
        files_toolbar.addWidget(commit_selected_btn)
        
        files_toolbar.addStretch()
        
        files_layout.addLayout(files_toolbar)
        
        # TreeWidget para arquivos
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderLabels(["Status", "File Path"])
        self.files_tree.setColumnWidth(0, 100)
        self.files_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.files_tree.setAlternatingRowColors(True)
        self.files_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.files_tree.itemDoubleClicked.connect(lambda item, column: self.show_diff_for_selected())
        
        files_layout.addWidget(self.files_tree)
        
        return files_group
    
    def create_log_panel(self):
        """Cria o painel de log"""
        log_group = QGroupBox("Log Messages")
        log_layout = QVBoxLayout(log_group)
        
        # Barra de ferramentas do log
        log_toolbar = QHBoxLayout()
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        log_toolbar.addWidget(clear_log_btn)
        
        log_toolbar.addStretch()
        
        log_layout.addLayout(log_toolbar)
        
        # Widget de log já foi criado em setup_managers
        log_layout.addWidget(self.log_text)
        
        return log_group
    
    def create_menu(self):
        """Cria o menu principal da aplicação"""
        # Menu File
        file_menu = QMenu("File", self)
        
        settings_action = QAction(get_icon("settings"), "Settings", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Git
        git_menu = QMenu("Git", self)
        
        init_git_action = QAction("Initialize Repository", self)
        init_git_action.triggered.connect(self.init_git_repo)
        git_menu.addAction(init_git_action)
        
        commit_action = QAction(get_icon("commit"), "Commit Changes", self)
        commit_action.triggered.connect(self.open_commit_dialog)
        git_menu.addAction(commit_action)
        
        sync_git_action = QAction("Sync with Remote", self)
        sync_git_action.triggered.connect(self.sync_git_repo)
        git_menu.addAction(sync_git_action)
        
        git_menu.addSeparator()
        
        branch_manager_action = QAction("Branch Manager", self)
        branch_manager_action.triggered.connect(self.open_branch_manager)
        git_menu.addAction(branch_manager_action)
        
        # Menu SVN
        svn_menu = QMenu("SVN", self)
        
        update_svn_action = QAction("Update from Repository", self)
        update_svn_action.triggered.connect(self.update_svn)
        svn_menu.addAction(update_svn_action)
        
        commit_svn_action = QAction("Commit Changes", self)
        commit_svn_action.triggered.connect(self.open_svn_commit)
        svn_menu.addAction(commit_svn_action)
        
        # Menu Tools
        tools_menu = QMenu("Tools", self)
        
        templates_action = QAction("Commit Templates", self)
        templates_action.triggered.connect(self.open_commit_templates)
        tools_menu.addAction(templates_action)
        
        tasks_action = QAction("Task Integration", self)
        tasks_action.triggered.connect(self.open_task_integration)
        tools_menu.addAction(tasks_action)
        
        auto_sync_action = QAction("Auto-Sync Settings", self)
        auto_sync_action.triggered.connect(self.open_auto_sync)
        tools_menu.addAction(auto_sync_action)
        
        tools_menu.addSeparator()
        
        sync_both_action = QAction("Synchronize Both Repositories", self)
        sync_both_action.triggered.connect(self.start_sync_repos)
        tools_menu.addAction(sync_both_action)
        
        # Menu Help
        help_menu = QMenu("Help", self)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Adicionar menus à barra de menus
        menu_bar = self.menuBar()
        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(git_menu)
        menu_bar.addMenu(svn_menu)
        menu_bar.addMenu(tools_menu)
        menu_bar.addMenu(help_menu)
    
    def update_status(self):
        """Atualiza o status dos repositórios"""
        self.statusBar.showMessage("Updating status...")
        
        # Limpar threads antigas que já terminaram
        self.active_threads = [t for t in self.active_threads if t.isRunning()]
        
        # Usar worker thread para não bloquear a interface
        self.status_worker = WorkerThread(self._update_status_worker)
        self.status_worker.finished.connect(self._on_status_updated)
        self.status_worker.log.connect(self.logger.log)
        self.active_threads.append(self.status_worker)
        self.status_worker.start()
    
    def _update_status_worker(self):
        """Worker para atualizar status (executado em thread separada)"""
        result = {
            "git_status": None,
            "svn_status": None,
            "local_status": None,
            "auto_sync_status": None,
            "branches": []
        }
        
        # Verificar diretório local
        if not self.local_working_copy:
            result["local_status"] = "Not set"
            return result
        
        if os.path.exists(self.local_working_copy):
            result["local_status"] = f"Exists: {self.local_working_copy}"
        else:
            result["local_status"] = f"Not found: {self.local_working_copy}"
            return result
        
        # Status Git
        if not self.git_manager:
            self.git_manager = GitManager(self.local_working_copy, self.logger)
        
        git_status = self.git_manager.get_status()
        if git_status["valid"]:
            result["git_status"] = git_status["message"]
            
            # Obter branches
            if "branch" in git_status:
                local_branches, remote_branches = self.git_manager.get_branches()
                result["branches"] = local_branches
                result["current_branch"] = git_status.get("branch")
        else:
            result["git_status"] = git_status["message"]
        
        # Status SVN
        if not self.svn_manager:
            self.svn_manager = SVNManager(self.local_working_copy, self.logger)
        
        svn_status = self.svn_manager.get_status()
        if svn_status["valid"]:
            result["svn_status"] = svn_status["message"]
        else:
            result["svn_status"] = svn_status["message"]
        
        # Status Auto-Sync
        if self.auto_sync_manager:
            result["auto_sync_status"] = "Enabled" if self.auto_sync_manager.enabled else "Disabled"
            if self.auto_sync_manager.enabled and self.auto_sync_manager.next_sync_time:
                time_left = self.auto_sync_manager.next_sync_time - datetime.now()
                if time_left.total_seconds() > 0:
                    minutes, seconds = divmod(int(time_left.total_seconds()), 60)
                    result["auto_sync_status"] += f" (Next sync in {minutes:02d}:{seconds:02d})"
        else:
            result["auto_sync_status"] = "Not available"
        
        return result
    
    def _on_status_updated(self, success, result):
        """Callback quando o status for atualizado"""
        if not success or not isinstance(result, dict):
            self.statusBar.showMessage("Failed to update status")
            return
        
        # Atualizar labels de status
        if "git_status" in result:
            self.git_status_label.setText(result["git_status"])
        
        if "svn_status" in result:
            self.svn_status_label.setText(result["svn_status"])
        
        if "local_status" in result:
            self.working_copy_label.setText(result["local_status"])
        
        if "auto_sync_status" in result:
            self.auto_sync_label.setText(result["auto_sync_status"])
        
        # Atualizar combo de branches
        if "branches" in result and result["branches"]:
            current_branch = result.get("current_branch")
            
            # Bloquear sinais para evitar triggers durante a atualização
            self.branch_combo.blockSignals(True)
            
            self.branch_combo.clear()
            self.branch_combo.addItems(result["branches"])
            
            # Selecionar branch atual
            if current_branch and current_branch in result["branches"]:
                index = result["branches"].index(current_branch)
                self.branch_combo.setCurrentIndex(index)
            
            self.branch_combo.blockSignals(False)
        
        # Atualizar lista de arquivos
        self.refresh_files_list()
        
        self.statusBar.showMessage("Status updated", 3000)
    
    def refresh_files_list(self):
        """Atualiza a lista de arquivos modificados"""
        self.statusBar.showMessage("Refreshing file list...")
        
        # Limpar árvore
        self.files_tree.clear()
        
        if not self.git_manager:
            self.statusBar.showMessage("Git manager not initialized", 3000)
            return
        
        # Obter arquivos modificados
        modified_files = self.git_manager.get_modified_files()
        
        # Status types com cores
        status_colors = {
            "M": QColor(0, 0, 255),      # Azul para modificados
            "A": QColor(0, 128, 0),      # Verde para adicionados
            "D": QColor(255, 0, 0),      # Vermelho para deletados
            "R": QColor(128, 0, 128),    # Roxo para renomeados
            "?": QColor(128, 128, 128),  # Cinza para não rastreados
            "C": QColor(255, 128, 0)     # Laranja para conflitos
        }
        
        status_labels = {
            "M": "Modified",
            "A": "Added",
            "D": "Deleted",
            "R": "Renamed",
            "?": "Untracked",
            "C": "Conflict"
        }
        
        # Adicionar arquivos à árvore
        for file_info in modified_files:
            file_path = file_info["path"]
            
            # Determinar tipo de status
            status_type = file_info["type"]
            status = status_labels.get(status_type, status_type)
            
            # Criar item
            item = QTreeWidgetItem([status, file_path])
            
            # Definir cor com base no status
            if status_type in status_colors:
                item.setForeground(0, status_colors[status_type])
            
            # Adicionar à treeview
            self.files_tree.addTopLevelItem(item)
        
        # Log
        self.logger.log(f"Found {len(modified_files)} modified files")
        self.statusBar.showMessage(f"Found {len(modified_files)} modified files", 3000)
    
    def get_selected_files(self):
        """Obtém arquivos selecionados no TreeWidget"""
        selected_items = self.files_tree.selectedItems()
        return [item.text(1) for item in selected_items]
    
    def show_diff_for_selected(self):
        """Mostra diferenças para os arquivos selecionados"""
        selected_files = self.get_selected_files()
        
        if not selected_files:
            QMessageBox.information(self, "Info", "No files selected")
            return
        
        if not self.git_manager:
            QMessageBox.critical(self, "Error", "Git repository not initialized")
            return
        
        # Mostrar diff para cada arquivo selecionado (limite a 5 por vez)
        for file_path in selected_files[:5]:
            diff_data = self.git_manager.get_diff(file_path)
            
            if diff_data:
                # Usar o estilo de visualização configurado
                diff_style = self.config.get("ui.diff_view_style", "side-by-side")
                diff_viewer = DiffViewer(self, f"Diff: {file_path}", file_path, diff_data, diff_style)
                diff_viewer.show()
            else:
                QMessageBox.critical(self, "Error", f"Could not get diff for {file_path}")
    
    def open_commit_dialog(self, selected_files=None):
        """Abre diálogo para commit"""
        if not self.git_manager:
            QMessageBox.critical(self, "Error", "Git repository not initialized")
            return
        
        # Obter arquivos modificados
        all_modified_files = self.git_manager.get_modified_files()
        if not all_modified_files:
            QMessageBox.information(self, "Info", "No modified files to commit")
            return
        
        # Se arquivos foram pré-selecionados, usar apenas esses
        if selected_files:
            files_to_show = [f for f in all_modified_files if f["path"] in selected_files]
        else:
            files_to_show = all_modified_files
        
        # Obter templates de commit
        commit_templates = self.template_manager.get_templates()
        
        # Criar e mostrar diálogo
        commit_dialog = CommitDialog(self, files_to_show, commit_templates)
        
        # Executar o diálogo
        if commit_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_files = commit_dialog.selected_files
            commit_message = commit_dialog.commit_message
            
            # Verificar se há uma tarefa relacionada
            task_id = None
            if self.task_manager and self.task_manager.extract_from_branch:
                # Extrair do nome da branch atual
                git_status = self.git_manager.get_status()
                if git_status["valid"] and "branch" in git_status:
                    branch_name = git_status["branch"]
                    task_id = self.task_manager.extract_task_id(branch_name=branch_name)
                
                # Se não encontrou na branch, tentar extrair da mensagem de commit
                if not task_id:
                    task_id = self.task_manager.extract_task_id(commit_message=commit_message)
            
            # Fazer commit
            self.statusBar.showMessage("Committing changes...")
            success, result = self.git_manager.commit(selected_files, commit_message)
            
            if success:
                QMessageBox.information(self, "Success", f"Successfully committed {len(selected_files)} files")
                self.statusBar.showMessage(f"Committed {len(selected_files)} files", 3000)
                
                # Atualizar status de tarefa se configurado
                if task_id and self.task_manager and self.task_manager.auto_update_task:
                    self.logger.log(f"Auto-updating task {task_id}")
                    success, msg = self.task_manager.update_task_status(task_id, "In Progress")
                    if success:
                        self.logger.log(f"Task {task_id} updated to 'In Progress'", "SUCCESS")
                    else:
                        self.logger.log(f"Failed to update task: {msg}", "WARNING")
                
                # Atualizar interface
                self.update_status()
            else:
                QMessageBox.critical(self, "Error", f"Error committing files: {result}")
                self.statusBar.showMessage("Commit failed", 3000)
    
    def init_git_repo(self):
        """Inicializa o repositório Git"""
        if not self.local_working_copy:
            QMessageBox.critical(self, "Error", "Local working copy not set")
            self.open_settings()
            return
        
        if not self.git_manager:
            self.git_manager = GitManager(self.local_working_copy, self.logger)
        
        # Confirmar inicialização
        reply = QMessageBox.question(
            self, "Initialize Repository", 
            f"Initialize Git repository in {self.local_working_copy}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Limpar threads antigas que já terminaram
        self.active_threads = [t for t in self.active_threads if t.isRunning()]
        
        # Usar worker thread para operação de longa duração
        self.statusBar.showMessage("Initializing Git repository...")
        worker = WorkerThread(self.git_manager.init_repo, self.git_repo_url)
        worker.finished.connect(self._on_git_init_complete)
        worker.log.connect(self.logger.log)
        self.active_threads.append(worker)
        worker.start()
    
    def _on_git_init_complete(self, success, result):
        """Callback quando a inicialização do Git for concluída"""
        if success:
            QMessageBox.information(self, "Success", "Git repository initialized successfully")
            self.statusBar.showMessage("Git repository initialized", 3000)
        else:
            QMessageBox.critical(self, "Error", "Failed to initialize Git repository")
            self.statusBar.showMessage("Git initialization failed", 3000)
        
        self.update_status()
    
    def sync_git_repo(self):
        """Sincroniza com o repositório Git remoto"""
        if not self.git_manager:
            QMessageBox.critical(self, "Error", "Git repository not initialized")
            return
        
        # Limpar threads antigas que já terminaram
        self.active_threads = [t for t in self.active_threads if t.isRunning()]
        
        # Usar worker thread para operação de longa duração
        self.statusBar.showMessage("Syncing with Git remote...")
        worker = WorkerThread(self.git_manager.sync_with_remote)
        worker.finished.connect(self._on_git_sync_complete)
        worker.log.connect(self.logger.log)
        self.active_threads.append(worker)
        worker.start()
    
    def _on_git_sync_complete(self, success, result):
        """Callback quando a sincronização Git for concluída"""
        if success:
            QMessageBox.information(self, "Success", "Git synchronization completed successfully")
            self.statusBar.showMessage("Git sync completed", 3000)
        else:
            QMessageBox.critical(self, "Error", f"Git synchronization failed: {result[1] if isinstance(result, tuple) else result}")
            self.statusBar.showMessage("Git sync failed", 3000)
        
        self.update_status()
    
    def update_svn(self):
        """Atualiza a partir do repositório SVN"""
        if not self.svn_manager:
            QMessageBox.critical(self, "Error", "SVN repository not initialized")
            return
        
        # Limpar threads antigas que já terminaram
        self.active_threads = [t for t in self.active_threads if t.isRunning()]
        
        # Usar worker thread para operação de longa duração
        self.statusBar.showMessage("Updating from SVN...")
        worker = WorkerThread(self.svn_manager.update)
        worker.finished.connect(self._on_svn_update_complete)
        worker.log.connect(self.logger.log)
        self.active_threads.append(worker)
        worker.start()
    
    def _on_svn_update_complete(self, success, result):
        """Callback quando a atualização SVN for concluída"""
        if success:
            QMessageBox.information(self, "Success", "SVN update completed successfully")
            self.statusBar.showMessage("SVN update completed", 3000)
        else:
            QMessageBox.critical(self, "Error", f"SVN update failed: {result[1] if isinstance(result, tuple) else result}")
            self.statusBar.showMessage("SVN update failed", 3000)
        
        self.update_status()
    
    def open_svn_commit(self):
        """Abre diálogo para commit SVN"""
        if not self.svn_manager:
            QMessageBox.critical(self, "Error", "SVN repository not initialized")
            return
        
        QMessageBox.information(self, "Not Implemented", "SVN commit dialog not implemented yet")
    
    def start_sync_repos(self):
        """Inicia sincronização de ambos os repositórios"""
        if not self.sync_manager:
            QMessageBox.critical(self, "Error", "Sync manager not initialized")
            return
        
        # Limpar threads antigas que já terminaram
        self.active_threads = [t for t in self.active_threads if t.isRunning()]
        
        # Usar worker thread para operação de longa duração
        self.statusBar.showMessage("Synchronizing repositories...")
        
        # Obter direção de sincronização das configurações
        sync_direction = self.config.get("sync.direction", "bidirectional")
        
        if sync_direction == "git_to_svn":
            worker = WorkerThread(self.sync_manager.sync_git_to_svn)
        elif sync_direction == "svn_to_git":
            worker = WorkerThread(self.sync_manager.sync_svn_to_git)
        else:  # bidirectional
            worker = WorkerThread(self.sync_manager.bidirectional_sync)
        
        worker.finished.connect(self._on_sync_repos_complete)
        worker.log.connect(self.logger.log)
        self.active_threads.append(worker)
        worker.start()
    
    def _on_sync_repos_complete(self, success, result):
        """Callback quando a sincronização de repositórios for concluída"""
        if success:
            QMessageBox.information(self, "Success", "Repository synchronization completed successfully")
            self.statusBar.showMessage("Repositories synchronized", 3000)
        else:
            QMessageBox.critical(self, "Error", f"Repository synchronization failed: {result[1] if isinstance(result, tuple) else result}")
            self.statusBar.showMessage("Repository sync failed", 3000)
        
        self.update_status()
    
    def on_branch_selected(self, index):
        """Manipula a seleção de branch no ComboBox"""
        if index < 0 or not self.git_manager:
            return
        
        branch_name = self.branch_combo.currentText()
        
        # Verificar se é a branch atual
        git_status = self.git_manager.get_status()
        if git_status["valid"] and "branch" in git_status and git_status["branch"] == branch_name:
            return
        
        # Confirmar checkout
        reply = QMessageBox.question(
            self, "Checkout Branch", 
            f"Switch to branch '{branch_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            # Reverter para a branch atual
            self.update_status()
            return
        
        # Limpar threads antigas que já terminaram
        self.active_threads = [t for t in self.active_threads if t.isRunning()]
        
        # Fazer checkout
        self.statusBar.showMessage(f"Checking out branch '{branch_name}'...")
        worker = WorkerThread(self.git_manager.repo.git.checkout, branch_name)
        worker.finished.connect(lambda success, result: self._on_checkout_completed(success, result, branch_name))
        worker.log.connect(self.logger.log)
        self.active_threads.append(worker)
        worker.start()
    
    def _on_checkout_completed(self, success, result, branch_name):
        """Callback quando o checkout de branch for concluído"""
        if success:
            self.logger.log(f"Switched to branch '{branch_name}'", "SUCCESS")
            self.statusBar.showMessage(f"Switched to branch '{branch_name}'", 3000)
        else:
            self.logger.log(f"Error checking out branch: {result}", "ERROR")
            QMessageBox.critical(self, "Error", f"Error checking out branch: {result}")
            self.statusBar.showMessage("Checkout failed", 3000)
        
        self.update_status()
    
    def open_settings(self):
        """Abre o diálogo de configurações"""
        settings = {
            "git_repo_url": self.git_repo_url,
            "svn_repo_url": self.svn_repo_url,
            "local_working_copy": self.local_working_copy
        }
        
        settings_dialog = SettingsDialog(self, settings)
        
        if settings_dialog.exec() == QDialog.DialogCode.Accepted:
            # Atualizar configurações
            self.git_repo_url = settings_dialog.git_url_var.get()
            self.svn_repo_url = settings_dialog.svn_url_var.get()
            self.local_working_copy = settings_dialog.working_copy_var.get()
            
            # Salvar no config manager
            self.config.set("git_repo_url", self.git_repo_url)
            self.config.set("svn_repo_url", self.svn_repo_url)
            self.config.set("local_working_copy", self.local_working_copy)
            
            # Aplicar configurações de tema
            theme = settings_dialog.theme_var.get()
            if theme != self.config.get("ui.theme", "system"):
                self.config.set("ui.theme", theme)
                reply = QMessageBox.question(
                    self, "Theme Changed", 
                    "The theme has been changed. Restart application to apply?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    QApplication.quit()
                    return
            
            # Reinicializar gerenciadores se necessário
            if self.local_working_copy:
                self.git_manager = GitManager(self.local_working_copy, self.logger)
                self.svn_manager = SVNManager(self.local_working_copy, self.logger)
                self.sync_manager = SyncManager(
                    self.git_manager, 
                    self.svn_manager, 
                    self.logger, 
                    self.config
                )
                
                # Verificar se auto-sync estava ativo e reiniciar
                if self.auto_sync_manager:
                    was_enabled = self.auto_sync_manager.enabled
                    self.auto_sync_manager.stop()
                    
                    self.auto_sync_manager = AutoSyncManager(self.sync_manager, self.config, self.logger)
                    if was_enabled or self.config.get("auto_sync.enabled", False):
                        self.auto_sync_manager.start()
            
            # Atualizar status
            self.logger.log("Settings updated")
            self.update_status()
    
    def open_branch_manager(self):
        """Abre o gerenciador de branches"""
        if not self.git_manager:
            QMessageBox.critical(self, "Error", "Git repository not initialized")
            return
        
        branch_dialog = BranchManagerDialog(self, self.git_manager, self.logger)
        branch_dialog.exec()
        
        # Atualizar status após fechar o diálogo
        self.update_status()
    
    def open_commit_templates(self):
        """Abre o gerenciador de templates de commit"""
        templates_dialog = CommitTemplateDialog(self, self.template_manager)
        templates_dialog.exec()
    
    def open_task_integration(self):
        """Abre o diálogo de integração com sistemas de tarefas"""
        task_dialog = TaskIntegrationDialog(self, self.task_manager)
        task_dialog.exec()
    
    def open_auto_sync(self):
        """Abre o diálogo de configuração de sincronização automática"""
        if not self.sync_manager:
            QMessageBox.critical(self, "Error", "Sync manager not initialized")
            return
        
        # TODO: Implementar diálogo de configuração de auto-sync
        QMessageBox.information(self, "Not Implemented", "Auto-sync settings dialog not implemented yet")
    
    def clear_log(self):
        """Limpa o widget de log"""
        if self.logger:
            self.logger.clear_widget()
    
    def show_about(self):
        """Mostra o diálogo 'Sobre'"""
        about_text = """Git-SVN Sync Tool

Version: 1.0.0
A tool for synchronizing Git and SVN repositories.

Features:
- Git and SVN repository management
- Synchronized commits
- Diff viewing
- Branch management
- Commit templates

Licensed under MIT License
"""
        QMessageBox.about(self, "About Git-SVN Sync Tool", about_text)
    
    def show_dependency_warning(self, missing_deps):
        """Mostra aviso sobre dependências ausentes"""
        if missing_deps:
            message = "The following dependencies are missing:\n\n"
            message += "\n".join(f"- {dep}" for dep in missing_deps)
            message += "\n\nSome features may not work properly."
            QMessageBox.warning(self, "Missing Dependencies", message)
    
    def closeEvent(self, event):
        """Manipula o evento de fechamento da janela"""
        # Parar auto-sync se estiver ativo
        if self.auto_sync_manager:
            self.auto_sync_manager.stop()
        
        # Parar todas as threads ativas
        for thread in list(self.active_threads):
            if thread.isRunning():
                thread.stop()
                thread.wait(100)  # Aguardar até 100ms para a thread terminar
        
        # Aguardar qualquer thread ativa ser finalizada
        import time
        
        # Pequena pausa para permitir que threads terminem
        time.sleep(0.1)
        
        # Processar eventos pendentes
        QApplication.processEvents()
        
        # Aceitar o evento para fechar a janela
        event.accept()