import csv

from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

api_id = 111111
api_hash = '111abc'
phone = '+111111'

client = TelegramClient(phone, api_id, api_hash)

csvfile = open('parsed_members.csv', 'w', encoding="utf-8", newline='')
csvwriter = csv.writer(csvfile)

async def main():
    members = await client.get_participants(-1002326046662)
    for i in members:
        member = [i.first_name + (' ' + i.last_name if i.last_name else ""), i.username if i.username else "", str(i.id)]
        csvwriter.writerow(member)
    csvfile.close()

with client:
    client.loop.run_until_complete(main())
