import random

from games.go.telegram_go_game import TelegramGoGame


GO_PROVERBS = [
    "The enemy's key point is yours.",
    "Play on the point of symmetry.",
    "Keep your stones connected.",
    "Don't try to cut what can't be cut.",
    "Strange things happen at the 1-2 points.",
    "Don't go fishing while your house is on fire.",
    "Lose your first 50 games as quickly as possible.",
]

PATIENCE_PROVERBS = [
    "Patience is bitter, but its fruit is sweet.",
    "The key to everything is patience.",
]


class GameHandlerException(Exception):
    pass


class GoGameHandler:
    def __init__(self):
        self.games = {}

    def get_game(self, chat_id, raise_if_not_found=False):
        game = self.games.get(chat_id)
        if game is None and raise_if_not_found:
            raise GameHandlerException("No Go game in this chat. Start one with /go")
        return game

    def new_game(self, chat_id, player_id, player_name, board_size=9):
        old_game = self.get_game(chat_id)
        if old_game is not None:
            _check_if_participating(player_id, old_game)

        if board_size not in (9, 13, 19):
            raise GameHandlerException("The board size has to be 9, 13 or 19!")

        new_game = TelegramGoGame(
            chat_id=chat_id,
            board_x=board_size,
            board_y=board_size,
        )
        new_game.add_player(player_id, player_name)
        self.games[chat_id] = new_game
        return new_game

    def join(self, chat_id, player_id, player_name):
        game = self.get_game(chat_id, raise_if_not_found=True)
        if game.has_enough_players():
            raise GameHandlerException("The game already has 2 players!")
        game.add_player(player_id, player_name)
        return game

    def place_stone(self, chat_id, player_id, coord):
        game = self.get_game(chat_id, raise_if_not_found=True)
        _check_enough_players(game)
        _check_if_participating(player_id, game)
        _check_player_turn(player_id, game)
        game.place_stone_str_coord(coord)
        return game

    def pass_turn(self, chat_id, player_id):
        game = self.get_game(chat_id, raise_if_not_found=True)
        _check_enough_players(game)
        _check_if_participating(player_id, game)
        _check_player_turn(player_id, game)
        game.pass_turn()
        return game

    def remove_game(self, chat_id):
        self.games.pop(chat_id, None)


def _check_if_participating(player_id, game):
    if player_id not in [p.id_ for p in game.players]:
        raise GameHandlerException("You are not part of the current game!")


def _check_player_turn(player_id, game):
    if not game.current_player:
        raise GameHandlerException("The game has no players yet!")
    if player_id != game.current_player.id_:
        msg = random.choice(PATIENCE_PROVERBS) + "\nIt is not your turn!"
        raise GameHandlerException(msg)


def _check_enough_players(game):
    if not game.has_enough_players():
        raise GameHandlerException("Another player needs to join with /go_join!")
