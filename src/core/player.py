"""
Este arquivo é responsável por reproduzir o macro

"""

import time
import logging
from pynput import keyboard, mouse
import pyautogui
import pydirectinput

from ..managers import window_manager

# Otimizações para PyDirectInput -
pydirectinput.PAUSE = 0.01  # Reduz a pausa padrão entre os comandos
pydirectinput.FAILSAFE = False # failsafe é ativado quando o mouse é movido para o canto da tela

class MacroPlayer:
    """
    Executa uma sequência de eventos de teclado e mouse.
    """
    def __init__(self):
        self.keyboard_controller = keyboard.Controller()
        self.mouse_controller = mouse.Controller()
        self.was_skipped = False
        self.engine = "pynput"
        self.use_optimized_pause = True

    def set_engine(self, engine_name, pydirectinput_pause=True):
        """Define o motor de reprodução e suas configurações."""
        if "Pynput" in engine_name:
            self.engine = "pynput"
        elif "PyAutoGUI" in engine_name:
            self.engine = "pyautogui"
        elif "PyDirectInput" in engine_name:
            self.engine = "pydirectinput"
        else:
            self.engine = "pynput" # Padrão
        
        self.use_optimized_pause = pydirectinput_pause

    def play(self, events, stop_signal, window_title=None):
        """
        Função de reprodução de macro

        Argumentos possíveis:
            events (list): A lista de dicionários de eventos a serem reproduzidos
            stop_signal (threading.Event): Um evento que quando definido interrompe a reprodução
            window_title (str, opcional): O título da janela onde a macro deve ser executada
        """
        if not events:
            return

        self.was_skipped = False

        # Se um título de janela for especificado, vai ver se ela tá ativa antes de começar
        if window_title and not window_manager.is_window_active(window_title):
            logging.warning(f"Reprodução pulada. Janela '{window_title}' não está ativa.")
            self.was_skipped = True
            return

        original_pause = pydirectinput.PAUSE
        if self.engine == 'pydirectinput':
            pydirectinput.PAUSE = 0.01 if self.use_optimized_pause else 0.1
        
        try:
            last_event_time = 0
            for event in events:
                if stop_signal.is_set():
                    break

                # Verifica a janela ativa antes de cada evento caso seja necessario
                if window_title and not window_manager.is_window_active(window_title):
                    logging.warning(f"Reprodução interrompida. Janela '{window_title}' não está mais ativa.")
                    self.was_skipped = True
                    break

                delay = event['time'] - last_event_time
                if delay > 0:
                    time.sleep(delay)
                
                if stop_signal.is_set():
                    break

                self._execute_event(event)
                last_event_time = event['time']
        finally:
            # Garante que a pausa seja restaurada ao valor original
            pydirectinput.PAUSE = original_pause

    def _execute_event(self, event):
        """
        Executa um único evento usando o motor especificado pelo usuário.
        """
        event_type = event.get('type')
        engine = self.engine
        
        try:
            if event_type == 'key_tap':
                key_str = self._get_key_string(event['key'])
                if engine == 'pydirectinput':
                    pydirectinput.press(key_str)
                else:
                    self.keyboard_controller.tap(event['key'])
            elif event_type == 'key_press':
                key_str = self._get_key_string(event['key'])
                if engine == 'pydirectinput':
                    pydirectinput.keyDown(key_str)
                else:
                    self.keyboard_controller.press(event['key'])
            elif event_type == 'key_release':
                key_str = self._get_key_string(event['key'])
                if engine == 'pydirectinput':
                    pydirectinput.keyUp(key_str)
                else:
                    self.keyboard_controller.release(event['key'])
            elif event_type == 'move':
                x, y = event['pos']
                if engine == 'pydirectinput':
                    pydirectinput.moveTo(x, y, duration=0) # Movimento instantâneo
                else:
                    self.mouse_controller.position = (x, y)
            elif event_type == 'click':
                self._handle_click(event, engine)
            elif event_type == 'scroll':
                self.mouse_controller.position = event['pos']
                self.mouse_controller.scroll(event['scroll'][0], event['scroll'][1])
        except Exception as e:
            logging.error(f"Erro ao executar o evento {event} com o motor {engine}: {e}")

    def _handle_click(self, event, engine):
        """Lida com eventos de clique usando o motor especificado."""
        x, y = event['pos']
        button_str = str(event['button']).split('.')[-1]

        if engine == 'pyautogui':
            if event['pressed']:
                pyautogui.mouseDown(x=x, y=y, button=button_str)
            else:
                pyautogui.mouseUp(x=x, y=y, button=button_str)
        elif engine == 'pydirectinput':
            pydirectinput.moveTo(x, y, duration=0) # Movimento instantâneo
            if event['pressed']:
                pydirectinput.mouseDown(button=button_str)
            else:
                pydirectinput.mouseUp(button=button_str)
        else: # Padrão para pynput
            self.mouse_controller.position = (x, y)
            time.sleep(0.01)
            self.mouse_controller.position = (x, y)
            
            from pynput.mouse import Button
            button = event['button']
            if isinstance(button, str):
                button = getattr(Button, button_str, None)
            
            if button:
                if event['pressed']:
                    self.mouse_controller.press(button)
                else:
                    self.mouse_controller.release(button)

    def _get_key_string(self, key):
        """Converte um objeto de tecla pynput para uma string que pydirectinput compreende"""
        # Tenta obter o caractere da tecla se for uma tecla normal 
        if hasattr(key, 'char') and key.char:
            return key.char

        # Para teclas especiais pega o nome
        if hasattr(key, 'name'):
            return key.name
            
        # Caso fallback converte para string
        return str(key)
