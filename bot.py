import datetime
import os
import glob
import re
import sqlite3 as sq
import asyncio
import json
import random
from datetime import timedelta
import pytz


from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


bot = Bot(token='7540561391:AAH-2_dRdlpGjI34JDC5pBb-0SOCsT5My3A')
dp = Dispatcher()
router = Router()
dp.include_router(router)


base = sq.connect('stats.db')
cur = base.cursor()
base.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, win INTEGER, loose INTEGER, draw INTEGER, logs TEXT)')
base.commit()


l = []
active = False


@router.message(Command('blackjack'))
async def blackjack(message: types.Message):
    if '@' in message.text:
        name = message.text[message.text.index('@'):]
        if name == '@VladislavZili':
            id = 673615097
            await message.answer(f'{name}, @{message.from_user.username} вызывает тебя в Блекджек!')

    deck = ['2','3','4','5','6','7','8','9','10','10','10','10','11']*4
    c1 = random.choice(deck)
    deck.remove(c1)
    c2 = random.choice(deck)
    deck.remove(c2)
    d1 = random.choice(deck)
    deck.remove(d1)
    d2 = random.choice(deck)
    deck.remove(d2)
    sum = int(c1) + int(c2)
    kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Еще', callback_data='add')).add(InlineKeyboardButton(text='Хватит', callback_data='enough')).as_markup()
    m = await message.answer(f'Ваши карты: {c1} {c2} - {sum}\nКарты дилера: {d1} XX - {d1}', reply_markup=kb)
    file = open(f'{m.message_id}.txt', 'a+')
    file.write(' '.join(deck) + '\n')
    file.write(f'{c1} {c2}\n{d1} {d2}' + '\n')
    file.write(f'{str(message.from_user.id)}')
    file.close()
    await asyncio.sleep(3600)
    os.remove(f'{m.message_id}.txt')


@router.callback_query(F.data == 'add')
async def add_card(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Еще', callback_data='add')).add(InlineKeyboardButton(text='Хватит', callback_data='enough')).as_markup()
    file = open(f'{callback.message.message_id}.txt', 'a+')
    file.seek(0)
    deck = file.readline()[:-1].split(' ')
    c = file.readline()[:-1].split(' ')
    d = file.readline()[:-1].split(' ')
    u = file.readline()
    if callback.from_user.id != int(u):
        return
    new_c = random.choice(deck)
    deck.remove(new_c)
    c.append(new_c)
    file.close()
    open(f'{callback.message.message_id}.txt', 'w').close()
    file = open(f'{callback.message.message_id}.txt', 'a+')
    file.write(' '.join(deck) + '\n')
    file.write(f'{" ".join(c)}\n{" ".join(d)}' + '\n')
    file.write(f'{str(callback.from_user.id)}')
    file.close()
    sum = 0
    sum1 = 0
    for i in d:
        sum1 += int(i)
    for i in c:
        sum += int(i)
    if sum > 21:
        if '11' in c:
            ind = c.index('11')
            c.pop(ind)
            c.insert(ind, '1')
            open(f'{callback.message.message_id}.txt', 'w').close()
            file = open(f'{callback.message.message_id}.txt', 'a+')
            file.write(' '.join(deck) + '\n')
            file.write(f'{" ".join(c)}\n{" ".join(d)}' + '\n')
            file.write(f'{str(callback.from_user.id)}')
            file.close()
            sum -= 10
            await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum}\nКарты дилера: {d[0]} XX - {d[0]}', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
        else:
            await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum}\nКарты дилера: {" ".join(d)} - {sum1}', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
            # sum = 0
            # for i in d:
            #     sum += int(i)
            # while (sum < 17):
            #     new_d = random.choice(deck)
            #     deck.remove(new_d)
            #     d.append(new_d)
            #     await asyncio.sleep(1.5)
            #     await bot.edit_message_text(f'Ваши карты: {" ".join(c)}\nКарты дилера: {" ".join(d)}', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
            #     sum += int(new_d)
            # if sum > 21:
            #     kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Новая игра', callback_data='newgame')).as_markup()
            #     await bot.edit_message_text(f'Ваши карты: {" ".join(c)}\nКарты дилера: {" ".join(d)}\n\nПовезло тебе, лошара!', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
            # else:
            kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Новая игра', callback_data='newgame')).as_markup()
            await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum}\nКарты дилера: {" ".join(d)} - {sum1}\n\nЛох, перебрал!', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
    elif sum == 21:
        kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Новая игра', callback_data='newgame')).as_markup()
        await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum}\nКарты дилера: {" ".join(d)} - {sum1}\n\nПобеда!', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
    else:
        await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum}\nКарты дилера: {d[0]} XX - {d[0]}', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == 'enough')
