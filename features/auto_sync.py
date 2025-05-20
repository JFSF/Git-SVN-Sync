# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import threading
import time
import os
from datetime import datetime, timedelta

class AutoSyncManager:
    def __init__(self, sync_manager, config_manager, logger):
        """Inicializa o gerenciador de sincronização automática"""
        self.sync_manager = sync_manager
        self.config = config_manager
        self.logger = logger
        
        self.sync_thread = None
        self.stop_event = threading.Event()
        self.next_sync_time = None
        self.sync_count = 0
        
        # Carregar configurações iniciais
        self.enabled = self.config.get("auto_sync.enabled", False)
        self.interval = self.config.get("auto_sync.interval_minutes", 30)
    
    def start(self):
        """Inicia a sincronização automática"""
        if self.sync_thread and self.sync_thread.is_alive():
            return
        
        self.enabled = self.config.get("auto_sync.enabled", False)
        self.interval = self.config.get("auto_sync.interval_minutes", 30)
        
        if not self.enabled:
            self.logger.log("Automatic synchronization is disabled", "WARNING")
            return
        
        self.stop_event.clear()
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        
        self.next_sync_time = datetime.now() + timedelta(minutes=self.interval)
        self.logger.log(f"Automatic synchronization started. Next sync at {self.next_sync_time.strftime('%H:%M:%S')}")
    
    def stop(self):
        """Para a sincronização automática"""
        if self.sync_thread and self.sync_thread.is_alive():
            self.stop_event.set()
            self.sync_thread.join(timeout=1.0)
            self.logger.log("Automatic synchronization stopped")
    
    def _sync_worker(self):
        """Função de trabalho para a thread de sincronização"""
        self.logger.log("Auto-sync thread started")
        
        while not self.stop_event.is_set():
            # Verificar se é hora de sincronizar
            if datetime.now() >= self.next_sync_time:
                self._perform_sync()
                
                # Calcular próximo tempo de sincronização
                self.next_sync_time = datetime.now() + timedelta(minutes=self.interval)
                self.logger.log(f"Next automatic sync at {self.next_sync_time.strftime('%H:%M:%S')}")
            
            # Aguardar um pouco (verificar a cada 10 segundos)
            self.stop_event.wait(10)
    
    def _perform_sync(self):
        """Realiza a sincronização automática"""
        self.sync_count += 1
        self.logger.log(f"\n=== Starting Automatic Synchronization (#{self.sync_count}) ===")
        
        # Obter direção de sincronização das configurações
        sync_direction = self.config.get("sync.direction", "bidirectional")
        
        try:
            result = False
            message = ""
            
            if sync_direction == "git_to_svn":
                self.logger.log("Auto-sync: Git to SVN")
                result, message = self.sync_manager.sync_git_to_svn()
            elif sync_direction == "svn_to_git":
                self.logger.log("Auto-sync: SVN to Git")
                result, message = self.sync_manager.sync_svn_to_git()
            else:  # bidirectional
                self.logger.log("Auto-sync: Bidirectional")
                result, message = self.sync_manager.bidirectional_sync()
            
            if result:
                self.logger.log(f"Automatic synchronization completed successfully: {message}", "SUCCESS")
                
                # Mostrar notificação de desktop se configurado
                if self.config.get("ui.show_notifications", True):
                    self._show_notification("Sync Successful", "Automatic synchronization completed successfully")
            else:
                self.logger.log(f"Automatic synchronization failed: {message}", "ERROR")
                
                # Mostrar notificação de desktop para falha
                if self.config.get("ui.show_notifications", True):
                    self._show_notification("Sync Failed", f"Automatic synchronization failed: {message}", error=True)
                
        except Exception as e:
            self.logger.log(f"Error during automatic synchronization: {str(e)}", "ERROR")
            
            # Mostrar notificação de desktop para erro
            if self.config.get("ui.show_notifications", True):
                self._show_notification("Sync Error", f"Error: {str(e)}", error=True)
    
    def _show_notification(self, title, message, error=False):
        """Mostra uma notificação de desktop"""
        try:
            # Verificar plataforma
            import platform
            system = platform.system()
            
            if system == "Windows":
                # Windows - usar win10toast
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(
                        title,
                        message,
                        icon_path=None,
                        duration=5,
                        threaded=True
                    )
                    return
                except ImportError:
                    pass
            
            elif system == "Darwin":  # macOS
                # Usar AppleScript
                try:
                    import subprocess
                    script = f'display notification "{message}" with title "{title}"'
                    subprocess.run(["osascript", "-e", script])
                    return
                except Exception:
                    pass
            
            else:  # Linux e outros
                # Tentar usar notify-send
                try:
                    import subprocess
                    subprocess.run(["notify-send", title, message])
                    return
                except Exception:
                    pass
            
            # Fallback - registrar apenas no log
            self.logger.log(f"Notification: {title} - {message}")
            
        except Exception as e:
            self.logger.log(f"Error showing notification: {str(e)}", "ERROR")

