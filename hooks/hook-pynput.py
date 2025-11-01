from PyInstaller.utils.hooks import collect_all

def hook(hook_api):
    # Coleta todos os componentes da biblioteca 'pynput'
    datas, binaries, hiddenimports = collect_all('pynput')

    # Adiciona os componentes encontrados ao hook
    hook_api.add_datas(datas)
    hook_api.add_binaries(binaries)
    hook_api.add_imports(*hiddenimports)