async def enough_cards(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Новая игра', callback_data='newgame')).as_markup()
    file = open(f'{callback.message.message_id}.txt', 'a+')
    file.seek(0)
    deck = file.readline()[:-1].split(' ')
    c = file.readline()[:-1].split(' ')
    d = file.readline()[:-1].split(' ')
    u = file.readline()
    if callback.from_user.id != int(u):
        return
    sum = 0
    sum1 = 0
    for i in c:
        sum1 += int(i)
    for i in d:
        sum += int(i)
    await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum1}\nКарты дилера: {" ".join(d)} - {sum}', None, callback.message.chat.id, callback.message.message_id)
    while (sum < 17):
        new_d = random.choice(deck)
        deck.remove(new_d)
        d.append(new_d)
        await asyncio.sleep(1.5)
        await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum1}\nКарты дилера: {" ".join(d)} - {sum}', None, callback.message.chat.id, callback.message.message_id)
        sum += int(new_d)
    if sum > 21:
        await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum1}\nКарты дилера: {" ".join(d)} - {sum}\n\nПовезло тебе, лошара!', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
    else:
        if sum > sum1:
            await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum1}\nКарты дилера: {" ".join(d)} - {sum}\n\nНедобрал, лошара!', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
        else:
            await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum1}\nКарты дилера: {" ".join(d)} - {sum}\n\nПовезло тебе, лошара!', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)


