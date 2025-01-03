import asyncio
import csv
import re

from telethon.sync import TelegramClient


api_id = 111
api_hash = '111'
phone = '+1111'

client = TelegramClient(phone, api_id, api_hash, system_version='4.16.30-vxCUSTOM')

async def main():
    csvfile = open('parsed_members.csv', 'w', encoding="utf-8", newline='')
    csvwriter = csv.writer(csvfile)

    csvfile2 = open('parsed_duels.csv', 'w', encoding="utf-8", newline='')
    csvwriter2 = csv.writer(csvfile2)

    csvwriter2.writerow(['Победитель', 'Проигравший', 'Ничья', 'Логи', 'Дата'])
    async for message in client.iter_messages(-1002326046662, from_user=7540561391, search='пристрелил'):
            print(message.text, message.date)
            try:
                winner = re.search('@\w* ', message.text).group()[1:-1]
                looser = re.search(' @\w* ', message.text).group()[2:-1]
            except:
                pass
            else:
                data = [winner, looser, '-', message.text, message.date]
                csvwriter2.writerow(data)

    async for message in client.iter_messages(-1002326046662, from_user=7540561391, search='поставил раком'):
            print(message.text, message.date)
            try:
                winner = re.search('@\w* ', message.text).group()[1:-1]
                looser = re.search(' @\w* ', message.text).group()[2:-1]
            except:
                pass
            else:
                data = [winner, looser, '-', message.text, message.date]
                csvwriter2.writerow(data)

    async for message in client.iter_messages(-1002326046662, from_user=7540561391, search='в паритете'):
            print(message.text, message.date)
            try:
                draw = re.search('@\w* ', message.text).group()[1:-1] + ' и ' + re.search(' @\w* ', message.text).group()[2:-1]
            except:
                pass
            else:
                data = ['-', '-', draw, message.text, message.date]
                csvwriter2.writerow(data)

    csvfile2.close()

    csvfile2 = open('parsed_duels.csv', 'r', encoding="utf-8", newline='')
    csvreader2 = csv.reader(csvfile2)
    sorted_rows = sorted(csvreader2, key=lambda row: row[4], reverse=True)
    csvfile2.close()

    csvfile2 = open('parsed_duels.csv', 'w', encoding="utf-8", newline='')
    csvwriter2 = csv.writer(csvfile2)
    csvwriter2.writerow(['Победитель', 'Проигравший', 'Ничья', 'Логи', 'Дата'])
    for row in sorted_rows:
        csvwriter2.writerow(row)
    csvfile2.close()

    members = await client.get_participants(-1002326046662)
    for i in members:
        member = [i.first_name + (' ' + i.last_name if i.last_name else ""), i.username if i.username else "", str(i.id)]
        csvwriter.writerow(member)

    csvfile.close()

with client:
    client.loop.run_until_complete(main())
