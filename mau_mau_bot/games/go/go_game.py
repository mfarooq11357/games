from games.go.exceptions import (
    CoordOccupiedException, InvalidBoardSizeException,
    InvalidCoordinateException, KoException, SelfCaptureException
)

ERROR_INVALID_COORDS = "This coordinate does not exist on the board!"
ERROR_INVALID_SIZE = "Supported board sizes are 9x9, 13x13 and 19x19!"
ERROR_COORD_OCCUPIED = "This coordinate already holds a stone!"
ERROR_SELF_CAPTURE = "The move is a self-capture and is not allowed!"
ERROR_KO = "Move not allowed because of Ko rule"

REVERSE = {"white": "black", "black": "white"}


class GridPosition:
    def __init__(self):
        self.group = set()
        self.color = None

    @property
    def is_free(self):
        return self.color is None

    def clear(self):
        self.group = set()
        self.color = None


class GoGame:
    def __init__(self, size_x=9, size_y=9):
        self.size_x = size_x
        self.size_y = size_y
        self.board = []
        self.last_stone_placed = None

        self._check_board_size(size_x, size_y)
        self._create_board()
        self.last_captured_single_stone = None

    def _create_board(self):
        for x in range(self.size_x):
            column = []
            for y in range(self.size_y):
                column.append(GridPosition())
            self.board.append(column)

    def place_stone_str_coord(self, coord, color):
        coord = coord.lower()
        self._check_stone_str_coord(coord)
        x, y = self._transform_coord(coord)
        self.place_stone(x, y, color)
        self.last_stone_placed = (x, y)

    def place_stone(self, x, y, color):
        self._check_stone_coord(x, y)
        self._check_pos_taken(x, y)

        adjacent_groups = self._detect_adjacent_groups(x, y, color)
        own_group = {item for groups in adjacent_groups for item in groups}
        own_group.add((x, y))
        adjacent_opponent_groups = self._detect_adjacent_groups(x, y, REVERSE[color])
        opponent_groups_atari = [
            group for group in adjacent_opponent_groups
            if len(self._group_liberties(group)) == 1
        ]

        self._check_ko(opponent_groups_atari)
        self._check_self_capture((x, y), own_group, opponent_groups_atari)

        self._capture_neighbors(opponent_groups_atari)
        self._merge_groups(own_group, color)

    def _capture_neighbors(self, opponent_groups):
        self.last_captured_single_stone = None
        if len(opponent_groups) == 1 and len(opponent_groups[0]) == 1:
            self.last_captured_single_stone = list(opponent_groups[0])[0]

        for group in opponent_groups:
            for x, y in group.copy():
                self.board[x][y].group.remove((x, y))
                self.board[x][y].clear()

    def _merge_groups(self, new_group, color):
        for x, y in new_group:
            self.board[x][y].group = new_group
            self.board[x][y].color = color

    def _group_liberties(self, group):
        group_liberties = set()
        for stone in group:
            stone_liberties = {
                (x, y) for x, y in self._neighbors_of(*stone)
                if self.board[x][y].is_free
            }
            group_liberties = group_liberties.union(stone_liberties)
        return group_liberties

    def _detect_adjacent_groups(self, x, y, color):
        return [self.board[x][y].group for x, y in self._neighbors_of(x, y, color)]

    def _neighbors_of(self, x, y, color=None):
        neighbors = []
        if x > 0:
            neighbors.append((x - 1, y))
        if x < self.size_x - 1:
            neighbors.append((x + 1, y))
        if y > 0:
            neighbors.append((x, y - 1))
        if y < self.size_y - 1:
            neighbors.append((x, y + 1))

        if color is not None:
            neighbors = [(x, y) for x, y in neighbors if self.board[x][y].color == color]
        return neighbors

    @staticmethod
    def _transform_coord(coord):
        letter = ord(coord[0]) - ord("a")
        number = int(coord[1:]) - 1
        return letter, number

    @staticmethod
    def _check_board_size(size_x, size_y):
        if (size_x, size_y) not in [(9, 9), (13, 13), (19, 19)]:
            raise InvalidBoardSizeException(ERROR_INVALID_SIZE)

    @staticmethod
    def _check_stone_str_coord(coord):
        has_letter = ord("a") <= ord(coord[0]) < ord("z")
        has_digit = coord[1:].isdigit()
        if not has_letter or not has_digit:
            raise InvalidCoordinateException(ERROR_INVALID_COORDS)

    def _check_stone_coord(self, x, y):
        x_in_range = 0 <= x < self.size_x
        y_in_range = 0 <= y < self.size_y
        if not x_in_range or not y_in_range:
            raise InvalidCoordinateException(ERROR_INVALID_COORDS)

    def _check_pos_taken(self, x, y):
        if not self.board[x][y].is_free:
            raise CoordOccupiedException(ERROR_COORD_OCCUPIED)

    def _check_ko(self, opponent_groups):
        if self.last_captured_single_stone is None:
            return

        single_threatened_neighbor = None
        for group in opponent_groups:
            group_liberties = len(self._group_liberties(group))
            if group_liberties == 1 and len(group) == 1:
                more_than_one_target = single_threatened_neighbor is not None
                if more_than_one_target:
                    return
                single_threatened_neighbor = list(group)[0]

        if self.last_stone_placed == single_threatened_neighbor:
            raise KoException(ERROR_KO)

    def _check_self_capture(self, stone, group, opponent_groups):
        if opponent_groups:
            return

        group_liberties = self._group_liberties(group)
        if stone in group_liberties:
            group_liberties.remove(stone)
        if not group_liberties:
            raise SelfCaptureException(ERROR_SELF_CAPTURE)
