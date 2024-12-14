import datetime
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
base.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username, win INTEGER, loose INTEGER, draw INTEGER, logs TEXT)')
base.commit()


l = []
active = False


@router.message(Command('rasstrel'))
async def mutes(message: types.Message):
    user = message.from_user.id
    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    status = user.status
    if message.from_user.id == 7187106984 or status == 'administrator' or status == 'owner' or status == 'creator':
        await message.answer('Вам пизда')
        file = open('users.txt', 'a+')
        file.seek(0)
        users = file.readlines()
        file.close()
        users = [x[0:-1] for x in users]
        for i in users:
            user = await bot.get_chat_member(message.chat.id, int(i))
            status = user.status
            if status != 'creator' and status != 'owner' and status != 'administrator':
                await bot.restrict_chat_member(message.chat.id, int(i), permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(weeks=20))


@router.message(Command('unmute'))
async def mutes(message: types.Message):
    user = message.from_user.id
    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    status = user.status
    if message.from_user.id == 7187106984 or status == 'administrator' or status == 'owner' or status == 'creator':
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
                await bot.restrict_chat_member(message.chat.id, user.user.id, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(minutes=2))
        await message.answer('Все муты сняты.')


@router.message(Command('mutes'))
async def mutes(message: types.Message):
    file = open('users.txt', 'a+')
    file.seek(0)
    users = file.readlines()
    file.close()
    users = [x[0:-1] for x in users]
    text = ' '
    for i in users:
        user = await bot.get_chat_member(message.chat.id, int(i))
        user_status = user.status
        if user_status == 'restricted':
            name = user.user.username
            if user.user.username == None: name = 'None'
            text = text + '@' + name + ' - ' + (user.until_date + timedelta(hours=3)).strftime("%d/%m/%Y, %H:%M:%S") + '\n'
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
        return
    for i in range(3):
        looser = random.choice(users)
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}\nЛузер: {looser}', chat_id=-1002326046662, message_id=message_id)
        await asyncio.sleep(0.5)
        await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}\nЛузер: ', chat_id=-1002326046662, message_id=message_id)
        await asyncio.sleep(0.5)
    await bot.edit_message_text(f'Правила рулетки: после старта выбирается 1 победитель и 1 проигравший. Проигравший дарит победителю гифт!\n\nПобедитель: {winner}\nЛузер: {looser}', chat_id=-1002326046662, message_id=message_id)
    file = open('roulette.txt', 'w')
    file.close()
    await asyncio.sleep(60)
    active = False


@router.callback_query(F.data == 'u')
async def u(callback: types.CallbackQuery):
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


@router.message(Command('stats'))
async def stats(message: types.Message):
    user = message.from_user.id


@router.message(Command('duel'))
async def duel(message: types.Message):
    # try:
    # user = message.from_user.id
    # cur.execute('INSERT INTO users (userid, username, win, loose, draw, logs) VALUES(?,?,?,?,?,?)', (message.from_user.id, message.from_user.username, 0, 0, 0, ''))
    # base.commit()
    # except:
    #     pass # user already recorded
    kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Стреляться!', callback_data='s')).as_markup()
    await message.answer(f'@{message.from_user.username} вызывает на дуэль!\n\nПравила дуэли: проигравший дарит победителю гифт. Не участвуйте в дуэлях, если не сможете подарить гифт, иначе будете чушпанами!', reply_markup=kb)


