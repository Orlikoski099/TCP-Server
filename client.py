import tkinter as tk
import threading
import socket
import os
from datetime import datetime

class ClientGUI:
    def __init__(self, master, client_id):
        self.master = master
        self.client_id = client_id

        # Configurações do cliente
        self.SERVER_HOST = '127.0.0.1'
        self.SERVER_PORT = 9999
        self.FILE_REQUEST = ''
        self.FILE_NAME = f'arquivo_{client_id}'
        self.client_socket = None

        # Configuração da interface gráfica
        self.setup_gui()

        # Iniciar thread para receber respostas do servidor
        self.thread_receive = threading.Thread(target=self.receive_response)
        self.thread_receive.daemon = True

    def setup_gui(self):
        """Configura a interface gráfica do cliente."""
        self.entry_arquivo = tk.Entry(self.master)
        self.entry_arquivo.pack()

        self.botao_enviar = tk.Button(self.master, text=f"Enviar Request Cliente {self.client_id}", command=self.send_request)
        self.botao_enviar.pack()

        self.status_label = tk.Label(self.master, text=f"Status Cliente {self.client_id}:")
        self.status_label.pack()

    def send_request(self):
        """Envia a requisição do arquivo ao servidor."""
        self.FILE_REQUEST = f'OBTER filesToSend/{self.entry_arquivo.get()}'
        if self.client_socket is None:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.SERVER_HOST, self.SERVER_PORT))
        self.client_socket.send(self.FILE_REQUEST.encode())
        print(f'Requisição enviada para o servidor pelo Cliente {self.client_id}.')
        
        if not self.thread_receive.is_alive():
            self.thread_receive.start()

    def receive_response(self):
        """Recebe a resposta do servidor e salva o arquivo."""
        nome_arquivo = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{self.client_id}_{self.FILE_NAME}"
        extensao = self.FILE_REQUEST.split(".")[-1]
        nome_arquivo = f"{nome_arquivo}.{extensao}"

        if not os.path.exists("filesReceived"):
            os.makedirs("filesReceived")

        caminho_arquivo = f"filesReceived/{nome_arquivo}"
        num_bytes = 0

        with open(caminho_arquivo, 'wb') as file:
            while True:
                pacote = self.client_socket.recv(1024)
                if not pacote:
                    break
                file.write(pacote)
                num_bytes += len(pacote)

        self.status_label.configure(text=f"Status Cliente {self.client_id}: Recebidos {num_bytes / 1024:.2f} Kbytes.")
        print(f'Arquivo recebido salvo em: {caminho_arquivo}')

        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None

if __name__ == "__main__":
    janela = tk.Tk()
    janela.title("Gerenciador de Clientes")

    # Criar três instâncias de ClientGUI como exemplo
    clients = [ClientGUI(janela, i) for i in range(1, 4)]

    # Iniciando o loop principal da interface gráfica
    janela.mainloop()
