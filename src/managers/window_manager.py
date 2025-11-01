import pygetwindow as gw
import logging

def get_active_window_title():
    """
    Retorna o título da janela que esta focalizada

    Returns:
        str or None: O título da janela ativa ou None se não houver nenhuma
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
        # Títulos das janelas do nosso aplicativo a serem ignoradas
        app_titles = {"Gravador de Macro", "Configurações", ""}

        # gw.getAllWindows() retorna uma lista de objetos de janela
        all_windows = gw.getAllWindows()

        # A janela ativa no momento será a de Configurações ou a principal
        current_active_window = gw.getActiveWindow()

        for window in all_windows:
            # Ignora a janela que está ativa no momento
            if window == current_active_window:
                continue
            
            # Ignora janelas sem título ou que pertencem ao app
            if window.title in app_titles:
                continue

            # Ignora janelas minimizadas, pois provavelmente não são o alvo
            if not window.isMaximized and not window.isRestored:
                continue

            # Retorna o título da primeira janela encontrada que atende aos critérios
            return window.title
                
    except Exception as e:
        logging.warning(f"Não foi possível obter a lista de janelas: {e}")
        
    # Fallback para o método original se a lógica acima falhar
    active_window = gw.getActiveWindow()
    return active_window.title if active_window else None


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
