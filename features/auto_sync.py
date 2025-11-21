# -*- coding: utf-8 -*-

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