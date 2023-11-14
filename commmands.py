import utils
import sqlite3
import json
import config
import random
import time

from datetime import datetime, timedelta
from config import bot, wait_time, sleeping
from telebot import types


def start_message(message):

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Команды', callback_data='buyflopp'))

    bot.send_message(message.chat.id, 'Привет! Шлёпа рад тебя видеть!👋😼 *Введи команду /cmd* для того, чтобы узнать '
                                      'как получить кота и ухаживать за своим Шлёпой!📄\nПосле приобретения обязательно '
                                      'следите за Шлёпой😻: кормите его, ухаживайте за ним и конечно играйтесь с ним, '
                                      '*иначе вы рискуете его потерять*😿', reply_markup=markup, parse_mode='Markdown')

    with open ('floppa-caracal.gif', 'rb') as animation_small_floppa:
        bot.send_animation(message.chat.id, animation_small_floppa)


def cmd_help(message):
    bot.send_message(message.chat.id, '<b>СПИСОК ВСЕХ КОМАНД📋:</b>\n\n/buy - купить Шлёпу😼\n/feed - Покормить Шлёпу🥟\n'
                                      '/clean - Вымыть Шлёпу🛁\n/play - Поиграть со Шлёпой🧸\n/myfloppa - Узнать о '
                                      'потребностях каракала🐈\n\n/work - сходить на работу и заработать флоппо-коины💰'
                                      '\n/shop - открыть магазин🏪\n/buy_item [номер предмета в магазине] - купить пре'
                                      'дмет в магазине🛒\n/inventory - открыть рюкзак с предметами🎒\n/use_item [номер '
                                      'предмета в инвентаре] - использовать предмет из рюкзака📦'
                                      '\n/sleep - отправить Шлёпу спать 😴\n/unsleep - разубдить Шлёпу 🛏'
                                      '\n/caz /cas - открыть меню казино 🎰',
                     parse_mode='html')


