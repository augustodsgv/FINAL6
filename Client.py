from socket import *
import time
import os
import zmq
from threading import Thread
import random
import cv2
import base64
import numpy as np
import subprocess
import re
import tkinter as tk
import sounddevice as sd
import pyaudio
import psutil


#Dicionários para associar contextos e sockets de envio com cada peer
context_text_sender = {}
socket_text_sender = {}
context_video_sender = {}
socket_video_sender = {}
context_audio_sender = {}
socket_audio_sender = {}

#Flag para sincronismo do programa
flag_ready = False

#Variavel para indicar o proprio endereço do processo
MyPort = 0

#Lista de peers online
PeersOnline = []

#socket para receber mensagens de texto
socket_text_receiver = zmq.Context().socket(zmq.SUB)

#Buffer de Envio e recebimento de menssagens para a interface grafica
sendMessageCache = []
recieveMessageCache = []

#PyAudio
audio = pyaudio.PyAudio()


''' Funções relacionadas à interface TK '''
# Função que fica ouvindo por mensagens adicionadas ao cache e coloca na tela
def enviaMensagemLoop():
	global flag_ready
	global MyPort
	global pn
	while(not flag_ready):
		flag_ready
	while True:
		if len(sendMessageCache) > 0:
			mensagem = sendMessageCache.pop(0)
			messages.insert(tk.INSERT, '%s\n' % f'Voce : {mensagem}')      # Envia a mensagem para o próprio terminal
			if(len(mensagem)>0 and mensagem[0]=='/'):
				try: 
					trataComandos(mensagem)	# Caso o trata comandos não achou o comando
				except:
					messages.insert(tk.INSERT, '%s\n' % 'Comando não encontrado')
				
			else:
				print(f'enviando {mensagem}')
				string_to_send = str(MyNick)+': '+mensagem
				for peer in PeersOnline:
					socket_text_sender[peer].send_string(string_to_send)
					print('enviando mensagem')
			input_user.set('')			# Limpando a mensagem após enviá-la

# Função que pega a mensagem da caixa de texto e bota no cache
def enviaMensagem():
	global sendMessageCache
	mensagem = input_field.get()
	sendMessageCache.append(mensagem)
	print(f'mensage {mensagem}')
	input_user.set('')			# Limpando a mensagem após enviá-la

# Função que fica em loop ouvindo no servidor ouvindo por mensagens para botar no cache
def recebeMensagemLoop():
	global recieveMessageCache
	while(True):
		mensagem = socket_text_receiver.recv_string()
		print(f'String recebida : {mensagem}')
		if(mensagem[0]=='/'):
			trataComandos(mensagem)
		else:
			recieveMessageCache.append(mensagem)

# Função que olha o cache de mensagens recebidas e exibe na tela
def recebeMensagem():
	global myPort
	global socket_text_receiver
	while True:
		try:
			string = recieveMessageCache.pop(0)
			if(string[0]=='/'):				# Verifica se é um comando
				trataComandos(string)
			else:
				messages.insert(tk.INSERT, '%s\n' % string)		# Caso não seja, printa a string
		except:
			pass

# Função que faz o loop do tkwindows
def mensageMainLoop(_):
	
	enviaMensagem()
	return "break"

# Função que gera uma porta para o servidor que recebe mensagens
def bindMyPort():
	global MyPort
	global flag_ready
	global socket_text_receiver
	port = 5555
	while(True):
		try:
			socket_text_receiver.bind('tcp://*:'+str(port))
			break
		except:
			port += 1

	try:
		MyIP = get_interface_ip('ham0')
	except:
		MyIP = gethostbyname(gethostname())
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('10.0.0.0', 0))
		print(s.getsockname()[0])
	MyPort = str(MyIP)+':'+str(port)
	
	flag_ready = True
	socket_text_receiver.setsockopt_string(zmq.SUBSCRIBE, '')
		
	return str(MyIP)+':'+str(port)

def get_interface_ip(interface):
    output = subprocess.check_output(['ifconfig', interface]).decode('utf-8')
    ip_match = re.search(r'inet\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', output)
    if ip_match:
        ip = ip_match.group(1)
        return ip

# Função que trata comandos
def trataComandos(string):
	print(string)
	# Comandos de recebimento
	if(string.find('ADDED ') == 1):
		print('foi adicionado')
		recv_add(string)
	elif(string.find('UPDATE ')==1):
		update(string)
	# Comando de envio
	elif(string.find('ADD ')==1):
		send_add(string)
	elif(string.find('EXIT ')==1):
		recv_left(string)
	elif(string.find('LEFT') ==1):
		send_left()
	else:
		raise Exception ('Comando nao existe')

