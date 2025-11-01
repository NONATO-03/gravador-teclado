import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

from pynput.keyboard import Key, Listener

from .managers import file_manager, config_manager
from .ui.actions_display import ActionsDisplay
from .managers.hotkey_manager import HotkeyManager
from .core.player import MacroPlayer
from .core.recorder import MacroRecorder
from .ui.settings_window import SettingsWindow
from .utils import resource_path


class FullMacroApp:
    """
    Classe principal que tem toda a lógica da aplicação e da GUI
    """
    def __init__(self, root, config):
        self.root = root
        self.root.title("Gravador de ações")
        
        try:
            self.root.iconbitmap(resource_path('img/icon.ico'))
        except tk.TclError:
            print("Aviso: O arquivo 'img/icon.ico' não foi encontrado ou não pôde ser carregado.")

        self.original_geometry = "450x580"  
        self.mini_geometry = "220x60"     
        self.root.geometry(self.original_geometry)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Carregar Configurações
        self.config = config # Usa a configuração pré carregada

        # Lógica 
        self.recorder = MacroRecorder(record_mode=self.config.get("record_mode"))
        self.player = MacroPlayer()
        self.hotkey_manager = HotkeyManager()

        # Estado
        self.is_playing = False
        self.playback_thread = None
        self.stop_playback_signal = threading.Event()
        self.recorded_events = []
        self.is_pinned = False
        self.is_mini_mode = False

        # Construção da Interface 
        # Frames para os dois modos de visualização
        self.main_frame = tk.Frame(self.root)
        self.mini_frame = tk.Frame(self.root, padx=5, pady=5)

        self._create_main_widgets()
        self._create_mini_widgets()

        # Inicia no modo principal
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Aplica atalhos salvos na inicialização
        self._update_hotkey_listener()

    def _create_main_widgets(self):
        """Cria os widgets para a visualização """
        parent = self.main_frame
        
        util_frame = tk.Frame(parent)
        util_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

        self.main_status_label = tk.Label(util_frame, text="Status: Pronto", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.main_status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Botões de utilidade da direita para a esquerda
        mini_btn = tk.Button(util_frame, text="─", width=4, command=self.toggle_mini_mode)
        mini_btn.pack(side=tk.RIGHT)
        
        self.main_pin_btn = tk.Button(util_frame, text="📌", width=4, command=self.toggle_pin)
        self.main_pin_btn.pack(side=tk.RIGHT)

        load_btn = tk.Button(util_frame, text="📂", width=4, command=self.load_actions)
        load_btn.pack(side=tk.RIGHT)

        save_btn = tk.Button(util_frame, text="💾", width=4, command=self.save_actions)
        save_btn.pack(side=tk.RIGHT)

        settings_btn = tk.Button(util_frame, text="⚙️", width=4, command=self.open_settings)
        settings_btn.pack(side=tk.RIGHT)

        #  Efeitos de sobrepor o mouse
        save_btn.bind("<Enter>", lambda e, b=save_btn, t="Salvar": self.on_hover(e, b, t))
        save_btn.bind("<Leave>", lambda e, b=save_btn, i="💾": self.on_leave(e, b, i))
        
        load_btn.bind("<Enter>", lambda e, b=load_btn, t="Carregar": self.on_hover(e, b, t))
        load_btn.bind("<Leave>", lambda e, b=load_btn, i="📂": self.on_leave(e, b, i))

        self.main_pin_btn.bind("<Enter>", lambda e, b=self.main_pin_btn, t="Fixar": self.on_hover(e, b, t))
        self.main_pin_btn.bind("<Leave>", lambda e, b=self.main_pin_btn, i="📌": self.on_leave(e, b, i))

        mini_btn.bind("<Enter>", lambda e, b=mini_btn, t="Minimizar": self.on_hover(e, b, t))
        mini_btn.bind("<Leave>", lambda e, b=mini_btn, i="─": self.on_leave(e, b, i))

        settings_btn.bind("<Enter>", lambda e, b=settings_btn, t="Config.": self.on_hover(e, b, t))
        settings_btn.bind("<Leave>", lambda e, b=settings_btn, i="⚙️": self.on_leave(e, b, i))


        control_frame = tk.Frame(parent, padx=10, pady=10)
        control_frame.pack(fill=tk.X)
        self.record_btn = tk.Button(control_frame, text="▶ Iniciar Gravação", command=self.start_recording_countdown, bg="#4CAF50", fg="white", width=20)
        self.record_btn.pack(side=tk.LEFT, expand=True)
        self.stop_record_btn = tk.Button(control_frame, text="■ Parar Gravação", command=self.stop_recording, state=tk.DISABLED, bg="#f44336", fg="white", width=20)
        self.stop_record_btn.pack(side=tk.LEFT, expand=True, padx=5)

        # Frame de ações gravadas
        self.actions_display_handler = ActionsDisplay(parent)

        # Frame de controles de reprodução
        playback_frame = tk.LabelFrame(parent, text="Controles de Reprodução", padx=10, pady=10)
        playback_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        tk.Label(playback_frame, text="Repetições:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.reps_entry = tk.Entry(playback_frame, width=10)
        self.reps_entry.insert(0, "1")
        self.reps_entry.grid(row=0, column=1, sticky=tk.W)

        self.infinite_var = tk.BooleanVar()
        self.infinite_check = tk.Checkbutton(playback_frame, text="Infinito", variable=self.infinite_var, command=self.toggle_reps_entry)
        self.infinite_check.grid(row=0, column=2, padx=10)

        tk.Label(playback_frame, text="Pausa entre repetições (s):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.delay_entry = tk.Entry(playback_frame, width=10)
        self.delay_entry.insert(0, "1.0")
        self.delay_entry.grid(row=1, column=1, sticky=tk.W)

        self.play_btn = tk.Button(playback_frame, text="▶ Reproduzir", command=self.start_playback_countdown, state=tk.DISABLED, bg="#2196F3", fg="white")
        self.play_btn.grid(row=2, column=0, columnspan=3, pady=10, sticky="ew")

        # Frame de Status
        status_frame = tk.Frame(parent, padx=10, pady=5)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.rep_count_label = tk.Label(status_frame, text="", anchor=tk.W)
        self.rep_count_label.pack(fill=tk.X)

        # Créditos
        credits_label = tk.Label(parent, text="Feito com carinho por Vitor Nonato", font=("Segoe UI", 8), fg="grey")
        credits_label.pack(side=tk.BOTTOM, pady=(0, 5))

    def _create_mini_widgets(self):
        """Cria os widgets para a visualização em miniatura"""
        parent = self.mini_frame
        
        self.mini_play_btn = tk.Button(parent, text="▶", command=self.start_playback_countdown, bg="#2196F3", fg="white", font=("Helvetica", 12, "bold"))
        self.mini_play_btn.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        self.mini_status_label = tk.Label(parent, text="Pronto", anchor=tk.W)
        self.mini_status_label.grid(row=0, column=1, sticky="nsew", padx=5)
        
        self.mini_pin_btn = tk.Button(parent, text="📌", width=3, command=self.toggle_pin)
        self.mini_pin_btn.grid(row=0, column=2, sticky="nsew", padx=2)

        tk.Button(parent, text="❐", width=3, command=self.toggle_mini_mode).grid(row=0, column=3, sticky="nsew", padx=2)

        parent.grid_columnconfigure(1, weight=1) # Faz o status label expandir

    def toggle_mini_mode(self):
        """Alterna entre o modo completo e o modo miniaturazinha"""
        self.is_mini_mode = not self.is_mini_mode
        if self.is_mini_mode:
            self.main_frame.pack_forget()
            self.mini_frame.pack(fill=tk.BOTH, expand=True)
            self.root.geometry(self.mini_geometry)
        else:
            self.mini_frame.pack_forget()
            self.main_frame.pack(fill=tk.BOTH, expand=True)
            self.root.geometry(self.original_geometry)
        # Garante que o estado de fixo seja mantido
        self.root.attributes('-topmost', self.is_pinned)

    # UI 

    def on_hover(self, event, button, text):
        """Quando o mouse entra na área do botão"""
        button.config(text=text, width=8)

    def on_leave(self, event, button, icon):
        """Quando o mouse sai da área do botão"""
        button.config(text=icon, width=4)

    def toggle_pin(self):
        """Alterna o estado sempre visível da janela"""
        self.is_pinned = not self.is_pinned
        self.root.attributes('-topmost', self.is_pinned)
        relief_style = tk.SUNKEN if self.is_pinned else tk.RAISED
        self.main_pin_btn.config(relief=relief_style)
        self.mini_pin_btn.config(relief=relief_style)

    def update_status(self, text):
        """Atualiza a label de status em ambas as visualizações"""
        self.root.after(0, lambda: self.main_status_label.config(text=f"Status: {text}"))
        self.root.after(0, lambda: self.mini_status_label.config(text=text))

    def display_action(self, action_text):
        """Exibe uma ação na caixa de texto"""
        self.root.after(0, lambda: self.actions_display_handler.add_action(action_text))

    def toggle_reps_entry(self):
        """Ativa/desativa o campo de repetições com base no checkbox infinito"""
        self.reps_entry.config(state=tk.DISABLED if self.infinite_var.get() else tk.NORMAL)

    # Gravação 

    def start_recording_countdown(self):
        """Inicia a contagem regressiva para a gravação"""
        if self.recorder.is_recording or self.is_playing:
            return

        self.recorded_events = []
        self.actions_display_handler.clear()
        
        self.record_btn.config(state=tk.DISABLED)
        self.play_btn.config(state=tk.DISABLED)
        
        for i in range(2, 0, -1):
            self.root.after((2 - i) * 1000, lambda i=i: self.update_status(f"Gravando em {i}..."))
        
        self.root.after(2000, self.start_actual_recording)

    def start_actual_recording(self):
        """Inicia a gravação"""
        self.recorder.start(on_action_callback=self.display_action)
        self.stop_record_btn.config(state=tk.NORMAL)
        self.update_status("Gravando...")

    def stop_recording(self):
        """Para a gravação e atualiza a UI"""
        if self.recorder.is_recording:
            self.recorder.stop()
            self.recorded_events = self.recorder.events
            self.update_status("Gravação parada.")
            self.stop_record_btn.config(state=tk.DISABLED)
            self.record_btn.config(state=tk.NORMAL)
            self.play_btn.config(state=tk.NORMAL if self.recorded_events else tk.DISABLED)
            self._update_actions_display() # Atualiza a tela com o que foi gravado

    # Reprodução 

    def start_playback_countdown(self):
        """Inicia a contagem regressiva para a reproduzir"""
        if self.is_playing or not self.recorded_events:
            return
        
        self.record_btn.config(state=tk.DISABLED)
        # Atualiza ambos os botões de play
        self.play_btn.config(text="■ Parar Reprodução", command=self.stop_playback)
        self.mini_play_btn.config(text="■", command=self.stop_playback)

        for i in range(2, 0, -1):
            self.root.after((2 - i) * 1000, lambda i=i: self.update_status(f"Reproduzindo em {i}..."))
        
        self.root.after(2000, self.start_actual_playback)
    
    def start_actual_playback(self):
        """Inicia a reprodução em uma nova thread."""
        self.is_playing = True
        self.update_status("Reproduzindo...")
        self.stop_playback_signal.clear() 
        
        self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.playback_thread.start()

    def stop_playback(self):
        """Avisa a thread de reprodução parar"""
        if self.is_playing:
            self.stop_playback_signal.set()
            self.update_status("Parando...")

    def _playback_loop(self):
        """O loop que executa em uma thread separada para não bloquear a GUI"""
        try:
            if self.infinite_var.get():
                num_reps = float('inf')
                loop_infinitely = True
            else:
                num_reps = int(self.reps_entry.get())
                loop_infinitely = False
        except ValueError:
            self.root.after(0, lambda: messagebox.showerror("Erro", "Número de repetições inválido."))
            self._playback_finished()
            return
            
        rep_num = 0
        while loop_infinitely or rep_num < num_reps:
            if self.stop_playback_signal.is_set():
                break
            
            rep_num += 1
            self.root.after(0, lambda r=rep_num: self.rep_count_label.config(text=f"Repetição: {r}/{num_reps if not loop_infinitely else '∞'}"))

            # Obtém o motor de reprodução da configuração
            engine_map = {
                "Pynput (Padrão)": "pynput",
                "PyAutoGUI (Apps)": "pyautogui",
                "PyDirectInput (Jogos)": "pydirectinput"
            }
            engine_name = self.config.get("playback_engine", "Pynput (Padrão)")
            engine = engine_map.get(engine_name, "pynput")

            # Obtém o título da janela especificada
            window_title = self.config.get("window_specific_title")

            self.player.play(self.recorded_events, self.stop_playback_signal, window_title)
            
            if self.stop_playback_signal.is_set():
                break

            # Pausa 
            if loop_infinitely or rep_num < num_reps:
                try:
                    delay = float(self.delay_entry.get())
                    if delay > 0:
                        time.sleep(delay)
                except ValueError:
                    pass  # Ignora se o delay for inválido
        
        self.root.after(0, self._playback_finished)
    
    def _playback_finished(self):
        """Atualiza a UI quando a reprodução termina ou é interrompida"""
        self.is_playing = False
        status_text = "Reprodução Finalizada"
        if self.stop_playback_signal.is_set():
            status_text = "Reprodução Parada"
        elif self.player.was_skipped:
            status_text = "Reprodução pulada (janela inativa)"

        self.update_status(status_text)
        self.rep_count_label.config(text="")
        # Atualiza ambos os botões de play
        self.play_btn.config(text="▶ Reproduzir", command=self.start_playback_countdown)
        self.mini_play_btn.config(text="▶", command=self.start_playback_countdown)
        self.record_btn.config(state=tk.NORMAL)
        if not self.recorded_events:
            self.play_btn.config(state=tk.DISABLED)
            
    # Configurações e atalhos 

    def open_settings(self):
        """Abre a janela"""
        SettingsWindow(self.root, self.config, self._save_config_and_update)

    def _save_config_and_update(self, new_config):
        """Callback para salvar a configuração e atualizar a aplicação"""
        self.config = new_config
        config_manager.save_config(self.config)
        self._apply_config_changes(new_config)
        messagebox.showinfo("Configurações", "Configurações salvas com sucesso.", parent=self.root)

    def _apply_config_changes(self, new_config):
        """Aplica as configurações atualizadas na aplicação"""
        self.config = new_config
        
        # Atualiza o modo de gravação no recorder
        self.recorder.set_record_mode(self.config.get("record_mode"))

        # Atualiza o motor de reprodução no player
        self.player.set_engine(
            self.config.get("playback_engine"),
            pydirectinput_pause=self.config.get("pydirectinput_optimized_pause")
        )
        
        # Atualiza os atalhos
        self._update_hotkey_listener()

    def _update_hotkey_listener(self):
        """Reconstrói o mapa de atalhos e reinicia o listener global"""
        callbacks = {}
        hotkeys = self.config.get("hotkeys", {})
        
        record_key = hotkeys.get('record')
        if record_key:
            # Constroi a string de combinação de teclas que o pynput espera
            key_str = f"<{record_key}>" if len(record_key) > 1 else record_key
            callbacks[key_str] = self.toggle_recording
        
        playback_key = hotkeys.get('playback')
        if playback_key:
            key_str = f"<{playback_key}>" if len(playback_key) > 1 else playback_key
            callbacks[key_str] = self.toggle_playback
            
        self.hotkey_manager.update_listener(callbacks)

    def toggle_recording(self):
        """Chamado pelo atalho para iniciar ou parar a gravação"""
        if self.recorder.is_recording:
            self.root.after(0, self.stop_recording)
        else:
            self.root.after(0, self.start_recording_countdown)

    def toggle_playback(self):
        """Chamado pelo atalho para iniciar ou parar a reprodução"""
        if self.is_playing:
            self.root.after(0, self.stop_playback)
        else:
            self.root.after(0, self.start_playback_countdown)

    def _on_closing(self):
        """Garante que os listeners sejam parados antes de fechar"""
        if self.recorder.is_recording:
            self.stop_recording()
        self.hotkey_manager.stop_listener()
        self.root.destroy()

    def save_actions(self):
        """Salva as ações gravadas usando o file_manager"""
        file_manager.save_events_to_file(self.recorded_events)

    def load_actions(self):
        """Carrega ações de um arquivo e atualiza a UI"""
        loaded_events = file_manager.load_events_from_file()
        if loaded_events is not None:
            self.recorded_events = loaded_events
            self._update_actions_display()

    def _update_actions_display(self):
        """Atualiza a caixa de texto com os eventos atuais"""
        self.actions_display_handler.update(self.recorded_events)
        self.play_btn.config(state=tk.NORMAL if self.recorded_events else tk.DISABLED)

