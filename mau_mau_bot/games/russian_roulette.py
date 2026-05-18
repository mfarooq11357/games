import logging
import random

from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext

logger = logging.getLogger(__name__)

rr_games = {}

SYM_EMPTY = '\u00b7'
SYM_CHAMBER = '\U0001f518'    # Radio button
SYM_HIT = '\U0001f534'        # Red circle


def rr_new(update: Update, context: CallbackContext):
    if update.message.chat.type == 'private':
        update.message.reply_text("Russian Roulette must be played in a group chat!")
        return

    user = update.message.from_user
    keyboard = [[InlineKeyboardButton("Join Game", callback_data="rr;join;0")]]
    msg = update.message.reply_text(
        "{} wants to play <b>Russian Roulette</b>!\nPress Join to play.".format(
            _mention(user)),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    cylinder = [''] * 6
    cylinder[random.randint(0, 5)] = 'X'

    rr_games[(msg.chat_id, msg.message_id)] = {
        'host_id': user.id,
        'host_name': user.first_name,
        'guest_id': None,
        'guest_name': None,
        'cylinder': cylinder,
        'current_turn': 'X',
        'settings': {'X': 'host', 'O': 'guest'},
    }


def rr_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(';')
    key = (query.message.chat_id, query.message.message_id)
    user_id = query.from_user.id

    if key not in rr_games:
        query.answer("This game has expired!")
        return

    game = rr_games[key]
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
        _update_rr(query, game, key)
        return

    if command == 'noop':
        query.answer()
        return

    if command == 'restart':
        cylinder = [''] * 6
        cylinder[random.randint(0, 5)] = 'X'
        if game['settings']['X'] == 'host':
            game['settings'] = {'X': 'guest', 'O': 'host'}
        else:
            game['settings'] = {'X': 'host', 'O': 'guest'}
        game['cylinder'] = cylinder
        game['current_turn'] = 'X'
        _update_rr(query, game, key)
        return

    if command == 'pull':
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

        chamber = int(data[2])
        if chamber < 1 or chamber > 6:
            query.answer()
            return

        if game['cylinder'][chamber - 1] == 'X':
            current_name = game['host_name'] if current_role == 'host' else game['guest_name']
            other_turn = 'O' if game['current_turn'] == 'X' else 'X'
            other_role = game['settings'][other_turn]
            other_name = game['host_name'] if other_role == 'host' else game['guest_name']

            game_output = "\U0001f480 <b>{} died!</b>\n".format(current_name)
            game_output += "\U0001f3c6 <b>{} won!</b>".format(other_name)
            game['current_turn'] = 'E'

            _update_rr(query, game, key, hit=chamber)
            return

        current_name = game['host_name'] if current_role == 'host' else game['guest_name']
        game['current_turn'] = 'O' if game['current_turn'] == 'X' else 'X'

        game['cylinder'] = [''] * 6
        game['cylinder'][random.randint(0, 5)] = 'X'

        _update_rr(query, game, key, survived=current_name)


def _update_rr(query, game, key, hit=None, survived=None):
    header = "{} vs. {}".format(game['host_name'], game['guest_name'] or '???')

    if game['current_turn'] == 'E' and hit:
        current_role = game['settings']['X' if game['settings']['X'] != 'host' else 'O']
        dead_turn = 'X'
        for t in ('X', 'O'):
            role = game['settings'][t]
            pid = game['host_id'] if role == 'host' else game['guest_id']
            if pid == query.from_user.id:
                dead_turn = t
                break
        dead_role = game['settings'][dead_turn]
        dead_name = game['host_name'] if dead_role == 'host' else game['guest_name']
        alive_turn = 'O' if dead_turn == 'X' else 'X'
        alive_role = game['settings'][alive_turn]
        alive_name = game['host_name'] if alive_role == 'host' else game['guest_name']

        footer = "\U0001f480 <b>{} died!</b>\n\U0001f3c6 <b>{} won!</b>".format(
            dead_name, alive_name)
    elif survived:
        footer = "\U0001f60e <b>{} survived!</b>\n".format(survived)
        cur_role = game['settings'][game['current_turn']]
        cur_name = game['host_name'] if cur_role == 'host' else game['guest_name']
        footer += "\u25b6 {}'s turn".format(cur_name)
    else:
        if game['guest_id'] is None:
            footer = "Waiting for opponent..."
        else:
            cur_role = game['settings'][game['current_turn']]
            cur_name = game['host_name'] if cur_role == 'host' else game['guest_name']
            footer = "\u25b6 {}'s turn".format(cur_name)

    keyboard = _build_cylinder_keyboard(hit)

    if game['current_turn'] == 'E':
        keyboard.append([InlineKeyboardButton("Play again!", callback_data="rr;restart;0")])

    query.edit_message_text(
        "{}\n\n{}".format(header, footer),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    query.answer()


def _build_cylinder_keyboard(hit=None):
    def _ch(n):
        if hit and n == hit:
            return SYM_HIT
        return SYM_CHAMBER

    return [
        [
            InlineKeyboardButton(SYM_EMPTY, callback_data="rr;noop;0"),
            InlineKeyboardButton(_ch(1), callback_data="rr;pull;1"),
            InlineKeyboardButton(_ch(2), callback_data="rr;pull;2"),
            InlineKeyboardButton(SYM_EMPTY, callback_data="rr;noop;0"),
        ],
        [
            InlineKeyboardButton(_ch(6), callback_data="rr;pull;6"),
            InlineKeyboardButton(SYM_EMPTY, callback_data="rr;noop;0"),
            InlineKeyboardButton(_ch(3), callback_data="rr;pull;3"),
        ],
        [
            InlineKeyboardButton(SYM_EMPTY, callback_data="rr;noop;0"),
            InlineKeyboardButton(_ch(5), callback_data="rr;pull;5"),
            InlineKeyboardButton(_ch(4), callback_data="rr;pull;4"),
            InlineKeyboardButton(SYM_EMPTY, callback_data="rr;noop;0"),
        ],
    ]


def _mention(user):
    return '<a href="tg://user?id={}">{}</a>'.format(user.id, user.first_name)


def register(dispatcher):
    dispatcher.add_handler(CommandHandler('rr', rr_new))
    dispatcher.add_handler(CallbackQueryHandler(rr_callback, pattern=r'^rr;'))
