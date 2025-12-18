import customtkinter as ctk
from tkinter import messagebox
import json, os, threading, platform
from business import DownloadManager

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green") 

COLOR_BG = "#F5F7F8"
COLOR_WHITE = "#FFFFFF"
COLOR_ACCENT = "#2D5A27"
COLOR_TEXT = "#2C3333"

class AppUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.manager = DownloadManager()
        self.dados_completos = []
        
        self.dict_tipo_part = {"TODOS": "-1", "BDR Não Patrocinados": "7", "Companhia Aberta": "1", "Companhia Dispensada de Registro": "6", "Companhia Estrangeira": "2", "Companhia Incentivada Registrada": "8"}
        self.dict_sit_emissor = {"TODOS": "-1", "Em Falência": "4", "Em Liquidação Extrajudicial": "5", "Em liquidação judicial": "7", "Em Recuperação Extrajudicial": "9", "Em Recuperação Judicial ou Equivalente": "8", "Fase Operacional": "2", "Fase Pré-Operacional": "1", "Paralisada": "6"}
        self.dict_cat_emissor = {"TODOS": "-1", "Categoria A": "1", "Categoria B": "2", "Não Identificado": "99"}

        self.title("CVM Pro - Coleta & Download")
        self.geometry("640x950") 
        self.configure(fg_color=COLOR_BG)
        
        self.setup_ui()
        self.after(100, self.carregar_dados)

    def setup_ui(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- SELETOR DE MODO ---
        self.mode_card = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_WHITE, corner_radius=15)
        self.mode_card.pack(padx=20, fill="x", pady=10)
        
        ctk.CTkLabel(self.mode_card, text="MODO DE OPERAÇÃO", font=("Inter", 10, "bold"), text_color=COLOR_ACCENT).pack(pady=(10,0))
        
        self.radio_var = ctk.StringVar(value="download")
        radio_frame = ctk.CTkFrame(self.mode_card, fg_color="transparent")
        radio_frame.pack(pady=10, fill="x")
        
        ctk.CTkRadioButton(radio_frame, text="Download PDFs", variable=self.radio_var, value="download").pack(side="left", expand=True)
        ctk.CTkRadioButton(radio_frame, text="Planilha (.xlsx)", variable=self.radio_var, value="planilha").pack(side="left", expand=True)
        ctk.CTkRadioButton(radio_frame, text="Ambos", variable=self.radio_var, value="ambos").pack(side="left", expand=True)

        self.card = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_WHITE, corner_radius=15)
        self.card.pack(padx=20, fill="both", expand=True, pady=5)

        d_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        d_frame.pack(fill="x", padx=25, pady=15)
        self.ent_de = self.create_date_input(d_frame, "Início", 0, "01/12/2025")
        self.ent_ate = self.create_date_input(d_frame, "Fim", 1, "18/12/2025")

        self.add_label("PALAVRAS-CHAVE (Separe por vírgula)")
        self.ent_palavra = ctk.CTkEntry(self.card, placeholder_text="aumento, capital", height=32)
        self.ent_palavra.pack(padx=25, fill="x", pady=2)

        self.busca_tp = self.add_search_field("BUSCAR TIPO PARTICIPANTE", lambda e: self.f_combo(self.busca_tp, self.cb_tp, list(self.dict_tipo_part.keys())))
        self.cb_tp = self.add_combo(list(self.dict_tipo_part.keys()))

        self.busca_se = self.add_search_field("BUSCAR SITUAÇÃO EMISSOR", lambda e: self.f_combo(self.busca_se, self.cb_se, list(self.dict_sit_emissor.keys())))
        self.cb_se = self.add_combo(list(self.dict_sit_emissor.keys()))

        self.busca_ce = self.add_search_field("BUSCAR CATEGORIA EMISSOR", lambda e: self.f_combo(self.busca_ce, self.cb_ce, list(self.dict_cat_emissor.keys())))
        self.cb_ce = self.add_combo(list(self.dict_cat_emissor.keys()))

        self.busca_cat_doc = self.add_search_field("BUSCAR CATEGORIA DOC", lambda e: self.f_cat_doc())
        self.cb_cat = self.add_combo([], self.on_cat_change)

        self.busca_tipo_doc = self.add_search_field("BUSCAR TIPO DOC", lambda e: self.f_tipo_doc())
        self.cb_tipo = self.add_combo([], self.on_tipo_change)

        self.busca_esp_doc = self.add_search_field("BUSCAR ESPÉCIE DOC", lambda e: self.f_esp_doc())
        self.cb_esp = self.add_combo([])

        self.progress = ctk.CTkProgressBar(self.card, height=6, progress_color=COLOR_ACCENT)
        self.progress.set(0)
        self.progress.pack(padx=30, fill="x", pady=15)
        self.lbl_msg = ctk.CTkLabel(self.card, text="Pronto para processar", font=("Inter", 11), text_color="#7F8487")
        self.lbl_msg.pack()

        self.btn = ctk.CTkButton(self.card, text="EXECUTAR AÇÃO", fg_color=COLOR_ACCENT, height=50, corner_radius=10, font=("Inter", 13, "bold"), command=self.disparar_processo)
        self.btn.pack(padx=30, fill="x", pady=20)

    def add_label(self, text):
        ctk.CTkLabel(self.card, text=text, font=("Inter", 9, "bold"), text_color="#7F8487").pack(anchor="w", padx=30, pady=(10, 0))

    def add_search_field(self, label, command):
        self.add_label(label)
        ent = ctk.CTkEntry(self.card, height=30)
        ent.pack(padx=25, fill="x", pady=1)
        ent.bind('<KeyRelease>', command)
        return ent

    def add_combo(self, values, command=None):
        cb = ctk.CTkComboBox(self.card, values=values, height=32, state="readonly")
        cb.pack(padx=25, fill="x", pady=(0, 5))
        if "TODOS" in values: cb.set("TODOS")
        elif values: cb.set(values[0])
        if command: cb.configure(command=command)
        return cb

    def create_date_input(self, master, label, col, val):
        ctk.CTkLabel(master, text=label, font=("Inter", 9, "bold")).grid(row=0, column=col, sticky="w", padx=5)
        ent = ctk.CTkEntry(master, height=35, justify="center")
        ent.grid(row=1, column=col, padx=5, sticky="ew")
        ent.insert(0, val)
        master.grid_columnconfigure(col, weight=1)
        return ent

    def f_combo(self, entry, combo, full_list):
        t = entry.get().lower()
        f = [i for i in full_list if t in i.lower()]
        if f: combo.configure(values=f); combo.set(f[0])

    def carregar_dados(self):
        if os.path.exists("categorias.json"):
            with open("categorias.json", 'r', encoding='utf-8') as f: self.dados_completos = json.load(f)
            self.lista_cat_doc = sorted(list(set(d['categoria'] for d in self.dados_completos)))
            self.cb_cat.configure(values=self.lista_cat_doc)
            self.cb_cat.set(self.lista_cat_doc[0])
            self.on_cat_change(None)

    def on_cat_change(self, e):
        cat = self.cb_cat.get()
        tipos = sorted(list(set(d['tipo'] for d in self.dados_completos if d['categoria'] == cat)))
        if "TODOS" not in tipos: tipos.insert(0, "TODOS")
        self.cb_tipo.configure(values=tipos); self.cb_tipo.set("TODOS")
        self.on_tipo_change(None)

    def on_tipo_change(self, e):
        cat, tip = self.cb_cat.get(), self.cb_tipo.get()
        if tip == "TODOS": self.cb_esp.configure(values=["TODOS"]); self.cb_esp.set("TODOS")
        else:
            esp = sorted(list(set(d['especie'] for d in self.dados_completos if d['categoria'] == cat and d['tipo'] == tip)))
            if "TODOS" not in esp: esp.insert(0, "TODOS")
            self.cb_esp.configure(values=esp); self.cb_esp.set("TODOS")

    def f_cat_doc(self):
        self.f_combo(self.busca_cat_doc, self.cb_cat, self.lista_cat_doc); self.on_cat_change(None)

    def f_tipo_doc(self):
        tipos = sorted(list(set(d['tipo'] for d in self.dados_completos if d['categoria'] == self.cb_cat.get())))
        if "TODOS" not in tipos: tipos.insert(0, "TODOS")
        self.f_combo(self.busca_tipo_doc, self.cb_tipo, tipos); self.on_tipo_change(None)

    def f_esp_doc(self):
        esps = sorted(list(set(d['especie'] for d in self.dados_completos if d['categoria'] == self.cb_cat.get() and d['tipo'] == self.cb_tipo.get())))
        if "TODOS" not in esps: esps.insert(0, "TODOS")
        self.f_combo(self.busca_esp_doc, self.cb_esp, esps)

    def atualizar_ui(self, p, a, t):
        self.progress.set(p/100)
        self.lbl_msg.configure(text=f"Processando {a} de {t}...", text_color=COLOR_ACCENT)

    def disparar_processo(self):
        modo = self.radio_var.get()
        cat, tip, esp = self.cb_cat.get(), self.cb_tipo.get(), self.cb_esp.get()
        match = [d for d in self.dados_completos if d['categoria'] == cat and d['tipo'] == tip and d['especie'] == esp]
        if not match: return messagebox.showwarning("Aviso", "Combine os filtros corretamente.")
        
        tp = self.dict_tipo_part.get(self.cb_tp.get(), "-1")
        se = self.dict_sit_emissor.get(self.cb_se.get(), "-1")
        ce = self.dict_cat_emissor.get(self.cb_ce.get(), "-1")
        
        self.btn.configure(state="disabled", text="AGUARDE...")
        threading.Thread(target=self.run_background, args=(modo, match[0]['id'], cat, self.ent_palavra.get(), tp, se, ce), daemon=True).start()

    def run_background(self, modo, cid, cat_nome, pc, tp, se, ce):
        try:
            total, pasta = self.manager.iniciar_fluxo(modo, self.ent_de.get(), self.ent_ate.get(), cid, cat_nome, pc, tp, se, ce, self.atualizar_ui)
            self.after(0, lambda: messagebox.showinfo("Sucesso", f"Processado com sucesso: {total} itens."))
            if total > 0 and platform.system() == "Windows": os.startfile(pasta)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.after(0, lambda: self.btn.configure(state="normal", text="EXECUTAR AÇÃO"))

if __name__ == "__main__":
    AppUI().mainloop()