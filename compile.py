import os
import subprocess
import customtkinter
import sys
import shutil

# 1. Localiza a pasta da biblioteca CustomTkinter
ctk_path = os.path.dirname(customtkinter.__file__)
separator = ";" if sys.platform.startswith("win") else ":"

# Limpeza manual de pastas anteriores para evitar conflitos de permissão
for folder in ['build', 'dist']:
    if os.path.exists(folder):
        shutil.rmtree(folder)

# 2. Configurações do PyInstaller
comando = [
    "pyinstaller",
    "--noconsole",
    "--onefile",
    "--clean",
    # Usando strings formatadas com aspas para evitar erro de caminhos com espaços
    f"--add-data=categorias.json{separator}.",
    f"--add-data={ctk_path}{separator}customtkinter",
    "--collect-all=pandas",
    "--collect-all=openpyxl",
    "--name=CVM_Downloader",
    "main.py"
]

print(">>> Iniciando a criação do Executável...")
try:
    subprocess.run(comando, check=True)
    print("\n" + "="*30)
    print("SUCESSO! Seu arquivo .exe está na pasta 'dist'.")
    print("="*30)
except Exception as e:
    print(f"\nERRO: {e}")