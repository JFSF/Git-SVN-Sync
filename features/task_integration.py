# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import re
import json
import os
import subprocess
import requests
from urllib.parse import urlparse

class TaskIntegrationManager:
    def __init__(self, config_manager, logger):
        """Inicializa o gerenciador de integração com sistemas de tarefas"""
        self.config = config_manager
        self.logger = logger
        
        # Carregar configurações
        self.load_config()
    
    def load_config(self):
        """Carrega configurações de integração de tarefas"""
        self.task_system = self.config.get("task_integration.system", "none")
        self.jira_url = self.config.get("task_integration.jira_url", "")
        self.jira_username = self.config.get("task_integration.jira_username", "")
        self.jira_token = self.config.get("task_integration.jira_token", "")
        self.jira_project = self.config.get("task_integration.jira_project", "")
        
        self.trello_api_key = self.config.get("task_integration.trello_api_key", "")
        self.trello_token = self.config.get("task_integration.trello_token", "")
        self.trello_board_id = self.config.get("task_integration.trello_board_id", "")
        
        self.extract_from_branch = self.config.get("task_integration.extract_from_branch", True)
        self.auto_update_task = self.config.get("task_integration.auto_update_task", False)
        self.task_id_regex = self.config.get("task_integration.task_id_regex", r'([A-Z]+-\d+)')
    
    def save_config(self):
        """Salva configurações de integração de tarefas"""
        self.config.set("task_integration.system", self.task_system)
        self.config.set("task_integration.jira_url", self.jira_url)
        self.config.set("task_integration.jira_username", self.jira_username)
        self.config.set("task_integration.jira_token", self.jira_token)
        self.config.set("task_integration.jira_project", self.jira_project)
        
        self.config.set("task_integration.trello_api_key", self.trello_api_key)
        self.config.set("task_integration.trello_token", self.trello_token)
        self.config.set("task_integration.trello_board_id", self.trello_board_id)
        
        self.config.set("task_integration.extract_from_branch", self.extract_from_branch)
        self.config.set("task_integration.auto_update_task", self.auto_update_task)
        self.config.set("task_integration.task_id_regex", self.task_id_regex)
    
    def extract_task_id(self, branch_name=None, commit_message=None):
        """Extrai o ID da tarefa do nome da branch ou mensagem de commit"""
        if not branch_name and not commit_message:
            return None
        
        # Tentar extrair usando regex configurada
        pattern = re.compile(self.task_id_regex)
        
        if branch_name:
            match = pattern.search(branch_name)
            if match:
                return match.group(1)
        
        if commit_message:
            match = pattern.search(commit_message)
            if match:
                return match.group(1)
        
        return None
    
    def get_task_info(self, task_id):
        """Obtém informações da tarefa do sistema configurado"""
        if not task_id:
            return None
        
        if self.task_system == "jira":
            return self._get_jira_task(task_id)
        elif self.task_system == "trello":
            return self._get_trello_task(task_id)
        
        return None
    
    def _get_jira_task(self, task_id):
        """Obtém informações de uma tarefa do Jira"""
        if not self.jira_url or not self.jira_username or not self.jira_token:
            self.logger.log("Jira credentials not configured", "WARNING")
            return None
        
        try:
            # Construir URL da API
            api_url = f"{self.jira_url.rstrip('/')}/rest/api/2/issue/{task_id}"
            
            # Fazer requisição à API do Jira
            response = requests.get(
                api_url,
                auth=(self.jira_username, self.jira_token),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extrair informações relevantes
                task_info = {
                    "id": task_id,
                    "title": data.get("fields", {}).get("summary", "No title"),
                    "status": data.get("fields", {}).get("status", {}).get("name", "Unknown"),
                    "type": data.get("fields", {}).get("issuetype", {}).get("name", "Task"),
                    "assignee": data.get("fields", {}).get("assignee", {}).get("displayName", "Unassigned"),
                    "url": f"{self.jira_url}/browse/{task_id}"
                }
                
                return task_info
            else:
                self.logger.log(f"Error getting Jira task: {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.logger.log(f"Error connecting to Jira: {str(e)}", "ERROR")
            return None
    
    def _get_trello_task(self, task_id):
        """Obtém informações de uma tarefa do Trello"""
        if not self.trello_api_key or not self.trello_token:
            self.logger.log("Trello credentials not configured", "WARNING")
            return None
        
        try:
            # Construir URL da API
            api_url = f"https://api.trello.com/1/boards/{self.trello_board_id}/cards"
            
            # Fazer requisição à API do Trello
            response = requests.get(
                api_url,
                params={
                    "key": self.trello_api_key,
                    "token": self.trello_token
                }
            )
            
            if response.status_code == 200:
                cards = response.json()
                
                # Procurar cartão com o ID da tarefa no nome ou descrição
                for card in cards:
                    if task_id in card.get("name", "") or task_id in card.get("desc", ""):
                        # Extrair informações relevantes
                        task_info = {
                            "id": task_id,
                            "title": card.get("name", "No title"),
                            "status": "Unknown",  # Precisaria de outra chamada para obter a lista
                            "type": "Card",
                            "assignee": "Unknown",  # Precisaria de outra chamada para obter membros
                            "url": card.get("shortUrl", "")
                        }
                        
                        return task_info
                
                self.logger.log(f"Trello card with ID {task_id} not found", "WARNING")
                return None
            else:
                self.logger.log(f"Error getting Trello card: {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.logger.log(f"Error connecting to Trello: {str(e)}", "ERROR")
            return None
    
    def update_task_status(self, task_id, new_status):
        """Atualiza o status de uma tarefa"""
        if not task_id or not new_status:
            return False, "Task ID or status not provided"
        
        if self.task_system == "jira":
            return self._update_jira_task_status(task_id, new_status)
        elif self.task_system == "trello":
            return self._update_trello_task_status(task_id, new_status)
        
        return False, "Task system not configured"
    
    def _update_jira_task_status(self, task_id, new_status):
        """Atualiza o status de uma tarefa do Jira"""
        if not self.jira_url or not self.jira_username or not self.jira_token:
            return False, "Jira credentials not configured"
        
        try:
            # Primeiro, obter os possíveis status e transições
            transitions_url = f"{self.jira_url.rstrip('/')}/rest/api/2/issue/{task_id}/transitions"
            
            response = requests.get(
                transitions_url,
                auth=(self.jira_username, self.jira_token),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                return False, f"Error getting transitions: {response.status_code}"
            
            transitions = response.json().get("transitions", [])
            
            # Procurar transição que corresponda ao status desejado
            transition_id = None
            for transition in transitions:
                if transition.get("name").lower() == new_status.lower():
                    transition_id = transition.get("id")
                    break
            
            if not transition_id:
                return False, f"Transition to status '{new_status}' not available"
            
            # Aplicar a transição
            update_response = requests.post(
                transitions_url,
                auth=(self.jira_username, self.jira_token),
                headers={"Content-Type": "application/json"},
                json={"transition": {"id": transition_id}}
            )
            
            if update_response.status_code == 204:
                self.logger.log(f"Updated Jira task {task_id} status to {new_status}", "SUCCESS")
                return True, f"Updated task status to {new_status}"
            else:
                return False, f"Error updating status: {update_response.status_code}"
                
        except Exception as e:
            self.logger.log(f"Error updating Jira task: {str(e)}", "ERROR")
            return False, str(e)
    
    def _update_trello_task_status(self, task_id, new_status):
        """Atualiza o status de uma tarefa do Trello"""
        if not self.trello_api_key or not self.trello_token:
            return False, "Trello credentials not configured"
        
        try:
            # Obter listas do quadro
            lists_url = f"https://api.trello.com/1/boards/{self.trello_board_id}/lists"
            
            response = requests.get(
                lists_url,
                params={
                    "key": self.trello_api_key,
                    "token": self.trello_token
                }
            )
            
            if response.status_code != 200:
                return False, f"Error getting Trello lists: {response.status_code}"
            
            lists = response.json()
            
            # Procurar lista que corresponda ao status desejado
            target_list_id = None
            for list_item in lists:
                if list_item.get("name").lower() == new_status.lower():
                    target_list_id = list_item.get("id")
                    break
            
            if not target_list_id:
                return False, f"List '{new_status}' not found on the board"
            
            # Encontrar o cartão que corresponde à tarefa
            cards_url = f"https://api.trello.com/1/boards/{self.trello_board_id}/cards"
            
            cards_response = requests.get(
                cards_url,
                params={
                    "key": self.trello_api_key,
                    "token": self.trello_token
                }
            )
            
            if cards_response.status_code != 200:
                return False, f"Error getting Trello cards: {cards_response.status_code}"
            
            cards = cards_response.json()
            
            # Procurar cartão com o ID da tarefa
            card_id = None
            for card in cards:
                if task_id in card.get("name", "") or task_id in card.get("desc", ""):
                    card_id = card.get("id")
                    break
            
            if not card_id:
                return False, f"Card with task ID {task_id} not found"
            
            # Mover o cartão para a lista desejada
            update_url = f"https://api.trello.com/1/cards/{card_id}"
            
            update_response = requests.put(
                update_url,
                params={
                    "key": self.trello_api_key,
                    "token": self.trello_token,
                    "idList": target_list_id
                }
            )
            
            if update_response.status_code == 200:
                self.logger.log(f"Updated Trello card for task {task_id} to list {new_status}", "SUCCESS")
                return True, f"Updated task status to {new_status}"
            else:
                return False, f"Error updating card: {update_response.status_code}"
                
        except Exception as e:
            self.logger.log(f"Error updating Trello card: {str(e)}", "ERROR")
            return False, str(e)
    
    def comment_on_task(self, task_id, comment_text):
        """Adiciona um comentário a uma tarefa"""
        if not task_id or not comment_text:
            return False, "Task ID or comment text not provided"
        
        if self.task_system == "jira":
            return self._comment_on_jira_task(task_id, comment_text)
        elif self.task_system == "trello":
            return self._comment_on_trello_task(task_id, comment_text)
        
        return False, "Task system not configured"
    
    def _comment_on_jira_task(self, task_id, comment_text):
        """Adiciona um comentário a uma tarefa do Jira"""
        if not self.jira_url or not self.jira_username or not self.jira_token:
            return False, "Jira credentials not configured"
        
        try:
            # Construir URL da API
            api_url = f"{self.jira_url.rstrip('/')}/rest/api/2/issue/{task_id}/comment"
            
            # Fazer requisição à API do Jira
            response = requests.post(
                api_url,
                auth=(self.jira_username, self.jira_token),
                headers={"Content-Type": "application/json"},
                json={"body": comment_text}
            )
            
            if response.status_code == 201:
                self.logger.log(f"Added comment to Jira task {task_id}", "SUCCESS")
                return True, "Comment added successfully"
            else:
                return False, f"Error adding comment: {response.status_code}"
                
        except Exception as e:
            self.logger.log(f"Error commenting on Jira task: {str(e)}", "ERROR")
            return False, str(e)
    
    def _comment_on_trello_task(self, task_id, comment_text):
        """Adiciona um comentário a uma tarefa do Trello"""
        if not self.trello_api_key or not self.trello_token:
            return False, "Trello credentials not configured"
        
        try:
            # Encontrar o cartão que corresponde à tarefa
            cards_url = f"https://api.trello.com/1/boards/{self.trello_board_id}/cards"
            
            cards_response = requests.get(
                cards_url,
                params={
                    "key": self.trello_api_key,
                    "token": self.trello_token
                }
            )
            
            if cards_response.status_code != 200:
                return False, f"Error getting Trello cards: {cards_response.status_code}"
            
            cards = cards_response.json()
            
            # Procurar cartão com o ID da tarefa
            card_id = None
            for card in cards:
                if task_id in card.get("name", "") or task_id in card.get("desc", ""):
                    card_id = card.get("id")
                    break
            
            if not card_id:
                return False, f"Card with task ID {task_id} not found"
            
            # Adicionar comentário ao cartão
            comment_url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
            
            comment_response = requests.post(
                comment_url,
                params={
                    "key": self.trello_api_key,
                    "token": self.trello_token,
                    "text": comment_text
                }
            )
            
            if comment_response.status_code == 200:
                self.logger.log(f"Added comment to Trello card for task {task_id}", "SUCCESS")
                return True, "Comment added successfully"
            else:
                return False, f"Error adding comment: {comment_response.status_code}"
                
        except Exception as e:
            self.logger.log(f"Error commenting on Trello card: {str(e)}", "ERROR")
            return False, str(e)

class TaskIntegrationDialog(tk.Toplevel):
    def __init__(self, parent, task_manager):
        """Inicializa o diálogo de integração com sistemas de tarefas"""
        super().__init__(parent)
        
        self.title("Task Integration")
        self.geometry("650x550")
        self.minsize(600, 500)
        self.transient(parent)
        self.grab_set()
        
        self.task_manager = task_manager
        
        # Criar widgets
        self.create_widgets()
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba de configuração
        config_frame = ttk.Frame(notebook, padding=10)
        notebook.add(config_frame, text="Configuration")
        
        # Aba de tarefas
        tasks_frame = ttk.Frame(notebook, padding=10)
        notebook.add(tasks_frame, text="Tasks")
        
        # Criar conteúdo das abas
        self.create_config_tab(config_frame)
        self.create_tasks_tab(tasks_frame)
        
        # Botões de ação
        button_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Save", 
                 command=self.save_config).pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="Close", 
                 command=self.destroy).pack(side=tk.RIGHT, padx=5)
    
    def create_config_tab(self, parent):
        """Cria o conteúdo da aba de configuração"""
        # Sistema de tarefas
        ttk.Label(parent, text="Task System:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.system_var = tk.StringVar(value=self.task_manager.task_system)
        system_combo = ttk.Combobox(parent, textvariable=self.system_var, width=15)
        system_combo["values"] = ["none", "jira", "trello"]
        system_combo["state"] = "readonly"
        system_combo.grid(row=0, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        system_combo.bind("<<ComboboxSelected>>", self.on_system_change)
        
        # Notebook para configurações específicas
        self.config_notebook = ttk.Notebook(parent)
        self.config_notebook.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, pady=(5, 10))
        
        # Configurações do Jira
        jira_frame = ttk.Frame(self.config_notebook, padding=10)
        self.config_notebook.add(jira_frame, text="Jira")
        
        ttk.Label(jira_frame, text="Jira URL:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.jira_url_var = tk.StringVar(value=self.task_manager.jira_url)
        ttk.Entry(jira_frame, textvariable=self.jira_url_var, width=40).grid(
            row=0, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0)
        )
        
        ttk.Label(jira_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.jira_username_var = tk.StringVar(value=self.task_manager.jira_username)
        ttk.Entry(jira_frame, textvariable=self.jira_username_var, width=30).grid(
            row=1, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0)
        )
        
        ttk.Label(jira_frame, text="API Token:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.jira_token_var = tk.StringVar(value=self.task_manager.jira_token)
        ttk.Entry(jira_frame, textvariable=self.jira_token_var, width=30, show="*").grid(
            row=2, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0)
        )
        
        ttk.Label(jira_frame, text="Default Project:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        self.jira_project_var = tk.StringVar(value=self.task_manager.jira_project)
        ttk.Entry(jira_frame, textvariable=self.jira_project_var, width=20).grid(
            row=3, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0)
        )
        
        ttk.Button(jira_frame, text="Test Connection", 
                 command=lambda: self.test_connection("jira")).grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 0)
        )
        
        # Configurações do Trello
        trello_frame = ttk.Frame(self.config_notebook, padding=10)
        self.config_notebook.add(trello_frame, text="Trello")
        
        ttk.Label(trello_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.trello_key_var = tk.StringVar(value=self.task_manager.trello_api_key)
        ttk.Entry(trello_frame, textvariable=self.trello_key_var, width=40).grid(
            row=0, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0)
        )
        
        ttk.Label(trello_frame, text="Token:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.trello_token_var = tk.StringVar(value=self.task_manager.trello_token)
        ttk.Entry(trello_frame, textvariable=self.trello_token_var, width=40, show="*").grid(
            row=1, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0)
        )
        
        ttk.Label(trello_frame, text="Board ID:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.trello_board_var = tk.StringVar(value=self.task_manager.trello_board_id)
        ttk.Entry(trello_frame, textvariable=self.trello_board_var, width=30).grid(
            row=2, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0)
        )
        
        ttk.Button(trello_frame, text="Test Connection", 
                 command=lambda: self.test_connection("trello")).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0)
        )
        
        # Configurações gerais
        ttk.Separator(parent, orient=tk.HORIZONTAL).grid(
            row=2, column=0, columnspan=2, sticky=tk.EW, pady=10
        )
        
        ttk.Label(parent, text="General Settings", font=("", 10, "bold")).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 5)
        )
        
        self.extract_branch_var = tk.BooleanVar(value=self.task_manager.extract_from_branch)
        ttk.Checkbutton(parent, text="Extract task ID from branch name", 
                       variable=self.extract_branch_var).grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 5)
        )
        
        self.auto_update_var = tk.BooleanVar(value=self.task_manager.auto_update_task)
        ttk.Checkbutton(parent, text="Automatically update task status on commit", 
                       variable=self.auto_update_var).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 5)
        )
        
        ttk.Label(parent, text="Task ID Regex:").grid(row=6, column=0, sticky=tk.W, pady=(5, 5))
        self.regex_var = tk.StringVar(value=self.task_manager.task_id_regex)
        ttk.Entry(parent, textvariable=self.regex_var, width=30).grid(
            row=6, column=1, sticky=tk.W, pady=(5, 5), padx=(5, 0)
        )
        
        # Ajustar expansão
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(1, weight=1)
    
    def create_tasks_tab(self, parent):
        """Cria o conteúdo da aba de tarefas"""
        # Frame de pesquisa
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Task ID:").pack(side=tk.LEFT)
        
        self.task_id_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.task_id_var, width=20).pack(
            side=tk.LEFT, padx=5
        )
        
        ttk.Button(search_frame, text="Search", 
                 command=self.search_task).pack(side=tk.LEFT)
        
        # Frame de detalhes da tarefa
        details_frame = ttk.LabelFrame(parent, text="Task Details")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Grade para detalhes
        details_grid = ttk.Frame(details_frame, padding=10)
        details_grid.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(details_grid, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.task_id_label = ttk.Label(details_grid, text="")
        self.task_id_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_grid, text="Title:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.task_title_label = ttk.Label(details_grid, text="")
        self.task_title_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_grid, text="Status:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.task_status_label = ttk.Label(details_grid, text="")
        self.task_status_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_grid, text="Type:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.task_type_label = ttk.Label(details_grid, text="")
        self.task_type_label.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_grid, text="Assignee:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.task_assignee_label = ttk.Label(details_grid, text="")
        self.task_assignee_label.grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # Link para a tarefa
        self.task_link_label = ttk.Label(details_grid, text="", foreground="blue", cursor="hand2")
        self.task_link_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(10, 2))
        self.task_link_label.bind("<Button-1>", self.open_task_link)
        
        # Configurar expansão
        details_grid.columnconfigure(1, weight=1)
        
        # Frame de ações
        actions_frame = ttk.LabelFrame(parent, text="Actions")
        actions_frame.pack(fill=tk.X)
        
        actions_content = ttk.Frame(actions_frame, padding=10)
        actions_content.pack(fill=tk.X)
        
        ttk.Label(actions_content, text="Update Status:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.status_var = tk.StringVar()
        status_combo = ttk.Combobox(actions_content, textvariable=self.status_var, width=20)
        status_combo["values"] = ["In Progress", "In Review", "Done"]
        status_combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Button(actions_content, text="Update", 
                 command=self.update_task_status).grid(row=0, column=2, pady=2)
        
        ttk.Label(actions_content, text="Add Comment:").grid(row=1, column=0, sticky=tk.W, pady=(10, 2))
        
        self.comment_text = tk.Text(actions_content, height=3, width=40)
        self.comment_text.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=2)
        
        ttk.Button(actions_content, text="Add Comment", 
                 command=self.add_task_comment).grid(row=2, column=2, pady=2, padx=5)
        
        # Ajustar colunas
        actions_content.columnconfigure(1, weight=1)
    
    def on_system_change(self, event):
        """Manipula a alteração do sistema de tarefas selecionado"""
        system = self.system_var.get()
        
        # Selecionar aba correspondente no notebook
        if system == "jira":
            self.config_notebook.select(0)
        elif system == "trello":
            self.config_notebook.select(1)
    
    def test_connection(self, system):
        """Testa a conexão com o sistema de tarefas selecionado"""
        if system == "jira":
            # Testar conexão com Jira
            url = self.jira_url_var.get()
            username = self.jira_username_var.get()
            token = self.jira_token_var.get()
            
            if not url or not username or not token:
                messagebox.showerror("Error", "Please fill in all Jira fields")
                return
            
            try:
                # Validar URL
                parsed_url = urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    messagebox.showerror("Error", "Invalid Jira URL")
                    return
                
                # Testar API
                api_url = f"{url.rstrip('/')}/rest/api/2/myself"
                
                response = requests.get(
                    api_url,
                    auth=(username, token),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    username = user_data.get("displayName", user_data.get("name", "unknown"))
                    messagebox.showinfo("Success", f"Connection successful! Logged in as {username}")
                else:
                    messagebox.showerror("Error", f"Connection failed: {response.status_code}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Connection error: {str(e)}")
            
        elif system == "trello":
            # Testar conexão com Trello
            api_key = self.trello_key_var.get()
            token = self.trello_token_var.get()
            board_id = self.trello_board_var.get()
            
            if not api_key or not token:
                messagebox.showerror("Error", "Please fill in API Key and Token fields")
                return
            
            try:
                # Testar API
                if board_id:
                    # Se o ID do quadro foi fornecido, testar acesso a ele
                    api_url = f"https://api.trello.com/1/boards/{board_id}"
                    
                    response = requests.get(
                        api_url,
                        params={
                            "key": api_key,
                            "token": token
                        }
                    )
                    
                    if response.status_code == 200:
                        board_data = response.json()
                        board_name = board_data.get("name", "unknown")
                        messagebox.showinfo("Success", f"Connection successful! Board: {board_name}")
                    else:
                        messagebox.showerror("Error", f"Connection failed: {response.status_code}")
                
                else:
                    # Se não, testar apenas as credenciais
                    api_url = "https://api.trello.com/1/members/me"
                    
                    response = requests.get(
                        api_url,
                        params={
                            "key": api_key,
                            "token": token
                        }
                    )
                    
                    if response.status_code == 200:
                        user_data = response.json()
                        username = user_data.get("fullName", user_data.get("username", "unknown"))
                        messagebox.showinfo("Success", f"Connection successful! Logged in as {username}")
                    else:
                        messagebox.showerror("Error", f"Connection failed: {response.status_code}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def save_config(self):
        """Salva as configurações"""
        # Atualizar configurações no gerenciador
        self.task_manager.task_system = self.system_var.get()
        self.task_manager.jira_url = self.jira_url_var.get()
        self.task_manager.jira_username = self.jira_username_var.get()
        self.task_manager.jira_token = self.jira_token_var.get()
        self.task_manager.jira_project = self.jira_project_var.get()
        
        self.task_manager.trello_api_key = self.trello_key_var.get()
        self.task_manager.trello_token = self.trello_token_var.get()
        self.task_manager.trello_board_id = self.trello_board_var.get()
        
        self.task_manager.extract_from_branch = self.extract_branch_var.get()
        self.task_manager.auto_update_task = self.auto_update_var.get()
        self.task_manager.task_id_regex = self.regex_var.get()
        
        # Salvar no config_manager
        self.task_manager.save_config()
        
        messagebox.showinfo("Success", "Task integration settings saved")
    
    def search_task(self):
        """Busca informações de uma tarefa"""
        task_id = self.task_id_var.get().strip()
        
        if not task_id:
            messagebox.showerror("Error", "Please enter a task ID")
            return
        
        # Validar formato usando regex configurada
        pattern = re.compile(self.regex_var.get())
        if not pattern.match(task_id):
            messagebox.showwarning("Warning", f"Task ID doesn't match the pattern: {self.regex_var.get()}")
        
        # Obter informações da tarefa
        task_info = self.task_manager.get_task_info(task_id)
        
        if not task_info:
            messagebox.showerror("Error", f"Could not find task with ID: {task_id}")
            return
        
        # Exibir informações
        self.task_id_label.config(text=task_info.get("id", ""))
        self.task_title_label.config(text=task_info.get("title", ""))
        self.task_status_label.config(text=task_info.get("status", ""))
        self.task_type_label.config(text=task_info.get("type", ""))
        self.task_assignee_label.config(text=task_info.get("assignee", ""))
        
        # Configurar link
        url = task_info.get("url", "")
        if url:
            self.task_link_label.config(text=f"Open in browser: {url}")
        else:
            self.task_link_label.config(text="")
    
    def open_task_link(self, event):
        """Abre o link da tarefa no navegador"""
        link_text = self.task_link_label.cget("text")
        if link_text:
            url = link_text.replace("Open in browser: ", "")
            import webbrowser
            webbrowser.open(url)
    
    def update_task_status(self):
        """Atualiza o status da tarefa"""
        task_id = self.task_id_label.cget("text")
        new_status = self.status_var.get()
        
        if not task_id:
            messagebox.showerror("Error", "No task selected")
            return
        
        if not new_status:
            messagebox.showerror("Error", "Please select a status")
            return
        
        # Atualizar status
        success, message = self.task_manager.update_task_status(task_id, new_status)
        
        if success:
            messagebox.showinfo("Success", message)
            self.search_task()  # Recarregar detalhes
        else:
            messagebox.showerror("Error", message)
    
    def add_task_comment(self):
        """Adiciona um comentário à tarefa"""
        task_id = self.task_id_label.cget("text")
        comment_text = self.comment_text.get(1.0, tk.END).strip()
        
        if not task_id:
            messagebox.showerror("Error", "No task selected")
            return
        
        if not comment_text:
            messagebox.showerror("Error", "Please enter a comment")
            return
        
        # Adicionar comentário
        success, message = self.task_manager.comment_on_task(task_id, comment_text)
        
        if success:
            messagebox.showinfo("Success", message)
            self.comment_text.delete(1.0, tk.END)  # Limpar campo
        else:
            messagebox.showerror("Error", message)