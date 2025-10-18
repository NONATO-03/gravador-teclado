import tkinter as tk
from tkinter import ttk
from pynput.keyboard import Key

class ActionsDisplay:
    """
    Gerencia a criação e atualização da área de exibição de ações gravadas
    usando um Treeview para agrupar movimentos do mouse.
    """
    def __init__(self, parent_frame):
        """
        Inicializa o frame e o widget Treeview para exibição de ações.

        Args:
            parent_frame (tk.Frame): O frame pai onde este widget será inserido.
        """
        actions_frame = tk.LabelFrame(parent_frame, text="Ações Gravadas", padx=10, pady=10)
        actions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(actions_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview
        self.tree = ttk.Treeview(actions_frame, yscrollcommand=scrollbar.set, columns=('Tempo', 'Ação', 'Detalhes'), show='headings')
        self.tree.heading('Tempo', text='Tempo')
        self.tree.heading('Ação', text='Ação')
        self.tree.heading('Detalhes', text='Detalhes')
        self.tree.column('Tempo', width=60, anchor='center')
        self.tree.column('Ação', width=120)
        self.tree.column('Detalhes', width=250)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        # Mapeamento de nomes de teclas para exibição amigável
        self.KEY_NAME_MAP = {
            'space': 'Espaço',
            'enter': 'Enter',
            'backspace': 'Backspace',
            'shift': 'Shift',
            'shift_r': 'Shift Dir',
            'ctrl': 'Ctrl',
            'ctrl_l': 'Ctrl Esq',
            'ctrl_r': 'Ctrl Dir',
            'alt': 'Alt',
            'alt_l': 'Alt Esq',
            'alt_gr': 'Alt Gr',
            'cmd': 'Cmd',
            'cmd_l': 'Cmd Esq',
            'cmd_r': 'Cmd Dir',
            'tab': 'Tab',
            'caps_lock': 'Caps Lock',
            'esc': 'Esc',
        }

    def clear(self):
        """Limpa todos os itens do Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def add_action(self, action_text):
        """
        Este método não é usado com a lógica de agrupamento do Treeview,
        pois a atualização é feita em lote.
        """
        pass # Não faz nada, a atualização é feita via update()

    def update(self, events):
        """
        Atualiza o Treeview com uma lista completa de eventos, agrupando
        os movimentos do mouse.

        Args:
            events (list): A lista de dicionários de eventos a serem exibidos.
        """
        self.clear()
        if not events:
            return

        i = 0
        while i < len(events):
            event = events[i]
            
            # Tenta agrupar eventos consecutivos idênticos (que não sejam 'move')
            if i + 1 < len(events) and event.get('type') != 'move':
                
                # Formata o evento atual para ver como ele é
                action_str, details_str = self._format_event(event)
                
                # Conta quantos eventos seguintes são idênticos
                count = 1
                j = i + 1
                while j < len(events):
                    next_action_str, next_details_str = self._format_event(events[j])
                    if events[j].get('type') != 'move' and action_str == next_action_str and details_str == next_details_str:
                        count += 1
                        j += 1
                    else:
                        break
                
                # Se houver mais de um evento igual, cria um grupo
                if count > 1:
                    start_time = event.get('time', 0)
                    
                    # Cria o nó pai para o grupo
                    parent_id = self.tree.insert(
                        '', 
                        tk.END, 
                        values=(f"{start_time:.2f}s", f"{action_str} [x{count}]", details_str)
                    )
                    
                    # Adiciona cada evento repetido como um filho
                    for k in range(i, i + count):
                        repeated_event = events[k]
                        time_str = f"[{repeated_event.get('time', 0):.2f}s]"
                        rep_action, rep_details = self._format_event(repeated_event)
                        self.tree.insert(parent_id, tk.END, values=(time_str, rep_action, rep_details))
                    
                    i += count # Pula todos os eventos que foram agrupados
                    continue # Volta para o início do loop

            # Se for um evento de movimento, agrupa com os próximos
            if event.get('type') == 'move':
                move_group = []
                start_time = event.get('time', 0)
                
                # Coleta todos os eventos 'move' consecutivos
                while i < len(events) and events[i].get('type') == 'move':
                    move_group.append(events[i])
                    i += 1
                
                end_time = move_group[-1].get('time', 0)
                duration = end_time - start_time
                
                # Cria o nó pai para o grupo de movimentos
                parent_id = self.tree.insert(
                    '', 
                    tk.END, 
                    values=(f"{start_time:.2f}s", "Mover Mouse", f"{len(move_group)} movimentos em {duration:.2f}s")
                )
                
                # Adiciona cada movimento como um filho do nó pai
                for move_event in move_group:
                    time_str = f"[{move_event.get('time', 0):.2f}s]"
                    pos_str = f"Para: {move_event.get('pos')}"
                    self.tree.insert(parent_id, tk.END, values=(time_str, "Moveu", pos_str))
            
            else:
                # Para outros tipos de evento (ou eventos únicos), adiciona uma linha normal
                time_str = f"{event.get('time', 0):.2f}s"
                action_str, details_str = self._format_event(event)
                self.tree.insert('', tk.END, values=(time_str, action_str, details_str))
                i += 1

    def _deserialize_key(self, key_data):
        """Converte uma string de volta para um objeto de tecla pynput, se necessário."""
        if key_data is None:
            return None
        # Se for uma string de uma tecla especial (ex: 'Key.space'), converte para objeto Key
        if isinstance(key_data, str) and key_data.startswith('Key.'):
             key_name = key_data.split('.')[-1]
             if hasattr(Key, key_name):
                 return getattr(Key, key_name)
        # Se for uma string de um caractere simples
        if isinstance(key_data, str):
            return key_data
        # Se já for um objeto Key ou KeyCode, retorna como está
        return key_data

    def _format_event(self, event):
        """Formata um único evento para exibição no Treeview."""
        event_type = event.get('type')
        
        if event_type in ['key_press', 'key_release', 'key_tap']:
            action_map = {
                'key_press': "Pressionar Tecla",
                'key_release': "Soltar Tecla",
                'key_tap': "Apertar Tecla"
            }
            action_str = action_map[event_type]
            
            key_data = self._deserialize_key(event.get('key'))

            key_display = ""
            if hasattr(key_data, 'name'):
                # É uma tecla especial (Key.space, Key.ctrl, etc.)
                key_display = self.KEY_NAME_MAP.get(key_data.name, key_data.name.capitalize())
            elif hasattr(key_data, 'char'):
                # É uma tecla de caractere normal (KeyCode)
                key_display = f"'{key_data.char}'"
            else:
                # Fallback para casos inesperados (como strings que não foram desserializadas)
                key_display = str(key_data)

            details_str = f"Tecla: {key_display}"
            return action_str, details_str

        elif event_type == 'click':
            action = 'Pressionar' if event.get('pressed') else 'Soltar'
            button_name = str(event.get('button')).split('.')[-1]
            return f"{action} Mouse", f"Botão: {button_name} em {event.get('pos')}"

        elif event_type == 'scroll':
            direction = "Cima" if event.get('scroll')[1] > 0 else "Baixo"
            return "Scroll", f"Direção: {direction} em {event.get('pos')}"
        
        return "Evento Desconhecido", str(event)