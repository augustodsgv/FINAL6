# Trabalho 1 de Sistemas Distribuídos
Este é um programa de mensagens e vídeos "intantâneo"\
Desenvolvido na matéria de Sistemas Distribuídos

# Como usar?
## Instalação
### Instalando dependências
* Esteja no diretório do programa
* Execute o comando ```pip install -r requirements.txt```
* Caso haja problema instalando o pyaudio ```sudo apt install portaudio19-dev python3-pyaudio```

### Conectando as Máquinas à rede
* Conecte todas as máquinas num servidor local ou numa VPN como o [Hamachi](https://vpn.net/)

### Pronto
* Agora é só rodar o programa
* Após rodar o programa use ```deactivte``` para sair do envelope

## Iniciando o programa
* Verifique se está na mesma pasta do arquivo
* Rode ```python3 FINAL6.py```
* Aguarde a interface iniciar

## Adicionando pessoas
* Obtenha o IP e porta do processo da outra máquina (aparece no título da janela e no terminal)
* Digite ```/ADD <IP:porta>``` na caixa de texto na parte inferior da interface
* Agora basta apreciar o rostinho lindo de seu amiguinho

## Saindo da chamada
* Basta digitar ```/LEFT``` na caixa de texto na parte inferior da interface
* O programa irá fechar a chamada e finalizará

# Decisões de projeto
* Optamos por deixar uma interface gráfica para evitar que mensagens recebidas afetassem a escrita das mensagens\
e para deixar o uso do programa mais amigável para o usuário
* No projeto foram usados diversos sockets para o envio dos dados afim de evitar congestionamentos\
no socket de envio
* Deixamos o adição de novas pessoas na conversa via interface por meio do comando ```/ADD``` para que se possa\
adicionar pessoas durante a execução do programa\


# Autores
[Augusto dos Santos Gomes Vaz](https://github.com/Augustodsgv)\
[Guilherme José da Silva](https://github.com/GuiJoseh)\
[Pedro Malandrin Klesse](https://github.com/Klesse)\
Yago Davi Pimenta
