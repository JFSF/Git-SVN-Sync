# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog
import os

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings):
        """Inicializa o diálogo de configurações"""
        super().__init__(parent)
        
        self.title("Settings")
        self.geometry("650x550")
        self.minsize(600, 500)
        self.transient(parent)
        self.grab_set()
        
        self.settings = settings
        self.result = None
        
        # Criar widgets
        self.create_widgets()
        
        # Comportamento modal
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.wait_visibility()
        self.focus_set()
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        # Frame principal com notebook
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook para diferentes abas de configuração
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Aba de repositórios
        repo_frame = self.create_repositories_tab()
        self.notebook.add(repo_frame, text="Repositories")
        
        # Aba de sincronização
        sync_frame = self.create_sync_tab()
        self.notebook.add(sync_frame, text="Synchronization")
        
        # Aba de credenciais
        cred_frame = self.create_credentials_tab()
        self.notebook.add(cred_frame, text="Credentials")
        
        # Aba de interface
        ui_frame = self.create_ui_tab()
        self.notebook.add(ui_frame, text="Interface")
        
        # Botões de ação
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Save", 
                 command=self.on_save).pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="Cancel", 
                 command=self.on_cancel).pack(side=tk.RIGHT, padx=(0, 5))
    
    def create_repositories_tab(self):
        """Cria a aba de configurações de repositórios"""
        frame = ttk.Frame(self.notebook, padding=10)
        
        # Git Repository
        ttk.Label(frame, text="Git Repository URL:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.git_url_var = tk.StringVar(value=self.settings.get("git_repo_url", ""))
        git_entry = ttk.Entry(frame, textvariable=self.git_url_var, width=50)
        git_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(5, 0))
        
        # SVN Repository
        ttk.Label(frame, text="SVN Repository URL:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        self.svn_url_var = tk.StringVar(value=self.settings.get("svn_repo_url", ""))
        svn_entry = ttk.Entry(frame, textvariable=self.svn_url_var, width=50)
        svn_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(5, 0))
        
        # Working Copy
        ttk.Label(frame, text="Local Working Copy:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        working_copy_frame = ttk.Frame(frame)
        working_copy_frame.grid(row=2, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(5, 0))
        
        self.working_copy_var = tk.StringVar(value=self.settings.get("local_working_copy", ""))
        working_copy_entry = ttk.Entry(working_copy_frame, textvariable=self.working_copy_var, width=40)
        working_copy_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def browse_directory():
            directory = filedialog.askdirectory()
            if directory:
                self.working_copy_var.set(directory)
        
        browse_btn = ttk.Button(working_copy_frame, text="Browse", command=browse_directory)
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Separador
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        # Configuração de branches
        ttk.Label(frame, text="Default Git Branch:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        
        self.default_branch_var = tk.StringVar(value=self.settings.get("default_branch", "main"))
        default_branch_entry = ttk.Entry(frame, textvariable=self.default_branch_var, width=20)
        default_branch_entry.grid(row=4, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        # Ignoring Files
        ttk.Label(frame, text="Files to Ignore:").grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        
        self.ignore_files_text = tk.Text(frame, height=5, width=50)
        self.ignore_files_text.grid(row=5, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(5, 0))
        
        # Preencher com valores existentes
        ignore_files = self.settings.get("ignore_files", [])
        if ignore_files:
            self.ignore_files_text.insert(tk.END, "\n".join(ignore_files))
        
        # Adicionar ScrollBar ao Text
        ignore_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.ignore_files_text.yview)
        ignore_scrollbar.grid(row=5, column=2, sticky=tk.NS, pady=(0, 5))
        self.ignore_files_text.config(yscrollcommand=ignore_scrollbar.set)
        
        # Configurar grid
        frame.columnconfigure(1, weight=1)
        
        return frame
    
    def create_sync_tab(self):
        """Cria a aba de configurações de sincronização"""
        frame = ttk.Frame(self.notebook, padding=10)
        
        # Auto Sync
        ttk.Label(frame, text="Automatic Synchronization", font=("", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.auto_sync_var = tk.BooleanVar(value=self.settings.get("auto_sync.enabled", False))
        auto_sync_check = ttk.Checkbutton(frame, text="Enable automatic synchronization", variable=self.auto_sync_var)
        auto_sync_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(frame, text="Sync interval (minutes):").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.sync_interval_var = tk.StringVar(value=str(self.settings.get("auto_sync.interval_minutes", 30)))
        sync_interval_entry = ttk.Entry(frame, textvariable=self.sync_interval_var, width=10)
        sync_interval_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        # Separador
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        # Sync Direction
        ttk.Label(frame, text="Synchronization Direction", font=("", 10, "bold")).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.sync_direction_var = tk.StringVar(value=self.settings.get("sync.direction", "bidirectional"))
        
        ttk.Radiobutton(frame, text="Bidirectional (Git ↔ SVN)", 
                       variable=self.sync_direction_var, value="bidirectional").grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 2)
        )
        
        ttk.Radiobutton(frame, text="Git to SVN only (Git → SVN)", 
                       variable=self.sync_direction_var, value="git_to_svn").grid(
            row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 2)
        )
        
        ttk.Radiobutton(frame, text="SVN to Git only (Git ← SVN)", 
                       variable=self.sync_direction_var, value="svn_to_git").grid(
            row=7, column=0, columnspan=2, sticky=tk.W, pady=(0, 2)
        )
        
        # Separador
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=8, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        # Conflict Resolution
        ttk.Label(frame, text="Conflict Resolution", font=("", 10, "bold")).grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.conflict_resolution_var = tk.StringVar(value=self.settings.get("sync.auto_resolve_conflicts", "none"))
        
        ttk.Radiobutton(frame, text="Ask me for each conflict", 
                       variable=self.conflict_resolution_var, value="none").grid(
            row=10, column=0, columnspan=2, sticky=tk.W, pady=(0, 2)
        )
        
        ttk.Radiobutton(frame, text="Always prefer Git changes", 
                       variable=self.conflict_resolution_var, value="git").grid(
            row=11, column=0, columnspan=2, sticky=tk.W, pady=(0, 2)
        )
        
        ttk.Radiobutton(frame, text="Always prefer SVN changes", 
                       variable=self.conflict_resolution_var, value="svn").grid(
            row=12, column=0, columnspan=2, sticky=tk.W, pady=(0, 2)
        )
        
        # Separador
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=13, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        # Opções adicionais
        ttk.Label(frame, text="Additional Options", font=("", 10, "bold")).grid(row=14, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.auto_stash_var = tk.BooleanVar(value=self.settings.get("sync.auto_stash", True))
        auto_stash_check = ttk.Checkbutton(frame, text="Automatically stash local changes before sync", variable=self.auto_stash_var)
        auto_stash_check.grid(row=15, column=0, columnspan=2, sticky=tk.W, pady=(0, 2))
        
        self.auto_push_var = tk.BooleanVar(value=self.settings.get("sync.auto_push", False))
        auto_push_check = ttk.Checkbutton(frame, text="Automatically push to Git remote after SVN sync", variable=self.auto_push_var)
        auto_push_check.grid(row=16, column=0, columnspan=2, sticky=tk.W, pady=(0, 2))
        
        # Configurar grid
        frame.columnconfigure(1, weight=1)
        
        return frame
    
    def create_credentials_tab(self):
        """Cria a aba de configurações de credenciais"""
        frame = ttk.Frame(self.notebook, padding=10)
        
        # Git Credentials
        ttk.Label(frame, text="Git Credentials", font=("", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        self.git_username_var = tk.StringVar(value=self.settings.get("credentials.git.username", ""))
        git_username_entry = ttk.Entry(frame, textvariable=self.git_username_var, width=30)
        git_username_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        ttk.Label(frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.git_password_var = tk.StringVar(value=self.settings.get("credentials.git.password", ""))
        git_password_entry = ttk.Entry(frame, textvariable=self.git_password_var, width=30, show="*")
        git_password_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        self.git_save_password_var = tk.BooleanVar(value=bool(self.settings.get("credentials.git.password", "")))
        git_save_password_check = ttk.Checkbutton(frame, text="Save password (caution: stored in plain text)", variable=self.git_save_password_var)
        git_save_password_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Separador
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        # SVN Credentials
        ttk.Label(frame, text="SVN Credentials", font=("", 10, "bold")).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(frame, text="Username:").grid(row=6, column=0, sticky=tk.W, pady=(0, 5))
        
        self.svn_username_var = tk.StringVar(value=self.settings.get("credentials.svn.username", ""))
        svn_username_entry = ttk.Entry(frame, textvariable=self.svn_username_var, width=30)
        svn_username_entry.grid(row=6, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        ttk.Label(frame, text="Password:").grid(row=7, column=0, sticky=tk.W, pady=(0, 5))
        
        self.svn_password_var = tk.StringVar(value=self.settings.get("credentials.svn.password", ""))
        svn_password_entry = ttk.Entry(frame, textvariable=self.svn_password_var, width=30, show="*")
        svn_password_entry.grid(row=7, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        self.svn_save_password_var = tk.BooleanVar(value=bool(self.settings.get("credentials.svn.password", "")))
        svn_save_password_check = ttk.Checkbutton(frame, text="Save password (caution: stored in plain text)", variable=self.svn_save_password_var)
        svn_save_password_check.grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Aviso de segurança
        security_frame = ttk.Frame(frame, padding=5)
        security_frame.grid(row=9, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        security_frame.configure(style="Warning.TFrame")
        
        ttk.Label(security_frame, text="⚠️ Security Warning:", font=("", 9, "bold")).pack(anchor=tk.W)
        ttk.Label(security_frame, text="Passwords are stored in plain text in the configuration file.\n"
                                    "For better security, consider using credential helpers or SSH keys.", 
                wraplength=400).pack(anchor=tk.W)
        
        # Configurar grid
        frame.columnconfigure(1, weight=1)
        
        return frame
    
    def create_ui_tab(self):
        """Cria a aba de configurações de interface"""
        frame = ttk.Frame(self.notebook, padding=10)
        
        # Theme
        ttk.Label(frame, text="Appearance", font=("", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(frame, text="Theme:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        self.theme_var = tk.StringVar(value=self.settings.get("ui.theme", "system"))
        theme_combo = ttk.Combobox(frame, textvariable=self.theme_var, width=15)
        theme_combo["values"] = ["system", "light", "dark"]
        theme_combo["state"] = "readonly"
        theme_combo.grid(row=1, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        # Diff View Style
        ttk.Label(frame, text="Default Diff View:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.diff_style_var = tk.StringVar(value=self.settings.get("ui.diff_view_style", "side-by-side"))
        
        ttk.Radiobutton(frame, text="Side by Side", 
                       variable=self.diff_style_var, value="side-by-side").grid(
            row=2, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0)
        )
        
        ttk.Radiobutton(frame, text="Unified View", 
                       variable=self.diff_style_var, value="unified").grid(
            row=3, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0)
        )
        
        # Separador
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        # Log Settings
        ttk.Label(frame, text="Logging", font=("", 10, "bold")).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.log_to_file_var = tk.BooleanVar(value=self.settings.get("logging.enable_file_logging", False))
        log_file_check = ttk.Checkbutton(frame, text="Enable logging to file", variable=self.log_to_file_var)
        log_file_check.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(frame, text="Log file location:").grid(row=7, column=0, sticky=tk.W, pady=(0, 5))
        
        log_path_frame = ttk.Frame(frame)
        log_path_frame.grid(row=7, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(5, 0))
        
        self.log_path_var = tk.StringVar(value=self.settings.get("logging.log_file_path", ""))
        log_path_entry = ttk.Entry(log_path_frame, textvariable=self.log_path_var, width=30)
        log_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def browse_log_file():
            filename = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("All files", "*.*")]
            )
            if filename:
                self.log_path_var.set(filename)
        
        browse_log_btn = ttk.Button(log_path_frame, text="Browse", command=browse_log_file)
        browse_log_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Separador
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=8, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        # Notifications
        ttk.Label(frame, text="Notifications", font=("", 10, "bold")).grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.show_notifications_var = tk.BooleanVar(value=self.settings.get("ui.show_notifications", True))
        notifications_check = ttk.Checkbutton(frame, text="Show desktop notifications", variable=self.show_notifications_var)
        notifications_check.grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Configurar grid
        frame.columnconfigure(1, weight=1)
        
        return frame
    
    def on_save(self):
        """Salva as configurações e fecha o diálogo"""
        # Coletar valores de todas as abas
        settings = {
            # Aba Repositories
            "git_repo_url": self.git_url_var.get(),
            "svn_repo_url": self.svn_url_var.get(),
            "local_working_copy": self.working_copy_var.get(),
            "default_branch": self.default_branch_var.get(),
            "ignore_files": [line for line in self.ignore_files_text.get(1.0, tk.END).split("\n") if line.strip()],
            
            # Aba Synchronization
            "auto_sync": {
                "enabled": self.auto_sync_var.get(),
                "interval_minutes": int(self.sync_interval_var.get() or 30)
            },
            "sync": {
                "direction": self.sync_direction_var.get(),
                "auto_resolve_conflicts": self.conflict_resolution_var.get(),
                "auto_stash": self.auto_stash_var.get(),
                "auto_push": self.auto_push_var.get()
            },
            
            # Aba Credentials
            "credentials": {
                "git": {
                    "username": self.git_username_var.get(),
                    "password": self.git_password_var.get() if self.git_save_password_var.get() else ""
                },
                "svn": {
                    "username": self.svn_username_var.get(),
                    "password": self.svn_password_var.get() if self.svn_save_password_var.get() else ""
                }
            },
            
            # Aba Interface
            "ui": {
                "theme": self.theme_var.get(),
                "diff_view_style": self.diff_style_var.get(),
                "show_notifications": self.show_notifications_var.get()
            },
            "logging": {
                "enable_file_logging": self.log_to_file_var.get(),
                "log_file_path": self.log_path_var.get()
            }
        }
        
        # Definir resultado e fechar
        self.result = settings
        self.destroy()
    
    def on_cancel(self):
        """Cancela as alterações e fecha o diálogo"""
        self.result = None
        self.destroy()