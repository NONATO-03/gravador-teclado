"""
Módulo do Gerenciador de Atalhos (Hotkeys)

Este módulo contém a classe `HotkeyManager`, responsável por ouvir
combinações de teclas globais em segundo plano, usando a classe
`pynput.keyboard.GlobalHotKeys`.

Responsabilidades:
- Iniciar e parar um listener de hotkeys em uma thread separada.
- Mapear strings de atalhos (ex: '<f9>') para funções de callback.
- Ser seguro para threads, permitindo que seja atualizado dinamicamente.
"""
import threading
import logging
from pynput import keyboard

class HotkeyManager:
    """Gerencia o listener de atalhos globais."""
    def __init__(self):
        self.listener = None
        self.thread = None

    def _string_to_key(self, key_str):
        """Converte uma string de configuração de volta para um objeto de tecla."""
        if key_str is None:
            return None
        if key_str.startswith("Key."):
            key_name = key_str.split('.')[-1]
            return getattr(keyboard.Key, key_name, None)
        return keyboard.KeyCode.from_char(key_str)

    def format_key_string(self, key_str):
        """Formata a string da tecla para o formato que o GlobalHotKeys espera."""
        if key_str is None:
            return None
        
        # Se for uma tecla especial como 'f9', 'space', etc.
        if len(key_str) > 1 and not key_str.startswith("Key."):
             return f'<{key_str}>'
        
        # Se for uma tecla especial já formatada
        if key_str.startswith("Key."):
            key_name = key_str.split('.')[-1]
            # Mapeia nomes comuns para o formato correto
            if key_name in ['shift', 'ctrl', 'alt']:
                return f'<{key_name}>'
            return f'<{key_name}>'

        # Se for um caractere simples
        return key_str

    def update_listener(self, hotkeys):
        """
        Para o listener atual e inicia um novo com os atalhos fornecidos.

        Args:
            hotkeys (dict): Um dicionário mapeando strings de atalho para callbacks.
                            Ex: {'<f9>': func_para_f9}
        """
        self.stop_listener()
        
        if not hotkeys:
            return
            
        # O listener é executado em uma thread separada para não bloquear a GUI
        self.thread = threading.Thread(target=self._run, args=(hotkeys,), daemon=True)
        self.thread.start()

    def _run(self, hotkeys):
        """Esta função é o alvo da thread e mantém o listener ativo."""
        try:
            # GlobalHotKeys é um gerenciador de contexto que simplifica o join
            with keyboard.GlobalHotKeys(hotkeys) as self.listener:
                self.listener.join()
        except Exception as e:
            # Em uma aplicação real, isso seria logado de forma mais robusta
            logging.error(f"Erro na thread do listener de atalhos: {e}")

    def stop_listener(self):
        """Para o listener de atalhos e sua thread de forma segura."""
        if self.listener:
            self.listener.stop()
        if self.thread and self.thread.is_alive():
            # A chamada stop() acima deve fazer com que a thread termine.
            # Damos um pequeno timeout para garantir.
            self.thread.join(timeout=0.1)
        self.listener = None
        self.thread = None

