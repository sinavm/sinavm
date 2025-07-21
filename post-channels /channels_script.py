import os
import json
import re
import html
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, FloodWaitError
import asyncio

# متغیرهای محیطی
api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")
telegram_session = os.getenv("TELEGRAM_SESSION")

# بررسی متغیرهای محیطی
if not api_id or not api_hash or not telegram_session:
    raise ValueError("TELEGRAM_API_ID, TELEGRAM_API_HASH, or TELEGRAM_SESSION not set")

# ایجاد کلاینت
client = TelegramClient(StringSession(telegram_session), int(api_id), api_hash)

# تابع بررسی و استخراج کانفیگ‌ها
def extract_config(message_text):
    config_patterns = {
        "vmess": r"vmess://[^\s]+",
        "vless": r"vless://[^\s]+",
        "ss": r"ss://[^\s]+",
        "trojan": r"trojan://[^\s]+"
    }
 configs = []
    for config_type, pattern in config_patterns.items():
        matches = re.findall(pattern, message_text)
        for match in matches:
            configs.append({"type": config_type, "link": match})
    return configs

# تابع بررسی و استخراج پروکسی‌ها
def extract_proxy(message_text):
    proxy_pattern = r"https://t\.me/proxy\?server=[^\s]+"
    return re.findall(proxy_pattern, message_text)

async def main():
    try:
        # اتصال به تلگرام
        await client.start()
        print("Connected to Telegram successfully")

        # خواندن لیست کانال‌ها
        with open('post-channels/channels_name.json', 'r') as f:
            channels = json.load(f)

        posts = []
        configs = []
        proxies = []

        # جمع‌آوری پست‌ها از هر کانال/گروه
        for channel in channels:
            async for message in client.iter_messages(channel, limit=50):
                if message.message and message.message.strip():
                    # استخراج متن کوتاه
                    words = message.message.strip().split()
                    short_text = ' '.join(words[:5])
                    if len(words) > 5:
                        short_text += '...'

                    link = f'https://t.me/{channel}/{message.id}'
                    date_str = message.date.strftime('%Y-%m-%d %H:%M')

                    posts.append({
                        "text": message.message.strip(),
                        "date": int(message.date.timestamp()),
                        "link": link,
                        "channel": channel
                    })

                    # استخراج کانفیگ‌ها
                    configs.extend(extract_config(message.message))

                    # استخراج پروکسی‌ها
                    proxies.extend(extract_proxy(message.message))

        # نام‌گذاری کانفیگ‌ها
        for i, config in enumerate(configs[:10], 1):
            config["name"] = f"@sinavm-{i}"

        # ذخیره پست‌ها
        with open('post-channels/posts_formatted.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print("posts_formatted.json saved")

        # ذخیره کانفیگ‌ها
        with open('post-channels/config.json', 'w', encoding='utf-8') as f:
            json.dump(configs[:10], f, ensure_ascii=False, indent=2)
        print("config.json saved")

        # ذخیره پروکسی‌ها
        with open('post-channels/telegram_proxy.json', 'w', encoding='utf-8') as f:
            json.dump(proxies[:10], f, ensure_ascii=False, indent=2)
        print("telegram_proxy.json saved")

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