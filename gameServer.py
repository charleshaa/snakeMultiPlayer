import sys
import time
from timer import *
import pygame
import json
import random
from Color import color
from constants import Constants
from snakeChan import SnakeChan
from snakePost import SnakePost
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

    #Envoie un message a tous les clients
    def broadcast(self, message, sec=False):
        for player in self.players:
            if sec:
                self.server.sendSecure(message, player)
            else:
                self.server.send(message, player)

    # Broadcast les scores et etats de tous les joueurs
    def sendPlayerInfo(self):
        obj = "{\"players_info\": ["
        for player in self.players:
            obj += "[\"" + str(self.players[player].nickname) + "\",\"" + str(self.players[player].color) + \
                       "\"," + str(self.players[player].score) + "," + str(self.players[player].ready).lower() + "],"
        obj = obj[:-1]
        obj += "]}"
        self.broadcast(obj, True)

    # Broadcast la position de tous les snakes, et regarde si un joueur a timeout
    def sendSnakesPositions(self):
        obj = "{\"snakes\": ["
        disconnect = []
        for player in self.players:
            obj += "[\"" + str(self.players[player].nickname) + "\"," + str(self.players[player].positions) + "],"
            if self.players[player].last_message > (Constants.PLAYER_TIMEOUT * 1000) and self.current_time - self.players[player].last_message > (Constants.PLAYER_TIMEOUT * 1000) :
                #Le joueur n'a pas envoye de messages depuis plus de 2 secondes
                print color.RED + "Le joueur " + self.players[player].nickname + " s'est deconnecte" + color.END
                disconnect.append(player)
        for p in disconnect:
            del self.players[p]
            del self.server.commDict[p]
        obj = obj[:-1]
        obj += "]}"
        self.broadcast(obj, False)

    # Broadcast les pommes
    def sendFood(self):
        obj = "{\"foods\": " + str(self.apples) + "}"
        self.broadcast(obj, True)

    # Broadcast un message pour l'agrandissement d'un serpent
    def growPlayer(self, name):
        self.broadcast("{\"grow\": \"" + name + "\"}", False)

    # Broadcast le game over d'un serpent
    def gameOver(self, name):
        print color.YELLOW + "Game over for " + name + color.END
        obj = "{\"game_over\": \"" + name + "\"}"
        self.broadcast(obj, True)

    # Routine du serveur
    def serve(self):

        while True:

            # La clock du jeu
            self.current_time += self.clock.tick(Constants.FPS)

            pieces = None # Variable qui contiendra les donnees de connexion
            data, addr = self.server.listen() # Attend un message d'un client

            if data is not None and not self.players.get(addr):
                #Nouveau joueur, on attrappe son username et sa couleur
                pieces = data.split('\\')
                if pieces[6] is not None: # Si on a un message du format de connexion, pieces[6] sera le username
                    # On enregistre le nouveau player
                    self.players[addr] = Player(pieces[8], pieces[6])
                    print color.GREEN + "Nouveau joueur " + pieces[8] + color.END

                    #On notifie tout le monde
                    self.sendPlayerInfo()


            elif data is not None: # On a de la donnee utilisable
                self.players[addr].last_message = self.current_time
                # On convertit le json
                dat = json.loads(data)
                for key in dat: # Une boucle qui sera de un pas, mais qui nous permet d'avoir la cle
                    if key == "body_p":
                        # on update la position des snakes et on calcule si ils ont mange
                        self.players[addr].positions = dat[key]

                        if not self.players[addr].ready: # si le player n'est pas ready, on se fiche des pommes ou collisions.
                            continue

                        for player in self.players: # Checkons les collisions
                            if not self.players[player].ready: # on s'en fiche si le player n'est pas ready
                                continue
                            for position in self.players[player].positions: # On regarde dans ses positions
                                if player == addr: # Si on est en train de regarder le meme player que celui qui envoie body_p
                                    same = self.players[player].positions.count(self.players[player].positions[0]) # on regarde si sa tete se confond avec son corps
                                    if(same > 1): # La tete est a la meme position qu'une autre case du serpent
                                        #un joueur s'est mange la queue -> game over
                                        self.gameOver(self.players[player].nickname)
                                        self.players[player].score -= 1
                                        self.players[player].ready = False
                                        self.sendPlayerInfo()
                                        break
                                else: # Sinon on regarde si il touche un autre serpent
                                    if self.players[addr].positions[0] == position: # il touche une autre position
                                        self.gameOver(self.players[addr].nickname)
                                        self.players[addr].score -= 1
                                        self.players[player].score += 1
                                        self.players[addr].ready = False
                                        self.sendPlayerInfo()
                                        break

                        for apple in self.apples: # On check si le joueur a mange une pomme
                            if self.players[addr].positions[0] == apple: # la tete est sur une pomme
                                self.apples.remove(apple) # on enleve la pomme
                                print color.CYAN +  "An apple has been eaten by " + self.players[addr].nickname + color.END
                                self.growPlayer(self.players[addr].nickname) # le serpent grandit
                                self.players[addr].score += 1 # le score aussi
                                self.sendFood() # On avise tout le monde que la pomme a ete mangee
                                self.sendPlayerInfo() # On avise tout le monde des scores
                                break


                    if key == "ready":
                        print color.BOLD + self.players[addr].nickname + " is now ready to play" + color.END
                        self.players[addr].ready = dat[key]
                        self.sendPlayerInfo()

            # Envoi perdiodique des positions de chacun
            if self.update_snakes_timer.expired(self.current_time):
                self.sendSnakesPositions()
            # Envoi periodique des pommes, on ne le fait pas tant que personne n'est ingame
            if self.new_apple_timer.expired(self.current_time) and len(self.players) > 0:
                self.apples.append([random.randint(0, Constants.UNITS - 1), random.randint(0, Constants.UNITS - 1)])
                self.sendFood()

Server(SnakeChan('127.0.0.1', 3100)).serve()
