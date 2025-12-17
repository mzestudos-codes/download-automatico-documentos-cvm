import logging
import requests
import os

# Configuração do Logging
log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler("execucao.log", encoding='utf-8'), # Salva em arquivo
        logging.StreamHandler() # Mostra no terminal
    ]
)
logger = logging.getLogger("CVM_Automation")

class FileManager:
    """Gerencia a criação de diretórios e escrita de arquivos."""
    @staticmethod
    def criar_diretorio(caminho):
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        return caminho

    @staticmethod
    def salvar_arquivo(conteudo, nome_arquivo, pasta_destino):
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)
        with open(caminho_completo, 'wb') as f:
            f.write(conteudo)

class CVMClient:
    """Cliente HTTP para o portal ENET CVM."""
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.base_url = "https://www.rad.cvm.gov.br/ENET"

    def consultar(self, payload):
        url = f"{self.base_url}/frmConsultaExternaCVM.aspx/ListarDocumentos"
        res = requests.post(url, json=payload, headers=self.headers)
        res.raise_for_status()
        return res.json()

    def baixar(self, params):
        url = f"{self.base_url}/frmDownloadDocumento.aspx"
        return requests.get(url, params=params).content