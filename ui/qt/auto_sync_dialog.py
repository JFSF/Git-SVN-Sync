#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Diálogo de configuração de sincronização automática em PyQt6
"""

from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QCheckBox, QSpinBox,
                             QRadioButton, QButtonGroup, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class AutoSyncDialog(QDialog):
    """Diálogo para configurar sincronização automática"""

    def __init__(self, parent, auto_sync_manager, config_manager):
        super().__init__(parent)

        self.auto_sync_manager = auto_sync_manager
        self.config = config_manager

        self.setWindowTitle("Automatic Synchronization Settings")
        self.setMinimumSize(500, 450)
        self.setModal(True)

        # Timer para atualizar status
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # Atualizar a cada 1 segundo

        self.create_ui()
        self.load_settings()
        self.update_status()

    def create_ui(self):
        """Cria a interface do diálogo"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Painel de status
        self.create_status_panel(layout)

        # Painel de configurações
        self.create_settings_panel(layout)

        # Botões de ação
        self.create_buttons(layout)

    def create_status_panel(self, parent_layout):
        """Cria o painel de status atual"""
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout(status_group)

        # Status atual
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Auto-sync:"))
        self.status_label = QLabel("Disabled")
        font = QFont()
        font.setBold(True)
        self.status_label.setFont(font)
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        status_layout.addLayout(status_row)

        # Próxima sincronização
        next_sync_row = QHBoxLayout()
        next_sync_row.addWidget(QLabel("Next sync:"))
        self.next_sync_label = QLabel("N/A")
        next_sync_row.addWidget(self.next_sync_label)
        next_sync_row.addStretch()
        status_layout.addLayout(next_sync_row)

        # Contador de sincronizações
        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("Sync count:"))
        self.sync_count_label = QLabel("0")
        count_row.addWidget(self.sync_count_label)
        count_row.addStretch()
        status_layout.addLayout(count_row)

        # Botões de controle
        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Auto-Sync")
        self.start_btn.clicked.connect(self.start_sync)
        control_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Auto-Sync")
        self.stop_btn.clicked.connect(self.stop_sync)
        control_layout.addWidget(self.stop_btn)

        self.force_sync_btn = QPushButton("Force Sync Now")
        self.force_sync_btn.clicked.connect(self.force_sync)
        control_layout.addWidget(self.force_sync_btn)

        control_layout.addStretch()
        status_layout.addLayout(control_layout)

        parent_layout.addWidget(status_group)

    def create_settings_panel(self, parent_layout):
        """Cria o painel de configurações"""
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)

        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable automatic synchronization")
        settings_layout.addWidget(self.enable_checkbox)

        settings_layout.addSpacing(10)

        # Intervalo
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Sync interval (minutes):"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setMinimum(1)
        self.interval_spinbox.setMaximum(1440)  # Máximo 24 horas
        self.interval_spinbox.setValue(30)
        interval_layout.addWidget(self.interval_spinbox)
        interval_layout.addStretch()
        settings_layout.addLayout(interval_layout)

        settings_layout.addSpacing(10)

        # Direção de sincronização
        direction_label = QLabel("Sync direction:")
        direction_label.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(direction_label)

        self.direction_group = QButtonGroup()
        self.bidirectional_radio = QRadioButton("Bidirectional (Git ⇄ SVN)")
        self.git_to_svn_radio = QRadioButton("Git to SVN only (Git → SVN)")
        self.svn_to_git_radio = QRadioButton("SVN to Git only (SVN → Git)")

        self.direction_group.addButton(self.bidirectional_radio, 0)
        self.direction_group.addButton(self.git_to_svn_radio, 1)
        self.direction_group.addButton(self.svn_to_git_radio, 2)

        settings_layout.addWidget(self.bidirectional_radio)
        settings_layout.addWidget(self.git_to_svn_radio)
        settings_layout.addWidget(self.svn_to_git_radio)

        settings_layout.addSpacing(10)

        # Resolução de conflitos
        conflict_label = QLabel("Conflict resolution:")
        conflict_label.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(conflict_label)

        self.conflict_group = QButtonGroup()
        self.manual_conflict_radio = QRadioButton("Manual resolution required")
        self.git_prefer_radio = QRadioButton("Always prefer Git version")
        self.svn_prefer_radio = QRadioButton("Always prefer SVN version")

        self.conflict_group.addButton(self.manual_conflict_radio, 0)
        self.conflict_group.addButton(self.git_prefer_radio, 1)
        self.conflict_group.addButton(self.svn_prefer_radio, 2)

        settings_layout.addWidget(self.manual_conflict_radio)
        settings_layout.addWidget(self.git_prefer_radio)
        settings_layout.addWidget(self.svn_prefer_radio)

        settings_layout.addSpacing(10)

        # Auto-push
        self.auto_push_checkbox = QCheckBox("Automatically push to Git remote after SVN sync")
        settings_layout.addWidget(self.auto_push_checkbox)

        parent_layout.addWidget(settings_group)

    def create_buttons(self, parent_layout):
        """Cria os botões de ação"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save Settings")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        parent_layout.addLayout(button_layout)

    def load_settings(self):
        """Carrega as configurações atuais"""
        # Enable
        self.enable_checkbox.setChecked(self.config.get("auto_sync.enabled", False))

        # Interval
        self.interval_spinbox.setValue(self.config.get("auto_sync.interval_minutes", 30))

        # Direction
        direction = self.config.get("sync.direction", "bidirectional")
        if direction == "bidirectional":
            self.bidirectional_radio.setChecked(True)
        elif direction == "git_to_svn":
            self.git_to_svn_radio.setChecked(True)
        else:
            self.svn_to_git_radio.setChecked(True)

        # Conflict resolution
        conflict = self.config.get("sync.auto_resolve_conflicts", "none")
        if conflict == "none":
            self.manual_conflict_radio.setChecked(True)
        elif conflict == "git":
            self.git_prefer_radio.setChecked(True)
        else:
            self.svn_prefer_radio.setChecked(True)

        # Auto-push
        self.auto_push_checkbox.setChecked(self.config.get("sync.auto_push", False))

    def save_settings(self):
        """Salva as configurações"""
        # Validar intervalo
        interval = self.interval_spinbox.value()
        if interval < 1:
            QMessageBox.warning(self, "Invalid Input",
                              "Sync interval must be at least 1 minute.")
            return

        # Salvar configurações
        self.config.set("auto_sync.enabled", self.enable_checkbox.isChecked())
        self.config.set("auto_sync.interval_minutes", interval)

        # Direction
        if self.bidirectional_radio.isChecked():
            self.config.set("sync.direction", "bidirectional")
        elif self.git_to_svn_radio.isChecked():
            self.config.set("sync.direction", "git_to_svn")
        else:
            self.config.set("sync.direction", "svn_to_git")

        # Conflict resolution
        if self.manual_conflict_radio.isChecked():
            self.config.set("sync.auto_resolve_conflicts", "none")
        elif self.git_prefer_radio.isChecked():
            self.config.set("sync.auto_resolve_conflicts", "git")
        else:
            self.config.set("sync.auto_resolve_conflicts", "svn")

        # Auto-push
        self.config.set("sync.auto_push", self.auto_push_checkbox.isChecked())

        # Aplicar alterações ao auto-sync manager
        self.auto_sync_manager.enabled = self.enable_checkbox.isChecked()
        self.auto_sync_manager.interval = interval

        # Reiniciar se necessário
        if self.enable_checkbox.isChecked():
            self.auto_sync_manager.stop()
            self.auto_sync_manager.start()
        else:
            self.auto_sync_manager.stop()

        QMessageBox.information(self, "Success",
                               "Auto-sync settings saved successfully!")

    def update_status(self):
        """Atualiza o status exibido"""
        if not self.auto_sync_manager:
            return

        # Status atual
        is_running = (self.auto_sync_manager.sync_thread and
                     self.auto_sync_manager.sync_thread.is_alive())

        if self.auto_sync_manager.enabled and is_running:
            self.status_label.setText("✓ Enabled and Running")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        else:
            self.status_label.setText("✗ Disabled or Stopped")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

        # Próxima sincronização
        if self.auto_sync_manager.next_sync_time:
            time_left = self.auto_sync_manager.next_sync_time - datetime.now()
            if time_left.total_seconds() > 0:
                minutes, seconds = divmod(int(time_left.total_seconds()), 60)
                self.next_sync_label.setText(
                    f"{minutes:02d}:{seconds:02d} (at {self.auto_sync_manager.next_sync_time.strftime('%H:%M:%S')})")
            else:
                self.next_sync_label.setText("Due now")
        else:
            self.next_sync_label.setText("N/A")

        # Contador
        self.sync_count_label.setText(str(self.auto_sync_manager.sync_count))

    def start_sync(self):
        """Inicia a sincronização automática"""
        if not self.enable_checkbox.isChecked():
            reply = QMessageBox.question(
                self, "Enable Auto-Sync?",
                "Auto-sync is currently disabled. Enable it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.enable_checkbox.setChecked(True)
            else:
                return

        self.auto_sync_manager.enabled = True
        self.auto_sync_manager.start()

    def stop_sync(self):
        """Para a sincronização automática"""
        self.auto_sync_manager.stop()

    def force_sync(self):
        """Força uma sincronização imediata"""
        if not self.auto_sync_manager:
            return

        reply = QMessageBox.question(
            self, "Force Sync",
            "This will perform an immediate synchronization. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Executar em thread para não bloquear a UI
            import threading
            threading.Thread(
                target=self.auto_sync_manager._perform_sync,
                daemon=True
            ).start()

    def closeEvent(self, event):
        """Evento de fechamento"""
        self.update_timer.stop()
        event.accept()
