import os
import html
import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")
telegram_session = os.getenv("TELEGRAM_SESSION")
channel_username = 'sinavm'

if not api_id or not api_hash or not telegram_session:
    raise ValueError("TELEGRAM_API_ID, TELEGRAM_API_HASH, or TELEGRAM_SESSION not set in environment variables")

client = TelegramClient(StringSession(telegram_session), int(api_id), api_hash)

async def main():
    try:
        await client.start()
        print("Connected to Telegram successfully")
        os.makedirs('media', exist_ok=True)

        posts_html = '<div class="telegram-posts">\n'
        posts_json = []
        count = 0

        async for message in client.iter_messages(channel_username, limit=20):
            text_raw = (message.message or '').strip()
            if not text_raw and not message.media:
                continue

            words = text_raw.split()
            short_text = ' '.join(words[:5]) if words else 'پست رسانه‌ای'
            if len(words) > 5:
                short_text += '...'

            link = f'https://t.me/{channel_username}/{message.id}'
            date_str = message.date.strftime('%Y-%m-%d %H:%M')
            media_info = None

            try:
                if message.photo:
                    path = await message.download_media(file=f'media/{message.id}.jpg')
                    if path:
                        media_info = {"type": "photo", "url": path.replace('\\', '/')}
                elif message.document and getattr(message.document, 'size', 0) and message.document.size <= 4_000_000:
                    path = await message.download_media(file=f'media/{message.id}')
                    if path:
                        media_info = {"type": "document", "url": path.replace('\\', '/')}
                elif message.video:
                    media_info = {"type": "video", "url": None}
            except Exception as media_err:
                print(f"media skip {message.id}: {media_err}")

            posts_html += f'<div class="telegram-post"><a href="{link}" target="_blank" class="post-link">{html.escape(short_text)}</a><br><small>{date_str}</small></div>\n'
            posts_json.append({
                "id": message.id,
                "text": text_raw,
                "preview": short_text,
                "date": int(message.date.timestamp()),
                "link": link,
                "media": media_info
            })

            count += 1
            if count == 5:
                break

        if count == 0:
            print("No posts with text found")
            posts_html += '<div class="telegram-post">پستی با متن یافت نشد.</div>\n'

        posts_html += '</div>'

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
