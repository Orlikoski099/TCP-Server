import socket
import threading
import os

# Configurações do servidor
HOST = '127.0.0.1'  # Endereço IP do servidor
PORT = 9999         # Porta para comunicação (maior que 1024)
BUFFER_SIZE = 1024  # Tamanho do buffer para leitura do arquivo

class OrlikoskiProtocol:
    def __init__(self):
        pass

    def processar_requisicao(self, mensagem):
        """Processa a requisição do cliente."""
        if not mensagem.startswith("OBTER "):
            return "Erro: Formato de requisição inválido."
        return mensagem.split(" ")[1]

    def processar_resposta_arquivo(self, dados_arquivo):
        """Processa a resposta do arquivo."""
        if not dados_arquivo:
            return "Erro: Dados do arquivo não recebidos."
        return dados_arquivo

    def processar_confirmacao(self, mensagem):
        """Processa a confirmação de recebimento."""
        return mensagem

    def processar_erro(self, mensagem):
        """Processa mensagens de erro."""
        return mensagem

def handle_client(client_socket):
    """Lida com a requisição do cliente em uma thread separada."""
    protocolo = OrlikoskiProtocol()
    try:
        request = client_socket.recv(1024).decode()
        print(f'Requisição recebida: {request}')
        
        arquivo_requisitado = protocolo.processar_requisicao(request)
        
        if arquivo_requisitado.startswith("Erro"):
            client_socket.send(arquivo_requisitado.encode())
            print('Mensagem de erro enviada para o cliente.')
        else:
            if os.path.exists(arquivo_requisitado):
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
        print(f'Erro ao processar requisição: {e}')
    finally:
        client_socket.close()

def main():
    """Inicializa o servidor TCP."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print('Servidor TCP iniciado.')

    while True:
        client_socket, addr = server_socket.accept()
        print(f'Conexão aceita de {addr}')
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()