@router.callback_query(F.data == 's')
async def d(callback: types.CallbackQuery):
    duelist = callback.message.text.split(' ')[0]
    r = random.randint(1,3)
    match r:
        case 1:
            await bot.edit_message_text(text=f'{duelist} пристрелил @{callback.from_user.username} и заслужил от него гифт!', chat_id=callback.message.chat.id, message_id=callback.message.message_id)
            #
            # win = cur.execute('SELECT win FROM users WHERE id == ?', (duelist,)).fetchone()[0]
            # win += 1
            # cur.execute('UPDATE users SET win == ? WHERE id == ?', (win, duelist))
            # logs = cur.execute('SELECT logs FROM users WHERE id == ?', (duelist,)).fetchone()[0]
            # logs += f"Победа над {callback.from_user.id} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M')}\n"
            # cur.execute('UPDATE users SET logs == ? WHERE id == ?', (logs, duelist))
            # base.commit()
            #
            # loose = cur.execute('SELECT loose FROM users WHERE id == ?', (callback.from_user.id,)).fetchone()[0]
            # loose += 1
            # cur.execute('UPDATE users SET loose == ? WHERE id == ?', (loose, callback.from_user.id))
            # logs = cur.execute('SELECT logs FROM users WHERE id == ?', (callback.from_user.id,)).fetchone()[0]
            # logs += f"Поражение от {duelist} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M')}\n"
            # cur.execute('UPDATE users SET logs == ? WHERE id == ?', (logs, callback.from_user.id))
            # base.commit()

        case 2:
            await bot.edit_message_text(text=f'@{callback.from_user.username} поставил раком {duelist} и вправе требовать от него подарок!', chat_id=callback.message.chat.id, message_id=callback.message.message_id)

            # win = cur.execute('SELECT win FROM users WHERE id == ?', (callback.from_user.id,)).fetchone()[0]
            # win += 1
            # cur.execute('UPDATE users SET win == ? WHERE id == ?', (win, callback.from_user.id))
            # logs = cur.execute('SELECT logs FROM users WHERE id == ?', (callback.from_user.id,)).fetchone()[0]
            # logs += f"Победа над {duelist} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M')}\n"
            # cur.execute('UPDATE users SET logs == ? WHERE id == ?', (logs, callback.from_user.id))
            # base.commit()
            #
            # loose = cur.execute('SELECT loose FROM users WHERE id == ?', (duelist,)).fetchone()[0]
            # loose += 1
            # cur.execute('UPDATE users SET loose == ? WHERE id == ?', (loose, duelist))
            # logs = cur.execute('SELECT logs FROM users WHERE id == ?', (duelist,)).fetchone()[0]
            # logs += f"Поражение от {callback.from_user.id} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M')}\n"
            # cur.execute('UPDATE users SET logs == ? WHERE id == ?', (logs, duelist))
            # base.commit()

        case 3:
            await bot.edit_message_text(text=f'@{callback.from_user.username} и {duelist} убили друг друга и находятся в паритете!', chat_id=callback.message.chat.id, message_id=callback.message.message_id)

            # draw = cur.execute('SELECT draw FROM users WHERE id == ?', (callback.from_user.id,)).fetchone()[0]
            # draw += 1
            # cur.execute('UPDATE users SET draw == ? WHERE id == ?', (draw, callback.from_user.id))
            # logs = cur.execute('SELECT logs FROM users WHERE id == ?', (callback.from_user.id,)).fetchone()[0]
            # logs += f"Ничья с {duelist} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M')}\n"
            # cur.execute('UPDATE users SET logs == ? WHERE id == ?', (logs, callback.from_user.id))
            # base.commit()
            #
            # draw = cur.execute('SELECT draw FROM users WHERE id == ?', (duelist,)).fetchone()[0]
            # draw += 1
            # cur.execute('UPDATE users SET draw == ? WHERE id == ?', (draw, duelist))
            # logs = cur.execute('SELECT logs FROM users WHERE id == ?', (duelist,)).fetchone()[0]
            # logs += f"Ничья с {callback.from_user.id} - {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d, %H:%M')}\n"
            # cur.execute('UPDATE users SET logs == ? WHERE id == ?', (logs, duelist))
            # base.commit()

    await callback.answer()


