import logging

from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext

logger = logging.getLogger(__name__)

rps_games = {}

SYMBOLS = {
    'R': 'ROCK',
    'R_short': '\u270a',    # Raised fist
    'P': 'PAPER',
    'P_short': '\u270b',    # Raised hand
    'S': 'SCISSORS',
    'S_short': '\u270c',    # Victory hand
}


def rps_new(update: Update, context: CallbackContext):
    if update.message.chat.type == 'private':
        update.message.reply_text("Rock-Paper-Scissors must be played in a group chat!")
        return

    user = update.message.from_user
    keyboard = [[InlineKeyboardButton("Join Game", callback_data="rps;join;0")]]
    msg = update.message.reply_text(
        "{} wants to play <b>Rock-Paper-Scissors</b>!\nPress Join to play.".format(
            _mention(user)),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    rps_games[(msg.chat_id, msg.message_id)] = {
        'host_id': user.id,
        'host_name': user.first_name,
        'guest_id': None,
        'guest_name': None,
        'host_pick': '',
        'guest_pick': '',
        'host_wins': 0,
        'guest_wins': 0,
        'round': 1,
    }


def rps_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(';')
    key = (query.message.chat_id, query.message.message_id)
    user_id = query.from_user.id

    if key not in rps_games:
        query.answer("This game has expired!")
        return

    game = rps_games[key]
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
        _update_rps(query, game)
        return

    if command == 'noop':
        query.answer()
        return

    if command == 'restart':
        game['host_pick'] = ''
        game['guest_pick'] = ''
        game['host_wins'] = 0
        game['guest_wins'] = 0
        game['round'] = 1
        game['ended'] = False
        _update_rps(query, game)
        return

    if command == 'pick':
        if game['guest_id'] is None:
            query.answer("Waiting for opponent!")
            return
        if game.get('ended'):
            query.answer("This game has ended!")
            return

        pick = data[2]
        if pick not in ('R', 'P', 'S'):
            query.answer("Invalid pick!")
            return

        if user_id == game['host_id'] and game['host_pick'] == '':
            game['host_pick'] = pick
            query.answer("You picked {}!".format(SYMBOLS[pick]))
        elif user_id == game['guest_id'] and game['guest_pick'] == '':
            game['guest_pick'] = pick
            query.answer("You picked {}!".format(SYMBOLS[pick]))
        elif user_id == game['host_id'] and game['host_pick'] != '':
            query.answer("You already picked!")
            return
        elif user_id == game['guest_id'] and game['guest_pick'] != '':
            query.answer("You already picked!")
            return
        else:
            query.answer("You're not in this game!")
            return

        _update_rps(query, game)


def _update_rps(query, game):
    game_output = ''
    host_pick_display = ''
    guest_pick_display = ''

    if game['host_pick'] != '' and game['guest_pick'] != '':
        result = _determine_winner(game['host_pick'], game['guest_pick'])
        game['round'] += 1

        host_pick_display = ' ({})'.format(SYMBOLS[game['host_pick'] + '_short'])
        guest_pick_display = ' ({})'.format(SYMBOLS[game['guest_pick'] + '_short'])

        if result == 'X':
            game['host_wins'] += 1
            game_output = "\U0001f3c5 <b>{} won this round!</b>\n".format(game['host_name'])
        elif result == 'O':
            game['guest_wins'] += 1
            game_output = "\U0001f3c5 <b>{} won this round!</b>\n".format(game['guest_name'])
        else:
            game_output = "\U0001f3c1 <b>This round was a draw!</b>\n"

        game['host_pick'] = ''
        game['guest_pick'] = ''

    game_ended = False
    if game['host_wins'] >= 3 and game['host_wins'] > game['guest_wins']:
        game_output = "\U0001f3c6 <b>{} won the game!</b>".format(game['host_name'])
        game_ended = True
    elif game['guest_wins'] >= 3 and game['guest_wins'] > game['host_wins']:
        game_output = "\U0001f3c6 <b>{} won the game!</b>".format(game['guest_name'])
        game_ended = True
    elif game['round'] > 5 and game['host_wins'] != game['guest_wins']:
        winner = game['host_name'] if game['host_wins'] > game['guest_wins'] else game['guest_name']
        game_output = "\U0001f3c6 <b>{} won the game!</b>".format(winner)
        game_ended = True
    elif not game_ended:
        if game['host_pick'] != '' and game['guest_pick'] == '':
            game_output += "Waiting for: {}".format(game['guest_name'])
        elif game['guest_pick'] != '' and game['host_pick'] == '':
            game_output += "Waiting for: {}".format(game['host_name'])
        else:
            game_output += "<b>Round {} - make your picks!</b>".format(game['round'])

    game['ended'] = game_ended

    scores = ''
    if game['host_wins'] > 0 or game['guest_wins'] > 0:
        scores = ' ({h}) vs. ({g})'.format(h=game['host_wins'], g=game['guest_wins'])

    header = "{}{} vs. {}{}".format(
        game['host_name'], host_pick_display,
        game['guest_name'] or '???', guest_pick_display,
    )
    if scores:
        header = "{}({}) vs. {}({})".format(
            game['host_name'], game['host_wins'],
            game['guest_name'] or '???', game['guest_wins'],
        )

    keyboard = []
    if not game_ended:
        keyboard.append([
            InlineKeyboardButton("{} {}".format(SYMBOLS['R'], SYMBOLS['R_short']),
                                 callback_data="rps;pick;R"),
            InlineKeyboardButton("{} {}".format(SYMBOLS['P'], SYMBOLS['P_short']),
                                 callback_data="rps;pick;P"),
            InlineKeyboardButton("{} {}".format(SYMBOLS['S'], SYMBOLS['S_short']),
                                 callback_data="rps;pick;S"),
        ])
    else:
        keyboard.append([InlineKeyboardButton("Play again!", callback_data="rps;restart;0")])

    query.edit_message_text(
        "{}\n\n{}".format(header, game_output),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def _determine_winner(host_pick, guest_pick):
    if host_pick == guest_pick:
        return 'T'
    wins = {('R', 'S'), ('S', 'P'), ('P', 'R')}
    if (host_pick, guest_pick) in wins:
        return 'X'
    return 'O'


def _mention(user):
    return '<a href="tg://user?id={}">{}</a>'.format(user.id, user.first_name)


def register(dispatcher):
    dispatcher.add_handler(CommandHandler('rps', rps_new))
    dispatcher.add_handler(CallbackQueryHandler(rps_callback, pattern=r'^rps;'))
