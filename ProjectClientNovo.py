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
from multiprocessing.pool import ThreadPool
#import sounddevice as sd


# Redirecionar a saída de erro para o dispositivo nulo
os.environ["PY_SOUNDCARD_ERROR_TARGET"] = "/dev/null"

context_text_sender = {}
socket_text_sender = {}
context_video_sender = {}
socket_video_sender = {}
context_audio_sender = {}
socket_audio_sender = {}
flag_ready = False
MyPort = 0
PeersOnline = []
socket_text_receiver = zmq.Context().socket(zmq.SUB)
sendMessageCache = []
recieveMessageCache = []



''' Funções relacionadas à interface TK '''
# Função que fica ouvindo por mensagens adicionadas ao cache e coloca na tela
def enviaMensagemLoop():
	global flag_ready
	global MyPort
	global pn
	while(not flag_ready):
		flag_ready
	for peer in PeersOnline:
		context_text_sender[peer]= zmq.Context()
		socket_text_sender [peer]= context_text_sender[peer].socket(zmq.PUB)
		socket_text_sender[peer].connect('tcp://'+str(peer))
	while True:
		if len(sendMessageCache) > 0:
			mensagem = sendMessageCache.pop(0)
			messages.insert(tk.INSERT, '%s\n' % f'Voce : {mensagem}')      # Envia a mensagem para o próprio terminal
			if(len(mensagem)>0 and mensagem[0]=='/'):
				try: 
					trataComandos(mensagem)					# Caso o trata comandos não achou o comando
				except:
					messages.insert(tk.INSERT, '%s\n' % 'Comando não encontrado')
				
			else:
				print(f'enviando {mensagem}')
				string_to_send = str(MyPort)+': '+mensagem
				for peer in PeersOnline:
					socket_text_sender[peer].send_string(string_to_send)
					print('enviando mensagem')
			input_user.set('')			# Limpando a mensagem após enviá-la
			pass

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
	global socket_text_receiver
	while(True):
		mensagem = socket_text_receiver.recv_string()
		print(f'String recebida : {mensagem}')
		if(mensagem[0]=='/'):
			trataComandos(mensagem)
		else:
			recieveMessageCache.append(mensagem)

# Função que olha o cache de mensagens recebidas e exibe na tela
def recebeMensagem():
	global recieveMessageCache
	if len(recieveMessageCache) > 0:
		mensagem = recieveMessageCache.pop(0)
		messages.insert(tk.INSERT, '%s\n' % mensagem)		# Caso não seja, printa a string

# Função que faz o loop do tkwindows
def mensageMainLoop(_):
	Thread(target=recebeMensagem).start()
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
	if(string.find('ADDED') == 1):
		print('foi adicionado')
		recv_add(string)
	elif(string.find('UPDATE')==1):
		update(string)
	# Comando de envio
	elif(string.find('ADD')==1):
		send_add(string)
	elif(string.find('LEFT') ==1):
		send_left()
	elif(string.find('LIST_PEERS') == 1):
		show_peers_online()
	#elif(string.find('/AUDIO')==1):
	#	send_audio(string)
	else:
		raise Exception ('Comando nao existe')
	
	#elif(string.find('AUDIO ')==1):
			#	recv_audio(string)

# Função que adiciona o ip da pessoa à sua lista de peers e envia à essa pessoa seus peers
def send_add(string):
	global context_text_sender
	global socket_text_sender
	global context_video_sender
	global socket_video_sender 
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


def send_left(string):
	pass

def recv_left(string):
	pass
	
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

# Função que lista os peers online
def show_peers_online():
	string = f'peers: {PeersOnline}'
	messages.insert(tk.INSERT, '%s\n' % string)
'''	
def send_audio(string):
	global MyPort
	duracao = int(string.split(' ')[1])
	context_audio_sender = {}
	socket_audio_sender = {}
	taxa_amostragem = 44100  # taxa de amostragem (44.1 kHz)
	sd.default.samplerate = taxa_amostragem
	sd.default.channels = 1  # número de canais (mono)
	print('Gravação de audio iniciada')
	gravacao = sd.rec(int(duracao*taxa_amostragem), dtype='float32')
	sd.wait()
	print('Gravação de audio encerrada')
	audio_data = np.asarray(gravacao, dtype=np.float32)
	audio_data /= np.max(np.abs(audio_data))  # Normaliza o áudio para valores entre -1 e 1
	audio_bytes = (audio_data*32767).astype(np.int16).tobytes()
	audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
	string_to_send = '/AUDIO '+MyPort+' '+audio_base64
	for peer in PeersOnline:
		socket_text_sender[peer].send_string(string_to_send)

def recv_audio(string):
	audio_bytes = base64.b64decode(string.split(' ')[2])
	audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)/32767
	sd.play(audio_data, samplerate=44100)
	sd.wait()
'''

''' FUNÇÕES OBSOLETAS '''

def text_sender():
	global flag_ready
	global MyPort
	global pn
	while(not flag_ready):
		flag_ready
	print('Text Sender Ready')
	for peer in PeersOnline:
		context_text_sender[peer]= zmq.Context()
		socket_text_sender [peer]= context_text_sender[peer].socket(zmq.PUB)
		socket_text_sender[peer].connect('tcp://'+str(peer))
	while(True):
		string = input()
		if(len(string)>0 and string[0]=='/'):
			if(string.find('ADD')==1):
				send_add(string)
			elif(string.find('LEFT')==1):
				send_left()
			#elif(string.find('AUDIO')==1):
			#	send_audio(string)
			else:
				print('Comando não reconhecido')
		else:
			string_to_send = str(MyPort)+': '+string
			for peer in PeersOnline:
				socket_text_sender[peer].send_string(string_to_send)

