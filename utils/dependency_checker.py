#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import subprocess
import sys

def check_dependencies():
    """
    Verifica se todas as dependências necessárias estão instaladas.
    
    Returns:
        Tuple[bool, List[str]]: (True se todas as dependências estão instaladas, lista de dependências faltantes)
    """
    missing_deps = []
    
    # Verificar dependências Python
    python_deps = [
        "PyQt6",
        "git",
        "requests",
    ]
    
    for dep in python_deps:
        try:
            importlib.import_module(dep)
        except ImportError:
            missing_deps.append(dep)
    
    # Verificar comandos externos (Git, SVN)
    external_commands = [
        ("git", "--version"),
        ("svn", "--version"),
    ]
    
    for cmd, arg in external_commands:
        try:
            subprocess.run([cmd, arg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            missing_deps.append(cmd)
    
    # Verificar componentes específicos do PyQt6
    if "PyQt6" not in missing_deps:
        qt_modules = [
            "PyQt6.QtWidgets",
            "PyQt6.QtCore",
            "PyQt6.QtGui"
        ]
        
        for module in qt_modules:
            try:
                importlib.import_module(module)
            except ImportError:
                missing_deps.append(module)
    
    # Verificar versão do Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 6):
        missing_deps.append("Python 3.6+")
    
    # Sugerir instalação de dependências opcionais
    optional_deps = {
        "pygments": "Syntax highlighting for code diffs",
        "win10toast": "Desktop notifications on Windows",
    }
    
    for dep, desc in optional_deps.items():
        try:
            importlib.import_module(dep)
        except ImportError:
            # Não adicionar à lista de missing_deps, apenas registrar como sugestão
            pass
    
    return (len(missing_deps) == 0, missing_deps)

if __name__ == "__main__":
    # Se executado diretamente, mostrar status de dependências
    all_deps_met, missing = check_dependencies()
    
    if all_deps_met:
        print("All dependencies are met!")
    else:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        
        print("\nPlease install the missing dependencies with pip:")
        pip_deps = [dep for dep in missing if dep not in ["git", "svn"]]
        if pip_deps:
            print(f"  pip install {' '.join(pip_deps)}")
        
        print("\nFor external commands, install them using your system's package manager.")