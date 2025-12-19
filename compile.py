import os
import subprocess
import customtkinter
import sys
import shutil

# 1. Localiza a pasta da biblioteca CustomTkinter
ctk_path = os.path.dirname(customtkinter.__file__)
separator = ";" if sys.platform.startswith("win") else ":"

print(">>> Limpando ambiente...")
for folder in ['build', 'dist']:
    if os.path.exists(folder):
        try:
            shutil.rmtree(folder)
        except Exception as e:
            print(f"Aviso: Não foi possível deletar {folder}: {e}")

# 2. Configurações do PyInstaller
comando = [
    "pyinstaller",
    "--noconsole",
    "--onefile",
    "--clean",
    # Arquivo de dados (JSON)
    f"--add-data=categorias.json{separator}.",
    # Biblioteca CustomTkinter (Essencial para o visual)
    f"--add-data={ctk_path}{separator}customtkinter",
    # Forçar a inclusão dos seus módulos locais
    "--hidden-import=business",
    "--hidden-import=infra",
    # Coleta de pacotes pesados
    "--collect-all=pandas",
    "--collect-all=openpyxl",
    # Nome do executável
    "--name=CVM_Downloader",
    "main.py"
]

print(f">>> Comando preparado. Iniciando compilação...")
try:
    # shell=True ajuda no Windows a localizar o executável do pyinstaller no PATH
    subprocess.run(comando, check=True, shell=sys.platform.startswith("win"))
    
    print("\n" + "="*30)
    print("SUCESSO! Seu arquivo .exe está na pasta 'dist'.")
    print("DICA: Certifique-se de que o arquivo 'categorias.json' estava na mesma pasta deste script.")
    print("="*30)
except subprocess.CalledProcessError as e:
    print(f"\nERRO NO PYINSTALLER: {e}")
except Exception as e:
    print(f"\nERRO GERAL: {e}")