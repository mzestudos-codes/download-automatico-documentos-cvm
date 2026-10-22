import customtkinter as ctk
from tkinter import messagebox, filedialog
import json, os, threading, platform, re, sys
from datetime import datetime
from business import DownloadManager, DataParser

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Visual
COLOR_BG, COLOR_CARD, COLOR_PRIMARY = "#F0F2F0", "#FFFFFF", "#2D5A27"
COLOR_ACCENT, COLOR_BORDER, COLOR_ERROR = "#1E3F1A", "#D1D5D1", "#B00020"
COLOR_TEXT_LABEL, COLOR_INPUT_BG = "#4A524A", "#F9FBF9"

class AppUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.manager = DownloadManager()
        self.dados_completos = []
        self.categorias_selecionadas = []
        self.custom_nome_var = ctk.BooleanVar(value=False)
        
        self.dict_tipo_part = {"TODOS": "-1", "BDR Não Patrocinados": "7", "Companhia Aberta": "1", "Companhia Dispensada de Registro": "6", "Companhia Estrangeira": "2", "Companhia Incentivada Registrada": "8"}
        self.dict_sit_emissor = {"TODOS": "-1", "Em Falência": "4", "Em Liquidação Extrajudicial": "5", "Em liquidação judicial": "7", "Em Recuperação Extrajudicial": "9", "Em Recuperação Judicial ou Equivalente": "8", "Fase Operacional": "2", "Fase Pré-Operacional": "1", "Paralisada": "6"}
        self.dict_cat_emissor = {"TODOS": "-1", "Categoria A": "1", "Categoria B": "2", "Não Identificado": "99"}
        
        # --- NOVO: Dicionário do Setor de Atividade ---
        self.dict_setor_atividade = {
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

        self.title("CVM Downloader")
        self.after(0, lambda: self.state('zoomed')) 
        self.configure(fg_color=COLOR_BG)
        self.setup_ui()
        self.after(100, self.carregar_dados)

    def setup_ui(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=COLOR_BG)
        self.scroll_frame.pack(fill="both", expand=True)
        self.container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", width=900)
        self.container.pack(pady=40)

        # Cabeçalho
        ctk.CTkLabel(self.container, text="CVM Downloader", font=("Segoe UI", 36, "bold"), text_color=COLOR_PRIMARY).pack(anchor="w")
        ctk.CTkFrame(self.container, height=2, fg_color=COLOR_PRIMARY).pack(fill="x", pady=(10, 30))

        # Modo
        self.radio_var = ctk.StringVar(value="download")
        m_card = self.create_card("CONFIGURAÇÃO DE EXECUÇÃO")
        
        # Radio buttons de Modo
        r_frame = ctk.CTkFrame(m_card, fg_color="transparent")
        r_frame.pack(pady=(15, 10), padx=25, fill="x")
        for t, v in [("Download PDFs", "download"), ("Gerar Planilha", "planilha"), ("Ambos", "ambos")]:
            ctk.CTkRadioButton(r_frame, text=t, variable=self.radio_var, value=v, font=("Segoe UI", 13, "bold"), command=self.on_modo_change).pack(side="left", expand=True)

        # Campo: Nome da Planilha
        f_nome_planilha = ctk.CTkFrame(m_card, fg_color="transparent")
        f_nome_planilha.pack(fill="x", padx=25, pady=(5, 10))
        
        f_nome_header = ctk.CTkFrame(f_nome_planilha, fg_color="transparent")
        f_nome_header.pack(fill="x", pady=(0, 4))
        
        ctk.CTkLabel(f_nome_header, text="NOME DO ARQUIVO DA PLANILHA (.XLSX)", font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT_LABEL).pack(side="left")
        self.chk_custom_nome = ctk.CTkCheckBox(
            f_nome_header, 
            text="Nome personalizado", 
            variable=self.custom_nome_var, 
            font=("Segoe UI", 11), 
            command=self.on_toggle_custom_nome,
            checkbox_height=18,
            checkbox_width=18
        )
        self.chk_custom_nome.pack(side="right")
        
        self.ent_nome_planilha = ctk.CTkEntry(f_nome_planilha, height=42, corner_radius=10)
        self.ent_nome_planilha.pack(fill="x")
        self.ent_nome_planilha.bind('<KeyRelease>', lambda e: self.on_nome_planilha_edit())

        # Campo: Pasta de Salvamento
        f_destino = ctk.CTkFrame(m_card, fg_color="transparent")
        f_destino.pack(fill="x", padx=25, pady=(5, 20))
        
        ctk.CTkLabel(f_destino, text="PASTA DE SALVAMENTO", font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT_LABEL).pack(anchor="w", pady=(0, 4))
        
        f_dest_input = ctk.CTkFrame(f_destino, fg_color="transparent")
        f_dest_input.pack(fill="x")
        
        self.ent_pasta_destino = ctk.CTkEntry(f_dest_input, height=42, corner_radius=10)
        self.ent_pasta_destino.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_pasta_destino.insert(0, os.path.abspath("."))
        
        self.btn_pasta_destino = ctk.CTkButton(
            f_dest_input, 
            text="Selecionar Pasta", 
            width=140, 
            height=42, 
            corner_radius=10,
            fg_color=COLOR_PRIMARY, 
            hover_color=COLOR_ACCENT, 
            font=("Segoe UI", 12, "bold"), 
            command=self.selecionar_pasta_destino
        )
        self.btn_pasta_destino.pack(side="right")

        # Datas e Palavras
        s_card = self.create_card("DATAS E PALAVRAS-CHAVE")
        d_grid = ctk.CTkFrame(s_card, fg_color="transparent")
        d_grid.pack(fill="x", padx=20, pady=20)
        self.ent_de = self.create_date_input(d_grid, "DATA INÍCIO", 0, "01/12/2025")
        self.ent_ate = self.create_date_input(d_grid, "DATA FIM", 1, "18/12/2025")
        
        ctk.CTkLabel(s_card, text="FILTRAR POR PALAVRAS-CHAVE", font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT_LABEL).pack(anchor="w", padx=25)
        self.ent_palavra = ctk.CTkEntry(s_card, placeholder_text="Ex: dividendo, fato relevante...", height=45, corner_radius=10)
        self.ent_palavra.pack(padx=25, fill="x", pady=(5, 25))

        # Emissor
        e_card = self.create_card("PERFIL DO EMISSOR")
        e_grid = ctk.CTkFrame(e_card, fg_color="transparent")
        e_grid.pack(fill="x", padx=15, pady=20)
        self.cb_tp = self.create_grid_combo(e_grid, "TIPO PARTICIPANTE", list(self.dict_tipo_part.keys()), 0)
        self.cb_se = self.create_grid_combo(e_grid, "SITUAÇÃO EMISSOR", list(self.dict_sit_emissor.keys()), 1)
        self.cb_ce = self.create_grid_combo(e_grid, "CATEGORIA REGISTRO", list(self.dict_cat_emissor.keys()), 2)
        # --- NOVO: Adicionando Setor de Atividade na coluna 3 ---
        self.cb_sa = self.create_grid_combo(e_grid, "SETOR DE ATIVIDADE", list(self.dict_setor_atividade.keys()), 3)

        # Documentos
        d_card = self.create_card("CLASSIFICAÇÃO DO DOCUMENTO")
        dg = ctk.CTkFrame(d_card, fg_color="transparent")
        dg.pack(fill="x", padx=15, pady=15)
        self.cb_cat = self.create_doc_filter_group(dg, "CATEGORIA", self.f_cat_doc_search, 0)
        self.cb_tipo = self.create_doc_filter_group(dg, "TIPO", self.f_tipo_doc_search, 1)
        self.cb_esp = self.create_doc_filter_group(dg, "ESPÉCIE", self.f_esp_doc_search, 2)

        b_box = ctk.CTkFrame(d_card, fg_color="transparent")
        b_box.pack(fill="x", padx=25, pady=5)
        ctk.CTkButton(b_box, text="+ Adicionar Classificação", fg_color=COLOR_PRIMARY, command=self.add_categoria_lista).pack(side="left", padx=5)
        ctk.CTkButton(b_box, text="Limpar Classificações", fg_color="gray", command=self.limpar_categorias).pack(side="left", padx=5)

        self.txt_lista = ctk.CTkTextbox(d_card, height=100, corner_radius=10, fg_color=COLOR_INPUT_BG, border_width=1, font=("Consolas", 12))
        self.txt_lista.pack(fill="x", padx=25, pady=(5, 15))
        self.atualizar_visual_lista()

        # Botão Ação
        self.btn = ctk.CTkButton(self.container, text="DOWNLOAD", fg_color=COLOR_PRIMARY, hover_color=COLOR_ACCENT, height=70, corner_radius=15, font=("Segoe UI", 16, "bold"), command=self.disparar_processo)
        self.btn.pack(fill="x", pady=20)
        
        self.progress = ctk.CTkProgressBar(self.container, height=15, progress_color=COLOR_PRIMARY)
        self.progress.set(0); self.progress.pack(fill="x")
        self.lbl_msg = ctk.CTkLabel(self.container, text="Aguardando parâmetros...", font=("Segoe UI", 13, "italic"), text_color=COLOR_TEXT_LABEL)
        self.lbl_msg.pack(pady=10)
        self.on_modo_change()

    # --- UI Helpers & Controle de Modos/Planilha ---
    def on_modo_change(self):
        modo = self.radio_var.get()
        if modo == "download":
            self.ent_nome_planilha.configure(state="disabled")
            self.chk_custom_nome.configure(state="disabled")
            self.btn.configure(text="INICIAR DOWNLOAD (PDFS)")
        else:
            self.ent_nome_planilha.configure(state="normal")
            self.chk_custom_nome.configure(state="normal")
            if modo == "planilha":
                self.btn.configure(text="GERAR PLANILHA (.XLSX)")
            else:
                self.btn.configure(text="INICIAR DOWNLOAD + PLANILHA")
            if not self.custom_nome_var.get():
                self.atualizar_previa_nome_planilha()

    def on_toggle_custom_nome(self):
        if not self.custom_nome_var.get():
            self.atualizar_previa_nome_planilha()

    def on_nome_planilha_edit(self):
        if not self.custom_nome_var.get():
            self.custom_nome_var.set(True)

    def atualizar_previa_nome_planilha(self):
        if self.custom_nome_var.get():
            return
        if self.categorias_selecionadas:
            cat_nome = "MULTIPLAS"
        elif hasattr(self, 'cb_cat') and self.cb_cat.get():
            cat_nome = self.cb_cat.get()
        else:
            cat_nome = "GERAL"
        
        cat_limpo = DataParser.limpar_nome(cat_nome, 40)
        dt_str = datetime.now().strftime("%Y%m%d")
        nome_sugerido = f"Base_Coleta_{cat_limpo}_{dt_str}.xlsx"
        
        self.ent_nome_planilha.configure(state="normal")
        self.ent_nome_planilha.delete(0, "end")
        self.ent_nome_planilha.insert(0, nome_sugerido)
        if self.radio_var.get() == "download":
            self.ent_nome_planilha.configure(state="disabled")

    def selecionar_pasta_destino(self):
        caminho_inicial = self.ent_pasta_destino.get().strip() or os.path.abspath(".")
        pasta = filedialog.askdirectory(title="Selecione a pasta de salvamento", initialdir=caminho_inicial)
        if pasta:
            self.ent_pasta_destino.delete(0, "end")
            self.ent_pasta_destino.insert(0, os.path.normpath(pasta))

    def create_card(self, title):
        ctk.CTkLabel(self.container, text=title, font=("Segoe UI", 12, "bold"), text_color=COLOR_PRIMARY).pack(anchor="w", padx=5, pady=(15, 5))
        c = ctk.CTkFrame(self.container, fg_color=COLOR_CARD, corner_radius=15, border_width=1, border_color=COLOR_BORDER)
        c.pack(fill="x", pady=(0, 10))
        return c

    def create_date_input(self, master, label, col, val):
        f = ctk.CTkFrame(master, fg_color="transparent")
        f.grid(row=0, column=col, sticky="ew", padx=10)
        ctk.CTkLabel(f, text=label, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ent = ctk.CTkEntry(f, height=45, corner_radius=10, justify="center", border_width=2)
        ent.pack(fill="x"); ent.insert(0, val)
        ent.bind('<KeyRelease>', lambda e: self.validar_datas_ui())
        master.grid_columnconfigure(col, weight=1)
        return ent

    # --- Lógica de Validação e Processo ---
    def validar_datas_ui(self):
        def check(entry):
            val = entry.get()
            if re.match(r"^\d{2}/\d{2}/\d{4}$", val):
                try:
                    datetime.strptime(val, "%d/%m/%Y")
                    entry.configure(border_color=COLOR_BORDER)
                    return True
                except: pass
            entry.configure(border_color=COLOR_ERROR); return False
        
        v1, v2 = check(self.ent_de), check(self.ent_ate)
        if v1 and v2:
            if datetime.strptime(self.ent_de.get(), "%d/%m/%Y") > datetime.strptime(self.ent_ate.get(), "%d/%m/%Y"):
                self.ent_de.configure(border_color=COLOR_ERROR); return False
            return True
        return False

    def add_categoria_lista(self):
        cat, tip, esp = self.cb_cat.get(), self.cb_tipo.get(), self.cb_esp.get()
        match = [d for d in self.dados_completos if d['categoria'] == cat and d['tipo'] == tip and d['especie'] == esp]
        if match and match[0] not in self.categorias_selecionadas:
            self.categorias_selecionadas.append(match[0]); self.atualizar_visual_lista()
            self.atualizar_previa_nome_planilha()

    def limpar_categorias(self):
        self.categorias_selecionadas = []; self.atualizar_visual_lista()
        self.atualizar_previa_nome_planilha()

    def atualizar_visual_lista(self):
        self.txt_lista.configure(state="normal"); self.txt_lista.delete("1.0", "end")
        if not self.categorias_selecionadas:
            self.txt_lista.insert("1.0", "FILA VAZIA: Usará apenas o filtro único acima.")
        else:
            txt = "FILA DE EXTRAÇÃO:\n" + "\n".join([f"• {c['categoria']} | {c['tipo']}" for c in self.categorias_selecionadas])
            self.txt_lista.insert("1.0", txt)
        self.txt_lista.configure(state="disabled")

    def disparar_processo(self):
        if not self.validar_datas_ui(): 
            return messagebox.showerror("Erro", "Verifique as datas (DD/MM/AAAA).")
        
        ids = ",".join([c['id'] for c in self.categorias_selecionadas]) if self.categorias_selecionadas else ""
        nome = "Múltiplas" if self.categorias_selecionadas else self.cb_cat.get()
        
        if not ids:
            match = [d for d in self.dados_completos if d['categoria'] == self.cb_cat.get() and d['tipo'] == self.cb_tipo.get() and d['especie'] == self.cb_esp.get()]
            if not match: return messagebox.showerror("Erro", "Selecione uma categoria.")
            ids = match[0]['id']
            selected_categories_label = f"{self.cb_cat.get()} / {self.cb_tipo.get()} / {self.cb_esp.get()}"
        else:
            selected_categories_label = " | ".join([f"{c['categoria']} / {c['tipo']} / {c['especie']}" for c in self.categorias_selecionadas])

        self.btn.configure(state="disabled", text="PROCESSANDO...")
        threading.Thread(target=self.run_background, args=(self.radio_var.get(), ids, nome, self.ent_palavra.get(), selected_categories_label), daemon=True).start()

    def run_background(self, modo, ids, nome_cat, pc, selected_categories_label):
        try:
            # --- NOVO: Captura do Setor de Atividade e Chamada Segura por Nomes (kwargs) ---
            tp = self.dict_tipo_part.get(self.cb_tp.get(), "-1")
            se = self.dict_sit_emissor.get(self.cb_se.get(), "-1")
            ce = self.dict_cat_emissor.get(self.cb_ce.get(), "-1")
            sa = self.dict_setor_atividade.get(self.cb_sa.get(), "-1")
            tp_label = self.cb_tp.get()
            se_label = self.cb_se.get()
            ce_label = self.cb_ce.get()
            sa_label = self.cb_sa.get()
            tipo_doc = self.cb_tipo.get()
            esp_doc = self.cb_esp.get()
            categoria_doc = self.cb_cat.get()
            
            total, pasta = self.manager.iniciar_fluxo(
                modo=modo, 
                data_de=self.ent_de.get(), 
                data_ate=self.ent_ate.get(), 
                cod_id=ids, 
                nome_cat=nome_cat, 
                pc=pc, 
                tp=tp, 
                se=se, 
                ce=ce, 
                sa=sa,
                tp_label=tp_label,
                se_label=se_label,
                ce_label=ce_label,
                sa_label=sa_label,
                tipo_doc=tipo_doc,
                esp_doc=esp_doc,
                categoria_doc=categoria_doc,
                selected_categories_label=selected_categories_label,
                pasta_destino=self.ent_pasta_destino.get().strip(),
                nome_planilha=self.ent_nome_planilha.get().strip(),
                is_custom_nome=self.custom_nome_var.get() and (modo in ["planilha", "ambos"]),
                callback_progresso=self.atualizar_ui
            )
            
            msg = f"Extração Finalizada!\n\nDocumentos: {total}\nLocal: {os.path.basename(pasta)}"
            self.after(0, lambda: messagebox.showinfo("Concluído", msg))
            if total > 0 and platform.system() == "Windows": os.startfile(pasta)
        except Exception as e: 
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally: 
            self.after(0, self.reset_ui)

    def reset_ui(self):
        self.btn.configure(state="normal")
        self.on_modo_change()
        self.progress.set(0); self.lbl_msg.configure(text="Pronto para nova consulta.")

    def atualizar_ui(self, p, a, t):
        self.progress.set(p/100)
        self.lbl_msg.configure(text=f"Item {a} de {t}...")

    # --- Métodos de Dados (Combos/Search) ---
    def carregar_dados(self):
        p = resource_path("categorias.json")
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f: 
                dados_brutos = json.load(f)
            
            self.dados_completos = []
            for d in dados_brutos:
                cat = d['categoria']
                if d['id'].startswith(("IPE", "EST")) and not cat.startswith(("Tipo:", "Espécie:")):
                    self.dados_completos.append(d)

            self.lista_cat_doc = sorted(list(set(d['categoria'] for d in self.dados_completos)))
            self.cb_cat.configure(values=self.lista_cat_doc)
            
            if self.lista_cat_doc: 
                self.cb_cat.set(self.lista_cat_doc[0])
                self.on_cat_change() 

    def on_cat_change(self, e=None):
        cat = self.cb_cat.get(); tipos = sorted(list(set(d['tipo'] for d in self.dados_completos if d['categoria'] == cat)))
        if "TODOS" not in tipos: tipos.insert(0, "TODOS")
        self.cb_tipo.configure(values=tipos); self.cb_tipo.set("TODOS"); self.on_tipo_change()
        self.atualizar_previa_nome_planilha()

    def on_tipo_change(self, e=None):
        cat, tip = self.cb_cat.get(), self.cb_tipo.get()
        esp = ["TODOS"] if tip == "TODOS" else sorted(list(set(d['especie'] for d in self.dados_completos if d['categoria'] == cat and d['tipo'] == tip)))
        if "TODOS" not in esp: esp.insert(0, "TODOS")
        self.cb_esp.configure(values=esp); self.cb_esp.set("TODOS")

    def f_cat_doc_search(self, ent, cb):
        t = ent.get().lower(); f = [i for i in self.lista_cat_doc if t in i.lower()]
        if f: cb.configure(values=f); cb.set(f[0]); self.on_cat_change()

    def f_tipo_doc_search(self, ent, cb):
        cat = self.cb_cat.get(); tipos = sorted(list(set(d['tipo'] for d in self.dados_completos if d['categoria'] == cat)))
        t = ent.get().lower(); f = [i for i in tipos if t in i.lower()]
        if f: cb.configure(values=f); cb.set(f[0]); self.on_tipo_change()

    def f_esp_doc_search(self, ent, cb):
        cat, tip = self.cb_cat.get(), self.cb_tipo.get(); esps = sorted(list(set(d['especie'] for d in self.dados_completos if d['categoria'] == cat and d['tipo'] == tip)))
        t = ent.get().lower(); f = [i for i in esps if t in i.lower()]
        if f: cb.configure(values=f); cb.set(f[0])

    def f_combo(self, entry, combo, full_list):
        t = entry.get().lower(); f = [i for i in full_list if t in i.lower()]
        if f: combo.configure(values=f); combo.set(f[0])

    def create_grid_combo(self, master, label, values, col):
        f = ctk.CTkFrame(master, fg_color="transparent")
        f.grid(row=0, column=col, sticky="ew", padx=10)
        ctk.CTkLabel(f, text=label, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        search = ctk.CTkEntry(f, placeholder_text="Filtrar...", height=30); search.pack(fill="x", pady=2)
        cb = ctk.CTkComboBox(f, values=values, height=42, state="readonly"); cb.pack(fill="x"); cb.set("TODOS")
        search.bind('<KeyRelease>', lambda e: self.f_combo(search, cb, values))
        master.grid_columnconfigure(col, weight=1); return cb

    def create_doc_filter_group(self, master, label, filter_cmd, col):
        f = ctk.CTkFrame(master, fg_color="transparent"); f.grid(row=0, column=col, sticky="ew", padx=10)
        ctk.CTkLabel(f, text=label, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        search = ctk.CTkEntry(f, placeholder_text="Buscar...", height=30); search.pack(fill="x", pady=2)
        cb = ctk.CTkComboBox(f, values=[], height=42, state="readonly"); cb.pack(fill="x")
        search.bind('<KeyRelease>', lambda e: filter_cmd(search, cb))
        master.grid_columnconfigure(col, weight=1); return cb

if __name__ == "__main__":
    AppUI().mainloop()