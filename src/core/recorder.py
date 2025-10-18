"""
Este arquivo é responsável por gravar o macro
"""
import time
import threading
from pynput import keyboard, mouse

class MacroRecorder:
    """
    Gerencia a gravação de ações do usuário tanto teclado quanto mouse.
    """
    def __init__(self, record_mode="Teclado e Mouse"):
        self.events = []
        self.is_recording = False
        self.start_time = 0
        self.keyboard_listener = None
        self.mouse_listener = None
        self._on_action_callback = None
        self.ignore_keys = set() # Conjunto de teclas a serem ignoradas.
        self.key_press_times = {}  # Dicionário para rastrear o tempo de pressionamento de cada tecla
        self.TAP_THRESHOLD = 0.2  # Limite em segundos para considerar um tap
        self.set_record_mode(record_mode)

    def set_record_mode(self, mode):
        """Define o que deve ser gravado."""
        self.record_mode = mode
        self.record_keyboard = "Mouse" not in self.record_mode
        self.record_mouse = "Teclado" not in self.record_mode

    def start(self, on_action_callback=None, ignore_keys=None):
        """
        Inicia a gravação, limpando eventos antigos e ativando os listeners.
        
        Argumentos:
            on_action_callback (callable, opcional): Uma função a ser chamada sempre que uma nova ação for registrada. Recebe uma string descritiva da ação. Defaults to None.
            ignore_keys (list, opcional): Uma lista de teclas a serem ignoradas durante a gravação. Defaults to None.
        """
        if self.is_recording:
            return

        self.events = []
        self.is_recording = True
        self.start_time = time.monotonic()
        self._on_action_callback = on_action_callback
        self.ignore_keys = set(ignore_keys or []) # Define as teclas a ignorar
        self.key_press_times.clear()

        # Configura e inicia os listeners com base no modo de gravação
        if self.record_keyboard:
            self.keyboard_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
            self.keyboard_listener.start()
        
        if self.record_mouse:
            self.mouse_listener = mouse.Listener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll)
            self.mouse_listener.start()

    def stop(self):
        """Para a gravação e desativa os listeners."""
        if not self.is_recording:
            return

        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

        # Processa quaisquer teclas que ainda estejam pressionadas como eventos do tipo press
        # Isso garante que se a gravação parar com uma tecla pressionada, ela vai ser registrada
        for key, press_time in self.key_press_times.items():
            t = press_time - self.start_time
            event = {'time': t, 'type': 'key_press', 'key': key}
            display = f"[{t:.2f}s] Pressionou Tecla: {key}"
            self._record_event(event, display)
        self.key_press_times.clear()
            
        # Garante que todos os eventos estejam em ordem cronológica estrita
        # Isso corrige um problema que  as vezes os eventos podem estar fora de ordem devido a threads
        self.events.sort(key=lambda e: e['time'])

        self.is_recording = False
        self._on_action_callback = None
        self.ignore_keys = set() # Limpa as teclas ignoradas

    def _record_event(self, event_data, display_text):
        """
        Adiciona um evento à lista e chama o callback de ação... caso exista
        """
        if not self.is_recording:
            return
            
        self.events.append(event_data)
        if self._on_action_callback:
            self._on_action_callback(display_text)

    # Callback para Listeners 

    def on_press(self, key):
        # Ignora eventos de repetição do sistema operacional
        if key in self.key_press_times:
            return
        # Verifica se a tecla deve ser ignorada
        if key in self.ignore_keys:
            return
        
        # Armazena o tempo que a tecla foi pressionada
        self.key_press_times[key] = time.monotonic()

    def on_release(self, key):
        if key not in self.key_press_times:
            return
            
        press_time = self.key_press_times.pop(key)
        release_time = time.monotonic()
        duration = release_time - press_time

        if duration < self.TAP_THRESHOLD:
            # Se a duração for curta, registra como um tap
            t = press_time - self.start_time
            event = {'time': t, 'type': 'key_tap', 'key': key}
            display = f"[{t:.2f}s] Apertou Tecla: {key}"
            self._record_event(event, display)
        else:
            # Se for longa, registra press e release separadamente
            # Evento de Pressionar
            t_press = press_time - self.start_time
            event_press = {'time': t_press, 'type': 'key_press', 'key': key}
            display_press = f"[{t_press:.2f}s] Pressionou Tecla: {key}"
            self._record_event(event_press, display_press)
            
            # Evento de Soltar
            t_release = release_time - self.start_time
            event_release = {'time': t_release, 'type': 'key_release', 'key': key}
            display_release = f"[{t_release:.2f}s] Soltou Tecla: {key}"
            self._record_event(event_release, display_release)

    def on_move(self, x, y):
        t = time.monotonic() - self.start_time
        # Registra eventos de movimento do mouse
        event = {'time': t, 'type': 'move', 'pos': (x, y)}
        self._record_event(event, f"[{t:.2f}s] Mouse Move: ({x}, {y})")

    def on_click(self, x, y, button, pressed):
        t = time.monotonic() - self.start_time
        action = 'pressionou' if pressed else 'soltou'
        event = {'time': t, 'type': 'click', 'pos': (x, y), 'button': button, 'pressed': pressed}
        display = f"[{t:.2f}s] Mouse {action}: {button}"
        self._record_event(event, display)

    def on_scroll(self, x, y, dx, dy):
        t = time.monotonic() - self.start_time
        event = {'time': t, 'type': 'scroll', 'pos': (x, y), 'scroll': (dx, dy)}
        display = f"[{t:.2f}s] Mouse Scroll: ({dx}, {dy})"
        self._record_event(event, display)

