"""Main GUI Window for Jarvis X."""

import math
from datetime import datetime
import tkinter as tk
import customtkinter as ctk
from utils.logger import get_logger
from utils.config_manager import get_config

logger = get_logger()
config = get_config()


class JarvisGUI:
    """Main GUI for Jarvis with digital avatar panel."""

    def __init__(self, jarvis):
        self.jarvis = jarvis

        self.theme = config.get('gui.theme', 'dark')
        self.width = config.get('gui.window_width', 1100)
        self.height = config.get('gui.window_height', 720)

        ctk.set_appearance_mode(self.theme)
        ctk.set_default_color_theme('green')

        self.root = ctk.CTk()
        self.root.title('Jarvis X - Command Interface')
        self.root.geometry(f'{self.width}x{self.height}')
        self.root.minsize(940, 620)

        self.avatar_phase = 0.0
        self.avatar_state = 'idle'
        self.notified_due_ids = set()

        self._setup_ui()
        self._animate_avatar()
        self._poll_due_items()

        self.jarvis.on_command(self._on_command)
        self.jarvis.on_response(self._on_response)

        logger.info('GUI initialized')

    def _setup_ui(self):
        header = ctk.CTkFrame(self.root, corner_radius=14)
        header.pack(fill='x', padx=14, pady=(14, 8))

        title = ctk.CTkLabel(
            header,
            text='J A R V I S   X',
            font=('Segoe UI Semibold', 30)
        )
        title.pack(side='left', padx=14, pady=12)

        self.status_label = ctk.CTkLabel(
            header,
            text='ONLINE',
            text_color='#00E08A',
            font=('Segoe UI', 14, 'bold')
        )
        self.status_label.pack(side='right', padx=14)

        content = ctk.CTkFrame(self.root, corner_radius=14)
        content.pack(fill='both', expand=True, padx=14, pady=(0, 8))

        left_panel = ctk.CTkFrame(content, width=320, corner_radius=12)
        left_panel.pack(side='left', fill='y', padx=(10, 6), pady=10)
        left_panel.pack_propagate(False)

        avatar_title = ctk.CTkLabel(
            left_panel,
            text='DIGITAL PRESENCE',
            font=('Segoe UI', 14, 'bold')
        )
        avatar_title.pack(pady=(12, 6))

        self.avatar_canvas = tk.Canvas(
            left_panel,
            width=280,
            height=280,
            bg='#0B1118',
            highlightthickness=0
        )
        self.avatar_canvas.pack(padx=12, pady=8)

        self.avatar_caption = ctk.CTkLabel(
            left_panel,
            text='Idle and listening for commands',
            font=('Segoe UI', 12),
            text_color='#A9B4C1'
        )
        self.avatar_caption.pack(pady=(4, 8))

        quick_row = ctk.CTkFrame(left_panel, fg_color='transparent')
        quick_row.pack(fill='x', padx=10, pady=(8, 4))

        ctk.CTkButton(quick_row, text='Due Alerts', command=lambda: self._run_quick('show due alerts')).pack(fill='x', pady=4)
        ctk.CTkButton(quick_row, text='Events', command=lambda: self._run_quick('list events')).pack(fill='x', pady=4)
        ctk.CTkButton(quick_row, text='Camera Video', command=lambda: self._run_quick('show camera video on pc')).pack(fill='x', pady=4)

        right_panel = ctk.CTkFrame(content, corner_radius=12)
        right_panel.pack(side='left', fill='both', expand=True, padx=(6, 10), pady=10)

        self.chat_display = ctk.CTkTextbox(
            right_panel,
            font=('Consolas', 12),
            wrap='word'
        )
        self.chat_display.pack(fill='both', expand=True, padx=10, pady=(10, 8))
        self.chat_display.configure(state='disabled')
        self.chat_display.tag_config('user', foreground='#5ED7FF')
        self.chat_display.tag_config('jarvis', foreground='#7FFFB0')
        self.chat_display.tag_config('system', foreground='#FFD166')
        self.chat_display.tag_config('error', foreground='#FF7A7A')

        input_frame = ctk.CTkFrame(right_panel, fg_color='transparent')
        input_frame.pack(fill='x', padx=10, pady=(0, 10))

        self.command_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text='Type a command: add alert, show lyrics, open camera video...',
            font=('Segoe UI', 12),
            height=42
        )
        self.command_entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
        self.command_entry.bind('<Return>', self._on_enter_pressed)

        self.send_button = ctk.CTkButton(
            input_frame,
            text='Send',
            command=self._on_send_clicked,
            width=110,
            height=42
        )
        self.send_button.pack(side='left', padx=(0, 8))

        self.voice_button = ctk.CTkButton(
            input_frame,
            text='Voice',
            command=self._on_voice_clicked,
            width=110,
            height=42,
            fg_color='#0D5DA6',
            hover_color='#1373CC'
        )
        self.voice_button.pack(side='left')

        controls = ctk.CTkFrame(self.root, corner_radius=12)
        controls.pack(fill='x', padx=14, pady=(0, 14))

        if self.jarvis.wake_word_detector:
            self.wake_word_var = ctk.BooleanVar(value=False)
            self.wake_word_toggle = ctk.CTkSwitch(
                controls,
                text='Wake Word',
                variable=self.wake_word_var,
                command=self._toggle_wake_word
            )
            self.wake_word_toggle.pack(side='left', padx=12, pady=8)

        self.voice_var = ctk.BooleanVar(value=config.get('voice.enabled', True))
        self.voice_toggle = ctk.CTkSwitch(
            controls,
            text='Voice Responses',
            variable=self.voice_var,
            command=self._toggle_voice
        )
        self.voice_toggle.pack(side='left', padx=12, pady=8)

        clear_button = ctk.CTkButton(
            controls,
            text='Clear Chat',
            command=self._clear_chat,
            width=120
        )
        clear_button.pack(side='right', padx=12, pady=8)

        greeting = 'Jarvis visual interface online. You can add alerts, open lyrics, and show camera video.'
        self._append_to_chat('JARVIS', greeting, 'jarvis')

    def _append_to_chat(self, sender: str, message: str, tag: str = 'system'):
        self.chat_display.configure(state='normal')
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.chat_display.insert('end', f'[{timestamp}] {sender}: ', tag)
        self.chat_display.insert('end', f'{message}\n')
        self.chat_display.configure(state='disabled')
        self.chat_display.see('end')

    def _run_quick(self, command: str):
        self.command_entry.delete(0, 'end')
        self.command_entry.insert(0, command)
        self._on_send_clicked()

    def _on_enter_pressed(self, _event):
        self._on_send_clicked()

    def _on_send_clicked(self):
        command = self.command_entry.get().strip()
        if not command:
            return

        self.command_entry.delete(0, 'end')
        self._append_to_chat('YOU', command, 'user')
        self._set_avatar_state('listening')
        self.jarvis.process_command(command, speak_response=self.voice_var.get())

    def _on_voice_clicked(self):
        self._append_to_chat('SYSTEM', 'Listening for voice command...', 'system')
        self._set_avatar_state('listening')
        self.root.update()

        result = self.jarvis.process_voice_command()
        if result.get('success') is False and result.get('error') == 'timeout':
            self._append_to_chat('SYSTEM', 'No speech detected.', 'system')
            self._set_avatar_state('idle')

    def _on_command(self, _command: str):
        pass

    def _on_response(self, result: dict):
        response = result.get('response', '')
        success = result.get('success', False)
        tag = 'jarvis' if success else 'error'
        self._append_to_chat('JARVIS', response, tag)
        self._set_avatar_state('speaking')
        self.root.after(1400, lambda: self._set_avatar_state('idle'))

    def _toggle_wake_word(self):
        if self.wake_word_var.get():
            self.jarvis.start_wake_word_detection()
            self._append_to_chat('SYSTEM', 'Wake word detection enabled.', 'system')
        else:
            if self.jarvis.wake_word_detector:
                self.jarvis.wake_word_detector.stop()
            self._append_to_chat('SYSTEM', 'Wake word detection disabled.', 'system')

    def _toggle_voice(self):
        enabled = self.voice_var.get()
        config.set('voice.enabled', enabled, save=False)
        state = 'enabled' if enabled else 'disabled'
        self._append_to_chat('SYSTEM', f'Voice responses {state}.', 'system')

    def _clear_chat(self):
        self.chat_display.configure(state='normal')
        self.chat_display.delete('1.0', 'end')
        self.chat_display.configure(state='disabled')

    def _set_avatar_state(self, state: str):
        self.avatar_state = state
        if state == 'listening':
            self.avatar_caption.configure(text='Listening...')
            self.status_label.configure(text='LISTENING', text_color='#5ED7FF')
        elif state == 'speaking':
            self.avatar_caption.configure(text='Responding...')
            self.status_label.configure(text='RESPONDING', text_color='#7FFFB0')
        else:
            self.avatar_caption.configure(text='Idle and listening for commands')
            self.status_label.configure(text='ONLINE', text_color='#00E08A')

    def _animate_avatar(self):
        self.avatar_canvas.delete('all')
        self.avatar_phase += 0.18

        center_x = 140
        center_y = 140
        state_boost = 1.0 if self.avatar_state == 'idle' else 1.6

        for ring in range(3):
            radius = 44 + (ring * 22) + math.sin(self.avatar_phase + ring) * (3.0 * state_boost)
            color = '#1EC8FF' if ring % 2 == 0 else '#34F5A0'
            self.avatar_canvas.create_oval(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                outline=color,
                width=2
            )

        points = []
        for x in range(20, 260, 8):
            t = (x / 14.0) + self.avatar_phase * 1.8
            y = center_y + math.sin(t) * (14 * state_boost)
            points.extend([x, y])
        self.avatar_canvas.create_line(points, fill='#75F3FF', width=2, smooth=True)

        self.avatar_canvas.create_oval(120, 120, 160, 160, fill='#58F4C0', outline='')
        self.avatar_canvas.create_oval(128, 128, 152, 152, fill='#0B1118', outline='')

        self.root.after(60, self._animate_avatar)

    def _poll_due_items(self):
        try:
            result = self.jarvis.command_processor.alerts_manager.list_items(kind='all', due_only=True)
            if result.get('success'):
                for item in result.get('alerts', []):
                    self._show_due_popup(item, 'Alert')
                for item in result.get('events', []):
                    self._show_due_popup(item, 'Event')
        except Exception as exc:
            logger.debug(f'Popup poll skipped: {exc}')

        self.root.after(30000, self._poll_due_items)

    def _show_due_popup(self, item: dict, kind: str):
        item_id = str(item.get('id', ''))
        if not item_id or item_id in self.notified_due_ids:
            return

        self.notified_due_ids.add(item_id)
        popup = ctk.CTkToplevel(self.root)
        popup.title(f'{kind} Due')
        popup.geometry('420x180')
        popup.attributes('-topmost', True)

        ctk.CTkLabel(popup, text=f'{kind} Reminder', font=('Segoe UI', 20, 'bold')).pack(pady=(16, 8))
        ctk.CTkLabel(popup, text=item.get('title', 'Untitled'), font=('Segoe UI', 14)).pack(pady=4)
        ctk.CTkLabel(popup, text=f"Due: {item.get('due_at', 'unknown')}", font=('Segoe UI', 12)).pack(pady=4)
        ctk.CTkButton(popup, text='Dismiss', command=popup.destroy, width=120).pack(pady=(10, 12))

        self._append_to_chat('SYSTEM', f"{kind} due: {item.get('title', 'Untitled')}", 'system')
        popup.after(20000, popup.destroy)

    def run(self):
        logger.info('Starting GUI main loop')
        self.root.protocol('WM_DELETE_WINDOW', self._on_closing)
        self.root.mainloop()

    def _on_closing(self):
        logger.info('GUI closing')
        self.jarvis.stop()
        self.root.destroy()
