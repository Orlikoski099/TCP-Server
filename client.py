import tkinter as tk
import threading
import socket
import os
from datetime import datetime
import random

class ClientGUI:
    def __init__(self, master, client_id, port):
        self.master = master
        self.client_id = client_id
        self.client_port = port

        # Configurações do cliente
        self.SERVER_HOST = '127.0.0.1'
        self.SERVER_PORT = 9999
        self.FILE_REQUEST = ''
        self.FILE_NAME = f'arquivo_{client_id}'
        self.client_socket = None
        self.thread_receive = None  # Inicializa como None

        self.frame = tk.Frame(self.master)
        self.frame.pack(pady=10)
        self.setup_gui()

    def setup_gui(self):
        tk.Label(self.frame, text="Nome do arquivo:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_arquivo = tk.Entry(self.frame)
        self.entry_arquivo.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.frame, text="Porta do cliente:").grid(row=0, column=2, padx=5, pady=5)
        self.porta_label = tk.Label(self.frame, text=str(self.client_port))
        self.porta_label.grid(row=0, column=3, padx=5, pady=5)

        self.botao_enviar = tk.Button(self.frame, text=f"Enviar Request Cliente {self.client_id}", command=self.send_request)
        self.botao_enviar.grid(row=0, column=4, padx=5, pady=5)

        self.size_label = tk.Label(self.frame, text="Tamanho da resposta: ")
        self.size_label.grid(row=1, columnspan=5, padx=5, pady=5)

        self.status_label = tk.Label(self.frame, text="Status: ")
        self.status_label.grid(row=2, columnspan=5, padx=5, pady=5)

        self.progress_label = tk.Label(self.frame, text="Progresso: 0%")
        self.progress_label.grid(row=3, columnspan=5, padx=5, pady=5)

        self.reset_button = tk.Button(self.frame, text="Resetar Cliente", command=self.reset_client)
        self.reset_button.grid(row=4, columnspan=5, padx=5, pady=5)

    def send_request(self):
        self.FILE_REQUEST = f'OBTER filesToSend/{self.entry_arquivo.get()}'

        try:
            if self.client_socket is None:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.bind(('', self.client_port))
                self.client_socket.connect((self.SERVER_HOST, self.SERVER_PORT))

            if self.thread_receive is None or not self.thread_receive.is_alive():
                # Inicia a thread de recebimento apenas se não estiver ativa
                self.thread_receive = threading.Thread(target=self.receive_response)
                self.thread_receive.daemon = True
                self.thread_receive.start()

            self.client_socket.send(self.FILE_REQUEST.encode())
            print(f'Requisição enviada para o servidor pelo Cliente {self.client_id}.')
        except ConnectionRefusedError:
            self.status_label.configure(text="Status: Erro - Servidor recusou a conexão ou está desligado")
            print("Erro: Servidor recusou a conexão ou está desligado")
        
    def receive_response(self):
        nome_arquivo = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{self.client_id}_{self.FILE_NAME}"
        extensao = self.FILE_REQUEST.split(".")[-1]
        nome_arquivo = f"{nome_arquivo}.{extensao}"

        if not os.path.exists("filesReceived"):
            os.makedirs("filesReceived")

        caminho_arquivo = f"filesReceived/{nome_arquivo}"
        num_bytes = 0
        tamanho_arquivo = 0

        try:
            pacote_inicial = self.client_socket.recv(8192)
            resposta = pacote_inicial.decode()

            if resposta.startswith("Erro"):
                self.status_label.configure(text=f"Status: {resposta}")
                print(f'Erro recebido do servidor: {resposta}')
                return
            elif resposta.startswith("TAMANHO"):
                tamanho_arquivo = int(resposta.split(" ")[1])
                pacote_inicial = self.client_socket.recv(8192)

            with open(caminho_arquivo, 'wb') as file:
                file.write(pacote_inicial)
                num_bytes += len(pacote_inicial)
                self.update_progress(num_bytes, tamanho_arquivo)

                while True:
                    pacote = self.client_socket.recv(8192)
                    if not pacote:
                        break
                    file.write(pacote)
                    num_bytes += len(pacote)
                    #gambiarra pra atualizar só as vezes o progresso 
                    if num_bytes % 10 == 0:
                        self.update_progress(num_bytes, tamanho_arquivo)

            self.update_progress(num_bytes, tamanho_arquivo)
            self.size_label.configure(text=f"Tamanho da resposta: {num_bytes / 1024:.2f} KB")
            self.status_label.configure(text="Status: Sucesso")
            print(f'Arquivo recebido salvo em: {caminho_arquivo}')

        except Exception as e:
            self.status_label.configure(text=f"Status: Erro - {e}")
            print(f'Erro ao receber o arquivo: {e}')

        finally:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None

    def update_progress(self, bytes_received, total_bytes):
        percentage = (bytes_received / total_bytes) * 100
        self.progress_label.configure(text=f"Progresso: {percentage:.2f}%")

    def reset_client(self):
        self.entry_arquivo.delete(0, tk.END)
        self.size_label.configure(text="Tamanho da resposta: ")
        self.status_label.configure(text="Status: ")
        self.progress_label.configure(text="Progresso: 0%")
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        if self.thread_receive and self.thread_receive.is_alive():
            self.thread_receive.join()  # Espera até que a thread termine

if __name__ == "__main__":
    janela = tk.Tk()
    janela.title("Gerenciador de Clientes")

    clients = [ClientGUI(janela, i, 8000 + i) for i in range(1, 4)]

    janela.mainloop()
