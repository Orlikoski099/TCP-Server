import socket
import threading
import os

# Configurações do servidor
HOST = '127.0.0.1'
PORT = 9999
BUFFER_SIZE = 8192

clients = []
lock = threading.Lock()

class OrlikoskiProtocol:
    def __init__(self):
        pass

    def processar_requisicao(self, mensagem):
        if mensagem.startswith("SAIR"):
            return "SAIR"
        elif mensagem.startswith("OBTER "):
            arquivo_requisitado = mensagem.split(" ")[1]
            return f'OBTER {arquivo_requisitado}'

    def enviar_arquivo(self, client_socket, arquivo_requisitado):
        try:
            if os.path.exists(arquivo_requisitado):
                tamanho_arquivo = os.path.getsize(arquivo_requisitado)
                client_socket.send(f"TAMANHO {tamanho_arquivo}".encode())
                
                with open(arquivo_requisitado, 'rb') as file:
                    while True:
                        dados = file.read(BUFFER_SIZE)
                        if not dados:
                            break
                        client_socket.send(dados)
                print(f'Arquivo {arquivo_requisitado} enviado para o cliente.')
            else:
                mensagem_erro = 'Erro: Arquivo não encontrado'
                client_socket.send(mensagem_erro.encode())
                print('Mensagem de erro enviada para o cliente.')
                
        except Exception as e:
            print(f'Erro ao enviar arquivo: {e}')

def handle_client(client_socket):
    protocolo = OrlikoskiProtocol()
    clients.append(client_socket)
    try:
        while True:
            request = client_socket.recv(1024).decode()
            if not request:
                break
            print(f'Requisição recebida: {request}')
            
            resposta = protocolo.processar_requisicao(request)

            if resposta.startswith("SAIR"):
                break
            elif resposta.startswith("OBTER"):
                arquivo_requisitado = resposta.split(" ")[1]
                protocolo.enviar_arquivo(client_socket, arquivo_requisitado)
            else:
                broadcast_message(resposta)

    except ConnectionResetError:
        print(f'Conexão fechada pelo cliente de forma inesperada.')
    except Exception as e:
        print(f'Erro ao processar requisição: {e}')

    finally:
        with lock:
            clients.remove(client_socket)
        client_socket.close()
        print(f'Cliente desconectado.')

def broadcast_message(message):
    print(message, len(clients))

    for client in clients[:]:
        try:
            client.send(message.encode())
        except Exception as e:
            print(e)
            with lock:
                clients.remove(client)

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print('Servidor TCP iniciado.')

    threading.Thread(target=console_input_thread).start()

    while True:
        client_socket, addr = server_socket.accept()
        print(f'Conexão aceita de {addr}')
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

def console_input_thread():
    while True:
        command = input()

        if command.startswith("SAIR"):
            try:
                if command == "SAIR":
                    # Desconectar todos os clientes
                    with lock:
                        for client in clients:
                            client.send("SAIR".encode())
                            client.close()
                        clients.clear()
                        print("Todos os clientes desconectados.")
                elif command.startswith("SAIR "):
                    # Desconectar cliente específico pelo índice
                    index = int(command.split()[1])
                    if 0 <= index < len(clients):
                        client = clients[index]
                        with lock:
                            clients.remove(client)
                            client.send("SAIR".encode())
                            client.close()
                            print(f"Cliente {index} desconectado.")
                    else:
                        print("Índice inválido.")
                else:
                    print("Comando inválido.")
            except ValueError:
                print("Comando inválido.")
        else:
            broadcast_message("CHAT " + command)

if __name__ == "__main__":
    main()