@router.callback_query(F.data == 'newgame')
async def newgame(callback: types.CallbackQuery):
    file = open(f'{callback.message.message_id}.txt', 'a+')
    file.seek(0)
    deck = file.readline()[:-1].split(' ')
    c = file.readline()[:-1].split(' ')
    d = file.readline()[:-1].split(' ')
    u = file.readline()
    if callback.from_user.id != int(u):
        return
    open(f'{callback.message.message_id}.txt', 'w').close()
    deck = ['2','3','4','5','6','7','8','9','10','10','10','10','11']*4
    c1 = random.choice(deck)
    deck.remove(c1)
    c2 = random.choice(deck)
    deck.remove(c2)
    d1 = random.choice(deck)
    deck.remove(d1)
    d2 = random.choice(deck)
    deck.remove(d2)
    sum = int(c1) + int(c2)
    kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Еще', callback_data='add')).add(InlineKeyboardButton(text='Хватит', callback_data='enough')).as_markup()
    await bot.edit_message_text(f'Ваши карты: {c1} {c2} - {sum}\nКарты дилера: {d1} XX - {d1}', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
    file = open(f'{callback.message.message_id}.txt', 'a+')
    file.write(' '.join(deck) + '\n')
    file.write(f'{c1} {c2}\n{d1} {d2}' + '\n')
    file.write(f'{str(callback.from_user.id)}')
    file.close()


@router.message(Command('rasstrel'))
async def rasstrel(message: types.Message):
    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    status = user.status
    if message.from_user.id == 7187106984 or status == 'administrator' or status == 'owner' or status == 'creator':
        try:
            userid = int(re.search('\d+', message.text).group())
            await bot.restrict_chat_member(message.chat.id, userid, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(seconds=1))
            user = await bot.get_chat_member(message.chat.id, userid)
            await message.answer(f'@{user.user.username} был расстрелян!')
        except:
                await message.answer('ГОООООООООООООООООООООООООООООЛ')
                file = open('users.txt', 'a+')
                file.seek(0)
                users = file.readlines()
                file.close()
                users = [x[0:-1] for x in users]
                for i in users:
                    user = await bot.get_chat_member(message.chat.id, int(i))
                    status = user.status
                    if status != 'creator' and status != 'owner' and status != 'administrator':
                        await bot.restrict_chat_member(message.chat.id, int(i), permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(seconds=1))


@router.message(Command('unmute'))
async def unmute(message: types.Message):
    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    status = user.status
    if message.from_user.id == 7187106984 or status == 'administrator' or status == 'owner' or status == 'creator':
        try:
            userid = int(re.search('\d+', message.text).group())
            await bot.restrict_chat_member(message.chat.id, userid, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(seconds=90))
            user = await bot.get_chat_member(message.chat.id, userid)
            await message.answer(f'@{user.user.username} был помилован!')
        except:
                file = open('users.txt', 'a+')
                file.seek(0)
                users = file.readlines()
                file.close()
                users = [x[0:-1] for x in users]
                text = ''
                for i in users:
                    user = await bot.get_chat_member(message.chat.id, int(i))
                    user_status = user.status
                    if user_status == 'restricted':
                        await bot.restrict_chat_member(message.chat.id, user.user.id, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(seconds=90))
                await message.answer('Все помилованы!')


@router.message(Command('mutes'))
async def mutes(message: types.Message):
    file = open('users.txt', 'a+')
    file.seek(0)
    users = file.readlines()
    file.close()
    users = [x[0:-1] for x in users]
    text = ''
    for i in users:
        user = await bot.get_chat_member(message.chat.id, int(i))
        user_status = user.status
        user_id = user.user.id
        if user_status == 'restricted':
            name = user.user.username
            if user.user.username == None: name = 'None'
            text = text + name + f' [{user_id}]' ' - ' + (user.until_date + timedelta(hours=3)).strftime("%d/%m/%Y, %H:%M:%S") + '\n'
    if text == '': text = 'Все свободны! УРАААААААААААААААААА!'
    await message.answer(text)


@router.message(Command('suggest'))
async def suggest(message: types.Message):
    file = open('suggest.txt', 'a+', encoding="utf-8")
    idea = "@" + message.from_user.username + ' - ' + message.text[9:]
    file.write(idea + '\n')
    file.close()


@router.message(Command('roulette'))
async def roulette(message: types.Message):
    global active
    if active:
        return
    else:
        active = True
    kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Участвую', callback_data='u')).add(InlineKeyboardButton(text='Я не приду', callback_data='n')).as_markup()
    bot_message = await message.answer('Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Победитель дарит проигравшему гифт!\n\nСтарт через 60', reply_markup=kb)
    message_id = bot_message.message_id
    s = 60
    for i in range(10):
        file = open('roulette.txt', 'a+')
        file.seek(0)
        users = file.readlines()
        file.close()
        users = ''.join(users)
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nУчастники:\n{users}\n\nСтарт через {s}', reply_markup=kb, chat_id=-1002326046662, message_id=message_id)
        await asyncio.sleep(6)
        s -= 6
        if s == 0:
            break
    file = open('roulette.txt', 'a+')
    file.seek(0)
    users = file.readlines()
    file.close()
    users = [x[0:-1] for x in users]
    if len(users) < 2:
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nНедостаточно игроков(', chat_id=-1002326046662, message_id=message_id)
        file = open('roulette.txt', 'w')
        file.close()
        await asyncio.sleep(60)
        active = False
        return
    for i in range(3):
        winner = random.choice(users)
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}', chat_id=-1002326046662, message_id=message_id)
        await asyncio.sleep(0.5)
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: ', chat_id=-1002326046662, message_id=message_id)
        await asyncio.sleep(0.5)
    await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}', chat_id=-1002326046662, message_id=message_id)
    users.remove(winner)
    if len(users) == 1:
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}\nЛузер: {users[0]}', chat_id=-1002326046662, message_id=message_id)
        file = open('roulette.txt', 'w')
        file.close()
        await asyncio.sleep(60)
        active = False
    else:
        for i in range(3):
            looser = random.choice(users)
            await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}\nЛузер: {looser}', chat_id=-1002326046662, message_id=message_id)
            await asyncio.sleep(0.5)
            await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}\nЛузер: ', chat_id=-1002326046662, message_id=message_id)
            await asyncio.sleep(0.5)
    await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}\nЛузер: {looser}', chat_id=-1002326046662, message_id=message_id)
    file = open('roulette.txt', 'w')
    file.close()

    win = cur.execute('SELECT win FROM users WHERE username == ?', (winner[1:],)).fetchone()[0]
    win += 1
    cur.execute('UPDATE users SET win == ? WHERE username == ?', (win, winner[1:]))
    logs = cur.execute('SELECT logs FROM users WHERE username == ?', (winner[1:],)).fetchone()[0]
    logs += f"Победа в рулетке над {looser[1:]} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M:%S')}\n"
    cur.execute('UPDATE users SET logs == ? WHERE username == ?', (logs, winner[1:]))
    base.commit()

    loose = cur.execute('SELECT loose FROM users WHERE username == ?', (looser[1:],)).fetchone()[0]
    loose += 1
    cur.execute('UPDATE users SET loose == ? WHERE username == ?', (loose, looser[1:]))
    logs = cur.execute('SELECT logs FROM users WHERE username == ?', (looser[1:],)).fetchone()[0]
    logs += f"Поражение в рулетке от {winner[1:]} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M:%S')}\n"
    cur.execute('UPDATE users SET logs == ? WHERE username == ?', (logs, looser[1:]))
    base.commit()

    await asyncio.sleep(60)
    active = False


