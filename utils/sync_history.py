#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de histórico de sincronizações
Mantém registro de todas as sincronizações realizadas
"""

import os
import json
from datetime import datetime


class SyncHistory:
    """Gerencia histórico de sincronizações"""

    def __init__(self, config_manager):
        """Inicializa o gerenciador de histórico"""
        self.config = config_manager

        # Determinar localização do arquivo de histórico
        config_dir = os.path.dirname(self.config.config_file)
        self.history_file = os.path.join(config_dir, "sync_history.json")

        self.history = []
        self.load()

    def load(self):
        """Carrega histórico do arquivo"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"Error loading sync history: {e}")
            self.history = []

    def save(self):
        """Salva histórico no arquivo"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving sync history: {e}")

    def add_entry(self, sync_type, success, files_count=0, message=""):
        """
        Adiciona entrada ao histórico

        Args:
            sync_type: Tipo de sincronização ("git_to_svn", "svn_to_git", "bidirectional")
            success: Se a sincronização foi bem-sucedida
            files_count: Número de arquivos sincronizados
            message: Mensagem adicional
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": sync_type,
            "success": success,
            "files_count": files_count,
            "message": message
        }

        self.history.append(entry)

        # Manter apenas as últimas 100 entradas
        if len(self.history) > 100:
            self.history = self.history[-100:]

        self.save()

    def get_recent(self, count=10):
        """
        Retorna as últimas N entradas do histórico

        Args:
            count: Número de entradas a retornar

        Returns:
            Lista com as entradas mais recentes
        """
        return list(reversed(self.history[-count:]))

    def get_stats(self):
        """
        Retorna estatísticas do histórico

        Returns:
            Dicionário com estatísticas
        """
        if not self.history:
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0
            }

        total = len(self.history)
        successful = sum(1 for entry in self.history if entry.get("success", False))
        failed = total - successful

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0.0
        }

    def clear(self):
        """Limpa todo o histórico"""
        self.history = []
        self.save()
