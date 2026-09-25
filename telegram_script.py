import os
import html
import json
import shutil
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from telethon.tl.types import DocumentAttributeFilename

api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")
telegram_session = os.getenv("TELEGRAM_SESSION")
channel_username = 'sinavm'
PAGES = 'https://sinavm.github.io/sinavm'

if not api_id or not api_hash or not telegram_session:
    raise ValueError("TELEGRAM_API_ID, TELEGRAM_API_HASH, or TELEGRAM_SESSION not set")

client = TelegramClient(StringSession(telegram_session), int(api_id), api_hash)

def original_name(message):
    if not message.document:
        return None
    for attr in message.document.attributes or []:
        if isinstance(attr, DocumentAttributeFilename):
            return attr.file_name
    return None

def looks_like_nv(message, filename):
    blob = ((message.message or '') + ' ' + (filename or '')).lower()
    return any(token in blob for token in ('nv', 'npvs', 'nvps', 'کانفیگ'))

async def save_document(message):
    os.makedirs('media', exist_ok=True)
    filename = original_name(message) or f'{message.id}.npvs'
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ('.npvs', '.nvps', '.conf', '.txt', '.json'):
        ext = '.npvs'
    local = f'media/{message.id}{ext}'
    path = await message.download_media(file=local)
    if not path:
        return None
    path = path.replace('\\', '/')
    return {
        "type": "document",
        "filename": os.path.basename(path),
        "url": path,
        "download_url": f'{PAGES}/{path}',
        "original_name": filename
    }

async def main():
    try:
        await client.start()
        print("Connected to Telegram successfully")
        os.makedirs('media', exist_ok=True)

        posts_html = '<div class="telegram-posts">\n'
        posts_json = []
        nv_files = []
        shown = 0

        async for message in client.iter_messages(channel_username, limit=40):
            text_raw = (message.message or '').strip()
            filename = original_name(message)
            media_info = None

            if message.document and getattr(message.document, 'size', 0) and message.document.size <= 8_000_000:
                if looks_like_nv(message, filename) or True:
                    try:
                        media_info = await save_document(message)
                        if media_info and looks_like_nv(message, filename):
                            nv_files.append({
                                "id": message.id,
                                "text": text_raw,
                                "link": f'https://t.me/{channel_username}/{message.id}',
                                **media_info
                            })
                    except Exception as media_err:
                        print(f"media skip {message.id}: {media_err}")
            elif message.photo:
                try:
                    path = await message.download_media(file=f'media/{message.id}.jpg')
                    if path:
                        path = path.replace('\\', '/')
                        media_info = {"type": "photo", "url": path, "download_url": f'{PAGES}/{path}'}
                except Exception as media_err:
                    print(f"photo skip {message.id}: {media_err}")

            if shown < 5 and (text_raw or media_info):
                words = text_raw.split()
                short_text = ' '.join(words[:5]) if words else 'پست رسانه‌ای'
                if len(words) > 5:
                    short_text += '...'
                link = f'https://t.me/{channel_username}/{message.id}'
                date_str = message.date.strftime('%Y-%m-%d %H:%M')
                posts_html += f'<div class="telegram-post"><a href="{link}" target="_blank" class="post-link">{html.escape(short_text)}</a><br><small>{date_str}</small></div>\n'
                posts_json.append({
                    "id": message.id,
                    "text": text_raw,
                    "preview": short_text,
                    "date": int(message.date.timestamp()),
                    "link": link,
                    "media": media_info
                })
                shown += 1

            if shown >= 5 and len(nv_files) >= 3:
                break

        if shown == 0:
            posts_html += '<div class="telegram-post">پستی با متن یافت نشد.</div>\n'
        posts_html += '</div>'

        latest = nv_files[:3]
        for i, item in enumerate(latest, 1):
            src = item.get('url')
            dest = f'media/nv-latest-{i}.npvs'
            if src and os.path.isfile(src):
                shutil.copyfile(src, dest)
                item['stable_url'] = f'{PAGES}/{dest}'

        with open('telegram-posts.html', 'w', encoding='utf-8') as f:
            f.write(posts_html)
        with open('posts_formatted.json', 'w', encoding='utf-8') as f:
            json.dump(posts_json, f, ensure_ascii=False, indent=2)
        with open('media/latest-nv.json', 'w', encoding='utf-8') as f:
            json.dump(latest, f, ensure_ascii=False, indent=2)
        print(f"saved posts={shown} nv_files={len(latest)}")

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
