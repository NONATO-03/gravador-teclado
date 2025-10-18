"""
Módulo de Gerenciamento de Janela

Fornece utilitários para interagir com as janelas do sistema operacional,
como obter a janela ativa. Requer a biblioteca 'pygetwindow'.
"""
import pygetwindow as gw
import logging

def get_active_window_title():
    """
    Retorna o título da janela atualmente em foco.

    Returns:
        str or None: O título da janela ativa ou None se não houver nenhuma.
    """
    try:
        active_window = gw.getActiveWindow()
        if active_window:
            return active_window.title
    except Exception as e:
        # pygetwindow pode lançar exceções em alguns ambientes
        logging.warning(f"Não foi possível obter a janela ativa: {e}")
    return None

def get_last_active_window_title():
    """
    Retorna o título da última janela em foco, ignorando as janelas do próprio app.

    Returns:
        str or None: O título da janela ou None se não encontrar uma adequada.
    """
    try:
        all_windows = gw.getAllTitles()
        app_titles = {"Gravador de Macro", "Configurações"}
        
        for title in all_windows:
            if title and title not in app_titles:
                # Retorna o primeiro título que não pertence ao nosso app
                return title
                
    except Exception as e:
        logging.warning(f"Não foi possível obter a lista de janelas: {e}")
        
    # Fallback para o método original se a lista falhar ou não encontrar nada
    return get_active_window_title()


def is_window_active(title):
    """
    Verifica se a janela ativa contém a string do título fornecido.
    A verificação não é case-sensitive.

    Args:
        title (str): O título (ou parte do título) a ser verificado.

    Returns:
        bool: True se a janela ativa corresponder, False caso contrário.
    """
    if not title:
        # Se nenhum título for especificado, a verificação sempre passa.
        return True
        
    active_title = get_active_window_title()
    if active_title:
        return title.lower() in active_title.lower()
        
    return False