@router.message(Command('shoot'))
async def shoot(message: types.Message):
    user = message.from_user.id
    file = open('users.txt', 'a+')
    file.seek(0)
    users = file.readlines()
    users = [x[0:-1] for x in users]
    if str(user) not in users:
        file.write(str(user) + '\n')
        users.append(str(user))
    file.close()
    t = random.randint(1, 8)
    match t:
        case 1:
            minutes = 5
            bantime = timedelta(minutes=minutes)
        case 2:
            minutes = 15
            bantime = timedelta(minutes=minutes)
        case 3:
            minutes = 30
            bantime = timedelta(minutes=minutes)
        case 4:
            minutes = 60
            bantime = timedelta(minutes=minutes)
        case 5:
            minutes = 120
            bantime = timedelta(minutes=minutes)
        case 6:
            minutes = 180
            bantime = timedelta(minutes=minutes)
        case 7:
            minutes = 240
            bantime = timedelta(minutes=minutes)
        case 8:
            minutes = 300
            bantime = timedelta(minutes=minutes)
    if user in l:
        return
    l.append(user)
    gif = FSInputFile('buckshot-roulette.mp4')
    r = random.randint(1,12)
    us = await bot.get_chat_member(message.chat.id, message.from_user.id)
    m = f'@{message.from_user.username} промахнулся и попал в '
    if us.status == 'owner' or us.status == 'creator' or us.status == 'administrator':
        l.remove(user)
        r = 1
        m = f'@{us.user.username} выстрелил в '
    if r == 1:
        num = len(users)
        r1 = random.randint(0, num-1)
        unlucky_user_id = users[r1]
        unlucky_user = await bot.get_chat_member(message.chat.id, int(unlucky_user_id))
        unlucky_username = unlucky_user.user.username
        unlucky_user_status = unlucky_user.status
        await message.answer(f'{m}@{unlucky_username} и подарил ему мут на {minutes} минут! @{unlucky_username}, Ваше последнее слово?')
        await asyncio.sleep(10)
        await bot.send_video(message.chat.id, video=gif)
        if unlucky_user_status == 'restricted':
            bantime = unlucky_user.until_date + timedelta(minutes=minutes)
            await bot.restrict_chat_member(message.chat.id, int(unlucky_user_id), permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=bantime)
        else:
            await bot.restrict_chat_member(message.chat.id, int(unlucky_user_id), permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=bantime)
    else:
        r = random.randint(1,6)
        if r == 1:
            await message.answer(f'Увы! Мут на {minutes} минут. Ваше последнее слово?')
            await asyncio.sleep(10)
            await bot.send_video(message.chat.id, video=gif)
            await bot.restrict_chat_member(message.chat.id, message.from_user.id, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=bantime)
        else:
            await message.answer('В этот раз Вам повезло! Или нет? Как знать...')
    await asyncio.sleep(60)
    l.remove(user)


@router.message(F.text.lower() == 'кто сосал?')
async def hui(message: types.Message):
    file = open('all_users.txt', 'a+')
    file.seek(0)
    users = file.readlines()
    users = [x[0:-1] for x in users]
    user = random.choice(users)
    await message.answer('@' + user + ' сосал')


@router.message()
async def hui(message: types.Message):

    file = open('all_users.txt', 'a+')
    user = message.from_user.username
    file.seek(0)
    users = file.readlines()
    users = [x[0:-1] for x in users]
    if str(user) not in users:
        file.write(str(user) + '\n')
    file.close()

    if message.text != None and 'хуй' in message.text.lower():
        if 'саня' not in message.text.lower():
            await message.answer(message.text)


async def main():
    # file = open('users.txt', 'a+')
    # file.seek(0)
    # users = file.readlines()
    # users = [x[0:-1] for x in users]
    # file.close()
    # for i in users:
    #     user = await bot.get_chat_member(-1002326046662, i)
    #     print(i, user.user.username)
    # user = await bot.get_chat_member(-1002326046662, 681101149)
    # print(user.status, user.until_date)
    # await bot.restrict_chat_member(-1002326046662, 7187106984, permissions=json.loads("""{"can_send_messages":"FALSE"}"""), until_date=timedelta(minutes=2))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())