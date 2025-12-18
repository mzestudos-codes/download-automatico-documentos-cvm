import re
import os
import time
import unicodedata
from datetime import datetime
from infra import CVMClient, FileManager

class DataParser:
    @staticmethod
    def limpar_nome(texto, limite=None):
        if not texto: return ""
        nfkd_form = unicodedata.normalize('NFKD', texto)
        texto_sem_acentos = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        texto_limpo = texto_sem_acentos.replace(" ", "_")
        texto_limpo = re.sub(r'[^a-zA-Z0-9_]', '', texto_limpo)
        texto_limpo = re.sub(r'_+', '_', texto_limpo).strip('_')
        if limite: texto_limpo = texto_limpo[:limite]
        return texto_limpo.upper()

    @staticmethod
    def processar_dados_brutos(raw_string, apenas_ativos=True):
        documentos_processados = []
        inativos_count = 0
        registros = raw_string.split('*')
        
        for registro in registros:
            if not registro or len(registro) < 50: continue
            campos = registro.split('$&')
            
            if len(campos) > 7:
                status = campos[7].strip().lower()
                if status != "ativo":
                    inativos_count += 1
                    if apenas_ativos: continue
                
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
        return documentos_processados, inativos_count

class DownloadManager:
    def __init__(self):
        self.client = CVMClient()
        self.file_mgr = FileManager()
        self.parser = DataParser()

    def iniciar_fluxo(self, data_de, data_ate, cod_id, palavras_brutas="", callback_progresso=None):
        ts_pasta = datetime.now().strftime("%Y%m%d_%H%M%S")
        pasta_execucao = os.path.abspath(os.path.join("Downloads", f"Downloads_{ts_pasta}"))
        self.file_mgr.criar_diretorio(pasta_execucao)

        palavras_formatadas = ""
        if palavras_brutas:
            termos = [p.strip() for p in palavras_brutas.split(',') if p.strip()]
            palavras_formatadas = "," + ",".join(termos)

        payload = {
            "dataDe": data_de, "dataAte": data_ate, "empresa": "",
            "setorAtividade": "-1", "categoriaEmissor": "-1", "situacaoEmissor": "-1",
            "tipoParticipante": "-1", "dataReferencia": "", "categoria": cod_id,
            "periodo": "2", "horaIni": "", "horaFim": "", 
            "palavraChave": palavras_formatadas, "ultimaDtRef": "false", 
            "tipoEmpresa": "0", "token": "", "versaoCaptcha": ""
        }

        res_json = self.client.consultar(payload)
        dados_brutos = res_json.get('d', {}).get('dados', "")
        
        # Agora retorna a lista e quantos inativos ignorou
        lista_docs, inativos = self.parser.processar_dados_brutos(dados_brutos, apenas_ativos=True)
        
        total = len(lista_docs)
        print(f"\n[INFO] Encontrados: {total + inativos} | Ativos: {total} | Inativos: {inativos}")
        
        if total == 0: return 0, pasta_execucao

        report_ids = '1030,1000,1060,1090,1120,1150,1180,1210,1240,1270,1300,1330,1360,1390,1420,1450,1480,0,2030,2000,2060,2090,2120,2150,2180,2210,2240,2270,2300,2330,3030,3000,3060,4030,4000,4060,4090,4120,4150,4180,4210,5030,5000,5060,5090,5120,5150,6030,6000,6090,6120,6150,6180,7030,7000,7045,7060,7090,7120,7150,7180,7210,7240,8030,8000,8060,8095,8120,8155,8180,8210,8240,8270,8300,8335,8360,8390,8420,8450,8480,8510,8540,8545,8570,8575,8600,9030,9000,9045,9060,10045,10000,10030,10060,10090,10095,10120,10150,11030,11000,11060,11020,11090,12030,12000,12060,12090,12120,12150,12180,12210,12240,12270,13030,13000,13045'

        for i, doc in enumerate(lista_docs):
            item_atual = i + 1
            cat_nome = doc['categoria']
            seq_cvm = doc["ids"][0]
            versao = doc["ids"][1]
            
            # --- ATUALIZA A UI ---
            if callback_progresso:
                progresso_percent = (item_atual / total) * 100
                callback_progresso(progresso_percent, item_atual, total)

            if any(x in cat_nome.upper() for x in ["FRE", "ITR", "DFP", "FCA"]):
                h = self.client.capturar_hash_dinamico(seq_cvm)
                t_doc = "FREWEB"
                if "ITR" in cat_nome.upper(): t_doc = "ITRWEB"
                if "DFP" in cat_nome.upper(): t_doc = "DFPWEB"
                
                payload_pdf = {
                    "reportIds": report_ids, "nrSequencialDocumento": seq_cvm,
                    "codigoCVM": doc["cod_cvm"], "tipoDocumento": t_doc,
                    "Hash": h, "token": "", "versaoCaptcha": ""
                }
                conteudo_pdf = self.client.baixar_via_relatorio(payload_pdf)
                time.sleep(1)
            else:
                params = {"Tela": "ext", "numSequencia": seq_cvm, "numVersao": versao, "numProtocolo": doc["ids"][2], "descTipo": doc["ids"][3], "CodigoInstituicao": "1"}
                conteudo_pdf = self.client.baixar_arquivo_estatico(params)

            if conteudo_pdf:
                emp_f = self.parser.limpar_nome(doc['empresa'], 80)
                cat_f = self.parser.limpar_nome(cat_nome, 40)
                pc_f = self.parser.limpar_nome(palavras_brutas, 40)
                pc_sep = f"_{pc_f}" if pc_f else ""
                
                nome_final = f"{emp_f}_{cat_f}{pc_sep}_ID{seq_cvm}_v{versao}.pdf"
                self.file_mgr.salvar_arquivo(conteudo_pdf, nome_final, pasta_execucao)
        
        return total, pasta_execucao