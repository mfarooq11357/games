from games.go.go_game import GoGame
from games.go.player import GoPlayer, PlayerColor


class TelegramGoGame(GoGame):
    def __init__(self, chat_id, board_x, board_y):
        super().__init__(board_x, board_y)
        self.chat_id = chat_id
        self.players = []
        self.current_player_index = 0

    @property
    def is_game_over(self):
        return all(player.did_pass for player in self.players)

    @property
    def current_player(self):
        if not self.players:
            return None
        return self.players[self.current_player_index]

    def add_player(self, player_id, player_name):
        is_first_player = not self.players
        color = PlayerColor.WHITE if is_first_player else PlayerColor.BLACK
        self.players.append(GoPlayer(player_id, player_name, color))
        self.current_player_index = len(self.players) - 1

    def place_stone_str_coord(self, coord, color=None):
        assert self.current_player
        super().place_stone_str_coord(coord, self.current_player.color)
        self.current_player.did_pass = False
        self._change_turn()

    def pass_turn(self):
        assert self.current_player
        self.current_player.did_pass = True
        self._change_turn()

    def _change_turn(self):
        self.current_player_index = (self.current_player_index + 1) % 2

    def has_enough_players(self):
        return len(self.players) == 2
