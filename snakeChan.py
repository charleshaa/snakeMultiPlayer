#SnakeChan
import socket
import select
from struct import *
from random import randint

class SnakeChan:

	def __init__(self, ip = 0, port=0, Pnum=0):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.connections = []
		self.Pnum = 19
		self.port = port
		self.ip = ip
		if self.port != 0 and self.ip !=0:
			self.socket.bind((ip, port))

	#############################
	#Retourne l'index du client dans clients[] en fonction de son tuple addresse (-1 si non trouve)
	#############################
	def clientsIndex(self, addr):
		for index, dataConnection in enumerate(self.connections):
			if dataConnection.addr == addr:
				return index
		return -1

	#############################
	#send permet d'envoyer des data a l'addresse voulu (le port est determine automatiquement)
	#############################
	def sendto(self, data, addr):
		com = self.connections[self.clientsIndex(addr)]
		if (com.etat == 2):
			self.socket.sendto(pack('I', com.req) + data, com.addr)
			com.req += 1
		else:
			self.socket.sendto(pack('I', 0xFFFFFFFF) + data, com.addr)

	#############################
	#Receive est bloquant, elle prend un parametre qui permet de definir un timeout
	#############################
	def receive(self, time=0):
		readable, writable, exceptional = select.select([self.socket], [], [], time)#Bloquant X(time) seconde ou jusqu'a ce que le socket ai recu des data
		for s in readable:
			data, addr = self.socket.recvfrom(1024) #On recupere les data

			if self.clientsIndex(addr)<0:
				self.connections.append(dataConnection(addr, 0))

			com = self.connections[self.clientsIndex(addr)]
			bytes = unpack('I', data[0:4])
			bytes = bytes[0]
			data = data[4:]
			if com.etat==2 and bytes != 0xFFFFFFFF:
				if bytes > com.ind:
					com.ind += 1
					if data == "ping":
						self.sendto("ok", com.addr)
						return data
					else:
						return (data, com.addr)
			else:
				if bytes == 0xFFFFFFFF:
					if com.type == 0:#Si type = client, on communique avec un client, on va prendre le role de serveur pour accepter la connection
						if self.acceptConnection(com, data) == 1:
							print "Connection made"
							return data, com.addr
					else:
						return data
		return None, None

	##############
	#Machine d'etat permetant d'accepter une connection
	##############
	def acceptConnection(self, com, data):
		if com.etat == 0:
			data = data.split(" ") #On split les data
			if data[0] == "GetToken" and data[2] == "Snake":#On verifie la logique protocolaire
				com.tokenA = data[1]
				com.etat=1
				com.tokenB = randint(0, 0xFFFFFFFF)#On genere un token B
				self.sendto("Token " + str(com.tokenB)+" "+str(com.tokenA)+" "+str(self.Pnum), com.addr)#On envoi ce token
				return 0
		elif com.etat == 1:
			data = data.split(" ") #On split les data
			if data[0] == "Connect":
				data = data[1].split("\\")#Formate les data
				del data[0]#idem
				if data[1] == str(com.tokenB) and data[3] == str(self.Pnum):#Si la reponse correspond a la logique protocolaire...
					self.sendto("Connected " + str(com.tokenB) + " as " + data[5] + " " + data[7], com.addr)#Envoi la confirmation de connection au client
					com.etat = 2#Passe l'etat du client a connecte
					com.compteur = 0
					return 1
			else:
				if com.compteur >2:
					com.etat = 0#Si le message n'est pas ce qu'on attend, le client regresse dans la machine d'etat
					com.compteur = 0
					return 0
				else:
					com.compteur += 1
		elif com.etat == 2:
			if com.compteur > 2:
				com.etat = 0
				return 0
			else:
				com.compteur += 1
		return 0

	##############
	#Machine d'etat permetant de se connecter
	##############
	def connect(self, addr, color="yellow", username="michel"):
		self.connections.append(dataConnection(addr, 1))
		com = self.connections[self.clientsIndex(addr)]
		while com.etat !=2:
			while com.etat==0:#Temps qu'on a pas de reponse satisfesante du serveur, on renverra le message
				com.tokenA = randint(0,0xFFFFFFFF) #Generation du premier token
				self.sendto("GetToken " + str(com.tokenA) + " Snake", com.addr)#Envoi le premier token
				data = self.receive(1)
				if data != None:
					data = data.split(" ", 4) #On split les data
					if data[2] == str(com.tokenA): #On verifie que la logique protocolaire ai ete respecte
						com.tokenB = data[1] #On recupere le token B
						com.Pnum = data[3] #On recupere le Pnum
						com.etat = 1 #On va pouvoir avancer
						self.sendto("Connect " + ("\\challenge\\"+ com.tokenB + "\\protocol\\" + com.Pnum + "\\color\\" + color + "\\nickname\\" + username), com.addr) #Envoi la reponse du challenge
			while com.etat == 1: #Temps qu'on a pas de reponse satisfesante du serveur, on revoi le message
				data = self.receive(1)
				#print data
				if data != None:
					data = data.split(" ", 2)#On split les data
					if data[0] == "Connected" and data[1] == str(com.tokenB):#On verifie que la logique protocolaire ai ete respecte
				   		com.etat = 2#On va pouvoir avancer
				   		com.compteur = 0
				   		continue
				if com.compteur>3:
					com.compteur = 0
					com.etat = 0
					break
				else:
					com.compteur += 1

class dataConnection: #Contient les donnes pour chaque client
	def __init__(self, addr, type):
		self.addr = addr
		self.etat = 0
		self.tokenA = None
		self.tokenB = None
		self.Pnum = None
		self.compteur = 0
		self.req = 1
		self.ind = 0
		self.type = type #type 0 = client, type 1 = serveur
