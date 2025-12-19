import re, os, time, unicodedata
import pandas as pd
from datetime import datetime
from infra import CVMClient, FileManager

class DataParser:
    @staticmethod
    def limpar_nome(texto, limite=None):
        if not texto: return "ARQUIVO"
        nfkd_form = unicodedata.normalize('NFKD', texto)
        texto_sem_acentos = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        texto_limpo = texto_sem_acentos.replace(" ", "_")
        texto_limpo = re.sub(r'[^a-zA-Z0-9_]', '', texto_limpo)
        texto_limpo = re.sub(r'_+', '_', texto_limpo).strip('_')
        if limite: texto_limpo = texto_limpo[:limite]
        return texto_limpo.upper()

    @staticmethod
    def extrair_data_limpa(texto_bruto, completa=False):
        """
        Garante DD/MM/AAAA para Referência. 
        Se a CVM enviar apenas o ano (comum no FRE), converte para 31/12/AAAA.
        """
        if not texto_bruto: return "-"
        limpo = re.sub(r'<.*?>', '', texto_bruto).strip()
        partes = limpo.split()
        
        if len(partes) >= 2:
            data_pt = partes[1]
            if len(data_pt) == 4 and data_pt.isdigit():
                data_pt = f"31/12/{data_pt}"
            if completa and len(partes) >= 3:
                return f"{data_pt} {partes[2]}"
            return data_pt
            
        if len(limpo) == 4 and limpo.isdigit():
            return f"31/12/{limpo}"
            
        return limpo

    @staticmethod
    def processar_dados_completos(raw_string):
        documentos = []
        if not raw_string: return []
        
        registros = raw_string.split('*')
        for registro in registros:
            if not registro or len(registro) < 20: continue
            
            campos = [c.strip() for c in registro.split('$&')]
            if len(campos) < 8: continue

            # --- FILTRO DE STATUS: APENAS "ATIVO" ---
            # Verificamos as posições 7 e 8, que são as colunas de status da CVM
            status_valido = False
            for idx in [7, 8]:
                if idx < len(campos):
                    # Comparamos o valor exato para evitar "Inativo" passar no teste
                    if campos[idx].upper() == "ATIVO":
                        status_valido = True
                        break
            
            if not status_valido:
                continue

            # Extração do ID Sequencial
            id_seq = None
            m = re.search(r"(?:Documento=|Documentos\(')(\d{5,7})", registro)
            if m: id_seq = m.group(1)

            if id_seq:
                m_v = re.search(r"Documentos\('\d+','(\d+)'", registro)
                versao = m_v.group(1) if m_v else "1"
                
                m_proto = re.search(r"OpenDownloadDocumentos\('\d+','\d+','(.*?)'", registro)
                if not m_proto:
                    m_proto = re.search(r"exibirProtocoloPDF\((\d+)", registro)
                
                protocolo = m_proto.group(1) if m_proto else ""
                cat_nome = campos[2]

                # Link inteligente
                if any(x in cat_nome.upper() for x in ["FRE", "ITR", "DFP", "FCA"]):
                    link = f"https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={id_seq}&CodigoTipoInstituicao=1"
                else:
                    link = f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoIPEExterno.aspx?NumeroProtocoloEntrega={protocolo}" if protocolo else "#"

                documentos.append({
                    "Código CVM": campos[0],
                    "Empresa": campos[1],
                    "Categoria": campos[2],
                    "Tipo": campos[3],
                    "Espécie": campos[11] if len(campos) > 11 else "-",
                    "Data Referência": DataParser.extrair_data_limpa(campos[5], False),
                    "Data Entrega": DataParser.extrair_data_limpa(campos[6], True),
                    "Status": "Ativo", 
                    "Versão": versao,
                    "Link do Documento": link,
                    "_ID_SEQ": id_seq,
                    "_PROTOCOLO": protocolo
                })
        return documentos
    
