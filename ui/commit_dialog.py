# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import os

class CommitDialog(tk.Toplevel):
    def __init__(self, parent, files, commit_templates=None):
        """Inicializa o diálogo de commit"""
        super().__init__(parent)
        
        self.title("Commit Changes")
        self.geometry("700x500")
        self.minsize(600, 400)
        self.transient(parent)
        self.grab_set()
        
        self.files = files
        self.commit_templates = commit_templates or []
        
        # Variáveis para resultado
        self.result = None
        self.selected_files = []
        self.commit_message = ""
        
        # Criar widgets
        self.create_widgets()
        
        # Comportamento modal
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.wait_visibility()
        self.focus_set()
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        # Frame principal
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ==========================================================
        # Área de seleção de arquivos
        # ==========================================================
        files_frame = ttk.LabelFrame(main_frame, text="Modified Files", padding=10)
        files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Botões de ação para arquivos
        file_actions = ttk.Frame(files_frame)
        file_actions.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(file_actions, text="Select All", 
                 command=self.select_all_files).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(file_actions, text="Deselect All", 
                 command=self.deselect_all_files).pack(side=tk.LEFT)
        
        # Treeview com checkboxes para arquivos
        columns = ("status", "path")
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show="headings", selectmode="extended")
        
        # Configurar colunas
        self.files_tree.heading("status", text="Status")
        self.files_tree.heading("path", text="File Path")
        
        self.files_tree.column("status", width=80, anchor="center")
        self.files_tree.column("path", width=350)
        
        # Scrollbar para a treeview
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        # Empacotar widgets
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Adicionar arquivos à treeview
        status_types = {
            "M": "Modified",
            "A": "Added",
            "D": "Deleted",
            "R": "Renamed",
            "?": "Untracked",
            "C": "Conflict"
        }
        
        for file_info in self.files:
            status = status_types.get(file_info.get('type', '?'), '?')
            path = file_info.get('path', '')
            
            item_id = self.files_tree.insert("", "end", values=(status, path))
            
            # Selecionar por padrão
            self.files_tree.selection_add(item_id)
        
        # ==========================================================
        # Área de mensagem de commit
        # ==========================================================
        message_frame = ttk.LabelFrame(main_frame, text="Commit Message", padding=10)
        message_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Template selector
        if self.commit_templates:
            template_frame = ttk.Frame(message_frame)
            template_frame.pack(fill=tk.X, pady=(0, 5))
            
            ttk.Label(template_frame, text="Use Template:").pack(side=tk.LEFT, padx=(0, 5))
            
            self.template_combo = ttk.Combobox(template_frame, width=40)
            self.template_combo.pack(side=tk.LEFT)
            
            template_names = [template["name"] for template in self.commit_templates]
            self.template_combo["values"] = [""] + template_names
            self.template_combo.current(0)
            
            self.template_combo.bind("<<ComboboxSelected>>", self.on_template_selected)
        
        # Campo de texto para mensagem
        self.message_text = tk.Text(message_frame, height=8, wrap=tk.WORD)
        self.message_text.pack(fill=tk.BOTH, expand=True)
        
        # ==========================================================
        # Botões de ação
        # ==========================================================
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(button_frame, text="Commit", 
                 command=self.on_commit).pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="Cancel", 
                 command=self.on_cancel).pack(side=tk.RIGHT, padx=(0, 5))
    
    def select_all_files(self):
        """Seleciona todos os arquivos na treeview"""
        for item in self.files_tree.get_children():
            self.files_tree.selection_add(item)
    
    def deselect_all_files(self):
        """Desmarca todos os arquivos na treeview"""
        for item in self.files_tree.get_children():
            self.files_tree.selection_remove(item)
    
    def on_template_selected(self, event):
        """Preenche o campo de mensagem com o template selecionado"""
        template_name = self.template_combo.get()
        
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
            self.message_text.delete(1.0, tk.END)
            
            # Inserir template
            self.message_text.insert(tk.END, template_content)
    
    def on_commit(self):
        """Processa o commit quando o usuário clica em 'Commit'"""
        # Verificar se há arquivos selecionados
        selected_items = self.files_tree.selection()
        if not selected_items:
            tk.messagebox.showerror("Error", "No files selected for commit")
            return
        
        # Obter caminhos dos arquivos selecionados
        self.selected_files = []
        for item in selected_items:
            file_path = self.files_tree.item(item, "values")[1]
            self.selected_files.append(file_path)
        
        # Obter mensagem de commit
        self.commit_message = self.message_text.get(1.0, tk.END).strip()
        if not self.commit_message:
            tk.messagebox.showerror("Error", "Commit message cannot be empty")
            return
        
        # Definir resultado e fechar
        self.result = True
        self.destroy()
    
    def on_cancel(self):
        """Cancela o commit"""
        self.result = False
        self.destroy()