def text_receiver():
	global MyPort
	global flag_ready
	context_text_receiver = zmq.Context()
	socket_text_receiver = context_text_receiver.socket(zmq.SUB)
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
		
	MyPort = str(MyIP)+':'+str(port)#gethostbyname(gethostname())
	print('My Port is: ',MyPort)
	print('Text Receiver Ready')
	#Thread(target=sync).start()
	flag_ready = True
	socket_text_receiver.setsockopt_string(zmq.SUBSCRIBE, '')
	while(True):
		string = socket_text_receiver.recv_string()
		if(string[0]=='/'):
			if(string.find('ADD ')==1):
				recv_add(string)
			elif(string.find('UPDATE ')==1):
				update(string)
			#elif(string.find('AUDIO ')==1):
			#	recv_audio(string)
		else:
			print(string)

''' Funções de vídeo '''		
def video_sender():
	global flag_ready
	global MyPort
	while(not flag_ready):
		flag_ready
	print('Video Sender Ready')
	camera = cv2.VideoCapture(0)  #inicia a camera
	for peer in PeersOnline:
		context_video_sender[peer]= zmq.Context()
		socket_video_sender [peer]= context_video_sender[peer].socket(zmq.PUB)
		socket_video_sender[peer].connect('tcp://'+peer.split(':')[0]+':'+str(int(peer.split(':')[1])+1000))
		socket_video_sender[peer].setsockopt(zmq.IDENTITY, bytes(str(MyPort),'utf-8'))
	while(True):
		(grabbed, frame) = camera.read()  
		try:
			frame = cv2.resize(frame, (640, 480))  
		except:
			frame = np.ones((480,640,3))*random.randrange(0,255)
		encoded, buffer = cv2.imencode('.jpg', frame)
		string_img = base64.b64encode(buffer).decode('utf-8')
		string_send = str(MyPort)+'ç'+string_img # ç é um caractere que não aparece na imagem codificada em string, perfeito para separar o cabeçalho do conteudo
		for peer in PeersOnline:
			socket_video_sender[peer].send_string(string_send)
	
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
		parts = string.split('ç')
		client_id = parts[0]
		frame = bytes(parts[1],'utf-8')
		img = base64.b64decode(frame)
		npimg = np.frombuffer(img, dtype=np.uint8)
		source = cv2.imdecode(npimg, 1)
		cv2.imshow("Transmitido de "+client_id, source)
		cv2.waitKey(10)

'''
def audio_sender():
	global flag_ready
	global MyPort
	while(not flag_ready):
		flag_ready
	print('Audio Sender Ready')
	taxa_amostragem = 3000 # taxa de amostragem (44.1 kHz)
	sd.default.samplerate = taxa_amostragem
	sd.default.channels = 1  # número de canais (mono)
	
	for peer in PeersOnline:
		context_audio_sender[peer]= zmq.Context()
		socket_audio_sender [peer]= context_audio_sender[peer].socket(zmq.PUB)
		socket_audio_sender[peer].connect('tcp://'+peer.split(':')[0]+':'+str(int(peer.split(':')[1])+2000))
		#socket_audio_sender[peer].setsockopt(zmq.IDENTITY, bytes(str(MyPort),'utf-8'))
	
	while(True):
		gravacao = sd.rec(int(2*taxa_amostragem), dtype='float32') 
		sd.wait()
		#encoded, buffer = cv2.imencode('.jpg', frame)
		audio_data = np.asarray(gravacao, dtype=np.float32)
		audio_data /= np.max(np.abs(audio_data))  # Normaliza o áudio para valores entre -1 e 1
		audio_bytes = (audio_data).astype(np.int16).tobytes()
		audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
		#print('Audio String:'+audio_base64)
		#string_send = str(MyPort)+'ç'+string_audio # ç é um caractere que não aparece na imagem codificada em string, perfeito para separar o cabeçalho do conteudo
		for peer in PeersOnline:
			socket_audio_sender[peer].send_string(audio_base64)

def toca_audio(audio):
	sd.play(audio, samplerate=3000)
	sd.wait()
	
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
		string = socket_audio_receiver.recv_string()
		audio_bytes = base64.b64decode(string)
		audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
		Thread(target=toca_audio,args=(audio_data,)).start()
	pass
'''

''' Parâmetros do sistema '''
pid = os.getpid()
print ('PID: '+str(pid))

''' Iniciando rede '''

# Criando nova porta
myPort = bindMyPort()
print (f'minha porta e : {myPort}')
#Thread(target=video_sender).start()
#Thread(target=video_receiver).start()
#Thread(target=audio_sender).start()
#Thread(target=audio_receiver).start()
#text_sender()

''' Iniciando janela '''
''' Variáveis globais da janela do TK '''
window = tk.Tk()		# Criando a janela
messages = tk.Text(window)			# Criando a janela de texto
messages.pack()
input_user = tk.StringVar()			# Não entendi bem o que é ainda
input_field = tk.Entry(window, text = input_user) # Setando a caixa de texto onde se escreve o texto
input_field.pack(side = tk.BOTTOM, fill = tk.X)		# Juntando tudo para criar a janela
window.title(myPort)
frame = tk.Frame(window)  # , width=300, height=300)
input_field.bind("<Return>", mensageMainLoop)
frame.pack()

# Iniciando Threads de envio e recebimento de mensagens

pool = ThreadPool(4)
pool.apply_async(enviaMensagemLoop)
pool.apply_async(recebeMensagemLoop)

window.mainloop()
