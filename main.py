import customtkinter as ctk
from tkinter import messagebox
import json, os, threading, platform, re, sys
from datetime import datetime
from business import DownloadManager

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
        
        self.dict_tipo_part = {"TODOS": "-1", "BDR Não Patrocinados": "7", "Companhia Aberta": "1", "Companhia Dispensada de Registro": "6", "Companhia Estrangeira": "2", "Companhia Incentivada Registrada": "8"}
        self.dict_sit_emissor = {"TODOS": "-1", "Em Falência": "4", "Em Liquidação Extrajudicial": "5", "Em liquidação judicial": "7", "Em Recuperação Extrajudicial": "9", "Em Recuperação Judicial ou Equivalente": "8", "Fase Operacional": "2", "Fase Pré-Operacional": "1", "Paralisada": "6"}
        self.dict_cat_emissor = {"TODOS": "-1", "Categoria A": "1", "Categoria B": "2", "Não Identificado": "99"}

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
        r_frame = ctk.CTkFrame(m_card, fg_color="transparent")
        r_frame.pack(pady=20, padx=30, fill="x")
        for t, v in [("Download PDFs", "download"), ("Gerar Planilha", "planilha"), ("Ambos", "ambos")]:
            ctk.CTkRadioButton(r_frame, text=t, variable=self.radio_var, value=v, font=("Segoe UI", 13, "bold")).pack(side="left", expand=True)

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

    # --- UI Helpers ---
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

    def limpar_categorias(self):
        self.categorias_selecionadas = []; self.atualizar_visual_lista()

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

        self.btn.configure(state="disabled", text="PROCESSANDO...")
        threading.Thread(target=self.run_background, args=(self.radio_var.get(), ids, nome, self.ent_palavra.get()), daemon=True).start()

    def run_background(self, modo, ids, nome_cat, pc):
        try:
            tp, se, ce = self.dict_tipo_part.get(self.cb_tp.get(), "-1"), self.dict_sit_emissor.get(self.cb_se.get(), "-1"), self.dict_cat_emissor.get(self.cb_ce.get(), "-1")
            total, pasta = self.manager.iniciar_fluxo(modo, self.ent_de.get(), self.ent_ate.get(), ids, nome_cat, pc, tp, se, ce, self.atualizar_ui)
            
            msg = f"Extração Finalizada!\n\nDocumentos: {total}\nLocal: {os.path.basename(pasta)}"
            self.after(0, lambda: messagebox.showinfo("Concluído", msg))
            if total > 0 and platform.system() == "Windows": os.startfile(pasta)
        except Exception as e: 
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally: 
            self.after(0, self.reset_ui)

    def reset_ui(self):
        self.btn.configure(state="normal", text="INICIAR PROCESSAMENTO INSTITUCIONAL")
        self.progress.set(0); self.lbl_msg.configure(text="Pronto para nova consulta.")

    def atualizar_ui(self, p, a, t):
        self.progress.set(p/100)
        self.lbl_msg.configure(text=f"Item {a} de {t}...")

    # --- Métodos de Dados (Combos/Search) ---
    # def carregar_dados(self):
    #     p = resource_path("categorias.json")
    #     if os.path.exists(p):
    #         with open(p, 'r', encoding='utf-8') as f: self.dados_completos = json.load(f)
    #         self.lista_cat_doc = sorted(list(set(d['categoria'] for d in self.dados_completos)))
    #         self.cb_cat.configure(values=self.lista_cat_doc)
    #         if self.lista_cat_doc: self.cb_cat.set(self.lista_cat_doc[0]); self.on_cat_change()
    def carregar_dados(self):
        p = resource_path("categorias.json")
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f: 
                dados_brutos = json.load(f)
            
            # --- NOVO: FILTRO DE LIMPEZA ---
            # Vamos guardar apenas os dados onde o ID começa com IPE ou EST
            # E ignorar categorias que começam com "Tipo:" ou "Espécie:"
            self.dados_completos = []
            for d in dados_brutos:
                cat = d['categoria']
                # Verifica se é um ID válido da CVM e não é um título falso
                if d['id'].startswith(("IPE", "EST")) and not cat.startswith(("Tipo:", "Espécie:")):
                    self.dados_completos.append(d)
            # ---------------------------------

            # Agora criamos a lista de categorias apenas com os dados limpos
            self.lista_cat_doc = sorted(list(set(d['categoria'] for d in self.dados_completos)))
            self.cb_cat.configure(values=self.lista_cat_doc)
            
            if self.lista_cat_doc: 
                self.cb_cat.set(self.lista_cat_doc[0])
                self.on_cat_change() # Isto vai acionar a cascata automaticamente!

    def on_cat_change(self, e=None):
        cat = self.cb_cat.get(); tipos = sorted(list(set(d['tipo'] for d in self.dados_completos if d['categoria'] == cat)))
        if "TODOS" not in tipos: tipos.insert(0, "TODOS")
        self.cb_tipo.configure(values=tipos); self.cb_tipo.set("TODOS"); self.on_tipo_change()

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