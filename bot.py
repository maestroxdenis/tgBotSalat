import csv
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
import pymssql

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import User
# Define connection parameters
server = 'testdbsqltgbot.database.windows.net'
database = 'testdbsqltgbot'
username = 'tgsalat'
password = 'salattg1!'

bot = Bot(token='7540561391:AAH-2_dRdlpGjI34JDC5pBb-0SOCsT5My3A')
dp = Dispatcher()
router = Router()
dp.include_router(router)

# old db
#base2 = sq.connect('stats.db')
#cur = base2.cursor()
#base2.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, win INTEGER, loose INTEGER, draw INTEGER, logs TEXT)')
#base2.commit()
# old db

baseInit = pymssql.connect(server, username, password, database)

cursorInit = baseInit.cursor()
cursorInit.execute('''
               IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'users' AND TABLE_SCHEMA = 'dbo')
               BEGIN
                   CREATE TABLE users(userId BIGINT PRIMARY KEY, username TEXT DEFAULT '', firstname TEXT, lastname TEXT, insertDateTime datetime DEFAULT GETUTCDATE(), everShoot SMALLINT DEFAULT 0)
               END;
               ''')
baseInit.commit()

cursorInit.execute('''
               IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'casinoLogs' AND TABLE_SCHEMA = 'dbo')
               BEGIN
                   CREATE TABLE casinoLogs (logId BIGINT  IDENTITY(1,1) PRIMARY KEY, userId BIGINT, rival BIGINT, state SMALLINT, insertDateTime datetime DEFAULT GETUTCDATE()) -- 0 loose, 1 win, 2 draw'
               END;
               ''')
baseInit.commit()

query = "SELECT userId, username, firstName, lastName, everShoot FROM users"

cursorInit.execute(query)

rows = cursorInit.fetchall()
cursorInit.close()
baseInit.close()

users = {
    int(row[0]): {
        "username": str(row[1]),
        "firstname": str(row[2]),
        "lastname": str(row[3]),
        "displayName": f"@{str(row[1])}" if row[1] != '' and row[1] != None else f"{str(row[2])} {str(row[3])}",
        "everShoot": bool(row[4])
    }
    for row in rows
}


l = []
active = False

def createUserIfNotExist(fromUser: User):
    if not fromUser.id in users:
        base = None
        cursor = None
        try:
            base = pymssql.connect(server, username, password, database)
            cursor = base.cursor()
            cursor.execute('INSERT INTO users (userId, username, firstname, lastname, everShoot) VALUES(%s,%s,%s,%s,%s)', (fromUser.id, fromUser.username, fromUser.first_name, fromUser.last_name, 0))
            users[fromUser.id] = {
                "username": fromUser.username,
                "firstname": fromUser.first_name,
                "lastname": fromUser.last_name,
                "displayName": f"@{fromUser.username}" if fromUser.username else f"{fromUser.first_name} {fromUser.last_name}",
                "everShoot": False
            }
            base.commit()
        except:
            base.rollback()
            pass
        finally:
            if cursor:
                cursor.close()
            if base:
                base.close()

@router.message(Command('blackjack'))
async def blackjack(message: types.Message):
    if '@' in message.text:
        name = message.text[message.text.index('@'):]
        if name == '@VladislavZili':
            id = 673615097
            await message.answer(f'{name}, @{message.from_user.username} вызывает тебя в Блекджек!')

    deck = ['2', '3', '4', '5', '6', '7', '8', '9', '10', '10', '10', '10', '11'] * 4
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


"""
Переписать под двух игроков, добавить ограничение на апдейты (20 в минуту)
"""


