import pip
pip.main(['install', 'pytz'])
pip.main(['install', 'psycopg2-binary'])
pip.main(['install', 'aiogram'])
pip.main(['install', 'cachetools'])
pip.main(['install', 'requests'])

from cachetools import TTLCache
import requests
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
import psycopg2
import time

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import User
from aiogram.types.chat_member_member import ChatMemberMember

# Define connection parameters
server = str(os.getenv('DATABASE_SERVER')
db_username = str(os.getenv('DATABASE_USER')
password = str(os.getenv('DATABASE_PASSWORD')
port = int(os.getenv('DATABASE_PORT')

#database = 'betatest' #beta test db
#bot = Bot(token='8174792705:AAHoySirgnNaENcPZTb1WCsewJOPGRZCzDs') # beta test bot
#chatId = -1002465405879 #beta test chat id

database = str(os.getenv('DATABASE')
bot = Bot(token=str(os.getenv('TG_TOKEN'))
chatId = int(os.getenv('CHAT_ID')

dp = Dispatcher()
router = Router()
dp.include_router(router)

enableNotNoiseCommands = True

baseInit = psycopg2.connect(
    dbname=database,
    user=db_username,
    password=password,
    host=server,
    port=port
)

cursorInit = baseInit.cursor()
cursorInit.execute('''
CREATE TABLE IF NOT EXISTS users(userId BIGINT PRIMARY KEY, username TEXT DEFAULT '', firstname TEXT, lastname TEXT, insertDateTime TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'), everShoot SMALLINT DEFAULT 0);
               ''')
baseInit.commit()

cursorInit.execute('''
CREATE TABLE IF NOT EXISTS casinoLogs (logId BIGSERIAL PRIMARY KEY, userId BIGINT, rival BIGINT, state SMALLINT, insertDateTime TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'));
               ''')

baseInit.commit()

cursorInit.execute('''
CREATE TABLE IF NOT EXISTS userInfos (infoId BIGSERIAL PRIMARY KEY, userId BIGINT, description TEXT, dtf TEXT, steam TEXT, insertDateTime TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'));
               ''')

baseInit.commit()

query = "SELECT userId, username, firstName, lastName, everShoot FROM users"

cursorInit.execute(query)

rows = cursorInit.fetchall()
cursorInit.close()
baseInit.close()

users = {
    int(row[0]): {
        "username": row[1],
        "firstname": row[2],
        "lastname": row[3],
        "displayName": f"@{str(row[1])}" if row[1] != '' and row[1] != None else f"{str(row[2])} {str(row[3])}",
        "everShoot": bool(row[4])
    }
    for row in rows
}

class UserInfo:
    def __init__(self, user_id, description, dtf, steam):
        self.user_id = user_id
        self.description = description
        self.dtf = dtf
        self.steam = steam

def escape_md(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + char if char in escape_chars else char for char in text)

async def refreshUsersData():
    data_refresh_interval = 3  # seconds
    for userId in users:
        try:
            user = (await bot.get_chat_member(chatId, userId)).user
            selectedUser = users[userId]
            requireRefresh = False
            if selectedUser["username"] != user.username:
                selectedUser["username"] = user.username
                requireRefresh = True
            if selectedUser["firstname"] != user.first_name:
                selectedUser["firstname"] = user.first_name
                requireRefresh = True
            if selectedUser["lastname"] != user.last_name:
                selectedUser["lastname"] = user.last_name
                requireRefresh = True

            if requireRefresh:
                base = None
                cursor = None
                try:
                    base = psycopg2.connect(dbname=database,user=db_username,password=password,host=server,port=port)
                    cursor = base.cursor()
                    cursor.execute('UPDATE users SET username = %s, firstname = %s, lastname = %s WHERE userId = %s', (selectedUser["username"], selectedUser["firstname"], selectedUser["lastname"], userId))
                    base.commit()
                except:
                    base.rollback()
                    pass
                finally:
                    if cursor:
                        cursor.close()
                    if base:
                        base.close()
        except Exception as e:
             print(f"Exception during refresh users {str(e)} {str(userId)}")

        time.sleep(data_refresh_interval)

shootCache = TTLCache(maxsize=100, ttl=15)
active = False

def createUserIfNotExist(fromUser: User):
    if not fromUser.id in users:
        base = None
        cursor = None
        try:
            base = psycopg2.connect(dbname=database,user=db_username,password=password,host=server,port=port)
            cursor = base.cursor()
            cursor.execute('INSERT INTO users (userId, username, firstname, lastname, everShoot) VALUES(%s,%s,%s,%s,%s)', (fromUser.id, fromUser.username, fromUser.first_name, fromUser.last_name, 0))
            cursor.execute('INSERT INTO userInfos (userId, description, dtf, steam) VALUES(%s, %s,%s,%s)', (fromUser.id, None, None, None))
            users[fromUser.id] = {
                "username": fromUser.username,
                "firstname": fromUser.first_name,
                "lastname": fromUser.last_name,
                "displayName": f"@{fromUser.first_name}" if fromUser.username else f"{fromUser.first_name} {fromUser.last_name}",
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

@router.chat_member()
async def send_welcome(chat_member: types.ChatMemberUpdated):
    if chat_member.new_chat_member.status == 'member':
        chatMember = chat_member.new_chat_member
        joinedUser = chatMember.user
        if joinedUser.id != bot.id and joinedUser.is_bot == False and users.get(joinedUser.id) is None:
            createUserIfNotExist(joinedUser)
            await chat_member.answer(f"Привет новенький [{escape_md(joinedUser.first_name)}](tg://user?id={joinedUser.id})\! С тебя гифт\!", parse_mode='MarkdownV2')

    if chat_member.new_chat_member.status == 'left':
        chatMember = chat_member.new_chat_member
        leftUser = chatMember.user
        if leftUser.id != bot.id and leftUser.is_bot == False and users.get(leftUser.id) is not None:
            await chat_member.answer(f"[{escape_md(leftUser.first_name)}](tg://user?id={leftUser.id}) покинул чат\. Пока лох\!", parse_mode='MarkdownV2')

@router.message(Command('blackjack'))
async def blackjack(message: types.Message):
    if enableNotNoiseCommands:
        return
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

@router.message(Command('who'))
async def who(message: types.Message):
    mentionedUser = None

    if len(message.entities) == 1:
        try:
            matched = re.match(r'^/who\S*\s(\S+)\s*$', message.text)
            if matched is not None:
                foundUserId = None
                username = str(matched.group(1)).lower()
                for key, value in users.items():
                    currentUserName = str(value["username"]).lower()
                    if currentUserName == username:
                        foundUserId = key
                        break
                mentionedUser = (await bot.get_chat_member(message.chat.id, int(foundUserId))).user
        except Exception as e:
            print(f"Exception during getting who info username without mention {str(e)}")
    else:
        for entity in message.entities:
            if entity.type == 'text_mention':
                mentionedUser = entity.user
                createUserIfNotExist(mentionedUser)

            if entity.type == 'mention':
                try:
                    username = re.search(' @\w*', message.text)
                    if username is not None:
                        foundUserId = None
                        username = str(username.group()[2:]).lower()
                        for key, value in users.items():
                            currentUserName = str(value["username"]).lower()
                            if currentUserName == username:
                                foundUserId = key
                                break
                        mentionedUser = (await bot.get_chat_member(message.chat.id, int(foundUserId))).user
                except Exception as e:
                    print(f"Exception during getting who info username {str(e)}")

            if mentionedUser:
                break

    if mentionedUser is not None:
        base = None
        cursor = None
        try:
            base = psycopg2.connect(dbname=database,user=db_username,password=password,host=server,port=port)
            cursor = base.cursor()
            cursor.execute('SELECT userId, description, dtf, steam FROM userInfos WHERE userId = %s', (mentionedUser.id,))
            rows = cursor.fetchall()
            infoText = ""
            firstname = users[mentionedUser.id]["firstname"]
            if len(rows) != 0:
                userRow = rows[0]
                userInfo = UserInfo(int(userRow[0]), userRow[1], userRow[2], userRow[3])
                if userInfo.description is not None:
                    infoText += f'{escape_md(userInfo.description)}\n'
                if userInfo.dtf is not None:
                    infoText += f'dtf: {escape_md(userInfo.dtf)}\n'
                if userInfo.steam is not None:
                    infoText += f'steam: {escape_md(userInfo.steam)}\n'
            else:
                cursor.execute('INSERT INTO userInfos (userId, description, dtf, steam) VALUES(%s, %s,%s,%s)', (mentionedUser.id, None, None, None))
                base.commit()

            if infoText == "":
                infoText += "Нет информации"
            await message.reply(f'[{escape_md(firstname)}]\:\n{infoText}', parse_mode='MarkdownV2')
        except Exception as e:
            print(f"Exception during getting who info {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if base:
                base.close()

@router.message(Command('rasstrel'))
async def rasstrel(message: types.Message):
    if enableNotNoiseCommands:
        return
    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    status = user.status
    if (status == 'owner' or status == 'creator') or (status == 'administrator' and user.can_restrict_members):
        try:
            userid = int(re.search('\d+', message.text).group())
            await bot.restrict_chat_member(message.chat.id, userid, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(seconds=1))
            user = await bot.get_chat_member(message.chat.id, userid)
            createUserIfNotExist(user.user)
            await message.answer(f'[{escape_md(users[userid]["firstname"])}](tg://user?id={userid}) был расстрелян\!', parse_mode='MarkdownV2')
        except:
            if not re.match(r'^/rasstrel\S*\s*$', message.text):
                return
            await message.answer('ГОООООООООООООООООООООООООООООЛ')
            for i in users:
                user = await bot.get_chat_member(message.chat.id, int(i))
                status = user.status
                if status != 'creator' and status != 'owner' and status != 'administrator':
                    await bot.restrict_chat_member(message.chat.id, int(i), permissions=json.loads("""{"can_send_messages":"TRUE", "can_send_audios":"TRUE", "can_send_documents":"TRUE", "can_send_photos":"TRUE", "can_send_videos":"TRUE", "can_send_video_notes":"TRUE", "can_send_voice_notes":"TRUE", "can_send_polls":"TRUE", "can_send_other_messages":"TRUE"}"""), until_date=timedelta(seconds=65))


@router.message(Command('unmute'))
async def unmute(message: types.Message):
    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    status = user.status
    if (status == 'owner' or status == 'creator') or (status == 'administrator' and user.can_restrict_members):
        try:
            userid = int(re.search('\d+', message.text).group())
            await bot.restrict_chat_member(message.chat.id, userid, permissions=json.loads("""{"can_send_messages":"TRUE", "can_send_audios":"TRUE", "can_send_documents":"TRUE", "can_send_photos":"TRUE", "can_send_videos":"TRUE", "can_send_video_notes":"TRUE", "can_send_voice_notes":"TRUE", "can_send_polls":"TRUE", "can_send_other_messages":"TRUE"}"""), until_date=timedelta(seconds=65))
            user = await bot.get_chat_member(message.chat.id, userid)
            await message.answer(f'[{escape_md(users[userid]["firstname"])}](tg://user?id={userid}) был помилован\!' , parse_mode='MarkdownV2')
        except:
            try:
                for i in users.keys():
                    try:
                        user = await bot.get_chat_member(message.chat.id, int(i))
                        user_status = user.status
                        if user_status == 'restricted':
                            await bot.restrict_chat_member(message.chat.id, user.user.id, permissions=json.loads("""{"can_send_messages":"TRUE"}"""), until_date=timedelta(seconds=65))
                    except Exception as e:
                        print(f"Exception during unmute {str(e)} {str(i)}")
            except Exception as e:
                print(f"Exception during unmute for {str(e)}")
            await message.answer('Все помилованы!')


@router.message(Command('mutes'))
async def mutes(message: types.Message):
    text = ''
    for i in users.keys():
        try:
            user = await bot.get_chat_member(message.chat.id, int(i))
            user_status = user.status
            user_id = user.user.id
            if user_status == 'restricted':
                text = text + f'[{escape_md(users[user_id]["firstname"])}](tg://user?id={user_id}) [{user_id}]' ' \- ' + (user.until_date + timedelta(hours=3)).strftime("%d/%m/%Y, %H:%M:%S") + '\n'
        except Exception as e:
                    print(f"Exception during mutes {str(e)} {str(i)}")
    if text == '': text = 'Все свободны\! УРАААААААААААААААААА\!'
    await message.answer(text, parse_mode='MarkdownV2')


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
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nУчастники:\n{users}\n\nСтарт через {s}', reply_markup=kb, chat_id=chatId, message_id=message_id)
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
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nНедостаточно игроков(', chat_id=chatId, message_id=message_id)
        file = open('roulette.txt', 'w')
        file.close()
        await asyncio.sleep(60)
        active = False
        return
    for i in range(3):
        winner = random.choice(users)
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}', chat_id=chatId, message_id=message_id)
        await asyncio.sleep(0.5)
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: ', chat_id=chatId, message_id=message_id)
        await asyncio.sleep(0.5)
    await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}', chat_id=chatId, message_id=message_id)
    users.remove(winner)
    if len(users) == 1:
        looser = users[0]
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}\nЛузер: {looser}', chat_id=chatId, message_id=message_id)
        file = open('roulette.txt', 'w')
        file.close()
        await asyncio.sleep(60)
        active = False
    else:
        for i in range(3):
            looser = random.choice(users)
            await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}\nЛузер: {looser}', chat_id=chatId, message_id=message_id)
            await asyncio.sleep(0.5)
            await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}\nЛузер: ', chat_id=chatId, message_id=message_id)
            await asyncio.sleep(0.5)
    await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}\nЛузер: {looser}', chat_id=chatId, message_id=message_id)
    file = open('roulette.txt', 'w')
    file.close()

    base = None
    cursor = None
    try:
        base = psycopg2.connect(dbname=database,user=db_username,password=password,host=server,port=port)
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
    if enableNotNoiseCommands:
        return
    userId = message.from_user.id
    base = None
    cursor = None
    try:
        base = psycopg2.connect(dbname=database,user=db_username,password=password,host=server,port=port)
        cursor = base.cursor()
        cursor.execute('SELECT userId, rival, state, insertDateTime FROM casinoLogs WHERE userId = %s ORDER BY insertDateTime DESC', (userId,))
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
    if enableNotNoiseCommands:
        return
    userId = message.from_user.id
    base = None
    cursor = None
    try:
        base = psycopg2.connect(dbname=database,user=db_username,password=password,host=server,port=port)
        cursor = base.cursor()
        cursor.execute('SELECT userId, rival, state, insertDateTime FROM casinoLogs WHERE userId = %s ORDER BY insertDateTime DESC', (userId,))
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
    if enableNotNoiseCommands:
        return
    stats = []
    base = None
    cursor = None
    try:
        base = psycopg2.connect(dbname=database,user=db_username,password=password,host=server,port=port)
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
        base = psycopg2.connect(dbname=database,user=db_username,password=password,host=server,port=port)
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
    # checking for cooldown
    user = message.from_user.id
    createUserIfNotExist(message.from_user)
    # if user in shootCache:
    #     return
    shootCache[user] = user


    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text='Стрелять!', callback_data=f'duelshoot|{user}')).row(InlineKeyboardButton(text='Не чето не хочу пока', callback_data='bye1')).as_markup()
    duelDisplayName = users[user]["displayName"]
    await message.answer(f'{duelDisplayName} вызывает на дуэль! Проигравший отправится отдыхать на срок 1 до 12 часов!', reply_markup=kb)

@router.message(Command('shoot'))
async def shoot(message: types.Message):
    fromUser = message.from_user
    # checking for cooldown
    if fromUser.id in shootCache:
        return
    shootCache[fromUser.id] = fromUser.id

    createUserIfNotExist(fromUser)
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


@router.message(F.text.lower() == 'жабки')
async def frogs(message: types.Message):
    stickers = []
    for i in range(5):
        sticker = await bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAEOQH5n89g5JV10sQdWgGu9lcD5Rqnh8gAC_BcAAts9OEmV9p6yNqTsXjYE')
        stickers.append(sticker)
    for i in range(5):
        await bot.delete_message(message.chat.id, stickers[i].message_id)


@router.message(F.text.lower().startswith(('кто ', 'кого ', 'кому ', 'кем ', 'о ком ')), F.text.lower().endswith('?'))
async def kto(message: types.Message):
    if enableNotNoiseCommands:
        return
    if message.chat.id > 0 and message.chat.id != 5163549672:
        await bot.send_message(chatId, message.text)
        userId = random.choice(list(users.keys()))
        user = users[userId]
        await bot.send_message(chatId, f'[{escape_md(user["firstname"])}](tg://user?id={userId}) {escape_md(message.text[4:-1].replace("мне", "тебе").replace("меня", "тебя").replace("мной", "тобой").replace("мой", "твой").replace("мою", "твою").replace("мое", "твое").replace("мои", "твои"))}', parse_mode='MarkdownV2')
    else:
        userId = random.choice(list(users.keys()))
        user = users[userId]
        await message.answer(f'[{escape_md(user["firstname"])}](tg://user?id={userId}) {escape_md(message.text[4:-1].replace("мне", "тебе").replace("меня", "тебя").replace("мной", "тобой").replace("мой", "твой").replace("мою", "твою").replace("мое", "твое").replace("мои", "твои"))}', parse_mode='MarkdownV2')


def pirozhok_dnya():
    fileExists = True
    first_name = None
    userId = None
    date = None
    try:
        file = open('pirozhok.txt', 'r', encoding="utf-8")
        file.seek(0)
        date = file.readline()[:-1]
        first_name = file.readline()[:-1]
        userId = int(file.readline())
        file.close()
    except Exception as e:
        print(f"Exception during loading pirozhok dnya {str(e)}")
        fileExists = False

    if fileExists is False or datetime.datetime.now().date() > datetime.datetime.strptime(date, '%Y-%m-%d').date():
        file = open('pirozhok.txt', 'w', encoding="utf-8")
        userId = random.choice(list(users.keys()))
        user = users[userId]
        first_name = user["firstname"]
        file.write(datetime.datetime.now().date().strftime('%Y-%m-%d') + '\n')
        file.write(first_name + '\n')
        file.write(str(userId))
        file.close()

        return first_name, userId
    else:
        return first_name, userId


def gay_dnya():
    fileExists = True
    first_name = None
    userId = None
    date = None
    try:
        file = open('gay.txt', 'r', encoding="utf-8")
        file.seek(0)
        date = file.readline()[:-1]
        first_name = file.readline()[:-1]
        userId = int(file.readline())
        file.close()
    except Exception as e:
        print(f"Exception during loading gay dnya {str(e)}")
        fileExists = False

    if fileExists is False or datetime.datetime.now().date() > datetime.datetime.strptime(date, '%Y-%m-%d').date():
        file = open('gay.txt', 'w', encoding="utf-8")
        userId = random.choice(list(users.keys()))
        user = users[userId]
        first_name = user["firstname"]
        file.write(datetime.datetime.now().date().strftime('%Y-%m-%d') + '\n')
        file.write(first_name + '\n')
        file.write(str(userId))
        file.close()

        return first_name, userId
    else:
        return first_name, userId


@router.message(F.text.lower().contains('гей дня'))
async def gdn(message: types.Message):
    if enableNotNoiseCommands:
        return
    first_name, userId = gay_dnya()
    await message.answer(f'[{escape_md(first_name)}](tg://user?id={userId}) гей дня', parse_mode='MarkdownV2', disable_web_page_preview=True)


@router.message(F.text.lower().contains('пирожок дня'))
async def pdn(message: types.Message):
    if enableNotNoiseCommands:
        return
    first_name, userId = pirozhok_dnya()
    await message.answer(f'[{escape_md(first_name)}](tg://user?id={userId}) пирожок дня', parse_mode='MarkdownV2', disable_web_page_preview=True)


@router.message(F.text.lower() == 'мяф')
async def myaf(message: types.Message):
    if enableNotNoiseCommands:
        return
    myafs = [FSInputFile('myaf1.mp4'), FSInputFile('myaf2.mp4'), FSInputFile('myaf3.mp4'), FSInputFile('myaf4.mp4'), FSInputFile('myaf5.mp4'), FSInputFile('myaf6.mp4'), FSInputFile('myaf7.mp4'), FSInputFile('myaf8.mp4')]
    gif = random.choice(myafs)
    await bot.send_document(message.chat.id, gif)

@router.message(F.text.lower().startswith('мяф '))
async def myafTenor(message: types.Message):
    if enableNotNoiseCommands:
        return
    try:
        matched = re.search(r'^мяф\s+(.*)', message.text, re.I)
        if matched:
            gif_url = await fetch_gif(matched.group(1))
            if gif_url:
                await bot.send_animation(
                    chat_id=chatId,
                    animation=gif_url
                )
    except Exception as e:
        print(f"Exception during myaf tenor {str(e)}")


async def fetch_gif(search_term):
    if search_term is None:
        search_term = 'котик'
    limit = 1
    clientKey = 'tgbot'
    tenorKey = 'AIzaSyCvFm1iwvb8jVoPd3Q9pRqx8uw_v-cGVJ0'
    response = requests.get(
        f'https://tenor.googleapis.com/v2/search?q={search_term}&key={tenorKey}&client_key={clientKey}&limit={limit}'
    )

    if response.status_code == 200:
        gifs = response.json()
        gif_url = gifs['results'][0]['media_formats']['gif']['url']
        return gif_url
    return None


# @router.message()
# async def chaos(message: types.Message):
#     if message.chat.id < 0 or message.chat.id == 5163549672:
#         return
#     await bot.send_message(chatId, message.text)


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
        text += f'{escape_md(users[id]["firstname"])}: {id}\n'
    await message.answer(text, parse_mode='MarkdownV2')


@router.message(Command('fullstats'))
async def fullfullstats(message: types.Message):
    await bot.send_document(message.chat.id, FSInputFile('parsed_duels.csv'))


@router.message(Command('myfullfullstats'))
async def myfullfullstats(message: types.Message):
    csvfile1 = open(f'{message.from_user.username}.csv', 'w', encoding="utf-8", newline='')
    csvwriter = csv.writer(csvfile1)
    csvfile2 = open('parsed_duels.csv', 'r', encoding="utf-8")
    csvreader = csv.reader(csvfile2)
    csvwriter.writerow(['Победитель', 'Проигравший', 'Ничья', 'Логи', 'Дата'])
    for row in csvreader:
        if row[0] == message.from_user.username or row[1] == message.from_user.username or message.from_user.username in row[2]:
            csvwriter.writerow(row)
    csvfile1.close()
    csvfile2.close()
    await bot.send_document(message.chat.id, FSInputFile(f'{message.from_user.username}.csv'))
    os.remove(f'{message.from_user.username}.csv')

async def main():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await asyncio.gather(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()), refreshUsersData())
    except:
        print("Fatal error, restarting main")
        await main()
    finally:
        print("Stopped execution, restarting main")
        await main()


for i in glob.glob('[0-9]*.txt'):
    os.remove(i)
asyncio.run(main())
