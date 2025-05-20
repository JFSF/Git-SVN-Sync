# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import os
from threading import Thread
import time

from utils.logger import LogManager
from core.git_manager import GitManager
from core.svn_manager import SVNManager
from ui.commit_dialog import CommitDialog
from ui.settings_dialog import SettingsDialog
from ui.diff_viewer import DiffViewer
from features.commit_templates import CommitTemplateManager, CommitTemplateDialog
from features.branch_manager import BranchManagerDialog

class MainWindow:
    def __init__(self, root, config):
        """Inicializa a janela principal"""
        self.root = root
        self.config = config
        
        # Configurar variáveis
        self.git_repo_url = self.config.get('git_repo_url', '')
        self.svn_repo_url = self.config.get('svn_repo_url', '')
        self.local_working_copy = self.config.get('local_working_copy', '')
        
        # Gerenciadores e serviços
        self._setup_managers()
        
        # Criar interface
        self._create_ui()
        
        # Atualizar status inicial
        self.update_status()
    
    def _setup_managers(self):
        """Inicializa gerenciadores e serviços"""
        # Configurar logger
        self.log_text = None  # será configurado após criação da UI
        self.logger = LogManager(self.log_text)
        
        # Gerenciadores
        self.git_manager = None
        self.svn_manager = None
        self.template_manager = CommitTemplateManager(self.config)
        
        if self.local_working_copy:
            self.git_manager = GitManager(self.local_working_copy, self.logger)
            # self.svn_manager = SVNManager(self.local_working_copy, self.logger)
    
    def _create_ui(self):
        """Cria a interface do usuário"""
        # Configurar tema
        self.root.configure(bg="#f0f2f5")
        
        # Menu principal
        self._create_menu()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Painel superior (status)
        self._create_status_panel(main_frame)
        
        # Barra de ferramentas
        self._create_toolbar(main_frame)
        
        # Área principal
        content_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        content_paned.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Painel esquerdo (arquivos)
        files_frame = self._create_files_panel(content_paned)
        
        # Painel direito (log)
        log_frame = self._create_log_panel(content_paned)
        
        # Adicionar painéis ao PanedWindow
        content_paned.add(files_frame, weight=1)
        content_paned.add(log_frame, weight=1)
        
        # Atualizar referência do logger
        self.logger.log_widget = self.log_text
        self.logger.setup_text_tags()
    
    def _create_menu(self):
        """Cria o menu principal"""
        menubar = tk.Menu(self.root)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Settings", command=self._open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Menu Git
        git_menu = tk.Menu(menubar, tearoff=0)
        git_menu.add_command(label="Initialize Repository", 
                           command=lambda: Thread(target=self._init_git_repo, daemon=True).start())
        git_menu.add_command(label="Commit Changes", 
                           command=self._open_git_commit)
        git_menu.add_command(label="Sync with Remote", 
                           command=lambda: Thread(target=self._sync_git_repo, daemon=True).start())
        git_menu.add_separator()
        git_menu.add_command(label="Branch Manager", command=self._open_branch_manager)
        menubar.add_cascade(label="Git", menu=git_menu)
        
        # Menu SVN
        svn_menu = tk.Menu(menubar, tearoff=0)
        svn_menu.add_command(label="Update from Repository", 
                           command=lambda: Thread(target=self._update_svn, daemon=True).start())
        svn_menu.add_command(label="Commit Changes", 
                           command=self._open_svn_commit)
        menubar.add_cascade(label="SVN", menu=svn_menu)
        
        # Menu Tools
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Commit Templates", command=self._open_commit_templates)
        tools_menu.add_command(label="Synchronize Both Repositories", 
                             command=lambda: Thread(target=self._sync_repos, daemon=True).start())
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Menu Help
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def _create_status_panel(self, parent):
        """Cria o painel de status"""
        status_frame = ttk.LabelFrame(parent, text="Repository Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid layout
        status_frame.columnconfigure(1, weight=1)
        
        # Git Status
        ttk.Label(status_frame, text="Git Repository:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.git_status = ttk.Label(status_frame, text="Not initialized")
        self.git_status.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # SVN Status
        ttk.Label(status_frame, text="SVN Repository:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.svn_status = ttk.Label(status_frame, text="Not initialized")
        self.svn_status.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Local Status
        ttk.Label(status_frame, text="Local Working Copy:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.local_status = ttk.Label(status_frame, text="Not set")
        self.local_status.grid(row=2, column=1, sticky=tk.W, pady=2)
    
    def _create_toolbar(self, parent):
        """Cria a barra de ferramentas"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # Botão de atualizar status
        refresh_btn = ttk.Button(toolbar, text="Refresh Status", command=self.update_status)
        refresh_btn.pack(side=tk.LEFT)
        
        # Botão de commit
        commit_btn = ttk.Button(toolbar, text="Commit Changes", command=self._open_git_commit)
        commit_btn.pack(side=tk.LEFT, padx=5)
        
        # Botão de sincronização
        sync_btn = ttk.Button(toolbar, text="Sync Repositories", 
                            command=lambda: Thread(target=self._sync_repos, daemon=True).start())
        sync_btn.pack(side=tk.LEFT)
        
        # Botão de visualização de diferenças
        diff_btn = ttk.Button(toolbar, text="View Differences", 
                            command=lambda: self._show_diff_for_selected())
        diff_btn.pack(side=tk.LEFT, padx=5)
        
        # Separador
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        # Branch selector
        ttk.Label(toolbar, text="Branch:").pack(side=tk.LEFT, padx=(0, 5))
        self.branch_combo = ttk.Combobox(toolbar, width=15, state="readonly")
        self.branch_combo.pack(side=tk.LEFT)
        self.branch_combo.bind("<<ComboboxSelected>>", self._on_branch_selected)
    
    def _create_files_panel(self, parent):
        """Cria o painel de arquivos"""
        files_frame = ttk.LabelFrame(parent, text="Modified Files", padding=10)
        
        # Barra de ferramentas de arquivos
        files_toolbar = ttk.Frame(files_frame)
        files_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(files_toolbar, text="Refresh", 
                 command=self._refresh_files_list).pack(side=tk.LEFT)
        
        ttk.Button(files_toolbar, text="Commit Selected", 
                 command=lambda: self._open_git_commit(self._get_selected_files())).pack(side=tk.LEFT, padx=5)
        
        # Treeview para arquivos
        columns = ("status", "path")
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show="headings", selectmode="extended")
        
        # Configurar colunas
        self.files_tree.heading("status", text="Status")
        self.files_tree.heading("path", text="File Path")
        
        self.files_tree.column("status", width=80, anchor="center")
        self.files_tree.column("path", width=350)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        # Empacotar widgets
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Duplo clique para visualização de diferenças
        self.files_tree.bind("<Double-1>", lambda e: self._show_diff_for_selected())
        
        return files_frame
    
    def _create_log_panel(self, parent):
        """Cria o painel de log"""
        log_frame = ttk.LabelFrame(parent, text="Log Messages", padding=10)
        
        # Barra de ferramentas do log
        log_toolbar = ttk.Frame(log_frame)
        log_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(log_toolbar, text="Clear Log", 
                 command=lambda: self.logger.clear_widget()).pack(side=tk.LEFT)
        
        # Widget de texto para log
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10)
        self.log_text.config(state=tk.DISABLED)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Empacotar widgets
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return log_frame
    
    def update_status(self):
        """Atualiza o status dos repositórios"""
        Thread(target=self._update_status_thread, daemon=True).start()
    
    def _update_status_thread(self):
        """Thread para atualizar status"""
        try:
            # Verificar diretório local
            if not self.local_working_copy:
                self.local_status.config(text="Not set")
                self.git_status.config(text="Not initialized")
                self.svn_status.config(text="Not initialized")
                return
            
            if os.path.exists(self.local_working_copy):
                self.local_status.config(text=f"Exists: {self.local_working_copy}")
                self.logger.log("Local working copy exists")
            else:
                self.local_status.config(text=f"Not found: {self.local_working_copy}")
                self.logger.log("Local working copy not found", "WARNING")
                return
            
            # Status Git
            if not self.git_manager:
                self.git_manager = GitManager(self.local_working_copy, self.logger)
            
            git_status = self.git_manager.get_status()
            if git_status["valid"]:
                self.git_status.config(text=git_status["message"])
                
                # Atualizar combo de branches
                if "branch" in git_status:
                    local_branches, remote_branches = self.git_manager.get_branches()
                    if local_branches:
                        self.branch_combo["values"] = local_branches
                        current_branch = git_status["branch"]
                        if current_branch in local_branches:
                            self.branch_combo.set(current_branch)
                        elif local_branches:
                            self.branch_combo.set(local_branches[0])
            else:
                self.git_status.config(text=git_status["message"])
            
            # Status SVN (a implementar)
            self.svn_status.config(text="Not implemented yet")
            
            # Atualizar lista de arquivos
            self._refresh_files_list()
            
        except Exception as e:
            self.logger.log(f"Error updating status: {str(e)}", "ERROR")
    
    def _refresh_files_list(self):
        """Atualiza a lista de arquivos modificados"""
        # Limpar árvore
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        if not self.git_manager:
            return
        
        # Obter arquivos modificados
        modified_files = self.git_manager.get_modified_files()
        
        # Status types
        status_labels = {
            "M": "Modified",
            "A": "Added",
            "D": "Deleted",
            "R": "Renamed",
            "?": "Untracked"
        }
        
        # Adicionar arquivos à árvore
        for file_info in modified_files:
            file_path = file_info["path"]
            
            # Determinar tipo de status
            status_type = file_info["type"]
            status = status_labels.get(status_type, status_type)
            
            # Adicionar à treeview
            self.files_tree.insert("", "end", values=(status, file_path))
            
        # Log
        self.logger.log(f"Found {len(modified_files)} modified files")
    
    def _get_selected_files(self):
        """Obtém arquivos selecionados na treeview"""
        selected_items = self.files_tree.selection()
        return [self.files_tree.item(item, "values")[1] for item in selected_items]
    
    def _show_diff_for_selected(self):
        """Mostra diferenças para o arquivo selecionado"""
        selected_files = self._get_selected_files()
        
        if not selected_files:
            messagebox.showinfo("Info", "No files selected")
            return
        
        if not self.git_manager:
            messagebox.showerror("Error", "Git repository not initialized")
            return
        
        # Mostrar diff para cada arquivo selecionado (limite a 5 por vez)
        for file_path in selected_files[:5]:
            diff_data = self.git_manager.get_diff(file_path)
            
            if diff_data:
                DiffViewer(self.root, f"Diff: {file_path}", file_path, diff_data)
            else:
                messagebox.showerror("Error", f"Could not get diff for {file_path}")
    
    def _init_git_repo(self):
        """Inicializa repositório Git"""
        if not self.local_working_copy:
            messagebox.showerror("Error", "Local working copy not set")
            self._open_settings()
            return
        
        if not self.git_manager:
            self.git_manager = GitManager(self.local_working_copy, self.logger)
        
        self.logger.log("Initializing Git repository...")
        
        success = self.git_manager.init_repo(self.git_repo_url)
        
        if success:
            messagebox.showinfo("Success", "Git repository initialized successfully")
        else:
            messagebox.showerror("Error", "Failed to initialize Git repository")
        
        self.update_status()
    
    def _open_git_commit(self, selected_files=None):
        """Abre diálogo para commit Git"""
        if not self.git_manager:
            messagebox.showerror("Error", "Git repository not initialized")
            return
        
        # Obter arquivos modificados
        all_modified_files = self.git_manager.get_modified_files()
        if not all_modified_files:
            messagebox.showinfo("Info", "No modified files to commit")
            return
        
        # Se arquivos foram pré-selecionados, usar apenas esses
        if selected_files:
            files_to_show = [f for f in all_modified_files if f["path"] in selected_files]
        else:
            files_to_show = all_modified_files
        
        # Obter templates de commit
        commit_templates = self.template_manager.get_templates()
        
        # Criar e mostrar diálogo
        commit_dialog = CommitDialog(self.root, files_to_show, commit_templates)
        
        # Esperar resposta
        self.root.wait_window(commit_dialog)
        
        # Processar resultado
        if commit_dialog.result:
            selected_files = commit_dialog.selected_files
            commit_message = commit_dialog.commit_message
            
            success, result = self.git_manager.commit(selected_files, commit_message)
            
            if success:
                messagebox.showinfo("Success", f"Successfully committed {len(selected_files)} files")
                self.update_status()
            else:
                messagebox.showerror("Error", f"Error committing files: {result}")
    
    def _sync_git_repo(self):
        """Sincroniza com repositório Git remoto"""
        if not self.git_manager:
            messagebox.showerror("Error", "Git repository not initialized")
            return
        
        self.logger.log("Syncing with Git remote repository...")
        
        success, message = self.git_manager.sync_with_remote()
        
        if success:
            self.logger.log("Git synchronization completed successfully", "SUCCESS")
            messagebox.showinfo("Success", "Git synchronization completed successfully")
        else:
            self.logger.log(f"Git synchronization failed: {message}", "ERROR")
            messagebox.showerror("Error", f"Git synchronization failed: {message}")
        
        self.update_status()
    
    def _update_svn(self):
        """Atualiza do repositório SVN"""
        self.logger.log("SVN update not implemented yet", "WARNING")
        messagebox.showinfo("Info", "SVN update not implemented yet")
    
    def _open_svn_commit(self):
        """Abre diálogo para commit SVN"""
        self.logger.log("SVN commit not implemented yet", "WARNING")
        messagebox.showinfo("Info", "SVN commit not implemented yet")
    
    def _sync_repos(self):
        """Sincroniza ambos os repositórios"""
        if not self.git_manager:
            messagebox.showerror("Error", "Git repository not initialized")
            return
        
        self.logger.log("\nStarting synchronization process...")
        
        # Sincronizar Git
        self.logger.log("Syncing with Git remote repository...")
        git_success, git_message = self.git_manager.sync_with_remote()
        
        if git_success:
            self.logger.log("Git synchronization completed successfully", "SUCCESS")
        else:
            self.logger.log(f"Git synchronization failed: {git_message}", "ERROR")
        
        # Sincronizar SVN (simulado)
        self.logger.log("SVN synchronization not implemented yet", "WARNING")
        
        self.logger.log("Synchronization process completed")
        messagebox.showinfo("Info", "Synchronization process completed")
        
        self.update_status()
    
    def _on_branch_selected(self, event):
        """Manipula a seleção de branch"""
        # A implementar com checkout de branch
        selected_branch = self.branch_combo.get()
        self.logger.log(f"Branch selection not implemented yet: {selected_branch}", "WARNING")
    
    def _open_settings(self):
        """Abre diálogo de configurações"""
        settings = {
            "git_repo_url": self.git_repo_url,
            "svn_repo_url": self.svn_repo_url,
            "local_working_copy": self.local_working_copy
        }
        
        settings_dialog = SettingsDialog(self.root, settings)
        
        # Esperar resposta
        self.root.wait_window(settings_dialog)
        
        # Processar resultado
        if settings_dialog.result:
            # Atualizar configurações
            self.git_repo_url = settings_dialog.result["git_repo_url"]
            self.svn_repo_url = settings_dialog.result["svn_repo_url"]
            self.local_working_copy = settings_dialog.result["local_working_copy"]
            
            # Salvar no config manager
            self.config.set("git_repo_url", self.git_repo_url)
            self.config.set("svn_repo_url", self.svn_repo_url)
            self.config.set("local_working_copy", self.local_working_copy)
            
            # Reinicializar gerenciadores
            if self.local_working_copy:
                self.git_manager = GitManager(self.local_working_copy, self.logger)
                # self.svn_manager = SVNManager(self.local_working_copy, self.logger)
            
            # Atualizar status
            self.logger.log("Settings updated")
            self.update_status()
    
    def _open_commit_templates(self):
        """Abre gerenciador de templates de commit"""
        CommitTemplateDialog(self.root, self.template_manager)
    
    def _open_branch_manager(self):
        """Abre gerenciador de branches"""
        if not self.git_manager:
            messagebox.showerror("Error", "Git repository not initialized")
            return
        
        self.logger.log("Branch manager not implemented yet", "WARNING")
        messagebox.showinfo("Info", "Branch manager not implemented yet")
    
    def _show_about(self):
        """Mostra diálogo "Sobre"""""
        about_text = """Git-SVN Sync Tool

Version: 1.0.0
A tool for synchronizing Git and SVN repositories.

Features:
- Git and SVN repository management
- Synchronized commits
- Diff viewing
- Branch management
- Commit templates
"""
        messagebox.showinfo("About", about_text)
    
    def show_dependency_warning(self, missing_deps):
        """Mostra aviso sobre dependências ausentes"""
        if missing_deps:
            message = "The following dependencies are missing:\n\n"
            message += "\n".join(f"- {dep}" for dep in missing_deps)
            message += "\n\nSome features may not work properly."
            messagebox.showwarning("Missing Dependencies", message)