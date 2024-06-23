import tkinter as tk
import threading
import socket
import os
from datetime import datetime

class ClientGUI:
    def __init__(self, master, client_id, port):
        self.master = master
        self.client_id = client_id
        self.client_port = port

        self.SERVER_HOST = '127.0.0.1'
        self.SERVER_PORT = 9999
        self.FILE_REQUEST = ''
        self.FILE_NAME = f'arquivo_{client_id}'
        self.client_socket = None
        self.thread_receive = None
        self.running = False

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

        self.connect_button = tk.Button(self.frame, text="Conectar ao Servidor", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=4, padx=5, pady=5)

        self.botao_enviar = tk.Button(self.frame, text=f"Enviar Request Cliente {self.client_id}", command=self.send_request, state=tk.DISABLED)
        self.botao_enviar.grid(row=1, column=4, padx=5, pady=5)

        self.size_label = tk.Label(self.frame, text="Tamanho da resposta: ")
        self.size_label.grid(row=2, columnspan=5, padx=5, pady=5)

        self.status_label = tk.Label(self.frame, text="Status: ")
        self.status_label.grid(row=3, columnspan=5, padx=5, pady=5)

        self.progress_label = tk.Label(self.frame, text="Progresso: 0%")
        self.progress_label.grid(row=4, columnspan=5, padx=5, pady=5)

        self.chat_label = tk.Label(self.frame, text="Mensagens do servidor:")
        self.chat_label.grid(row=5, columnspan=5, padx=5, pady=5)

        self.chat_text = tk.Text(self.frame, height=10, width=50)
        self.chat_text.grid(row=0, column=5, rowspan=6, padx=5, pady=5, sticky='ns')

    def toggle_connection(self):
        if self.client_socket:
            self.reset_client()
            self.botao_enviar.config(state=tk.DISABLED)
        else:
            self.connect_to_server()

    def connect_to_server(self):
        try:
            if self.client_socket is None:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.bind(('', self.client_port))
                self.client_socket.connect((self.SERVER_HOST, self.SERVER_PORT))
                self.running = True

            if self.thread_receive is None or not self.thread_receive.is_alive():
                self.thread_receive = threading.Thread(target=self.receive_response)
                self.thread_receive.daemon = True
                self.thread_receive.start()

            self.status_label.configure(text="Status: Conectado ao servidor")
            self.connect_button.configure(text="Desconectar do Servidor")
            print(f'Cliente {self.client_id} conectado ao servidor.')
            self.botao_enviar.config(state=tk.NORMAL)

        except ConnectionRefusedError:
            self.status_label.configure(text="Status: Erro - Servidor recusou a conexão ou está desligado")
            print("Erro: Servidor recusou a conexão ou está desligado")

    def send_request(self):
        self.FILE_REQUEST = f'OBTER filesToSend/{self.entry_arquivo.get()}'
        try:
            if self.client_socket:
                self.client_socket.send(self.FILE_REQUEST.encode())
                print(f'Requisição enviada para o servidor pelo Cliente {self.client_id}.')
        except Exception as e:
            self.status_label.configure(text=f"Status: Erro ao enviar requisição - {e}")
            print(f'Erro ao enviar requisição: {e}')

    def receive_response(self):
        extensao = self.entry_arquivo.get().split(".")[-1] if "." in self.entry_arquivo.get() else "bin"
        nome_arquivo = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{self.client_id}_{self.FILE_NAME}.{extensao}"

        if not os.path.exists("filesReceived"):
            os.makedirs("filesReceived")

        caminho_arquivo = f"filesReceived/{nome_arquivo}"
        num_bytes = 0
        tamanho_arquivo = 0

        try:
            while self.running:
                pacote_inicial = self.client_socket.recv(8192)
                if not pacote_inicial:
                    break
                resposta = pacote_inicial.decode(errors='ignore')

                if resposta.startswith("SAIR"):
                    self.reset_client()
                    break
                elif resposta.startswith("TAMANHO"):
                    tamanho_arquivo = int(resposta.split(" ")[1])
                    continue  # Continue recebendo os dados do arquivo
                elif resposta.startswith("CHAT"):
                    self.chat_text.insert(tk.END, f'{resposta.replace("CHAT ", "Aviso do servidor: ")}\n')
                    continue  # Continue recebendo mensagens de chat
                else:
                    # Primeiro pacote não deve conter "TAMANHO", então reabra o arquivo para escrita
                    with open(caminho_arquivo, 'ab') as file:
                        file.write(pacote_inicial)
                        num_bytes += len(pacote_inicial)
                        self.update_progress(num_bytes, tamanho_arquivo)

                        while num_bytes < tamanho_arquivo:
                            pacote = self.client_socket.recv(8192)
                            if not pacote:
                                break
                            file.write(pacote)
                            num_bytes += len(pacote)
                            self.update_progress(num_bytes, tamanho_arquivo)

            self.update_progress(num_bytes, tamanho_arquivo)
            self.size_label.configure(text=f"Tamanho da resposta: {num_bytes / 1024:.2f} KB")
            self.status_label.configure(text="Status: Sucesso")
            print(f'Arquivo recebido salvo em: {caminho_arquivo}')

        except Exception as e:
            if self.running:
                self.status_label.configure(text=f"Status: Erro - {e}")
                print(f'Erro ao receber o arquivo: {e}')

        finally:
            self.reset_client()

    def get_file_extension(self, file_name):
        _, ext = os.path.splitext(file_name)
        return ext[1:] if ext else "bin"

    def update_progress(self, bytes_received, total_bytes):
        percentage = (bytes_received / total_bytes) * 100
        self.progress_label.configure(text=f"Progresso: {percentage:.2f}%")

    def reset_client(self):
        self.botao_enviar.config(state=tk.DISABLED)
        self.size_label.configure(text="Tamanho da resposta: ")
        self.status_label.configure(text="Status: ")
        self.progress_label.configure(text="Progresso: 0%")
        self.chat_text.delete(1.0, tk.END)
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        self.running = False
        self.connect_button.configure(text="Conectar ao Servidor")

if __name__ == "__main__":
    janela = tk.Tk()
    janela.title("Gerenciador de Clientes")

    clients = [ClientGUI(janela, i, 7000 + i) for i in range(1, 4)]

    janela.mainloop()
