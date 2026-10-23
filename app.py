import streamlit as st
import json, os, io, zipfile, re
from datetime import datetime
import pandas as pd
from business import DownloadManager, DataParser

# --- Configuração da Página ---
st.set_page_config(
    page_title="CVM Downloader Web",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Customizado para Visual Moderno e Elegante ---
st.markdown("""
<style>
    .main-title {
        color: #2D5A27;
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 0px;
    }
    .sub-title {
        color: #4A524A;
        font-size: 1.05rem;
        margin-top: 2px;
        margin-bottom: 25px;
    }
    .metric-card {
        background-color: #F9FBF9;
        border: 1px solid #D1D5D1;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .stButton>button {
        border-radius: 10px;
        font-weight: 700;
    }
    div[data-testid="stStatusWidget"] {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- Dicionários de Domínio CVM ---
DICT_TIPO_PART = {
    "TODOS": "-1", 
    "BDR Não Patrocinados": "7", 
    "Companhia Aberta": "1", 
    "Companhia Dispensada de Registro": "6", 
    "Companhia Estrangeira": "2", 
    "Companhia Incentivada Registrada": "8"
}

DICT_SIT_EMISSOR = {
    "TODOS": "-1", 
    "Em Falência": "4", 
    "Em Liquidação Extrajudicial": "5", 
    "Em liquidação judicial": "7", 
    "Em Recuperação Extrajudicial": "9", 
    "Em Recuperação Judicial ou Equivalente": "8", 
    "Fase Operacional": "2", 
    "Fase Pré-Operacional": "1", 
    "Paralisada": "6"
}

DICT_CAT_EMISSOR = {
    "TODOS": "-1", 
    "Categoria A": "1", 
    "Categoria B": "2", 
    "Não Identificado": "99"
}

DICT_SETOR_ATIVIDADE = {
    "TODOS": "-1", "Agricultura (Açúcar, Álcool e Cana)": "1210", "Alimentos": "1220", 
    "Arrendamento Mercantil": "1260", "Bancos": "1240", "Bebidas e Fumo": "1090", 
    "Bolsas de Valores/Mercadorias e Futuros": "1410", "Brinquedos e Lazer": "1400", 
    "Comércio (Atacado e Varejo)": "1190", "Comércio Exterior": "1200", 
    "Comunicação e Informática": "1150", "Construção Civil, Mat. Constr. e Decoração": "1110", 
    "Cooperativas": "1230", "Crédito Imobiliário": "1300", "Educação": "1380", 
    "Embalagens": "1330", "Emp. Adm. Part. - Agricultura (Açúcar, Álcool e Cana)": "3210", 
    "Emp. Adm. Part. - Alimentos": "3220", "Emp. Adm. Part. - Arrendamento Mercantil": "3260", 
    "Emp. Adm. Part. - Bancos": "3240", "Emp. Adm. Part. - Bebidas e Fumo": "3090", 
    "Emp. Adm. Part. - Brinquedos e Lazer": "3400", "Emp. Adm. Part. - Comércio (Atacado e Varejo)": "3190", 
    "Emp. Adm. Part. - Comércio Exterior": "3200", "Emp. Adm. Part. - Comunicação e Informática": "3150", 
    "Emp. Adm. Part. - Const. Civil, Mat. Const. e Decoração": "3110", "Emp. Adm. Part. - Cooperativas": "3230", 
    "Emp. Adm. Part. - Crédito Imobiliário": "3300", "Emp. Adm. Part. - Educação": "3380", 
    "Emp. Adm. Part. - Embalagens": "3330", "Emp. Adm. Part. - Energia Elétrica": "3120", 
    "Emp. Adm. Part. - Extração Mineral": "3030", "Emp. Adm. Part. - Factoring": "3290", 
    "Emp. Adm. Part. - Farmacêutico e Higiene": "3080", "Emp. Adm. Part. - Gráficas e Editoras": "3100", 
    "Emp. Adm. Part. - Hospedagem e Turismo": "3180", "Emp. Adm. Part. - Intermediação Financeira": "3280", 
    "Emp. Adm. Part. - Máqs., Equip., Veíc. e Peças": "3070", "Emp. Adm. Part. - Metalurgia e Siderurgia": "3060", 
    "Emp. Adm. Part. - Papel e Celulose": "3040", "Emp. Adm. Part. - Pesca": "3320", 
    "Emp. Adm. Part. - Petróleo e Gás": "3010", "Emp. Adm. Part. - Petroquímicos e Borracha": "3020", 
    "Emp. Adm. Part. - Previdência Privada": "3270", "Emp. Adm. Part. - Reflorestamento": "3310", 
    "Emp. Adm. Part. - Saneamento, Serv. Água e Gás": "3160", "Emp. Adm. Part. - Securitização de Recebíveis": "3390", 
    "Emp. Adm. Part. - Seguradoras e Corretoras": "3250", "Emp. Adm. Part. - Sem Setor Principal": "3990", 
    "Emp. Adm. Part. - Serviços médicos": "3170", "Emp. Adm. Part. - Serviços Transporte e Logística": "3140", 
    "Emp. Adm. Part. - Telecomunicações": "3130", "Emp. Adm. Part. - Têxtil e Vestuário": "3050", 
    "Emp. Adm. Part.-Bolsas de Valores/Mercadorias e Futuros": "3410", "Energia Elétrica": "1120", 
    "Extração Mineral": "1030", "Factoring": "1290", "Farmacêutico e Higiene": "1080", 
    "Gráficas e Editoras": "1100", "Hospedagem e Turismo": "1180", "Intermediação Financeira": "1280", 
    "Máquinas, Equipamentos, Veículos e Peças": "1070", "Metalurgia e Siderurgia": "1060", 
    "Papel e Celulose": "1040", "Pesca": "1320", "Petróleo e Gás": "1010", "Petroquímicos e Borracha": "1020", 
    "Previdência Privada": "1270", "Reflorestamento": "1310", "Saneamento, Serv. Água e Gás": "1160", 
    "Securitização de Recebíveis": "1390", "Seguradoras e Corretoras": "1250", "Serviços médicos": "1170", 
    "Serviços Transporte e Logística": "1140", "Telecomunicações": "1130", "Têxtil e Vestuário": "1050"
}

# --- Carregamento de Categorias com Cache ---
@st.cache_data
def carregar_categorias():
    caminho = "categorias.json"
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    filtrados = []
    for d in dados:
        cat = d.get("categoria", "")
        if d.get("id", "").startswith(("IPE", "EST")) and not cat.startswith(("Tipo:", "Espécie:")):
            filtrados.append(d)
    return filtrados

DADOS_CATEGORIAS = carregar_categorias()
LISTA_CATEGORIAS = sorted(list(set(d["categoria"] for d in DADOS_CATEGORIAS)))

# --- Inicialização do Session State ---
if "fila_categorias" not in st.session_state:
    st.session_state.fila_categorias = []
if "custom_nome_ativo" not in st.session_state:
    st.session_state.custom_nome_ativo = False
if "nome_personalizado_valor" not in st.session_state:
    st.session_state.nome_personalizado_valor = ""
if "ultimo_resultado" not in st.session_state:
    st.session_state.ultimo_resultado = None

# --- Cabeçalho ---
st.markdown('<div class="main-title">🏛️ CVM Downloader Web</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Automação de extração, estruturação em planilha e download de documentos da CVM</div>', unsafe_allow_html=True)

# --- 1. Configuração de Execução ---
with st.container():
    st.subheader("1. Configuração de Execução")
    col_modo, col_custom = st.columns([1.5, 2.5])
    
    with col_modo:
        opcao_modo = st.radio(
            "Modo de Operação", 
            ["Download PDFs", "Gerar Planilha (.xlsx)", "Ambos (PDFs + Planilha)"],
            index=1,
            help="Escolha se deseja apenas baixar os arquivos, apenas gerar a planilha com os links ou ambos."
        )
        modo_codigo = "download" if "Download PDFs" in opcao_modo else "planilha" if "Gerar Planilha" in opcao_modo else "ambos"

    with col_custom:
        if modo_codigo in ["planilha", "ambos"]:
            st.session_state.custom_nome_ativo = st.checkbox("Nome personalizado para a planilha / pasta", value=st.session_state.custom_nome_ativo)
            
            # Cálculo da prévia dinâmica
            if st.session_state.fila_categorias:
                cat_tag = "MULTIPLAS"
            else:
                cat_tag = "DOCUMENTOS"
            
            nome_sugerido = f"Base_Coleta_{cat_tag}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            if not st.session_state.custom_nome_ativo:
                st.session_state.nome_personalizado_valor = nome_sugerido
                st.text_input("Nome do arquivo / pasta:", value=nome_sugerido, disabled=True, help="Desmarque a checkbox para manter a prévia automática baseada nas categorias.")
            else:
                st.session_state.nome_personalizado_valor = st.text_input(
                    "Nome personalizado do arquivo / pasta:", 
                    value=st.session_state.nome_personalizado_valor or nome_sugerido,
                    help="Defina o nome exato. A pasta e a planilha gerada terão este nome."
                )
        else:
            st.info("💡 No modo 'Download PDFs', a planilha não é gerada.")

st.divider()

# --- 2. Datas e Palavras-Chave ---
st.subheader("2. Datas e Palavras-Chave")
col_d1, col_d2, col_pc = st.columns([1, 1, 2])

with col_d1:
    dt_inicio = st.date_input("Data Início", value=datetime(2025, 12, 1), format="DD/MM/YYYY")
with col_d2:
    dt_fim = st.date_input("Data Fim", value=datetime(2025, 12, 18), format="DD/MM/YYYY")
with col_pc:
    palavra_chave = st.text_input("Filtrar por Palavra-Chave (opcional)", placeholder="Ex: dividendo, fato relevante, grupamento...")

st.divider()

# --- 3. Perfil do Emissor & Setor de Atividade ---
st.subheader("3. Perfil do Emissor & Setor de Atividade")
col_p1, col_p2, col_p3, col_p4 = st.columns(4)

with col_p1:
    tp_selecionado = st.selectbox("Tipo de Participante", list(DICT_TIPO_PART.keys()), index=0)
with col_p2:
    se_selecionado = st.selectbox("Situação do Emissor", list(DICT_SIT_EMISSOR.keys()), index=0)
with col_p3:
    ce_selecionado = st.selectbox("Categoria de Registro", list(DICT_CAT_EMISSOR.keys()), index=0)
with col_p4:
    sa_selecionado = st.selectbox("Setor de Atividade", list(DICT_SETOR_ATIVIDADE.keys()), index=0)

st.divider()

# --- 4. Classificação do Documento & Fila de Extração ---
st.subheader("4. Classificação do Documento")

col_cat, col_tipo, col_esp = st.columns(3)

with col_cat:
    cat_sel = st.selectbox("Categoria", LISTA_CATEGORIAS, index=0 if LISTA_CATEGORIAS else None)

# Tipos filtrados por Categoria
tipos_disp = sorted(list(set(d["tipo"] for d in DADOS_CATEGORIAS if d["categoria"] == cat_sel)))
if "TODOS" not in tipos_disp: tipos_disp.insert(0, "TODOS")

with col_tipo:
    tipo_sel = st.selectbox("Tipo", tipos_disp, index=0)

# Espécies filtradas por Categoria e Tipo
if tipo_sel == "TODOS":
    esps_disp = ["TODOS"]
else:
    esps_disp = sorted(list(set(d["especie"] for d in DADOS_CATEGORIAS if d["categoria"] == cat_sel and d["tipo"] == tipo_sel)))
if "TODOS" not in esps_disp: esps_disp.insert(0, "TODOS")

with col_esp:
    esp_sel = st.selectbox("Espécie", esps_disp, index=0)

# Botões de Fila
col_btn_add, col_btn_clear, col_vazio = st.columns([1.2, 1, 3])
with col_btn_add:
    if st.button("➕ Adicionar à Fila", use_container_width=True):
        match = [d for d in DADOS_CATEGORIAS if d['categoria'] == cat_sel and d['tipo'] == tipo_sel and d['especie'] == esp_sel]
        if match and match[0] not in st.session_state.fila_categorias:
            st.session_state.fila_categorias.append(match[0])
            st.success(f"Adicionado: {cat_sel} | {tipo_sel}")
with col_btn_clear:
    if st.button("🗑️ Limpar Fila", use_container_width=True):
        st.session_state.fila_categorias = []
        st.info("Fila de classificações esvaziada.")

# Exibição da Fila Atual
if st.session_state.fila_categorias:
    st.markdown("**📋 Fila de Extração Ativa:**")
    df_fila = pd.DataFrame([{
        "ID CVM": c['id'],
        "Categoria": c['categoria'],
        "Tipo": c['tipo'],
        "Espécie": c['especie']
    } for c in st.session_state.fila_categorias])
    st.dataframe(df_fila, use_container_width=True, hide_index=True)
else:
    st.caption("ℹ️ *A fila está vazia. O downloader usará a classificação selecionada acima.*")

st.divider()

# --- 5. Disparo do Processo e Feedback ao Vivo ---
st.subheader("5. Execução")

col_exec, col_espaco = st.columns([1.5, 2.5])
with col_exec:
    botao_iniciar = st.button("🚀 INICIAR PROCESSAMENTO", type="primary", use_container_width=True)

if botao_iniciar:
    if dt_inicio > dt_fim:
        st.error("❌ A Data Início não pode ser maior do que a Data Fim.")
    else:
        # Prepara IDs e rótulos
        if st.session_state.fila_categorias:
            ids = ",".join([c['id'] for c in st.session_state.fila_categorias])
            nome_cat_final = "Múltiplas"
            selected_cat_label = " | ".join([f"{c['categoria']} / {c['tipo']} / {c['especie']}" for c in st.session_state.fila_categorias])
        else:
            match = [d for d in DADOS_CATEGORIAS if d['categoria'] == cat_sel and d['tipo'] == tipo_sel and d['especie'] == esp_sel]
            if not match:
                st.error("Selecione uma categoria válida.")
                st.stop()
            ids = match[0]['id']
            nome_cat_final = cat_sel
            selected_cat_label = f"{cat_sel} / {tipo_sel} / {esp_sel}"

        # Elementos de Progresso e Log ao vivo
        prog_bar = st.progress(0)
        status_txt = st.empty()
        log_expander = st.expander("📜 Terminal de Logs em Tempo Real", expanded=True)
        log_box = log_expander.empty()
        logs_coletados = []

        def callback_progresso(pct, atual, total):
            prog_bar.progress(int(pct) / 100)
            status_txt.markdown(f"**Baixando itens:** `{atual}` de `{total}` ({int(pct)}%)")

        def callback_log(linha):
            logs_coletados.append(linha)
            # Exibe as últimas 15 linhas no container
            log_box.code("\n".join(logs_coletados[-18:]), language="log")

        manager = DownloadManager()

        status_txt.info("🔄 Conectando à CVM e consultando registros...")

        try:
            total, pasta = manager.iniciar_fluxo(
                modo=modo_codigo,
                data_de=dt_inicio.strftime("%d/%m/%Y"),
                data_ate=dt_fim.strftime("%d/%m/%Y"),
                cod_id=ids,
                nome_cat=nome_cat_final,
                pc=palavra_chave.strip(),
                tp=DICT_TIPO_PART.get(tp_selecionado, "-1"),
                se=DICT_SIT_EMISSOR.get(se_selecionado, "-1"),
                ce=DICT_CAT_EMISSOR.get(ce_selecionado, "-1"),
                sa=DICT_SETOR_ATIVIDADE.get(sa_selecionado, "-1"),
                tp_label=tp_selecionado,
                se_label=se_selecionado,
                ce_label=ce_selecionado,
                sa_label=sa_selecionado,
                tipo_doc=tipo_sel,
                esp_doc=esp_sel,
                categoria_doc=cat_sel,
                selected_categories_label=selected_cat_label,
                pasta_destino="",
                nome_planilha=st.session_state.nome_personalizado_valor if st.session_state.custom_nome_ativo else "",
                is_custom_nome=st.session_state.custom_nome_ativo,
                callback_progresso=callback_progresso,
                callback_log=callback_log
            )

            prog_bar.progress(1.0)
            status_txt.empty()

            st.session_state.ultimo_resultado = {
                "total": total,
                "pasta": pasta,
                "modo": modo_codigo,
                "ts": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }

            if total == 0:
                st.warning("⚠️ Nenhum documento ATIVO foi encontrado para os filtros selecionados.")
            else:
                st.success(f"🎉 **Extração Finalizada com Sucesso!** Total de documentos: `{total}`")

        except Exception as e:
            st.error(f"Erro durante a execução: {str(e)}")

# --- 6. Área de Download dos Arquivos Gerados ---
if st.session_state.ultimo_resultado and st.session_state.ultimo_resultado.get("total", 0) > 0:
    res = st.session_state.ultimo_resultado
    pasta_gerada = res["pasta"]
    
    st.subheader("📥 Baixar Arquivos Extraídos")
    st.caption(f"Execução finalizada em `{res['ts']}` | Pasta: `{os.path.basename(pasta_gerada)}`")
    
    col_d_excel, col_d_zip, col_d_log = st.columns(3)
    
    # 1. Download do Excel
    with col_d_excel:
        arquivos_xlsx = [f for f in os.listdir(pasta_gerada) if f.lower().endswith(".xlsx")]
        if arquivos_xlsx:
            nome_excel = arquivos_xlsx[0]
            caminho_excel = os.path.join(pasta_gerada, nome_excel)
            with open(caminho_excel, "rb") as f_excel:
                st.download_button(
                    label=f"📊 Baixar Planilha ({nome_excel})",
                    data=f_excel.read(),
                    file_name=nome_excel,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.caption("Planilha não aplicável para este modo.")

    # 2. Download do Pacote ZIP (PDFs)
    with col_d_zip:
        arquivos_pdf = [f for f in os.listdir(pasta_gerada) if f.lower().endswith(".pdf")]
        if arquivos_pdf:
            # Compacta em memória
            buffer_zip = io.BytesIO()
            with zipfile.ZipFile(buffer_zip, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for pdf in arquivos_pdf:
                    caminho_pdf = os.path.join(pasta_gerada, pdf)
                    zip_file.write(caminho_pdf, arcname=pdf)
            buffer_zip.seek(0)
            
            nome_zip = f"{os.path.basename(pasta_gerada)}.zip"
            st.download_button(
                label=f"📦 Baixar PDFs em ZIP ({len(arquivos_pdf)} arquivos)",
                data=buffer_zip,
                file_name=nome_zip,
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.caption("PDFs não aplicáveis para este modo.")

    # 3. Download do Log
    with col_d_log:
        caminho_log = os.path.join(pasta_gerada, "execucao_detalhada.log")
        if os.path.exists(caminho_log):
            with open(caminho_log, "rb") as f_log:
                st.download_button(
                    label="📄 Baixar Log Detalhado (.log)",
                    data=f_log.read(),
                    file_name="execucao_detalhada.log",
                    mime="text/plain",
                    use_container_width=True
                )
