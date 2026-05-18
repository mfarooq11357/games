import logging

from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext

logger = logging.getLogger(__name__)

# In-memory game storage: key = (chat_id, message_id)
ttt_games = {}

SYMBOLS = {
    '': ' ',
    'X': '\u274c',       # Cross mark
    'O': '\u2b55',       # Hollow red circle
    'X_won': '\u274c',
    'O_won': '\u2b55',
    'X_lost': '\u2716',  # Heavy multiplication
    'O_lost': '\u25cb',  # White circle
}


def ttt_new(update: Update, context: CallbackContext):
    if update.message.chat.type == 'private':
        update.message.reply_text("Tic-Tac-Toe must be played in a group chat!")
        return

    user = update.message.from_user
    keyboard = [[InlineKeyboardButton("Join Game", callback_data="ttt;join;0")]]
    msg = update.message.reply_text(
        "{} wants to play <b>Tic-Tac-Toe</b>!\nPress Join to play.".format(
            _mention(user)),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    ttt_games[(msg.chat_id, msg.message_id)] = {
        'host_id': user.id,
        'host_name': user.first_name,
        'guest_id': None,
        'guest_name': None,
        'board': [[''] * 3 for _ in range(3)],
        'current_turn': 'X',
        'settings': {'X': 'host', 'O': 'guest'},
    }


def ttt_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(';')
    chat_id = query.message.chat_id
    msg_id = query.message.message_id
    user_id = query.from_user.id
    key = (chat_id, msg_id)

    if key not in ttt_games:
        query.answer("This game has expired!")
        return

    game = ttt_games[key]
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
        _update_board_message(query, game, key)
        return

    if command == 'move':
        if game['guest_id'] is None:
            query.answer("Waiting for an opponent to join!")
            return

        if game['current_turn'] == 'E':
            query.answer("This game has ended!")
            return

        current_role = game['settings'][game['current_turn']]
        current_player_id = game['host_id'] if current_role == 'host' else game['guest_id']

        if user_id != current_player_id:
            query.answer("It's not your turn!")
            return

        row, col = int(data[2]), int(data[3])
        if game['board'][row][col] != '':
            query.answer("Invalid move!")
            return

        game['board'][row][col] = game['current_turn']
        game['current_turn'] = 'O' if game['current_turn'] == 'X' else 'X'

        _update_board_message(query, game, key)


def _update_board_message(query, game, key):
    board = game['board']
    is_over = _check_winner(board)

    host_sym = SYMBOLS['X'] if game['settings']['X'] == 'host' else SYMBOLS['O']
    guest_sym = SYMBOLS['O'] if game['settings']['O'] == 'guest' else SYMBOLS['X']

    header = "{} ({}) vs. {} ({})".format(
        _mention_name(game['host_name']), host_sym,
        _mention_name(game['guest_name'] or '???'), guest_sym
    )

    if is_over == 'X' or is_over == 'O':
        winner_role = game['settings'][is_over]
        winner_name = game['host_name'] if winner_role == 'host' else game['guest_name']
        footer = "\U0001f3c6 <b>{} won!</b>".format(_mention_name(winner_name))
        game['current_turn'] = 'E'
    elif is_over == 'T':
        footer = "\U0001f3c1 <b>Game ended with a draw!</b>"
        game['current_turn'] = 'E'
    else:
        current_role = game['settings'][game['current_turn']]
        current_name = game['host_name'] if current_role == 'host' else game['guest_name']
        current_sym = SYMBOLS[game['current_turn']]
        footer = "\u25b6 {} ({})".format(_mention_name(current_name), current_sym)

    keyboard = _build_keyboard(board, is_over)

    if is_over in ('X', 'O', 'T'):
        keyboard.append([InlineKeyboardButton("Play again!", callback_data="ttt;restart;0")])

    query.edit_message_text(
        "{}\n\n{}".format(header, footer),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    query.answer()


def _build_keyboard(board, is_over):
    keyboard = []
    for r in range(3):
        row = []
        for c in range(3):
            cell = board[r][c]
            if is_over and cell != '' and not cell.endswith('_won') and not cell.endswith('_lost'):
                display = SYMBOLS.get(cell + '_lost', SYMBOLS.get(cell, ' '))
            elif cell.endswith('_won'):
                display = SYMBOLS.get(cell, SYMBOLS.get(cell.replace('_won', ''), ' '))
            elif cell != '':
                display = SYMBOLS.get(cell, ' ')
            else:
                display = '\u00b7'

            cb = "ttt;move;{};{}".format(r, c) if cell == '' and not is_over else "ttt;noop;0"
            row.append(InlineKeyboardButton(display, callback_data=cb))
        keyboard.append(row)
    return keyboard


def _check_winner(board):
    for r in range(3):
        if board[r][0] != '' and board[r][0] == board[r][1] == board[r][2]:
            winner = board[r][0]
            board[r][0] = winner + '_won'
            board[r][1] = winner + '_won'
            board[r][2] = winner + '_won'
            return winner
    for c in range(3):
        if board[0][c] != '' and board[0][c] == board[1][c] == board[2][c]:
            winner = board[0][c]
            board[0][c] = winner + '_won'
            board[1][c] = winner + '_won'
            board[2][c] = winner + '_won'
            return winner
    if board[0][0] != '' and board[0][0] == board[1][1] == board[2][2]:
        winner = board[0][0]
        board[0][0] = winner + '_won'
        board[1][1] = winner + '_won'
        board[2][2] = winner + '_won'
        return winner
    if board[0][2] != '' and board[0][2] == board[1][1] == board[2][0]:
        winner = board[0][2]
        board[0][2] = winner + '_won'
        board[1][1] = winner + '_won'
        board[2][0] = winner + '_won'
        return winner
    if all(board[r][c] != '' for r in range(3) for c in range(3)):
        return 'T'
    return None


def _mention(user):
    return '<a href="tg://user?id={}">{}</a>'.format(user.id, user.first_name)


def _mention_name(name):
    return name or '???'


def _handle_restart(query, game, key):
    if game['settings']['X'] == 'host':
        game['settings'] = {'X': 'guest', 'O': 'host'}
    else:
        game['settings'] = {'X': 'host', 'O': 'guest'}
    game['board'] = [[''] * 3 for _ in range(3)]
    game['current_turn'] = 'X'
    _update_board_message(query, game, key)


def ttt_full_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(';')
    key = (query.message.chat_id, query.message.message_id)

    if data[1] == 'restart':
        if key in ttt_games:
            _handle_restart(query, ttt_games[key], key)
        else:
            query.answer("Game expired!")
        return

    if data[1] == 'noop':
        query.answer()
        return

    ttt_callback(update, context)


def register(dispatcher):
    dispatcher.add_handler(CommandHandler('ttt', ttt_new))
    dispatcher.add_handler(CallbackQueryHandler(ttt_full_callback, pattern=r'^ttt;'))