# @router.callback_query(F.data == 'add')
# async def add_card(callback: types.CallbackQuery):
#     kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Еще', callback_data='add')).add(InlineKeyboardButton(text='Хватит', callback_data='enough')).as_markup()
#     file = open(f'{callback.message.message_id}.txt', 'a+')
#     file.seek(0)
#     deck = file.readline()[:-1].split(' ')
#     c = file.readline()[:-1].split(' ')
#     d = file.readline()[:-1].split(' ')
#     u = file.readline()
#     if callback.from_user.id != int(u):
#         return
#     new_c = random.choice(deck)
#     deck.remove(new_c)
#     c.append(new_c)
#     file.close()
#     open(f'{callback.message.message_id}.txt', 'w').close()
#     file = open(f'{callback.message.message_id}.txt', 'a+')
#     file.write(' '.join(deck) + '\n')
#     file.write(f'{" ".join(c)}\n{" ".join(d)}' + '\n')
#     file.write(f'{str(callback.from_user.id)}')
#     file.close()
#     sum = 0
#     sum1 = 0
#     for i in d:
#         sum1 += int(i)
#     for i in c:
#         sum += int(i)
#     if sum > 21:
#         if '11' in c:
#             ind = c.index('11')
#             c.pop(ind)
#             c.insert(ind, '1')
#             open(f'{callback.message.message_id}.txt', 'w').close()
#             file = open(f'{callback.message.message_id}.txt', 'a+')
#             file.write(' '.join(deck) + '\n')
#             file.write(f'{" ".join(c)}\n{" ".join(d)}' + '\n')
#             file.write(f'{str(callback.from_user.id)}')
#             file.close()
#             sum -= 10
#             await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum}\nКарты дилера: {d[0]} XX - {d[0]}', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
#         else:
#             await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum}\nКарты дилера: {" ".join(d)} - {sum1}', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
#             # sum = 0
#             # for i in d:
#             #     sum += int(i)
#             # while (sum < 17):
#             #     new_d = random.choice(deck)
#             #     deck.remove(new_d)
#             #     d.append(new_d)
#             #     await asyncio.sleep(1.5)
#             #     await bot.edit_message_text(f'Ваши карты: {" ".join(c)}\nКарты дилера: {" ".join(d)}', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
#             #     sum += int(new_d)
#             # if sum > 21:
#             #     kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Новая игра', callback_data='newgame')).as_markup()
#             #     await bot.edit_message_text(f'Ваши карты: {" ".join(c)}\nКарты дилера: {" ".join(d)}\n\nПовезло тебе, лошара!', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
#             # else:
#             kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Новая игра', callback_data='newgame')).as_markup()
#             await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum}\nКарты дилера: {" ".join(d)} - {sum1}\n\nЛох, перебрал!', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
#     elif sum == 21:
#         kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Новая игра', callback_data='newgame')).as_markup()
#         await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum}\nКарты дилера: {" ".join(d)} - {sum1}\n\nПобеда!', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
#     else:
#         await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum}\nКарты дилера: {d[0]} XX - {d[0]}', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
#     await callback.answer()


# @router.callback_query(F.data == 'enough')
# async def enough_cards(callback: types.CallbackQuery):
#     kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Новая игра', callback_data='newgame')).as_markup()
#     file = open(f'{callback.message.message_id}.txt', 'a+')
#     file.seek(0)
#     deck = file.readline()[:-1].split(' ')
#     c = file.readline()[:-1].split(' ')
#     d = file.readline()[:-1].split(' ')
#     u = file.readline()
#     if callback.from_user.id != int(u):
#         return
#     sum = 0
#     sum1 = 0
#     for i in c:
#         sum1 += int(i)
#     for i in d:
#         sum += int(i)
#     await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum1}\nКарты дилера: {" ".join(d)} - {sum}', None, callback.message.chat.id, callback.message.message_id)
#     while (sum < 17):
#         new_d = random.choice(deck)
#         deck.remove(new_d)
#         d.append(new_d)
#         await asyncio.sleep(1.5)
#         await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum1}\nКарты дилера: {" ".join(d)} - {sum}', None, callback.message.chat.id, callback.message.message_id)
#         sum += int(new_d)
#     if sum > 21:
#         await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum1}\nКарты дилера: {" ".join(d)} - {sum}\n\nПовезло тебе, лошара!', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
#     else:
#         if sum > sum1:
#             await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum1}\nКарты дилера: {" ".join(d)} - {sum}\n\nНедобрал, лошара!', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
#         else:
#             await bot.edit_message_text(f'Ваши карты: {" ".join(c)} - {sum1}\nКарты дилера: {" ".join(d)} - {sum}\n\nПовезло тебе, лошара!', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
#
#
# @router.callback_query(F.data == 'newgame')
# async def newgame(callback: types.CallbackQuery):
#     file = open(f'{callback.message.message_id}.txt', 'a+')
#     file.seek(0)
#     deck = file.readline()[:-1].split(' ')
#     c = file.readline()[:-1].split(' ')
#     d = file.readline()[:-1].split(' ')
#     u = file.readline()
#     if callback.from_user.id != int(u):
#         return
#     open(f'{callback.message.message_id}.txt', 'w').close()
#     deck = ['2','3','4','5','6','7','8','9','10','10','10','10','11']*4
#     c1 = random.choice(deck)
#     deck.remove(c1)
#     c2 = random.choice(deck)
#     deck.remove(c2)
#     d1 = random.choice(deck)
#     deck.remove(d1)
#     d2 = random.choice(deck)
#     deck.remove(d2)
#     sum = int(c1) + int(c2)
#     kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Еще', callback_data='add')).add(InlineKeyboardButton(text='Хватит', callback_data='enough')).as_markup()
#     await bot.edit_message_text(f'Ваши карты: {c1} {c2} - {sum}\nКарты дилера: {d1} XX - {d1}', None, callback.message.chat.id, callback.message.message_id, reply_markup=kb)
#     file = open(f'{callback.message.message_id}.txt', 'a+')
#     file.write(' '.join(deck) + '\n')
#     file.write(f'{c1} {c2}\n{d1} {d2}' + '\n')
#     file.write(f'{str(callback.from_user.id)}')
#     file.close()


