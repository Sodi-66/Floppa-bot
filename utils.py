import sqlite3
import time
import config
from config import bot
from datetime import datetime, timedelta
import random

from config import nice_clients, strict_clients, not_strict_clients, farm_problems

last_age_update = datetime.now().date()


def create_shop_db():
    conn = sqlite3.connect('shop-items.db')
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, effect TEXT)')
    conn.commit()

    # Добавление предметов в магазин
    items_to_insert = [
        ('Зелье "Сотка"', 100, '{"hunger": 100,  "boredom": 100, "waste": 100}'),
        ("Малое зелье веселья", 40, '{"boredom": 100}'),
        ('Миска пельмешей', 40, '{"hunger": 100}'),
        ('Мыло "Кимбо"', 40, '{"waste": 100}'),
        ('Лотерейный билет', 200, '{"coin_range": [50, 400]}'),
        ('Бетономешалка', 350, '{"coin":60}'),

    ]
    cursor.executemany('INSERT INTO items (name, price, effect) VALUES (?, ?, ?)', items_to_insert)

    conn.commit()

    conn.close()


def check_floppa_needs():
    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT user_id, floppa_name, hunger, waste, boredom FROM users WHERE hunger = 0 OR waste = 0 OR boredom = 0')
    users_to_notify = cursor.fetchall()

    for user_id, floppa_name, hunger, waste, boredom in users_to_notify:
        message = f"Вашему Шлёпе {floppa_name} требуется срочный уход или вы его потеряете!😿 Параметры:\n"
        if hunger == 0:
            message += f"Сытость😋: {hunger}%\n"
        if waste == 0:
            message += f"Чистота🗑: {waste}%\n"
        if boredom == 0:
            message += f"Весёлый🥱: {boredom}%\n"

        bot.send_message(user_id, message)

    conn.close()


def update_floppas():
    global last_age_update

    while True:
        time.sleep(60)

        conn = sqlite3.connect('users-floppa.sql')
        cursor = conn.cursor()

        cursor.execute('SELECT user_id, wait_interval, sleeping FROM users')
        user_data = cursor.fetchall()

        for user_id, wait_interval, sleeping in user_data:
            if sleeping:
                time.sleep(wait_interval)  # Ждем увеличенный интервал времени (4 минуты)

                cursor.execute(
                    'UPDATE users SET hunger = hunger - 1, waste = waste - 1, boredom = boredom - 1 WHERE user_id = ?',
                    (user_id,))
                conn.commit()

            else:
                check_floppa_needs()

                cursor.execute('UPDATE users SET hunger = hunger - 1, waste = waste - 1, boredom = boredom - 1 WHERE user_id = ?', (user_id,))
                conn.commit()

        today = datetime.now().date()
        if today > last_age_update:
            update_age()
            last_age_update = today

        # Получаем информацию о пользователях, у которых закончились параметры
        cursor.execute('SELECT user_id, floppa_name FROM users WHERE hunger <= 0 AND waste <= 0 AND boredom <= 0')
        users_to_notify = cursor.fetchall()

        for user_id, floppa_name in users_to_notify:
            # Удаляем пользователя из базы данных
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            conn.commit()

            # Отправляем пользователю сообщение о удалении Шлёпы
            bot.send_message(user_id, f"К сожалению, *ваш Шлёпа {floppa_name} убежал* из-за того, что вы за ним не "
                                      f"следили.🙀\nВы можете приобрести нового Шлёпу с помощью *команды /buy.* "
                                      f"Впредь будьте ответственнее.😾", parse_mode='Markdown')

        # Очищаем список последних кормлений, у которых прошло более 40 минут
        now = datetime.now()
        for user_id in list(config.last_feed_times.keys()):
            if now - config.last_feed_times[user_id] > timedelta(minutes=40):
                del config.last_feed_times[user_id]

        conn.close()


def update_age():
    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    cursor.execute('UPDATE users SET age = age + 1')
    conn.commit()

    conn.close()


