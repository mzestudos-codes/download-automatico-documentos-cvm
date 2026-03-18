import re, os, time, unicodedata
import pandas as pd
from datetime import datetime
from infra import CVMClient, FileManager

class DataParser:
    @staticmethod
    def limpar_nome(texto, limite=None):
        if not texto: return "ARQUIVO"
        nfkd_form = unicodedata.normalize('NFKD', texto)
        s = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        s = re.sub(r'[^a-zA-Z0-9_]', '_', s.replace(" ", "_"))
        s = re.sub(r'_+', '_', s).strip('_')
        return s[:limite].upper() if limite else s.upper()

    @staticmethod
    def extrair_data_limpa(texto_bruto, completa=False):
        if not texto_bruto: return "-"
        limpo = re.sub(r'<.*?>', '', texto_bruto).strip()
        partes = limpo.split()
        if len(partes) >= 2:
            dt = partes[1]
            if len(dt) == 4 and dt.isdigit(): dt = f"31/12/{dt}"
            if completa and len(partes) >= 3: return f"{dt} {partes[2]}"
            return dt
        return f"31/12/{limpo}" if (len(limpo)==4 and limpo.isdigit()) else limpo

    @staticmethod
    def processar_dados_completos(raw_string):
        documentos = []
        if not raw_string: return []
        
        # O portal CVM separa registros por '*'
        registros = raw_string.split('*')
        for registro in registros:
            if not registro or len(registro) < 20: continue
            
            # O separador de campos é '$&'
            campos = [c.strip() for c in registro.split('$&')]
            
            # Validação mínima de colunas
            if len(campos) < 6: continue

            # Filtro de Ativo rigoroso
            status = campos[7].upper().strip() if len(campos) > 7 else ""
            if status != "ATIVO": 
                continue

            # --- CORREÇÃO: CAPTURA E LIMPEZA DA ESPÉCIE ---
            # A CVM manda no índice 4: <spanOrder>ASSUNTO</spanOrder>ESPÉCIE
            especie_bruta = campos[4] if len(campos) > 4 else ""
            
            # Vamos separar o que é assunto do que é espécie
            if "</spanOrder>" in especie_bruta:
                # Pega só o texto que vem DEPOIS do fechamento da tag (a Espécie real)
                especie_limpa = especie_bruta.split("</spanOrder>")[-1]
            else:
                especie_limpa = especie_bruta
                
            # Limpa qualquer sujeira HTML que possa sobrar e remove espaços
            especie_limpa = re.sub(r'<.*?>', '', especie_limpa).strip()
            
            # Se sobrar apenas um traço ou nada, convertemos para N/A
            if especie_limpa in ["-", ""]: 
                especie_limpa = "N/A"

            # --- CAPTURA DE NOVOS CAMPOS PARA A PLANILHA ---
            modalidade = campos[9].strip() if len(campos) > 9 else "-"
            
            # Assunto vem limpinho no índice 11
            assunto = campos[11].strip() if len(campos) > 11 else "-"
            if not assunto: 
                assunto = "-"

            # --- EXTRAÇÃO DE DADOS PARA DOWNLOAD ---
            id_seq = None
            m_id = re.search(r"(?:Documento=|Documentos\(')(\d{5,8})", registro)
            if m_id: id_seq = m_id.group(1)
            else: continue

            m_v = re.search(r"Documentos\('\d+','(\d+)'", registro)
            versao = m_v.group(1) if m_v else "1"
            
            m_p = re.search(r"OpenDownloadDocumentos\('\d+','\d+','(\d+)'", registro)
            if not m_p: m_p = re.search(r"ProtocoloEntrega=(\d+)", registro)
            protocolo = m_p.group(1) if m_p else ""

            m_tipo = re.search(r"OpenDownloadDocumentos\('\d+','\d+','\d+','(.*?)'\)", registro)
            desc_tipo = m_tipo.group(1) if m_tipo else "RE"

            documentos.append({
                "Código CVM": campos[0],
                "Empresa": campos[1],
                "Categoria": campos[2],
                "Tipo": campos[3],
                "Espécie": especie_limpa, 
                "Data Referência": DataParser.extrair_data_limpa(campos[5], False) if len(campos) > 5 else "-",
                "Data Entrega": DataParser.extrair_data_limpa(campos[6], True) if len(campos) > 6 else "-",
                "Status": status.capitalize(), 
                "V": versao,
                "Modalidade": modalidade,
                "Assunto": assunto,
                "Link do Documento": LinkInteligente(id_seq, protocolo, campos[2]),
                "_ID_SEQ": id_seq,
                "_PROTOCOLO": protocolo,
                "_DESC_TIPO": desc_tipo
            })
        return documentos