@router.message(Command('rasstrel'))
async def rasstrel(message: types.Message):
    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    status = user.status
    if message.from_user.id == 7187106984 or status == 'administrator' or status == 'owner' or status == 'creator':
        try:
            userid = int(re.search('\d+', message.text).group())
            await bot.restrict_chat_member(message.chat.id, userid, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(seconds=1))
            user = await bot.get_chat_member(message.chat.id, userid)
            createUserIfNotExist(user.user)
            killedDisplayName = users[userid]["displayName"]
            await message.answer(f'{killedDisplayName} был расстрелян!')
        except:
            await message.answer('ГОООООООООООООООООООООООООООООЛ')
            for i in users:
                user = await bot.get_chat_member(message.chat.id, int(i))
                status = user.status
                if status != 'creator' and status != 'owner' and status != 'administrator' and user.user.id != 7187106984:
                    await bot.restrict_chat_member(message.chat.id, int(i), permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(seconds=65))


@router.message(Command('unmute'))
async def unmute(message: types.Message):
    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    status = user.status
    if message.from_user.id == 7187106984 or status == 'administrator' or status == 'owner' or status == 'creator':
        try:
            userid = int(re.search('\d+', message.text).group())
            await bot.restrict_chat_member(message.chat.id, userid, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(seconds=65))
            user = await bot.get_chat_member(message.chat.id, userid)
            await message.answer(f'@{user.user.username} был помилован!')
        except:
            for i in users.keys():
                user = await bot.get_chat_member(message.chat.id, int(i))
                user_status = user.status
                if user_status == 'restricted':
                    await bot.restrict_chat_member(message.chat.id, user.user.id, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(seconds=65))
            await message.answer('Все помилованы!')


