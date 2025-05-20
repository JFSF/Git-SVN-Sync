#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QTabWidget, QVBoxLayout,
                            QWidget, QFormLayout, QLabel, QLineEdit, QPushButton,
                            QFileDialog, QHBoxLayout, QCheckBox, QRadioButton,
                            QTextEdit, QGroupBox, QComboBox, QScrollArea, QSizePolicy,
                            QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor

from utils.helpers import (is_valid_url, is_valid_path, normalize_path, 
                         secure_encode, secure_decode)


class SettingsDialog(QDialog):
    """Diálogo de configurações usando Qt6 com validação aprimorada"""
    
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        
        self.settings = settings if settings else {}
        
        self.setWindowTitle("Settings")
        self.setMinimumSize(700, 550)
        
        # Criar widgets e layout
        self.create_widgets()
        
        # Preencher campos com valores existentes
        self.load_settings()
        
        # Configurar validação de campos
        self.setup_validation()
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # TabWidget para abas
        self.tab_widget = QTabWidget(self)
        main_layout.addWidget(self.tab_widget)
        
        # Criar abas
        self.create_repositories_tab()
        self.create_sync_tab()
        self.create_credentials_tab()
        self.create_ui_tab()
        
        # Botões de diálogo
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | 
                                      QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_save)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def create_repositories_tab(self):
        """Cria a aba de configurações de repositórios"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Formulário
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Git Repository
        git_url_label = QLabel("Git Repository URL:")
        git_url_label.setToolTip("Enter the URL of the Git repository to sync with")
        self.git_url_edit = QLineEdit()
        self.git_url_edit.setPlaceholderText("https://github.com/username/repo.git")
        self.git_url_edit.textChanged.connect(self.on_git_url_changed)
        form_layout.addRow(git_url_label, self.git_url_edit)
        
        # Label para feedback de validação
        self.git_url_validation = QLabel("")
        self.git_url_validation.setStyleSheet("color: gray; font-style: italic;")
        form_layout.addRow("", self.git_url_validation)
        
        # SVN Repository
        svn_url_label = QLabel("SVN Repository URL:")
        svn_url_label.setToolTip("Enter the URL of the SVN repository to sync with")
        self.svn_url_edit = QLineEdit()
        self.svn_url_edit.setPlaceholderText("https://svn.example.com/project/trunk")
        self.svn_url_edit.textChanged.connect(self.on_svn_url_changed)
        form_layout.addRow(svn_url_label, self.svn_url_edit)
        
        # Label para feedback de validação
        self.svn_url_validation = QLabel("")
        self.svn_url_validation.setStyleSheet("color: gray; font-style: italic;")
        form_layout.addRow("", self.svn_url_validation)
        
        # Working Copy
        working_copy_layout = QHBoxLayout()
        self.working_copy_edit = QLineEdit()
        self.working_copy_edit.setPlaceholderText("Path to local working copy")
        self.working_copy_edit.textChanged.connect(self.on_working_copy_changed)
        working_copy_layout.addWidget(self.working_copy_edit)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_directory)
        working_copy_layout.addWidget(browse_button)
        
        form_layout.addRow("Local Working Copy:", working_copy_layout)
        
        # Label para feedback de validação
        self.working_copy_validation = QLabel("")
        self.working_copy_validation.setStyleSheet("color: gray; font-style: italic;")
        form_layout.addRow("", self.working_copy_validation)
        
        # Default Branch
        self.default_branch_edit = QLineEdit()
        self.default_branch_edit.setPlaceholderText("main")
        form_layout.addRow("Default Git Branch:", self.default_branch_edit)
        
        layout.addLayout(form_layout)
        
        # Arquivo para ignorar
        ignore_group = QGroupBox("Files to Ignore")
        ignore_layout = QVBoxLayout(ignore_group)
        
        ignore_help = QLabel("Enter one pattern per line. Examples: *.pyc, .DS_Store, build/")
        ignore_help.setStyleSheet("color: gray; font-style: italic;")
        ignore_layout.addWidget(ignore_help)
        
        self.ignore_files_text = QTextEdit()
        self.ignore_files_text.setMinimumHeight(100)
        ignore_layout.addWidget(self.ignore_files_text)
        
        layout.addWidget(ignore_group)
        
        # Adicionar aba ao TabWidget
        self.tab_widget.addTab(tab, "Repositories")
    
    def create_sync_tab(self):
        """Cria a aba de configurações de sincronização"""
        tab = QScrollArea()
        tab.setWidgetResizable(True)
        tab.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        
        # Auto Sync
        auto_sync_group = QGroupBox("Automatic Synchronization")
        auto_sync_layout = QVBoxLayout(auto_sync_group)
        
        self.auto_sync_check = QCheckBox("Enable automatic synchronization")
        auto_sync_layout.addWidget(self.auto_sync_check)
        
        sync_interval_layout = QHBoxLayout()
        sync_interval_layout.addWidget(QLabel("Sync interval (minutes):"))
        self.sync_interval_edit = QLineEdit()
        self.sync_interval_edit.setMaximumWidth(100)
        self.sync_interval_edit.textChanged.connect(self.on_sync_interval_changed)
        sync_interval_layout.addWidget(self.sync_interval_edit)
        
        # Validação do intervalo
        self.sync_interval_validation = QLabel("")
        self.sync_interval_validation.setStyleSheet("color: gray; font-style: italic;")
        sync_interval_layout.addWidget(self.sync_interval_validation)
        sync_interval_layout.addStretch()
        
        auto_sync_layout.addLayout(sync_interval_layout)
        layout.addWidget(auto_sync_group)
        
        # Sync Direction
        direction_group = QGroupBox("Synchronization Direction")
        direction_layout = QVBoxLayout(direction_group)
        
        self.direction_bidir_radio = QRadioButton("Bidirectional (Git ↔ SVN)")
        self.direction_git_to_svn_radio = QRadioButton("Git to SVN only (Git → SVN)")
        self.direction_svn_to_git_radio = QRadioButton("SVN to Git only (Git ← SVN)")
        
        direction_layout.addWidget(self.direction_bidir_radio)
        direction_layout.addWidget(self.direction_git_to_svn_radio)
        direction_layout.addWidget(self.direction_svn_to_git_radio)
        
        layout.addWidget(direction_group)
        
        # Conflict Resolution
        conflict_group = QGroupBox("Conflict Resolution")
        conflict_layout = QVBoxLayout(conflict_group)
        
        self.conflict_none_radio = QRadioButton("Ask me for each conflict")
        self.conflict_git_radio = QRadioButton("Always prefer Git changes")
        self.conflict_svn_radio = QRadioButton("Always prefer SVN changes")
        
        conflict_layout.addWidget(self.conflict_none_radio)
        conflict_layout.addWidget(self.conflict_git_radio)
        conflict_layout.addWidget(self.conflict_svn_radio)
        
        layout.addWidget(conflict_group)
        
        # Opções adicionais
        options_group = QGroupBox("Additional Options")
        options_layout = QVBoxLayout(options_group)
        
        self.auto_stash_check = QCheckBox("Automatically stash local changes before sync")
        self.auto_push_check = QCheckBox("Automatically push to Git remote after SVN sync")
        
        options_layout.addWidget(self.auto_stash_check)
        options_layout.addWidget(self.auto_push_check)
        
        layout.addWidget(options_group)
        
        # Espaço extra no final
        layout.addStretch()
        
        # Configurar scroll area
        tab.setWidget(scroll_content)
        
        # Adicionar aba ao TabWidget
        self.tab_widget.addTab(tab, "Synchronization")
    
    def create_credentials_tab(self):
        """Cria a aba de configurações de credenciais"""
        tab = QScrollArea()
        tab.setWidgetResizable(True)
        tab.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        
        # Git Credentials
        git_cred_group = QGroupBox("Git Credentials")
        git_cred_layout = QFormLayout(git_cred_group)
        git_cred_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.git_username_edit = QLineEdit()
        git_cred_layout.addRow("Username:", self.git_username_edit)
        
        self.git_password_edit = QLineEdit()
        self.git_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        git_cred_layout.addRow("Password:", self.git_password_edit)
        
        self.git_save_password_check = QCheckBox("Save password (caution: stored in plain text)")
        git_cred_layout.addRow("", self.git_save_password_check)
        
        layout.addWidget(git_cred_group)
        
        # SVN Credentials
        svn_cred_group = QGroupBox("SVN Credentials")
        svn_cred_layout = QFormLayout(svn_cred_group)
        svn_cred_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.svn_username_edit = QLineEdit()
        svn_cred_layout.addRow("Username:", self.svn_username_edit)
        
        self.svn_password_edit = QLineEdit()
        self.svn_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        svn_cred_layout.addRow("Password:", self.svn_password_edit)
        
        self.svn_save_password_check = QCheckBox("Save password (caution: stored in plain text)")
        svn_cred_layout.addRow("", self.svn_save_password_check)
        
        layout.addWidget(svn_cred_group)
        
        # Aviso de segurança
        warning_label = QLabel("⚠️ Security Warning: Passwords are stored in plain text in the"
                             " configuration file. For better security, consider using"
                             " credential helpers or SSH keys.")
        warning_label.setStyleSheet("background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px;")
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # Espaço extra no final
        layout.addStretch()
        
        # Configurar scroll area
        tab.setWidget(scroll_content)
        
        # Adicionar aba ao TabWidget
        self.tab_widget.addTab(tab, "Credentials")
    
    def create_ui_tab(self):
        """Cria a aba de configurações de interface"""
        tab = QScrollArea()
        tab.setWidgetResizable(True)
        tab.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        
        # Aparência
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["system", "light", "dark"])
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        # Diff View Style
        self.diff_style_side_radio = QRadioButton("Side by Side")
        self.diff_style_unified_radio = QRadioButton("Unified View")
        
        diff_style_layout = QVBoxLayout()
        diff_style_layout.addWidget(self.diff_style_side_radio)
        diff_style_layout.addWidget(self.diff_style_unified_radio)
        
        appearance_layout.addRow("Default Diff View:", diff_style_layout)
        
        layout.addWidget(appearance_group)
        
        # Log Settings
        log_group = QGroupBox("Logging")
        log_layout = QVBoxLayout(log_group)
        
        self.log_to_file_check = QCheckBox("Enable logging to file")
        self.log_to_file_check.toggled.connect(lambda checked: self.log_path_edit.setEnabled(checked))
        log_layout.addWidget(self.log_to_file_check)
        
        log_file_layout = QHBoxLayout()
        log_file_layout.addWidget(QLabel("Log file location:"))
        self.log_path_edit = QLineEdit()
        self.log_path_edit.setEnabled(False)  # Inicialmente desabilitado
        log_file_layout.addWidget(self.log_path_edit)
        
        log_browse_button = QPushButton("Browse")
        log_browse_button.clicked.connect(self.browse_log_file)
        log_file_layout.addWidget(log_browse_button)
        
        log_layout.addLayout(log_file_layout)
        
        layout.addWidget(log_group)
        
        # Notifications
        notif_group = QGroupBox("Notifications")
        notif_layout = QVBoxLayout(notif_group)
        
        self.show_notifications_check = QCheckBox("Show desktop notifications")
        notif_layout.addWidget(self.show_notifications_check)
        
        layout.addWidget(notif_group)
        
        # Espaço extra no final
        layout.addStretch()
        
        # Configurar scroll area
        tab.setWidget(scroll_content)
        
        # Adicionar aba ao TabWidget
        self.tab_widget.addTab(tab, "Interface")
    
    def setup_validation(self):
        """Configura validação em tempo real para os campos"""
        # Esta função é chamada após load_settings para configurar validadores
        
        # Verifica a URL Git inicial
        self.on_git_url_changed(self.git_url_edit.text())
        
        # Verifica a URL SVN inicial
        self.on_svn_url_changed(self.svn_url_edit.text())
        
        # Verifica o working copy inicial
        self.on_working_copy_changed(self.working_copy_edit.text())
        
        # Verifica o intervalo de sincronização inicial
        self.on_sync_interval_changed(self.sync_interval_edit.text())
    
    def on_git_url_changed(self, text):
        """Valida a URL do repositório Git em tempo real"""
        if not text:
            self.git_url_validation.setText("")
            return
            
        text = text.strip()
        if is_valid_url(text):
            self.git_url_validation.setText("✓ Valid URL")
            self.git_url_validation.setStyleSheet("color: green;")
        else:
            self.git_url_validation.setText("⚠ URL may not be valid")
            self.git_url_validation.setStyleSheet("color: orange;")
    
    def on_svn_url_changed(self, text):
        """Valida a URL do repositório SVN em tempo real"""
        if not text:
            self.svn_url_validation.setText("")
            return
            
        text = text.strip()
        if is_valid_url(text):
            self.svn_url_validation.setText("✓ Valid URL")
            self.svn_url_validation.setStyleSheet("color: green;")
        else:
            self.svn_url_validation.setText("⚠ URL may not be valid")
            self.svn_url_validation.setStyleSheet("color: orange;")
    
    def on_working_copy_changed(self, text):
        """Valida o diretório de trabalho em tempo real"""
        if not text:
            self.working_copy_validation.setText("")
            return
            
        text = text.strip()
        text = normalize_path(text)
        
        if is_valid_path(text):
            self.working_copy_validation.setText("✓ Directory exists")
            self.working_copy_validation.setStyleSheet("color: green;")
        else:
            self.working_copy_validation.setText("⚠ Directory does not exist (will be created)")
            self.working_copy_validation.setStyleSheet("color: orange;")
    
    def on_sync_interval_changed(self, text):
        """Valida o intervalo de sincronização em tempo real"""
        if not text:
            self.sync_interval_validation.setText("")
            return
            
        try:
            value = int(text)
            if value <= 0:
                self.sync_interval_validation.setText("⚠ Must be positive")
                self.sync_interval_validation.setStyleSheet("color: red;")
            elif value < 5:
                self.sync_interval_validation.setText("⚠ Very short interval")
                self.sync_interval_validation.setStyleSheet("color: orange;")
            else:
                self.sync_interval_validation.setText("✓")
                self.sync_interval_validation.setStyleSheet("color: green;")
        except ValueError:
            self.sync_interval_validation.setText("⚠ Must be a number")
            self.sync_interval_validation.setStyleSheet("color: red;")
    
    def browse_directory(self):
        """Abre diálogo para selecionar diretório de trabalho"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Working Directory", "", QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.working_copy_edit.setText(directory)
    
    def browse_log_file(self):
        """Abre diálogo para selecionar arquivo de log"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Log File", "", "Log Files (*.log);;All Files (*)"
        )
        if file_path:
            self.log_path_edit.setText(file_path)
    
    def load_settings(self):
        """Carrega as configurações nos campos do formulário"""
        # Aba Repositories
        self.git_url_edit.setText(self.settings.get("git_repo_url", ""))
        self.svn_url_edit.setText(self.settings.get("svn_repo_url", ""))
        self.working_copy_edit.setText(self.settings.get("local_working_copy", ""))
        self.default_branch_edit.setText(self.settings.get("default_branch", "main"))
        
        # Arquivos ignorados
        ignore_files = self.settings.get("ignore_files", [])
        if ignore_files:
            self.ignore_files_text.setText("\n".join(ignore_files))
        
        # Aba Synchronization
        self.auto_sync_check.setChecked(self.settings.get("auto_sync.enabled", False))
        self.sync_interval_edit.setText(str(self.settings.get("auto_sync.interval_minutes", 30)))
        
        # Direção de sincronização
        sync_direction = self.settings.get("sync.direction", "bidirectional")
        if sync_direction == "git_to_svn":
            self.direction_git_to_svn_radio.setChecked(True)
        elif sync_direction == "svn_to_git":
            self.direction_svn_to_git_radio.setChecked(True)
        else:  # bidirectional
            self.direction_bidir_radio.setChecked(True)
        
        # Resolução de conflitos
        conflict_resolution = self.settings.get("sync.auto_resolve_conflicts", "none")
        if conflict_resolution == "git":
            self.conflict_git_radio.setChecked(True)
        elif conflict_resolution == "svn":
            self.conflict_svn_radio.setChecked(True)
        else:  # none
            self.conflict_none_radio.setChecked(True)
        
        # Opções adicionais
        self.auto_stash_check.setChecked(self.settings.get("sync.auto_stash", True))
        self.auto_push_check.setChecked(self.settings.get("sync.auto_push", False))
        
        # Aba Credentials
        self.git_username_edit.setText(self.settings.get("credentials.git.username", ""))
        # Usar secure_decode se a senha estiver codificada
        git_password = self.settings.get("credentials.git.password", "")
        self.git_password_edit.setText(git_password)
        self.git_save_password_check.setChecked(bool(git_password))
        
        self.svn_username_edit.setText(self.settings.get("credentials.svn.username", ""))
        # Usar secure_decode se a senha estiver codificada
        svn_password = self.settings.get("credentials.svn.password", "")
        self.svn_password_edit.setText(svn_password)
        self.svn_save_password_check.setChecked(bool(svn_password))
        
        # Aba Interface
        theme = self.settings.get("ui.theme", "system")
        self.theme_combo.setCurrentText(theme)
        
        diff_style = self.settings.get("ui.diff_view_style", "side-by-side")
        if diff_style == "unified":
            self.diff_style_unified_radio.setChecked(True)
        else:  # side-by-side
            self.diff_style_side_radio.setChecked(True)
        
        self.log_to_file_check.setChecked(self.settings.get("logging.enable_file_logging", False))
        self.log_path_edit.setText(self.settings.get("logging.log_file_path", ""))
        self.log_path_edit.setEnabled(self.log_to_file_check.isChecked())
        
        self.show_notifications_check.setChecked(self.settings.get("ui.show_notifications", True))
    
    def validate_and_save(self):
        """Valida os campos e salva se todos forem válidos"""
        # Validar campos obrigatórios e críticos
        
        # Validar intervalo de sincronização
        try:
            sync_interval = int(self.sync_interval_edit.text() or "30")
            if sync_interval <= 0:
                QMessageBox.critical(self, "Error", "Sync interval must be at least 1 minute")
                self.tab_widget.setCurrentIndex(1)  # Muda para a aba Synchronization
                self.sync_interval_edit.setFocus()
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Sync interval must be a number")
            self.tab_widget.setCurrentIndex(1)  # Muda para a aba Synchronization
            self.sync_interval_edit.setFocus()
            return
        
        # Verificar diretório de trabalho
        working_dir = self.working_copy_edit.text().strip()
        if working_dir and not is_valid_path(working_dir):
            reply = QMessageBox.question(
                self, "Directory Not Found", 
                f"The directory '{working_dir}' does not exist. Do you want to create it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    os.makedirs(working_dir, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not create directory: {str(e)}")
                    return
            else:
                self.tab_widget.setCurrentIndex(0)  # Muda para a aba Repositories
                self.working_copy_edit.setFocus()
                return
        
        # Verificar log file path
        if self.log_to_file_check.isChecked():
            log_path = self.log_path_edit.text().strip()
            if not log_path:
                QMessageBox.critical(self, "Error", "Log file path is required when logging is enabled")
                self.tab_widget.setCurrentIndex(3)  # Muda para a aba Interface
                self.log_path_edit.setFocus()
                return
            
            # Verificar se o diretório do arquivo de log existe
            log_dir = os.path.dirname(os.path.abspath(log_path))
            if not os.path.exists(log_dir):
                reply = QMessageBox.question(
                    self, "Directory Not Found", 
                    f"The directory for the log file does not exist. Do you want to create it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        os.makedirs(log_dir, exist_ok=True)
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Could not create directory: {str(e)}")
                        return
                else:
                    self.tab_widget.setCurrentIndex(3)  # Muda para a aba Interface
                    self.log_path_edit.setFocus()
                    return
        
        # Validar URLs de repositório
        git_url = self.git_url_edit.text().strip()
        if git_url and not is_valid_url(git_url):
            reply = QMessageBox.question(
                self, "Invalid URL", 
                "The Git repository URL may not be valid. Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.tab_widget.setCurrentIndex(0)  # Muda para a aba Repositories
                self.git_url_edit.setFocus()
                return
        
        svn_url = self.svn_url_edit.text().strip()
        if svn_url and not is_valid_url(svn_url):
            reply = QMessageBox.question(
                self, "Invalid URL", 
                "The SVN repository URL may not be valid. Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.tab_widget.setCurrentIndex(0)  # Muda para a aba Repositories
                self.svn_url_edit.setFocus()
                return
        
        # Se todas as validações passaram, salvar configurações
        settings = self.get_settings()
        if settings:
            self.settings = settings
            self.accept()
    
    def get_settings(self):
        """Obtém as configurações atualizadas do formulário"""
        # Construir dicionário de configurações
        settings = {
            # Aba Repositories
            "git_repo_url": self.git_url_edit.text().strip(),
            "svn_repo_url": self.svn_url_edit.text().strip(),
            "local_working_copy": normalize_path(self.working_copy_edit.text().strip()),
            "default_branch": self.default_branch_edit.text().strip() or "main",
            "ignore_files": [line for line in self.ignore_files_text.toPlainText().split("\n") if line.strip()],
            
            # Aba Synchronization
            "auto_sync.enabled": self.auto_sync_check.isChecked(),
            "auto_sync.interval_minutes": int(self.sync_interval_edit.text() or "30"),
            
            # Direção de sincronização
            "sync.direction": "git_to_svn" if self.direction_git_to_svn_radio.isChecked() else
                            "svn_to_git" if self.direction_svn_to_git_radio.isChecked() else
                            "bidirectional",
            
            # Resolução de conflitos
            "sync.auto_resolve_conflicts": "git" if self.conflict_git_radio.isChecked() else
                                        "svn" if self.conflict_svn_radio.isChecked() else
                                        "none",
            
            # Opções adicionais
            "sync.auto_stash": self.auto_stash_check.isChecked(),
            "sync.auto_push": self.auto_push_check.isChecked(),
            
            # Aba Credentials
            "credentials.git.username": self.git_username_edit.text().strip(),
            "credentials.git.password": self.git_password_edit.text() if self.git_save_password_check.isChecked() else "",
            "credentials.svn.username": self.svn_username_edit.text().strip(),
            "credentials.svn.password": self.svn_password_edit.text() if self.svn_save_password_check.isChecked() else "",
            
            # Aba Interface
            "ui.theme": self.theme_combo.currentText(),
            "ui.diff_view_style": "unified" if self.diff_style_unified_radio.isChecked() else "side-by-side",
            "logging.enable_file_logging": self.log_to_file_check.isChecked(),
            "logging.log_file_path": self.log_path_edit.text().strip(),
            "ui.show_notifications": self.show_notifications_check.isChecked()
        }
        
        return settings