# Função que adiciona o ip da pessoa à sua lista de peers e envia à essa pessoa seus peers
def send_add(string):
	global context_text_sender
	global socket_text_sender
	global context_video_sender
	global socket_video_sender 
	global context_audio_sender
	global socket_audio_sender
	global PeersOnline
	peer = string.split(' ')[1]
	context_text_sender[peer]= zmq.Context()
	socket_text_sender [peer]= context_text_sender[peer].socket(zmq.PUB)
	socket_text_sender[peer].connect('tcp://'+str(peer))
	time.sleep(0.5)
	string_to_send = f'/ADDED {MyPort}'
	update = "/UPDATE "+peer
	for peer2 in PeersOnline:
		socket_text_sender[peer2].send_string(update)
	for peer2 in PeersOnline:
		string_to_send += ' '+str(peer2)
	socket_text_sender[peer].send_string(string_to_send)
	PeersOnline.append(peer)
	context_video_sender[peer]= zmq.Context()
	socket_video_sender [peer]= context_text_sender[peer].socket(zmq.PUB)
	socket_video_sender[peer].connect('tcp://'+peer.split(':')[0]+':'+str(int(peer.split(':')[1])+1000))
	context_audio_sender[peer]= zmq.Context()
	socket_audio_sender [peer]= context_text_sender[peer].socket(zmq.PUB)
	socket_audio_sender[peer].connect('tcp://'+peer.split(':')[0]+':'+str(int(peer.split(':')[1])+2000))
	print ('Novo Peer Online:',peer)

# Função que recebe um adicionar de mensagens
def recv_add(string):
	global context_text_sender
	global socket_text_sender
	global context_video_sender
	global socket_video_sender
	global context_audio_sender
	global socket_audio_sender
	global PeersOnline
	PeersOnline = string.split(' ')[1:]
	for peer in PeersOnline:
		context_text_sender[peer]= zmq.Context()
		socket_text_sender [peer]= context_text_sender[peer].socket(zmq.PUB)
		socket_text_sender[peer].connect('tcp://'+str(peer))
		context_video_sender[peer]= zmq.Context()
		socket_video_sender [peer]= context_text_sender[peer].socket(zmq.PUB)
		socket_video_sender[peer].connect('tcp://'+peer.split(':')[0]+':'+str(int(peer.split(':')[1])+1000))
		context_audio_sender[peer]= zmq.Context()
		socket_audio_sender [peer]= context_text_sender[peer].socket(zmq.PUB)
		socket_audio_sender[peer].connect('tcp://'+peer.split(':')[0]+':'+str(int(peer.split(':')[1])+2000))
		print ('Novo Peer Online:',peer)


#Função para informar peers que você deixou a chamada e encerrar o programa
def send_left():
	global MyPort
	left = "/EXIT "+ MyPort
	for peer in PeersOnline:
		socket_text_sender[peer].send_string(left)
	pid = os.getpid()
	processo_corrente = psutil.Process(pid)
	processo_corrente.terminate()


#Função para receber que um peer deixou a chamada e parar de enviar dados para este
def recv_left(string):
	global flag_ready
	print(string)
	
	global PeersOnline
	global context_text_sender
	global socket_text_sender
	global context_video_sender
	global socket_video_sender
	global context_audio_sender
	global socket_audio_sender
	peer = string.split(' ')[1]
	
	PeersOnline.remove(peer)
	time.sleep(1)
	cv2.waitKey(10)
	cv2.destroyAllWindows()


#Função para atualizar sua lista de peers onlines na chamada quando outra pessoa o está adicionando
def update(string):
	global PeersOnline
	for peer in string.split(' ')[1:]:
		PeersOnline.append(peer)
		context_text_sender[peer]= zmq.Context()
		socket_text_sender [peer]= context_text_sender[peer].socket(zmq.PUB)
		socket_text_sender[peer].connect('tcp://'+str(peer))
		context_video_sender[peer]= zmq.Context()
		socket_video_sender [peer]= context_text_sender[peer].socket(zmq.PUB)
		socket_video_sender[peer].connect('tcp://'+peer.split(':')[0]+':'+str(int(peer.split(':')[1])+1000))
		context_audio_sender[peer]= zmq.Context()
		socket_audio_sender [peer]= context_text_sender[peer].socket(zmq.PUB)
		socket_audio_sender[peer].connect('tcp://'+peer.split(':')[0]+':'+str(int(peer.split(':')[1])+2000))
		print ('Novo Peer Online:',peer)
	PeersOnline = list(set(PeersOnline))


''' Funções de vídeo '''
#Thread para ficar enviando vídeo para os peers na suas portas de video		
def video_sender():
	global flag_ready
	global MyPort
	while(not flag_ready):
		flag_ready
	print('Video Sender Ready')
	camera = cv2.VideoCapture(0)  #inicia a camera
	while(True):
		(grabbed, frame) = camera.read()  
		try:
			frame = cv2.resize(frame, (640, 480))  
		except:
			frame = np.ones((480,640,3))*random.randrange(0,255)
		encoded, buffer = cv2.imencode('.jpg', frame)
		string_img = base64.b64encode(buffer).decode('utf-8')
		string_send = str(MyNick)+'@'+str(MyPort)+' '+string_img # ç é um caractere que não aparece na imagem codificada em string, perfeito para separar o cabeçalho do conteudo
		for peer in PeersOnline:
			socket_video_sender[peer].send_string(string_send)
		time.sleep(0.1)

