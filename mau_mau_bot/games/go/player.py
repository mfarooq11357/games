class PlayerColor:
    WHITE = "white"
    BLACK = "black"


class GoPlayer:
    def __init__(self, id_, name, color):
        self.id_ = id_
        self.name = name
        self.color = color
        self.did_pass = False
