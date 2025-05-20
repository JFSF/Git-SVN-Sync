# -*- coding: utf-8 -*-

import os
import shutil
import time
from datetime import datetime
import tempfile

class SyncManager:
    def __init__(self, git_manager, svn_manager, logger, config_manager):
        """Inicializa o gerenciador de sincronização"""
        self.git_manager = git_manager
        self.svn_manager = svn_manager
        self.logger = logger
        self.config = config_manager
        self.working_dir = git_manager.working_dir if git_manager else None
        
    def check_prerequisites(self):
        """Verifica se todos os pré-requisitos para sincronização estão disponíveis"""
        if not self.git_manager or not self.svn_manager:
            return False, "Git or SVN manager not initialized"
            
        if not self.working_dir or not os.path.exists(self.working_dir):
            return False, "Working directory not set or does not exist"
            
        # Verificar se é repositório Git
        if not self.git_manager.is_git_repo():
            return False, "Not a Git repository"
            
        # Verificar se é repositório SVN
        if not self.svn_manager.is_svn_repo():
            return False, "Not an SVN working copy"
            
        return True, "Prerequisites met"
    
    def sync_git_to_svn(self):
        """Sincroniza alterações do Git para o SVN"""
        self.logger.log("\n=== Synchronizing Git to SVN ===")
        
        # Verificar pré-requisitos
        prereq_met, message = self.check_prerequisites()
        if not prereq_met:
            self.logger.log(f"Cannot synchronize: {message}", "ERROR")
            return False, message
            
        try:
            # 1. Atualizar do Git remoto primeiro
            self.logger.log("Updating from Git remote...")
            git_success, git_message = self.git_manager.sync_with_remote()
            
            if not git_success:
                self.logger.log(f"Error updating from Git: {git_message}", "ERROR")
                return False, f"Git update failed: {git_message}"
                
            self.logger.log("Git update completed successfully")
            
            # 2. Obter lista de arquivos modificados no Git
            git_files = self.git_manager.get_modified_files()
            
            if not git_files:
                self.logger.log("No files modified in Git repository", "WARNING")
                return True, "No changes to synchronize"
                
            # 3. Atualizar do SVN para garantir que estamos trabalhando com a versão mais recente
            self.logger.log("Updating from SVN remote...")
            svn_update_success, svn_update_message = self.svn_manager.update()
            
            if not svn_update_success:
                self.logger.log(f"Error updating from SVN: {svn_update_message}", "ERROR")
                return False, f"SVN update failed: {svn_update_message}"
                
            self.logger.log("SVN update completed successfully")
            
            # 4. Comparar arquivos modificados para sincronizar apenas o que foi alterado no Git
            files_to_sync = []
            
            for git_file in git_files:
                # Verificar se o arquivo existe fisicamente
                file_path = os.path.join(self.working_dir, git_file["path"])
                
                if git_file["type"] == "D":  # Arquivo deletado no Git
                    files_to_sync.append(git_file["path"])
                elif os.path.exists(file_path):  # Arquivo adicionado ou modificado
                    files_to_sync.append(git_file["path"])
            
            if not files_to_sync:
                self.logger.log("No files to synchronize with SVN", "WARNING")
                return True, "No changes to synchronize"
                
            # 5. Commitar alterações no SVN
            self.logger.log(f"Committing {len(files_to_sync)} files to SVN...")
            
            # Gerar mensagem de commit com base na configuração
            sync_message = self.config.get("sync.commit_message", "Synchronized changes from Git to SVN")
            sync_message += f"\nGit-SVN-Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Usar credenciais do SVN se disponíveis
            svn_username = self.config.get("credentials.svn.username")
            svn_password = self.config.get("credentials.svn.password")
            
            svn_commit_success, svn_commit_message = self.svn_manager.commit(
                files_to_sync, 
                sync_message,
                username=svn_username,
                password=svn_password
            )
            
            if svn_commit_success:
                self.logger.log(f"SVN commit completed successfully: {svn_commit_message}", "SUCCESS")
                return True, "Synchronization completed successfully"
            else:
                self.logger.log(f"SVN commit failed: {svn_commit_message}", "ERROR")
                return False, f"SVN commit failed: {svn_commit_message}"
                
        except Exception as e:
            self.logger.log(f"Error during Git to SVN synchronization: {str(e)}", "ERROR")
            return False, str(e)
    
    def sync_svn_to_git(self):
        """Sincroniza alterações do SVN para o Git"""
        self.logger.log("\n=== Synchronizing SVN to Git ===")
        
        # Verificar pré-requisitos
        prereq_met, message = self.check_prerequisites()
        if not prereq_met:
            self.logger.log(f"Cannot synchronize: {message}", "ERROR")
            return False, message
            
        try:
            # 1. Atualizar do SVN remoto primeiro
            self.logger.log("Updating from SVN remote...")
            svn_success, svn_message = self.svn_manager.update()
            
            if not svn_success:
                self.logger.log(f"Error updating from SVN: {svn_message}", "ERROR")
                return False, f"SVN update failed: {svn_message}"
                
            self.logger.log("SVN update completed successfully")
            
            # 2. Obter lista de arquivos modificados no SVN
            svn_files = self.svn_manager.get_modified_files()
            
            if not svn_files:
                self.logger.log("No files modified in SVN repository", "WARNING")
                return True, "No changes to synchronize"
                
            # 3. Verificar se há alterações conflitantes no Git
            git_status = self.git_manager.get_status()
            
            if git_status["valid"] and "status" in git_status and git_status["status"] == "Modified":
                self.logger.log("Git repository has local modifications", "WARNING")
                
                # Opção para fazer stash das alterações (se configurado)
                if self.config.get("sync.auto_stash", False):
                    self.logger.log("Auto-stashing Git changes...")
                    try:
                        self.git_manager.repo.git.stash()
                        self.logger.log("Git changes stashed successfully")
                        stashed = True
                    except Exception as e:
                        self.logger.log(f"Error stashing Git changes: {str(e)}", "ERROR")
                        return False, f"Error stashing Git changes: {str(e)}"
                else:
                    self.logger.log("Git has local changes that may conflict with SVN updates", "WARNING")
                    return False, "Git has uncommitted changes. Commit or stash them first."
            else:
                stashed = False
            
            # 4. Preparar arquivos para commit no Git
            files_to_sync = []
            
            for svn_file in svn_files:
                # Verificar se o arquivo existe fisicamente
                file_path = os.path.join(self.working_dir, svn_file["path"])
                
                if svn_file["type"] == "D":  # Arquivo deletado no SVN
                    files_to_sync.append(svn_file["path"])
                elif os.path.exists(file_path):  # Arquivo adicionado ou modificado
                    files_to_sync.append(svn_file["path"])
            
            if not files_to_sync:
                # Restaurar stash se necessário
                if stashed:
                    self.logger.log("Restoring stashed Git changes...")
                    try:
                        self.git_manager.repo.git.stash("pop")
                        self.logger.log("Git stash restored successfully")
                    except Exception as e:
                        self.logger.log(f"Error restoring Git stash: {str(e)}", "ERROR")
                
                self.logger.log("No files to synchronize with Git", "WARNING")
                return True, "No changes to synchronize"
                
            # 5. Commitar alterações no Git
            self.logger.log(f"Committing {len(files_to_sync)} files to Git...")
            
            # Gerar mensagem de commit com base na configuração
            sync_message = self.config.get("sync.commit_message", "Synchronized changes from SVN to Git")
            sync_message += f"\nGit-SVN-Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            git_commit_success, git_commit_message = self.git_manager.commit(
                files_to_sync, 
                sync_message
            )
            
            if git_commit_success:
                self.logger.log(f"Git commit completed successfully: {git_commit_message}", "SUCCESS")
                
                # 6. Enviar alterações para o Git remoto (se configurado)
                if self.config.get("sync.auto_push", False):
                    self.logger.log("Pushing changes to Git remote...")
                    try:
                        self.git_manager.repo.remotes.origin.push()
                        self.logger.log("Git push completed successfully", "SUCCESS")
                    except Exception as e:
                        self.logger.log(f"Error pushing to Git remote: {str(e)}", "ERROR")
                        return False, f"Git commit succeeded but push failed: {str(e)}"
                
                # 7. Restaurar stash se necessário
                if stashed:
                    self.logger.log("Restoring stashed Git changes...")
                    try:
                        self.git_manager.repo.git.stash("pop")
                        self.logger.log("Git stash restored successfully")
                    except Exception as e:
                        self.logger.log(f"Error restoring Git stash: {str(e)}", "ERROR")
                
                return True, "Synchronization completed successfully"
            else:
                # Restaurar stash se necessário
                if stashed:
                    self.logger.log("Restoring stashed Git changes...")
                    try:
                        self.git_manager.repo.git.stash("pop")
                        self.logger.log("Git stash restored successfully")
                    except Exception as e:
                        self.logger.log(f"Error restoring Git stash: {str(e)}", "ERROR")
                
                self.logger.log(f"Git commit failed: {git_commit_message}", "ERROR")
                return False, f"Git commit failed: {git_commit_message}"
                
        except Exception as e:
            self.logger.log(f"Error during SVN to Git synchronization: {str(e)}", "ERROR")
            return False, str(e)
    
    def bidirectional_sync(self):
        """Sincroniza em ambas as direções com detecção de conflitos"""
        self.logger.log("\n=== Starting Bidirectional Synchronization ===")
        
        # Verificar pré-requisitos
        prereq_met, message = self.check_prerequisites()
        if not prereq_met:
            self.logger.log(f"Cannot synchronize: {message}", "ERROR")
            return False, message
            
        try:
            # 1. Criar cópia temporária do diretório de trabalho para detecção de conflitos
            temp_dir = tempfile.mkdtemp(prefix="git_svn_sync_")
            self.logger.log(f"Created temporary directory for conflict detection: {temp_dir}")
            
            # Copiar todo o diretório (exceto .git e .svn)
            for item in os.listdir(self.working_dir):
                if item in ['.git', '.svn']:
                    continue
                    
                source = os.path.join(self.working_dir, item)
                destination = os.path.join(temp_dir, item)
                
                if os.path.isdir(source):
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)
            
            # 2. Atualizar do Git remoto
            self.logger.log("Updating from Git remote...")
            git_success, git_message = self.git_manager.sync_with_remote()
            
            if not git_success:
                self.logger.log(f"Error updating from Git: {git_message}", "ERROR")
                # Limpar temporário e sair
                shutil.rmtree(temp_dir)
                return False, f"Git update failed: {git_message}"
                
            self.logger.log("Git update completed successfully")
            
            # 3. Detectar alterações do Git (comparando com o temporário)
            git_changes = self._detect_changes(temp_dir, self.working_dir)
            self.logger.log(f"Detected {len(git_changes)} files changed by Git update")
            
            # 4. Atualizar do SVN remoto
            self.logger.log("Updating from SVN remote...")
            svn_success, svn_message = self.svn_manager.update()
            
            if not svn_success:
                self.logger.log(f"Error updating from SVN: {svn_message}", "ERROR")
                # Limpar temporário e sair
                shutil.rmtree(temp_dir)
                return False, f"SVN update failed: {svn_message}"
                
            self.logger.log("SVN update completed successfully")
            
            # 5. Detectar alterações finais (após ambas as atualizações)
            final_changes = self._detect_changes(temp_dir, self.working_dir)
            self.logger.log(f"Detected {len(final_changes)} files changed after both updates")
            
            # 6. Detectar possíveis conflitos
            svn_changes = []
            conflicts = []
            
            for file_path in final_changes:
                if file_path in git_changes:
                    # Possível conflito - alterado por ambos
                    conflicts.append(file_path)
                else:
                    # Alterado apenas pelo SVN
                    svn_changes.append(file_path)
            
            # Limpar diretório temporário
            shutil.rmtree(temp_dir)
            self.logger.log("Cleaned up temporary directory")
            
            # 7. Relatar alterações e conflitos
            self.logger.log(f"Git changes: {len(git_changes)} files")
            self.logger.log(f"SVN changes: {len(svn_changes)} files")
            
            if conflicts:
                self.logger.log(f"Detected {len(conflicts)} potential conflicts", "WARNING")
                for file_path in conflicts:
                    self.logger.log(f"Conflict in file: {file_path}", "WARNING")
                
                # Verificar configuração de resolução automática
                auto_resolve = self.config.get("sync.auto_resolve_conflicts", "none")
                
                if auto_resolve == "git":
                    self.logger.log("Auto-resolving conflicts in favor of Git...")
                    # As mudanças do Git já estão aplicadas, só precisamos adicionar ao controle do SVN
                    success, message = self.svn_manager.commit(
                        conflicts,
                        "Auto-resolved conflicts in favor of Git"
                    )
                    if success:
                        self.logger.log("Conflicts resolved in favor of Git", "SUCCESS")
                    else:
                        self.logger.log(f"Error resolving conflicts: {message}", "ERROR")
                    
                elif auto_resolve == "svn":
                    self.logger.log("Auto-resolving conflicts in favor of SVN...")
                    # Reverter para versão do SVN e commitar no Git
                    success, message = self.git_manager.commit(
                        conflicts,
                        "Auto-resolved conflicts in favor of SVN"
                    )
                    if success:
                        self.logger.log("Conflicts resolved in favor of SVN", "SUCCESS")
                    else:
                        self.logger.log(f"Error resolving conflicts: {message}", "ERROR")
                
                else:  # "none" ou outro valor
                    self.logger.log("Manual conflict resolution required", "WARNING")
                    return False, "Synchronization encountered conflicts that need manual resolution"
            
            # 8. Se não houver conflitos não resolvidos, commitar alterações
            if git_changes and not conflicts:
                # Commitar no SVN as mudanças do Git
                self.logger.log("Committing Git changes to SVN...")
                svn_commit_success, svn_commit_message = self.svn_manager.commit(
                    git_changes,
                    "Synchronized changes from Git"
                )
                
                if svn_commit_success:
                    self.logger.log("SVN commit completed successfully", "SUCCESS")
                else:
                    self.logger.log(f"SVN commit failed: {svn_commit_message}", "ERROR")
            
            if svn_changes and not conflicts:
                # Commitar no Git as mudanças do SVN
                self.logger.log("Committing SVN changes to Git...")
                git_commit_success, git_commit_message = self.git_manager.commit(
                    svn_changes,
                    "Synchronized changes from SVN"
                )
                
                if git_commit_success:
                    self.logger.log("Git commit completed successfully", "SUCCESS")
                    
                    # Push para Git se configurado
                    if self.config.get("sync.auto_push", False):
                        self.logger.log("Pushing changes to Git remote...")
                        try:
                            self.git_manager.repo.remotes.origin.push()
                            self.logger.log("Git push completed successfully", "SUCCESS")
                        except Exception as e:
                            self.logger.log(f"Error pushing to Git remote: {str(e)}", "ERROR")
                else:
                    self.logger.log(f"Git commit failed: {git_commit_message}", "ERROR")
            
            self.logger.log("Synchronization completed successfully", "SUCCESS")
            return True, "Bidirectional synchronization completed successfully"
            
        except Exception as e:
            self.logger.log(f"Error during bidirectional synchronization: {str(e)}", "ERROR")
            return False, str(e)
    
    def _detect_changes(self, base_dir, compare_dir):
        """Detecta arquivos modificados entre dois diretórios"""
        changes = []
        
        for root, dirs, files in os.walk(compare_dir):
            # Ignorar diretórios .git e .svn
            if '.git' in dirs:
                dirs.remove('.git')
            if '.svn' in dirs:
                dirs.remove('.svn')
            
            # Path relativo para comparação
            rel_path = os.path.relpath(root, compare_dir)
            base_path = os.path.join(base_dir, rel_path) if rel_path != '.' else base_dir
            
            # Verificar cada arquivo
            for file in files:
                compare_file = os.path.join(root, file)
                base_file = os.path.join(base_path, file)
                
                # Obter path relativo para o arquivo
                rel_file_path = os.path.relpath(compare_file, compare_dir)
                
                # Verificar se o arquivo existe no diretório base
                if not os.path.exists(base_file):
                    # Arquivo novo ou deletado
                    changes.append(rel_file_path)
                    continue
                
                # Comparar conteúdo
                try:
                    with open(base_file, 'rb') as f1, open(compare_file, 'rb') as f2:
                        if f1.read() != f2.read():
                            changes.append(rel_file_path)
                except Exception:
                    # Erro ao comparar, considerar como alterado
                    changes.append(rel_file_path)
        
        return changes