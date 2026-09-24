import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import datetime
import pystray
import queue

from PIL import Image, ImageDraw

# =========================
# CONFIGURAÇÕES
# =========================

INTERVALO_SEGUNDOS = 10
DURACAO_AVISO_SEGUNDOS = 20
QUANTIDADE_ML = 200
META_DIARIA_ML=2000
PASTA_DADOS = os.path.join(os.getenv("APPDATA"), ".lembrete_agua")
ADIAR_AVISO_SEGUNDOS = 10 *60 

os.makedirs(PASTA_DADOS, exist_ok=True)
ARQUIVO_DADOS = os.path.join(PASTA_DADOS, "agua_dados.json")

class LembreteAgua:

    def __init__(self, root):
        self.root = root
        
        self.root.title("Lembrete de Água")
        self.root.geometry("450x560")
        self.root.resizable(False, False)
        self.root.configure(bg="#F4F7FB")

        # self.root.withdraw()

        self.popup = None
        self.timer_fechar = None
        self.timer_contagem = None
        self.pausado = False
        self.fila_acoes = queue.Queue()
        self.icone_bandeja = None
        
        self.total_bebido = self.carregar_dados()
        self.data_atual = str(datetime.date.today())
        
        self.intervalo_nome, self.intervalo_segundos = self.carregar_intervalo()
        self.criar_janela_principal()
        self.root.withdraw()  # Esconde a janela principal inicialmente
        
        #Ao clicar no X, esconde em vez de encerrar
        self.root.protocol("WM_DELETE_WINDOW", self.ocultar_janela)
        
        # Inicia o icone perto do relógio
        self.criar_icone_bandeja()
        # Verifica comandos vindos do ícone
        self.processar_fila()
        # Começa a contagem
        self.agendar_aviso()
        self.verificar_mudanca_dia()
        
    def carregar_dados(self):
        hoje = str(datetime.date.today())
        if not os.path.exists(ARQUIVO_DADOS):
            return 0
        
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
                
                # Se os dados forem de hoje, mantém o total
                if dados.get("data") == hoje:
                    return dados.get("total_bebido", 0)
                # Se mudou o dia, começa do zero
                return 0
        except:
            return 0

    def carregar_intervalo(self):
        if not os.path.exists(ARQUIVO_DADOS):
            return "Teste-10 segundos", INTERVALO_SEGUNDOS
        
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
                
            nome = dados.get("intervalo_nome", "Teste-10 segundos")
            segundos = dados.get("intervalo_segundos", INTERVALO_SEGUNDOS)
            return nome, segundos
        except:
            return "Teste-10 segundos", INTERVALO_SEGUNDOS
           
    def salvar_dados(self):
                dados = {
                    "data":str(datetime.date.today()),
                    "total_bebido":self.total_bebido,
                    "intervalo_segundos":self.intervalo_segundos,
                    "intervalo_nome":self.opcao_intervalo.get()
                }
                
                with open(ARQUIVO_DADOS, "w", encoding="utf-8") as arquivo:
                    json.dump(dados, arquivo, indent=4, ensure_ascii=False)

    def verificar_mudanca_dia(self):
        hoje = str(datetime.date.today())

        if hoje != self.data_atual:
            self.data_atual = hoje
            self.total_bebido = 0

            self.salvar_dados()
            self.atualizar_janela_principal()

        print("Novo dia: consumo de água zerado.")

    # Verifica novamente a cada minuto
        self.root.after(
        60 * 1000,
        self.verificar_mudanca_dia
    )
    def ocultar_janela(self):
        self.root.withdraw()
        
    def abrir_janela(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    def solicitar_beber (self, icon=None, item=None):
        self.fila_acoes.put(("beber",None))

    def solicitar_zerar(self, icon=None, item=None):
        self.fila_acoes.put(("zerar",None))
            
    def solicitar_pausa(self, icon=None, item=None):
        self.fila_acoes.put(("pausa",None))
        
    def solicitar_intervalo(self, nome):
        self.fila_acoes.put(("intervalo", nome))
                    
    def solicitar_abrir(self, icon=None, item=None):
        self.fila_acoes.put("abrir") 
        
    def solicitar_sair(self, icon=None, item=None):
        self.fila_acoes.put("sair")
        
    def processar_fila(self):
        try:
            while True:
                acao = self.fila_acoes.get_nowait()
                
                #Aceita comandos antigos
                if acao == "abrir":
                    self.abrir_janela()
                    
                elif acao == "sair":
                    self.sair_programa()
                    return
                
                #novos comandos da bandeja
                elif isinstance(acao, tuple):
                    comando, valor = acao
                    if comando == "beber":
                        self.bebi_agua()
                    elif comando == "zerar":
                        self.zerar_agua()
                    elif comando == "pausa":
                        self.alternar_pausa()
                    elif comando == "intervalo":
                        self.opcao_intervalo.set(valor)
                        self.alterar_intervalo()
                        
        except queue.Empty:
            pass

        self.root.after(100, self.processar_fila)
        
    def criar_icone_bandeja(self):
        
        imagem = Image.new("RGB", (64, 64), "white")
        desenho = ImageDraw.Draw(imagem)
        
        # Desenha uma gota simples
        desenho.ellipse(
            (18, 24, 46, 52),
            fill="#1976D2",
            outline="black"
            )
        
        desenho.polygon(
            [(32, 8), (18, 34), (46, 34)],
            fill="#1976D2",
            outline="black"
            )
        
        #Submenu de intervalos
        menu_intervalo = pystray.Menu(
            
            pystray.MenuItem(
                "Teste-10 segundos",
                lambda icon, item:
                self.solicitar_intervalo("Teste-10 segundos")
            ),
            
            pystray.MenuItem(
                "30 minutos",
                lambda icon, item:
                self.solicitar_intervalo("30 minutos")
            ),
            
            pystray.MenuItem(
                "45 minutos",
                lambda icon, item:
                self.solicitar_intervalo("45 minutos")
            ),
            
            pystray.MenuItem(
                "60 minutos",
                lambda icon, item:
                self.solicitar_intervalo("60 minutos")
            ),
            
            pystray.MenuItem(
                "90 minutos",
                lambda icon, item:
                self.solicitar_intervalo("90 minutos")
            )
        )
            
            # Menu principal
        menu=pystray.Menu(
                
            pystray.MenuItem(
                    f"💧 Bebi {QUANTIDADE_ML} ml",
                    self.solicitar_beber
                ),
            
            pystray.MenuItem(
                    "🔄 Resetar Consumo",
                    self.solicitar_zerar
                ),

            pystray.MenuItem(
                    "⏸️ Pausar/Continuar lembretes",
                    self.solicitar_pausa
                ),
            
            pystray.MenuItem(
                    "Intervalo",
                    menu_intervalo
                ),
            
            pystray.Menu.SEPARATOR,
            
            pystray.MenuItem(
                    "Abrir painel",
                    self.solicitar_abrir,
                    default=True
                ),
            
            pystray.MenuItem(
                    "Sair",
                    self.solicitar_sair
                )
            )
        self.icone_bandeja = pystray.Icon(
            "lembrete_agua",
            imagem,
            "Lembrete de Água",
            menu
        )
        
        self.icone_bandeja.run_detached()
        
    def sair_programa(self):
        if self.icone_bandeja is not None:
            self.icone_bandeja.stop()
        self.root.destroy() 

    def destruir_popup(self):
        if self.popup is not None:
            try:
                if self.timer_fechar is not None:
                    self.popup.after_cancel(self.timer_fechar)
            except:
                pass

            self.popup.destroy()
            self.popup = None
            self.timer_fechar = None

    def criar_janela_principal(self):

      # =========================
      # CORES
      # =========================

      fundo = "#F4F7FB"
      branco = "#FFFFFF"
      azul = "#1976D2"
      azul_escuro = "#155AA8"
      texto = "#1E293B"
      texto_secundario = "#64748B"
      borda = "#E2E8F0"
      verde = "#16A34A"
      cinza_botao = "#E9EEF5"

      self.root.configure(bg=fundo)

      # =========================
      # ESTILO DA BARRA
      # =========================

      estilo = ttk.Style()

      estilo.configure(
        "Agua.Horizontal.TProgressbar",
        troughcolor="#E8EEF5",
        background=azul,
        thickness=12
      )

      # =========================
      # CONTAINER
      # =========================

      container = tk.Frame(
             self.root,
             bg=fundo
      )

      container.pack(
        fill="both",
        expand=True,
        padx=22,
        pady=18
      )

      # =========================
      # CABEÇALHO
      # =========================

      tk.Label(
        container,
        text="💧 Lembrete de Água",
        font=("Segoe UI", 20, "bold"),
        bg=fundo,
        fg=texto
      ).pack(anchor="w")

      tk.Label(
        container,
        text="Acompanhe sua hidratação ao longo do dia",
        font=("Segoe UI", 9),
        bg=fundo,
        fg=texto_secundario
      ).pack(
        anchor="w",
        pady=(0, 14)
      )

      # =========================
      # CARD PRINCIPAL
      # =========================

      card_agua = tk.Frame(
        container,
        bg=branco,
        highlightbackground=borda,
        highlightthickness=1
      )

      card_agua.pack(
        fill="x",
        pady=(0, 12)
      )

      tk.Label(
        card_agua,
        text="Água hoje",
        font=("Segoe UI", 10),
        bg=branco,
        fg=texto_secundario
      ).pack(
        anchor="w",
        padx=18,
        pady=(14, 0)
      )

      self.label_total = tk.Label(
        card_agua,
        text=f"{self.total_bebido} / {META_DIARIA_ML} ml",
        font=("Segoe UI", 26, "bold"),
        bg=branco,
        fg=azul
      )

      self.label_total.pack(
        anchor="w",
        padx=18,
        pady=(2, 8)
      )

      self.barra_principal = ttk.Progressbar(
        card_agua,
        style="Agua.Horizontal.TProgressbar",
        orient="horizontal",
        mode="determinate",
        maximum=META_DIARIA_ML,
        value=min(self.total_bebido, META_DIARIA_ML)
      )

      self.barra_principal.pack(
        fill="x",
        padx=18
      )

      percentual = min(
        int((self.total_bebido / META_DIARIA_ML) * 100),
        100
      )

      self.label_percentual = tk.Label(
        card_agua,
        text=f"{percentual}% da meta diária",
        font=("Segoe UI", 9, "bold"),
        bg=branco,
        fg=texto_secundario
      )

      self.label_percentual.pack(
        anchor="w",
        padx=18,
        pady=(7, 0)
      )

      faltam = max(
        META_DIARIA_ML - self.total_bebido,
        0
      )

      self.label_faltam = tk.Label(
        card_agua,
        text=f"Faltam {faltam} ml para atingir sua meta",
        font=("Segoe UI", 9),
        bg=branco,
        fg=texto_secundario
      )

      self.label_faltam.pack(
        anchor="w",
        padx=18,
        pady=(1, 14)
      )

      # =========================
      # CARD LEMBRETE
      # =========================

      card_lembrete = tk.Frame(
        container,
        bg=branco,
        highlightbackground=borda,
        highlightthickness=1
      )

      card_lembrete.pack(
        fill="x",
        pady=(0, 12)
      )

      linha_status = tk.Frame(
        card_lembrete,
        bg=branco
      )

      linha_status.pack(
        fill="x",
        padx=18,
        pady=(12, 3)
      )

      tk.Label(
        linha_status,
        text="Próximo lembrete",
        font=("Segoe UI", 9),
        bg=branco,
        fg=texto_secundario
      ).pack(side="left")

      self.label_status = tk.Label(
        linha_status,
        text="● Ativo",
        font=("Segoe UI", 9, "bold"),
        bg=branco,
        fg=verde
      )

      self.label_status.pack(side="right")

      self.label_proximo_aviso = tk.Label(
        card_lembrete,
        text="00:00",
        font=("Segoe UI", 21, "bold"),
        bg=branco,
        fg=texto
      )

      self.label_proximo_aviso.pack(
        anchor="w",
        padx=18,
        pady=(0, 12)
      )

      # =========================
      # INTERVALO
      # =========================

      frame_intervalo = tk.Frame(
        container,
        bg=fundo
      )

      frame_intervalo.pack(
        fill="x",
        pady=(1, 12)
      )

      tk.Label(
        frame_intervalo,
        text="Intervalo dos lembretes",
        font=("Segoe UI", 9, "bold"),
        bg=fundo,
        fg=texto
      ).pack(anchor="w")

      self.opcao_intervalo = tk.StringVar(
        value=self.intervalo_nome
      )

      self.combo_intervalo = ttk.Combobox(
        frame_intervalo,
        textvariable=self.opcao_intervalo,
        state="readonly",
        font=("Segoe UI", 10)
      )

      self.combo_intervalo["values"] = (
        "Teste-10 segundos",
        "30 minutos",
        "45 minutos",
        "60 minutos",
        "90 minutos"
      )

      self.combo_intervalo.pack(
        fill="x",
        pady=(5, 0)
      )

      self.combo_intervalo.bind(
        "<<ComboboxSelected>>",
        self.alterar_intervalo
      )

      # =========================
      # BOTÕES
      # =========================

      botoes = tk.Frame(
        container,
        bg=fundo
      )

      botoes.pack(
        fill="x"
      )

      botoes.columnconfigure(0, weight=1)
      botoes.columnconfigure(1, weight=1)

      botao_adicionar = tk.Button(
        botoes,
        text=f"💧 +{QUANTIDADE_ML} ml",
        font=("Segoe UI", 10, "bold"),
        command=self.bebi_agua,
        bg=azul,
        fg="white",
        activebackground=azul_escuro,
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        height=2
      )

      botao_adicionar.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=(0, 5),
        pady=4
      )

      botao_zerar = tk.Button(
        botoes,
        text="↺ Zerar",
        font=("Segoe UI", 10),
        command=self.zerar_agua,
        bg=cinza_botao,
        fg=texto,
        activebackground="#DDE4EC",
        relief="flat",
        cursor="hand2",
        height=2
      )

      botao_zerar.grid(
        row=0,
        column=1,
        sticky="ew",
        padx=(5, 0),
        pady=4
      )

      self.botao_pausar = tk.Button(
        botoes,
        text="⏸ Pausar",
        font=("Segoe UI", 10),
        command=self.alternar_pausa,
        bg=cinza_botao,
        fg=texto,
        activebackground="#DDE4EC",
        relief="flat",
        cursor="hand2",
        height=2
      )

      self.botao_pausar.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=(0, 5),
        pady=4
      )

      botao_sair = tk.Button(
        botoes,
        text="Sair",
        font=("Segoe UI", 10),
        command=self.sair_programa,
        bg=cinza_botao,
        fg=texto_secundario,
        activebackground="#DDE4EC",
        relief="flat",
        cursor="hand2",
        height=2
      )

      botao_sair.grid(
        row=1,
        column=1,
        sticky="ew",
        padx=(5, 0),
        pady=4
      )
    def alterar_intervalo(self, event=None):
        opcao = self.opcao_intervalo.get()
        if opcao == "Teste-10 segundos":
            self.intervalo_segundos = 10
        elif opcao == "30 minutos":
            self.intervalo_segundos = 30 * 60
        elif opcao == "45 minutos":
            self.intervalo_segundos = 45 * 60
        elif opcao == "60 minutos":
            self.intervalo_segundos = 60 * 60
        elif opcao == "90 minutos":
            self.intervalo_segundos = 90 * 60
        self.salvar_dados()
        self.agendar_aviso()
                    
    def alternar_pausa(self):

       if not self.pausado:

        self.pausado = True

        if self.timer_contagem is not None:
            try:
                self.root.after_cancel(
                    self.timer_contagem
                )
            except:
                pass

            self.timer_contagem = None

        self.label_proximo_aviso.config(
            text="Pausado"
        )

        self.label_status.config(
            text="● Pausado",
            fg="#F59E0B"
        )

        self.botao_pausar.config(
            text="▶ Continuar"
        )

       else:

        self.pausado = False

        self.label_status.config(
            text="● Ativo",
            fg="#16A34A"
        )

        self.botao_pausar.config(
            text="⏸ Pausar"
        )

        self.agendar_aviso()   

    def agendar_aviso(self):
        
        if self.pausado:
            return
        if self.timer_contagem is not None:
            try:
                self.root.after_cancel(self.timer_contagem)
            except:
                pass
            self.timer_contagem = None
        self.segundos_restantes = self.intervalo_segundos
        self.atualizar_contagem()

    def atualizar_contagem(self):
        if self.pausado:
            return
        minutos, segundos = divmod(self.segundos_restantes, 60)
        
        self.label_proximo_aviso.config(
    text=f"{minutos:02d}:{segundos:02d}"
)
        if self.segundos_restantes > 0:
            self.segundos_restantes -= 1
            self.timer_contagem = self.root.after(1000, self.atualizar_contagem)
        else:
            self.timer_contagem = None
            self.mostrar_aviso()
            
    def mostrar_aviso(self):
        """Mostra o aviso na tela."""

        self.popup = tk.Toplevel(self.root)

        # Remove barra normal da janela
        self.popup.overrideredirect(True)

        # Mantém acima das outras janelas
        self.popup.attributes("-topmost", True)

        largura = 340
        altura = 300

        largura_tela = self.popup.winfo_screenwidth()

        # Canto superior direito
        x = largura_tela - largura - 30
        y = 50

        self.popup.geometry(
            f"{largura}x{altura}+{x}+{y}"
        )

        self.popup.configure(bg="#1976D2")

        titulo = tk.Label(
            self.popup,
            text="💧 Hora de beber água!",
            font=("Segoe UI", 16, "bold"),
            bg="#1976D2",
            fg="white"
        )

        titulo.pack(pady=(25, 5))

        mensagem = tk.Label(
            self.popup,
            text=f"Beba aproximadamente {QUANTIDADE_ML} ml de água",
            font=("Segoe UI", 11),
            bg="#1976D2",
            fg="white"
        )

        mensagem.pack()
        
        total=tk.Label(
            self.popup,
            text=f"Hoje: {self.total_bebido}/{META_DIARIA_ML} ml",
            font=("Segoe UI", 10, "bold"),
            bg="#1976D2",
            fg="White"
        )
        
        total.pack(pady=5)
        
        barra=ttk.Progressbar(
            self.popup,
            orient="horizontal",
            length=250,
            mode="determinate",
            maximum=META_DIARIA_ML,
            value=min(self.total_bebido, META_DIARIA_ML)
        )
        barra.pack(pady=5)
        
        botao_bebi=tk.Button(
            self.popup,
            text=f"💧 Bebi {QUANTIDADE_ML} ml",
            font=("Segoe UI",10,"bold"),
            command= self.bebi_agua,
            bg="white",
            fg="#1976D2",
            relief="flat",
            cursor="hand2"
        )
        botao_bebi.pack(pady=8)

        botao_adiar = tk.Button(
            self.popup,
            text="⏰ Adiar lembrete",
            font=("Segoe UI", 10, "bold"),
            command=self.adiar_aviso,
            bg="white",
            fg="#1976D2",
            relief="flat",
            cursor="hand2"
        )
        botao_adiar.pack(pady=4)

        dica = tk.Label(
            self.popup,
            text="Clique para fechar",
            font=("Segoe UI", 9),
            bg="#1976D2",
            fg="white"
        )

        dica.pack(pady=8)

        # Clicar em qualquer parte fecha o aviso
        
        titulo.bind("<Button-1>", self.fechar_aviso)
        mensagem.bind("<Button-1>", self.fechar_aviso)
        dica.bind("<Button-1>", self.fechar_aviso)

        # Fecha sozinho depois de alguns segundos
        self.timer_fechar = self.popup.after(
            DURACAO_AVISO_SEGUNDOS * 1000,
            self.fechar_aviso
        )

    def zerar_agua(self):
        confirmar = messagebox.askyesno(
            "Zerar água",
            "Deseja zerar a quantidade de água bebida hoje?"
        )
        if not confirmar:
                return

        self.total_bebido = 0
        self.salvar_dados()
        self.atualizar_janela_principal()

    def bebi_agua(self):
        self.total_bebido += QUANTIDADE_ML
        
        self.salvar_dados()
        
        self.atualizar_janela_principal()
        
        print(f"Água bebida hoje:{self.total_bebido} ml")
        if self.popup is not None:
           self.fechar_aviso()
        
    def atualizar_janela_principal(self):

       self.label_total.config(
         text=f"{self.total_bebido} / {META_DIARIA_ML} ml"
    )

       self.barra_principal["value"] = min(
         self.total_bebido,
         META_DIARIA_ML
    )

       percentual = min(
         int((self.total_bebido / META_DIARIA_ML) * 100),
         100
    )

       self.label_percentual.config(
         text=f"{percentual}% da meta diária"
    )

       faltam = max(
        META_DIARIA_ML - self.total_bebido,
        0
    )

       if faltam > 0:
        self.label_faltam.config(
            text=f"Faltam {faltam} ml para atingir sua meta",
            fg="#64748B"
        )
       else:
        self.label_faltam.config(
            text="✓ Meta diária atingida!",
            fg="#16A34A"
        )
    def fechar_aviso(self, event=None):
        self.destruir_popup()

        #Começa novamente o intervalo normal
        self.agendar_aviso()

    def adiar_aviso(self):
        self.destruir_popup()

        if self.timer_contagem is not None:
            try:
                self.root.after_cancel(self.timer_contagem)
            except:
                pass
            self.timer_contagem = None

        self.segundos_restantes = ADIAR_AVISO_SEGUNDOS
        self.atualizar_contagem()


# =========================
# INÍCIO DO PROGRAMA
# =========================

root = tk.Tk()

app = LembreteAgua(root)

root.mainloop()