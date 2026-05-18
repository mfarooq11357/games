import logging

from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext

logger = logging.getLogger(__name__)

c4_games = {}

ROWS = 6
COLS = 7

SYMBOLS = {
    '': '\u26aa',         # White circle (empty)
    'X': '\U0001f535',    # Blue circle
    'O': '\U0001f534',    # Red circle
    'X_won': '\U0001f537', # Large blue diamond
    'O_won': '\U0001f536', # Large orange diamond
    'X_lost': '\u26ab',   # Black circle
    'O_lost': '\u26ab',   # Black circle
}

COL_LABELS = ['\u0031\u20e3', '\u0032\u20e3', '\u0033\u20e3',
              '\u0034\u20e3', '\u0035\u20e3', '\u0036\u20e3', '\u0037\u20e3']


def c4_new(update: Update, context: CallbackContext):
    if update.message.chat.type == 'private':
        update.message.reply_text("Connect Four must be played in a group chat!")
        return

    user = update.message.from_user
    keyboard = [[InlineKeyboardButton("Join Game", callback_data="c4;join;0")]]
    msg = update.message.reply_text(
        "{} wants to play <b>Connect Four</b>!\nPress Join to play.".format(
            _mention(user)),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    c4_games[(msg.chat_id, msg.message_id)] = {
        'host_id': user.id,
        'host_name': user.first_name,
        'guest_id': None,
        'guest_name': None,
        'board': [['' for _ in range(COLS)] for _ in range(ROWS)],
        'current_turn': 'X',
        'settings': {'X': 'host', 'O': 'guest'},
    }


def c4_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(';')
    key = (query.message.chat_id, query.message.message_id)
    user_id = query.from_user.id

    if key not in c4_games:
        query.answer("This game has expired!")
        return

    game = c4_games[key]
    command = data[1]

    if command == 'join':
        if user_id == game['host_id']:
            query.answer("You can't play against yourself!")
            return
        if game['guest_id'] is not None:
            query.answer("Game already has two players!")
            return
        game['guest_id'] = user_id
        game['guest_name'] = query.from_user.first_name
        _update_board(query, game, key)
        return

    if command == 'noop':
        query.answer()
        return

    if command == 'restart':
        if game['settings']['X'] == 'host':
            game['settings'] = {'X': 'guest', 'O': 'host'}
        else:
            game['settings'] = {'X': 'host', 'O': 'guest'}
        game['board'] = [['' for _ in range(COLS)] for _ in range(ROWS)]
        game['current_turn'] = 'X'
        _update_board(query, game, key)
        return

    if command == 'drop':
        if game['guest_id'] is None:
            query.answer("Waiting for opponent!")
            return
        if game['current_turn'] == 'E':
            query.answer("This game has ended!")
            return

        current_role = game['settings'][game['current_turn']]
        current_pid = game['host_id'] if current_role == 'host' else game['guest_id']
        if user_id != current_pid:
            query.answer("It's not your turn!")
            return

        col = int(data[2])
        board = game['board']

        placed = False
        for row in range(ROWS - 1, -1, -1):
            if board[row][col] == '':
                board[row][col] = game['current_turn']
                placed = True
                break

        if not placed:
            query.answer("Column is full!")
            return

        game['current_turn'] = 'O' if game['current_turn'] == 'X' else 'X'
        _update_board(query, game, key)


def _update_board(query, game, key):
    board = game['board']
    is_over = _check_winner(board)

    host_sym = SYMBOLS['X'] if game['settings']['X'] == 'host' else SYMBOLS['O']
    guest_sym = SYMBOLS['O'] if game['settings']['O'] == 'guest' else SYMBOLS['X']

    header = "{} ({}) vs. {} ({})".format(
        game['host_name'], host_sym,
        game['guest_name'] or '???', guest_sym
    )

    if is_over in ('X', 'O'):
        winner_role = game['settings'][is_over]
        winner_name = game['host_name'] if winner_role == 'host' else game['guest_name']
        footer = "\U0001f3c6 <b>{} won!</b>".format(winner_name)
        game['current_turn'] = 'E'
    elif is_over == 'T':
        footer = "\U0001f3c1 <b>Draw!</b>"
        game['current_turn'] = 'E'
    else:
        cur_role = game['settings'][game['current_turn']]
        cur_name = game['host_name'] if cur_role == 'host' else game['guest_name']
        footer = "\u25b6 {} ({})".format(cur_name, SYMBOLS[game['current_turn']])

    keyboard = []

    if not is_over and game['guest_id'] is not None:
        drop_row = []
        for c in range(COLS):
            drop_row.append(InlineKeyboardButton(
                COL_LABELS[c], callback_data="c4;drop;{}".format(c)))
        keyboard.append(drop_row)

    for r in range(ROWS):
        row = []
        for c in range(COLS):
            cell = board[r][c]
            if is_over and cell and not cell.endswith('_won'):
                sym = SYMBOLS.get(cell + '_lost', SYMBOLS.get(cell, SYMBOLS['']))
            else:
                sym = SYMBOLS.get(cell, SYMBOLS[''])
            row.append(InlineKeyboardButton(sym, callback_data="c4;noop;0"))
        keyboard.append(row)

    if is_over:
        keyboard.append([InlineKeyboardButton("Play again!", callback_data="c4;restart;0")])

    query.edit_message_text(
        "{}\n\n{}".format(header, footer),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    query.answer()


def _check_winner(board):
    empty = 0
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == '':
                empty += 1
            # Horizontal
            if c + 3 < COLS:
                if (board[r][c] != '' and
                    board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]):
                    w = board[r][c]
                    for i in range(4):
                        board[r][c+i] = w + '_won'
                    return w
            # Vertical
            if r + 3 < ROWS:
                if (board[r][c] != '' and
                    board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]):
                    w = board[r][c]
                    for i in range(4):
                        board[r+i][c] = w + '_won'
                    return w
            # Diagonal down-right
            if r + 3 < ROWS and c + 3 < COLS:
                if (board[r][c] != '' and
                    board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]):
                    w = board[r][c]
                    for i in range(4):
                        board[r+i][c+i] = w + '_won'
                    return w
            # Diagonal up-right
            if r - 3 >= 0 and c + 3 < COLS:
                if (board[r][c] != '' and
                    board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]):
                    w = board[r][c]
                    for i in range(4):
                        board[r-i][c+i] = w + '_won'
                    return w
    if empty == 0:
        return 'T'
    return None


def _mention(user):
    return '<a href="tg://user?id={}">{}</a>'.format(user.id, user.first_name)


def register(dispatcher):
    dispatcher.add_handler(CommandHandler('c4', c4_new))
    dispatcher.add_handler(CallbackQueryHandler(c4_callback, pattern=r'^c4;'))
