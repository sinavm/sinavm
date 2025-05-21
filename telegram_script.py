import os
import html
from telethon.sync import TelegramClient

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")

client = TelegramClient("anon", api_id, api_hash)

async def main():
    html_output = '<div class="telegram-posts">\n'
    async for message in client.iter_messages('@sinavm', limit=5):
        if message.message:
            message_text = html.escape(message.message)
            html_output += f'<div class="telegram-post"><a href="https://t.me/sinavm/{message.id}" target="_blank" class="post-link">{message_text}</a><br><small>{message.date}</small></div>\n'
    html_output += '</div>'

    with open('telegram-posts.html', 'w', encoding='utf-8') as f:
        f.write(html_output)

with client:
    client.loop.run_until_complete(main())
