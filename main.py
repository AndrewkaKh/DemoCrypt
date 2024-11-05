from telegram_bot import TelegramBot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, filters
from data_base import DataBase
from fetch_prices import CryptoPrices
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
import seaborn as sns


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

    text = f"Ваш портфель:\n"
    for crypto_name in crypto_prices.crypt.keys():
        tmp_balance = db.show_balance(user_id, crypto_name)
        if (tmp_balance != 0):
            text += f"{crypto_name}: {tmp_balance:.10f}\n"

    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


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
async def plot_selected_crypto_chart(update: Update, context: ContextTypes.DEFAULT_TYPE, crypto_name=None):
    await update.callback_query.message.delete()
    if not crypto_name:
        #await update.callback_query.message.delete()
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

    plt.rcParams['figure.figsize'] = 10, 8
    plt.rcParams['font.size'] = 12
    sns.set_style('darkgrid')

    buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close(fig)

    # Отправляем график как фото
    await update.callback_query.answer()
    await update.callback_query.message.reply_photo(buffer)

    # Кнопки "Назад" и "Обновить"
    back_button = InlineKeyboardButton("Назад", callback_data="charts")
    refresh_button = InlineKeyboardButton("Обновить", callback_data=f"show_chart_{crypto_name}")
    keyboard = [[refresh_button], [back_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем новое текстовое сообщение с кнопками "Назад" и "Обновить"
    await update.callback_query.message.reply_text("Выберите действие:", reply_markup=reply_markup)


"""@TelegramBot.AddCallbackQueryHandler(pattern="buy_crypto")
async def buy_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Добавляем кнопку "Назад" для возврата в главное меню
    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Покупка криптовалюты пока недоступна.", reply_markup=reply_markup)
"""

@TelegramBot.AddCallbackQueryHandler(pattern="buy_crypto")
async def initiate_crypto_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Отправляем сообщение с выбором валюты для обмена
    keyboard = [
        [InlineKeyboardButton(crypto, callback_data=f"buy_from_{crypto}") for crypto in crypto_prices._CRYPTO_NAMES]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Выберите валюту, которую хотите обменять:", reply_markup=reply_markup)

@TelegramBot.AddCallbackQueryHandler(pattern=r"^buy_from_(.+)")
async def select_target_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем выбранную валюту
    from_crypto = update.callback_query.data.split("_")[2]
    context.user_data["from_crypto"] = from_crypto

    # Предлагаем выбрать валюту, на которую будет произведен обмен
    keyboard = [
        [InlineKeyboardButton(crypto, callback_data=f"buy_to_{crypto}") for crypto in crypto_prices._CRYPTO_NAMES if crypto != from_crypto]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Выберите валюту, на которую хотите обменять:", reply_markup=reply_markup)

@TelegramBot.AddCallbackQueryHandler(pattern=r"^buy_to_(.+)")
async def enter_exchange_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем целевую валюту
    to_crypto = update.callback_query.data.split("_")[2]
    context.user_data["to_crypto"] = to_crypto

    user_id = update.effective_user.id

    # Запрашиваем у пользователя количество для обмена
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(f"На данный момент у вас есть {db.show_balance(user_id, context.user_data['from_crypto'])} {context.user_data['from_crypto']}\nВведите количество {context.user_data['from_crypto']} для обмена:")


    # Устанавливаем флаг ожидания ввода количества
    context.user_data["awaiting_amount"] = True

# Добавляем MessageHandler, который будет обрабатывать текстовые сообщения и проверять флаг `awaiting_amount`
@TelegramBot.AddMessageHandler(filters=filters.TEXT)
async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, ожидаем ли ввода количества
    if context.user_data.get("awaiting_amount", False):
        try:
            # Преобразуем введенный текст в число
            amount = float(update.message.text)
            context.user_data["amount"] = amount

            # Получаем курсы валют и рассчитываем сумму
            from_crypto = context.user_data["from_crypto"]
            to_crypto = context.user_data["to_crypto"]
            print(from_crypto, to_crypto)
            # Получаем курсы валют, проверяя, что цены корректно возвращаются
            from_quote = crypto_prices.crypt[from_crypto][-1]
            to_quote = crypto_prices.crypt[to_crypto][-1]
            print(from_quote, to_quote)
            # Убедитесь, что полученные значения не равны None
            if from_quote is None or to_quote is None:
                await update.message.reply_text("Ошибка при получении цен для обмена.")
                return

            calculated_amount = db._count_amount(amount, from_quote, to_quote)

            # Подтверждение обмена
            keyboard = [
                [
                    InlineKeyboardButton("Да", callback_data="confirm_exchange"),
                    InlineKeyboardButton("Нет", callback_data="buy_crypto")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Вы обменяете {amount} {from_crypto} на {calculated_amount:.6f} {to_crypto}. Подтвердить?",
                reply_markup=reply_markup
            )

            # Сбрасываем флаг ожидания
            context.user_data["awaiting_amount"] = False

        except ValueError:
            # Обработка некорректного ввода
            await update.message.reply_text("Пожалуйста, введите корректное число для количества.")

@TelegramBot.AddCallbackQueryHandler(pattern="confirm_exchange")
async def confirm_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Выполняем операцию обмена
    user_id = update.effective_user.id
    from_crypto = context.user_data["from_crypto"]
    to_crypto = context.user_data["to_crypto"]
    amount = context.user_data["amount"]

    # Получаем текущие котировки и рассчитываем целевую сумму
    from_quote = crypto_prices.crypt[from_crypto][-1]
    to_quote = crypto_prices.crypt[to_crypto][-1]

    if from_quote is None or to_quote is None:
        await update.callback_query.edit_message_text("Ошибка при получении цен для обмена.")
        return

    if db.change_crypto(user_id, amount, from_crypto, to_crypto, from_quote, to_quote):
        await update.callback_query.edit_message_text("Обмен выполнен успешно!")
    else:
        await update.callback_query.edit_message_text("Недостаточно средств для обмена.")

    # Удаляем временные данные
    context.user_data.clear()


if __name__ == "__main__":
    crypto_prices = CryptoPrices()
    crypto_prices.start()
    db = DataBase()
    bot.run()
    db.close()