@router.message(Command('mutes'))
async def mutes(message: types.Message):
    text = ''
    for i in users.keys():
        user = await bot.get_chat_member(message.chat.id, int(i))
        user_status = user.status
        user_id = user.user.id
        if user_status == 'restricted':
            name = user.user.username
            if user.user.username == None: name = f'{user.user.first_name} {user.user.last_name}'
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
    #reset file if already exists
    file = open('roulette.txt', 'w')
    file.write('')
    file.close()

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
        looser = users[0]
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}\nЛузер: {looser}', chat_id=-1002326046662, message_id=message_id)
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

    base = None
    cursor = None
    try:
        base = pymssql.connect(server, username, password, database)
        cursor = base.cursor()
        cursor.execute('INSERT INTO casinoLogs (userId, rival, state) VALUES(%s,%s,%s)', (winner.split(':')[0], looser.split(':')[0], 1))
        cursor.execute('INSERT INTO casinoLogs (userId, rival, state) VALUES(%s,%s,%s)', (looser.split(':')[0], winner.split(':')[0], 0))
        base.commit()
    except Exception as e:
        print(f"Exception during roulette {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if base:
            base.close()

    await asyncio.sleep(60)
    active = False


@router.callback_query(F.data == 'u')
async def u(callback: types.CallbackQuery):
    createUserIfNotExist(callback.from_user)
    displayName = users[callback.from_user.id]["displayName"]
    user = f'{callback.from_user.id}:{displayName}'
    file = open('roulette.txt', 'a+')
    file.seek(0)
    rouletteUsers = file.readlines()
    rouletteUsers = [x[0:-1] for x in rouletteUsers]
    if user not in rouletteUsers:
        file.write(user + '\n')
    file.close()
    await callback.answer()


@router.callback_query(F.data == 'n')
async def n(callback: types.CallbackQuery):
    displayName = users[callback.from_user.id]["displayName"]
    user = f'{callback.from_user.id}:{displayName}'
    file = open('roulette.txt', 'a+')
    file.seek(0)
    rouletteUsers = file.readlines()
    rouletteUsers = [x for x in rouletteUsers]
    if user + '\n' in rouletteUsers:
        rouletteUsers.remove(user + '\n')
    file.close()
    file = open('roulette.txt', 'w')
    file.write(''.join(rouletteUsers))
    file.close()
    await callback.answer()


@router.message(Command('mystats'))
async def stats(message: types.Message):
    userId = message.from_user.id
    base = None
    cursor = None
    try:
        base = pymssql.connect(server, username, password, database)
        cursor = base.cursor()
        cursor.execute('SELECT userId, rival, state, insertDateTime FROM casinoLogs WHERE userId = %s ORDER BY insertDateTime DESC', (userId))
        rows = cursor.fetchall()

        if len(rows) == 0:
            await message.answer('У вас ничего нет!')

        loose = 0
        win = 0
        draw = 0
        recordsText = ""
        recordedLogs = 0
        for row in rows:
            result = int(row[2])
            resultMessage = ""
            if result == 0:
                loose += 1
                resultMessage = "Поражение от"

            if result == 1:
                win += 1
                resultMessage = "Победа над"
            if result == 2:
                draw += 1
                resultMessage = "Ничья с"

            if recordedLogs < 15:
                recordsText += f'{resultMessage} <a href="https://t.me/{users[int(row[1])]["displayName"][1:]}">{users[int(row[1])]["displayName"][1:]}</a> в {str(row[3].strftime("%H:%M:%S, %d.%m.%Y"))}\n'
                recordedLogs += 1
        text = ' Имя / Победы / Поражения / Ничьи\n'
        text += f'{users[userId]["displayName"]} / {win} / {loose} / {draw}\n{recordsText}'
        await message.answer(text, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        print(f"Exception during mystats {str(e)}")
        await message.answer('У вас ничего нет!')
    finally:
        if cursor:
            cursor.close()
        if base:
            base.close()


@router.message(Command('myfullstats'))
async def myfullstats(message: types.Message):
    userId = message.from_user.id
    base = None
    cursor = None
    try:
        base = pymssql.connect(server, username, password, database)
        cursor = base.cursor()
        cursor.execute('SELECT userId, rival, state, insertDateTime FROM casinoLogs WHERE userId = %s ORDER BY insertDateTime DESC', (userId))
        rows = cursor.fetchall()

        if len(rows) == 0:
            await message.answer('У вас ничего нет!')

        filename = message.from_user.username
        file = open(f'{filename}.txt', 'w', encoding="utf-8")

        loose = 0
        win = 0
        draw = 0
        recordsText = []
        for row in rows:
            result = int(row[2])
            resultMessage = ""
            if result == 0:
                loose += 1
                resultMessage = "Поражение от"

            if result == 1:
                win += 1
                resultMessage = "Победа над"
            if result == 2:
                draw += 1
                resultMessage = "Ничья с"

            recordsText.append(f'{resultMessage} {users[int(row[1])]["displayName"][1:]} в {str(row[3].strftime("%H:%M:%S, %d.%m.%Y"))}\n')

        file.write('Победы / Поражения / Ничьи\n')
        file.write(f'{win} / {loose} / {draw}\n')
        file.writelines(recordsText)
        file.close()
        await bot.send_document(message.chat.id, FSInputFile(f'{filename}.txt'))
        os.remove(f'{filename}.txt')

    except Exception as e:
        print(f"Exception during mystats {str(e)}")
        await message.answer('У вас ничего нет!')
    finally:
        if cursor:
            cursor.close()
        if base:
            base.close()


@router.message(Command('stats'))
async def stats(message: types.Message):
    stats = []
    base = None
    cursor = None
    try:
        base = pymssql.connect(server, username, password, database)
        cursor = base.cursor()
        cursor.execute('''
                            SELECT 
                               userId,
                               SUM(CASE WHEN state = 1 THEN 1 ELSE 0 END) AS win,
                               SUM(CASE WHEN state = 0 THEN 1 ELSE 0 END) AS loose,
                               SUM(CASE WHEN state = 2 THEN 1 ELSE 0 END) AS draw
                             FROM casinoLogs group by userId
                            ''')
        stats = cursor.fetchall()
    except Exception as e:
        print(f"Exception during mystats {str(e)}")
        pass
    finally:
        if cursor:
            cursor.close()
        if base:
            base.close()
    text = ' Имя / Победы / Поражения / Ничьи\n'
    for row in stats:
        text += f'<a href="https://t.me/{users[int(row[0])]["displayName"][1:]}">{users[int(row[0])]["displayName"][1:]}</a>' + " / "
        text += f'{row[1]} / {row[2]} / {row[3]}\n'
    await message.answer(text, parse_mode='HTML', disable_web_page_preview=True)


@router.message(Command('duel'))
async def duel(message: types.Message):
    createUserIfNotExist(message.from_user)
    kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Стреляться!', callback_data=f's|{message.from_user.id}')).as_markup()
    await message.answer(f'@{message.from_user.username} вызывает на дуэль!\n\nПравила дуэли: проигравший дарит победителю гифт. Не участвуйте в дуэлях, если не сможете подарить гифт, иначе будете чушпанами!', reply_markup=kb)


@router.callback_query(lambda query: query.data.startswith('s|'))
async def d(callback: types.CallbackQuery):
    duelist = int(callback.data.split('|')[1])
    fromUser = callback.from_user
    if duelist == fromUser.id:
        await bot.edit_message_text(text=f'{users[duelist]["displayName"]} передумал стреляться и сбежал!', chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        return
    createUserIfNotExist(fromUser)
    r = random.randint(1, 3)    
    base = None
    cursor = None
    try:
        base = pymssql.connect(server, username, password, database)
        cursor = base.cursor()
        match r:
            case 1:
                await bot.edit_message_text(text=f'{users[duelist]["displayName"]} пристрелил {users[callback.from_user.id]["displayName"]} и заслужил от него гифт!', chat_id=callback.message.chat.id, message_id=callback.message.message_id)
                cursor.execute('INSERT INTO casinoLogs (userId, rival, state) VALUES(%s,%s,%s)', (duelist, fromUser.id, 1))
                cursor.execute('INSERT INTO casinoLogs (userId, rival, state) VALUES(%s,%s,%s)', (fromUser.id, duelist, 0))
                base.commit()

            case 2:
                await bot.edit_message_text(text=f'{users[callback.from_user.id]["displayName"]} поставил раком {users[duelist]["displayName"]} и вправе требовать от него подарок!', chat_id=callback.message.chat.id, message_id=callback.message.message_id)
                cursor.execute('INSERT INTO casinoLogs (userId, rival, state) VALUES(%s,%s,%s)', (fromUser.id, duelist, 1))
                cursor.execute('INSERT INTO casinoLogs (userId, rival, state) VALUES(%s,%s,%s)', (duelist, fromUser.id, 0))
                base.commit()

            case 3:
                await bot.edit_message_text(text=f'{users[callback.from_user.id]["displayName"]} и {users[duelist]["displayName"]} убили друг друга и находятся в паритете!', chat_id=callback.message.chat.id, message_id=callback.message.message_id)
                cursor.execute('INSERT INTO casinoLogs (userId, rival, state) VALUES(%s,%s,%s)', (fromUser.id, duelist, 2))
                cursor.execute('INSERT INTO casinoLogs (userId, rival, state) VALUES(%s,%s,%s)', (duelist, fromUser.id, 2))
                base.commit()
    finally:
        if cursor:
            cursor.close()
        if base:
            base.close()
    await callback.answer()


@router.callback_query(F.data == 'bye')
async def bye(callback: types.CallbackQuery):
    username = re.search('@\w*,', callback.message.text).group()[:-1]
    if callback.from_user.username == username:
        await bot.send_message(callback.message.chat.id, f'{username} трусливо сбежал! Гоните его! Насмехайтесь над ним!')
    await callback.answer()


@router.callback_query(F.data == 'bye1')
async def bye1(callback: types.CallbackQuery):
    username = callback.from_user.username
    await bot.send_message(callback.message.chat.id, f'{username} трусливо сбежал! Гоните его! Насмехайтесь над ним!')
    await callback.answer()


@router.callback_query(lambda query: query.data.startswith('shoot|'))
async def shoot_cb(callback: types.CallbackQuery):
    duelInitiator = int(callback.data.split('|')[1])
    duelMember = int(callback.data.split('|')[2])
    if callback.from_user.id != duelMember:
        return
    opponents = [duelInitiator, duelMember]
    dead = random.choice(opponents)
    opponents.remove(dead)

    deadDisplayName = users[dead]["displayName"]
    winnerDisplayName = users[opponents[0]]["displayName"]

    mute_hours_seq = [1] * 173 + [2] * 115 + [3] * 77 + [4] * 51 + [5] * 34 + [6] * 23 + [7] * 15 + [8] * 10 + [9] * 7 + [10] * 5 + [11] * 3 + [12] * 2
    mute_hours = random.choice(mute_hours_seq)
    hours_declension = dict(sorted(list({key: 'час' for key in [1, 21]}.items()) +
                                   list({key: 'часа' for key in [2, 3, 4, 22, 23, 24]}.items()) +
                                   list({key: 'часов' for key in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]}.items())))

    dead_user = await bot.get_chat_member(callback.message.chat.id, dead)
    dead_user_status = dead_user.status
    if dead_user_status == 'restricted':
        bantime = dead_user.until_date + timedelta(hours=mute_hours)
    else:
        bantime = datetime.datetime.now() + timedelta(hours=mute_hours)

    await callback.message.delete_reply_markup()
    await bot.send_message(callback.message.chat.id, f'{winnerDisplayName} отправил {deadDisplayName} в Вальгаллу на {mute_hours} {hours_declension[mute_hours]}. {deadDisplayName}, Ваше последнее слово?')
    await asyncio.sleep(10)
    gif = FSInputFile('buckshot-roulette.mp4')
    await bot.send_video(callback.message.chat.id, video=gif)
    await bot.restrict_chat_member(callback.message.chat.id, dead, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=bantime)
    await callback.answer()


@router.callback_query(lambda query: query.data.startswith('duelshoot|'))
async def shootduel(callback: types.CallbackQuery):
    duelInitiator = int(callback.data.split('|')[1])
    duelMember = callback.from_user.id
    createUserIfNotExist(callback.from_user)

    opponents = [duelInitiator, duelMember]
    dead = random.choice(opponents)
    opponents.remove(dead)

    deadDisplayName = users[dead]["displayName"]
    winnerDisplayName = users[opponents[0]]["displayName"]

    mute_hours_seq = [1] * 173 + [2] * 115 + [3] * 77 + [4] * 51 + [5] * 34 + [6] * 23 + [7] * 15 + [8] * 10 + [9] * 7 + [10] * 5 + [11] * 3 + [12] * 2
    mute_hours = random.choice(mute_hours_seq)
    hours_declension = dict(sorted(list({key: 'час' for key in [1, 21]}.items()) +
                                   list({key: 'часа' for key in [2, 3, 4, 22, 23, 24]}.items()) +
                                   list({key: 'часов' for key in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]}.items())))

    dead_user = await bot.get_chat_member(callback.message.chat.id, dead)
    dead_user_status = dead_user.status
    if dead_user_status == 'restricted':
        bantime = dead_user.until_date + timedelta(hours=mute_hours)
    else:
        bantime = datetime.datetime.now() + timedelta(hours=mute_hours)

    await callback.message.delete_reply_markup()
    await bot.send_message(callback.message.chat.id, f'{winnerDisplayName} отправил {deadDisplayName} в Вальгаллу на {mute_hours} {hours_declension[mute_hours]}. {deadDisplayName}, Ваше последнее слово?')
    await asyncio.sleep(10)
    gif = FSInputFile('buckshot-roulette.mp4')
    await bot.send_video(callback.message.chat.id, video=gif)
    await bot.restrict_chat_member(callback.message.chat.id, dead, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=bantime)
    await callback.answer()


@router.message(Command('duelshoot'))
async def duelshoot(message: types.Message):
    # checking for 60 sec cooldown
    user = message.from_user.id
    createUserIfNotExist(message.from_user)
    if user in l:
        return
    l.append(user)

    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text='Стрелять!', callback_data=f'duelshoot|{user}')).row(InlineKeyboardButton(text='Не чето не хочу пока', callback_data='bye1')).as_markup()
    duelDisplayName = users[user]["displayName"]
    await message.answer(f'{duelDisplayName} вызывает на дуэль! Проигравший отправится отдыхать на срок 1 до 12 часов!', reply_markup=kb)

    await asyncio.sleep(120)
    l.remove(user)