@router.callback_query(F.data == 'u')
async def u(callback: types.CallbackQuery):
    try:
        cur.execute('INSERT INTO users (username, win, loose, draw, logs) VALUES(?,?,?,?,?)', (callback.from_user.username, 0, 0, 0, ''))
        base.commit()
    except:
        pass # user already recorded
    user = callback.from_user.username
    file = open('roulette.txt', 'a+')
    file.seek(0)
    users = file.readlines()
    users = [x[0:-1] for x in users]
    if '@' + str(user) not in users:
        file.write('@' + str(user) + '\n')
        users.append('@' + str(user))
    file.close()
    await callback.answer()


@router.callback_query(F.data == 'n')
async def n(callback: types.CallbackQuery):
    user = callback.from_user.username
    file = open('roulette.txt', 'a+')
    file.seek(0)
    users = file.readlines()
    users = [x for x in users]
    if '@' + str(user) + '\n' in users:
        users.remove('@' + str(user) + '\n')
    file.close()
    file = open('roulette.txt', 'w')
    file.write(''.join(users))
    file.close()
    await callback.answer()


@router.message(Command('mystats'))
async def stats(message: types.Message):
    user = message.from_user.username
    try:
        stats = cur.execute('SELECT * FROM users WHERE username == ?',(message.from_user.username,)).fetchone()
        username = stats[0]
        # text = '--' * len(username)
        text = '[Победы:Поражения:Ничьи]\n'
        text += str(stats[0]) + ': '
        for i in stats[1:4]:
            text += str(i) + ':'
        text = text[:-1]
        text += '\n'
        for i in stats[4:]:
            text += i + '\n'
        await message.answer(text)
    except:
        await message.answer('У вас ничего нет!')


@router.message(Command('stats'))
async def stats(message: types.Message):
    try:
        stats = cur.execute('SELECT * FROM users').fetchall()
    except:
        pass
    # usernames = cur.execute('SELECT username FROM users').fetchall()
    # usernames = [i[0] for i in usernames]
    # text = '--' * len(max(usernames, key=len))
    text = '[Победы:Поражения:Ничьи]\n'
    for i in stats:
        # username = i[0] + ' ' + '-' * (len(max(usernames, key=len)) - len(i[0])) + '---------' + ' '
        text += i[0] + ': '
        for j in i[1:4]:
            text += str(j) + ':'
        text = text[:-1]
        text += '\n'
    await message.answer(text)


@router.message(Command('duel'))
async def duel(message: types.Message):
    try:
        user = message.from_user.id
        cur.execute('INSERT INTO users (username, win, loose, draw, logs) VALUES(?,?,?,?,?)', (message.from_user.username, 0, 0, 0, ''))
        base.commit()
    except:
        pass # user already recorded
    kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Стреляться!', callback_data='s')).as_markup()
    await message.answer(f'@{message.from_user.username} вызывает на дуэль!\n\nПравила дуэли: проигравший дарит победителю гифт. Не участвуйте в дуэлях, если не сможете подарить гифт, иначе будете чушпанами!', reply_markup=kb)


