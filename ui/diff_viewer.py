# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import os
import re
import difflib

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_for_filename, TextLexer
    from pygments.formatters import HtmlFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

class DiffViewer(tk.Toplevel):
    def __init__(self, parent, title, file_path, diff_data, mode="side_by_side"):
        """Inicializa o visualizador de diferenças"""
        super().__init__(parent)
        
        self.title(title or "Diff Viewer")
        self.geometry("900x600")
        self.minsize(700, 400)
        
        self.file_path = file_path
        self.diff_data = diff_data
        self.mode = mode  # side_by_side ou unified
        
        self.create_widgets()
        self.display_diff()
    
    def create_widgets(self):
        """Cria os widgets do visualizador"""
        # Frame principal
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barra de ferramentas
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # Botões de modo de visualização
        side_by_side_btn = ttk.Button(toolbar, text="Side by Side", 
                                     command=lambda: self.change_mode("side_by_side"))
        side_by_side_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        unified_btn = ttk.Button(toolbar, text="Unified", 
                               command=lambda: self.change_mode("unified"))
        unified_btn.pack(side=tk.LEFT)
        
        # Frame para visualização
        self.view_frame = ttk.Frame(main_frame)
        self.view_frame.pack(fill=tk.BOTH, expand=True)
        
        if self.mode == "side_by_side":
            # Visão lado a lado
            self.side_by_side_view()
        else:
            # Visão unificada
            self.unified_view()
    
    def side_by_side_view(self):
        """Configurar visão lado a lado"""
        # Limpar frame
        for widget in self.view_frame.winfo_children():
            widget.destroy()
        
        # Criar layout de dois painéis
        paned = ttk.PanedWindow(self.view_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Painel esquerdo (versão antiga)
        left_frame = ttk.Frame(paned)
        ttk.Label(left_frame, text="Original").pack(anchor="w")
        
        left_scroll_y = ttk.Scrollbar(left_frame, orient=tk.VERTICAL)
        left_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        left_scroll_x = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL)
        left_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.left_text = tk.Text(left_frame, wrap=tk.NONE, 
                                yscrollcommand=left_scroll_y.set,
                                xscrollcommand=left_scroll_x.set)
        self.left_text.pack(fill=tk.BOTH, expand=True)
        left_scroll_y.config(command=self.left_text.yview)
        left_scroll_x.config(command=self.left_text.xview)
        
        # Painel direito (versão nova)
        right_frame = ttk.Frame(paned)
        ttk.Label(right_frame, text="Modified").pack(anchor="w")
        
        right_scroll_y = ttk.Scrollbar(right_frame, orient=tk.VERTICAL)
        right_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        right_scroll_x = ttk.Scrollbar(right_frame, orient=tk.HORIZONTAL)
        right_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.right_text = tk.Text(right_frame, wrap=tk.NONE, 
                                 yscrollcommand=right_scroll_y.set,
                                 xscrollcommand=right_scroll_x.set)
        self.right_text.pack(fill=tk.BOTH, expand=True)
        right_scroll_y.config(command=self.right_text.yview)
        right_scroll_x.config(command=self.right_text.xview)
        
        # Sincronizar rolagem
        def sync_scroll(*args):
            self.right_text.yview_moveto(args[0])
        self.left_text.yview_moveto = sync_scroll
        
        def sync_scroll2(*args):
            self.left_text.yview_moveto(args[0])
        self.right_text.yview_moveto = sync_scroll2
        
        # Adicionar painéis ao paned window
        paned.add(left_frame, weight=1)
        paned.add(right_frame, weight=1)
    
    def unified_view(self):
        """Configurar visão unificada"""
        # Limpar frame
        for widget in self.view_frame.winfo_children():
            widget.destroy()
        
        # Criar único painel
        frame = ttk.Frame(self.view_frame)
        frame.pack(fill=tk.BOTH, expand=True)
        
        scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.unified_text = tk.Text(frame, wrap=tk.NONE, 
                                  yscrollcommand=scroll_y.set,
                                  xscrollcommand=scroll_x.set)
        self.unified_text.pack(fill=tk.BOTH, expand=True)
        scroll_y.config(command=self.unified_text.yview)
        scroll_x.config(command=self.unified_text.xview)
    
    def change_mode(self, mode):
        """Muda o modo de visualização"""
        if mode == self.mode:
            return
        
        self.mode = mode
        
        if mode == "side_by_side":
            self.side_by_side_view()
        else:
            self.unified_view()
        
        self.display_diff()
    
    def display_diff(self):
        """Exibe as diferenças no modo atual"""
        if not self.diff_data:
            return
        
        if self.diff_data["type"] == "new_file":
            # Arquivo novo - mostrar conteúdo completo
            if self.mode == "side_by_side":
                self.left_text.config(state=tk.NORMAL)
                self.left_text.delete(1.0, tk.END)
                self.left_text.insert(tk.END, "(New File)")
                self.left_text.config(state=tk.DISABLED)
                
                self.right_text.config(state=tk.NORMAL)
                self.right_text.delete(1.0, tk.END)
                self.right_text.insert(tk.END, self.diff_data["content"])
                self.right_text.config(state=tk.DISABLED)
            else:
                self.unified_text.config(state=tk.NORMAL)
                self.unified_text.delete(1.0, tk.END)
                self.unified_text.insert(tk.END, f"NEW FILE: {self.file_path}\n\n")
                self.unified_text.insert(tk.END, self.diff_data["content"])
                self.unified_text.config(state=tk.DISABLED)
                
        elif self.diff_data["type"] == "diff":
            # Arquivo modificado - processar diff
            diff_text = self.diff_data["diff"]
            
            if self.mode == "side_by_side":
                # Interpretar diff para exibição lado a lado
                old_lines = []
                new_lines = []
                
                in_old = False
                in_new = False
                
                for line in diff_text.split('\n'):
                    if line.startswith('@@'):
                        in_old = False
                        in_new = False
                        old_lines.append("...")
                        new_lines.append("...")
                    elif line.startswith('-'):
                        old_lines.append(line[1:])
                        in_old = True
                    elif line.startswith('+'):
                        new_lines.append(line[1:])
                        in_new = True
                    elif line.startswith(' '):
                        old_lines.append(line[1:])
                        new_lines.append(line[1:])
                        in_old = False
                        in_new = False
                
                # Preencher textos
                self.left_text.config(state=tk.NORMAL)
                self.left_text.delete(1.0, tk.END)
                for line in old_lines:
                    self.left_text.insert(tk.END, line + "\n")
                self.left_text.config(state=tk.DISABLED)
                
                self.right_text.config(state=tk.NORMAL)
                self.right_text.delete(1.0, tk.END)
                for line in new_lines:
                    self.right_text.insert(tk.END, line + "\n")
                self.right_text.config(state=tk.DISABLED)
                
            else:
                # Visão unificada - mostrar diff diretamente
                self.unified_text.config(state=tk.NORMAL)
                self.unified_text.delete(1.0, tk.END)
                
                for line in diff_text.split('\n'):
                    if line.startswith('-'):
                        self.unified_text.insert(tk.END, line + "\n", "removed")
                    elif line.startswith('+'):
                        self.unified_text.insert(tk.END, line + "\n", "added")
                    else:
                        self.unified_text.insert(tk.END, line + "\n")
                
                self.unified_text.config(state=tk.DISABLED)
                
                # Configurar tags para colorização
                self.unified_text.tag_configure("removed", background="#ffcccc")
                self.unified_text.tag_configure("added", background="#ccffcc")