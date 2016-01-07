# -*- coding: utf-8 -*-

import pygame
import json
from constants import Constants
from object_snake import *
from object_foods import *
from scores import *
from preferences import Preferences
from banner import *
from timer import *
from snakeChan import SnakeChan
from snakePost import SnakePost

class Game:
    def __init__(self):
        pygame.init()

        #get preferences
        self.preferences = Preferences()
        # self.nickname = raw_input('Choose a username: ')
        # self.color = raw_input('Choose a color (red, green, blue, yellow, white): ')
        #resolution, flags, depth, display
        self.unit=Constants.RESOLUTION[0]/Constants.UNITS
        self.banner = Banner()
        self.score_width=self.unit*15

        if self.preferences.fullscreen:
            self.screen = pygame.display.set_mode((Constants.RESOLUTION[0]+self.score_width,\
                                               Constants.RESOLUTION[1]),pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((Constants.RESOLUTION[0]+self.score_width,\
                                               Constants.RESOLUTION[1]),0,32)

        pygame.display.set_caption(Constants.CAPTION)

        #game area surface
        self.gamescreen = pygame.Surface(Constants.RESOLUTION)
        #score area rectangle surface
        self.scorescreen = pygame.Surface((self.score_width,Constants.RESOLUTION[1]))

        #Snake and foods manager
        self.me=Snake(color=pygame.color.THECOLORS[self.preferences.get("color")],\
                    nickname=self.preferences.get("nickname"))


        self.f=Foods()

        self.others = {}

        #Score manager
        self.scores=Scores((self.score_width,Constants.RESOLUTION[1]))

        #add our own score, the server will send us the remaining one at connection
        self.scores.new_score(self.preferences.get("nickname"),\
                        pygame.color.THECOLORS[self.preferences.get("color")])

	#game area background color
        self.gamescreen.fill(Constants.COLOR_BG)
        self.scorescreen.fill((100,100,100))

        #timers
        self.clock=pygame.time.Clock();
        self.current_time=0

        self.move_snake_timer=Timer(1.0/Constants.SNAKE_SPEED*1000,self.current_time,periodic=True)
        self.blink_snake_timer=Timer(1.0/Constants.SNAKE_BLINKING_SPEED*1000,self.current_time,periodic=True)
        self.blink_banner_timer=Timer(500,self.current_time,periodic=True)
        self.new_apple_timer=Timer(Constants.NEW_APPLE_PERIOD*1000,self.current_time,periodic=True)



    def process_events(self):
        #key handling
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                   self.running=False
                if event.key == pygame.K_UP:
                   self.me.action(1)
                if event.key == pygame.K_DOWN:
                   self.me.action(2)
                if event.key == pygame.K_LEFT:
                   self.me.action(3)
                if event.key == pygame.K_RIGHT:
                   self.me.action(4)
                if event.key == pygame.K_SPACE:
                   #self.me.set_ready()
                   self.com.sendSecure("{\"ready\": true}", self.address)
    def run(self):

        self.address = (self.preferences.get("server"), self.preferences.get("port"))
        self.client = SnakeChan()

        self.client.connect(self.address, self.preferences.get("color"), self.preferences.get("nickname"))
        self.com = SnakePost(self.client, self.preferences.get("nickname"))

        whole_second=0
        self.running=True
        while self.running:
            #time tracking
            self.current_time+=self.clock.tick(Constants.FPS)

            #check if the snake is still alive
            if not self.me.alive:
                self.me.alive=True
                self.me.restart()

            #check if game need more food
            # if self.new_apple_timer.expired(self.current_time):
            #     self.f.make()

            #check if we need to move our own snake's state
            #if we do, send an update of our position to
            #the server
            if self.move_snake_timer.expired(self.current_time):
                self.me.move()
                pos = self.me.netinfo()
                self.com.send(pos, self.address)

            #check if we need to blink the unready snakes (unready state)
            if self.blink_snake_timer.expired(self.current_time):
                for snake in self.others:
                    self.others[snake].blink()

            #check if snake has eaten
            # if self.me.ready:
            #     if self.f.check(self.me.head):
            #         self.me.grow(Constants.GROW)
            #         self.scores.inc_score(self.nickname,1)


            #cleanup background
            self.gamescreen.fill(Constants.COLOR_BG)

            #draw scores
            self.scores.draw(self.screen)

            #draw all snakes positions as last seen by the server
            #we do not compute their positions ourselves!
            #self.me.draw(self.gamescreen)
            for snake in self.others:
                self.others[snake].draw(self.gamescreen)
            #draw food
            self.f.draw(self.gamescreen)

            #process external events (keyboard,...)
            self.process_events()

            #then update display
            #update game area on screen container
            self.screen.blit(self.gamescreen,(self.score_width,0))

            pygame.display.update()

            data, addr = self.com.listen()
            if data is not None:
                dat = json.loads(data)
                for key in dat:
                    if key == 'players_info':
                        #update players and scores
                        for player in dat[key]:

                            if not self.others.get(player[0]):
                                print "New player ! " + player[0]
                                self.others[player[0]] = Snake(color=pygame.color.THECOLORS[player[1]], nickname=player[0])
                                self.scores.new_score(player[0], self.others.get(player[0]).color)

                            else:
                                if player[3]:
                                    self.others[player[0]].set_ready()
                                else:
                                    self.others[player[0]].set_unready()
                            self.scores.set_score(player[0], player[2])
                    elif key == "snakes":
                        for val in dat[key]:
                            if len(val[1]) > 0 and self.others[val[0]]:
                                self.others[val[0]].setBody(val[1])
                        # on regarde si il y a des serpents a enlever
                        if len(dat[key]) != len(self.others):
                            for nickname in self.others.keys():
                                connected = False
                                for val in dat[key]:
                                    if val[0] == nickname:
                                        connected = True
                                if not connected:
                                    del self.others[nickname]
                                    self.scores.del_score(nickname)
                    elif key == "foods":
                        self.f.set_positions(dat[key])
                    elif key == "grow":
                        if dat[key] == self.preferences.get("nickname"):
                            self.me.grow(Constants.GROW)
                    elif key == "game_over":
                        if dat[key] == self.preferences.get("nickname"):
                            self.me.restart()
