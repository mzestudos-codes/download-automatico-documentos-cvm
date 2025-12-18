import requests
import base64
import re
import os

class CVMClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json; charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.rad.cvm.gov.br",
            "Referer": "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
        })

    def consultar(self, payload):
        url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx/ListarDocumentos"
        try:
            response = self.session.post(url, json=payload, timeout=40)
            return response.json()
        except:
            return {}

    def capturar_hash_dinamico(self, seq):
        url = f"https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={seq}&CodigoTipoInstituicao=1"
        try:
            response = self.session.get(url, timeout=30)
            match = re.search(r"id=\"hdnHash\" value=\"(.*?)\"", response.text)
            if match: return match.group(1)
            match_alt = re.search(r"Hash: '(.*?)'", response.text)
            return match_alt.group(1) if match_alt else ""
        except:
            return ""

    def baixar_via_relatorio(self, payload):
        url = "https://www.rad.cvm.gov.br/ENET/frmRelatorioPDF.aspx/GerarRelatorio"
        try:
            response = self.session.post(url, json=payload, timeout=300)
            response.raise_for_status()
            res_json = response.json()
            base64_string = res_json.get('d', '')
            if base64_string and isinstance(base64_string, str):
                return base64.b64decode(base64_string)
            return b""
        except:
            return b""

    def baixar_arquivo_estatico(self, params):
        url = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx"
        try:
            response = self.session.get(url, params=params, timeout=60)
            return response.content
        except:
            return b""

class FileManager:
    @staticmethod
    def criar_diretorio(caminho):
        if not os.path.exists(caminho): os.makedirs(caminho)

    @staticmethod
    def salvar_arquivo(conteudo, nome, pasta):
        if not conteudo: return
        caminho_final = os.path.join(pasta, nome)
        with open(caminho_final, 'wb') as f:
            f.write(conteudo)