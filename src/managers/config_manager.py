"""
Arquivo dedicado ao gerencimento das configurações
"""
import json
import os
import logging

CONFIG_FILE = 'config.json'

DEFAULT_CONFIG = {
    "theme": "dark",
    "playback_engine": "Pynput (Padrão)",
    "record_mode": "Teclado e Mouse",
    "hotkeys": {
        "record": None,
        "playback": None
    },
    "window_specific_title": "",
    "pydirectinput_optimized_pause": True
}

def save_config(config):
    """Salva o dicionário de configurações no arquivo JSON."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Erro ao salvar as configurações: {e}")

def load_config():
    """
    Carrega as configurações do arquivo JSON. Caso o arquivo não existir ou estiver corrompido ele retorna a configuração padrão.
    """
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Garante que todas as chaves padrão existam
            for key, value in DEFAULT_CONFIG.items():
                config.setdefault(key, value)
            return config
    except (json.JSONDecodeError, Exception) as e:
        logging.error(f"Erro ao carregar as configurações, usando padrão: {e}")
        return DEFAULT_CONFIG.copy()
