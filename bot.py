from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = ''
CHANNEL_ID =

temp_orders = {}
TABLES = {
    '1': 'Стол для 1-3 персон',
    '2': 'Стол для 3-6 персон',
    '3': 'Стол для 7 и более персон',
    '4': 'Банкет с предзаказом'
}
AVAILABLE_HOURS = list(range(12, 22))


def get_available_dates():
    today = datetime.now().date()
    dates = []
    for i in range(1, 15):
        date = today + timedelta(days=i)
        dates.append(date)
    return dates


def format_date(date):
    months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн',
              'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
    return f"{date.day} {months[date.month - 1]}"


def format_date_full(date):
    return date.strftime('%d.%m.%Y')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    temp_orders[user_id] = {
        'table': None,
        'date': None,
        'time': None,
    }

    keyboard = [
        [InlineKeyboardButton("📅 Выбрать дату", callback_data='choose_date')],
    ]

    await update.message.reply_text(
        f"👋 Привет, {update.effective_user.first_name}, выберите дату бронирования:\n\n",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    available_dates = get_available_dates()

    keyboard = []
    row = []

    for i, date in enumerate(available_dates):
        date_str = format_date(date)
        callback_data = f'date_{date.strftime("%Y%m%d")}'
        row.append(InlineKeyboardButton(date_str, callback_data=callback_data))

        if len(row) == 3 or i == len(available_dates) - 1:
            keyboard.append(row)
            row = []

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])

    await query.edit_message_text(
        "📅 *Выберите дату бронирования:*\n\n"
        "🗓️ Доступны даты с завтрашнего дня на 2 недели вперёд:\n\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def select_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    date_str = query.data.split('_')[1]
    selected_date = datetime.strptime(date_str, '%Y%m%d').date()

    temp_orders[user_id]['date'] = selected_date

    await show_time_selection(query, user_id, selected_date)


async def show_time_selection(query, user_id, selected_date):
    keyboard = []
    row = []

    for hour in AVAILABLE_HOURS:
        time_str = f"{hour}:00"
        callback_data = f'time_{hour}'
        row.append(InlineKeyboardButton(time_str, callback_data=callback_data))

        if len(row) == 4:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])

    await query.edit_message_text(
        f"📅 *Дата:* {format_date_full(selected_date)}\n\n"
        f"⏰ *Выберите время бронирования:*\n\n"
        f"🕐 Доступное время: с 12:00 до 21:00",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    hour = int(query.data.split('_')[1])

    temp_orders[user_id]['time'] = hour

    selected_date = temp_orders[user_id].get('date')

    keyboard = []
    for num, desc in TABLES.items():
        keyboard.append([InlineKeyboardButton(f"{desc}", callback_data=f'table_{num}')])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])

    await query.edit_message_text(
        f"📅 *Дата:* {format_date_full(selected_date)}\n\n"
        f"⏰ *Время:* {hour}:00\n\n"
        f"🍽️ *Выберите стол:*\n\n"
        f"Уточните количество персон:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def select_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    table_num = query.data.split('_')[1]

    temp_orders[user_id]['table'] = {
        'number': table_num,
        'description': TABLES[table_num]
    }

    selected_date = temp_orders[user_id].get('date')
    selected_time = temp_orders[user_id].get('time')

    await query.edit_message_text(
        f"📅 *Дата:* {format_date_full(selected_date)}\n\n"
        f"⏰ *Время:* {selected_time}:00\n\n"
        f"✅ *Выбран стол:* {TABLES[table_num]}\n\n",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Отправить бронирование", callback_data='send_reservation')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back')]
        ]),
        parse_mode='Markdown'
    )


async def send_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    order = temp_orders.get(user_id, {})
    user = query.from_user

    selected_date = order['date']
    selected_time = order.get('time')

    channel_msg = f"🆕 *НОВОЕ БРОНИРОВАНИЕ!*\n\n"
    channel_msg += f"👤 Клиент: {user.first_name} {user.last_name or ''}\n"
    channel_msg += f"🆔 ID: {user.id}\n"
    channel_msg += f"📱 Username: @{user.username or 'нет'}\n\n"
    channel_msg += f"📅 *ДАТА:* {format_date_full(selected_date)}\n"
    channel_msg += f"⏰ *Время:* {selected_time}:00\n"
    channel_msg += f"🍽️ *СТОЛИК:* {order['table']['description']}\n"
    channel_msg += f"\n⏰ Время отправления бронирования: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=channel_msg,
            parse_mode='Markdown'
        )
        print(f"✅ Бронирование отправлено в канал {CHANNEL_ID}")

        client_msg = (
            "✅ *Бронирование отправлено!*\n\n"
            "🎉 *Спасибо за выбор нашего ресторана!*\n\n"
            f"📅 *Дата:* {format_date_full(selected_date)}\n"
            f"⏰ *Время:* {selected_time}:00\n"
            f"🍽️ *Стол:* {order['table']['description']}\n\n"
            "✨ Скоро с вами свяжутся для подтверждения.\n\n"
            "🤗 *Ждём вас!*"
        )

        await query.edit_message_text(client_msg, parse_mode='Markdown')
        del temp_orders[user_id]

    except Exception as e:
        error_msg = f"❌ Ошибка при отправке в канал!\n\n"
        error_msg += f"Проверьте:\n"
        error_msg += f"1. Бот добавлен в канал? (да)\n"
        error_msg += f"2. Бот имеет права администратора? (да)\n"
        error_msg += f"3. Правильный ли ID канала? (сейчас: {CHANNEL_ID})\n"
        error_msg += f"\nОшибка: {e}"

        await query.edit_message_text(error_msg)
        print(f"Ошибка: {e}")


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    temp_orders[user_id] = {
        'table': None,
        'date': None,
        'time': None,
    }

    keyboard = [
        [InlineKeyboardButton("📅 Выбрать дату", callback_data='choose_date')],
    ]

    await query.edit_message_text(
        f"👋 Привет, {query.from_user.first_name}, выберите дату бронирования:\n\n",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))

    app.add_handler(CallbackQueryHandler(choose_date, pattern='choose_date'))
    app.add_handler(CallbackQueryHandler(select_date, pattern='date_'))
    app.add_handler(CallbackQueryHandler(select_time, pattern='time_'))
    app.add_handler(CallbackQueryHandler(select_table, pattern='table_'))
    app.add_handler(CallbackQueryHandler(send_reservation, pattern='send_reservation'))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern='back'))

    print("🤖 Бот запущен и готов к работе!")
    print("📅 Доступные даты: с завтрашнего дня на 2 недели вперёд")

    app.run_polling()


if __name__ == '__main__':
    main()