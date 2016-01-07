import sys
import time
from timer import *
import pygame
import json
import random
from constants import Constants
from snakeChan import SnakeChan
from snakePost import SnakePost
from multi_snake import Game
from Player import Player

class Server:

	def __init__(self, channel):
		self.server = SnakePost(channel, "server")

		self.players = {}
		self.apples = []

		self.clock = pygame.time.Clock()
		self.current_time = 0
		self.new_apple_timer=Timer(Constants.NEW_APPLE_PERIOD*1000,self.current_time,periodic=True)
		self.update_snakes_timer = Timer(0.1 * 1000, self.current_time, periodic=True)

	def broadcast(self, message, sec=False):
		for player in self.players:
			if sec:
				self.server.sendSecure(message, player)
			else:
				self.server.send(message, player)

	def sendPlayerInfo(self):
		obj = "{\"players_info\": ["
		for player in self.players:
			obj += "[\"" + str(self.players[player].nickname) + "\",\"" + str(self.players[player].color) + \
					   "\"," + str(self.players[player].score) + "," + str(self.players[player].ready).lower() + "],"
		obj = obj[:-1]
		obj += "]}"
		self.broadcast(obj, True)

	def sendSnakesPositions(self):
		obj = "{\"snakes\": ["
		disconnect = []
		for player in self.players:
			obj += "[\"" + str(self.players[player].nickname) + "\"," + str(self.players[player].positions) + "],"
			if self.players[player].last_message > 2000 and self.current_time - self.players[player].last_message > 2000 :
				#Le joueur n'a pas envoye de messages depuis plus de 2 secondes
				print "Le joueur " + self.players[player].nickname + " s'est deco"
				disconnect.append(player)
		for p in disconnect:
			del self.players[p]
			del self.server.commDict[p]
		obj = obj[:-1]
		obj += "]}"
		self.broadcast(obj, False)

	def sendFood(self):
		obj = "{\"foods\": " + str(self.apples) + "}"
		self.broadcast(obj, True)

	def growPlayer(self, name):
		self.broadcast("{\"grow\": \"" + name + "\"}", False)

	def gameOver(self, name):
		obj = "{\"game_over\": \"" + name + "\"}"
		self.broadcast(obj, True)

	def serve(self):

		while True:

			self.current_time += self.clock.tick(60)

			pieces = None
			data, addr = self.server.listen()

			if data is not None and not self.players.get(addr):
				#new player, on attrappe son username et sa couleur
				pieces = data.split('\\')
				if pieces[6] is not None:
					# On enregistre le nouveau player
					self.players[addr] = Player(pieces[8], pieces[6])
					print "New player " + pieces[8]

					#On notifie tout le monde, et on envoie les pommes
					self.sendPlayerInfo()


			elif data is not None:
				self.players[addr].last_message = self.current_time
				uname = self.players.get(addr).nickname

				dat = json.loads(data)
				for key in dat:
					if key == "body_p":
						# on update la position des snakes et on calcule si ils ont mange
						self.players[addr].positions = dat[key]

						if not self.players[addr].ready:
							continue

						for apple in self.apples:
							if self.players[addr].positions[0] == apple: # la tete est sur une pomme
								self.apples.remove(apple) # on enleve la pomme
								print "Will grow once " + self.players[addr].nickname
								self.growPlayer(self.players[addr].nickname)
								self.players[addr].score += 1
								self.sendFood()
								self.sendPlayerInfo()
								break

						for player in self.players:
							if not self.players[player].ready:
								continue
							for position in self.players[player].positions:
								if player == addr:
									same = self.players[player].positions.count(self.players[player].positions[0])
									if(same > 1):
										#un joueur s'est mange la queue -> game over
										self.gameOver(self.players[player].nickname)
										self.players[player].score -= 1
										self.players[player].ready = False
										self.sendPlayerInfo()
										break
								else:
									if self.players[addr].positions[0] == position:
										self.gameOver(self.players[addr].nickname)
										self.players[addr].score -= 1
										self.players[player].score += 1
										self.players[addr].ready = False
										self.sendPlayerInfo()
										break
					# on doit check les collisions et si on a mange une pommes
					if key == "ready":
						self.players[addr].ready = dat[key]
						self.sendPlayerInfo()


			if self.update_snakes_timer.expired(self.current_time):
				self.sendSnakesPositions()

			if self.new_apple_timer.expired(self.current_time) and len(self.players) > 0:
				self.apples.append([random.randint(0, Constants.UNITS - 1), random.randint(0, Constants.UNITS - 1)])
				self.sendFood()

Server(SnakeChan('127.0.0.1', 3100)).serve()