def work_result_dumplings(message, coin_increase):
    user_id = message.from_user.id

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    # Получаем текущие значения параметров пользователя
    cursor.execute('SELECT coin, hunger, waste, boredom FROM users WHERE user_id = ?', (user_id,))
    current_values = cursor.fetchone()

    coin, hunger, waste, boredom = current_values

    cursor.execute('SELECT item_name FROM inventory WHERE user_id = ? AND item_name = ?', (user_id, 'Бетономешалка'))
    has_concrete_mixer = cursor.fetchone()

    hunger = max(hunger - 5, 0)
    waste = max(waste - 15, 0)
    boredom = max(boredom - 15, 0)
    coin += coin_increase

    # Обновляем базу данных с новыми значениями параметров
    cursor.execute('UPDATE users SET coin = ?, hunger = ?, waste = ?, boredom = ? WHERE user_id = ?',
                   (coin, hunger, waste, boredom, user_id))
    conn.commit()

    conn.close()


def work_result(message):
    user_id = message.from_user.id

    conn = sqlite3.connect('users-floppa.sql')
    cursor = conn.cursor()

    # Получаем текущие значения параметров пользователя
    cursor.execute('SELECT coin, hunger, waste, boredom FROM users WHERE user_id = ?', (user_id,))
    current_values = cursor.fetchone()

    coin, hunger, waste, boredom = current_values

    cursor.execute('SELECT item_name FROM inventory WHERE user_id = ? AND item_name = ?', (user_id, 'Бетономешалка'))
    has_concrete_mixer = cursor.fetchone()

    # Уменьшаем параметры на 10 (или 20 для boredom), но не ниже 0
    hunger = max(hunger - 10, 0)
    waste = max(waste - 10, 0)
    boredom = max(boredom - 20, 0)

    if has_concrete_mixer:
        coin += 60
    else:
        coin += 30

    # Обновляем базу данных с новыми значениями параметров
    cursor.execute('UPDATE users SET coin = ?, hunger = ?, waste = ?, boredom = ? WHERE user_id = ?',
                   (coin, hunger, waste, boredom, user_id))
    conn.commit()

    conn.close()


def check_sleeping(message):
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

    conn.close()


def win_change_boredom(message):
    user_id = message.from_user.id

    conn_users = sqlite3.connect('users-floppa.sql')
    cursor_users = conn_users.cursor()

    cursor_users.execute('SELECT boredom FROM users WHERE user_id = ?', (user_id,))
    current_values = cursor_users.fetchone()

    # Извлечь значение из кортежа
    boredom = current_values[0]

    boredom = min(boredom + 1, 100)

    cursor_users.execute('UPDATE users SET boredom = ? WHERE user_id = ?',
                   (boredom, user_id))
    conn_users.commit()

    conn_users.close()


def loss_change_boredom(message):
    user_id = message.from_user.id

    conn_users = sqlite3.connect('users-floppa.sql')
    cursor_users = conn_users.cursor()

    cursor_users.execute('SELECT boredom FROM users WHERE user_id = ?', (user_id,))
    current_values = cursor_users.fetchone()

    # Извлечь значение из кортежа
    boredom = current_values[0]

    boredom = max(boredom - 2, 0)

    cursor_users.execute('UPDATE users SET boredom = ? WHERE user_id = ?',
                   (boredom, user_id))
    conn_users.commit()

    conn_users.close()


