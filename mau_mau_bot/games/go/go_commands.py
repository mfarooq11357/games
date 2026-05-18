import html
import logging
import random

from telegram import Update, ParseMode
from telegram.ext import CommandHandler, CallbackContext

from games.go.game_handler import GoGameHandler, GameHandlerException, GO_PROVERBS
from games.go.go_screenshot import take_in_memory_screenshot
from games.go.exceptions import KoException

logger = logging.getLogger(__name__)

go_handler = GoGameHandler()


def go_new(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.message.from_user

    if update.message.chat.type == 'private':
        update.message.reply_text("Go must be played in a group chat!")
        return

    board_size = 9
    if context.args:
        try:
            board_size = int(context.args[0])
        except ValueError:
            pass

    try:
        go_handler.new_game(chat_id, user.id, user.first_name, board_size)
        update.message.reply_text(
            "<b>New Go game created!</b> Another player can join with /go_join",
            parse_mode=ParseMode.HTML
        )
    except GameHandlerException as e:
        update.message.reply_text(html.escape(str(e)))


def go_join(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.message.from_user

    try:
        game = go_handler.join(chat_id, user.id, user.first_name)
        update.message.reply_text("<b>Let the Go game begin!</b>", parse_mode=ParseMode.HTML)
        _show_board(update, context, game)
        _show_turn(update, game)
    except GameHandlerException as e:
        update.message.reply_text(html.escape(str(e)))


def go_place(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.message.from_user

    if not context.args:
        update.message.reply_text("Please supply coordinates (e.g. <code>/go_place a1</code>)",
                                  parse_mode=ParseMode.HTML)
        return

    coord = context.args[0]
    try:
        game = go_handler.place_stone(chat_id, user.id, coord)
        _show_board(update, context, game)
        _show_turn(update, game)
    except KoException as e:
        update.message.reply_text(html.escape(str(e)))
        update.message.reply_text("<i>If you don't like Ko don't Play Go.</i>",
                                  parse_mode=ParseMode.HTML)
    except (GameHandlerException, Exception) as e:
        update.message.reply_text(html.escape(str(e)))


def go_pass(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.message.from_user

    try:
        game = go_handler.pass_turn(chat_id, user.id)
        if game.is_game_over:
            go_handler.remove_game(chat_id)
            update.message.reply_text("The game is over. Well played!")
            return
        update.message.reply_text("{} passed".format(html.escape(user.first_name)),
                                  parse_mode=ParseMode.HTML)
        _show_board(update, context, game)
        _show_turn(update, game)
    except GameHandlerException as e:
        update.message.reply_text(html.escape(str(e)))


def go_show(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    game = go_handler.get_game(chat_id)
    if game is None:
        update.message.reply_text("No Go game running. Start one with /go")
        return
    _show_board(update, context, game)


def go_kill(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    game = go_handler.get_game(chat_id)
    if game is None:
        update.message.reply_text("No Go game running in this chat.")
        return
    go_handler.remove_game(chat_id)
    update.message.reply_text("Go game terminated.")


def go_proverb(update: Update, context: CallbackContext):
    proverb = random.choice(GO_PROVERBS)
    update.message.reply_text('"{}"'.format(proverb))


def _show_board(update, context, game):
    try:
        image = take_in_memory_screenshot(game)
        context.bot.send_photo(update.effective_chat.id, photo=image)
    except Exception as e:
        update.message.reply_text(str(e))


def _show_turn(update, game):
    if game.current_player is None:
        return
    name = html.escape(game.current_player.name)
    color = game.current_player.color
    update.message.reply_text(
        "It is {}'s ({}) turn".format(name, color),
        parse_mode=ParseMode.HTML
    )


def register(dispatcher):
    dispatcher.add_handler(CommandHandler('go', go_new))
    dispatcher.add_handler(CommandHandler('go_join', go_join))
    dispatcher.add_handler(CommandHandler('go_place', go_place))
    dispatcher.add_handler(CommandHandler('go_pass', go_pass))
    dispatcher.add_handler(CommandHandler('go_show', go_show))
    dispatcher.add_handler(CommandHandler('go_kill', go_kill))
    dispatcher.add_handler(CommandHandler('go_proverb', go_proverb))
