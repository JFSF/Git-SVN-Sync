#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="GitSVNSync",
    version="1.0.0",
    description="A tool for synchronizing Git and SVN repositories",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyQt6>=6.5.0",
        "GitPython>=3.1.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
        ],
        "optional": [
            "pygments>=2.12.0",  # Para destacar sintaxe
            "win10toast>=0.9.0;platform_system=='Windows'",  # Notificações no Windows
        ],
    },
    entry_points={
        "console_scripts": [
            "git-svn-sync=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Software Development :: Version Control :: SVN",
    ],
    python_requires=">=3.7",
)