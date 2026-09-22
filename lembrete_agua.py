import tkinter as tk
from tkinter import ttk
import json
import os
import datetime

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
        self.root.geometry("350x300")
        self.root.resizable(False, False)

        # self.root.withdraw()

        self.popup = None
        self.timer_fechar = None
        self.timer_contagem = None
        
        self.segundos_restantes = INTERVALO_SEGUNDOS
        
        self.total_bebido = self.carregar_dados()
        
        self.criar_janela_principal()
        self.root.after(100, self.agendar_aviso)

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

    def salvar_dados(self):
                dados = {
                    "data":str(datetime.date.today()),
                    "total_bebido":self.total_bebido
                }
                
                with open(ARQUIVO_DADOS, "w", encoding="utf-8") as arquivo:
                    json.dump(dados, arquivo, indent=4)
                    
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
            text=f"Próximo aviso: 00: {INTERVALO_SEGUNDOS:02d}",
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
        
        botao_adicionar.pack(pady=5)
        
        botao_sair=tk.Button(
            self.root,
            text="Sair",
            font=("Segoe UI", 10),
            command=self.root.destroy,
            width=18
        )
        
        botao_sair.pack(pady=10)
            
                            
    def agendar_aviso(self):
        #Cancela uma contagem anterior se existir
        if self.timer_fechar is not None:
            try:
                self.root.after_cancel(self.timer_contagem)
            except:
                pass
            
            self.segundos_restantes = INTERVALO_SEGUNDOS
            
            self.atualizar_contagem()

    def atualizar_contagem(self):
        
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