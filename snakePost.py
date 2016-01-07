import socket
import Queue
import random
import pygame
from pygame.locals import *
from Color import color
from struct import *
from snakeChan import SnakeChan

#commDict = {addr, ListDeData}
#ackDict = {addr, ListDeAck}

class SnakePost:

	def __init__(self, canalTransmission, ident):
		pygame.init()
		pygame.time.set_timer(USEREVENT+1, 30) #L'evennement userevent+1 occure toutes les 30ms
		self.canalTransmission = canalTransmission
		self.commDict = {} #Contien les donnees en attente d'envoi securise.
		self.pendingAck = (None, None)
		self.id = ident
		print color.GREEN + "snakePost instanciated." + color.END

	def send(self, data, addr, seq=0):
		ack=0
		if self.pendingAck[0] == addr:#Si un ack est en attente pour cette addr
			ack = self.pendingAck[1] #On va pouvoir ajouter ce ack au message
			self.pendingAck = (None, None) #Est effacer ce ack en attente.

		#!!!HOT FIX!!! IL ARRIVE DE RENTRER DANS SEND SANS DATA/ADDR VALABLE. CECI PERMET DE BYPASSER CELA, MAIS CA RESTE ANNORMAL
		#JE PENSE QUE SA DOIT VENIR DE SENDaLLsECUREqUEUED. LA LISTE D'ATTENTE PEUT ETRE NON VIDE MAIS CONTENIR DES ELEMENT VIDES. [(NONE, NONE, NONE)]#
		if addr != None:
			self.canalTransmission.sendto( pack( 'I', ((ack<<16)|seq) ) + data, addr )

	def sendSecure(self, data, addr):#N'envoi pas, va simplement mettre en attente le message.
		seq = random.randint(1, 0xFFFF)
		dataToSendToAddr = self.commDict.get(addr) #Recupere la liste d'attente pour l'addr donnee
		if dataToSendToAddr:
			if len(dataToSendToAddr)>=64: #Si il y a plus de 63 messages en attente de securisation
				return 1 #Il faudra reessayer plus tard
			else:
				dataToSendToAddr.append((data, seq))#On ajoute les data en liste d'attente
				return 0
		else:
			self.commDict[addr] = [(data, seq)] #On ajoute les data en liste d'attente
			return 0

	def sendAllSecureQueued(self):
		for addr, dataToSendToAddr in self.commDict.iteritems(): #Recupere une liste d'attente
			if dataToSendToAddr: #Si elle est pleine
				data = dataToSendToAddr[0]
				self.send(data[0], addr, data[1]) #Envoi le premier message

	def listen(self):
		data = None
		addr = None
		bup = None
		##TOUTES LES 30[ms] ON ENVOI LES MESSAGES SECURISE##
		for event in pygame.event.get():
			if event.type == USEREVENT+1:
				self.sendAllSecureQueued() #calling the function wheever we get timer event.

		if self.pendingAck[1] != None: #Si on a encore un ack a faire, on le fait
			self.send("", self.pendingAck[0])

		data, addr = self.canalTransmission.receive( 0 ) #non bloquant
		if data == "": ####!!!! We have to check if snakChan return None or "" if non data is received
				data = None
		if(data != None):
			##ON PREPARE AU TRAITEMENT LES DONNEES RECU##
			#print data
			bytes = unpack( 'I', data[0:4] )
			bytes = bytes[0]
			bup = data
			data = data[4:]
			if data == "": ####!!!! We have to check if snakChan return None or "" if non data is received
				data = None
			bytesT = bytes
			ack = ( (bytes&0xFFFF0000) >> 16 ) #Numero d'ack qui confirme un envoi securise
			seq = bytesT&0x0000FFFF #Numero de sequence qu'on va devoir ack
			#print self.id, "recoi", seq, ack, data

			##TRAITEMENT DU ACK SI IL EST PLUS GRAND QUE ZERO##
			if ( ack>0 ):
				dataToSendToAddr = self.commDict.get( addr )#Recupere la liste de donne a envoyer a addr
				if dataToSendToAddr:
					dataToSendToAddr = [(dat, sequence) for dat, sequence in dataToSendToAddr if sequence != ack]#Retourne la liste moins l'element confirme
					self.commDict[addr] = dataToSendToAddr

			##TRAITEMENT DE LA SEQUENCE SI ELLE EST PLUS GRAND QUE ZERO##
			if ( seq>0 ):
				self.pendingAck = (addr, seq)
				dataToSendToAddr = self.commDict.get(addr)
				if dataToSendToAddr:
					print "ICI"
					data = dataToSendToAddr[0]
					self.send(data[0], addr, data[1])

		return ( data, addr )

	def close(self):
		if self.pendingAck[1] != None: #Si on a encore un ack a faire, on le fait
			self.send("", self.pendingAck[0])