@router.message(Command('shoot'))
async def shoot(message: types.Message):
    fromUser = message.from_user
    createUserIfNotExist(fromUser)
    # checking for 180 sec cooldown
    if fromUser in l:
        return
    l.append(fromUser)
    username = re.search(' @\w*', message.text)
    userId = re.search(' \d*', message.text)
    if username != None:
        username = username.group()[2:]
        try:
            foundUserId = None
            for key, value in users.items():
                if value["username"] == username:
                    foundUserId = key
                    break
            user = (await bot.get_chat_member(message.chat.id, int(foundUserId))).user
            createUserIfNotExist(user)
            duelInitiatorDisplayName = users[fromUser.id]["displayName"]
            duelMemberDisplayName = users[user.id]["displayName"]
            kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text='Стрелять!', callback_data=f'shoot|{fromUser.id}|{user.id}')).row(InlineKeyboardButton(text='Не чето не хочу пока', callback_data=f'bye')).as_markup()
            await message.answer(f'{duelMemberDisplayName}, {duelInitiatorDisplayName} вызывает Вас на дуэль! Проигравший отправится отдыхать на срок 1 до 12 часов!', reply_markup=kb)
            return
        except:
            pass
    elif userId != None:
        userId = userId.group()[1:]
        try:
            user = (await bot.get_chat_member(message.chat.id, int(userId))).user
            createUserIfNotExist(user)
            duelInitiatorDisplayName = users[fromUser.id]["displayName"]
            duelMemberDisplayName = users[user.id]["displayName"]
            kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text='Стрелять!', callback_data=f'shoot|{fromUser.id}|{user.id}')).row(InlineKeyboardButton(text='Не чето не хочу пока', callback_data=f'bye')).as_markup()
            await message.answer(f'{duelMemberDisplayName}, {duelInitiatorDisplayName} вызывает Вас на дуэль! Проигравший отправится отдыхать на срок 1 до 12 часов!', reply_markup=kb)
            return
        except:
            pass

    # !!! later add check for field evershoot (and update for shoot initiator to 1)
    users_id = list(users.keys())
    
    # duration of mute in minutes
    mute_hours_seq = [1] * 173 + [2] * 115 + [3] * 77 + [4] * 51 + [5] * 34 + [6] * 23 + [7] * 15 + [8] * 10 + [9] * 7 + [10] * 5 + [11] * 3 + [12] * 2
    mute_hours = random.choice(mute_hours_seq)
    hours_declension = dict(sorted(list({key: 'час' for key in [1, 21]}.items()) +
                                   list({key: 'часа' for key in [2, 3, 4, 22, 23, 24]}.items()) +
                                   list({key: 'часов' for key in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]}.items())))

    # russian roulette for mute [1h-24h]
    shot1 = random.randint(1, 6)
    if shot1 == 1:
        await message.answer(f'Увы! Мут на {mute_hours} {hours_declension[mute_hours]}. Ваше последнее слово?')
        await asyncio.sleep(10)
        gif = FSInputFile('buckshot-roulette.mp4')
        await bot.send_video(message.chat.id, video=gif)
        await bot.restrict_chat_member(message.chat.id, fromUser.id, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(hours=mute_hours))
    else:
        await message.answer('В этот раз Вам повезло! Или нет? Как знать...')

    # russian roulette for mute [1h-24h] - miss in another member
    shot2 = random.randint(1, 24)
    if shot2 == 1:
        unlucky_user_id = random.choice(users_id)
        unlucky_user = await bot.get_chat_member(message.chat.id, int(unlucky_user_id))
        unlucky_username = users[unlucky_user.user.id]["displayName"]
        unlucky_user_status = unlucky_user.status
        if unlucky_user_status == 'restricted':
            bantime = unlucky_user.until_date + timedelta(hours=mute_hours)
        else:
            bantime = datetime.datetime.now() + timedelta(hours=mute_hours)

        shootUserDisplayName = users[user.id]["displayName"]
        if shot1 == 1:
            await message.answer(f'{shootUserDisplayName} прошил себя насквозь и зацепил {unlucky_username}, уложив его спать на {mute_hours} {hours_declension[mute_hours]}! {unlucky_username}, Ваше последнее слово?')
            await asyncio.sleep(10)
            gif = FSInputFile('buckshot-roulette.mp4')
            await bot.send_video(message.chat.id, video=gif)
            await bot.restrict_chat_member(message.chat.id, int(unlucky_user_id), permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=bantime)
        else:
            await message.answer(f'{shootUserDisplayName} промахнулся и попал в {unlucky_username} и подарил ему мут на {mute_hours} {hours_declension[mute_hours]}! {unlucky_username}, Ваше последнее слово?')
            await asyncio.sleep(10)
            gif = FSInputFile('buckshot-roulette.mp4')
            await bot.send_document(message.chat.id, gif)
            await bot.restrict_chat_member(message.chat.id, int(unlucky_user_id), permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=bantime)

    await asyncio.sleep(120)
    l.remove(user)


