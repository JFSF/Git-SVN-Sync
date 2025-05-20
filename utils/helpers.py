#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import platform
from urllib.parse import urlparse
from collections import Counter

def is_valid_url(url):
    """Verifica se uma URL é válida"""
    if not url:
        return False
        
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def is_valid_path(path):
    """Verifica se um caminho de diretório é válido e existe"""
    if not path:
        return False
        
    return os.path.exists(path)

def normalize_path(path):
    """Normaliza um caminho de diretório"""
    if not path:
        return ""
        
    # Converter separadores de caminho para o padrão do sistema
    path = path.replace('\\', os.sep).replace('/', os.sep)
    
    # Expandir caminhos relativos à pasta do usuário
    if path.startswith('~'):
        path = os.path.expanduser(path)
    
    return os.path.normpath(path)

def secure_encode(text):
    """Codifica texto de forma básica (não segura)"""
    if not text:
        return ""
        
    # Codificação básica - não use para senhas reais em produção
    return ''.join(chr(ord(c) + 1) for c in text)

def secure_decode(text):
    """Decodifica texto de forma básica (não segura)"""
    if not text:
        return ""
        
    # Decodificação básica - não use para senhas reais em produção
    return ''.join(chr(ord(c) - 1) for c in text)

def suggest_commit_message(files):
    """Sugere uma mensagem de commit com base nos arquivos modificados"""
    if not files:
        return "No changes to commit"
    
    # Contar tipos de alterações
    change_types = Counter([file.get('type', '?') for file in files])
    
    # Determinar o tipo principal de alteração
    main_change = None
    if change_types.get('A', 0) > change_types.get('M', 0) and change_types.get('A', 0) > change_types.get('D', 0):
        main_change = "Add"
    elif change_types.get('D', 0) > change_types.get('M', 0):
        main_change = "Remove"
    elif change_types.get('R', 0) > 0:
        main_change = "Rename"
    else:
        main_change = "Update"
    
    # Identificar categorias de arquivos
    file_extensions = [os.path.splitext(file.get('path', ''))[1] for file in files]
    file_extensions = [ext.lower() for ext in file_extensions if ext]
    
    extension_categories = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.html': 'HTML',
        '.css': 'CSS',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'header',
        '.md': 'documentation',
        '.txt': 'text',
        '.json': 'JSON configuration',
        '.xml': 'XML configuration',
        '.yml': 'YAML configuration',
        '.yaml': 'YAML configuration',
        '.ini': 'configuration'
    }
    
    # Identificar categoria principal
    extension_counts = Counter(file_extensions)
    main_category = None
    
    if extension_counts:
        main_ext = extension_counts.most_common(1)[0][0]
        main_category = extension_categories.get(main_ext, 'files')
    else:
        main_category = 'files'
    
    # Gerar mensagem de commit
    num_files = len(files)
    
    if num_files == 1:
        file_path = files[0].get('path', '')
        file_name = os.path.basename(file_path)
        return f"{main_change} {file_name}"
    else:
        return f"{main_change} {num_files} {main_category}"

def format_commit_message(message, task_id=None):
    """Formata uma mensagem de commit com boas práticas"""
    if not message:
        return ""
    
    # Dividir em linhas
    lines = message.strip().split('\n')
    
    # Formatar primeira linha (assunto)
    subject = lines[0].strip()
    
    # Verificar se já tem prefixo de tipo
    prefixes = ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore']
    has_prefix = any(subject.startswith(f"{p}:") or subject.startswith(f"{p}(") for p in prefixes)
    
    # Adicionar tarefa se fornecida e não estiver na mensagem
    if task_id and task_id not in subject:
        if has_prefix:
            # Procurar onde inserir o ID da tarefa (após o escopo, se houver)
            if '(' in subject and '):' in subject:
                parts = subject.split('):', 1)
                subject = f"{parts[0]}): [{task_id}]{parts[1]}"
            else:
                parts = subject.split(':', 1)
                subject = f"{parts[0]}: [{task_id}]{parts[1]}"
        else:
            # Adicionar no início
            subject = f"[{task_id}] {subject}"
    
    # Reconstruir a mensagem
    if len(lines) > 1:
        # Garantir linha em branco entre assunto e corpo
        if lines[1].strip():
            formatted_message = subject + '\n\n' + '\n'.join(lines[1:])
        else:
            formatted_message = subject + '\n' + '\n'.join(lines[1:])
    else:
        formatted_message = subject
    
    return formatted_message