#Thread para ficar recebendo os videos e exibir em uma janela com o nome de cada peer
def video_receiver():
	global MyPort
	context_video_receiver = zmq.Context()
	socket_video_receiver = context_video_receiver.socket(zmq.SUB)
	port = 6555
	while(True):
		try:
			socket_video_receiver.bind('tcp://*:'+str(port))
			break
		except:
			port += 1
	
	while(not flag_ready):
		flag_ready
	print('Video Receiver Ready')
	socket_video_receiver.setsockopt_string(zmq.SUBSCRIBE, '')
	while(True):
		string = socket_video_receiver.recv_string()
		parts = string.split(' ')
		client_id = parts[0]
		frame = bytes(parts[1],'utf-8')
		img = base64.b64decode(frame)
		npimg = np.frombuffer(img, dtype=np.uint8)
		source = cv2.imdecode(npimg, 1)
		cv2.imshow(client_id, source)
		cv2.waitKey(10)

#Thread para ficar enviando audio para os peers na suas portas de audio
def audio_sender():
	global flag_ready
	global MyPort
	global audio
	while(not flag_ready):
		flag_ready
	print('Audio Sender Ready')
	taxa_amostragem = 44100 # taxa de amostragem (44.1 kHz)
	sd.default.samplerate = taxa_amostragem
	sd.default.channels = 1  # número de canais (mono)
	
	while(True):
		samplerate = 44100  # Taxa de amostragem em Hz
		duration = 0.3  # Tempo de gravação em segundos
		
		stream = audio.open(format=pyaudio.paInt16,
					channels=1,
					rate=samplerate,
					input=True,
					frames_per_buffer=int(samplerate/10))
		frames = []
		start_time = time.time()
		while time.time() - start_time < duration:
			data = stream.read(int(samplerate/10))
			frames.append(data)
		stream.stop_stream()
		stream.close()
		
		audio_bytes = b''.join(frames)
		encoded_audio = base64.b64encode(audio_bytes).decode('utf-8')
		for peer in PeersOnline:
			socket_audio_sender[peer].send_string(encoded_audio)

#Função para reproduzir um audio
def toca_audio(audio_data):
	global audio
	samplerate = 44100  # Taxa de amostragem em Hz
	stream = audio.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=samplerate,
                    output=True)
	stream.write(audio_data.tobytes())
	stream.stop_stream()
	stream.close()

#Thread para ficar recebendo os audios e reproduzi-los	
def audio_receiver():
	global MyPort
	context_audio_receiver = zmq.Context()
	socket_audio_receiver = context_audio_receiver.socket(zmq.SUB)
	port = 7555
	while(True):
		try:
			socket_audio_receiver.bind('tcp://*:'+str(port))
			break
		except:
			port += 1
	
	while(not flag_ready):
		flag_ready
	print('Audio Receiver Ready')
	print('Audio Port ='+str(port))
	socket_audio_receiver.setsockopt_string(zmq.SUBSCRIBE, '')
	while(True):
		encoded_audio = socket_audio_receiver.recv_string()
		decoded_audio = base64.b64decode(encoded_audio)
		audio_data = np.frombuffer(decoded_audio, dtype=np.int16)
		Thread(target=toca_audio,args=(audio_data,)).start()


MyNick = input('Defina seu apelido:')
''' Parâmetros do sistema '''
pid = os.getpid()
print ('PID: '+str(pid))

''' Iniciando rede '''
# Criando nova porta
myPort = bindMyPort()
print (f'minha porta e : {myPort}')
Thread(target=video_sender).start()
Thread(target=video_receiver).start()
Thread(target=audio_sender).start()
Thread(target=audio_receiver).start()
Thread(target=recebeMensagem).start()

''' Iniciando janela '''
''' Variáveis globais da janela do TK '''
window = tk.Tk()		# Criando a janela
messages = tk.Text(window)			# Criando a janela de texto
messages.pack()
input_user = tk.StringVar()			# Não entendi bem o que é ainda
input_field = tk.Entry(window, text = input_user) # Setando a caixa de texto onde se escreve o texto
input_field.pack(side = tk.BOTTOM, fill = tk.X)		# Juntando tudo para criar a janela
window.title(MyNick+'@'+myPort)
frame = tk.Frame(window)  # , width=300, height=300)
input_field.bind("<Return>", mensageMainLoop)
frame.pack()

# Iniciando Threads de envio e recebimento de mensagens

Thread(target=enviaMensagemLoop).start()
Thread(target=recebeMensagemLoop).start()

window.mainloop()
