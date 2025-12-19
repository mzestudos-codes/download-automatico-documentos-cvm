import requests
import base64
import re
import os
import html

class CVMClient:
    def __init__(self):
        self.session = requests.Session()
        self.headers_base = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json; charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.rad.cvm.gov.br"
        }

    def consultar(self, payload):
        url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx/ListarDocumentos"
        try:
            response = self.session.post(url, json=payload, headers=self.headers_base, timeout=40)
            data = response.json()
            # Tratamento vital: Converte \u0026 em & e outros escapes HTML
            if 'd' in data and 'dados' in data['d']:
                data['d']['dados'] = html.unescape(data['d']['dados'])
            return data
        except:
            return {}

    def capturar_hash_dinamico(self, seq):
        url = f"https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={seq}&CodigoTipoInstituicao=1"
        try:
            headers = self.headers_base.copy()
            headers["Referer"] = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
            response = self.session.get(url, headers=headers, timeout=30)
            match = re.search(r'id="hdnHash"\s+value="(.*?)"', response.text)
            if not match:
                match = re.search(r"Hash:\s*'(.*?)'", response.text)
            return match.group(1) if match else ""
        except:
            return ""

    def baixar_via_relatorio(self, payload):
        url = "https://www.rad.cvm.gov.br/ENET/frmRelatorioPDF.aspx/GerarRelatorio"
        try:
            headers = self.headers_base.copy()
            headers["Referer"] = f"https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={payload['nrSequencialDocumento']}&CodigoTipoInstituicao=1"
            response = self.session.post(url, json=payload, headers=headers, timeout=300)
            base64_string = response.json().get('d', '')
            return base64.b64decode(base64_string) if base64_string else b""
        except:
            return b""

    def baixar_arquivo_estatico(self, params):
        url = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx"
        try:
            response = self.session.get(url, params=params, headers=self.headers_base, timeout=60)
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
        nome_valido = re.sub(r'[\\/*?:"<>|]', "", nome)
        with open(os.path.join(pasta, nome_valido), 'wb') as f:
            f.write(conteudo)