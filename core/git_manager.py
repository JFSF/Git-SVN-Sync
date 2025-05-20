# -*- coding: utf-8 -*-

import os
import git
from git import GitCommandError

class GitManager:
    def __init__(self, working_dir, logger):
        """Inicializa o gerenciador Git"""
        self.working_dir = working_dir
        self.logger = logger
        self.repo = None
        
        if self.is_git_repo():
            try:
                self.repo = git.Repo(working_dir)
            except Exception as e:
                self.logger.log(f"Error initializing Git repo: {str(e)}", "ERROR")
    
    def is_git_repo(self):
        """Verifica se o diretório é um repositório Git"""
        return os.path.exists(os.path.join(self.working_dir, '.git'))
    
    def init_repo(self, remote_url=None):
        """Inicializa um repositório Git"""
        try:
            if not os.path.exists(self.working_dir):
                os.makedirs(self.working_dir)
                self.logger.log("Created local directory")
            
            if self.is_git_repo():
                self.repo = git.Repo(self.working_dir)
                self.logger.log("Git repository already exists")
                return True
            
            # Inicializar repositório
            self.repo = git.Repo.init(self.working_dir)
            self.logger.log("Initialized empty Git repository")
            
            # Configurar remote se fornecido
            if remote_url:
                self.repo.create_remote('origin', remote_url)
                self.logger.log(f"Added remote 'origin' pointing to {remote_url}")
            
            # Criar .gitignore
            gitignore_path = os.path.join(self.working_dir, '.gitignore')
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, 'w') as f:
                    f.write("# Default gitignore\n*.pyc\n*.swp\n.DS_Store\n__pycache__/\n")
                self.logger.log("Created default .gitignore file")
            
            return True
            
        except Exception as e:
            self.logger.log(f"Error initializing Git repository: {str(e)}", "ERROR")
            return False
    
    def get_status(self):
        """Obtém o status do repositório"""
        if not self.repo:
            return {
                "valid": False,
                "message": "Not a Git repository"
            }
        
        try:
            branch = "Detached" if self.repo.head.is_detached else self.repo.active_branch.name
            status = "Clean" if not self.repo.is_dirty() else "Modified"
            
            # Contar arquivos modificados
            modified_count = 0
            untracked_count = len(self.repo.untracked_files)
            
            for item in self.repo.index.diff(None):
                modified_count += 1
            
            return {
                "valid": True,
                "branch": branch,
                "status": status,
                "modified_count": modified_count,
                "untracked_count": untracked_count,
                "message": f"Branch: {branch}, {status}"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"Error: {str(e)}"
            }
    
    def get_modified_files(self):
        """Obtém lista de arquivos modificados e não rastreados"""
        modified_files = []
        
        if not self.repo:
            return modified_files
        
        try:
            # Arquivos modificados e excluídos (rastreados)
            for item in self.repo.index.diff(None):
                change_type = item.change_type  # A, D, M, R
                modified_files.append({
                    "path": item.a_path,
                    "type": change_type,
                    "tracked": True
                })
            
            # Arquivos não rastreados
            for item in self.repo.untracked_files:
                modified_files.append({
                    "path": item,
                    "type": "?",
                    "tracked": False
                })
            
            return modified_files
            
        except Exception as e:
            self.logger.log(f"Error getting modified files: {str(e)}", "ERROR")
            return []

    def get_diff(self, file_path):
        """Obtém diferenças de um arquivo"""
        if not self.repo:
            return None
        
        try:
            # Verificar se o arquivo é rastreado ou não
            if file_path in self.repo.untracked_files:
                # Arquivo não rastreado - ler conteúdo completo
                with open(os.path.join(self.working_dir, file_path), 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                return {
                    "type": "new_file",
                    "content": content,
                    "diff": None
                }
            else:
                # Arquivo rastreado - obter diff
                diff = self.repo.git.diff(file_path)
                return {
                    "type": "diff",
                    "content": None,
                    "diff": diff
                }
        except Exception as e:
            self.logger.log(f"Error getting diff for {file_path}: {str(e)}", "ERROR")
            return None
    
    def commit(self, files, message, author=None):
        """Realiza commit de arquivos"""
        if not self.repo:
            return False, "Not a Git repository"
        
        try:
            # Adicionar arquivos selecionados
            for file_path in files:
                self.repo.git.add(file_path)
            
            # Configurar autor se fornecido
            if author:
                commit = self.repo.index.commit(message, author=author)
            else:
                commit = self.repo.index.commit(message)
            
            self.logger.log(f"Committed {len(files)} files with message: {message}", "SUCCESS")
            self.logger.log(f"Commit hash: {commit.hexsha}")
            
            return True, commit.hexsha
            
        except Exception as e:
            self.logger.log(f"Error committing files: {str(e)}", "ERROR")
            return False, str(e)
    
    def sync_with_remote(self, remote_name="origin", branch_name=None):
        """Sincroniza com o repositório remoto (fetch, pull)"""
        if not self.repo:
            return False, "Not a Git repository"
        
        try:
            # Verificar se remote existe
            if remote_name not in [r.name for r in self.repo.remotes]:
                return False, f"Remote '{remote_name}' not found"
            
            remote = self.repo.remotes[remote_name]
            
            # Fetch
            self.logger.log(f"Fetching from {remote_name}...")
            fetch_info = remote.fetch()
            self.logger.log(f"Fetch completed: {len(fetch_info)} refs updated")
            
            # Pull (se branch_name for None, usa a branch atual)
            if not self.repo.head.is_detached:
                current_branch = branch_name or self.repo.active_branch.name
                self.logger.log(f"Pulling from {remote_name}/{current_branch}...")
                
                # Verificar e stash mudanças locais se necessário
                if self.repo.is_dirty():
                    self.logger.log("Stashing local changes...")
                    self.repo.git.stash()
                    stashed = True
                else:
                    stashed = False
                
                # Pull
                pull_info = remote.pull()
                self.logger.log(f"Pull completed")
                
                # Recuperar stash se necessário
                if stashed and self.repo.git.stash('list'):
                    self.logger.log("Applying stashed changes...")
                    self.repo.git.stash('pop')
                    self.logger.log("Stashed changes applied")
                
            return True, "Synchronization completed successfully"
            
        except Exception as e:
            self.logger.log(f"Error syncing with remote: {str(e)}", "ERROR")
            return False, str(e)
    
    def get_branches(self):
        """Obtém lista de branches locais e remotas"""
        if not self.repo:
            return [], []
        
        try:
            local_branches = [b.name for b in self.repo.branches]
            remote_branches = [b.name for b in self.repo.remote().refs]
            
            return local_branches, remote_branches
            
        except Exception as e:
            self.logger.log(f"Error getting branches: {str(e)}", "ERROR")
            return [], []
    
    def create_branch(self, branch_name, checkout=True):
        """Cria uma nova branch"""
        if not self.repo:
            return False, "Not a Git repository"
        
        try:
            # Verificar se a branch já existe
            if branch_name in [b.name for b in self.repo.branches]:
                return False, f"Branch '{branch_name}' already exists"
            
            # Criar branch
            new_branch = self.repo.create_head(branch_name)
            
            # Checkout se solicitado
            if checkout:
                new_branch.checkout()
                self.logger.log(f"Created and switched to branch '{branch_name}'", "SUCCESS")
            else:
                self.logger.log(f"Created branch '{branch_name}'", "SUCCESS")
            
            return True, f"Branch '{branch_name}' created successfully"
            
        except Exception as e:
            self.logger.log(f"Error creating branch: {str(e)}", "ERROR")
            return False, str(e)