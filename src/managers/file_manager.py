"""
Módulo de Gerenciamento de Arquivos

Este módulo centraliza a lógica para salvar e carregar as listas de eventos
de macro em arquivos JSON.

Responsabilidades:
- Serializar os eventos (converter objetos para um formato salvável).
- Desserializar os eventos (converter dados do arquivo de volta para objetos).
- Lidar com as caixas de diálogo para salvar e abrir arquivos.
"""
import json
from tkinter import filedialog, messagebox
from pynput.keyboard import Key

def _serialize_event(event):
    """Converte um único evento para um formato serializável em JSON."""
    serializable_event = event.copy()
    
    # Converte o botão do mouse para string
    if 'button' in serializable_event:
        serializable_event['button'] = str(serializable_event['button'])
        
    # Converte a tecla do teclado para string
    if 'key' in serializable_event:
        key_obj = serializable_event['key']
        # Para objetos de tecla pynput, usamos o nome
        if hasattr(key_obj, 'name'):
            serializable_event['key'] = key_obj.name
        # Para caracteres (já são strings), mantemos como está
        elif isinstance(key_obj, str):
            serializable_event['key'] = key_obj
        else:
            serializable_event['key'] = str(key_obj)
            
    return serializable_event

def save_events_to_file(events):
    """
    Abre uma caixa de diálogo para salvar eventos em um arquivo JSON.

    Args:
        events (list): A lista de eventos gravados.
    
    Returns:
        bool: True se o arquivo foi salvo com sucesso, False caso contrário.
    """
    if not events:
        messagebox.showwarning("Aviso", "Nenhuma ação gravada para salvar.")
        return False

    file_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    
    if not file_path:
        return False

    try:
        serializable_events = [_serialize_event(e) for e in events]
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_events, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Sucesso", "Ações gravadas salvas com sucesso.")
        return True
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível salvar as ações: {e}")
        return False

def load_events_from_file():
    """
    Abre uma caixa de diálogo para carregar eventos de um arquivo JSON.

    Returns:
        list or None: A lista de eventos carregados ou None se a operação falhar ou for cancelada.
    """
    file_path = filedialog.askopenfilename(
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )

    if not file_path:
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        # A desserialização completa da tecla (para objeto) é complexa e agora
        # é tratada pela camada de UI (`actions_display`) para exibição e pelo
        # `player` durante a execução. Aqui, apenas garantimos que a estrutura
        # básica seja carregada. O player e a UI saberão como lidar com as strings.

        messagebox.showinfo("Sucesso", "Ações carregadas com sucesso.")
        return loaded_data
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível carregar as ações: {e}")
        return None