@router.message(F.text.lower().startswith(('кто ', 'кого ', 'кому ', 'кем ', 'о ком ')), F.text.lower().endswith('?'))
async def kto(message: types.Message):
    if message.chat.id > 0 and message.chat.id != 5163549672:
        await bot.send_message(-1002326046662, message.text)
        userId = random.choice(list(users.keys()))
        user = users[userId]
        await bot.send_message(-1002326046662, user["displayName"] + f' {message.text[4:-1].replace("мне", "тебе").replace("меня", "тебя").replace("мной", "тобой").replace("мой", "твой").replace("мою", "твою").replace("мое", "твое").replace("мои", "твои")}')
    else:
        userId = random.choice(list(users.keys()))
        user = users[userId]
        await message.answer(user["displayName"] + f' {message.text[4:-1].replace("мне", "тебе").replace("меня", "тебя").replace("мной", "тобой").replace("мой", "твой").replace("мою", "твою").replace("мое", "твое").replace("мои", "твои")}')


def pirozhok_dnya():
    fileExists = True
    first_name = None
    username = None
    date = None
    try:
        file = open('pirozhok.txt', 'r', encoding="utf-8")
        file.seek(0)
        date = file.readline()[:-1]
        first_name = file.readline()[:-1]
        username = file.readline()
        file.close()
    except Exception as e:
        print(f"Exception during loading pirozhok dnya {str(e)}")
        fileExists = False

    if fileExists is False or datetime.datetime.now().date() > datetime.datetime.strptime(date, '%Y-%m-%d').date():
        file = open('pirozhok.txt', 'w', encoding="utf-8")
        userId = random.choice(list(users.keys()))
        user = users[userId]
        first_name = user["firstname"]
        username = user["username"]
        file.write(datetime.datetime.now().date().strftime('%Y-%m-%d') + '\n')
        file.write(first_name + '\n')
        file.write(username)
        file.close()

        return first_name, username
    else:
        return first_name, username


