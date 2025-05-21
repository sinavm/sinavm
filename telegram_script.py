import os
import html
from telethon.sync import TelegramClient

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH"))

client = TelegramClient("anon", api_id, api_hash)

MAX_LENGTH = 200

async def main():
    channel_username = "sinavm"
    html_output = '<div class="telegram-posts">\n'
    count = 0

    async for message in client.iter_messages(channel_username):
        # متن اصلی پیام یا کپشن (برای عکس/فایل)
        text = message.message or message.media.caption if message.media else None

        if text:
            text = text.strip()
            if len(text) > MAX_LENGTH:
                text = text[:MAX_LENGTH].rstrip() + "..."
            text = html.escape(text)

            link = f"https://t.me/{channel_username}/{message.id}"
            date_str = message.date.strftime("%Y-%m-%d %H:%M:%S")
            html_output += f'<div class="telegram-post"><a href="{link}" target="_blank" class="post-link">{text}</a><br><small>{date_str}</small></div>\n'
            count += 1

        if count == 2:
            break

    if count == 0:
        html_output += '<div class="telegram-post">هیچ پست متنی یافت نشد.</div>\n'

    html_output += '</div>'

    with open('telegram-posts.html', 'w', encoding='utf-8') as f:
        f.write(html_output)

with client:
    client.loop.run_until_complete(main())
