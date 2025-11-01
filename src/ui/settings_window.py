"""
Janela de configurações
"""
import tkinter as tk
from tkinter import ttk, messagebox
from pynput.keyboard import Listener, Key

from ..managers import window_manager
from ..utils import resource_path

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, config, on_save_callback):
        super().__init__(parent)
        self.transient(parent)
        self.title("Configurações")
        try:
            self.iconbitmap(resource_path('img/icon.ico'))
        except tk.TclError:
            print("Aviso: O arquivo de ícone para a janela de configurações não foi encontrado.")
        self.geometry("480x600")
        self.parent = parent
        self.config = config
        self.original_theme = self.config.get("theme", "dark") # Salva o tema original
        self.on_save = on_save_callback

        self.grab_set()

        # Mapeamento de Temas 
        self.theme_map = {"Escuro": "dark", "Claro": "light"}
        self.reverse_theme_map = {v: k for k, v in self.theme_map.items()}

        # Variáveis de UI 
        self.theme_var = tk.StringVar(value=self.reverse_theme_map.get(self.original_theme))
        self.record_mode_var = tk.StringVar(value=self.config.get("record_mode", "Teclado e Mouse"))
        self.playback_engine_var = tk.StringVar(value=self.config.get("playback_engine"))
        self.pydirectinput_pause_var = tk.BooleanVar(value=self.config.get("pydirectinput_optimized_pause", True))
        self.window_title_var = tk.StringVar(value=self.config.get("window_specific_title", ""))
        self.record_hotkey_var = tk.StringVar(value=self._format_key_for_display(self.config["hotkeys"].get("record")))
        self.playback_hotkey_var = tk.StringVar(value=self._format_key_for_display(self.config["hotkeys"].get("playback")))
        
        self.temp_hotkeys = self.config["hotkeys"].copy()
        self.config_listener = None
        self.active_hotkey_config_type = None
        self.status_label = None

        self._create_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Aparência 
        theme_frame = ttk.LabelFrame(main_frame, text="Aparência", padding="10")
        theme_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(theme_frame, text="Tema:").pack(side=tk.LEFT, padx=(0, 5))
        theme_options = list(self.theme_map.keys())
        theme_dropdown = ttk.Combobox(theme_frame, textvariable=self.theme_var, values=theme_options, state="readonly")
        theme_dropdown.pack(fill=tk.X, expand=True)
        theme_dropdown.bind("<<ComboboxSelected>>", self._on_theme_change)

        # Modo de Gravação
        record_mode_frame = ttk.LabelFrame(main_frame, text="Modo de Gravação", padding="10")
        record_mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(record_mode_frame, text="Gravar:").pack(side=tk.LEFT, padx=(0, 5))
        record_mode_options = ["Teclado e Mouse", "Somente Teclado", "Somente Mouse"]
        record_mode_dropdown = ttk.Combobox(record_mode_frame, textvariable=self.record_mode_var, values=record_mode_options, state="readonly")
        record_mode_dropdown.pack(fill=tk.X, expand=True)

        # Motor de Reprodução 
        engine_frame = ttk.LabelFrame(main_frame, text="Motor de Reprodução", padding="10")
        engine_frame.pack(fill=tk.X, pady=5)
        
        engine_options = ["Pynput (Padrão)", "PyAutoGUI (Apps)", "PyDirectInput (Jogos)"]
        engine_dropdown = ttk.Combobox(engine_frame, textvariable=self.playback_engine_var, values=engine_options, state="readonly")
        engine_dropdown.pack(fill=tk.X, expand=True)
        engine_dropdown.bind("<<ComboboxSelected>>", self._toggle_pydirectinput_options)

        # Opção de pausa para PyDirectInput (oculta)
        self.pydirectinput_pause_check = ttk.Checkbutton(
            engine_frame, 
            text="Usar pausa otimizada (0.01s)", 
            variable=self.pydirectinput_pause_var
        )
        # Chama a função para definir o estado inicial
        self._toggle_pydirectinput_options()

        #  Atalhos Globais 
        hotkey_frame = ttk.LabelFrame(main_frame, text="Atalhos Globais", padding="10")
        hotkey_frame.pack(fill=tk.X, pady=5)

        ttk.Label(hotkey_frame, text="Gravação (Iniciar/Parar):").grid(row=0, column=0, sticky=tk.W, pady=2)
        record_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.record_hotkey_var, state='readonly')
        record_hotkey_entry.grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(hotkey_frame, text="Definir", command=lambda: self._set_hotkey_listen_mode('record')).grid(row=0, column=2, padx=(0,2))
        ttk.Button(hotkey_frame, text="Limpar", command=lambda: self._clear_hotkey('record')).grid(row=0, column=3)

        ttk.Label(hotkey_frame, text="Reprodução (Iniciar/Parar):").grid(row=1, column=0, sticky=tk.W, pady=2)
        playback_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.playback_hotkey_var, state='readonly')
        playback_hotkey_entry.grid(row=1, column=1, padx=5, sticky="ew")
        ttk.Button(hotkey_frame, text="Definir", command=lambda: self._set_hotkey_listen_mode('playback')).grid(row=1, column=2, padx=(0,2))
        ttk.Button(hotkey_frame, text="Limpar", command=lambda: self._clear_hotkey('playback')).grid(row=1, column=3)

        hotkey_frame.columnconfigure(1, weight=1) # Permite que a coluna da entrada se expanda

        # Janela Específica 
        window_frame = ttk.LabelFrame(main_frame, text="Executar somente na janela...", padding="10")
        window_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(window_frame, text="Título da Janela (ou parte dele):").pack(anchor=tk.W)
        window_entry = ttk.Entry(window_frame, textvariable=self.window_title_var)
        window_entry.pack(fill=tk.X, expand=True, pady=2)

        # Status e botões 
        self.status_label = ttk.Label(main_frame, text=" ")
        self.status_label.pack(pady=(10, 0))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10,0))
        
        ttk.Button(button_frame, text="Salvar e Fechar", command=self._save_and_close).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Cancelar", command=self._on_closing).pack(side=tk.RIGHT, padx=5)

    def _toggle_pydirectinput_options(self, event=None):
        if self.playback_engine_var.get() == "PyDirectInput (Jogos)":
            self.pydirectinput_pause_check.pack(anchor=tk.W, pady=5)
        else:
            self.pydirectinput_pause_check.pack_forget()

    def _on_theme_change(self, event=None):
        """Exibe um aviso caso o tema seja mudado"""
        selected_theme_display = self.theme_var.get()
        selected_theme = self.theme_map.get(selected_theme_display)
        if selected_theme and selected_theme != self.original_theme:
            messagebox.showinfo(
                "Reinicialização Necessária",
                "A alteração do tema será aplicada após reiniciar o aplicativo.",
                parent=self
            )

    def _set_hotkey_listen_mode(self, hotkey_type):
        """Ativa o modo de escuta para definir um novo atalho"""
        if self.config_listener:
            return
        self.active_hotkey_config_type = hotkey_type
        self.status_label.config(text=f"Pressione uma tecla para definir o atalho de '{hotkey_type}'...")
        self.config_listener = Listener(on_press=self._on_hotkey_press_for_config)
        self.config_listener.start()

    def _on_hotkey_press_for_config(self, key):
        """Callback do listener temporário que captura a tecla do atalho"""
        hotkey_type = self.active_hotkey_config_type
        self.temp_hotkeys[hotkey_type] = self._serialize_key(key)
        
        display_text = self._format_key_for_display(key)
        if hotkey_type == 'record':
            self.record_hotkey_var.set(display_text)
        else:
            self.playback_hotkey_var.set(display_text)
        
        self.status_label.config(text="Atalho definido. Salve para aplicar.")
        self.active_hotkey_config_type = None

        if self.config_listener:
            self.config_listener.stop()
            self.config_listener = None
        return False

    def _clear_hotkey(self, hotkey_type):
        """Limpa um atalho definido antes"""
        self.temp_hotkeys[hotkey_type] = None
        if hotkey_type == 'record':
            self.record_hotkey_var.set("")
        else:
            self.playback_hotkey_var.set("")
        self.status_label.config(text=f"Atalho de '{hotkey_type}' limpo.")

    def _format_key_for_display(self, key_data):
        """Formata o dado da tecla string ou None para ser exibido"""
        if not key_data:
            return ""
        return str(key_data).replace("Key.", "").capitalize()

    def _serialize_key(self, key):
        """Converte um objeto de tecla pynput para uma string serializável"""
        if isinstance(key, Key):
            return key.name
        elif hasattr(key, 'char'):
            return key.char
        return str(key)

    def _save_and_close(self):
        # Salva as configurações
        selected_theme_display = self.theme_var.get()
        self.config["theme"] = self.theme_map.get(selected_theme_display, self.original_theme)
        self.config["record_mode"] = self.record_mode_var.get()
        self.config["playback_engine"] = self.playback_engine_var.get()
        self.config["pydirectinput_optimized_pause"] = self.pydirectinput_pause_var.get()
        self.config["window_specific_title"] = self.window_title_var.get()
        self.config["hotkeys"] = self.temp_hotkeys

        self.on_save(self.config)
        self.destroy()

    def _on_closing(self):
        # Descarta as alterações e fecha
        self.destroy()
