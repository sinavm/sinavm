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
    print("Error: TELEGRAM_API_ID, TELEGRAM_API_HASH, or TELEGRAM_SESSION not set")
    exit(1)

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
        if matches:
            print(f"Found {len(matches)} {config_type} configs: {matches}")
        for match in matches:
            configs.append({"type": config_type, "link": match})
    return configs

# تابع بررسی و استخراج پروکسی‌ها
def extract_proxy(message_text):
    proxy_pattern = r"https://t\.me/proxy\?server=[^\s]+"
    proxies = re.findall(proxy_pattern, message_text)
    if proxies:
        print(f"Found {len(proxies)} proxies: {proxies}")
    return proxies

async def main():
    try:
        # بررسی وجود فایل channels_name.json
        if not os.path.exists('post-channels/channels_name.json'):
            print("Error: channels_name.json not found in post-channels/")
            return

        # خواندن لیست کانال‌ها
        with open('post-channels/channels_name.json', 'r') as f:
            channels = json.load(f)
        print(f"Loaded {len(channels)} channels: {channels}")

        # بررسی دسترسی به کانال‌ها
        valid_channels = []
        for channel in channels:
            try:
                entity = await client.get_entity(channel)
                valid_channels.append(channel)
                print(f"Access to {channel} confirmed, ID: {entity.id}")
            except Exception as e:
                print(f"Cannot access {channel}: {str(e)}")
                continue

        if not valid_channels:
            print("Error: No accessible channels found")
            return

        # اتصال به تلگرام
        await client.start()
        print("Connected to Telegram successfully")

        posts = []
        configs = []
        proxies = []

        # جمع‌آوری پست‌ها از هر کانال/گروه
        for channel in valid_channels:
            try:
                print(f"Fetching messages from channel: {channel}")
                message_count = 0
                async for message in client.iter_messages(channel, limit=50):
                    await asyncio.sleep(0.5)  # تأخیر برای جلوگیری از FloodWaitError
                    if message.message and message.message.strip():
                        message_count += 1
                        print(f"Processing message {message.id} from {channel}: {message.message[:50]}...")
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
                print(f"Found {message_count} valid messages in {channel}")
            except Exception as e:
                print(f"Error fetching messages from {channel}: {str(e)}")
                continue

        print(f"Collected {len(posts)} posts, {len(configs)} configs, {len(proxies)} proxies")

        # نام‌گذاری کانفیگ‌ها
        for i, config in enumerate(configs[:10], 1):
            config["name"] = f"@sinavm-{i}"

        # ذخیره پست‌ها
        if posts:
            with open('post-channels/posts_formatted.json', 'w', encoding='utf-8') as f:
                json.dump(posts, f, ensure_ascii=False, indent=2)
            print("posts_formatted.json saved")
        else:
            print("No posts collected, skipping posts_formatted.json")

        # ذخیره کانفیگ‌ها
        if configs:
            with open('post-channels/config.json', 'w', encoding='utf-8') as f:
                json.dump(configs[:10], f, ensure_ascii=False, indent=2)
            print("config.json saved")
        else:
            print("No configs collected, skipping config.json")

        # ذخیره پروکسی‌ها
        if proxies:
            with open('post-channels/telegram_proxy.json', 'w', encoding='utf-8') as f:
                json.dump(proxies[:10], f, ensure_ascii=False, indent=2)
            print("telegram_proxy.json saved")
        else:
            print("No proxies collected, skipping telegram_proxy.json")

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
