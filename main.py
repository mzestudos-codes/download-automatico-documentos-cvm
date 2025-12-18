import customtkinter as ctk
from tkinter import messagebox
import json, os, threading, platform, re
from datetime import datetime
from business import DownloadManager

# Configurações de Aparência
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue") 

COLOR_BG = "#F0F2F5"
COLOR_CARD = "#FFFFFF"
COLOR_PRIMARY = "#1A73E8"
COLOR_ERROR = "#D93025"  # Vermelho para bordas de erro
COLOR_TEXT_MAIN = "#202124"
COLOR_TEXT_SECONDARY = "#5F6368"

class AppUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.manager = DownloadManager()
        self.dados_completos = []
        
        self.dict_tipo_part = {"TODOS": "-1", "BDR Não Patrocinados": "7", "Companhia Aberta": "1", "Companhia Dispensada de Registro": "6", "Companhia Estrangeira": "2", "Companhia Incentivada Registrada": "8"}
        self.dict_sit_emissor = {"TODOS": "-1", "Em Falência": "4", "Em Liquidação Extrajudicial": "5", "Em liquidação judicial": "7", "Em Recuperação Extrajudicial": "9", "Em Recuperação Judicial ou Equivalente": "8", "Fase Operacional": "2", "Fase Pré-Operacional": "1", "Paralisada": "6"}
        self.dict_cat_emissor = {"TODOS": "-1", "Categoria A": "1", "Categoria B": "2", "Não Identificado": "99"}

        self.title("CVM Intelligence Pro")
        self.geometry("700x950") 
        self.configure(fg_color=COLOR_BG)
        
        self.setup_ui()
        self.after(100, self.carregar_dados)

    def setup_ui(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 20))
        ctk.CTkLabel(header_frame, text="CVM Intelligence", font=("Segoe UI", 24, "bold"), text_color=COLOR_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Validação de datas e logs de execução ativos", font=("Segoe UI", 13), text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")

        # MODO
        self.create_section_title("MODO DE OPERAÇÃO")
        self.mode_card = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color="#E0E0E0")
        self.mode_card.pack(fill="x", pady=(0, 15))
        self.radio_var = ctk.StringVar(value="download")
        radio_frame = ctk.CTkFrame(self.mode_card, fg_color="transparent")
        radio_frame.pack(pady=15, padx=20, fill="x")
        for text, val in [("Download PDFs", "download"), ("Gerar Planilha", "planilha"), ("Ambos", "ambos")]:
            ctk.CTkRadioButton(radio_frame, text=text, variable=self.radio_var, value=val, font=("Segoe UI", 12), fg_color=COLOR_PRIMARY).pack(side="left", expand=True)

        # BUSCA + DATAS
        self.create_section_title("PARAMETROS DE BUSCA")
        self.search_card = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color="#E0E0E0")
        self.search_card.pack(fill="x", pady=(0, 15))

        d_frame = ctk.CTkFrame(self.search_card, fg_color="transparent")
        d_frame.pack(fill="x", padx=20, pady=15)
        self.ent_de = self.create_date_input(d_frame, "Data Início", 0, "01/12/2025")
        self.ent_ate = self.create_date_input(d_frame, "Data Fim", 1, "18/12/2025")
        
        self.add_field_label(self.search_card, "PALAVRAS-CHAVE (Separe por vírgula)")
        self.ent_palavra = ctk.CTkEntry(self.search_card, placeholder_text="Ex: aumento, capital", height=38, corner_radius=8)
        self.ent_palavra.pack(padx=20, fill="x", pady=(0, 15))

        # EMISSOR
        self.create_section_title("PERFIL DO EMISSOR")
        self.emissor_card = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color="#E0E0E0")
        self.emissor_card.pack(fill="x", pady=(0, 15))
        self.busca_tp = self.create_search_combo_group(self.emissor_card, "Tipo de Participante", self.dict_tipo_part)
        self.cb_tp = self.last_combo
        self.busca_se = self.create_search_combo_group(self.emissor_card, "Situação do Emissor", self.dict_sit_emissor)
        self.cb_se = self.last_combo
        self.busca_ce = self.create_search_combo_group(self.emissor_card, "Categoria de Registro", self.dict_cat_emissor)
        self.cb_ce = self.last_combo

        # DOCUMENTO
        self.create_section_title("DETALHES DO DOCUMENTO")
        self.doc_card = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color="#E0E0E0")
        self.doc_card.pack(fill="x", pady=(0, 20))
        self.add_field_label(self.doc_card, "Categoria do Documento")
        self.busca_cat_doc = ctk.CTkEntry(self.doc_card, height=30); self.busca_cat_doc.pack(padx=20, fill="x")
        self.cb_cat = self.add_styled_combo(self.doc_card, [], self.on_cat_change)
        self.busca_cat_doc.bind('<KeyRelease>', lambda e: self.f_cat_doc())
        self.add_field_label(self.doc_card, "Tipo")
        self.busca_tipo_doc = ctk.CTkEntry(self.doc_card, height=30); self.busca_tipo_doc.pack(padx=20, fill="x")
        self.cb_tipo = self.add_styled_combo(self.doc_card, [], self.on_tipo_change)
        self.busca_tipo_doc.bind('<KeyRelease>', lambda e: self.f_tipo_doc())
        self.add_field_label(self.doc_card, "Espécie")
        self.busca_esp_doc = ctk.CTkEntry(self.doc_card, height=30); self.busca_esp_doc.pack(padx=20, fill="x")
        self.cb_esp = self.add_styled_combo(self.doc_card, [])
        self.busca_esp_doc.bind('<KeyRelease>', lambda e: self.f_esp_doc())

        self.btn = ctk.CTkButton(self.scroll_frame, text="EXECUTAR PROCESSAMENTO", fg_color=COLOR_PRIMARY, height=55, font=("Segoe UI", 14, "bold"), command=self.disparar_processo)
        self.btn.pack(fill="x", pady=10)
        self.progress = ctk.CTkProgressBar(self.scroll_frame, height=8); self.progress.set(0); self.progress.pack(fill="x", pady=5)
        self.lbl_msg = ctk.CTkLabel(self.scroll_frame, text="Aguardando validação de dados...", font=("Segoe UI", 12)); self.lbl_msg.pack()

    # --- LÓGICA DE VALIDAÇÃO ---
    def validar_datas_ui(self):
        def check_fmt(entry):
            val = entry.get()
            if re.match(r"^\d{2}/\d{2}/\d{4}$", val):
                try:
                    datetime.strptime(val, "%d/%m/%Y")
                    entry.configure(border_color="#E0E0E0")
                    return True
                except: pass
            entry.configure(border_color=COLOR_ERROR)
            return False

        v1 = check_fmt(self.ent_de)
        v2 = check_fmt(self.ent_ate)

        if v1 and v2:
            d1 = datetime.strptime(self.ent_de.get(), "%d/%m/%Y")
            d2 = datetime.strptime(self.ent_ate.get(), "%d/%m/%Y")
            if d1 > d2:
                self.ent_de.configure(border_color=COLOR_ERROR)
                self.ent_ate.configure(border_color=COLOR_ERROR)
                return False
            return True
        return False

    # --- UI FACTORY ---
    def create_date_input(self, master, label, col, val):
        ctk.CTkLabel(master, text=label, font=("Segoe UI", 10)).grid(row=0, column=col, sticky="w", padx=5)
        ent = ctk.CTkEntry(master, height=38, corner_radius=8, justify="center", border_width=2)
        ent.grid(row=1, column=col, padx=5, sticky="ew")
        ent.insert(0, val)
        ent.bind('<KeyRelease>', lambda e: self.validar_datas_ui())
        return ent

    def disparar_processo(self):
        if not self.validar_datas_ui():
            return messagebox.showerror("Erro de Data", "Verifique se as datas estão no formato DD/MM/AAAA e se o Início é anterior ao Fim.")
        
        cat_sel, tip, esp = self.cb_cat.get(), self.cb_tipo.get(), self.cb_esp.get()
        match = [d for d in self.dados_completos if d['categoria'] == cat_sel and d['tipo'] == tip and d['especie'] == esp]
        if not match: return messagebox.showwarning("Aviso", "Filtros inválidos.")
        
        tp, se, ce = self.dict_tipo_part.get(self.cb_tp.get(), "-1"), self.dict_sit_emissor.get(self.cb_se.get(), "-1"), self.dict_cat_emissor.get(self.cb_ce.get(), "-1")
        
        self.btn.configure(state="disabled", text="EM EXECUÇÃO...")
        threading.Thread(target=self.run_background, args=(self.radio_var.get(), match[0]['id'], cat_sel, self.ent_palavra.get(), tp, se, ce), daemon=True).start()

    # --- MÉTODOS RESTANTES (IGUAIS) ---
    def create_section_title(self, text): ctk.CTkLabel(self.scroll_frame, text=text, font=("Segoe UI", 11, "bold"), text_color=COLOR_PRIMARY).pack(anchor="w", padx=5, pady=(10, 5))
    def add_field_label(self, master, text): ctk.CTkLabel(master, text=text, font=("Segoe UI", 10, "bold"), text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(10, 2))
    def add_styled_combo(self, master, values, command=None):
        cb = ctk.CTkComboBox(master, values=values, height=35, state="readonly"); cb.pack(padx=20, fill="x", pady=(2, 12))
        if "TODOS" in values: cb.set("TODOS")
        elif values: cb.set(values[0])
        if command: cb.configure(command=command)
        return cb
    def create_search_combo_group(self, master, label, data_dict):
        self.add_field_label(master, label); ent = ctk.CTkEntry(master, height=30); ent.pack(padx=20, fill="x")
        combo = self.add_styled_combo(master, list(data_dict.keys()))
        ent.bind('<KeyRelease>', lambda e: self.f_combo(ent, combo, list(data_dict.keys())))
        self.last_combo = combo
        return ent
    def f_combo(self, entry, combo, full_list):
        t = entry.get().lower(); f = [i for i in full_list if t in i.lower()]
        if f: combo.configure(values=f); combo.set(f[0])
    def carregar_dados(self):
        if os.path.exists("categorias.json"):
            with open("categorias.json", 'r', encoding='utf-8') as f: self.dados_completos = json.load(f)
            self.lista_cat_doc = sorted(list(set(d['categoria'] for d in self.dados_completos)))
            self.cb_cat.configure(values=self.lista_cat_doc); self.cb_cat.set(self.lista_cat_doc[0]); self.on_cat_change(None)
    def on_cat_change(self, e):
        cat = self.cb_cat.get(); tipos = sorted(list(set(d['tipo'] for d in self.dados_completos if d['categoria'] == cat)))
        if "TODOS" not in tipos: tipos.insert(0, "TODOS")
        self.cb_tipo.configure(values=tipos); self.cb_tipo.set("TODOS"); self.on_tipo_change(None)
    def on_tipo_change(self, e):
        cat, tip = self.cb_cat.get(), self.cb_tipo.get()
        if tip == "TODOS": self.cb_esp.configure(values=["TODOS"]); self.cb_esp.set("TODOS")
        else:
            esp = sorted(list(set(d['especie'] for d in self.dados_completos if d['categoria'] == cat and d['tipo'] == tip)))
            if "TODOS" not in esp: esp.insert(0, "TODOS")
            self.cb_esp.configure(values=esp); self.cb_esp.set("TODOS")
    def f_cat_doc(self): self.f_combo(self.busca_cat_doc, self.cb_cat, self.lista_cat_doc); self.on_cat_change(None)
    def f_tipo_doc(self): tipos = sorted(list(set(d['tipo'] for d in self.dados_completos if d['categoria'] == self.cb_cat.get()))); self.f_combo(self.busca_tipo_doc, self.cb_tipo, tipos); self.on_tipo_change(None)
    def f_esp_doc(self): esps = sorted(list(set(d['especie'] for d in self.dados_completos if d['categoria'] == self.cb_cat.get() and d['tipo'] == self.cb_tipo.get()))); self.f_combo(self.busca_esp_doc, self.cb_esp, esps)
    def atualizar_ui(self, p, a, t): self.progress.set(p/100); self.lbl_msg.configure(text=f"Processando item {a} de {t}...", text_color=COLOR_PRIMARY)
    def run_background(self, modo, cid, cat_nome, pc, tp, se, ce):
        try:
            total, pasta = self.manager.iniciar_fluxo(modo, self.ent_de.get(), self.ent_ate.get(), cid, cat_nome, pc, tp, se, ce, self.atualizar_ui)
            if total > 0 and platform.system() == "Windows": os.startfile(pasta)
        except Exception as e: self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally: self.after(0, lambda: self.btn.configure(state="normal", text="EXECUTAR AÇÃO"))

if __name__ == "__main__":
    AppUI().mainloop()