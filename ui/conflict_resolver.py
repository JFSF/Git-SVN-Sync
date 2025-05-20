# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import os
import difflib
from itertools import zip_longest

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_for_filename, TextLexer
    from pygments.formatters import HtmlFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

class ConflictResolver(tk.Toplevel):
    def __init__(self, parent, file_path, working_dir, git_manager, svn_manager, logger):
        """Inicializa o resolvedor de conflitos"""
        super().__init__(parent)
        
        self.file_path = file_path
        self.working_dir = working_dir
        self.git_manager = git_manager
        self.svn_manager = svn_manager
        self.logger = logger
        
        self.title(f"Resolve Conflict: {file_path}")
        self.geometry("900x700")
        self.minsize(800, 600)
        self.transient(parent)
        self.grab_set()
        
        # Estado para guardar resultado
        self.result = None  # pode ser "git", "svn", "merged", ou None (cancelado)
        self.merged_content = None
        
        # Conteúdo dos arquivos
        self.git_content = None
        self.svn_content = None
        self.base_content = None
        
        # Obter conteúdo dos arquivos
        self._load_file_versions()
        
        # Criar widgets
        self.create_widgets()
        self.load_diff()
    
    def _load_file_versions(self):
        """Carrega as diferentes versões do arquivo"""
        file_full_path = os.path.join(self.working_dir, self.file_path)
        
        try:
            # Versão local/atual
            with open(file_full_path, 'r', encoding='utf-8', errors='replace') as f:
                self.current_content = f.read()
            
            # Versão Git (versão HEAD)
            try:
                if self.git_manager and self.git_manager.repo:
                    git_content = self.git_manager.repo.git.show(f"HEAD:{self.file_path}")
                    self.git_content = git_content
                else:
                    self.git_content = "Git content not available"
            except Exception as e:
                self.logger.log(f"Error getting Git version: {str(e)}", "ERROR")
                self.git_content = "Error: Git content not available"
            
            # Versão SVN (versão do repositório)
            try:
                if self.svn_manager and self.svn_manager.is_svn_repo():
                    # Usar SVN cat para obter a versão do repositório
                    import subprocess
                    process = subprocess.run(
                        ["svn", "cat", self.file_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=self.working_dir
                    )
                    
                    if process.returncode == 0:
                        self.svn_content = process.stdout
                    else:
                        self.svn_content = "SVN content not available"
                else:
                    self.svn_content = "SVN content not available"
            except Exception as e:
                self.logger.log(f"Error getting SVN version: {str(e)}", "ERROR")
                self.svn_content = "Error: SVN content not available"
            
            # Versão base (versão ancestral comum)
            # Para simplificar, usamos uma das versões
            self.base_content = self.git_content
            
        except Exception as e:
            self.logger.log(f"Error loading file versions: {str(e)}", "ERROR")
    
    def create_widgets(self):
        """Cria os widgets do resolvedor de conflitos"""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Visão três painéis
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Painel Git
        git_frame = ttk.LabelFrame(paned_window, text="Git Version")
        
        git_scroll = ttk.Scrollbar(git_frame, orient=tk.VERTICAL)
        git_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.git_text = tk.Text(git_frame, wrap=tk.NONE, yscrollcommand=git_scroll.set)
        self.git_text.pack(fill=tk.BOTH, expand=True)
        git_scroll.config(command=self.git_text.yview)
        
        # Painel SVN
        svn_frame = ttk.LabelFrame(paned_window, text="SVN Version")
        
        svn_scroll = ttk.Scrollbar(svn_frame, orient=tk.VERTICAL)
        svn_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.svn_text = tk.Text(svn_frame, wrap=tk.NONE, yscrollcommand=svn_scroll.set)
        self.svn_text.pack(fill=tk.BOTH, expand=True)
        svn_scroll.config(command=self.svn_text.yview)
        
        # Painel de Mesclagem
        merged_frame = ttk.LabelFrame(paned_window, text="Merged Result")
        
        merged_scroll = ttk.Scrollbar(merged_frame, orient=tk.VERTICAL)
        merged_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.merged_text = tk.Text(merged_frame, wrap=tk.NONE, yscrollcommand=merged_scroll.set)
        self.merged_text.pack(fill=tk.BOTH, expand=True)
        merged_scroll.config(command=self.merged_text.yview)
        
        # Adicionar painéis ao PanedWindow
        paned_window.add(git_frame, weight=1)
        paned_window.add(svn_frame, weight=1)
        paned_window.add(merged_frame, weight=1)
        
        # Botões de escolha/ação
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="Use Git Version", 
                 command=self.use_git_version).pack(side=tk.LEFT)
        
        ttk.Button(action_frame, text="Use SVN Version", 
                 command=self.use_svn_version).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="Auto-Merge", 
                 command=self.auto_merge).pack(side=tk.LEFT)
        
        ttk.Button(action_frame, text="Save Merged", 
                 command=self.save_merged).pack(side=tk.RIGHT)
        
        ttk.Button(action_frame, text="Cancel", 
                 command=self.cancel).pack(side=tk.RIGHT, padx=5)
    
    def load_diff(self):
        """Carrega o conteúdo nos painéis de texto"""
        # Limpar painéis
        self.git_text.delete(1.0, tk.END)
        self.svn_text.delete(1.0, tk.END)
        self.merged_text.delete(1.0, tk.END)
        
        # Configurar tags para estilo
        self.git_text.tag_configure("diff_add", background="#ccffcc")
        self.git_text.tag_configure("diff_del", background="#ffcccc")
        
        self.svn_text.tag_configure("diff_add", background="#ccffcc")
        self.svn_text.tag_configure("diff_del", background="#ffcccc")
        
        self.merged_text.tag_configure("conflict", background="#ffffcc")
        
        # Inserir conteúdo nos painéis Git e SVN
        if self.git_content:
            self.git_text.insert(tk.END, self.git_content)
        
        if self.svn_content:
            self.svn_text.insert(tk.END, self.svn_content)
        
        # Destaque das diferenças
        self._highlight_differences()
        
        # Criar mesclagem inicial
        self.auto_merge()
    
    def _highlight_differences(self):
        """Destaca as diferenças entre as versões Git e SVN"""
        if not self.git_content or not self.svn_content:
            return
            
        # Dividir conteúdo em linhas
        git_lines = self.git_content.splitlines()
        svn_lines = self.svn_content.splitlines()
        
        # Obter sequência de operações para transformar git_lines em svn_lines
        matcher = difflib.SequenceMatcher(None, git_lines, svn_lines)
        
        # Aplicar tags para destacar diferenças no Git
        self.git_text.delete(1.0, tk.END)
        line_num = 1
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Linhas iguais
                for line in git_lines[i1:i2]:
                    self.git_text.insert(tk.END, line + "\n")
                    line_num += 1
            elif tag == 'delete':
                # Linhas presentes apenas no Git
                for line in git_lines[i1:i2]:
                    self.git_text.insert(tk.END, line + "\n", "diff_del")
                    line_num += 1
            elif tag == 'insert':
                # Linhas ausentes no Git (presentes apenas no SVN)
                # Nada a fazer aqui para o painel Git
                pass
            elif tag == 'replace':
                # Linhas diferentes em ambos
                for line in git_lines[i1:i2]:
                    self.git_text.insert(tk.END, line + "\n", "diff_del")
                    line_num += 1
        
        # Aplicar tags para destacar diferenças no SVN
        self.svn_text.delete(1.0, tk.END)
        line_num = 1
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Linhas iguais
                for line in svn_lines[j1:j2]:
                    self.svn_text.insert(tk.END, line + "\n")
                    line_num += 1
            elif tag == 'delete':
                # Linhas presentes apenas no Git (ausentes no SVN)
                # Nada a fazer aqui para o painel SVN
                pass
            elif tag == 'insert':
                # Linhas presentes apenas no SVN
                for line in svn_lines[j1:j2]:
                    self.svn_text.insert(tk.END, line + "\n", "diff_add")
                    line_num += 1
            elif tag == 'replace':
                # Linhas diferentes em ambos
                for line in svn_lines[j1:j2]:
                    self.svn_text.insert(tk.END, line + "\n", "diff_add")
                    line_num += 1
    
    def use_git_version(self):
        """Usa a versão Git como resultado final"""
        self.merged_text.delete(1.0, tk.END)
        self.merged_text.insert(tk.END, self.git_content)
        self.merged_content = self.git_content
        self.result = "git"
    
    def use_svn_version(self):
        """Usa a versão SVN como resultado final"""
        self.merged_text.delete(1.0, tk.END)
        self.merged_text.insert(tk.END, self.svn_content)
        self.merged_content = self.svn_content
        self.result = "svn"
    
    def auto_merge(self):
        """Tenta realizar uma mesclagem automática"""
        if not self.git_content or not self.svn_content or not self.base_content:
            return
            
        # Dividir conteúdo em linhas
        git_lines = self.git_content.splitlines()
        svn_lines = self.svn_content.splitlines()
        base_lines = self.base_content.splitlines()
        
        # Usar o algoritmo de três vias
        merged_lines = []
        has_conflicts = False
        
        # Comparar base com Git e SVN
        git_matcher = difflib.SequenceMatcher(None, base_lines, git_lines)
        svn_matcher = difflib.SequenceMatcher(None, base_lines, svn_lines)
        
        git_opcodes = git_matcher.get_opcodes()
        svn_opcodes = svn_matcher.get_opcodes()
        
        # Mapear alterações em relação à base
        git_changes = {}
        svn_changes = {}
        
        for tag, i1, i2, j1, j2 in git_opcodes:
            if tag != 'equal':
                for i in range(i1, i2):
                    git_changes[i] = (tag, j1, j2)
        
        for tag, i1, i2, j1, j2 in svn_opcodes:
            if tag != 'equal':
                for i in range(i1, i2):
                    svn_changes[i] = (tag, j1, j2)
        
        # Construir resultado mesclado
        for i, base_line in enumerate(base_lines):
            git_change = git_changes.get(i)
            svn_change = svn_changes.get(i)
            
            if git_change and not svn_change:
                # Apenas Git alterou esta linha
                tag, j1, j2 = git_change
                if tag == 'replace' or tag == 'delete':
                    # Usar versão do Git (ou remover)
                    if j1 < j2:
                        merged_lines.extend(git_lines[j1:j2])
                elif tag == 'insert':
                    # Não deveria acontecer com uma única linha
                    pass
            
            elif svn_change and not git_change:
                # Apenas SVN alterou esta linha
                tag, j1, j2 = svn_change
                if tag == 'replace' or tag == 'delete':
                    # Usar versão do SVN (ou remover)
                    if j1 < j2:
                        merged_lines.extend(svn_lines[j1:j2])
                elif tag == 'insert':
                    # Não deveria acontecer com uma única linha
                    pass
            
            elif git_change and svn_change:
                # Ambos alteraram - possível conflito
                git_tag, git_j1, git_j2 = git_change
                svn_tag, svn_j1, svn_j2 = svn_change
                
                if git_tag == 'delete' and svn_tag == 'delete':
                    # Ambos removeram - sem conflito
                    pass
                else:
                    # Conflito - adicionar marcadores
                    merged_lines.append("<<<<<<< GIT")
                    if git_j1 < git_j2:
                        merged_lines.extend(git_lines[git_j1:git_j2])
                    merged_lines.append("=======")
                    if svn_j1 < svn_j2:
                        merged_lines.extend(svn_lines[svn_j1:svn_j2])
                    merged_lines.append(">>>>>>> SVN")
                    has_conflicts = True
            
            else:
                # Nenhum alterou - usar linha base
                merged_lines.append(base_line)
        
        # Adicionar linhas inseridas no final
        # (Simplificação - pode não capturar todas as inserções)
        
        # Exibir resultado mesclado
        self.merged_text.delete(1.0, tk.END)
        merged_content = "\n".join(merged_lines)
        self.merged_text.insert(tk.END, merged_content)
        
        # Destacar conflitos
        if has_conflicts:
            self._highlight_conflicts()
            self.logger.log(f"Merge conflicts found in {self.file_path}", "WARNING")
        else:
            self.logger.log(f"Auto-merge successful for {self.file_path}", "SUCCESS")
        
        self.merged_content = merged_content
        self.result = "merged" if not has_conflicts else None
    
    def _highlight_conflicts(self):
        """Destaca as áreas de conflito no texto mesclado"""
        content = self.merged_text.get(1.0, tk.END)
        start_pos = "1.0"
        
        while True:
            conflict_start = self.merged_text.search("<<<<<<< GIT", start_pos, tk.END)
            if not conflict_start:
                break
                
            conflict_end = self.merged_text.search(">>>>>>> SVN", conflict_start, tk.END)
            if not conflict_end:
                break
                
            # Adicionar tag até o final da linha de conflito
            conflict_end_line = self.merged_text.index(f"{conflict_end} lineend")
            self.merged_text.tag_add("conflict", conflict_start, conflict_end_line)
            
            # Avançar para o próximo conflito
            start_pos = conflict_end_line
    
    def save_merged(self):
        """Salva o resultado mesclado"""
        self.merged_content = self.merged_text.get(1.0, tk.END)
        
        if "<<<<<<< GIT" in self.merged_content:
            if not tk.messagebox.askyesno("Save With Conflicts", 
                                       "The merged result still contains conflict markers. Save anyway?"):
                return
        
        self.result = "merged"
        self.destroy()
    
    def cancel(self):
        """Cancela a resolução de conflito"""
        self.result = None
        self.destroy()