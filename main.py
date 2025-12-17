import customtkinter as ctk
from tkinter import messagebox
import json
import os
import threading
import platform
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
        self.lista_cat = []
        self.lista_tipo = []
        self.lista_esp = []

        self.title("Downloader de PDFs da CVM")
        # Janela reduzida para 620 de altura
        self.geometry("600x620")
        self.configure(fg_color=COLOR_BG)
        self.resizable(False, False)
        
        self.setup_ui()
        self.after(100, self.carregar_dados)

    def setup_ui(self):
        # Header compacto
        self.header_label = ctk.CTkLabel(self, text="CVM Downloader", 
                                        font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
                                        text_color=COLOR_TEXT)
        self.header_label.pack(pady=(25, 15))

        # Card Principal
        self.card = ctk.CTkFrame(self, fg_color=COLOR_WHITE, corner_radius=15)
        self.card.pack(padx=30, fill="both", expand=True, pady=(0, 25))

        # --- SEÇÃO DE DATAS (Lado a Lado) ---
        date_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        date_frame.pack(fill="x", padx=25, pady=(20, 10))
        
        self.ent_de = self.create_input(date_frame, "Início", 0, "01/12/2025")
        self.ent_ate = self.create_input(date_frame, "Fim", 1, "05/12/2025")

        # --- FILTROS COMPACTOS ---
        # Categoria
        self.busca_cat = self.create_filter_block("CATEGORIA", self.filtrar_cat)
        self.cb_cat = self.create_styled_combo(self.ao_selecionar_categoria)

        # Tipo
        self.busca_tipo = self.create_filter_block("TIPO", self.filtrar_tipo_ui)
        self.cb_tipo = self.create_styled_combo(self.ao_selecionar_tipo)

        # Espécie
        self.busca_esp = self.create_filter_block("ESPÉCIE", self.filtrar_esp_ui)
        self.cb_esp = self.create_styled_combo(None)

        # --- PROGRESSO ---
        self.progress = ctk.CTkProgressBar(self.card, height=6, progress_color=COLOR_ACCENT)
        self.progress.set(0)
        self.progress.pack(padx=30, fill="x", pady=(15, 0))
        
        self.lbl_msg = ctk.CTkLabel(self.card, text="Pronto para baixar", font=ctk.CTkFont(size=11), text_color="#7F8487")
        self.lbl_msg.pack(pady=(2, 10))

        # --- BOTÃO ---
        self.btn = ctk.CTkButton(self.card, text="BAIXAR ARQUIVOS", 
                                 fg_color=COLOR_ACCENT, hover_color="#1E3F1A",
                                 font=ctk.CTkFont(size=13, weight="bold"),
                                 height=45, corner_radius=10, command=self.disparar_processo)
        self.btn.pack(padx=30, fill="x", pady=(5, 25))

    def create_filter_block(self, label_text, command):
        """Cria o label e o entry de busca de forma compacta."""
        lbl = ctk.CTkLabel(self.card, text=label_text, font=ctk.CTkFont(size=9, weight="bold"), text_color="#7F8487")
        lbl.pack(anchor="w", padx=30, pady=(8, 0))
        
        ent = ctk.CTkEntry(self.card, placeholder_text=f"Filtrar {label_text.lower()}...", height=30, 
                           corner_radius=6, border_width=1, border_color="#E5E5E5", fg_color="#FAFAFA")
        ent.pack(padx=25, fill="x", pady=2)
        ent.bind('<KeyRelease>', lambda e: command())
        return ent

    def create_styled_combo(self, command):
        cb = ctk.CTkComboBox(self.card, height=32, corner_radius=6, border_color="#E5E5E5", 
                             fg_color="#FAFAFA", button_color="#E5E5E5", state="readonly")
        cb.pack(padx=25, fill="x", pady=(0, 5))
        if command: cb.configure(command=lambda x: command(None))
        return cb

    def create_input(self, master, placeholder, col, default_val):
        ent = ctk.CTkEntry(master, placeholder_text=placeholder, height=35, corner_radius=6, 
                           border_color="#E5E5E5", fg_color="#FAFAFA", text_color=COLOR_TEXT, justify="center")
        ent.grid(row=0, column=col, padx=5, sticky="ew")
        ent.insert(0, default_val)
        master.grid_columnconfigure(col, weight=1)
        return ent

    # --- Lógica de Dados ---
    def carregar_dados(self):
        if os.path.exists("categorias.json"):
            with open("categorias.json", 'r', encoding='utf-8') as f:
                self.dados_completos = json.load(f)
            self.lista_cat = sorted(list(set(d['categoria'] for d in self.dados_completos)))
            self.cb_cat.configure(values=self.lista_cat)
            self.cb_cat.set(self.lista_cat[0])
            self.ao_selecionar_categoria(None)

    def ao_selecionar_categoria(self, event):
        cat_sel = self.cb_cat.get()
        tipos = sorted(list(set(d['tipo'] for d in self.dados_completos if d['categoria'] == cat_sel)))
        if "TODOS" not in tipos: tipos.insert(0, "TODOS")
        self.lista_tipo = tipos
        self.cb_tipo.configure(values=tipos)
        self.cb_tipo.set("TODOS")
        self.ao_selecionar_tipo(None)

    def ao_selecionar_tipo(self, event):
        cat_sel, tipo_sel = self.cb_cat.get(), self.cb_tipo.get()
        if tipo_sel == "TODOS":
            self.cb_esp.configure(values=["TODOS"])
        else:
            especies = sorted(list(set(d['especie'] for d in self.dados_completos if d['categoria'] == cat_sel and d['tipo'] == tipo_sel)))
            if "TODOS" not in especies: especies.insert(0, "TODOS")
            self.lista_esp = especies
            self.cb_esp.configure(values=especies)
        self.cb_esp.set("TODOS")

    def filtrar_cat(self):
        termo = self.busca_cat.get().lower()
        filtradas = [i for i in self.lista_cat if termo in i.lower()]
        if filtradas:
            self.cb_cat.configure(values=filtradas)
            self.cb_cat.set(filtradas[0])
            self.ao_selecionar_categoria(None)

    def filtrar_tipo_ui(self):
        termo = self.busca_tipo.get().lower()
        filtradas = [i for i in self.lista_tipo if termo in i.lower()]
        if filtradas:
            self.cb_tipo.configure(values=filtradas)
            self.cb_tipo.set(filtradas[0])
            self.ao_selecionar_tipo(None)

    def filtrar_esp_ui(self):
        termo = self.busca_esp.get().lower()
        filtradas = [i for i in self.lista_esp if termo in i.lower()]
        if filtradas:
            self.cb_esp.configure(values=filtradas)
            self.cb_esp.set(filtradas[0])

    def atualizar_ui(self, p, a, t):
        self.progress.set(p/100)
        self.lbl_msg.configure(text=f"Arquivo {a} de {t}...", text_color=COLOR_ACCENT)

    def disparar_processo(self):
        match = [d for d in self.dados_completos if d['categoria'] == self.cb_cat.get() 
                 and d['tipo'] == self.cb_tipo.get() and d['especie'] == self.cb_esp.get()]
        if not match: return messagebox.showwarning("Aviso", "ID não encontrado.")
        
        self.btn.configure(state="disabled", text="BAIXANDO...")
        threading.Thread(target=self.run_background, args=(match[0]['id'],), daemon=True).start()

    def run_background(self, cod_id):
        try:
            total, pasta = self.manager.iniciar_fluxo(self.ent_de.get(), self.ent_ate.get(), cod_id, self.atualizar_ui)
            self.after(0, lambda: messagebox.showinfo("CVM Pro", f"Concluído: {total} arquivos."))
            if platform.system() == "Windows": self.after(500, lambda: os.startfile(pasta))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.after(0, lambda: self.btn.configure(state="normal", text="BAIXAR ARQUIVOS"))

if __name__ == "__main__":
    app = AppUI()
    app.mainloop()