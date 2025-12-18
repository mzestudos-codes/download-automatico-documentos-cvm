import re
import os
import time
import unicodedata
import pandas as pd
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
    def extrair_data_limpa(texto_bruto):
        if not texto_bruto: return "-"
        limpo = re.sub(r'<.*?>', '', texto_bruto).strip()
        partes = limpo.split(' ')
        if len(partes) > 1:
            return " ".join(partes[1:])
        return limpo

    @staticmethod
    def processar_dados_completos(raw_string):
        documentos = []
        if not raw_string: return []
        registros = raw_string.split('*')
        for registro in registros:
            if not registro or len(registro) < 50: continue
            campos = registro.split('$&')
            if len(campos) > 10:
                status = campos[7].strip()
                if status.lower() != "ativo": continue 

                match_ids = re.search(r"OpenDownloadDocumentos\('(\d+)','(\d+)','(\d+)','(.*?)'\)", registro)
                if match_ids:
                    seq, versao, protocolo, modalidade = match_ids.groups()
                    dt_ref = DataParser.extrair_data_limpa(campos[5])
                    dt_ent = DataParser.extrair_data_limpa(campos[6])
                    
                    documentos.append({
                        "Código CVM": campos[0].strip(),
                        "Empresa": campos[1].strip(),
                        "Categoria": campos[2].strip(),
                        "Tipo": campos[3].strip(),
                        "Espécie": campos[11].strip() if len(campos) > 11 else "-",
                        "Data Referência": dt_ref,
                        "Data Entrega": dt_ent,
                        "Status": status,
                        "V": versao,
                        "Modalidade": modalidade,
                        "LINK": f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoIPEExterno.aspx?NumeroProtocoloEntrega={protocolo}",
                        "_ID_SEQ": seq,
                        "_PROTOCOLO": protocolo
                    })
        return documentos

class DownloadManager:
    def __init__(self):
        self.client = CVMClient()
        self.file_mgr = FileManager()
        self.parser = DataParser()

    def iniciar_fluxo(self, modo, data_de, data_ate, cod_id, nome_categoria, palavra_chave="", 
                      tipo_part="-1", sit_emissor="-1", cat_emissor="-1", callback_progresso=None):
        
        cat_limpa = self.parser.limpar_nome(nome_categoria)
        prefixo = "Downloads" if modo == "download" else "Base" if modo == "planilha" else "Coleta_Completa"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S") # Timestamp para pasta e arquivo
        
        pasta_execucao = os.path.abspath(os.path.join(prefixo, f"{prefixo}_{cat_limpa}_{ts}"))
        self.file_mgr.criar_diretorio(pasta_execucao)

        palavras_formatadas = ""
        if palavra_chave:
            termos = [p.strip() for p in palavra_chave.split(',') if p.strip()]
            palavras_formatadas = "," + ",".join(termos)

        payload = {
            "dataDe": data_de, "dataAte": data_ate, "empresa": "",
            "setorAtividade": "-1", "categoriaEmissor": cat_emissor,
            "situacaoEmissor": sit_emissor, "tipoParticipante": tipo_part,
            "dataReferencia": "", "categoria": cod_id, "periodo": "2",
            "horaIni": "", "horaFim": "", "palavraChave": palavras_formatadas,
            "ultimaDtRef": "false", "tipoEmpresa": "0", "token": "", "versaoCaptcha": ""
        }

        res_json = self.client.consultar(payload)
        dados_brutos = res_json.get('d', {}).get('dados', "")
        lista = self.parser.processar_dados_completos(dados_brutos)
        
        total = len(lista)
        if total == 0: return 0, pasta_execucao

        if modo in ["planilha", "ambos"]:
            df = pd.DataFrame(lista)
            df_export = df.drop(columns=['_ID_SEQ', '_PROTOCOLO'])
            # NOME COM TIMESTAMP ADICIONADO AQUI
            nome_xlsx = f"Base_Coleta_{cat_limpa}_{ts}.xlsx"
            caminho_xlsx = os.path.join(pasta_execucao, nome_xlsx)
            df_export.to_excel(caminho_xlsx, index=False)
            if modo == "planilha": return total, pasta_execucao

        rep_ids = '1030,1000,1060,1090,1120,1150,1180,1210,1240,1270,1300,1330,1360,1390,1420,1450,1480,0,2030,2000,2060,2090,2120,2150,2180,2210,2240,2270,2300,2330,3030,3000,3060,4030,4000,4060,4090,4120,4150,4180,4210,5030,5000,5060,5090,5120,5150,6030,6000,6090,6120,6150,6180,7030,7000,7045,7060,7090,7120,7150,7180,7210,7240,8030,8000,8060,8095,8120,8155,8180,8210,8240,8270,8300,8335,8360,8390,8420,8450,8480,8510,8540,8545,8570,8575,8600,9030,9000,9045,9060,10045,10000,10030,10060,10090,10095,10120,10150,11030,11000,11060,11020,11090,12030,12000,12060,12090,12120,12150,12180,12210,12240,12270,13030,13000,13045'
        
        for i, doc in enumerate(lista):
            if callback_progresso: callback_progresso(((i+1)/total)*100, i+1, total)
            if any(x in doc['Categoria'].upper() for x in ["FRE", "ITR", "DFP", "FCA"]):
                h = self.client.capturar_hash_dinamico(doc['_ID_SEQ'])
                t_doc = "FREWEB"
                if "ITR" in doc['Categoria'].upper(): t_doc = "ITRWEB"
                if "DFP" in doc['Categoria'].upper(): t_doc = "DFPWEB"
                payload_pdf = {"reportIds": rep_ids, "nrSequencialDocumento": doc['_ID_SEQ'], "codigoCVM": doc["Código CVM"], "tipoDocumento": t_doc, "Hash": h, "token": "", "versaoCaptcha": ""}
                conteudo_pdf = self.client.baixar_via_relatorio(payload_pdf)
                time.sleep(0.5)
            else:
                params = {"Tela": "ext", "numSequencia": doc['_ID_SEQ'], "numVersao": doc["V"], "numProtocolo": doc["_PROTOCOLO"], "descTipo": doc["Modalidade"], "CodigoInstituicao": "1"}
                conteudo_pdf = self.client.baixar_arquivo_estatico(params)

            if conteudo_pdf:
                emp_f = self.parser.limpar_nome(doc['Empresa'], 80)
                cat_f = self.parser.limpar_nome(doc['Categoria'], 40)
                pc_f = self.parser.limpar_nome(palavra_chave, 40)
                pc_sep = f"_{pc_f}" if pc_f else ""
                nome_final = f"{emp_f}_{cat_f}{pc_sep}_ID{doc['_ID_SEQ']}_v{doc['V']}.pdf"
                self.file_mgr.salvar_arquivo(conteudo_pdf, nome_final, pasta_execucao)
        
        return total, pasta_execucao