class DownloadManager:
    def __init__(self):
        self.client = CVMClient()
        self.file_mgr = FileManager()
        self.parser = DataParser()

    def escrever_log(self, pasta, mensagem):
        caminho_log = os.path.join(pasta, "execucao_detalhada.log")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(caminho_log, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {mensagem}\n")

    def iniciar_fluxo(self, modo, data_de, data_ate, cod_id, nome_cat, pc="", tp="-1", se="-1", ce="-1", callback_progresso=None):
        cat_folder = self.parser.limpar_nome(nome_cat)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        sub = "Downloads" if modo == "download" else "Bases"
        pasta = os.path.abspath(os.path.join(sub, f"{sub}_{cat_folder}_{ts}"))
        self.file_mgr.criar_diretorio(pasta)
        
        self.escrever_log(pasta, f"--- INICIANDO COLETA: {nome_cat} ---")

        payload = {
            "dataDe": data_de, "dataAte": data_ate, "empresa": "", "setorAtividade": "-1", 
            "categoriaEmissor": ce, "situacaoEmissor": se, "tipoParticipante": tp, 
            "dataReferencia": "", "categoria": cod_id, "periodo": "2", "horaIni": "", 
            "horaFim": "", "palavraChave": "," + pc if pc else "", "ultimaDtRef": "false", 
            "tipoEmpresa": "0", "token": "", "versaoCaptcha": ""
        }

        res = self.client.consultar(payload)
        dados_brutos = res.get('d', {}).get('dados', "")
        lista = self.parser.processar_dados_completos(dados_brutos)
        total = len(lista)
        
        self.escrever_log(pasta, f"Total de registros ATIVOS encontrados: {total}")

        if total == 0:
            return 0, pasta

        if modo in ["planilha", "ambos"]:
            nome_planilha = f"Base_Coleta_{cat_folder}_{ts}.xlsx"
            df = pd.DataFrame(lista).drop(columns=['_ID_SEQ', '_PROTOCOLO'], errors='ignore')
            df.to_excel(os.path.join(pasta, nome_planilha), index=False)

        if modo in ["download", "ambos"]:
            rep_ids = '1030,1000,1060,1090,1120,1150,1180,1210,1240,1270,1300,1330,1360,1390,1420,1450,1480,0,2030,2000,2060,2090,2120,2150,2180,2210,2240,2270,2300,2330,3030,3000,3060,4030,4000,4060,4090,4120,4150,4180,4210,5030,5000,5060,5090,5120,5150,6030,6000,6090,6120,6150,6180,7030,7000,7045,7060,7090,7120,7150,7180,7210,7240,8030,8000,8060,8095,8120,8155,8180,8210,8240,8270,8300,8335,8360,8390,8420,8450,8480,8510,8540,8545,8570,8575,8600,9030,9000,9045,9060,10045,10000,10030,10060,10090,10095,10120,10150,11030,11000,11060,11020,11090,12030,12000,12060,12090,12120,12150,12180,12210,12240,12270,13030,13000,13045'
            for i, d in enumerate(lista):
                if callback_progresso: callback_progresso(((i+1)/total)*100, i+1, total)
                try:
                    cat_up = d['Categoria'].upper()
                    nome_arq = f"{self.parser.limpar_nome(d['Empresa'], 80)}_{self.parser.limpar_nome(d['Categoria'], 40)}_ID{d['_ID_SEQ']}_v{d['V']}.pdf"
                    
                    if any(x in cat_up for x in ["FRE", "ITR", "DFP", "FCA"]):
                        h = self.client.capturar_hash_dinamico(d['_ID_SEQ'])
                        t_doc = "FREWEB" if "FRE" in cat_up else "ITRWEB" if "ITR" in cat_up else "DFPWEB"
                        conteudo = self.client.baixar_via_relatorio({
                            "reportIds": rep_ids, "nrSequencialDocumento": d['_ID_SEQ'], 
                            "codigoCVM": d["Código CVM"], "tipoDocumento": t_doc, "Hash": h, "token": "", "versaoCaptcha": ""
                        })
                    else:
                        conteudo = self.client.baixar_arquivo_estatico({
                            "Tela": "ext", "numSequencia": d['_ID_SEQ'], "numVersao": d["V"], 
                            "numProtocolo": d["_PROTOCOLO"], "descTipo": "RE", "CodigoInstituicao": "1"
                        })
                    if conteudo: self.file_mgr.salvar_arquivo(conteudo, nome_arq, pasta)
                except Exception as ex:
                    self.escrever_log(pasta, f"Erro no item {d['_ID_SEQ']}: {str(ex)}")

        return total, pasta