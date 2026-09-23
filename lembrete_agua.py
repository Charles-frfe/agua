import tkinter as tk
from tkinter import ttk
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
DURACAO_AVISO_SEGUNDOS = 120
QUANTIDADE_ML = 200
META_DIARIA_ML=2000
ARQUIVO_DADOS= os.path.join(
    os.path.dirname(os.path.abspath(__file__))
    , "agua_dados.json")


class LembreteAgua:

    def __init__(self, root):
        self.root = root
        
        self.root.title("Lembrete de Água")
        self.root.geometry("450x450")
        self.root.resizable(False, False)

        # self.root.withdraw()

        self.popup = None
        self.timer_fechar = None
        self.timer_contagem = None
        self.pausado = False
        self.fila_acoes = queue.Queue()
        self.icone_bandeja = None
        
        self.total_bebido = self.carregar_dados()
        
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
                    
    def ocultar_janela(self):
        self.root.withdraw()
        
    def abrir_janela(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    def solicitar_beber (self, icon=None, item=None):
        self.fila_acoes.put(("beber",None))
        
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
        desenho.ellipse((18, 24, 46, 52), fill="#1976D2", outline="black")
        
        desenho.polygon([(32, 8), (18, 34), (46, 34)], fill="#1976D2", outline="black")
        
        menu_intervalo = pystray.Menu(
            pystray.MenuItem(
                "Intervalo: Teste-10 segundos",
                lambda icon, item: self.solicitar_intervalo("Teste-10 segundos")
            ),
            
            pystray.MenuItem(
                "30 minutos",
                lambda icon, item: self.solicitar_intervalo("30 minutos")
            ),
            pystray.MenuItem(
                "45 minutos",
                lambda icon, item: self.solicitar_intervalo("45 minutos")
            ),
            pystray.MenuItem(
                "60 minutos",
                lambda icon, item: self.solicitar_intervalo("60 minutos")
            ),
            
            pystray.MenuItem(
                "90 minutos",
                lambda icon, item: self.solicitar_intervalo("90 minutos")
            ),
            
            menu=pystray.Menu(
                
                pystray.MenuItem(
                    f"💧 Bebi {QUANTIDADE_ML} ml",
                    self.solicitar_beber
                ),
                pystray.MenuItem(
                    "⏸️ Pausar/Continuar lembretes",
                    self.solicitar_pausa
                ),
                pystray.MenuItem(
                    "Abrir janela",
                    self.solicitar_abrir
                ),
                pystray.MenuItem(
                    "Sair",
                    self.solicitar_sair
                )
            )
        )
        self.icone_bandeja = pystray.Icon(
            "Lembrete de Água",
            imagem,
            "Lembrete de Água",
            menu_intervalo
        )
        self.icone_bandeja.run_detached()
        
    def sair_programa(self):
        if self.icone_bandeja is not None:
            self.icone_bandeja.stop()
        self.root.destroy() 
           
    def criar_janela_principal(self):
        
        titulo = tk.Label(
            self.root,
            text="💧 Água hoje",
            font=("Segoe UI", 20, "bold"))
        titulo.pack(pady=(25, 10))
         
        self.label_total = tk.Label(
             self.root,
                text=f"{self.total_bebido}/{META_DIARIA_ML} ml",
                font=("Segoe UI", 16,)   
            )
        self.label_total.pack(pady=5)
        
        self.barra_principal=ttk.Progressbar(
            self.root,
            orient="horizontal",
            length=280,
            mode="determinate",
            maximum=META_DIARIA_ML,
            value=min(self.total_bebido, META_DIARIA_ML)
        )
        
        self.barra_principal.pack(pady=15)
        
        self.label_proximo_aviso = tk.Label(
            self.root,
            text=f"Próximo aviso:00:{INTERVALO_SEGUNDOS:02d}",
            font=("Segoe UI", 12)
        )
        
        self.label_proximo_aviso.pack(pady=5)

        botao_adicionar=tk.Button(
            self.root,
            text=f"💧 + {QUANTIDADE_ML} ml",
            font=("Segoe UI", 11, "bold"),
            command=self.bebi_agua,
            width=18
        )
        
        label_intervalo = tk.Label(
            self.root,
            text="Intervalo dos lembretes:",
            font=("Segoe UI", 10)
        )
        label_intervalo.pack(pady=(5, 2))
        
        self.opcao_intervalo = tk.StringVar(value=self.intervalo_nome)
        
        self.combo_intervalo = ttk.Combobox(
            self.root,
            textvariable=self.opcao_intervalo,
            state="readonly",
            width=20
        )
        self.combo_intervalo["values"] =(
                "Teste-10 segundos",
                "30 minutos",
                "45 minutos",
                "60 minutos",
                "90 minutos",
            )
        self.combo_intervalo.pack(pady=5)
        
        self.combo_intervalo.bind("<<ComboboxSelected>>", self.alterar_intervalo)
        
        self.botao_pausar=tk.Button(
            self.root,
            text="Pausar lembretes",
            font=("Segoe UI", 10,),
            command=self.alternar_pausa,
            width=18
        )
        self.botao_pausar.pack(pady=5)
        
        botao_adicionar.pack(pady=5)
        
        botao_sair=tk.Button(
            self.root,
            text="Sair",
            font=("Segoe UI", 10),
            command=self.sair_programa,
            width=18
        )
        
        botao_sair.pack(pady=10)
            
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
            #Pausar
            self.pausado = True
            
            if self.timer_contagem is not None:
                try:
                    self.root.after_cancel(self.timer_contagem)
                except:
                    pass
                
                self.timer_contagem = None
                self.label_proximo_aviso.config(
                    text="Lembretes pausados"
                )
                self.botao_pausar.config(text="Continuar lembretes")
        else:
            #Continuar
            self.pausado = False
            
            self.botao_pausar.config(text="Pausar lembretes")
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
            text=f"Próximo aviso: {minutos:02d}:{segundos:02d}"
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
        altura = 260

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

    def bebi_agua(self):
        self.total_bebido += QUANTIDADE_ML
        
        self.salvar_dados()
        
        self.atualizar_janela_principal()
        
        print(f"Água bebida hoje:{self.total_bebido} ml")
        if self.popup is not None:
           self.fechar_aviso()
        
    def atualizar_janela_principal(self):
        
        self.label_total.config(
            text=f"{self.total_bebido}/{META_DIARIA_ML} ml"
        )
        
        self.barra_principal.config(
            value=min(self.total_bebido, META_DIARIA_ML)
        )
        
        self.barra_principal["value"] = min(self.total_bebido, META_DIARIA_ML)
         
    def fechar_aviso(self, event=None):
        """Fecha o aviso e inicia uma nova contagem."""

        if self.popup is not None:

            try:
                if self.timer_fechar is not None:
                    self.popup.after_cancel(self.timer_fechar)
            except:
                pass

            self.popup.destroy()
            self.popup = None
            self.timer_fechar = None

        # Começa a contar novamente
            self.agendar_aviso()


# =========================
# INÍCIO DO PROGRAMA
# =========================

root = tk.Tk()

app = LembreteAgua(root)

root.mainloop()