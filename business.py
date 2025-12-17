import re
import os
import json
from datetime import datetime
from infra import CVMClient, FileManager

class DataParser:
    """Interpretador especializado na string de dados complexa da CVM."""
    @staticmethod
    def processar_dados_brutos(raw_string):
        documentos_processados = []
        registros = raw_string.split('*')
        for registro in registros:
            if not registro: continue
            campos = registro.split('$&')
            if len(campos) > 5:
                empresa = campos[1].strip()
                categoria = campos[2].strip()
                padrao_dl = r"OpenDownloadDocumentos\('(\d+)','(\d+)','(\d+)','(\w+)'\)"
                match = re.search(padrao_dl, registro)
                if match:
                    documentos_processados.append({
                        "empresa": empresa,
                        "categoria": categoria,
                        "ids": match.groups()
                    })
        return documentos_processados

class CategoryExtractor:
    """Lê o arquivo JSON pré-convertido."""
    @staticmethod
    def carregar_do_json(caminho="categorias.json"):
        if not os.path.exists(caminho): return []
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            return [f"{item['id']} -> {item['nome']}" for item in dados]
        except Exception as e:
            print(f"[ERRO] Falha ao ler categorias.json: {e}")
            return []

class DownloadManager:
    """Orquestrador que gerencia o fluxo e reporta progresso."""
    def __init__(self):
        self.client = CVMClient()
        self.parser = DataParser()
        self.file_mgr = FileManager()

    def iniciar_fluxo(self, data_de, data_ate, cod_categoria, callback_progresso=None):
        ts_pasta = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Criamos o caminho absoluto para facilitar a abertura da pasta depois
        pasta_execucao = os.path.abspath(os.path.join("Downloads", f"Downloads_{ts_pasta}"))
        self.file_mgr.criar_diretorio(pasta_execucao)

        payload = {
            "dataDe": data_de, "dataAte": data_ate, "empresa": "",
            "setorAtividade": "-1", "categoriaEmissor": "-1", "situacaoEmissor": "-1",
            "tipoParticipante": "-1", "dataReferencia": "", "categoria": cod_categoria,
            "periodo": "2", "horaIni": "", "horaFim": "", "palavraChave":"",
            "ultimaDtRef":"false", "tipoEmpresa":"0", "token": "", "versaoCaptcha": ""
        }

        res_json = self.client.consultar(payload)
        dados_brutos = res_json.get('d', {}).get('dados', "")
        lista_docs = self.parser.processar_dados_brutos(dados_brutos)
        
        total = len(lista_docs)
        if total == 0: return 0, pasta_execucao

        for i, doc in enumerate(lista_docs):
            item_atual = i + 1
            ids = doc["ids"]
            params = {
                "Tela": "ext", "numSequencia": ids[0], "numVersao": ids[1],
                "numProtocolo": ids[2], "descTipo": ids[3], "CodigoInstituicao": "1"
            }
            
            conteudo_pdf = self.client.baixar(params)
            ts_arquivo = datetime.now().strftime("%H%M%S")
            nome_base = f"{doc['empresa']}_{doc['categoria']}_{ts_arquivo}.pdf"
            nome_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_base)
            
            self.file_mgr.salvar_arquivo(conteudo_pdf, nome_limpo, pasta_execucao)
            
            if callback_progresso:
                percentual = (item_atual / total) * 100
                callback_progresso(percentual, item_atual, total)
            
        return total, pasta_execucao