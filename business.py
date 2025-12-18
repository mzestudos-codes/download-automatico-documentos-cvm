import re
import os
import time
from datetime import datetime
from infra import CVMClient, FileManager

class DataParser:
    @staticmethod
    def processar_dados_brutos(raw_string, apenas_ativos=True):
        documentos_processados = []
        registros = raw_string.split('*')
        for registro in registros:
            if not registro or len(registro) < 50: continue
            campos = registro.split('$&')
            if len(campos) > 7:
                status = campos[7].strip()
                if apenas_ativos and status.lower() != "ativo": continue
                
                cod_cvm = re.sub(r'\D', '', campos[0].strip()).zfill(6)
                padrao_dl = r"OpenDownloadDocumentos\('(\d+)','(\d+)','([\w-]+)','(.*?)'\)"
                match = re.search(padrao_dl, registro)
                
                if match:
                    documentos_processados.append({
                        "empresa": campos[1].strip(),
                        "categoria": campos[2].strip(),
                        "cod_cvm": cod_cvm,
                        "ids": match.groups()
                    })
        return documentos_processados

class DownloadManager:
    def __init__(self):
        self.client = CVMClient()
        self.file_mgr = FileManager()
        self.parser = DataParser()

    def iniciar_fluxo(self, data_de, data_ate, cod_categoria, callback_progresso=None):
        ts_pasta = datetime.now().strftime("%Y%m%d_%H%M%S")
        pasta_execucao = os.path.abspath(os.path.join("Downloads", f"Downloads_{ts_pasta}"))
        self.file_mgr.criar_diretorio(pasta_execucao)

        payload_consulta = {
            "dataDe": data_de, "dataAte": data_ate, "empresa": "",
            "setorAtividade": "-1", "categoriaEmissor": "-1", "situacaoEmissor": "-1",
            "tipoParticipante": "-1", "dataReferencia": "", "categoria": cod_categoria,
            "periodo": "2", "horaIni": "", "horaFim": "", "palavraChave": "",
            "ultimaDtRef": "false", "tipoEmpresa": "0", "token": "", "versaoCaptcha": ""
        }

        res_json = self.client.consultar(payload_consulta)
        dados_brutos = res_json.get('d', {}).get('dados', "")
        lista_docs = self.parser.processar_dados_brutos(dados_brutos)
        
        total = len(lista_docs)
        if total == 0: return 0, pasta_execucao

        report_ids = '1030,1000,1060,1090,1120,1150,1180,1210,1240,1270,1300,1330,1360,1390,1420,1450,1480,0,2030,2000,2060,2090,2120,2150,2180,2210,2240,2270,2300,2330,3030,3000,3060,4030,4000,4060,4090,4120,4150,4180,4210,5030,5000,5060,5090,5120,5150,6030,6000,6090,6120,6150,6180,7030,7000,7045,7060,7090,7120,7150,7180,7210,7240,8030,8000,8060,8095,8120,8155,8180,8210,8240,8270,8300,8335,8360,8390,8420,8450,8480,8510,8540,8545,8570,8575,8600,9030,9000,9045,9060,10045,10000,10030,10060,10090,10095,10120,10150,11030,11000,11060,11020,11090,12030,12000,12060,12090,12120,12150,12180,12210,12240,12270,13030,13000,13045'

        for i, doc in enumerate(lista_docs):
            item_atual = i + 1
            cat = doc['categoria'].upper()
            seq = doc["ids"][0]
            
            print(f"[{item_atual}/{total}] Processando: {doc['empresa'][:30]}...")
            
            if any(x in cat for x in ["FRE", "ITR", "DFP", "FCA"]):
                # Captura o Hash para este documento específico
                hash_dinamico = self.client.capturar_hash_e_cookies(seq)
                
                tipo_doc = "FREWEB" if "FRE" in cat else "ITRWEB"
                if "DFP" in cat: tipo_doc = "DFPWEB"
                
                payload_pdf = {
                    "reportIds": report_ids, 
                    "nrSequencialDocumento": seq,
                    "codigoCVM": doc["cod_cvm"],
                    "tipoDocumento": tipo_doc,
                    "Hash": hash_dinamico,
                    "token": "", "versaoCaptcha": ""
                }
                conteudo_pdf = self.client.baixar_via_relatorio(payload_pdf)
                time.sleep(1.5) # Pausa para o servidor respirar
            else:
                params = {"Tela": "ext", "numSequencia": seq, "numVersao": doc["ids"][1], "numProtocolo": doc["ids"][2], "descTipo": doc["ids"][3], "CodigoInstituicao": "1"}
                conteudo_pdf = self.client.baixar_arquivo_estatico(params)

            if conteudo_pdf:
                # Sanitização do nome
                empresa_nome = re.sub(r'[\\/*?:"<>|]', "_", doc['empresa'][:30])
                nome_final = f"{empresa_nome}_{cat[:3]}_v{doc['ids'][1]}.pdf"
                self.file_mgr.salvar_arquivo(conteudo_pdf, nome_final, pasta_execucao)
            
            if callback_progresso:
                callback_progresso((item_atual/total)*100, item_atual, total)
        
        return total, pasta_execucao