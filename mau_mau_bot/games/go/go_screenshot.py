import os
from io import BytesIO

from PIL import Image, ImageDraw

from games.go.go_game import GoGame
from games.go.vec2 import Vec2

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'images', 'go')

board_map = {
    9: os.path.join(IMAGES_DIR, "board_9.jpg"),
    13: os.path.join(IMAGES_DIR, "board_13_no_numbers.jpg"),
    19: os.path.join(IMAGES_DIR, "board_19_no_numbers.jpg"),
}

stone_colors = {
    "white": (255, 255, 255, 0),
    "black": (0, 0, 0, 0),
}
stone_border_colors = {
    "white": stone_colors["black"],
    "black": stone_colors["white"],
}


def take_in_memory_screenshot(go_game):
    bytes_io = BytesIO()
    image = take_screenshot(go_game)
    image.save(bytes_io, "JPEG")
    bytes_io.seek(0)
    return bytes_io


def take_screenshot(go_game):
    background_image = board_map[go_game.size_x]
    img = Image.open(background_image)
    draw = ImageDraw.Draw(img)

    background = Vec2(*img.size)
    border_size = background * 0.125
    cell_width = (background - border_size * 2) / (go_game.size_x - 1)
    grid_start = background * 0.5 - cell_width * (go_game.size_x - 1) * 0.5
    stone_size = cell_width * 0.9
    mark_size = stone_size * 0.5

    def _get_bounding_box(coord, stone_size_):
        bb_start = grid_start + cell_width * coord - stone_size_ * 0.5
        bb_end = bb_start + stone_size_
        return bb_start, bb_end

    for x in range(go_game.size_x):
        for y in range(go_game.size_y):
            if go_game.board[x][y].is_free:
                continue

            stone_color = stone_colors[go_game.board[x][y].color]
            border_color = stone_border_colors[go_game.board[x][y].color]

            coord = Vec2(x, y)
            if go_game.board[x][y].color == "white":
                bb_start, bb_end = _get_bounding_box(coord, stone_size)
                draw.ellipse((*bb_start, *bb_end), fill=border_color)
                bb_start, bb_end = _get_bounding_box(coord, stone_size * 0.85)
            else:
                bb_start, bb_end = _get_bounding_box(coord, stone_size)
            draw.ellipse((*bb_start, *bb_end), fill=stone_color)

            if (x, y) == go_game.last_stone_placed:
                mark_color_value = border_color
                bb_start = grid_start + cell_width * coord - mark_size * 0.5
                bb_end = bb_start + mark_size
                draw.rectangle((*bb_start, *bb_end), outline=mark_color_value, width=3)

    return img
