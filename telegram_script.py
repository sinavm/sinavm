import os
import html
import json
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
import asyncio

# گرفتن متغیرهای محیطی
api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")
channel_username = 'sinavm'  # نام کانال شما

# بررسی وجود متغیرهای محیطی
if not api_id or not api_hash:
    raise ValueError("TELEGRAM_API_ID or TELEGRAM_API_HASH not set in environment variables")

# نام فایل session
session_file = "session.session"

# ایجاد کلاینت
client = TelegramClient(session_file, int(api_id), api_hash)

async def main():
    try:
        # اتصال به Telegram
        await client.start()
        print("Connected to Telegram successfully")

        posts_html = '<div class="telegram-posts">\n'
        posts_json = []
        count = 0

        # خواندن پیام‌ها
        async for message in client.iter_messages(channel_username, limit=20):
            if message.message and message.message.strip():
                # محدود کردن به 5 کلمه اول
                words = message.message.strip().split()
                short_text = ' '.join(words[:5])
                if len(words) > 5:
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
                if count == 5:
                    break

        if count == 0:
            print("No posts with text found")
            posts_html += '<div class="telegram-post">پستی با متن یافت نشد.</div>\n'

        posts_html += '</div>'

        # ذخیره فایل‌ها
        with open('telegram-posts.html', 'w', encoding='utf-8') as f:
            f.write(posts_html)
        print("telegram-posts.html saved")

        with open('posts_formatted.json', 'w', encoding='utf-8') as f:
            json.dump(posts_json, f, ensure_ascii=False, indent=2)
        print("posts_formatted.json saved")

    except FloodWaitError as e:
        print(f"Flood wait error: Please wait {e.seconds} seconds")
        raise
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise
    finally:
        await client.disconnect()
        print("Disconnected from Telegram")

if __name__ == '__main__':
    try:
        client.loop.run_until_complete(main())
    except Exception as e:
        print(f"Main execution failed: {str(e)}")
        exit(1)
