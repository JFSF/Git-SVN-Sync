# -*- coding: utf-8 -*-

import os
import subprocess
from datetime import datetime

class SVNManager:
    def __init__(self, working_dir, logger):
        """Inicializa o gerenciador SVN"""
        self.working_dir = working_dir
        self.logger = logger
        self.svn_url = None
        
    def is_svn_repo(self):
        """Verifica se o diretório é um repositório SVN"""
        return os.path.exists(os.path.join(self.working_dir, '.svn'))
    
    def check_svn_command(self):
        """Verifica se o comando SVN está disponível"""
        try:
            subprocess.run(["svn", "--version"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            self.logger.log("SVN command not found. Please install SVN client.", "ERROR")
            return False
    
    def set_repository_url(self, url):
        """Define a URL do repositório SVN"""
        self.svn_url = url
        
    def checkout(self, url=None, username=None, password=None):
        """Realiza checkout do repositório SVN"""
        if not self.check_svn_command():
            return False, "SVN command not available"
            
        repo_url = url or self.svn_url
        if not repo_url:
            return False, "SVN repository URL not set"
            
        self.logger.log(f"Checking out SVN repository from {repo_url}...")
        
        try:
            cmd = ["svn", "checkout", repo_url, self.working_dir]
            
            # Adicionar credenciais se fornecidas
            if username and password:
                cmd.extend(["--username", username, "--password", password, "--non-interactive"])
                
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(self.working_dir)
            )
            
            if process.returncode == 0:
                self.logger.log("SVN checkout completed successfully", "SUCCESS")
                self.svn_url = repo_url
                return True, "Checkout completed successfully"
            else:
                error_msg = process.stderr.strip()
                self.logger.log(f"SVN checkout failed: {error_msg}", "ERROR")
                return False, error_msg
                
        except Exception as e:
            self.logger.log(f"Error during SVN checkout: {str(e)}", "ERROR")
            return False, str(e)
    
    def get_status(self):
        """Obtém o status do repositório SVN"""
        if not self.check_svn_command():
            return {
                "valid": False,
                "message": "SVN command not available"
            }
            
        if not self.is_svn_repo():
            return {
                "valid": False,
                "message": "Not an SVN working copy"
            }
            
        try:
            process = subprocess.run(
                ["svn", "info"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.working_dir
            )
            
            if process.returncode == 0:
                info_output = process.stdout.strip()
                
                # Extrair informações relevantes
                url = None
                revision = None
                
                for line in info_output.split('\n'):
                    if line.startswith("URL:"):
                        url = line.replace("URL:", "").strip()
                    elif line.startswith("Revision:"):
                        revision = line.replace("Revision:", "").strip()
                
                if url and revision:
                    return {
                        "valid": True,
                        "url": url,
                        "revision": revision,
                        "message": f"Working copy at revision {revision}"
                    }
                else:
                    return {
                        "valid": False,
                        "message": "Could not parse SVN info"
                    }
            else:
                error_msg = process.stderr.strip()
                return {
                    "valid": False,
                    "message": f"SVN error: {error_msg}"
                }
                
        except Exception as e:
            return {
                "valid": False,
                "message": f"Error: {str(e)}"
            }
    
    def get_modified_files(self):
        """Obtém lista de arquivos modificados"""
        if not self.check_svn_command() or not self.is_svn_repo():
            return []
            
        try:
            process = subprocess.run(
                ["svn", "status"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.working_dir
            )
            
            if process.returncode == 0:
                status_output = process.stdout.strip()
                modified_files = []
                
                for line in status_output.split('\n'):
                    if not line.strip():
                        continue
                        
                    status_code = line[0]
                    file_path = line[8:].strip()
                    
                    # Status: A (added), M (modified), D (deleted), ? (unversioned), C (conflict)
                    if status_code in ['A', 'M', 'D', '?', 'C']:
                        modified_files.append({
                            "path": file_path,
                            "type": status_code,
                            "tracked": status_code != '?'
                        })
                
                return modified_files
            else:
                self.logger.log(f"SVN status error: {process.stderr.strip()}", "ERROR")
                return []
                
        except Exception as e:
            self.logger.log(f"Error getting SVN status: {str(e)}", "ERROR")
            return []
    
    def update(self, revision=None):
        """Atualiza o repositório SVN para a última revisão ou revisão específica"""
        if not self.check_svn_command() or not self.is_svn_repo():
            return False, "Not an SVN working copy"
            
        try:
            cmd = ["svn", "update"]
            
            # Atualizar para revisão específica
            if revision:
                cmd.extend(["-r", str(revision)])
                
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.working_dir
            )
            
            if process.returncode == 0:
                update_info = process.stdout.strip()
                self.logger.log(f"SVN update completed: {update_info}", "SUCCESS")
                return True, update_info
            else:
                error_msg = process.stderr.strip()
                self.logger.log(f"SVN update failed: {error_msg}", "ERROR")
                return False, error_msg
                
        except Exception as e:
            self.logger.log(f"Error during SVN update: {str(e)}", "ERROR")
            return False, str(e)
    
    def commit(self, files, message, username=None, password=None):
        """Realiza commit de arquivos para o repositório SVN"""
        if not self.check_svn_command() or not self.is_svn_repo():
            return False, "Not an SVN working copy"
            
        if not files:
            return False, "No files specified for commit"
            
        if not message:
            return False, "Commit message cannot be empty"
            
        try:
            # Adicionar arquivos não versionados primeiro
            for file_path in files:
                # Verificar se o arquivo está não versionado
                status_process = subprocess.run(
                    ["svn", "status", file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=self.working_dir
                )
                
                if status_process.returncode == 0 and status_process.stdout.strip():
                    status_line = status_process.stdout.strip()
                    if status_line.startswith('?'):
                        # Adicionar arquivo
                        add_process = subprocess.run(
                            ["svn", "add", file_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            cwd=self.working_dir
                        )
                        
                        if add_process.returncode == 0:
                            self.logger.log(f"Added file to version control: {file_path}")
                        else:
                            self.logger.log(f"Error adding file {file_path}: {add_process.stderr.strip()}", "ERROR")
            
            # Preparar comando de commit
            cmd = ["svn", "commit"]
            
            # Adicionar arquivos específicos
            cmd.extend(files)
            
            # Adicionar mensagem
            cmd.extend(["-m", message])
            
            # Adicionar credenciais se fornecidas
            if username and password:
                cmd.extend(["--username", username, "--password", password, "--non-interactive"])
            
            # Executar commit
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.working_dir
            )
            
            if process.returncode == 0:
                commit_info = process.stdout.strip()
                self.logger.log(f"SVN commit completed: {commit_info}", "SUCCESS")
                return True, commit_info
            else:
                error_msg = process.stderr.strip()
                self.logger.log(f"SVN commit failed: {error_msg}", "ERROR")
                return False, error_msg
                
        except Exception as e:
            self.logger.log(f"Error during SVN commit: {str(e)}", "ERROR")
            return False, str(e)
            
    def get_diff(self, file_path):
        """Obtém diferenças de um arquivo"""
        if not self.check_svn_command() or not self.is_svn_repo():
            return None
            
        try:
            # Verificar status do arquivo
            status_process = subprocess.run(
                ["svn", "status", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.working_dir
            )
            
            if status_process.returncode != 0:
                self.logger.log(f"Error checking status for {file_path}: {status_process.stderr.strip()}", "ERROR")
                return None
                
            status_line = status_process.stdout.strip()
            if not status_line:
                self.logger.log(f"File {file_path} has no modifications")
                return None
                
            status_code = status_line[0] if status_line else None
            
            # Arquivo não versionado
            if status_code == '?':
                # Ler conteúdo completo
                file_full_path = os.path.join(self.working_dir, file_path)
                if os.path.exists(file_full_path):
                    with open(file_full_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    return {
                        "type": "new_file",
                        "content": content,
                        "diff": None
                    }
                else:
                    return None
            
            # Arquivo modificado, obter diff
            diff_process = subprocess.run(
                ["svn", "diff", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.working_dir
            )
            
            if diff_process.returncode == 0:
                diff_output = diff_process.stdout.strip()
                return {
                    "type": "diff",
                    "content": None,
                    "diff": diff_output
                }
            else:
                self.logger.log(f"Error getting diff for {file_path}: {diff_process.stderr.strip()}", "ERROR")
                return None
                
        except Exception as e:
            self.logger.log(f"Error getting diff for {file_path}: {str(e)}", "ERROR")
            return None