@router.callback_query(F.data == 's')
async def d(callback: types.CallbackQuery):
    duelist = callback.message.text.split(' ')[0][1:]
    try:
        cur.execute('INSERT INTO users (username, win, loose, draw, logs) VALUES(?,?,?,?,?)', (callback.from_user.username, 0, 0, 0, ''))
    except:
        pass
    base.commit()
    r = random.randint(1,3)
    match r:
        case 1:
            await bot.edit_message_text(text=f'@{duelist} пристрелил @{callback.from_user.username} и заслужил от него гифт!', chat_id=callback.message.chat.id, message_id=callback.message.message_id)

            win = cur.execute('SELECT win FROM users WHERE username == ?', (duelist,)).fetchone()[0]
            win += 1
            cur.execute('UPDATE users SET win == ? WHERE username == ?', (win, duelist))
            logs = cur.execute('SELECT logs FROM users WHERE username == ?', (duelist,)).fetchone()[0]
            logs += f"Победа над {callback.from_user.username} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M:%S')}\n"
            cur.execute('UPDATE users SET logs == ? WHERE username == ?', (logs, duelist))
            base.commit()

            loose = cur.execute('SELECT loose FROM users WHERE username == ?', (callback.from_user.username,)).fetchone()[0]
            loose += 1
            cur.execute('UPDATE users SET loose == ? WHERE username == ?', (loose, callback.from_user.username))
            logs = cur.execute('SELECT logs FROM users WHERE username == ?', (callback.from_user.username,)).fetchone()[0]
            logs += f"Поражение от {duelist} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M:%S')}\n"
            cur.execute('UPDATE users SET logs == ? WHERE username == ?', (logs, callback.from_user.username))
            base.commit()

        case 2:
            await bot.edit_message_text(text=f'@{callback.from_user.username} поставил раком @{duelist} и вправе требовать от него подарок!', chat_id=callback.message.chat.id, message_id=callback.message.message_id)

            win = cur.execute('SELECT win FROM users WHERE username == ?', (callback.from_user.username,)).fetchone()[0]
            win += 1
            cur.execute('UPDATE users SET win == ? WHERE username == ?', (win, callback.from_user.username))
            logs = cur.execute('SELECT logs FROM users WHERE username == ?', (callback.from_user.username,)).fetchone()[0]
            logs += f"Победа над {duelist} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M:%S')}\n"
            cur.execute('UPDATE users SET logs == ? WHERE username == ?', (logs, callback.from_user.username))
            base.commit()

            loose = cur.execute('SELECT loose FROM users WHERE username == ?', (duelist,)).fetchone()[0]
            loose += 1
            cur.execute('UPDATE users SET loose == ? WHERE username == ?', (loose, duelist))
            logs = cur.execute('SELECT logs FROM users WHERE username == ?', (duelist,)).fetchone()[0]
            logs += f"Поражение от {callback.from_user.username} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M:%S')}\n"
            cur.execute('UPDATE users SET logs == ? WHERE username == ?', (logs, duelist))
            base.commit()

        case 3:
            await bot.edit_message_text(text=f'@{callback.from_user.username} и @{duelist} убили друг друга и находятся в паритете!', chat_id=callback.message.chat.id, message_id=callback.message.message_id)

            draw = cur.execute('SELECT draw FROM users WHERE username == ?', (callback.from_user.username,)).fetchone()[0]
            draw += 1
            cur.execute('UPDATE users SET draw == ? WHERE username == ?', (draw, callback.from_user.username))
            logs = cur.execute('SELECT logs FROM users WHERE username == ?', (callback.from_user.username,)).fetchone()[0]
            logs += f"Ничья с {duelist} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M:%S')}\n"
            cur.execute('UPDATE users SET logs == ? WHERE username == ?', (logs, callback.from_user.username))
            base.commit()

            draw = cur.execute('SELECT draw FROM users WHERE username == ?', (duelist,)).fetchone()[0]
            draw += 1
            cur.execute('UPDATE users SET draw == ? WHERE username == ?', (draw, duelist))
            logs = cur.execute('SELECT logs FROM users WHERE username == ?', (duelist,)).fetchone()[0]
            logs += f"Ничья с {callback.from_user.username} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M:%S')}\n"
            cur.execute('UPDATE users SET logs == ? WHERE username == ?', (logs, duelist))
            base.commit()

    await callback.answer()


