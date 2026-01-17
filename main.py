import os
import json
from telethon import TelegramClient, events
from gtts import gTTS

CONFIG_FILE = 'config.json'
user_data = {}

# --- Configuration Handling ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_config(bot_token, api_id, api_hash, admin_id):
    config = {
        "bot_token": bot_token,
        "api_id": int(api_id),
        "api_hash": api_hash,
        "admin_id": int(admin_id)
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    return config

config = load_config()
if not config:
    print("--- First Time Setup ---")
    bot_token = input("Enter Bot Token: ")
    api_id = input("Enter API ID: ")
    api_hash = input("Enter API Hash: ")
    admin_id = input("Enter Admin User ID: ")
    config = save_config(bot_token, api_id, api_hash, admin_id)

client = TelegramClient('bot_session', config['api_id'], config['api_hash']).start(bot_token=config['bot_token'])

# --- Voice Generation Function (Fixed for Mixed Text) ---
def generate_voice(text):
    output_file = "voice.mp3"
    # 'hi' (Hindi) ল্যাঙ্গুয়েজ কোডটি বাংলা, হিন্দি এবং ইংরেজি মিক্সড পড়ার জন্য সেরা কাজ করে
    tts = gTTS(text=text, lang='hi', slow=False)
    tts.save(output_file)
    return output_file

# --- Bot Commands ---

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id != config['admin_id']:
        return
    await event.respond("বট চালু হয়েছে!\n\n- যেকোনো টেক্সট পাঠান (বাংলা+হিন্দি+ইংলিশ মিক্স কাজ করবে)\n- /long দিয়ে লম্বা মেসেজ মোড চালু করুন\n- /gen দিয়ে অডিও জেনারেট করুন")

@client.on(events.NewMessage(pattern='/long'))
async def long_mode(event):
    if event.sender_id != config['admin_id']: return
    user_data[event.sender_id] = []
    await event.respond("🎤 **Long Mode ON**\nএখন একের পর এক টেক্সট পাঠান। শেষ হলে /gen লিখুন।")

@client.on(events.NewMessage(pattern='/gen'))
async def generate_long_voice(event):
    if event.sender_id != config['admin_id']: return
    
    if event.sender_id not in user_data or not user_data[event.sender_id]:
        return await event.respond("আগে কিছু টেক্সট পাঠান!")
    
    full_text = " ".join(user_data[event.sender_id])
    msg = await event.respond("পুরো টেক্সটটি প্রসেস করে ভয়েস বানানো হচ্ছে...")
    
    try:
        voice_file = generate_voice(full_text)
        await client.send_file(event.chat_id, voice_file, caption="✅ Long Voice Generated")
        os.remove(voice_file)
        del user_data[event.sender_id]
        await msg.delete()
    except Exception as e:
        await msg.edit(f"Error: {str(e)}")

@client.on(events.NewMessage)
async def handle_text(event):
    if event.sender_id != config['admin_id'] or event.text.startswith('/'):
        return

    # /long মোডে থাকলে ডাটা সেভ হবে
    if event.sender_id in user_data:
        user_data[event.sender_id].append(event.text)
        await event.respond(f"✅ মেসেজ {len(user_data[event.sender_id])} সেভ হলো।")
        return

    # সাধারণ মোড
    msg = await event.respond("ভয়েস তৈরি হচ্ছে...")
    try:
        voice_file = generate_voice(event.text)
        await client.send_file(event.chat_id, voice_file)
        os.remove(voice_file)
        await msg.delete()
    except Exception as e:
        await msg.edit(f"Error: {str(e)}")

print("বটটি এখন সচল। টেলিগ্রামে চেক করুন।")
client.run_until_disconnected()
