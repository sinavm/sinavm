from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
import os

api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')

channel_username = 'sinavm'  # آیدی کانال بدون @
limit = 20  # تعداد پست‌ها

client = TelegramClient('session_name', api_id, api_hash)

def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def main():
    await client.start()

    channel = await client.get_entity(channel_username)
    history = await client(GetHistoryRequest(
        peer=channel,
        limit=limit,
        offset_date=None,
        offset_id=0,
        max_id=0,
        min_id=0,
        add_offset=0,
        hash=0,
        from_id=None
    ))

    html_posts = ''
    for message in history.messages:
        text = message.message or ''  # متن پست (اگر نبود خالی)
        if not text.strip():
            continue  # اگر پست متن نداشت رد کن

        safe_text = escape_html(text).replace('\n', '<br>')

        # لینک مستقیم پست در تلگرام به شکل: https://t.me/{channel_username}/{message_id}
        post_link = f"https://t.me/{channel_username}/{message.id}"

        post_html = f'''
        <a href="{post_link}" target="_blank" class="telegram-post">
            <div class="post-text">{safe_text}</div>
        </a>
        '''
        html_posts += post_html + '\n'

    with open('telegram-posts.html', 'w', encoding='utf-8') as f:
        f.write(html_posts)

with client:
    client.loop.run_until_complete(main())