@router.callback_query(F.data == 'bye')
async def bye(callback: types.CallbackQuery):
    username = re.search('@\w*,', callback.message.text).group()[:-1]
    if callback.from_user.username == username:
        await bot.send_message(callback.message.chat.id, f'{username} трусливо сбежал! Гоните его! Насмехайтесь над ним!')
    await callback.answer()


@router.callback_query(F.data == 'shoot')
async def shootduel(callback: types.CallbackQuery):
    username1 = re.search('@\w*,', callback.message.text).group()[:-1]
    if '@' + callback.from_user.username != username1:
        return
    userid1 = callback.from_user.id

    file = open('members.txt', 'r')
    user_seq = file.readlines()
    file.close()
    user_seq = [x[:-1] for x in user_seq]
    user_dict = {x[0] : x[1] for x in [i.split(':') for i in user_seq]}
    username2 = re.search(' @\w*', callback.message.text).group()[1:]
    userid2 = user_dict[username2]

    d = {username1:userid1, username2:userid2}

    opponents = [username1, username2]
    dead = random.choice(opponents)
    opponents.remove(dead)

    mute_hours_seq = [x for x in range(1, 9)]
    mute_hours = random.choice(mute_hours_seq)
    hours_declension = dict(sorted(list({key: 'час' for key in [1,21]}.items()) +
                            list({key: 'часа' for key in [2,3,4,22,23,24]}.items()) +
                            list({key: 'часов' for key in [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]}.items())))

    await callback.message.delete_reply_markup()
    await bot.send_message(callback.message.chat.id, f'{opponents[0]} отправил {dead} в Вальгаллу на {mute_hours} {hours_declension[mute_hours]}. {dead}, Ваше последнее слово?')
    await asyncio.sleep(10)
    gif = FSInputFile('buckshot-roulette.mp4')
    await bot.send_video(callback.message.chat.id, video=gif)
    await bot.restrict_chat_member(callback.message.chat.id, d[dead], permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(hours=mute_hours))

    await callback.answer()


@router.message(Command('shoot'))
async def shoot(message: types.Message):
    user = message.from_user.id

    # checking for 60 sec cooldown
    if user in l:
        return
    l.append(user)

    # checking for shoot with another member
    file = open('members.txt', 'r')
    user_seq = file.readlines()
    file.close()
    user_seq = [x[:-1] for x in user_seq]
    user_dict = {x[0] : x[1] for x in [i.split(':') for i in user_seq]}
    username = re.search(' @\w*', message.text)
    if username != None:
        username = username.group()[1:]
        try:
            user = await bot.get_chat_member(message.chat.id, int(user_dict[username]))
        except:
            pass
        else:
            kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text='Стрелять!', callback_data='shoot')).row(InlineKeyboardButton(text='Не чето не хочу пока', callback_data='bye')).as_markup()
            await message.answer(f'@{user.user.username}, @{message.from_user.username} вызывает Вас на дуэль! Проигравший отправится отдыхать на срок 1 до 24 часов!', reply_markup=kb)
            return


    # get members.txt from file: contains list of members.txt who whenever used command /shoot only
    file = open('users.txt', 'a+')
    file.seek(0)
    users_id = file.readlines()
    users_id = [x[0:-1] for x in users_id]
    if str(user) not in users_id:
        file.write(str(user) + '\n')
        users_id.append(str(user))
    file.close()

    # duration of mute in minutes
    mute_hours_seq = [x for x in range(1, 25)]
    mute_hours = random.choice(mute_hours_seq)
    hours_declension = dict(sorted(list({key: 'час' for key in [1,21]}.items()) +
                            list({key: 'часа' for key in [2,3,4,22,23,24]}.items()) +
                            list({key: 'часов' for key in [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]}.items())))


    # russian roulette for mute [1h-24h]
    shot1 = random.randint(1, 6)
    if shot1 == 1:
        await message.answer(f'Увы! Мут на {mute_hours} {hours_declension[mute_hours]}. Ваше последнее слово?')
        await asyncio.sleep(10)
        gif = FSInputFile('buckshot-roulette.mp4')
        await bot.send_video(message.chat.id, video=gif)
        await bot.restrict_chat_member(message.chat.id, message.from_user.id, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(hours=mute_hours))
    else:
        await message.answer('В этот раз Вам повезло! Или нет? Как знать...')


    # russian roulette for mute [1h-24h] - miss in another member
    shot2 = random.randint(1, 24)
    if shot2 == 1:
        unlucky_user_id = random.choice(users_id)
        unlucky_user = await bot.get_chat_member(message.chat.id, int(unlucky_user_id))
        unlucky_username = unlucky_user.user.username
        unlucky_user_status = unlucky_user.status
        if unlucky_user_status == 'restricted':
            bantime = unlucky_user.until_date + timedelta(hours=mute_hours)
        else:
            bantime = mute_hours

        if shot1 == 1:
            await message.answer(f'@{message.from_user.username} прошил себя насквозь и зацепил @{unlucky_username}, уложив его спать на {mute_hours} {hours_declension[mute_hours]}! @{unlucky_username}, Ваше последнее слово?')
            await asyncio.sleep(10)
            gif = FSInputFile('buckshot-roulette.mp4')
            await bot.send_video(message.chat.id, video=gif)
            await bot.restrict_chat_member(message.chat.id, int(unlucky_user_id), permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=bantime)

        else:
            await message.answer(f'@{message.from_user.username} промахнулся и попал в @{unlucky_username} и подарил ему мут на {mute_hours} {hours_declension[mute_hours]}! @{unlucky_username}, Ваше последнее слово?')
            await asyncio.sleep(10)
            gif = FSInputFile('buckshot-roulette.mp4')
            await bot.send_document(message.chat.id, gif)
            await bot.restrict_chat_member(message.chat.id, int(unlucky_user_id), permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=bantime)

    await asyncio.sleep(300)
    l.remove(user)


