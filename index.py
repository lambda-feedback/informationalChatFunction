from lf_toolkit import create_server, run

from src.module import chat_health_module, chat_module


def main():
    server = create_server()
    server.chat(chat_module)
    server.chat_health(chat_health_module)
    run(server)


if __name__ == "__main__":
    main()
