import os
import re
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
POST_LIMIT = 12
HISTORY_LIMIT = 80

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

def safe_filename(name, fallback):
    name = os.path.basename(name or '') or fallback
    name = name.replace('/', '-').replace('\\', '-').replace('..', '.')
    name = re.sub(r'[\x00-\x1f]', '', name).strip() or fallback
    return name

def looks_like_nv(message, filename):
    ext = os.path.splitext(filename or '')[1].lower()
    return ext in ('.npvs', '.nvps', '.npv', '.npvt')

def extract_password(text):
    match = re.search(r'(?im)^\s*(?:رمز(?:\s+عبور)?|password|pass)\s*[:：=]\s*(.+?)\s*$', text or '')
    return match.group(1).strip() if match else None

def classify_document(filename, path):
    ext = os.path.splitext(filename or '')[1].lower()
    sample = ''
    if path and os.path.isfile(path) and os.path.getsize(path) <= 2_000_000:
        try:
            with open(path, 'r', encoding='utf-8-sig') as file:
                sample = file.read(65536)
        except (UnicodeDecodeError, OSError):
            sample = ''
    if ext in ('.npvs', '.nvps', '.npv', '.npvt'):
        return 'NPV / NapsternetV'
    if ext == '.ovpn' or '<client>' in sample or 'remote ' in sample and 'proto ' in sample:
        return 'OpenVPN'
    if ext in ('.conf', '.wg') and ('[Interface]' in sample or '[Peer]' in sample):
        return 'WireGuard'
    if ext == '.json':
        if '"outbounds"' in sample and ('"route"' in sample or '"dns"' in sample):
            return 'Sing-box'
        if '"inbounds"' in sample and '"outbounds"' in sample:
            return 'V2Ray / Xray'
        return 'فایل JSON'
    if ext in ('.yaml', '.yml'):
        if 'outbounds:' in sample and ('route:' in sample or 'dns:' in sample):
            return 'Sing-box'
        return 'فایل YAML'
    if ext in ('.txt', '.list'):
        if re.search(r'(?m)^(vless|vmess|trojan|ss|ssr|hy2|tuic)://', sample):
            return 'لیست کانفیگ'
        return 'فایل متنی'
    labels = {
        '.zip': 'فایل فشرده ZIP',
        '.apk': 'برنامه اندروید',
        '.pdf': 'سند PDF',
        '.jpg': 'تصویر',
        '.jpeg': 'تصویر',
        '.png': 'تصویر',
        '.mp4': 'ویدئو'
    }
    return labels.get(ext, 'فایل پیوست')

async def save_document(message):
    os.makedirs('media', exist_ok=True)
    raw_name = original_name(message) or f'{message.id}.bin'
    filename = safe_filename(raw_name, f'{message.id}.bin')
    local = os.path.join('media', filename)
    path = await message.download_media(file=local)
    if not path:
        return None
    path = path.replace('\\', '/')
    extension = os.path.splitext(filename)[1].lower() or '.bin'
    id_copy = f'media/{message.id}{extension}'
    if os.path.abspath(path) != os.path.abspath(id_copy):
        try:
            shutil.copyfile(path, id_copy)
        except Exception:
            pass
    return {
        "type": "video" if getattr(message, 'video', None) or os.path.splitext(raw_name)[1].lower() in ('.mp4', '.mov', '.webm', '.mkv') else "document",
        "filename": os.path.basename(path),
        "original_name": raw_name,
        "url": path,
        "download_url": f'{PAGES}/{path}',
        "size": getattr(message.document, 'size', None),
        "kind": classify_document(raw_name, path)
    }

async def main():
    try:
        await client.start()
        print("Connected to Telegram successfully")
        os.makedirs('media', exist_ok=True)

        posts_html = '<div class="telegram-posts-grid">\n'
        posts_json = []
        nv_files = []

        async for message in client.iter_messages(channel_username, limit=HISTORY_LIMIT):
            text_raw = (message.message or '').strip()
            filename = original_name(message)
            media_info = None

            if message.document and getattr(message.document, 'size', 0) and message.document.size <= 12_000_000:
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
                        media_info = {
                            "type": "photo",
                            "filename": f'{message.id}.jpg',
                            "url": path,
                            "download_url": f'{PAGES}/{path}'
                        }
                except Exception as media_err:
                    print(f"photo skip {message.id}: {media_err}")

            if len(posts_json) < POST_LIMIT and (text_raw or media_info):
                password = extract_password(text_raw)
                visible_text = re.sub(r'(?im)^\s*(?:رمز(?:\s+عبور)?|password|pass)\s*[:：=]\s*.+?\s*$', '', text_raw).strip()
                preview = ' '.join(visible_text.split())
                if len(preview) > 150:
                    preview = preview[:147].rstrip() + '...'
                if not preview:
                    preview = media_info.get('original_name') if media_info else 'پست رسانه‌ای'
                link = f'https://t.me/{channel_username}/{message.id}'
                date_str = message.date.strftime('%Y-%m-%d %H:%M')
                posts_html += (
                    f'<article class="telegram-post">'
                    f'<a href="{link}" target="_blank" rel="noopener noreferrer" class="post-link">'
                    f'<span class="post-preview">{html.escape(preview)}</span>'
                    f'<span class="post-open-label">مشاهده پست <span aria-hidden="true">←</span></span>'
                    f'</a><small>{date_str}</small></article>\n'
                )
                post = {
                    "id": message.id,
                    "text": visible_text,
                    "preview": preview,
                    "date": int(message.date.timestamp()),
                    "date_label": date_str,
                    "link": link,
                    "media": media_info
                }
                if password:
                    post["password"] = password
                posts_json.append(post)

            if len(posts_json) >= POST_LIMIT and len(nv_files) >= 3:
                break

        if not posts_json:
            posts_html += '<div class="telegram-post">در حال حاضر پستی برای نمایش پیدا نشد.</div>\n'
        posts_html += '</div>'

        latest = nv_files[:3]
        for i, item in enumerate(latest, 1):
            src = item.get('url')
            dest = f'media/nv-latest-{i}.npvs'
            if src and os.path.isfile(src):
                shutil.copyfile(src, dest)
                item['stable_url'] = f'{PAGES}/{dest}'

        with open('telegram-posts.html', 'w', encoding='utf-8') as file:
            file.write(posts_html)
        with open('posts_formatted.json', 'w', encoding='utf-8') as file:
            json.dump(posts_json, file, ensure_ascii=False, indent=2)
        with open('media/latest-nv.json', 'w', encoding='utf-8') as file:
            json.dump(latest, file, ensure_ascii=False, indent=2)
        print(f"saved posts={len(posts_json)} nv_files={len(latest)}")

    except FloodWaitError as error:
        print(f"Flood wait error: Please wait {error.seconds} seconds")
        raise
    except Exception as error:
        print(f"Error occurred: {str(error)}")
        raise
    finally:
        await client.disconnect()
        print("Disconnected from Telegram")

if __name__ == '__main__':
    try:
        client.loop.run_until_complete(main())
    except Exception as error:
        print(f"Main execution failed: {str(error)}")
        exit(1)
