# -*- coding: utf-8 -*-

import os
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class CommitTemplateManager:
    def __init__(self, config_manager):
        """Inicializa o gerenciador de templates de commit"""
        self.config_manager = config_manager
        self.templates = self._load_templates()
    
    def _load_templates(self):
        """Carrega templates do gerenciador de configurações"""
        templates = self.config_manager.get('commit_templates', [])
        
        # Se não houver templates, criar alguns padrões
        if not templates:
            templates = [
                {
                    "name": "fix: Bug Fix",
                    "template": "fix: {description}\n\nFixes #{issue_number}"
                },
                {
                    "name": "feat: New Feature",
                    "template": "feat: {description}\n\nCloses #{issue_number}"
                },
                {
                    "name": "docs: Documentation",
                    "template": "docs: {description}"
                },
                {
                    "name": "style: Code Style",
                    "template": "style: {description}"
                },
                {
                    "name": "refactor: Code Refactoring",
                    "template": "refactor: {description}\n\nReason: {reason}"
                },
                {
                    "name": "test: Adding Tests",
                    "template": "test: {description}"
                },
                {
                    "name": "chore: Build/Maintenance",
                    "template": "chore: {description}"
                }
            ]
            self.config_manager.set('commit_templates', templates)
        
        return templates
    
    def get_templates(self):
        """Retorna a lista de templates"""
        return self.templates
    
    def add_template(self, name, template):
        """Adiciona um novo template"""
        self.templates.append({
            "name": name,
            "template": template
        })
        self.config_manager.set('commit_templates', self.templates)
    
    def update_template(self, index, name, template):
        """Atualiza um template existente"""
        if 0 <= index < len(self.templates):
            self.templates[index] = {
                "name": name,
                "template": template
            }
            self.config_manager.set('commit_templates', self.templates)
    
    def delete_template(self, index):
        """Remove um template"""
        if 0 <= index < len(self.templates):
            del self.templates[index]
            self.config_manager.set('commit_templates', self.templates)
    
    def get_template_by_name(self, name):
        """Obtém um template pelo nome"""
        for template in self.templates:
            if template["name"] == name:
                return template["template"]
        return None

class CommitTemplateDialog(tk.Toplevel):
    def __init__(self, parent, template_manager, callback=None):
        """Inicializa o diálogo de gerenciamento de templates"""
        super().__init__(parent)
        
        self.title("Commit Templates")
        self.geometry("600x500")
        self.minsize(500, 400)
        self.transient(parent)
        self.grab_set()
        
        self.template_manager = template_manager
        self.callback = callback
        
        self.create_widgets()
        self.load_templates()
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        # Frame principal
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame esquerdo para lista de templates
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(left_frame, text="Available Templates").pack(anchor="w", pady=(0, 5))
        
        self.templates_listbox = tk.Listbox(left_frame, width=30, exportselection=0)
        self.templates_listbox.pack(fill=tk.Y, expand=True)
        self.templates_listbox.bind('<<ListboxSelect>>', self.on_template_select)
        
        # Botões para gerenciar templates
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(btn_frame, text="New", command=self.on_new_template).pack(side=tk.LEFT)
        self.edit_btn = ttk.Button(btn_frame, text="Edit", command=self.on_edit_template, state=tk.DISABLED)
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        self.delete_btn = ttk.Button(btn_frame, text="Delete", command=self.on_delete_template, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT)
        
        # Frame direito para edição de template
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_frame, text="Template Name:").pack(anchor="w", pady=(0, 5))
        self.name_entry = ttk.Entry(right_frame, width=50)
        self.name_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(right_frame, text="Template Content:").pack(anchor="w", pady=(0, 5))
        self.template_text = tk.Text(right_frame, height=10, width=50)
        self.template_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        ttk.Label(right_frame, text="Placeholder Help:").pack(anchor="w", pady=(0, 5))
        help_text = tk.Text(right_frame, height=6, width=50)
        help_text.pack(fill=tk.X, pady=(0, 10))
        help_text.insert(tk.END, "Available placeholders:\n"
                           "{description} - Brief description of changes\n"
                           "{issue_number} - Issue or ticket number\n"
                           "{reason} - Reason for changes\n"
                           "{author} - Commit author\n\n"
                           "Use placeholders like {name} in your template.")
        help_text.config(state=tk.DISABLED)
        
        # Botões de ação
        action_frame = ttk.Frame(right_frame)
        action_frame.pack(fill=tk.X)
        
        self.save_btn = ttk.Button(action_frame, text="Save", command=self.on_save_template, state=tk.DISABLED)
        self.save_btn.pack(side=tk.RIGHT)
        
        ttk.Button(action_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=5)
    
    def load_templates(self):
        """Carrega templates na listbox"""
        self.templates_listbox.delete(0, tk.END)
        
        for template in self.template_manager.get_templates():
            self.templates_listbox.insert(tk.END, template["name"])
    
    def on_template_select(self, event):
        """Manipula a seleção de um template"""
        if not self.templates_listbox.curselection():
            return
        
        index = self.templates_listbox.curselection()[0]
        template = self.template_manager.get_templates()[index]
        
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, template["name"])
        
        self.template_text.delete(1.0, tk.END)
        self.template_text.insert(tk.END, template["template"])
        
        self.edit_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.NORMAL)
    
    def on_new_template(self):
        """Cria um novo template"""
        self.templates_listbox.selection_clear(0, tk.END)
        
        self.name_entry.delete(0, tk.END)
        self.template_text.delete(1.0, tk.END)
        
        self.edit_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.NORMAL)
    
    def on_edit_template(self):
        """Habilita edição de um template"""
        # Já está habilitado pela seleção, só um placeholder para futura funcionalidade
        pass
    
    def on_delete_template(self):
        """Remove um template"""
        if not self.templates_listbox.curselection():
            return
        
        index = self.templates_listbox.curselection()[0]
        template_name = self.templates_listbox.get(index)
        
        if messagebox.askyesno("Confirm Delete", f"Delete template '{template_name}'?"):
            self.template_manager.delete_template(index)
            self.load_templates()
            
            self.name_entry.delete(0, tk.END)
            self.template_text.delete(1.0, tk.END)
            
            self.edit_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)
            self.save_btn.config(state=tk.DISABLED)
    
    def on_save_template(self):
        """Salva um template novo ou editado"""
        name = self.name_entry.get().strip()
        template = self.template_text.get(1.0, tk.END).strip()
        
        if not name or not template:
            messagebox.showerror("Error", "Name and template content are required")
            return
        
        # Verificar se é edição ou novo
        if self.templates_listbox.curselection():
            index = self.templates_listbox.curselection()[0]
            self.template_manager.update_template(index, name, template)
        else:
            self.template_manager.add_template(name, template)
        
        self.load_templates()
        
        # Selecionar o template salvo
        for i in range(self.templates_listbox.size()):
            if self.templates_listbox.get(i) == name:
                self.templates_listbox.selection_set(i)
                break
        
        if self.callback:
            self.callback()