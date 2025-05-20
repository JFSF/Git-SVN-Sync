#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import platform
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QStandardPaths

class ConfigManager:
    """Gerenciador de configurações com suporte a Qt6"""
    
    def __init__(self, config_file=None):
        """Inicializa o gerenciador de configurações"""
        # Determinar localização do arquivo de configuração
        if config_file:
            self.config_file = config_file
        else:
            # Usar local padrão com base no sistema operacional
            app_data_dir = self._get_app_data_dir()
            self.config_file = os.path.join(app_data_dir, "git_svn_sync", "config.json")
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
        
        # Inicializar configurações
        self.config = {}
        
        # Carregar configurações
        self.load()
    
    def _get_app_data_dir(self):
        """Obtém o diretório de dados da aplicação com base no sistema"""
        app_data_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        
        # Fallback para métodos tradicionais se o Qt não fornecer uma localização válida
        if not app_data_dir:
            system = platform.system()
            if system == "Windows":
                app_data_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
            elif system == "Darwin":  # macOS
                app_data_dir = os.path.expanduser("~/Library/Application Support")
            else:  # Linux e outros
                app_data_dir = os.path.expanduser("~/.config")
        
        return app_data_dir
    
    def load(self):
        """Carrega configurações do arquivo"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                # Arquivo não existe, criar com configurações padrão
                self.config = self._get_default_config()
                self.save()
                
        except Exception as e:
            # Erro ao carregar, usar configurações padrão
            self.config = self._get_default_config()
            QMessageBox.warning(
                None, "Configuration Error", 
                f"Error loading configuration: {str(e)}\nUsing default settings."
            )
    
    def save(self):
        """Salva configurações no arquivo"""
        try:
            # Garantir que o diretório existe
            os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
                
        except Exception as e:
            QMessageBox.critical(
                None, "Configuration Error", 
                f"Error saving configuration: {str(e)}"
            )
    
    def get(self, key, default=None):
        """Obtém um valor de configuração"""
        # Suporte para chaves aninhadas como "section.key"
        if '.' in key:
            sections = key.split('.')
            config = self.config
            
            for section in sections[:-1]:
                config = config.get(section, {})
                
            return config.get(sections[-1], default)
        else:
            return self.config.get(key, default)
    
    def set(self, key, value):
        """Define um valor de configuração"""
        # Suporte para chaves aninhadas como "section.key"
        if '.' in key:
            sections = key.split('.')
            config = self.config
            
            # Navegar pela hierarquia, criando dicionários aninhados se necessário
            for section in sections[:-1]:
                if section not in config:
                    config[section] = {}
                elif not isinstance(config[section], dict):
                    config[section] = {}
                
                config = config[section]
                
            # Definir o valor na seção final
            config[sections[-1]] = value
        else:
            self.config[key] = value
        
        # Salvar após cada alteração
        self.save()
    
    def _get_default_config(self):
        """Retorna configurações padrão"""
        return {
            "git_repo_url": "",
            "svn_repo_url": "",
            "local_working_copy": "",
            "default_branch": "main",
            
            "sync": {
                "direction": "bidirectional",
                "auto_resolve_conflicts": "none",
                "auto_stash": True,
                "auto_push": False,
                "commit_message": "Synchronized changes"
            },
            
            "auto_sync": {
                "enabled": False,
                "interval_minutes": 30
            },
            
            "ui": {
                "theme": "system",
                "diff_view_style": "side-by-side",
                "show_notifications": True
            },
            
            "logging": {
                "enable_file_logging": False,
                "log_file_path": ""
            },
            
            "credentials": {
                "git": {
                    "username": "",
                    "password": ""
                },
                "svn": {
                    "username": "",
                    "password": ""
                }
            }
        }