# Função auxiliar
def LinkInteligente(id_seq, protocolo, cat_nome):
    if any(x in cat_nome.upper() for x in ["FRE", "ITR", "DFP", "FCA"]):
        return f"https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={id_seq}&CodigoTipoInstituicao=1"
    return f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoIPEExterno.aspx?NumeroProtocoloEntrega={protocolo}" if protocolo else "#"
    
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
        prefixo = "Downloads" if modo == "download" else "Base" if modo == "planilha" else "Coleta_Completa"
        pasta = os.path.abspath(os.path.join(prefixo, f"{prefixo}_{cat_folder}_{ts}"))
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
        
        self.escrever_log(pasta, f"Registros ATIVOS identificados: {total}")

        if total == 0: return 0, pasta

        if modo in ["planilha", "ambos"]:
            df = pd.DataFrame(lista).drop(columns=['_ID_SEQ', '_PROTOCOLO', '_DESC_TIPO'], errors='ignore')
            df.to_excel(os.path.join(pasta, f"Base_Coleta_{cat_folder}_{ts}.xlsx"), index=False)

        if modo in ["download", "ambos"]:
            rep_ids = '1030,1000,1060,1090,1120,1150,1180,1210,1240,1270,1300,1330,1360,1390,1420,1450,1480,0,2030,2000,2060,2090,2120,2150,2180,2210,2240,2270,2300,2330,3030,3000,3060,4030,4000,4060,4090,4120,4150,4180,4210,5030,5000,5060,5090,5120,5150,6030,6000,6090,6120,6150,6180,7030,7000,7045,7060,7090,7120,7150,7180,7210,7240,8030,8000,8060,8095,8120,8155,8180,8210,8240,8270,8300,8335,8360,8390,8420,8450,8480,8510,8540,8545,8570,8575,8600,9030,9000,9045,9060,10045,10000,10030,10060,10090,10095,10120,10150,11030,11000,11060,11020,11090,12030,12000,12060,12090,12120,12150,12180,12210,12240,12270,13030,13000,13045'
            for i, d in enumerate(lista):
                if callback_progresso: callback_progresso(((i+1)/total)*100, i+1, total)
                try:
                    cat_up = d['Categoria'].upper()
                    nome_arq = f"{self.parser.limpar_nome(d['Empresa'], 80)}_{self.parser.limpar_nome(d['Categoria'], 40)}_ID{d['_ID_SEQ']}_v{d['V']}.pdf"
                    
                    if any(x in cat_up for x in ["FRE", "ITR", "DFP", "FCA"]):
                        # 1. Captura Hash
                        h = self.client.capturar_hash_dinamico(d['_ID_SEQ'])
                        
                        if h:
                            # 2. Delay para o servidor processar
                            time.sleep(2) 
                            
                            t_doc = "FREWEB" if "FRE" in cat_up else "ITRWEB" if "ITR" in cat_up else "DFPWEB"
                            conteudo = self.client.baixar_via_relatorio({
                                "reportIds": rep_ids, 
                                "nrSequencialDocumento": d['_ID_SEQ'], 
                                "codigoCVM": d["Código CVM"], 
                                "tipoDocumento": t_doc, 
                                "Hash": h, 
                                "token": "", "versaoCaptcha": ""
                            })
                        else:
                            conteudo = b""
                    else:
                        # Download PDF Normal
                        conteudo = self.client.baixar_arquivo_estatico({
                            "Tela": "ext", "numSequencia": d['_ID_SEQ'], "numVersao": d["V"], 
                            "numProtocolo": d["_PROTOCOLO"], "descTipo": d["_DESC_TIPO"], 
                            "CodigoInstituicao": "1"
                        })
                        time.sleep(0.5)
                    
                    if conteudo and len(conteudo) > 1000: 
                        self.file_mgr.salvar_arquivo(conteudo, nome_arq, pasta)
                        self.escrever_log(pasta, f"OK: {nome_arq}")
                    else:
                        self.escrever_log(pasta, f"FALHA: {nome_arq} (Servidor recusou ou Hash inválido)")                

                except Exception as ex:
                    self.escrever_log(pasta, f"ERRO no item {d['_ID_SEQ']}: {str(ex)}")

        return total, pasta