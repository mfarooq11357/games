import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, WebAppInfo
from telegram import MenuButtonWebApp
from telegram.ext import CallbackContext, CommandHandler

logger = logging.getLogger(__name__)

PUBLIC_BASE = os.environ.get(
    "RENDER_EXTERNAL_URL", "https://games-bot-8vhs.onrender.com"
).rstrip("/")

ARCADE_GAMES = {
    "snake": {
        "slug": "snake",
        "title": "Snake",
        "blurb": (
            "Steer the snake, eat apples, and don't hit your own body. "
            "The edges wrap around."
        ),
    },
    "rush": {
        "slug": "racer",
        "title": "Vector Rush",
        "blurb": (
            "Fly through the course, dodge obstacles, and use the phase dash "
            "when it is charged."
        ),
    },
    "helix": {
        "slug": "helix",
        "title": "Helix Smash",
        "blurb": (
            "Rotate around the tower and slip through the moving gaps. "
            "Charge a fireball to smash a block."
        ),
    },
}


def arcade_url(menu_key):
    game = ARCADE_GAMES[menu_key]
    return "{}/arcade?game={}".format(PUBLIC_BASE, game["slug"])


def play_keyboard(menu_key, chat_type):
    url = arcade_url(menu_key)
    if chat_type == "private":
        play = InlineKeyboardButton(
            "Play in Telegram", web_app=WebAppInfo(url=url)
        )
    else:
        play = InlineKeyboardButton("Play", url=url)
    return InlineKeyboardMarkup([
        [play],
        [InlineKeyboardButton("Back to Games", callback_data="menu;back")],
    ])


def install_menu_button(bot):
    bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Arcade",
            web_app=WebAppInfo(url=PUBLIC_BASE + "/arcade"),
        )
    )


def _send_game(update: Update, menu_key):
    game = ARCADE_GAMES[menu_key]
    chat = update.effective_chat
    update.effective_message.reply_text(
        "<b>{}</b>\n\n{}".format(game["title"], game["blurb"]),
        parse_mode=ParseMode.HTML,
        reply_markup=play_keyboard(menu_key, chat.type if chat else "private"),
    )


def arcade_menu(update: Update, context: CallbackContext):
    _send_game(update, "snake")


def snake_cmd(update: Update, context: CallbackContext):
    _send_game(update, "snake")


def rush_cmd(update: Update, context: CallbackContext):
    _send_game(update, "rush")


def helix_cmd(update: Update, context: CallbackContext):
    _send_game(update, "helix")


def register(dispatcher):
    dispatcher.add_handler(CommandHandler("arcade", arcade_menu))
    dispatcher.add_handler(CommandHandler("snake", snake_cmd))
    dispatcher.add_handler(CommandHandler("rush", rush_cmd))
    dispatcher.add_handler(CommandHandler("helix", helix_cmd))
    try:
        install_menu_button(dispatcher.bot)
    except Exception:
        logger.exception("Could not set the arcade menu button")