def gay_dnya():
    fileExists = True
    first_name = None
    username = None
    date = None
    try: 
        file = open('gay.txt', 'r', encoding="utf-8")
        file.seek(0)
        date = file.readline()[:-1]
        first_name = file.readline()[:-1]
        username = file.readline()
        file.close()
    except Exception as e:
        print(f"Exception during loading gay dnya {str(e)}")
        fileExists = False

    if fileExists is False or datetime.datetime.now().date() > datetime.datetime.strptime(date, '%Y-%m-%d').date():
        file = open('gay.txt', 'w', encoding="utf-8")
        userId = random.choice(list(users.keys()))
        user = users[userId]
        first_name = user["firstname"]
        username = user["username"]
        file.write(datetime.datetime.now().date().strftime('%Y-%m-%d') + '\n')
        file.write(first_name + '\n')
        file.write(username)
        file.close()

        return first_name, username
    else:
        return first_name, username


@router.message(F.text.lower().contains('гей дня'))
async def gdn(message: types.Message):
    first_name, username = gay_dnya()
    await message.answer(f'<a href="https://t.me/{username}">{username} {first_name}</a> гей дня', parse_mode='HTML', disable_web_page_preview=True)


@router.message(F.text.lower().contains('пирожок дня'))
async def pdn(message: types.Message):
    first_name, username = pirozhok_dnya()
    await message.answer(f'<a href="https://t.me/{username}">{username} {first_name}</a> пирожок дня', parse_mode='HTML', disable_web_page_preview=True)


