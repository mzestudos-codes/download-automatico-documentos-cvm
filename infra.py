import requests, base64, re, os, html

class CVMClient:
    def __init__(self):
        self.session = requests.Session()
        self.headers_base = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json; charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.rad.cvm.gov.br",
            "Referer": "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
        }

    def consultar(self, payload):
        url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx/ListarDocumentos"
        try:
            # Garante que temos um cookie inicial
            self.session.get("https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx", timeout=20)
            response = self.session.post(url, json=payload, headers=self.headers_base, timeout=40)
            data = response.json()
            if 'd' in data and 'dados' in data['d']:
                data['d']['dados'] = html.unescape(data['d']['dados'])
            return data
        except: return {}

    def capturar_hash_dinamico(self, seq):
        url = f"https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={seq}&CodigoTipoInstituicao=1"
        try:
            # Importante: Para os estruturados, precisamos carregar a página com cabeçalhos de navegação
            headers = self.headers_base.copy()
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            del headers["Content-Type"] # Requisição GET não tem content-type
            
            res = self.session.get(url, headers=headers, timeout=30)
            
            m = re.search(r'id="hdnHash"\s+value="(.*?)"', res.text)
            if not m: m = re.search(r"Hash:\s*'(.*?)'", res.text)
            return m.group(1) if m else ""
        except: return ""

    def baixar_via_relatorio(self, payload):
        url = "https://www.rad.cvm.gov.br/ENET/frmRelatorioPDF.aspx/GerarRelatorio"
        try:
            headers = self.headers_base.copy()
            # Referer obrigatório do popup de relatório
            headers["Referer"] = f"https://www.rad.cvm.gov.br/ENET/frmRelatorioPDF.aspx?CodigoTipoDocumento=9&numeroSequencialDocumento={payload['nrSequencialDocumento']}&Hash={payload['Hash']}"
            
            # Removemos o X-Requested-With para essa chamada específica de relatório
            if "X-Requested-With" in headers: del headers["X-Requested-With"]

            response = self.session.post(url, json=payload, headers=headers, timeout=300)
            res_json = response.json()
            base64_string = res_json.get('d', '')
            if base64_string and len(base64_string) > 1000:
                return base64.b64decode(base64_string)
            return b""
        except: return b""

    def baixar_arquivo_estatico(self, params):
        url = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx"
        try:
            headers = self.headers_base.copy()
            del headers["Content-Type"]
            response = self.session.get(url, params=params, headers=headers, timeout=60)
            return response.content
        except: return b""

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