import logging

from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext

from utils import send_async, display_name

logger = logging.getLogger(__name__)

GAMES_MENU = [
    [
        InlineKeyboardButton("\U0001f0cf UNO", callback_data="menu;uno"),
        InlineKeyboardButton("\u26ab Go", callback_data="menu;go"),
    ],
    [
        InlineKeyboardButton("\u274c Tic-Tac-Toe", callback_data="menu;ttt"),
        InlineKeyboardButton("\U0001f534 Connect Four", callback_data="menu;c4"),
    ],
    [
        InlineKeyboardButton("\u270a Rock-Paper-Scissors", callback_data="menu;rps"),
        InlineKeyboardButton("\U0001f52b Russian Roulette", callback_data="menu;rr"),
    ],
]


GAME_INFO = {
    'uno': (
        "\U0001f0cf <b>UNO - Card Game</b>\n\n"
        "Play the classic UNO card game with friends!\n\n"
        "<b>Commands (use in group chat):</b>\n"
        "/uno - Start a new game\n"
        "/uno_join - Join a game\n"
        "/uno_start - Start the game\n"
        "/uno_leave - Leave the game\n"
        "/uno_kick - Kick a player\n"
        "/uno_skip - Skip current player\n"
        "/uno_close - Close lobby\n"
        "/uno_open - Open lobby\n"
        "/uno_kill - Terminate game\n\n"
        "<i>Min 2 players. Play cards via inline query (@botname).</i>"
    ),
    'go': (
        "\u26ab <b>Go - Board Game</b>\n\n"
        "Play the ancient strategy game Go!\n\n"
        "<b>Commands (use in group chat):</b>\n"
        "/go - Start a new 9x9 game\n"
        "/go 13 - Start a 13x13 game\n"
        "/go 19 - Start a 19x19 game\n"
        "/go_join - Join a game\n"
        "/go_place a1 - Place a stone\n"
        "/go_pass - Pass your turn\n"
        "/go_show - Show the board\n"
        "/go_kill - End the game\n\n"
        "<i>2 players. Both pass = game over.</i>"
    ),
    'ttt': (
        "\u274c <b>Tic-Tac-Toe</b>\n\n"
        "Classic 3x3 grid game!\n\n"
        "<b>How to play:</b>\n"
        "/ttt - Create a new game\n"
        "Other player clicks <b>Join</b>\n"
        "Take turns clicking the grid!\n\n"
        "<i>2 players. First to get 3 in a row wins!</i>"
    ),
    'c4': (
        "\U0001f534 <b>Connect Four</b>\n\n"
        "Drop discs to connect four in a row!\n\n"
        "<b>How to play:</b>\n"
        "/c4 - Create a new game\n"
        "Other player clicks <b>Join</b>\n"
        "Click column numbers to drop discs!\n\n"
        "<i>2 players. 6 rows x 7 columns.</i>"
    ),
    'rps': (
        "\u270a <b>Rock-Paper-Scissors</b>\n\n"
        "Best of 5 rounds!\n\n"
        "<b>How to play:</b>\n"
        "/rps - Create a new game\n"
        "Other player clicks <b>Join</b>\n"
        "Both players pick simultaneously!\n\n"
        "<i>2 players. First to 3 wins!</i>"
    ),
    'rr': (
        "\U0001f52b <b>Russian Roulette</b>\n\n"
        "Test your luck!\n\n"
        "<b>How to play:</b>\n"
        "/rr - Create a new game\n"
        "Other player clicks <b>Join</b>\n"
        "Take turns picking a chamber!\n\n"
        "<i>2 players. Don't hit the bullet!</i>"
    ),
}


def show_menu(update: Update, context: CallbackContext):
    # Handle UNO deep-link: /start select
    if context.args and context.args[0] == 'select':
        from shared_vars import gm
        from internationalization import _
        user_id = update.message.from_user.id
        if user_id in gm.userid_players:
            players = gm.userid_players[user_id]
            groups = []
            for player in players:
                title = player.game.chat.title
                if player == gm.userid_current.get(user_id):
                    title = '- %s -' % player.game.chat.title
                groups.append(
                    [InlineKeyboardButton(text=title,
                                          callback_data=str(player.game.chat.id))]
                )
            send_async(context.bot, update.message.chat_id,
                       text=_('Please select the group you want to play in.'),
                       reply_markup=InlineKeyboardMarkup(groups))
            return

    text = (
        "\U0001f3ae <b>Game Bot - Choose a Game!</b>\n\n"
        "Welcome! I host multiple games you can play with friends in group chats.\n"
        "Tap a game below to see how to play:"
    )
    update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(GAMES_MENU)
    )


def menu_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(';')

    if len(data) < 2:
        query.answer()
        return

    game_key = data[1]
    if game_key == 'back':
        query.edit_message_text(
            "\U0001f3ae <b>Game Bot - Choose a Game!</b>\n\n"
            "Welcome! I host multiple games you can play with friends in group chats.\n"
            "Tap a game below to see how to play:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(GAMES_MENU)
        )
        query.answer()
        return

    info = GAME_INFO.get(game_key)
    if info:
        back_button = [[InlineKeyboardButton("\u25c0 Back to Games", callback_data="menu;back")]]
        query.edit_message_text(
            info,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    query.answer()


def register(dispatcher):
    dispatcher.add_handler(CommandHandler('games', show_menu))
    dispatcher.add_handler(CallbackQueryHandler(menu_callback, pattern=r'^menu;'))