@router.message(F.text.lower() == 'мяф')
async def myaf(message: types.Message):
    myafs = [FSInputFile('myaf1.mp4'), FSInputFile('myaf2.mp4'), FSInputFile('myaf3.mp4'), FSInputFile('myaf4.mp4'), FSInputFile('myaf5.mp4'), FSInputFile('myaf6.mp4'), FSInputFile('myaf7.mp4'), FSInputFile('myaf8.mp4')]
    gif = random.choice(myafs)
    await bot.send_document(message.chat.id, gif)


# @router.message()
# async def chaos(message: types.Message):
#     if message.chat.id < 0 or message.chat.id == 5163549672:
#         return
#     await bot.send_message(-1002326046662, message.text)


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


@router.message(F.text.contains('ГО'))
async def gol(message: types.Message):
    await bot.send_audio(message.chat.id, FSInputFile('goooool.mp3'), caption='ГООООООООООООЛ!')


@router.message(Command('members'))
async def get_members(message: types.Message):
    text = ''
    for id in users:
        displayName = users[id]['displayName']
        text += f'{displayName}:{id}\n'
    await message.answer(text)


async def main():
    # await bot.restrict_chat_member(-1002326046662, 7187106984, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(seconds=65))
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))


for i in glob.glob('[0-9]*.txt'):
    os.remove(i)
asyncio.run(main())
