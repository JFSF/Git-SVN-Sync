# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import re

class BranchManagerDialog(tk.Toplevel):
    def __init__(self, parent, git_manager, logger):
        """Inicializa o diálogo de gerenciamento de branches"""
        super().__init__(parent)
        
        self.title("Branch Manager")
        self.geometry("700x500")
        self.minsize(600, 400)
        self.transient(parent)
        self.grab_set()
        
        self.git_manager = git_manager
        self.logger = logger
        
        # Variáveis
        self.current_branch = None
        self.local_branches = []
        self.remote_branches = []
        
        # Criar widgets
        self.create_widgets()
        
        # Atualizar lista de branches
        self.refresh_branches()
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Layout de duas colunas
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Branches locais
        local_frame = ttk.LabelFrame(main_frame, text="Local Branches", padding=10)
        local_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 5))
        
        self.local_listbox = tk.Listbox(local_frame, selectmode=tk.SINGLE)
        local_scrollbar = ttk.Scrollbar(local_frame, orient=tk.VERTICAL, 
                                      command=self.local_listbox.yview)
        self.local_listbox.configure(yscrollcommand=local_scrollbar.set)
        
        self.local_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        local_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.local_listbox.bind('<<ListboxSelect>>', self.on_local_branch_select)
        
        # Branches remotas
        remote_frame = ttk.LabelFrame(main_frame, text="Remote Branches", padding=10)
        remote_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(5, 0))
        
        self.remote_listbox = tk.Listbox(remote_frame, selectmode=tk.SINGLE)
        remote_scrollbar = ttk.Scrollbar(remote_frame, orient=tk.VERTICAL, 
                                       command=self.remote_listbox.yview)
        self.remote_listbox.configure(yscrollcommand=remote_scrollbar.set)
        
        self.remote_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        remote_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.remote_listbox.bind('<<ListboxSelect>>', self.on_remote_branch_select)
        
        # Frames de ações
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        
        # Informações da branch atual
        current_frame = ttk.LabelFrame(action_frame, text="Current Branch", padding=10)
        current_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(current_frame, text="Branch:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.current_branch_label = ttk.Label(current_frame, text="...")
        self.current_branch_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(current_frame, text="Status:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.current_status_label = ttk.Label(current_frame, text="...")
        self.current_status_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Ações para branches
        branch_actions = ttk.Frame(action_frame)
        branch_actions.pack(fill=tk.X)
        
        # Coluna da esquerda - Ações locais
        local_actions = ttk.LabelFrame(branch_actions, text="Local Branch Actions", padding=10)
        local_actions.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Button(local_actions, text="Checkout Selected", 
                 command=self.checkout_selected_branch).pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(local_actions, text="Create New Branch", 
                 command=self.create_new_branch).pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(local_actions, text="Delete Selected", 
                 command=self.delete_selected_branch).pack(fill=tk.X, pady=(0, 5))
        
        # Coluna da direita - Ações remotas
        remote_actions = ttk.LabelFrame(branch_actions, text="Remote Branch Actions", padding=10)
        remote_actions.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Button(remote_actions, text="Checkout Remote", 
                 command=self.checkout_remote_branch).pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(remote_actions, text="Pull from Remote", 
                 command=self.pull_from_remote).pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(remote_actions, text="Push to Remote", 
                 command=self.push_to_remote).pack(fill=tk.X, pady=(0, 5))
        
        # Botões de ação principal
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=2, column=0, columnspan=2, sticky=tk.E, pady=(10, 0))
        
        ttk.Button(bottom_frame, text="Refresh", 
                 command=self.refresh_branches).pack(side=tk.LEFT)
        
        ttk.Button(bottom_frame, text="Close", 
                 command=self.destroy).pack(side=tk.LEFT, padx=(5, 0))
        
        # Configuração de expansão
        main_frame.rowconfigure(0, weight=1)
    
    def refresh_branches(self):
        """Atualiza a lista de branches locais e remotas"""
        try:
            # Obter branches
            self.local_branches, self.remote_branches = self.git_manager.get_branches()
            
            # Atualizar listbox de branches locais
            self.local_listbox.delete(0, tk.END)
            for branch in self.local_branches:
                self.local_listbox.insert(tk.END, branch)
            
            # Atualizar listbox de branches remotas
            self.remote_listbox.delete(0, tk.END)
            for branch in self.remote_branches:
                self.remote_listbox.insert(tk.END, branch)
            
            # Destacar branch atual
            git_status = self.git_manager.get_status()
            if git_status["valid"] and "branch" in git_status:
                self.current_branch = git_status["branch"]
                self.current_branch_label.config(text=self.current_branch)
                self.current_status_label.config(text=git_status.get("status", "Unknown"))
                
                # Selecionar na lista
                try:
                    index = self.local_branches.index(self.current_branch)
                    self.local_listbox.selection_clear(0, tk.END)
                    self.local_listbox.selection_set(index)
                    self.local_listbox.see(index)
                except ValueError:
                    pass
            else:
                self.current_branch = None
                self.current_branch_label.config(text="Unknown")
                self.current_status_label.config(text="Unknown")
            
        except Exception as e:
            self.logger.log(f"Error refreshing branches: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Error refreshing branches: {str(e)}")
    
    def on_local_branch_select(self, event):
        """Manipula a seleção de uma branch local"""
        # Limpar seleção na lista de branches remotas
        self.remote_listbox.selection_clear(0, tk.END)
    
    def on_remote_branch_select(self, event):
        """Manipula a seleção de uma branch remota"""
        # Limpar seleção na lista de branches locais
        self.local_listbox.selection_clear(0, tk.END)
    
    def get_selected_local_branch(self):
        """Obtém a branch local selecionada"""
        selection = self.local_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "No local branch selected")
            return None
        
        return self.local_branches[selection[0]]
    
    def get_selected_remote_branch(self):
        """Obtém a branch remota selecionada"""
        selection = self.remote_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "No remote branch selected")
            return None
        
        return self.remote_branches[selection[0]]
    
    def checkout_selected_branch(self):
        """Faz checkout da branch local selecionada"""
        branch_name = self.get_selected_local_branch()
        if not branch_name:
            return
        
        try:
            # Verificar se é a branch atual
            if branch_name == self.current_branch:
                messagebox.showinfo("Info", f"Already on branch '{branch_name}'")
                return
            
            # Fazer checkout
            self.logger.log(f"Checking out branch '{branch_name}'...")
            self.git_manager.repo.git.checkout(branch_name)
            self.logger.log(f"Switched to branch '{branch_name}'", "SUCCESS")
            
            # Atualizar interface
            self.refresh_branches()
            
        except Exception as e:
            self.logger.log(f"Error checking out branch: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Error checking out branch: {str(e)}")
    
    def create_new_branch(self):
        """Cria uma nova branch"""
        # Abrir diálogo para entrada de nome
        branch_dialog = tk.Toplevel(self)
        branch_dialog.title("Create New Branch")
        branch_dialog.geometry("400x150")
        branch_dialog.transient(self)
        branch_dialog.grab_set()
        
        # Centralizar na tela
        branch_dialog.update_idletasks()
        width = branch_dialog.winfo_width()
        height = branch_dialog.winfo_height()
        x = (branch_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (branch_dialog.winfo_screenheight() // 2) - (height // 2)
        branch_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Frame principal
        frame = ttk.Frame(branch_dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Label e entrada de texto
        ttk.Label(frame, text="New Branch Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        branch_name_var = tk.StringVar()
        name_entry = ttk.Entry(frame, textvariable=branch_name_var, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
        name_entry.focus_set()
        
        # Opção para checkout
        checkout_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Checkout new branch after creation", 
                       variable=checkout_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Botões
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=tk.E)
        
        def create_branch():
            name = branch_name_var.get().strip()
            
            # Validar nome
            if not name:
                messagebox.showerror("Error", "Branch name cannot be empty")
                return
            
            # Validar formato
            if not re.match(r'^[a-zA-Z0-9_\-./]+$', name):
                messagebox.showerror("Error", "Invalid branch name. Use only letters, numbers, underscores, hyphens, dots, and slashes.")
                return
            
            # Verificar se já existe
            if name in self.local_branches:
                messagebox.showerror("Error", f"Branch '{name}' already exists")
                return
            
            # Criar branch
            try:
                self.logger.log(f"Creating branch '{name}'...")
                success, message = self.git_manager.create_branch(name, checkout=checkout_var.get())
                
                if success:
                    self.logger.log(message, "SUCCESS")
                    branch_dialog.destroy()
                    self.refresh_branches()
                else:
                    messagebox.showerror("Error", message)
                    
            except Exception as e:
                self.logger.log(f"Error creating branch: {str(e)}", "ERROR")
                messagebox.showerror("Error", f"Error creating branch: {str(e)}")
        
        ttk.Button(button_frame, text="Create", command=create_branch).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Cancel", 
                 command=branch_dialog.destroy).pack(side=tk.RIGHT, padx=(0, 5))
    
    def delete_selected_branch(self):
        """Remove a branch local selecionada"""
        branch_name = self.get_selected_local_branch()
        if not branch_name:
            return
        
        # Verificar se é a branch atual
        if branch_name == self.current_branch:
            messagebox.showerror("Error", "Cannot delete the currently checked out branch")
            return
        
        # Confirmar exclusão
        if not messagebox.askyesno("Confirm Delete", f"Delete branch '{branch_name}'?"):
            return
        
        try:
            self.logger.log(f"Deleting branch '{branch_name}'...")
            self.git_manager.repo.git.branch("-d", branch_name)
            self.logger.log(f"Branch '{branch_name}' deleted", "SUCCESS")
            
            # Atualizar interface
            self.refresh_branches()
            
        except Exception as e:
            self.logger.log(f"Error deleting branch: {str(e)}", "ERROR")
            
            # Verificar se é erro de branch não mesclada
            if "not fully merged" in str(e):
                # Perguntar se deseja forçar exclusão
                if messagebox.askyesno("Force Delete", 
                                   f"Branch '{branch_name}' is not fully merged. Force delete?"):
                    try:
                        self.git_manager.repo.git.branch("-D", branch_name)
                        self.logger.log(f"Branch '{branch_name}' force deleted", "SUCCESS")
                        self.refresh_branches()
                    except Exception as e2:
                        self.logger.log(f"Error force deleting branch: {str(e2)}", "ERROR")
                        messagebox.showerror("Error", f"Error force deleting branch: {str(e2)}")
            else:
                messagebox.showerror("Error", f"Error deleting branch: {str(e)}")
    
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
            if messagebox.askyesno("Local Branch Exists", 
                               f"A local branch '{branch_name}' already exists. Checkout the local branch?"):
                try:
                    self.git_manager.repo.git.checkout(branch_name)
                    self.logger.log(f"Switched to branch '{branch_name}'", "SUCCESS")
                    self.refresh_branches()
                except Exception as e:
                    self.logger.log(f"Error checking out branch: {str(e)}", "ERROR")
                    messagebox.showerror("Error", f"Error checking out branch: {str(e)}")
            return
        
        # Criar branch de rastreamento
        try:
            self.logger.log(f"Creating tracking branch for '{remote_branch}'...")
            self.git_manager.repo.git.checkout('-b', branch_name, remote_branch)
            self.logger.log(f"Switched to new branch '{branch_name}' tracking '{remote_branch}'", "SUCCESS")
            
            # Atualizar interface
            self.refresh_branches()
            
        except Exception as e:
            self.logger.log(f"Error checking out remote branch: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Error checking out remote branch: {str(e)}")
    
    def pull_from_remote(self):
        """Puxa alterações da branch remota para a branch atual"""
        # Verificar se há uma branch atual
        if not self.current_branch:
            messagebox.showerror("Error", "No active branch")
            return
        
        try:
            self.logger.log(f"Pulling changes from remote for branch '{self.current_branch}'...")
            self.git_manager.repo.git.pull()
            self.logger.log("Pull completed successfully", "SUCCESS")
            
            # Atualizar interface
            self.refresh_branches()
            
        except Exception as e:
            self.logger.log(f"Error pulling from remote: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Error pulling from remote: {str(e)}")
    
    def push_to_remote(self):
        """Envia alterações da branch atual para a branch remota"""
        # Verificar se há uma branch atual
        if not self.current_branch:
            messagebox.showerror("Error", "No active branch")
            return
        
        try:
            # Verificar se a branch remota existe
            remote_branch = f"origin/{self.current_branch}"
            
            if remote_branch in self.remote_branches:
                # Branch remota existe - push normal
                self.logger.log(f"Pushing changes to remote for branch '{self.current_branch}'...")
                self.git_manager.repo.git.push()
            else:
                # Branch remota não existe - definir upstream
                self.logger.log(f"Setting up remote branch for '{self.current_branch}'...")
                self.git_manager.repo.git.push('--set-upstream', 'origin', self.current_branch)
            
            self.logger.log("Push completed successfully", "SUCCESS")
            
            # Atualizar interface
            self.refresh_branches()
            
        except Exception as e:
            self.logger.log(f"Error pushing to remote: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Error pushing to remote: {str(e)}")