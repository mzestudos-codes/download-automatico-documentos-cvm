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
    def extrair_data_limpa(texto_bruto):
        if not texto_bruto: return "-"
        limpo = re.sub(r'<.*?>', '', texto_bruto).strip()
        partes = limpo.split(' ')
        return " ".join(partes[1:]) if len(partes) > 1 else limpo

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
                    documentos.append({
                        "Código CVM": campos[0].strip(), "Empresa": campos[1].strip(), "Categoria": campos[2].strip(),
                        "Tipo": campos[3].strip(), "Espécie": campos[11].strip() if len(campos) > 11 else "-",
                        "Data Referência": DataParser.extrair_data_limpa(campos[5]),
                        "Data Entrega": DataParser.extrair_data_limpa(campos[6]),
                        "Status": status, "V": versao, "Modalidade": modalidade,
                        "LINK": f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoIPEExterno.aspx?NumeroProtocoloEntrega={protocolo}",
                        "_ID_SEQ": seq, "_PROTOCOLO": protocolo
                    })
        return documentos

class DownloadManager:
    def __init__(self):
        self.client = CVMClient(); self.file_mgr = FileManager(); self.parser = DataParser()

    def escrever_log(self, pasta, mensagem):
        caminho_log = os.path.join(pasta, "execucao_detalhada.log")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(caminho_log, "a", encoding="utf-8") as f: f.write(f"[{ts}] {mensagem}\n")

    def iniciar_fluxo(self, modo, data_de, data_ate, cod_id, nome_categoria, pc="", tp="-1", se="-1", ce="-1", callback_progresso=None):
        cat_limpa = self.parser.limpar_nome(nome_categoria)
        prefixo = "Downloads" if modo == "download" else "Base" if modo == "planilha" else "Coleta_Completa"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        pasta = os.path.abspath(os.path.join(prefixo, f"{prefixo}_{cat_limpa}_{ts}"))
        self.file_mgr.criar_diretorio(pasta)
        
        self.escrever_log(pasta, "--- INÍCIO DA SESSÃO ---")
        self.escrever_log(pasta, f"MODO: {modo} | CATEGORIAS: {cod_id}")
        self.escrever_log(pasta, f"FILTROS: Data: {data_de} a {data_ate} | Palavra-Chave: '{pc}' | Perfil Emissor (tp/se/ce): {tp}/{se}/{ce}")

        payload = {
            "dataDe": data_de, "dataAte": data_ate, "empresa": "", "setorAtividade": "-1", 
            "categoriaEmissor": ce, "situacaoEmissor": se, "tipoParticipante": tp, 
            "dataReferencia": "", "categoria": cod_id, "periodo": "2", "horaIni": "", 
            "horaFim": "", "palavraChave": "," + pc if pc else "", "ultimaDtRef": "false", 
            "tipoEmpresa": "0", "token": "", "versaoCaptcha": ""
        }

        res = self.client.consultar(payload)
        lista = self.parser.processar_dados_completos(res.get('d', {}).get('dados', ""))
        total = len(lista)
        
        self.escrever_log(pasta, f"RESULTADO CONSULTA: {total} documentos ativos encontrados.")

        if total == 0:
            self.escrever_log(pasta, "ENCERRADO: Nenhum documento para processar.")
            return 0, pasta

        if modo in ["planilha", "ambos"]:
            file_excel = os.path.join(pasta, f"Relatorio_Dados_{ts}.xlsx")
            pd.DataFrame(lista).drop(columns=['_ID_SEQ', '_PROTOCOLO']).to_excel(file_excel, index=False)
            self.escrever_log(pasta, f"PLANILHA GERADA: {os.path.basename(file_excel)}")

        if modo in ["download", "ambos"]:
            rep_ids = '1030,1000,1060,1090,1120,1150,1180,1210,1240,1270,1300,1330,1360,1390,1420,1450,1480,0,2030,2000,2060,2090,2120,2150,2180,2210,2240,2270,2300,2330,3030,3000,3060,4030,4000,4060,4090,4120,4150,4180,4210,5030,5000,5060,5090,5120,5150,6030,6000,6090,6120,6150,6180,7030,7000,7045,7060,7090,7120,7150,7180,7210,7240,8030,8000,8060,8095,8120,8155,8180,8210,8240,8270,8300,8335,8360,8390,8420,8450,8480,8510,8540,8545,8570,8575,8600,9030,9000,9045,9060,10045,10000,10030,10060,10090,10095,10120,10150,11030,11000,11060,11020,11090,12030,12000,12060,12090,12120,12150,12180,12210,12240,12270,13030,13000,13045'
            sucesso, erro = 0, 0
            for i, d in enumerate(lista):
                if callback_progresso: callback_progresso(((i+1)/total)*100, i+1, total)
                
                try:
                    nome_arq = f"{self.parser.limpar_nome(d['Empresa'], 50)}_{self.parser.limpar_nome(d['Categoria'], 25)}_ID{d['_ID_SEQ']}.pdf"
                    if any(x in d['Categoria'].upper() for x in ["FRE", "ITR", "DFP", "FCA"]):
                        h = self.client.capturar_hash_dinamico(d['_ID_SEQ'])
                        t_doc = "FREWEB" if "FRE" in d['Categoria'].upper() else "ITRWEB" if "ITR" in d['Categoria'].upper() else "DFPWEB"
                        payload_pdf = {"reportIds": rep_ids, "nrSequencialDocumento": d['_ID_SEQ'], "codigoCVM": d["Código CVM"], "tipoDocumento": t_doc, "Hash": h, "token": "", "versaoCaptcha": ""}
                        conteudo = self.client.baixar_via_relatorio(payload_pdf)
                        time.sleep(0.3)
                    else:
                        conteudo = self.client.baixar_arquivo_estatico({"Tela": "ext", "numSequencia": d['_ID_SEQ'], "numVersao": d["V"], "numProtocolo": d["_PROTOCOLO"], "descTipo": d["Modalidade"], "CodigoInstituicao": "1"})
                    
                    if conteudo:
                        self.file_mgr.salvar_arquivo(conteudo, nome_arq, pasta)
                        self.escrever_log(pasta, f"OK: {nome_arq}")
                        sucesso += 1
                    else:
                        raise Exception("Conteúdo vazio retornado do servidor")
                except Exception as ex:
                    self.escrever_log(pasta, f"ERRO ao baixar ID {d['_ID_SEQ']}: {str(ex)}")
                    erro += 1
            
            self.escrever_log(pasta, f"RESUMO DOWNLOAD: Sucessos: {sucesso} | Falhas: {erro}")
        
        self.escrever_log(pasta, "--- FIM DA SESSÃO ---")
        return total, pasta