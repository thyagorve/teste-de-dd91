import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import init, Fore, Style
import requests
import time

init(autoreset=True)

print_lock = threading.Lock()
positive_proxies = []

def check_proxy(proxy_host, cloudfront_request):
    try:
        # Estabelecer conexão com o proxy HTTP
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.settimeout(0.5)  # Limite de tempo de 0.5 segundo
        proxy_socket.connect((proxy_host, 80))  # Tentar conectar ao proxy

        # Enviar a requisição GET com o valor de CLOUDFRONT
        proxy_socket.send(cloudfront_request.encode())

        # Receber a resposta do proxy
        response = proxy_socket.recv(4096)

        # Coletar o número do status HTTP
        status_code = response.split(b' ')[1]

        # Definir a cor e a mensagem de acordo com o status_code
        if status_code == b'200':
            color = Fore.YELLOW
            message = "Passou perto"
        elif status_code in [b'101', b'403']:
            color = Fore.GREEN
            message = "ONLINE"
            positive_proxies.append(proxy_host)
        else:
            color = Fore.RED
            message = "OFFLINE"

        # Bloquear o acesso ao print para garantir a exibição correta
        with print_lock:
            # Exibir a execução do proxy com a cor e mensagem adequadas
            print(f"{color}- {message} Status: {status_code.decode()} --> {proxy_host} ")

        # Fechar a conexão com o proxy
        proxy_socket.close()

    except Exception as e:
        # Bloquear o acesso ao print para garantir a exibição correta
        with print_lock:
            # Exibir a execução do proxy com cor vermelha (erro)
            print(f"{Fore.RED}- OFFLINE {proxy_host}")

def send_telegram_message(message, chat_id, bot_token):
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(telegram_url, json=payload)
    if response.status_code != 200:
        print(f"Erro ao enviar mensagem para o Telegram. Status code: {response.status_code}")
    else:
        print("Mensagem enviada para o Telegram.")

def main():
    print(f"{Fore.GREEN}{Style.BRIGHT}Pressione Enter quando estiver no dados movel...{Style.RESET_ALL}")
    input("")
    cloudfront_host = "d1rsm6mlg3ld3j.cloudfront.net"

    # Ler hosts a partir do arquivo hosts.txt
    with open("hosts.txt", "r") as file:
        hosts = file.read().splitlines()

    # Requisição a ser enviada ao CloudFront
    cloudfront_request = f"GET / HTTP/1.1\r\nHost: {cloudfront_host}\r\nConnection: Upgrade\r\nUpgrade: Websocket\r\n\r\n"

    # Exemplo de uso com ThreadPoolExecutor
    start_time = time.time()
    with ThreadPoolExecutor() as executor:
        futures = []
        
        for proxy_host in hosts:
            futures.append(executor.submit(check_proxy, proxy_host, cloudfront_request))

        # Aguardar a conclusão das tarefas
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print("Erro durante a execução do teste")

    execution_time = time.time() - start_time
    print("Tempo:", execution_time)

    # Exibir a lista de proxies positivos
    print("Proxies positivos:")
    for proxy in positive_proxies:
        print(proxy)

    # Solicitar confirmação do usuário antes de enviar os resultados para o Telegram
    input("Pressione Enter para enviar os resultados para o Telegram...")
    
    # Enviar os resultados para o Telegram
    bot_token = "1103334762:AAEvhYWE48KqL9uwCbB_KM-Zzk6R-IG3P40"
    chat_id = "505357397"
    message = "Proxies positivos:\n" + "\n".join(positive_proxies)
    send_telegram_message(message, chat_id, bot_token)

if __name__ == '__main__':
    main()
