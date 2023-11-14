import telebot
import threading
import sqlite3
import callbacks
import commmands
import utils

from utils import update_floppas


tg_token = '6627394164:AAHOSe5nb6ZYM3Tbt2VnvXuEXh5S4-898hs'

bot = telebot.TeleBot(tg_token)


@bot.message_handler(commands=['start'])
def main_start_message(message):
    commmands.start_message(message)


@bot.message_handler(commands=['cmd'])
def main_cmd(message):
    commmands.cmd_help(message)


@bot.message_handler(commands=['buy'])
def buy_floppa(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        bot.send_message(chat_id, '*Вы уже приобрели Шлёпу!*😸\n\n/myfloppa - посмотреть потребности Шлёпы.',
                         parse_mode='Markdown')
    else:
        bot.send_message(chat_id, '*Введите имя* для вашего Каракала😼:', parse_mode='Markdown')
        bot.register_next_step_handler(message, lambda msg: save_floppa_name(msg, user_id, chat_id, username))

    conn.close()


def save_floppa_name(message, user_id, chat_id, username):
    floppa_name = message.text

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, user_id INTEGER,  username TEXT,'
                       ' floppa_name TEXT, coin INTEGER, age INTEGER, hunger INTEGER, waste INTEGER, boredom INTEGER,'
                       'sleeping INTEGER DEFAULT 0, wait_interval INTEGER DEFAULT 60)')
    conn.commit()

    cursor.execute(
            'INSERT INTO users (user_id, username, floppa_name, coin, age,  hunger, waste, boredom) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, username, floppa_name, 0, 0, 100, 100, 100))
    conn.commit()

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute(
        'CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY, user_id INTEGER, item_name TEXT, effect TEXT)')
    conn.commit()

    conn.close()

    bot.send_message(chat_id,
                         f'*Поздравляем с приобретением Шлёпы, {username}!*😼 Вашего (вашу) Шлёпу зовут {floppa_name}.'
                         f'\n*Введите команду /myfloppa* , чтобы посмотреть потребности Шлёпы.🤔\nВведите \cmd ,'
                         f'чтобы узнать больше команд. 📋', parse_mode='Markdown')

    conn.close()


@bot.message_handler(commands=['createshopdb'])
def main_create_shop(message):
    utils.create_shop_db()


@bot.message_handler(commands=['shop'])
def main_shop(message):
    commmands.shop(message)


@bot.message_handler(commands=['buy_item'])
def main_buy_item(message):
    commmands.buy_item(message)


@bot.message_handler(commands=['use_item'])
def main_use_item(message):
    commmands.use_item(message)


@bot.message_handler(commands=['inventory', 'inv'])
def main_inv(message):
    commmands.inventory(message)


@bot.message_handler(commands=['myfloppa'])
def main_myfloppa(message):
    commmands.my_floppa_info(message)


@bot.message_handler(commands=['feed'])
def main_feed(message):
    commmands.feed_floppa(message)


@bot.message_handler(commands=['clean'])
def main_clean(message):
    commmands.clean_floppa(message)


@bot.message_handler(commands=['play'])
def main_play(message):
    commmands.play_with_floppa(message)


@bot.message_handler(commands=['work'])
def main_work(message):
    commmands.work_floppa(message)


@bot.message_handler(commands=['setage'])
def main_set_age(message):
    commmands.set_age(message)


@bot.message_handler(commands=['sleep'])
def block_cmd(message):
    commmands.sleep_command(message)


@bot.message_handler(commands=['unsleep'])
def unblock_cmd(message):
    commmands.unsleep_command(message)


@bot.message_handler(commands=['caz', 'cas'])
def main_start_casino(message):
    commmands.start_casino(message)


@bot.message_handler(commands=['cuzbas'])
def main_create_cas_base(message):
    commmands.create_cas_base(message)


@bot.callback_query_handler(func=lambda call: True)
def main_inline_buttons(call):
    
    if call.data == 'buy_chips':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет идти в казино сейчас..😵‍💫'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введи сумму которую хотите обменять на фишки.🎰\n*1 коин = 1 фишка*',
                                 parse_mode='Markdown')
                bot.register_next_step_handler(call.message, utils.short_callback_buy_chips)

    if call.data == 'sell_chips':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет идти в казино сейчас 😵‍💫'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введи количество фишек, которые вы хотите заменить на флоппо-коины.💰'
                                          '\n*1 коин = 1 фишка*', parse_mode='Markdown')
                bot.register_next_step_handler(call.message, utils.short_callback_sell_chips)

    if call.data == 'red':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils.red_casino)

    if call.data == 'black':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils.black_casino)

    if call.data == 'zero':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils.zero_casino)

    if call.data == 'even':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils.even_casino)

    if call.data == 'odd':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils.odd_casino)

    if call.data == 'st':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils.st_casino)

    if call.data == 'nd':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils.nd_casino)

    if call.data == 'rd':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils.rd_casino)

    if call.data == '34':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils._1_34)

    if call.data == '35':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils._2_35)

    if call.data == '36':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils._3_36)

    if call.data == '1-18':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils._1_18)

    if call.data == '19-36':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn_users = sqlite3.connect('users-floppa.sql')
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user_check = cursor_users.fetchone()

        if existing_user_check[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
        else:
            if existing_user_check[8] < 20:
                bot.send_message(chat_id, f'*Шлёпа в тильте!*, Шлёпа не хочет играть в казино сейчас..😩'
                                          f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            else:
                bot.send_message(chat_id, 'Введите ставку 🃏')
                bot.register_next_step_handler(call.message, utils._19_36)

    callbacks.handle_inline_buttons(call)


update_thread = threading.Thread(target=update_floppas)
update_thread.start()

bot.polling(none_stop=True)
