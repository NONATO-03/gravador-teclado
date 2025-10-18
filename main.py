"""
Entry Point
"""
import tkinter as tk
from src.app import FullMacroApp    
from src.managers import config_manager
import logging 
import sys
import ctypes
# Importações explícitas para ajudar o PyInstaller
from pynput import keyboard, mouse
import pyautogui
import pydirectinput
import sv_ttk

def main():
    """ 
    inicia a aplicação.
    """
    # Define um ID de modelo de usuário de aplicativo exclusivo para o Windows.
    # Isso ajuda o Windows a agrupar a janela corretamente e usar o ícone certo na barra de tarefas.
    if sys.platform.startswith('win'):
        myappid = 'nonato.action.recorder.v1' # Pode ser qualquer string única
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # Carrega as configurações antes de criar a janela 
    config = config_manager.load_config()
    
    try:
        root = tk.Tk()

        # Aplica o tema com base na configurações carregadas
        sv_ttk.set_theme(config.get("theme", "dark"))

        app = FullMacroApp(root, config) # Passa a config 
        root.mainloop()
    except Exception as e:
        logging.error(f"Ocorreu um erro fatal ao iniciar a aplicação: {e}")
        # Mostra um pop-up de erro antes de fechar
        tk.messagebox.showerror("Erro Crítico", f"Não foi possível iniciar a aplicação.\nErro: {e}")


if __name__ == "__main__":
    main()