class AutoSyncDialog(tk.Toplevel):
    def __init__(self, parent, auto_sync_manager, config_manager):
        """Inicializa o diálogo de configuração de sincronização automática"""
        super().__init__(parent)
        
        self.title("Automatic Synchronization")
        self.geometry("450x400")
        self.minsize(400, 350)
        self.transient(parent)
        self.grab_set()
        
        self.auto_sync_manager = auto_sync_manager
        self.config = config_manager
        
        # Variáveis para configurações
        self.enabled_var = tk.BooleanVar(value=self.config.get("auto_sync.enabled", False))
        self.interval_var = tk.StringVar(value=str(self.config.get("auto_sync.interval_minutes", 30)))
        self.direction_var = tk.StringVar(value=self.config.get("sync.direction", "bidirectional"))
        self.conflict_var = tk.StringVar(value=self.config.get("sync.auto_resolve_conflicts", "none"))
        self.auto_push_var = tk.BooleanVar(value=self.config.get("sync.auto_push", False))
        
        # Criar widgets
        self.create_widgets()
        
        # Atualizar status
        self.update_status()
        
        # Timer para atualizar o status a cada segundo
        self.after(1000, self.update_status)
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status atual
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(status_frame, text="Auto-sync:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.status_label = ttk.Label(status_frame, text="Disabled")
        self.status_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(status_frame, text="Next sync:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.next_sync_label = ttk.Label(status_frame, text="N/A")
        self.next_sync_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(status_frame, text="Sync count:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.sync_count_label = ttk.Label(status_frame, text="0")
        self.sync_count_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Ações
        action_frame = ttk.Frame(status_frame)
        action_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        self.start_btn = ttk.Button(action_frame, text="Start Now", command=self.start_sync)
        self.start_btn.pack(side=tk.LEFT)
        
        self.stop_btn = ttk.Button(action_frame, text="Stop", command=self.stop_sync)
        self.stop_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        self.force_sync_btn = ttk.Button(action_frame, text="Force Sync Now", command=self.force_sync)
        self.force_sync_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Configurações
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Enable auto-sync
        enable_check = ttk.Checkbutton(settings_frame, text="Enable automatic synchronization", 
                                      variable=self.enabled_var)
        enable_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Interval
        ttk.Label(settings_frame, text="Sync interval (minutes):").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        interval_entry = ttk.Entry(settings_frame, textvariable=self.interval_var, width=10)
        interval_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        # Direction
        ttk.Label(settings_frame, text="Sync direction:").grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        
        direction_frame = ttk.Frame(settings_frame)
        direction_frame.grid(row=2, column=1, sticky=tk.W, pady=(10, 5), padx=(5, 0))
        
        ttk.Radiobutton(direction_frame, text="Bidirectional", variable=self.direction_var, 
                       value="bidirectional").pack(anchor=tk.W)
        ttk.Radiobutton(direction_frame, text="Git to SVN only", variable=self.direction_var, 
                       value="git_to_svn").pack(anchor=tk.W)
        ttk.Radiobutton(direction_frame, text="SVN to Git only", variable=self.direction_var, 
                       value="svn_to_git").pack(anchor=tk.W)
        
        # Conflict resolution
        ttk.Label(settings_frame, text="Conflict resolution:").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        
        conflict_frame = ttk.Frame(settings_frame)
        conflict_frame.grid(row=3, column=1, sticky=tk.W, pady=(10, 5), padx=(5, 0))
        
        ttk.Radiobutton(conflict_frame, text="Manual resolution", variable=self.conflict_var, 
                       value="none").pack(anchor=tk.W)
        ttk.Radiobutton(conflict_frame, text="Always prefer Git", variable=self.conflict_var, 
                       value="git").pack(anchor=tk.W)
        ttk.Radiobutton(conflict_frame, text="Always prefer SVN", variable=self.conflict_var, 
                       value="svn").pack(anchor=tk.W)
        
        # Auto-push
        auto_push_check = ttk.Checkbutton(settings_frame, text="Auto-push to Git after SVN sync", 
                                         variable=self.auto_push_var)
        auto_push_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Botões de ação
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Save", command=self.save_settings).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=(0, 5))
    
    def update_status(self):
        """Atualiza o status exibido no diálogo"""
        if not self.auto_sync_manager:
            return
        
        # Status atual
        if self.auto_sync_manager.enabled and self.auto_sync_manager.sync_thread and self.auto_sync_manager.sync_thread.is_alive():
            self.status_label.config(text="Enabled and running")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="Disabled or stopped")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
        
        # Próxima sincronização
        if self.auto_sync_manager.next_sync_time:
            time_left = self.auto_sync_manager.next_sync_time - datetime.now()
            if time_left.total_seconds() > 0:
                minutes, seconds = divmod(int(time_left.total_seconds()), 60)
                self.next_sync_label.config(text=f"{minutes:02d}:{seconds:02d} (at {self.auto_sync_manager.next_sync_time.strftime('%H:%M:%S')})")
            else:
                self.next_sync_label.config(text="Due now")
        else:
            self.next_sync_label.config(text="N/A")
        
        # Contador de sincronizações
        self.sync_count_label.config(text=str(self.auto_sync_manager.sync_count))
        
        # Atualizar novamente em 1 segundo
        self.after(1000, self.update_status)
    
    def save_settings(self):
        """Salva as configurações"""
        try:
            # Validar intervalo
            interval = int(self.interval_var.get())
            if interval < 1:
                tk.messagebox.showerror("Error", "Sync interval must be at least 1 minute")
                return
            
            # Salvar configurações
            self.config.set("auto_sync.enabled", self.enabled_var.get())
            self.config.set("auto_sync.interval_minutes", interval)
            self.config.set("sync.direction", self.direction_var.get())
            self.config.set("sync.auto_resolve_conflicts", self.conflict_var.get())
            self.config.set("sync.auto_push", self.auto_push_var.get())
            
            # Aplicar alterações
            self.auto_sync_manager.enabled = self.enabled_var.get()
            self.auto_sync_manager.interval = interval
            
            # Reiniciar se necessário
            if self.enabled_var.get():
                self.auto_sync_manager.stop()
                self.auto_sync_manager.start()
            else:
                self.auto_sync_manager.stop()
            
            tk.messagebox.showinfo("Success", "Auto-sync settings saved successfully")
            
        except ValueError:
            tk.messagebox.showerror("Error", "Invalid sync interval. Please enter a number.")
    
    def start_sync(self):
        """Inicia a sincronização automática"""
        self.auto_sync_manager.start()
    
    def stop_sync(self):
        """Para a sincronização automática"""
        self.auto_sync_manager.stop()
    
    def force_sync(self):
        """Força uma sincronização imediata"""
        threading.Thread(target=self.auto_sync_manager._perform_sync, daemon=True).start()