@router.message(F.text.lower().startswith(('кто ', 'кого ', 'кому ', 'кем ', 'о ком ')).endswith('?'))
async def hui(message: types.Message):
    file = open('all_users.txt', 'a+')
    file.seek(0)
    users = file.readlines()
    users = [x[0:-1] for x in users]
    user = random.choice(users)
    await message.answer('@' + user + f' {message.text[4:].replace("мне", "тебе").replace("меня", "тебя").replace("мной", "тобой").replace("мой", "твой").replace("мою", "твою").replace("мое", "твое").replace("мои", "твои")}')


@router.message(F.text.lower() == 'мяф')
async def hui(message: types.Message):
    myafs = [FSInputFile('myaf1.mp4'), FSInputFile('myaf2.mp4'), FSInputFile('myaf3.mp4'), FSInputFile('myaf4.mp4'), FSInputFile('myaf5.mp4'), FSInputFile('myaf6.mp4'), FSInputFile('myaf7.mp4'), FSInputFile('myaf8.mp4')]
    gif = random.choice(myafs)
    await bot.send_document(message.chat.id, gif)


# @router.message(F.text.lower().contains('ху'))
# async def hui(message: types.Message):
#
#     file = open('all_users.txt', 'a+')
#     user = message.from_user.username
#     file.seek(0)
#     users = file.readlines()
#     users = [x[0:-1] for x in users]
#     if str(user) not in users:
#         file.write(str(user) + '\n')
#     file.close()
#     await message.answer(message.text)


# async def gol():
#     while True:
#         r = random.randint(1,1)
#         if r == 1:
#             await bot.send_audio(-1002326046662, FSInputFile('goooool.mp3'), caption='ГООООООООООООЛ')
#             await asyncio.sleep(1800)


@router.message(Command('members'))
async def get_members(message: types.Message):
    file = open('members.txt', 'a+')
    file.seek(0)
    members = file.readlines()
    text = ''.join(members)
    file.close()
    await message.answer(text)


async def main():
    # file = open('users.txt', 'a+')
    # file.seek(0)
    # users = file.readlines()
    # users = [x[0:-1] for x in users]
    # file.close()
    # for i in users:
    #     user = await bot.get_chat_member(-1002326046662, i)
    #     print(i, user.user.username)
    # await bot.restrict_chat_member(-1002326046662, 7187106984, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(seconds=90))

    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))


for i in glob.glob('[0-9]*.txt'):
    os.remove(i)
asyncio.run(main())
