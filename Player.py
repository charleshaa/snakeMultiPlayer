class Player:

    def __init__(self, nickname, color):
        self.nickname = nickname
        self.color = color
        self.score = 0
        self.ready = False
        self.positions = []
        self.last_message = 0
