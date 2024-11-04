from telegram_bot import TelegramBot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from data_base import DataBase
from fetch_prices import CryptoPrices
import matplotlib.pyplot as plt
import io
from telegram import InputMediaPhoto
from datetime import datetime, timedelta


bot = TelegramBot("7832412416:AAFKYWoHnpL9ehHcZy8LlyWeyTxq5b8Ap30")
db = DataBase()  # Создаем экземпляр базы данных


@TelegramBot.AddCommandHandler("start")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.add_user(user_id)  # Добавляем пользователя в базу данных
    await update.message.reply_text("Привет! Добро пожаловать в нашего криптобота!")
    await show_menu(update)


@TelegramBot.AddCommandHandler("menu")
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_menu(update)


async def show_menu(update):
    # Создаем кнопки для меню
    keyboard = [
        [InlineKeyboardButton("Профиль", callback_data="profile")],
        [InlineKeyboardButton("Просмотр графиков криптовалют", callback_data="charts")],
        [InlineKeyboardButton("Покупка криптовалюты", callback_data="buy_crypto")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Проверяем, вызвано ли show_menu из сообщения или callback_query
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("Выберите действие:", reply_markup=reply_markup)


@TelegramBot.AddCallbackQueryHandler(pattern="back_to_menu")
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Возвращаем пользователя в главное меню
    await update.callback_query.answer()
    await show_menu(update)

@TelegramBot.AddCallbackQueryHandler(pattern="profile")
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usd_balance = db.show_balance(user_id, "USD_T")
    # Добавляем кнопку "Назад" для возврата в главное меню
    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(f"Ваш баланс:\nUSD_T: {usd_balance:.2f} USDT", reply_markup=reply_markup)


@TelegramBot.AddCallbackQueryHandler(pattern="charts")
async def show_chart_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []

    for crypto_name in crypto_prices.crypt.keys():
        button_text = f"{crypto_name}/USDT - USDT/{crypto_name}"
        callback_data = f"show_chart_{crypto_name}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton("Назад", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()  # Завершаем callback query
    await update.callback_query.edit_message_text(
        text="Выберите криптовалюту для отображения графика:",
        reply_markup=reply_markup
    )


@TelegramBot.AddCallbackQueryHandler(pattern="back_to_menu_charts")
async def back_to_menu_charts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await show_chart_menu(update)


@TelegramBot.AddCallbackQueryHandler(pattern="show_chart_")
async def plot_selected_crypto_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    crypto_name = update.callback_query.data.split("_")[-1]

    if crypto_name not in crypto_prices.crypt:
        await update.callback_query.answer("Криптовалюта не найдена.")
        return

    prices = list(crypto_prices.crypt[crypto_name])
    timestamps = [datetime.now() - timedelta(seconds=i * CryptoPrices.interval_) for i in range(len(prices))][::-1]

    fig, ax = plt.subplots(2, 1, figsize=(10, 8))
    ax[0].plot(timestamps, prices, label=f"{crypto_name}/USDT")
    ax[0].set_title(f"Курс {crypto_name}/USDT за последние 24 часа")
    ax[0].set_xlabel("Время")
    ax[0].set_ylabel("Цена")
    ax[0].legend()

    inverted_prices = [1 / price for price in prices if price > 0]
    ax[1].plot(timestamps, inverted_prices, label=f"USDT/{crypto_name}")
    ax[1].set_title(f"Курс USDT/{crypto_name} за последние 24 часа")
    ax[1].set_xlabel("Время")
    ax[1].set_ylabel("Цена")
    ax[1].legend()

    buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close(fig)

    # Создаем кнопку "Назад" для возврата к выбору графиков
    keyboard = [
        [InlineKeyboardButton("Назад", callback_data="back_to_menu_charts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Обновляем сообщение с изображением графика и кнопкой "Назад"
    await update.callback_query.answer()
    await update.callback_query.edit_message_media(
        media=InputMediaPhoto(buffer),
        reply_markup=reply_markup
    )


@TelegramBot.AddCallbackQueryHandler(pattern="buy_crypto")
async def buy_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Добавляем кнопку "Назад" для возврата в главное меню
    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Покупка криптовалюты пока недоступна.", reply_markup=reply_markup)


if __name__ == "__main__":
    crypto_prices = CryptoPrices()
    crypto_prices.start()
    bot.run()
    db.close()