def shop(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute('SELECT sleeping FROM users WHERE user_id = ?', (user_id,))
    sleep_check = cursor.fetchone()

    if sleep_check[0] == 1:
        bot.send_message(chat_id,
                         'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                         parse_mode='Markdown')
        return

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:

        cursor.execute('SELECT waste FROM users WHERE user_id = ?', (user_id,))
        enough_clean = cursor.fetchone()

        if enough_clean[0] < 20:
            bot.send_message(chat_id, 'Вашего Шлёпу вышвырнули из магазина!😿 *Помойте его, он слишком грязный.😾*'
                                      '\n\n*/clean - помыть*', parse_mode='Markdown')
            return

        conn_1 = sqlite3.connect('shop-items.db')
        cursor_1 = conn_1.cursor()

        cursor_1.execute('SELECT id, name, price FROM items')
        items = cursor_1.fetchall()

        shop_message = "Доступные предметы в магазине🛍:\n"
        for item_id, name, price in items:
            shop_message += f"{item_id}. {name} - {price} флоппо-коинов💰\n"

        bot.send_message(chat_id, shop_message)

        conn_1.close()

    else:
        bot.send_message(chat_id,
                         "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\n*Введите "
                         "команду /buy.*", parse_mode='Markdown')

    conn.close()


def buy_item(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        item_id = int(message.text.split()[1])
    except (ValueError, IndexError):
        bot.send_message(message.chat.id, "Правильное использование команды✅: */buy_item [номер предмета]*",
                         parse_mode='Markdown')
        return

    conn_1 = sqlite3.connect('users-floppa.sql')
    cursor_1 = conn_1.cursor()

    cursor_1.execute('SELECT sleeping FROM users WHERE user_id = ?', (user_id,))
    sleep_check = cursor_1.fetchone()

    if sleep_check[0] == 1:
        bot.send_message(chat_id,
                         'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                         parse_mode='Markdown')
        return

    cursor_1.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor_1.fetchone()

    if existing_user:

        cursor_1.execute('SELECT waste FROM users WHERE user_id = ?', (user_id,))
        enough_clean = cursor_1.fetchone()

        if enough_clean[0] < 20:
            bot.send_message(chat_id, 'Вашего Шлёпу вышвырнули из магазина!😿 *Помойте его, он слишком грязный.😾*'
                                      '\n\n*/clean - помыть*', parse_mode='Markdown')
            return

        conn = sqlite3.connect('shop-items.db')
        cursor = conn.cursor()

        cursor.execute('SELECT name, price, effect FROM items WHERE id = ?', (item_id,))
        item = cursor.fetchone()

        if item:

            username = message.from_user.username

            cursor_1.execute('SELECT coin FROM users WHERE user_id = ?', (user_id,))
            user_coin = cursor_1.fetchone()[0]

            # Проверка наличия предмета в инвентаре
            cursor_1.execute('SELECT item_name FROM inventory WHERE user_id = ? AND item_name = ?', (user_id, item[0]))
            existing_item = cursor_1.fetchone()

            if user_coin >= item[1] and not existing_item:
                # Обновляем баланс пользователя
                cursor_1.execute('UPDATE users SET coin = coin - ? WHERE user_id = ?', (item[1], user_id))
                conn_1.commit()

                # Добавляем предмет в инвентарь пользователя
                cursor_1.execute('INSERT INTO inventory (user_id, item_name, effect) VALUES (?, ?, ?)',
                                 (user_id, item[0], item[2]))
                conn_1.commit()

                bot.send_message(chat_id, f"Поздравляем, {username}! *Вы приобрели {item[0]}* за {item[1]} "
                                                  f"флоппо-коинов.💰", parse_mode='Markdown')
            elif existing_item:
                bot.send_message(chat_id, f"*У вас уже есть {item[0]}* в рюкзаке.\n/inv - проверить рюкзак.🎒",
                                 parse_mode='Markdown')
            else:
                bot.send_message(chat_id, f"*У вас недостаточно флоппо-коинов* для покупки {item[0]}.🛒\n"
                                                  f"Сходите на работу, чтобы стать богаче (/work).\n/myfloppa - "
                                                  f"*проверить баланс коинов.*💰",
                                 parse_mode='Markdown')

        else:
            bot.send_message(chat_id, "*Предмет не найден.*😾", parse_mode='Markdown')

        conn.close()

    else:
        bot.send_message(chat_id,
                         "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\nВведите "
                         "команду /buy.", parse_mode='Markdown')

    conn_1.close()


# Команда для использования предмета из инвентаря
def use_item(message):
    try:
        item_id = int(message.text.split()[1])
    except (ValueError, IndexError):
        bot.send_message(message.chat.id, "Правильное использование команды✅: */use_item [номер предмета]*",
                         parse_mode='Markdown')
        return

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    user_id = message.from_user.id
    chat_id = message.chat.id

    cursor.execute('SELECT sleeping FROM users WHERE user_id = ?', (user_id,))
    sleep_check = cursor.fetchone()

    if sleep_check[0] == 1:
        bot.send_message(chat_id,
                         'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                         parse_mode='Markdown')
        return

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.execute('SELECT item_name, effect FROM inventory WHERE user_id = ?', (user_id,))
        inventory_items = cursor.fetchall()

        if item_id <= 0 or item_id > len(inventory_items):
            bot.send_message(chat_id, "*Неправильный номер предмета либо ваш рюкзак пуст.* ❌",
                             parse_mode='Markdown')
            return

        item_name, item_effect = inventory_items[item_id - 1]

        effect = json.loads(item_effect)

        if item_name == 'Бетономешалка':
            bot.send_message(chat_id, '❌Бетономешалка - это пассивный предмет. Благодаря ей вы будете получать'
                                      ' больше флоппо-коинов на работе.')
            return

        if "hunger" in effect:
            cursor.execute('UPDATE users SET hunger = ? WHERE user_id = ?', (effect["hunger"], user_id))
        if "waste" in effect:
            cursor.execute('UPDATE users SET waste = ? WHERE user_id = ?', (effect["waste"], user_id))
        if "boredom" in effect:
            cursor.execute('UPDATE users SET boredom = ? WHERE user_id = ?', (effect["boredom"], user_id))

        if 'coin_range' in effect:
            coin_range = effect['coin_range']
            random_coin = random.randint(coin_range[0], coin_range[1])
            cursor.execute('UPDATE users SET coin = coin + ? WHERE user_id = ?',
                           (random_coin, user_id))

        # Удаление использованного предмета из инвентаря
        if item_name != 'Бетономешалка':
            cursor.execute('DELETE FROM inventory WHERE user_id = ? AND item_name = ?', (user_id, item_name))
            conn.commit()

        bot.send_message(chat_id, f"*Вы использовали {item_name}. ✅*", parse_mode='Markdown')
        if 'coin_range' in effect:
            bot.send_message(chat_id, f'Вы получили {random_coin} монет.\n/myfloppa - проверить кошелёк')

    else:
        bot.send_message(chat_id,
                         "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\nВведите "
                         "команду /buy.", parse_mode='Markdown')

    conn.close()


# Обработчик команды /sleep
def sleep_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        # Устанавливаем интервал времени в 240 секунд (4 минуты)
        cursor.execute('UPDATE users SET wait_interval = 240, sleeping = 1 WHERE user_id = ?', (user_id,))
        conn.commit()

        bot.send_message(chat_id, "*Шлёпа засыпает😼💤.*\n\nВы не сможете использовать большинство команд, а нужды будут "
                                  "уменьшены.", parse_mode='Markdown')

    else:
        bot.send_message(chat_id,
                         "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\nВведите "
                         "команду /buy.", parse_mode='Markdown')

    conn.close()


def unsleep_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        # Устанавливаем интервал времени обратно в 60 секунд (1 минута) и снимаем флаг сна
        cursor.execute('UPDATE users SET wait_interval = 60, sleeping = 0 WHERE user_id = ?', (user_id,))
        conn.commit()

        bot.send_message(chat_id, "*Шлёпа проснулся.*😼🥱 Тщательно ухаживайте за котом. ", parse_mode='Markdown')

    else:
        bot.send_message(chat_id,
                         "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\nВведите "
                         "команду /buy.", parse_mode='Markdown')
    conn.close()


# Команда для просмотра инвентаря пользователя
def inventory(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute('SELECT sleeping FROM users WHERE user_id = ?', (user_id,))
    sleep_check = cursor.fetchone()

    if sleep_check[0] == 1:
        bot.send_message(chat_id,
                         'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                         parse_mode='Markdown')
        return

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.execute('SELECT item_name, effect FROM inventory WHERE user_id = ?', (user_id,))
        inventory_items = cursor.fetchall()

        inventory_message = "Ваш рюкзак🎒:\n"
        for item_name, effect_json in inventory_items:
            effect = json.loads(effect_json)
            inventory_message += f"{item_name}\n"

        bot.send_message(message.chat.id, inventory_message)

    else:
        bot.send_message(chat_id,
                         "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\n*Введите "
                         "команду /buy.*", parse_mode='Markdown')

    conn.close()


def my_floppa_info(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute('SELECT username, floppa_name, coin, age, hunger, waste, boredom FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        username, floppa_name, coin, age, hunger, waste, boredom = result

        if user_id in config.last_feed_times:
            time_since_last_feed = datetime.now() - config.last_feed_times[user_id]
            time_until_next_feed = timedelta(minutes=40) - time_since_last_feed
        else:
            time_until_next_feed = timedelta(minutes=0)

        if user_id in config.last_clean_times:
            time_since_last_clean = datetime.now() - config.last_clean_times[user_id]
            time_until_next_clean = timedelta(hours=1) - time_since_last_clean
        else:
            time_until_next_clean = timedelta(hours=0)

        if user_id in config.last_play_times:
            time_since_last_play = datetime.now() - config.last_play_times[user_id]
            time_until_next_play = timedelta(minutes=30) - time_since_last_play
        else:
            time_until_next_play = timedelta(minutes=0)

        if user_id in config.last_work_time:
            time_since_last_work = datetime.now() - config.last_work_time[user_id]
            time_until_next_work = timedelta(seconds=3600) - time_since_last_work
        else:
            time_until_next_work = timedelta(seconds=0)

        minutes_feed, seconds_feed = divmod(time_until_next_feed.seconds, 60)
        time_until_next_feed_str = f"{minutes_feed} минут.🕞"

        minutes_clean, seconds_clean = divmod(time_until_next_clean.seconds, 60)
        time_until_next_clean_str = f"{minutes_clean} минут.🕘"

        minutes_play, seconds_play = divmod(time_until_next_play.seconds, 60)
        time_until_next_play_str = f"{minutes_play} минут.🕔"

        hours_work, remainder_work = divmod(time_until_next_work.seconds, 3600)
        minutes_work, seconds_work = divmod(remainder_work, 60)
        time_until_next_work_str = f"{minutes_work} минут.🕜"

        info_message = (
            f"Имя хозяина👨🏻🧑: {username}\n"
            f"Имя Шлёпы😼: {floppa_name}\n"
            f"Возраст Шлёпы🥳: {age} день\n"
            f"Флоппо-коины💰: {coin}\n\n"
            f"Сытость😋: {hunger}%\n"
            f"Чистота🧼: {waste}%\n"
            f"Весёлый😸: {boredom}%\n\n"
            f"Следующее кормление через🥟: {time_until_next_feed_str}\n"
            f"Следующая уборка через🧹: {time_until_next_clean_str}\n"
            f"Следующая игра через🧸: {time_until_next_play_str}\n"
            f"Следующая рабочая смена через👷🏼: {time_until_next_work_str}\n"
        )
    else:
        info_message = "Вы еще не приобрели Шлёпу.😿\nКупите Шлёпу при помощи команды /buy"

    bot.send_message(chat_id, info_message)
    with open('self.gif', 'rb') as gif_my_floppa:
        bot.send_animation(message.chat.id, gif_my_floppa)

    conn.close()


def feed_floppa(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute('SELECT sleeping FROM users WHERE user_id = ?', (user_id,))
    sleep_check = cursor.fetchone()

    if sleep_check[0] == 1:
        bot.send_message(chat_id,
                         'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                         parse_mode='Markdown')
        return

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        if user_id in config.last_feed_times and datetime.now() - config.last_feed_times[user_id] < timedelta(minutes=40):
            bot.send_message(chat_id, 'Вы недавно кормили Шлёпу. 😋 *Попробуйте позже.*', parse_mode='Markdown')
        else:
            conn = sqlite3.connect('users-floppa.sql')
            cursor = conn.cursor()

            cursor.execute('SELECT hunger FROM users WHERE user_id = ?', (user_id,))
            current_hunger = cursor.fetchone()[0]
            new_hunger = min(current_hunger + 50, 100)

            cursor.execute('UPDATE users SET hunger = ? WHERE user_id = ?', (new_hunger, user_id))
            conn.commit()

            config.last_feed_times[user_id] = datetime.now()

            bot.send_message(chat_id, f'Шлёпа наелся!😋 *Сытость теперь {new_hunger}%.*', parse_mode='Markdown')

            conn.close()

    else:
        bot.send_message(chat_id,
                         "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\n*Введите "
                         "команду /buy.*", parse_mode='Markdown')


def clean_floppa(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute('SELECT sleeping FROM users WHERE user_id = ?', (user_id,))
    sleep_check = cursor.fetchone()

    if sleep_check[0] == 1:
        bot.send_message(chat_id,
                         'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                         parse_mode='Markdown')
        return

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:

        cursor.execute('SELECT boredom FROM users WHERE user_id = ?', (user_id,))
        enough_boredom = cursor.fetchone()

        if enough_boredom[0] < 20:
            bot.send_message(chat_id, f'*Вам стоит поиграть с котом🧸*, Шлёпа не слушается вас и не хочет мыться.😾'
                                      f'\n\n*/play - поиграть*', parse_mode='Markdown')
            return

        if user_id in config.last_clean_times and datetime.now() - config.last_clean_times[user_id] < timedelta(hours=1):
            bot.send_message(chat_id, 'Вы недавно мыли Шлёпу.😼🧼 *Попробуйте позже.*\n/myfloppa - узнать время',
                             parse_mode='Markdown')
        else:
            conn = sqlite3.connect('users-floppa.sql')
            cursor = conn.cursor()

            cursor.execute('UPDATE users SET waste = 100 WHERE user_id = ?', (user_id,))
            conn.commit()

            config.last_clean_times[user_id] = datetime.now()

            bot.send_message(chat_id, '*Шлёпа теперь чистый!*😼', parse_mode='Markdown')

            conn.close()
    else:
        bot.send_message(chat_id,
                         "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\n*Введите "
                         "команду /buy.*", parse_mode='Markdown')


def play_with_floppa(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute('SELECT sleeping FROM users WHERE user_id = ?', (user_id,))
    sleep_check = cursor.fetchone()

    if sleep_check[0] == 1:
        bot.send_message(chat_id,
                         'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                         parse_mode='Markdown')
        return

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:

        cursor.execute('SELECT hunger FROM users WHERE user_id = ?', (user_id,))
        hunger_count = cursor.fetchone()

        if hunger_count[0] < 20:
            bot.send_message(chat_id, f'*Вам стоит покормить кота🥩*, Шлёпа не будет играть на голодный желудок.😾'
                                      f'\n{hunger_count}% сытости\n\n*/feed - покормить*', parse_mode='Markdown')
            return

        if user_id in config.last_play_times and datetime.now() - config.last_play_times[user_id] < timedelta(minutes=30):
            bot.send_message(chat_id, 'Вы недавно играли со Шлёпой. 😼🧸 *Попробуйте позже.*\n/myfloppa - узнать время',
                             parse_mode='Markdown')
        else:
            conn = sqlite3.connect('users-floppa.sql')
            cursor = conn.cursor()

            cursor.execute('SELECT boredom FROM users WHERE user_id = ?', (user_id,))
            current_boredom = cursor.fetchone()[0]
            new_boredom = min(current_boredom + 40, 100)

            cursor.execute('UPDATE users SET boredom = ? WHERE user_id = ?', (new_boredom, user_id))
            conn.commit()

            config.last_play_times[user_id] = datetime.now()

            bot.send_message(chat_id, 'Вы поиграли с Шлёпой! *Теперь он веселее.*😸', parse_mode='Markdown')

            conn.close()

    else:
        bot.send_message(chat_id,
                         "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\n*Введите "
                         "команду /buy.*", parse_mode='Markdown')


def work_floppa(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute('SELECT sleeping FROM users WHERE user_id = ?', (user_id,))
    sleep_check = cursor.fetchone()

    if sleep_check[0] == 1:
        bot.send_message(chat_id,
                         'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                         parse_mode='Markdown')
        return

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:

        work_markup = types.InlineKeyboardMarkup()
        cement_button = types.InlineKeyboardButton(text='Цементный завод 🗿', callback_data='work_cement')
        dumpling_button = types.InlineKeyboardButton(text='Пельменная 🥟', callback_data='work_dumpling')
        farm_button = types.InlineKeyboardButton(text='Мятная плантация 🌿', callback_data='button_farm')
        work_markup.add(cement_button, dumpling_button)
        work_markup.add(farm_button)
        bot.send_message(chat_id, 'Выберите работу на которую пойдёте.', reply_markup=work_markup)

    else:
        bot.send_message(chat_id,
                         "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\n*Введите "
                         "команду /buy.*", parse_mode='Markdown')


def set_age(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    # Проверяем, существует ли пользователь в базе данных
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        # Обновляем параметр age для пользователя
        cursor.execute('UPDATE users SET age = ? WHERE user_id = ?', (5, user_id))
        conn.commit()

        bot.send_message(chat_id, 'Вашему Шлёпе установлен возраст 5 лет! 🎂')
    else:
        bot.send_message(chat_id,
                         "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\n*Введите "
                         "команду /buy.*", parse_mode='Markdown')

    conn.close()


def create_cas_base(message):
    conn = sqlite3.connect('casino.sql')
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE IF NOT EXISTS casino(id INTEGER PRIMARY KEY, user_id INTEGER, username TEXT, '
                   'chips INTEGER, wins INTEGER, losses INTEGER)')

    conn.commit()
    conn.close()

    bot.reply_to(message, 'Вы создали базу кузбаса!')


def start_casino(message):
    user_id = message.from_user.id

    if user_id in config.last_casino_time:
        last_usage_time = config.last_casino_time[user_id]
        current_time = time.time()

        # Проверьте, прошла ли минута с момента последнего использования команды
        if current_time - last_usage_time < 365:
            wait_time = int(365 - (current_time - last_usage_time))
            bot.reply_to(message, f"Подождите еще {wait_time} секунд перед использованием команды. 😼⏳")
            return

    # Если прошла минута или пользователь впервые использует команду, выполните вашу логику
    chat_id = message.chat.id

    conn = sqlite3.connect('casino.sql')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM casino WHERE user_id=?', (user_id,))
    user_data = cursor.fetchone()

    conn_base = sqlite3.connect('users-floppa.sql')
    cursor_base = conn_base.cursor()

    cursor_base.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor_base.fetchone()

    if existing_user:

        if existing_user[9] == 1:
            bot.send_message(chat_id,
                             'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                             parse_mode='Markdown')
            return
        if existing_user[8] < 20:
            bot.send_message(chat_id, f'*Шлёпа в тильте! 😿*, Шлёпа не хочет играть в казино сейчас..'
                                      f'\n\n*/play - порадовать Шлёпу.*', parse_mode='Markdown')
            return

        if user_data is None:
            username = message.from_user.username if message.from_user.username else message.from_user.first_name
            cursor.execute('INSERT INTO casino(user_id, username, chips, wins, losses) VALUES(?, ?, 0, 0, 0)',
                           (user_id, username))
            conn.commit()
            bot.reply_to(message,
                         f'Добро пожаловать в казино, {username}🧐!\n\n(Введите еще раз команду, чтобы играть)')

        else:
            keyboard = types.InlineKeyboardMarkup()
            casino_button_1 = types.InlineKeyboardButton(text='Играть 🎰', callback_data='play_caz')
            casino_button_2 = types.InlineKeyboardButton(text='Статистика 📋', callback_data='my_chips')
            casino_button_3 = types.InlineKeyboardButton(text='Купить фишки 💰', callback_data='buy_chips')
            casino_button_4 = types.InlineKeyboardButton(text='Продать фишки 💲', callback_data='sell_chips')
            keyboard.add(casino_button_1, casino_button_2)
            keyboard.add(casino_button_3, casino_button_4)

            with open('casino_floppa.jpg', 'rb') as casino_photo:
                bot.send_photo(chat_id, casino_photo)

            bot.send_message(chat_id, '*Приветствуем в нашем казино🧐!* ', parse_mode='Markdown', reply_markup=keyboard)

    else:
        bot.send_message(chat_id,
                         "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\nВведите "
                         "команду /buy.", parse_mode='Markdown')

    # Обновите время последнего использования команды
    config.last_casino_time[user_id] = time.time()

    conn_base.close()
    conn.close()
