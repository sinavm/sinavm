import os
import html
import json
import re
from telethon import TelegramClient

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
channel_username = 'sinavm'

client = TelegramClient("session.session", api_id, api_hash)

def split_into_sentences(text):
    # تقسیم متن بر اساس پایان جملات (نقطه، علامت سوال، تعجب و ...)
    sentence_endings = re.compile(r'(?<=[.!؟])\s+')
    return sentence_endings.split(text)

async def main():
    posts_html = '<div class="telegram-posts">\n'
    posts_json = []

    count = 0
    async for message in client.iter_messages(channel_username, limit=20):
        if message.message and message.message.strip():
            sentences = split_into_sentences(message.message.strip())
            short_sentences = sentences[:20]
            short_text = ' '.join(short_sentences)
            if len(sentences) > 20:
                short_text += '...'

            text = html.escape(short_text)
            link = f'https://t.me/{channel_username}/{message.id}'
            date_str = message.date.strftime('%Y-%m-%d %H:%M')

            posts_html += f'<div class="telegram-post"><a href="{link}" target="_blank" class="post-link">{text}</a><br><small>{date_str}</small></div>\n'
            posts_json.append({
                "text": message.message.strip(),
                "date": int(message.date.timestamp()),
                "link": link
            })

            count += 1
            if count == 6:
                break

    if count == 0:
        posts_html += '<div class="telegram-post">پستی با متن یافت نشد.</div>\n'

    posts_html += '</div>'

    with open('telegram-posts.html', 'w', encoding='utf-8') as f:
        f.write(posts_html)

    with open('posts_formatted.json', 'w', encoding='utf-8') as f:
        json.dump(posts_json, f, ensure_ascii=False, indent=2)

with client:
    client.loop.run_until_complete(main())