def _1_34(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_34 = message.text

    try:
        chips_to_34 = int(chips_to_34)
        if chips_to_34 < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_34:

            random_casino_number = random.randint(0, 36)

            if random_casino_number in config._2_to_1_34:
                chips_win = chips_to_34 * 3
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance, new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_34
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips, new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def _2_35(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_35 = message.text

    try:
        chips_to_35 = int(chips_to_35)
        if chips_to_35 < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_35:

            random_casino_number = random.randint(0, 36)

            if random_casino_number in config._2_to_1_35:
                chips_win = chips_to_35 * 3
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance, new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_35
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips, new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def _3_36(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_36 = message.text

    try:
        chips_to_36 = int(chips_to_36)
        if chips_to_36 < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_36:

            random_casino_number = random.randint(0, 36)

            if random_casino_number in config._2_to_1_36:
                chips_win = chips_to_36 * 3
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance, new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_36
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips, new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def _1_18(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_18 = message.text

    try:
        chips_to_18 = int(chips_to_18)
        if chips_to_18 < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_18:

            random_casino_number = random.randint(0, 36)

            if random_casino_number in config._1_to_18:
                chips_win = chips_to_18 * 2
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance, new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_18
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips, new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def _19_36(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_19 = message.text

    try:
        chips_to_19 = int(chips_to_19)
        if chips_to_19 < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_19:

            random_casino_number = random.randint(0, 36)

            if random_casino_number in config._19_to_36:
                chips_win = chips_to_19 * 2
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance, new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_19
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips, new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def st_casino(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_st = message.text

    try:
        chips_to_st = int(chips_to_st)
        if chips_to_st < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_st:

            random_casino_number = random.randint(0, 36)

            if random_casino_number in config.st_12:
                chips_win = chips_to_st * 3
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance, new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_st
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips, new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def nd_casino(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_nd = message.text

    try:
        chips_to_nd = int(chips_to_nd)
        if chips_to_nd < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_nd:

            random_casino_number = random.randint(0, 36)

            if random_casino_number in config.nd_12:
                chips_win = chips_to_nd * 3
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance, new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_nd
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips, new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def rd_casino(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_rd = message.text

    try:
        chips_to_rd = int(chips_to_rd)
        if chips_to_rd < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_rd:

            random_casino_number = random.randint(0, 36)

            if random_casino_number in config.rd_12:
                chips_win = chips_to_rd * 3
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance, new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_rd
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips, new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:

            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def odd_casino(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_odd = message.text

    try:
        chips_to_odd = int(chips_to_odd)
        if chips_to_odd < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_odd:

            random_casino_number = random.randint(0, 36)

            if random_casino_number % 2 != 0:
                chips_win = chips_to_odd * 2
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance, new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_odd
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips, new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:

            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def even_casino(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_even = message.text

    try:
        chips_to_even = int(chips_to_even)
        if chips_to_even < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_even:

            random_casino_number = random.randint(0, 36)

            if random_casino_number % 2 == 0:
                chips_win = chips_to_even * 2
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance, new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_even
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips, new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def zero_casino(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_zero = message.text

    try:
        chips_to_zero = int(chips_to_zero)
        if chips_to_zero < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_zero:

            random_casino_number = random.randint(0, 36)

            if random_casino_number == 0:
                chips_win = chips_to_zero * 36
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance, new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_zero
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips, new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def black_casino(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_black = message.text

    try:
        chips_to_black = int(chips_to_black)
        if chips_to_black < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_black:

            random_casino_number = random.randint(0, 36)

            if random_casino_number in config.black_numbers:
                chips_win = chips_to_black * 2
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance,new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_black
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips,new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def red_casino(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_red = message.text

    try:
        chips_to_red = int(chips_to_red)
        if chips_to_red < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для ставки.* 😾', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    cursor.execute('SELECT chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]
        current_wins = casino_data[1]
        current_losses = casino_data[2]

        if current_chips >= chips_to_red:

            random_casino_number = random.randint(0, 36)

            if random_casino_number in config.red_numbers:
                chips_win = chips_to_red * 2
                new_chips_balance = current_chips + chips_win
                new_balance_wins = current_wins + 1
                cursor.execute('UPDATE casino SET chips=?, wins=? WHERE user_id=?',
                               (new_chips_balance, new_balance_wins, user_id))
                conn.commit()

                win_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\nПоздравляю, *вы выиграли {chips_win}'
                                          f' фишек.🎰*', parse_mode='Markdown')
            else:

                current_chips -= chips_to_red
                new_balance_loss = current_losses + 1
                cursor.execute('UPDATE casino SET chips=?, losses=? WHERE user_id=?',
                               (current_chips, new_balance_loss, user_id))
                conn.commit()

                loss_change_boredom(message)

                bot.send_message(chat_id, f'Выпало число {random_casino_number}🔢\n*Увы, но в этот раз вам не везёт.😿*',
                                 parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас нет фишек.💰\n*Введите /caz*, чтобы купить их. 🧐',
                         parse_mode='Markdown')

    conn.close()


def short_callback_sell_chips(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chips_to_sell = message.text

    try:
        chips_to_sell = int(chips_to_sell)
        if chips_to_sell < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректное количество фишек для продажи.😾*', parse_mode='Markdown')
        return

    conn = sqlite3.connect('casino.sql')  # Открываем базу данных казино
    cursor = conn.cursor()

    conn_1 = sqlite3.connect('users-floppa.sql')
    cursor_1 = conn_1.cursor()

    cursor.execute('SELECT chips FROM casino WHERE user_id=?', (user_id,))
    casino_data = cursor.fetchone()

    if casino_data is not None:
        current_chips = casino_data[0]

        if current_chips >= chips_to_sell:
            chips_price = 1  # Сколько флоппо-коинов за одну фишку
            exchanged_coins = chips_to_sell  # Просто обменять фишки на коины
            remaining_chips = current_chips - chips_to_sell

            # Обновляем баланс фишек в базе данных казино
            cursor.execute('UPDATE casino SET chips=? WHERE user_id=?', (remaining_chips, user_id))
            conn.commit()

            # Обновляем баланс флоппо-коинов в базе данных флоппа
            cursor_1.execute('SELECT coin FROM users WHERE user_id=?', (user_id,))
            user_data = cursor_1.fetchone()
            current_coins = user_data[0] if user_data is not None else 0
            new_coins_balance = current_coins + exchanged_coins
            cursor_1.execute('UPDATE users SET coin=? WHERE user_id=?', (new_coins_balance, user_id))
            conn_1.commit()

            bot.send_message(chat_id, f'*Вы успешно обменяли {chips_to_sell} фишек 💰 на {exchanged_coins} флоппо-коинов 💲*',
                             parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно фишек 💰* для этой операции.', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но у вас *нет фишек для продажи💰*', parse_mode='Markdown')

    conn.close()
    conn_1.close()


def short_callback_buy_chips(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    coins_to_exchange = message.text

    try:
        coins_to_exchange = int(coins_to_exchange)
        if coins_to_exchange < 1:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, '*Введите корректную сумму!*😾', parse_mode='Markdown')
        return

    # Открываем базу данных казино
    conn_casino = sqlite3.connect('casino.sql')
    cursor_casino = conn_casino.cursor()

    # Открываем базу данных пользователей
    conn_users = sqlite3.connect('users-floppa.sql')
    cursor_users = conn_users.cursor()

    # Выбираем баланс флоппо-коинов (coins) для текущего пользователя из базы данных пользователей
    cursor_users.execute('SELECT coin FROM users WHERE user_id=?', (user_id,))
    user_data = cursor_users.fetchone()

    if user_data is not None:

        current_coins = user_data[0]

        if current_coins >= coins_to_exchange:
            chips_price = 1  # Сколько коинов нужно для одной фишки
            exchanged_chips = coins_to_exchange  # Просто обменять коины на фишки
            remaining_coins = current_coins - coins_to_exchange

            # Обновляем баланс флоппо-коинов в базе данных пользователей
            cursor_users.execute('UPDATE users SET coin=? WHERE user_id=?', (remaining_coins, user_id))
            conn_users.commit()

            # Обновляем баланс фишек в базе данных казино
            cursor_casino.execute('SELECT chips FROM casino WHERE user_id=?', (user_id,))
            casino_data = cursor_casino.fetchone()
            current_chips = casino_data[0] if casino_data is not None else 0
            new_chips_balance = current_chips + exchanged_chips
            cursor_casino.execute('UPDATE casino SET chips=? WHERE user_id=?', (new_chips_balance, user_id))
            conn_casino.commit()

            bot.send_message(chat_id,
                             f'Вы успешно обменяли *{coins_to_exchange} флоппо-коинов 💲 на {exchanged_chips} фишек 💰*',
                             parse_mode='Markdown')

        else:
            bot.send_message(chat_id, 'У вас *недостаточно флоппо-коинов* для этой операции. 🧐', parse_mode='Markdown')

    else:
        bot.send_message(chat_id, 'Простите, но мы вам не доверяем!🧐 *(Вас нет в базе данных!)*', parse_mode='Markdown')

    conn_casino.close()
    conn_users.close()

