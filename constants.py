#  YetAnotherPythonSnake 0.92
#  Author: Simone Cingano (simonecingano@gmail.com)
#  Web: http://simonecingano.it
#  Licence: MIT
#

import os

class Constants:
    """ All of the in-game constants are declared here."""

    # GAME NAME
    CAPTION = "Yet Another Python Snake - Single-player"
    UNITS = 40
    RESOLUTION = (500,500)

    # FPS
    FPS = 60

    #In square per seconds
    SNAKE_SPEED = 10

    #In one apple every X seconds
    NEW_APPLE_PERIOD = 10
    #maximum number of apple at the same time on the board
    MAX_APPLE_SAME_TIME = 5

    #In blink per second
    SNAKE_BLINKING_SPEED = 2

    COLOR_BG = (0,0,0)

    START_LENGTH = 5

    #by how much the snake will grow for each apple
    GROW = 2

    PREFERENCES_FILE="data/preferences.dat"

    CREDITS = """*Yet Another Python Snake (YAPS v0.92)
This game was made, as a personal exercise with python
and pygame, in a few days in June 2012
It's free, licensed under MIT Licence
Visit http://simonecingano.it for more info and the source code

*Design & Programming
Simone Cingano

*Sound & Music
NLM, Setuniman, Rock Savage, j1987, qubodup, theta4, Freqman
(CC) freesound.org

*Title Background
"Close up grass" by Sam Kim
(CC) flickr.com"""
