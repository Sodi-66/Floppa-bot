import sqlite3
import config
import utils
import random

from config import bot
from commmands import cmd_help
from telebot import types
from config import nice_clients, strict_clients, not_strict_clients, farm_problems
from datetime import timedelta, datetime
from utils import work_result_dumplings as salary

current_client = None
current_farm_problem = None


@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):

    global current_client
    global current_farm_problem

    if call.data == 'play_caz':

        chat_id = call.message.chat.id

        casino_keyboard = types.InlineKeyboardMarkup()
        zero_button = types.InlineKeyboardButton(text='0️⃣ [36:1]', callback_data='zero')
        red_button = types.InlineKeyboardButton(text='🟥', callback_data='red')
        black_button = types.InlineKeyboardButton(text='⬛️', callback_data='black')
        even_button = types.InlineKeyboardButton(text='Чётное', callback_data='even')
        odd_button = types.InlineKeyboardButton(text='Нечётное', callback_data='odd')
        st_button = types.InlineKeyboardButton(text='1️⃣st 12', callback_data='st')
        nd_button = types.InlineKeyboardButton(text='2️⃣nd 12', callback_data='nd')
        rd_button = types.InlineKeyboardButton(text='3️⃣rd 12', callback_data='rd')
        _34_button = types.InlineKeyboardButton(text='1️⃣ ряд', callback_data='34')
        _35_button = types.InlineKeyboardButton(text='2️⃣ ряд', callback_data='35')
        _36_button = types.InlineKeyboardButton(text='3️⃣ ряд', callback_data='36')
        _1_to_18_button = types.InlineKeyboardButton(text='1️⃣-1️⃣8️⃣', callback_data='1-18')
        _19_to_36_button = types.InlineKeyboardButton(text='1️⃣9️⃣-3️⃣6️⃣', callback_data='19-36')
        casino_keyboard.add(zero_button, )
        casino_keyboard.add(red_button, black_button)
        casino_keyboard.add(even_button, odd_button)
        casino_keyboard.add(_1_to_18_button, _19_to_36_button)
        casino_keyboard.add(st_button, nd_button, rd_button)
        casino_keyboard.add(_34_button, _35_button, _36_button)

        bot.send_message(chat_id, '*Выберите на что будете ставить 🤔*', parse_mode='Markdown',
                         reply_markup=casino_keyboard)

    if call.data == 'my_chips':

        user_id = call.from_user.id
        conn = sqlite3.connect('casino.sql')
        cursor = conn.cursor()

        cursor.execute('SELECT username, chips, wins, losses FROM casino WHERE user_id=?', (user_id,))
        user_data = cursor.fetchone()

        if user_data is not None:
            username, chips, wins, losses = user_data
            response = f'{username}🧐:\n\nБаланс фишек 🎰: {chips}\nПобеды в играх 🥇: {wins}\nПоражения в играх 😟: {losses}'
        else:
            response = 'Простите, но мы вас не доверяем! (Вас нет в базе данных!)'

        bot.send_message(call.message.chat.id, response)
        conn.close()

    if call.data == 'buyflopp':
        cmd_help(call.message)

    if call.data == 'work_cement':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

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

            cursor.execute('SELECT coin, waste, hunger, boredom FROM users WHERE user_id = ?', (user_id,))
            current_values = cursor.fetchone()

            coin, waste, hunger, boredom = current_values

            if waste < 15 or hunger < 15 or boredom < 15:
                bot.send_message(chat_id, '*Шлёпе нужен уход*, сейчас он не может работать.😾\n\n/myfloppa',
                                 parse_mode='Markdown')
                return

            if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
                remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
                hours, remainder = divmod(remaining_time.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите ещё '
                                          f'{minutes} минут.*', parse_mode='Markdown')
            else:
                has_concrete_mixer = False

                cursor.execute('SELECT item_name FROM inventory WHERE user_id = ? AND item_name = ?',
                               (user_id, 'Бетономешалка'))
                has_concrete_mixer = cursor.fetchone()

                if has_concrete_mixer:
                    earned_money = 60
                else:
                    earned_money = 30

                bot.send_message(chat_id,
                                 f'Шлёпа славно замесил цемент и получил зарплату - {earned_money} флоппо-коинов'
                                 '.😼💰\nСледующая смена через час.⌛️')
                config.last_work_time[user_id] = datetime.now()
                utils.work_result(call)

        else:
            bot.send_message(chat_id,
                             "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\n*Введите "
                             "команду /buy.*", parse_mode='Markdown')

    if call.data == 'work_dumpling':
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        conn = sqlite3.connect('users-floppa.sql')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.execute('SELECT age, sleeping FROM users WHERE user_id = ?', (user_id,))
            needs_check = cursor.fetchone()

            if needs_check[1] == 1:
                bot.send_message(chat_id,
                                 'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                                 parse_mode='Markdown')
                return

            if needs_check[0] < 5:

                bot.send_message(chat_id, '*Ваш Шлёпа еще слишком мал👶*, чтобы работать в пельменной. ',
                                 parse_mode='Markdown')
                return

            cursor.execute('SELECT coin, waste, hunger, boredom FROM users WHERE user_id = ?', (user_id,))
            current_values = cursor.fetchone()

            coin, waste, hunger, boredom = current_values

            if waste < 15 or hunger < 15 or boredom < 15:
                bot.send_message(chat_id, '*Шлёпе нужен уход*, сейчас он не может работать.😾\n\n/myfloppa',
                                 parse_mode='Markdown')
                return

            if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
                remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
                hours, remainder = divmod(remaining_time.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите ещё '
                                          f'{minutes} минут.*', parse_mode='Markdown')
            else:
                client = random.choice(nice_clients + strict_clients + not_strict_clients)
                current_client = client

                client_markup = types.InlineKeyboardMarkup()
                advice_button = types.InlineKeyboardButton(text='Дать совет 📋', callback_data='advice')
                discount_button = types.InlineKeyboardButton(text='Предложить скидку 💰', callback_data='discount')
                fast_cook_button = types.InlineKeyboardButton(text='Быстрое приготовление ⌛️', callback_data='faster')
                quality_cook_button = types.InlineKeyboardButton(text='Качественное приготовление ✅',
                                                                 callback_data='quality')
                client_markup.add(advice_button)
                client_markup.add(discount_button)
                client_markup.add(fast_cook_button)
                client_markup.add(quality_cook_button)

                bot.send_message(chat_id, f'*К нам пожаловал клиент - {client}👨🏻*. Что будет делать Шлёпа?😼',
                                 reply_markup=client_markup, parse_mode='Markdown')

        else:
            bot.send_message(chat_id,
                             "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\n*Введите "
                             "команду /buy.*", parse_mode='Markdown')

    if call.data == 'advice':
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        client = current_client

        if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
            remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите (/myfloppa - узнать '
                                      f'время)*', parse_mode='Markdown')
            return

        config.last_work_time[user_id] = datetime.now()

        if client in strict_clients:
            client_likes = random.random() < 0.25
            if client_likes:
                money = 40
                bot.send_message(chat_id, f'*{client} был/была ресторанным критиком.🧢*\nМогло быть и лучше, но '
                                          f'*клиенту понравилось.*\nВы заработали {money} флоппо-коинов. 💰',
                                 parse_mode='Markdown')
                salary(call, money)

            else:
                money = 30
                bot.send_message(chat_id, f'*{client} был/была ресторанным критиком.*\nКлиенту не понравилось.'
                                          f'\nВы заработали {money} флоппо-коинов. 💰', parse_mode='Markdown')
                salary(call, money)

        if client in not_strict_clients:
            client_likes = random.random() < 0.41
            if client_likes:
                money = 60
                bot.send_message(chat_id, f'{client} заплатил(а), не оставив отзыв. 💬\n*Вы заработали {money} флоппо'
                                          f'-коинов. 💰*', parse_mode='Markdown')
                salary(call, money)

            else:
                money = 45
                bot.send_message(chat_id, f'*{client} не понравилось в пельменной. 👎🏿*\nВы заработали {money} флоппо-'
                                          f'коинов. 💰', parse_mode='Markdown')
                salary(call, money)

        if client in nice_clients:
            client_likes = random.random() < 0.75
            if client_likes:
                money = 90
                bot.send_message(chat_id, f'*Клиенту {client} всё понравилось!💚*\nСервис в этом заведении отменный!'
                                          f'\nВы заработали {money} флоппо-коинов. 💰', parse_mode='Markdown')
                salary(call, money)

            else:
                money = 60
                bot.send_message(chat_id, f'Клиенту {client} не понравилось в пельменной.👎🏿\n*Вы заработали {money}'
                                          f'флоппо-коинов. 💰*', parse_mode='Markdown')
                salary(call, money)

    if call.data == 'discount':
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        client = current_client

        if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
            remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите (/myfloppa - узнать '
                                      f'время)*', parse_mode='Markdown')
            return

        config.last_work_time[user_id] = datetime.now()

        if client in strict_clients:
            client_likes = random.random() < 0.15
            if client_likes:
                money = 35
                bot.send_message(chat_id, f'*{client} был/была ресторанным критиком.*\nПельмени могли быть и лучше.☝️'
                                          f'\nВы заработали {money} флоппо-коинов. 💰', parse_mode='Markdown')
                salary(call, money)

            else:
                money = 25
                bot.send_message(chat_id, f'*{client} был/была ресторанным критиком.*\nСкидка не может скрыть ужасный'
                                          f' вкус блюда.😡🎩\nВы заработали {money} флоппо-коинов. 💰',
                                 parse_mode='Markdown')
                salary(call, money)

        if client in not_strict_clients:
            client_likes = random.random() < 0.5
            if client_likes:
                money = 65
                bot.send_message(chat_id, f'*{client} заплатил(а), отметив отличные цены.🤔*\nВы заработали {money}'
                                          f'флоппо-коинов. 💰', parse_mode='Markdown')
                salary(call, money)

            else:
                money = 45
                bot.send_message(chat_id, f'*{client} не понравилось в пельменной.*\nПельмени оказались не вкусными.🤮'
                                          f'\nВы заработали {money} флоппо-коинов. 💰', parse_mode='Markdown')
                salary(call, money)

        if client in nice_clients:
            client_likes = random.random() < 0.83
            if client_likes:
                money = 90
                bot.send_message(chat_id, f'*Клиенту {client} всё понравилось!*\nЦены просто замечательные!🇨🇫'
                                          f'\nВы заработали {money} флоппо-коинов. 💰', parse_mode='Markdown')
                salary(call, money)

            else:
                money = 70
                bot.send_message(chat_id, f'*Клиенту {client} не понравилось в пельменной.*\nОтвратительный сервис. 😤'
                                          f'\nВы заработали {money} флоппо-коинов. 💰', parse_mode='Markdown')
                salary(call, money)

    if call.data == 'faster':
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        client = current_client

        if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
            remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите (/myfloppa - узнать '
                                      f'время)*', parse_mode='Markdown')
            return

        config.last_work_time[user_id] = datetime.now()

        if client in strict_clients:
            client_likes = random.random() < 0.13
            if client_likes:
                money = 60
                bot.send_message(chat_id, f'*{client} был/была ресторанным критиком.*\nЗаказ принесли быстро, но '
                                          f'сервис, еда и цены оказались плохими.😤🎩\nВы заработали {money} '
                                  'флоппо-коинов. 💰', parse_mode='Markdown')
                salary(call, money)

            else:
                money = 30
                bot.send_message(chat_id, f'*{client} был/была ресторанным критиком.*\nКритик оставил'
                                          f'отрицательный отзыв.🎩\nВы заработали {money} флоппо-коинов. 💰',
                                 parse_mode='Markdown')
                salary(call, money)

        if client in not_strict_clients:
            client_likes = random.random() < 0.5
            if client_likes:
                money = 90
                bot.send_message(chat_id, f'*Клиенту понравилось в пельменной.*\n{client}: Как же быстро принесли наш'
                                          f' заказ!💚\nВы заработали {money} флоппо-коинов. 💰', parse_mode='Markdown')
                salary(call, money)

            else:
                money = 60
                bot.send_message(chat_id, f'*Клиенту не понравилось в пельменной.*\n{client}: Цена не соответствует '
                                          f'качеству заказа!😝\nВы заработали {money} флоппо-коинов. 💰',
                                 parse_mode='Markdown')
                salary(call, money)

        if client in nice_clients:
            client_likes = random.random() < 0.3
            if client_likes:
                money = 50
                bot.send_message(chat_id, f'*Клиенту {client} понравилось!*\nПельмени получились не идеальными, но '
                                          f'заказ принесли быстро!🙂\nВы заработали {money} флоппо-коинов. 💰',
                                 parse_mode='Markdown')
                salary(call, money)
            else:
                money = 40
                bot.send_message(chat_id, f'*Клиенту {client} не понравилось в пельменной.*\nУжасно не вкусные '
                                          f'пельмени!🤢\nВы заработали {money} флоппо-коинов. 💰',
                                 parse_mode='Markdown')
                salary(call, money)

    if call.data == 'quality':
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        client = current_client

        if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
            remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите (/myfloppa - узнать '
                                      f'время)*', parse_mode='Markdown')
            return
        config.last_work_time[user_id] = datetime.now()
        if client in strict_clients:
            client_likes = random.random() < 0.65

            if client_likes:
                money = 90
                bot.send_message(chat_id, f'*{client} был/была ресторанным критиком.*\n{client}: Искренне рекомендую '
                                          f'заходить в эту пельменную.👍🏿🎩\nВы заработали {money} флоппо-коинов. 💰',
                                 parse_mode='Markdown')
                salary(call, money)

            else:
                money = 60
                bot.send_message(chat_id, f'*{client} был/была ресторанным критиком.*\n{client}: Здесь отвратительно '
                                          f'всё.🤬🎩\nВы заработали {money} флоппо-коинов. 💰', parse_mode='Markdown')
                salary(call, money)

        if client in not_strict_clients:
            client_likes = random.random() < 0.5

            if client_likes:
                money = 60
                bot.send_message(chat_id, f'{client} заплатил(а), отметив, что здесь готовят отличные пельмени.💚'
                                          f'\n*Вы заработали {money} флоппо-коинов. 💰*', parse_mode='Markdown')
                salary(call, money)

            else:
                money = 50
                bot.send_message(chat_id, f'*{client} не понравилось в пельменной.*\nПришлось слишком долго ждать '
                                          f'заказ. 😞\nВы заработали {money} флоппо-коинов. 💰', parse_mode='Markdown')
                salary(call, money)

        if client in nice_clients:
            client_likes = random.random() < 0.2

            if client_likes:
                money = 40
                bot.send_message(chat_id, f'*Клиенту {client} понравилось!*\nВкус отменный, но пришлось долго ждать '
                                          f'заказ. 🙂\nВы заработали {money} флоппо-коинов. 💰', parse_mode='Markdown')
                salary(call, money)

            else:
                money = 30
                bot.send_message(chat_id, f'*Клиенту {client} не понравилось в пельменной.*\nРазве можно так долго '
                                          f'готовить пельмени?!🤬\nВы заработали {money} флоппо-коинов. 💰',
                                 parse_mode='Markdown')
                salary(call, money)

    if call.data == 'button_farm':
        chat_id = call.message.chat.id
        user_id = call.from_user.id

        conn = sqlite3.connect('users-floppa.sql')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.execute('SELECT age, sleeping FROM users WHERE user_id = ?', (user_id,))
            needs_check = cursor.fetchone()

            if needs_check[1] == 1:
                bot.send_message(chat_id,
                                 'Ваш Шлёпа спит!😴 Вы не можете использовать команды.\n\n*/unsleep - разбудить Шлёпу*',
                                 parse_mode='Markdown')
                return

            if needs_check[0] < 10:
                bot.send_message(chat_id, '*Ваш Шлёпа еще слишком мал👶*, чтобы работать на плантации. ',
                                 parse_mode='Markdown')
                return

            cursor.execute('SELECT coin, waste, hunger, boredom FROM users WHERE user_id = ?', (user_id,))
            current_values = cursor.fetchone()

            coin, waste, hunger, boredom = current_values

            if waste < 15 or hunger < 15 or boredom < 15:
                bot.send_message(chat_id, '*Шлёпе нужен уход*, сейчас он не может работать.😾\n\n/myfloppa',
                                 parse_mode='Markdown')
                return

            if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
                remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
                hours, remainder = divmod(remaining_time.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите ещё '
                                          f'{minutes} минут.*', parse_mode='Markdown')
            else:
                problem = random.choice(farm_problems)
                current_farm_problem = problem

                farm_markup = types.InlineKeyboardMarkup()
                sowing_button = types.InlineKeyboardButton(text='Посев 🎋', callback_data='sowing')
                watering_button = types.InlineKeyboardButton(text='Полив 💦', callback_data='watering')
                fungicides_button = types.InlineKeyboardButton(text='Применить\nфунгициды 🌫', callback_data='fungicides')
                fertilizer_button = types.InlineKeyboardButton(text='Удобрение 💩', callback_data='fertilizer')
                collection_button = types.InlineKeyboardButton(text='Сбор мяты 🌱', callback_data='collection')
                remove_weed_button = types.InlineKeyboardButton(text='Убрать сорняки 🍁', callback_data='weed')

                farm_markup.add(sowing_button, watering_button)
                farm_markup.add(collection_button, remove_weed_button)
                farm_markup.add(fungicides_button)
                farm_markup.add(fertilizer_button)

                bot.send_message(chat_id, f'Добро пожаловать на плантацию, где мы выращиваем отборную мяту!🍃\n\n'
                                          f'*Проблема: {problem}⚠️🌿*\n\nЧто Шлёпа будет делать?😼',
                                 parse_mode='Markdown', reply_markup=farm_markup)

        else:
            bot.send_message(chat_id,
                             "Прежде чем использовать эту команду, пожалуйста, приобретите Шлёпу.😼💰\n*Введите "
                             "команду /buy.*", parse_mode='Markdown')

    if call.data == 'sowing':
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        problem = current_farm_problem

        if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
            remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите (/myfloppa - узнать '
                                      f'время)*', parse_mode='Markdown')
            return

        config.last_work_time[user_id] = datetime.now()

        if 'не посажено' in problem:
            money = 100
            salary(call, money)
            bot.send_message(chat_id, f'*Посев прошёл успешно*, Шлёпа получил достойную зарплату ({money} флоппо-'
                                      f'коинов)💰!', parse_mode='Markdown')
        else:
            money = 30
            salary(call, money)
            bot.send_message(chat_id, f'Это никак не помогло решению нашей проблемы‼️\n*Шлёпа получает очень '
                                      f'маленькую зарплату!* ({money} флоппо-коинов)💰', parse_mode='Markdown')

    if call.data == 'watering':
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        problem = current_farm_problem

        if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
            remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите (/myfloppa - узнать '
                                      f'время)*', parse_mode='Markdown')
            return

        config.last_work_time[user_id] = datetime.now()

        if problem == 'Засуха':
            money = 100
            salary(call, money)
            bot.send_message(chat_id, f'Отлично! Шлёпа получил достойную *зарплату ({money} флоппо-'
                                      f'коинов)💰!*', parse_mode='Markdown')
        else:
            money = 30
            salary(call, money)
            bot.send_message(chat_id, f'Это никак не помогло решению нашей проблемы!❌\n*Шлёпа получает очень '
                                      f'маленькую зарплату 💰! ({money} флоппо-коинов)*', parse_mode='Markdown')

    if call.data == 'fungicides':
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        problem = current_farm_problem

        if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
            remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите (/myfloppa - узнать '
                                      f'время)*', parse_mode='Markdown')
            return

        config.last_work_time[user_id] = datetime.now()

        if 'плесенью и грибком' in problem:
            money = 100
            salary(call, money)
            bot.send_message(chat_id, f'*Кусты выздоровели!* 🌿 Шлёпа получил достойную зарплату ({money} флоппо-'
                                      f'коинов)💰!', parse_mode='Markdown')
        else:
            money = 30
            salary(call, money)
            bot.send_message(chat_id, f'Это никак не помогло решению нашей проблемы!❌\n*Шлёпа получает очень '
                                      f'маленькую зарплату 💰! ({money} флоппо-коинов)*', parse_mode='Markdown')

    if call.data == 'fertilizer':
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        problem = current_farm_problem

        if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
            remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите (/myfloppa - узнать '
                                      f'время)*', parse_mode='Markdown')
            return

        config.last_work_time[user_id] = datetime.now()

        if 'не могут вырасти' in problem:
            money = 100
            salary(call, money)
            bot.send_message(chat_id, f'Ура! *Кусты наконец-то начали рости.* 🎉 Шлёпа получил достойную зарплату' 
                                      f'({money} флоппо-коинов) 💰!', parse_mode='Markdown')

        else:
            money = 30
            salary(call, money)
            bot.send_message(chat_id, f'Это никак не помогло решению нашей проблемы!❌\n*Шлёпа получает очень '
                                      f'маленькую зарплату 💰! ({money} флоппо-коинов)*', parse_mode='Markdown')

    if call.data == 'weed':
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        problem = current_farm_problem

        if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
            remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите (/myfloppa - узнать '
                                      f'время)*', parse_mode='Markdown')
            return

        config.last_work_time[user_id] = datetime.now()

        if 'заросла сорняком' in problem:
            money = 100
            salary(call, money)
            bot.send_message(chat_id, f'Отлично! *Теперь тут чисто. 🧹*\nШлёпа получил достойную зарплату ({money} '
                                      f'флоппо-коинов) 💰!',
                             parse_mode='Markdown')

        else:
            money = 30
            salary(call, money)
            bot.send_message(chat_id, f'Это никак не помогло решению нашей проблемы!❌\n*Шлёпа получает очень '
                                      f'маленькую зарплату 💰! ({money} флоппо-коинов)*', parse_mode='Markdown')

    if call.data == 'collection':
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        problem = current_farm_problem

        if user_id in config.last_work_time and (datetime.now() - config.last_work_time[user_id]).seconds < 3600:
            remaining_time = timedelta(seconds=3600 - (datetime.now() - config.last_work_time[user_id]).seconds)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            bot.send_message(chat_id, f'Шлёпа уже работал недавно.😾 *Пожалуйста, подождите (/myfloppa - узнать '
                                      f'время)*', parse_mode='Markdown')
            return

        config.last_work_time[user_id] = datetime.now()

        if 'обильные кусты' in problem:
            money = 100
            salary(call, money)
            bot.send_message(chat_id, f'*Ухх, сколько мяты собрано!🌱* Шлёпа получил достойную зарплату'
                                      f'({money} флоппо-коинов) 💰!', parse_mode='Markdown')

        else:
            money = 30
            salary(call, money)
            bot.send_message(chat_id, f'Это никак не помогло решению нашей проблемы!❌\n*Шлёпа получает очень '
                                      f'маленькую зарплату 💰! ({money} флоппо-коинов)*', parse_mode='Markdown')
