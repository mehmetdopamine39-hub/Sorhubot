#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# CK SORGUBOT ULTIMATE PRO v28.0 - RENDER EDITION
# @rinexdestek | @cksorgupanel

import os
import sys
import json
import sqlite3
import random
import asyncio
import ssl
import logging
import time
import re
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode

# ==================== TOKEN ====================
TOKEN = "8254362814:AAFWFOZNy0FEG-ZwUmeO8gZf6wfHplwfN7A"
ADMIN_IDS = [8610336203]

# ==================== RENDER AYARLARI ====================
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# ==================== PAKET KURULUMU ====================
def install_packages():
    """Paketleri kur"""
    packages = {
        'pycryptodome': 'Crypto',
        'aiohttp': 'aiohttp',
        'python-telegram-bot': 'telegram',
        'cloudscraper': 'cloudscraper',
        'gunicorn': 'gunicorn'
    }
    
    print("📦 GEREKLİ PAKETLER KURULUYOR...")
    print("━" * 40)
    
    installed = []
    failed = []
    
    for package, import_name in packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package} zaten kurulu")
            installed.append(package)
        except ImportError:
            print(f"📥 {package} kuruluyor...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
                print(f"✅ {package} kuruldu!")
                installed.append(package)
            except Exception as e:
                print(f"❌ {package} kurulamadı: {e}")
                failed.append(package)
    
    print("━" * 40)
    
    if failed:
        print(f"❌ BAŞARISIZ PAKETLER: {', '.join(failed)}")
    else:
        print("✅ TÜM PAKETLER HAZIR!")
    
    return installed, failed

INSTALLED, FAILED = install_packages()

# ==================== TELEGRAM IMPORT ====================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import cloudscraper
import aiohttp
from aiohttp import ClientSession, TCPConnector, ClientTimeout

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)
logger = logging.getLogger(__name__)

# ==================== PREMIUM EMOJİLER ====================
EMOJI = {
    "logo": "🤖",
    "sparkle": "✨",
    "fire": "🔥",
    "crown": "👑",
    "check": "✅",
    "error": "❌",
    "info": "ℹ️",
    "warning": "⚠️",
    "lock": "🔒",
    "unlock": "🔓",
    "user": "👤",
    "search": "🔍",
    "phone": "📱",
    "home": "🏠",
    "bank": "🏦",
    "chart": "📊",
    "gear": "⚙️",
    "menu": "📋",
    "back": "🔙",
    "rocket": "🚀",
    "shield": "🛡️",
    "star": "⭐",
    "gift": "🎁",
    "cool": "😎",
    "brain": "🧠",
    "target": "🎯",
    "database": "🗄️",
    "megaphone": "📢",
    "package": "📦",
    "time": "⏰"
}

STICKMAN = {
    "hello": "╔══════════════════╗\n║  🧍‍♂️  Merhaba! ║\n╚══════════════════╝",
    "search": "╔══════════════════╗\n║  🧍‍♂️  Arıyor... ║\n╚══════════════════╝",
    "done": "╔══════════════════╗\n║  🧍‍♂️  Tamam!   ║\n╚══════════════════╝",
    "error": "╔══════════════════╗\n║  🧍‍♂️  Hata!    ║\n╚══════════════════╝",
    "think": "╔══════════════════╗\n║  🧍‍♂️  Düşün... ║\n╚══════════════════╝",
    "wave": "╔══════════════════╗\n║  🧍‍♂️  Selam!   ║\n╚══════════════════╝"
}

# ==================== USER-AGENT ====================
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/',
    }

# ==================== API'LER ====================
API_URLS = {
    "tcgsm": {
        "url": "https://arastir.vip/api/tcgsm.php",
        "params": {"tc": "{value}"},
        "name": f"{EMOJI['phone']} TC'den GSM",
        "example": "12345678901",
        "desc": "TC ile GSM sorgula"
    },
    "sulale": {
        "url": "https://arastir.vip/api/sulale.php",
        "params": {"tc": "{value}"},
        "name": f"{EMOJI['user']} Sülale Sorgu",
        "example": "12345678901",
        "desc": "TC ile aile sorgula"
    },
    "gsmtc": {
        "url": "https://arastir.vip/api/gsmtc.php",
        "params": {"gsm": "{value}"},
        "name": f"{EMOJI['search']} GSM'den TC",
        "example": "5551234567",
        "desc": "GSM ile TC sorgula"
    },
    "adsoyad": {
        "url": "https://arastir.vip/api/adsoyad.php",
        "params": {"adi": "{adi}", "soyadi": "{soyadi}"},
        "name": f"{EMOJI['user']} Ad Soyad",
        "example": "roket atar",
        "multi": True,
        "desc": "Ad ve soyad ile sorgula"
    },
    "adres": {
        "url": "https://arastir.vip/api/adres.php",
        "params": {"tc": "{value}"},
        "name": f"{EMOJI['home']} Adres Sorgu",
        "example": "12345678901",
        "desc": "TC ile adres sorgula"
    },
    "isyeri": {
        "url": "https://arastir.vip/api/isyeri.php",
        "params": {"tc": "{value}"},
        "name": f"{EMOJI['bank']} İş Yeri",
        "example": "12345678901",
        "desc": "TC ile iş yeri sorgula"
    },
    "tc": {
        "url": "https://arastir.vip/api/tc.php",
        "params": {"tc": "{value}"},
        "name": f"{EMOJI['target']} TC Sorgu",
        "example": "12345678901",
        "desc": "TC doğrulama"
    },
    "iban": {
        "url": "https://anyapi.io/api/v1/iban",
        "params": {"apiKey": "6alee0spg0op0nan20fd5gjdc2tgto7poqqrbe2s06uoiepevf5ok5g", "iban": "{value}"},
        "name": f"{EMOJI['bank']} IBAN Sorgu",
        "example": "TR280006256953335759003718",
        "desc": "IBAN doğrulama",
        "cloudflare": True
    }
}

# ==================== VERİTABANI ====================
DB_FILE = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        join_date TEXT,
        total_queries INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS query_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        query_type TEXT,
        query_value TEXT,
        query_time TEXT,
        result_count INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    for admin_id in ADMIN_IDS:
        c.execute("INSERT OR IGNORE INTO users (user_id, join_date, is_admin) VALUES (?, ?, ?)",
                  (admin_id, datetime.now().isoformat(), 1))
    
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance', 'false')")
    conn.commit()
    conn.close()
    print(f"{EMOJI['check']} Veritabanı hazır")

def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (user_id, join_date) VALUES (?, ?)",
                  (user_id, datetime.now().isoformat()))
        conn.commit()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
    conn.close()
    return user

def is_admin(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
    r = c.fetchone()
    conn.close()
    return r and r[0] == 1

def is_banned(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    r = c.fetchone()
    conn.close()
    return r and r[0] == 1

def get_maintenance():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'maintenance'")
    r = c.fetchone()
    conn.close()
    return r and r[0] == 'true'

def toggle_maintenance():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'maintenance'")
    current = c.fetchone()
    new_val = 'false' if current and current[0] == 'true' else 'true'
    c.execute("UPDATE settings SET value = ? WHERE key = 'maintenance'", (new_val,))
    conn.commit()
    conn.close()
    return new_val == 'true'

def log_query(user_id, query_type, query_value, result_count=0):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO query_logs (user_id, query_type, query_value, query_time, result_count) VALUES (?, ?, ?, ?, ?)",
              (user_id, query_type, query_value[:100], datetime.now().isoformat(), result_count))
    c.execute("UPDATE users SET total_queries = total_queries + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned = 0")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_user_count():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    return c.fetchone()[0]

def get_query_count():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM query_logs")
    return c.fetchone()[0]

def get_banned_count():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
    return c.fetchone()[0]

def get_top_users(limit=5):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, total_queries FROM users ORDER BY total_queries DESC LIMIT ?", (limit,))
    return c.fetchall()

def get_recent_queries(limit=10):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, query_type, query_value, query_time, result_count FROM query_logs ORDER BY id DESC LIMIT ?", (limit,))
    return c.fetchall()

def ban_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_banned_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned = 1")
    return [row[0] for row in c.fetchall()]

# ==================== API İSTEK ====================
async def make_request(url: str, use_cloudflare: bool = False) -> Optional[Dict]:
    headers = get_headers()
    
    if use_cloudflare:
        try:
            scraper = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
            )
            response = scraper.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    return {"sonuc": response.text[:500] if response.text.strip() else "Boş sonuç"}
            return {"hata": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"hata": str(e)[:50]}
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = TCPConnector(ssl=ssl_context)
    timeout = ClientTimeout(total=30, connect=15)
    
    try:
        async with ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(url, headers=headers, allow_redirects=True) as resp:
                text = await resp.text()
                try:
                    return json.loads(text)
                except:
                    json_match = re.search(r'({.*}|\[.*\])', text, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except:
                            pass
                    return {"sonuc": text[:500] if text.strip() else "Boş sonuç"}
    except Exception as e:
        return {"hata": str(e)[:50]}

def format_result(query_type: str, data: Dict, value: str) -> Tuple[str, int]:
    if query_type == "iban":
        return format_iban(data), 1
    
    api_info = API_URLS.get(query_type, {})
    result = f"{api_info.get('name', 'Sorgu')}\n━━━━━━━━━━━━━━━━━━━━━━\n"
    result += f"{EMOJI['search']} **Aranan:** `{value}`\n"
    result += f"{EMOJI['time']} **Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    count = 0
    if isinstance(data, dict):
        for k, v in data.items():
            if v and str(v) not in ["", "None", "null", "{}", "[]", "-", "0"]:
                result += f"{EMOJI['target']} **{k.replace('_', ' ').title()}:** `{v}`\n"
                count += 1
    elif isinstance(data, list):
        for i, item in enumerate(data, 1):
            if item:
                result += f"{EMOJI['star']} **{i}. KAYIT**\n"
                if isinstance(item, dict):
                    for k, v in item.items():
                        if v:
                            result += f"   ▫️ {k}: `{v}`\n"
                else:
                    result += f"   ▫️ `{item}`\n"
                result += "\n"
                count += 1
    else:
        if str(data).strip():
            result += f"📄 **Sonuç:**\n```\n{str(data)[:500]}\n```\n"
            count = 1
    
    if count == 0:
        result = f"{EMOJI['error']} **Sonuç bulunamadı**"
    else:
        result += f"\n━━━━━━━━━━━━━━━━━━━━━━\n{EMOJI['crown']} @rinexdestek | @cksorgupanel"
    
    return result, count

def format_iban(data: Dict) -> str:
    result = f"{EMOJI['bank']} **IBAN SORGULAMA**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    valid = data.get('valid', False)
    result += f"{EMOJI['check']} **Geçerli:** {'Evet' if valid else 'Hayır'}\n"
    
    if valid:
        bank = data.get('bankData', {})
        if bank:
            result += f"\n{EMOJI['database']} **BANKA BİLGİLERİ**\n━━━━━━━━━━━━━━━━━━━━━━\n"
            if bank.get('name'):
                result += f"🏛️ **Banka:** `{bank['name']}`\n"
            if bank.get('bic'):
                result += f"🔢 **BIC:** `{bank['bic']}`\n"
            if data.get('country'):
                result += f"🌍 **Ülke:** `{data['country']}`\n"
        if data.get('bban'):
            result += f"\n{EMOJI['target']} **BBAN:** `{data['bban']}`\n"
        if data.get('account'):
            result += f"{EMOJI['bank']} **Hesap:** `{data['account']}`\n"
    
    result += f"\n━━━━━━━━━━━━━━━━━━━━━━\n{EMOJI['crown']} @rinexdestek | @cksorgupanel"
    return result

async def execute_query(query_type: str, value: str) -> Tuple[str, int, bool]:
    if query_type not in API_URLS:
        return f"{EMOJI['error']} Geçersiz sorgu", 0, False
    
    api = API_URLS[query_type]
    
    if api.get("multi"):
        parts = value.split()
        if query_type == "adsoyad":
            if len(parts) < 2:
                return f"{EMOJI['error']} Format: Ad Soyad", 0, False
            params = {"adi": parts[0], "soyadi": " ".join(parts[1:])}
        else:
            params = {k: value for k in api["params"]}
    else:
        params = {}
        for key, template in api["params"].items():
            params[key] = template.replace("{value}", value) if "{value}" in template else value
    
    url = api["url"]
    if params:
        url = f"{url}?{urlencode(params)}"
    
    data = await make_request(url, api.get("cloudflare", False))
    
    if data and "hata" not in data:
        result, count = format_result(query_type, data, value)
        return result, count, True
    else:
        hata = data.get("hata", "API yanıt vermiyor") if data else "Bağlantı hatası"
        return f"{EMOJI['error']} **HATA:** {hata}", 0, False

# ==================== MENÜLER ====================
def main_menu(is_admin_user=False):
    buttons = [
        [InlineKeyboardButton(f"{EMOJI['phone']} TC'den GSM", callback_data="q_tcgsm")],
        [InlineKeyboardButton(f"{EMOJI['user']} Sülale", callback_data="q_sulale")],
        [InlineKeyboardButton(f"{EMOJI['search']} GSM'den TC", callback_data="q_gsmtc")],
        [InlineKeyboardButton(f"{EMOJI['user']} Ad Soyad", callback_data="q_adsoyad")],
        [InlineKeyboardButton(f"{EMOJI['home']} Adres", callback_data="q_adres")],
        [InlineKeyboardButton(f"{EMOJI['bank']} İş Yeri", callback_data="q_isyeri")],
        [InlineKeyboardButton(f"{EMOJI['target']} TC Sorgu", callback_data="q_tc")],
        [InlineKeyboardButton(f"{EMOJI['bank']} IBAN", callback_data="q_iban")],
        [InlineKeyboardButton(f"{EMOJI['chart']} İstatistikler", callback_data="m_stats")],
        [InlineKeyboardButton(f"{EMOJI['info']} Yardım", callback_data="m_help")],
        [InlineKeyboardButton(f"{EMOJI['gift']} Premium", callback_data="m_premium")],
        [InlineKeyboardButton(f"{EMOJI['crown']} Kanal", url="https://t.me/cksorgupanel"),
         InlineKeyboardButton(f"{EMOJI['user']} Destek", url="https://t.me/rinexdestek")]
    ]
    if is_admin_user:
        buttons.append([InlineKeyboardButton(f"{EMOJI['gear']} Admin", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

def result_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{EMOJI['rocket']} Yeni Sorgu", callback_data="new_query")],
        [InlineKeyboardButton(f"{EMOJI['menu']} Ana Menü", callback_data="main_menu")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{EMOJI['chart']} İstatistikler", callback_data="a_stats")],
        [InlineKeyboardButton(f"{EMOJI['megaphone']} Duyuru", callback_data="a_announce")],
        [InlineKeyboardButton(f"{EMOJI['lock']} Ban Yönetimi", callback_data="a_ban")],
        [InlineKeyboardButton(f"{EMOJI['database']} Son Sorgular", callback_data="a_logs")],
        [InlineKeyboardButton(f"{EMOJI['star']} Top Kullanıcılar", callback_data="a_top")],
        [InlineKeyboardButton(f"{EMOJI['gear']} Bakım Modu", callback_data="a_maintenance")],
        [InlineKeyboardButton(f"{EMOJI['back']} Ana Menü", callback_data="main_menu")]
    ])

def ban_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{EMOJI['lock']} Banla", callback_data="ban_user"),
         InlineKeyboardButton(f"{EMOJI['unlock']} Ban Kaldır", callback_data="unban_user")],
        [InlineKeyboardButton(f"{EMOJI['database']} Banlı Liste", callback_data="banned_list")],
        [InlineKeyboardButton(f"{EMOJI['back']} Geri", callback_data="admin_panel")]
    ])

# ==================== KOMUTLAR ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if get_maintenance() and not is_admin(user_id):
        return await update.message.reply_text(f"{EMOJI['warning']} Bot bakımda!", parse_mode=ParseMode.MARKDOWN)
    
    if is_banned(user_id):
        return await update.message.reply_text(f"{EMOJI['lock']} Banlandınız! @rinexdestek", parse_mode=ParseMode.MARKDOWN)
    
    get_user(user_id)
    
    await update.message.reply_text(
        f"{STICKMAN['hello']}\n\n"
        f"{EMOJI['sparkle']} **Hoşgeldin {user.first_name}!**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{EMOJI['rocket']} **CK SORGUBOT v28.0**\n"
        f"{EMOJI['brain']} **8 Sorgu Tipi**\n"
        f"{EMOJI['shield']} **Cloudflare Korumalı**\n"
        f"{EMOJI['gift']} **Tümü ÜCRETSİZ!**\n\n"
        f"{EMOJI['cool']} *Hadi başlayalım!*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu(is_admin(user_id))
    )

async def menu_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    
    text = (
        f"{EMOJI['chart']} **İSTATİSTİKLERİN**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{EMOJI['user']} **ID:** `{query.from_user.id}`\n"
        f"{EMOJI['search']} **Sorgu:** `{user[4] if user else 0}`\n"
        f"{EMOJI['time']} **Katılım:** `{user[3][:16] if user else '?'}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{EMOJI['gift']} **Her şey ÜCRETSİZ!**"
    )
    await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=result_menu())

async def menu_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        f"{EMOJI['info']} **YARDIM & ÖRNEKLER**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{STICKMAN['think']}\n\n"
        f"📌 **Sorgu Tipleri:**\n\n"
        f"• {EMOJI['phone']} **TC'den GSM:** `12345678901`\n"
        f"• {EMOJI['user']} **Sülale:** `12345678901`\n"
        f"• {EMOJI['search']} **GSM'den TC:** `5551234567`\n"
        f"• {EMOJI['user']} **Ad Soyad:** `roket atar`\n"
        f"• {EMOJI['home']} **Adres:** `12345678901`\n"
        f"• {EMOJI['bank']} **İş Yeri:** `12345678901`\n"
        f"• {EMOJI['target']} **TC Sorgu:** `12345678901`\n"
        f"• {EMOJI['bank']} **IBAN:** `TR280006256953335759003718`\n\n"
        f"💡 **Sorguyu seç → Değeri gönder**\n"
        f"{EMOJI['crown']} @rinexdestek"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{EMOJI['back']} Geri", callback_data="main_menu")]
    ])
    await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

async def menu_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        f"{EMOJI['gift']} **PREMIUM EMOJİLER**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{EMOJI['crown']} **Bot Premium ile süslendi!**\n\n"
        f"{EMOJI['package']} **Kullanılan Paketler:**\n"
        f"• `instart_che`\n"
        f"• `wi_euthymia`\n"
        f"• `BrandsPack`\n\n"
        f"{EMOJI['sparkle']} *Premium keyfi!*"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{EMOJI['back']} Geri", callback_data="main_menu")],
        [InlineKeyboardButton(f"{EMOJI['package']} Paket Ekle", url="https://t.me/addemoji/instart_che")]
    ])
    await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

# ==================== ADMIN ====================
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    text = (
        f"{EMOJI['chart']} **BOT İSTATİSTİKLERİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{EMOJI['user']} **Kullanıcı:** `{get_user_count()}`\n"
        f"{EMOJI['search']} **Sorgu:** `{get_query_count()}`\n"
        f"{EMOJI['lock']} **Banlı:** `{get_banned_count()}`"
    )
    if query:
        await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu())
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu())

async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    logs = get_recent_queries(10)
    if logs:
        text = f"{EMOJI['database']} **SON 10 SORGU**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for log in logs:
            text += f"{EMOJI['user']} `{log[0]}` | {log[1]} | {log[2][:20]}\n"
    else:
        text = f"{EMOJI['info']} Sorgu yok"
    if query:
        await query.message.edit_text(text[:4000], parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu())
    else:
        await update.message.reply_text(text[:4000], parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu())

async def admin_top(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    top = get_top_users(5)
    if top:
        text = f"{EMOJI['star']} **TOP 5**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, (uid, q) in enumerate(top, 1):
            medal = ["🥇", "🥈", "🥉", "📌", "📌"][i-1]
            text += f"{medal} `{uid}` → `{q}` sorgu\n"
    else:
        text = f"{EMOJI['info']} Aktif kullanıcı yok"
    if query:
        await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu())
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu())

async def admin_announce(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    context.user_data["admin_action"] = "announce"
    msg = f"{EMOJI['megaphone']} **DUYURU GÖNDER**\n━━━━━━━━━━━━━━━━━━━━━━\n\nMetni yaz:\n\n❌ `/cancel`"
    if query:
        await query.message.edit_text(msg, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def admin_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    on = toggle_maintenance()
    status = "AÇIK" if on else "KAPALI"
    text = f"{EMOJI['gear']} **Bakım Modu {status}**"
    if query:
        await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu())
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu())

# ==================== CALLBACK ====================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if get_maintenance() and not is_admin(user_id) and data not in ["main_menu"]:
        await query.message.edit_text(f"{EMOJI['warning']} Bakımda!", reply_markup=main_menu(False))
        return
    
    if data == "main_menu":
        await query.message.edit_text(f"{EMOJI['menu']} **Ana Menü**", parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(is_admin(user_id)))
        return
    if data == "new_query":
        await query.message.edit_text(f"{EMOJI['rocket']} **Yeni Sorgu**", parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(is_admin(user_id)))
        return
    if data == "m_stats":
        return await menu_stats(update, context)
    if data == "m_help":
        return await menu_help(update, context)
    if data == "m_premium":
        return await menu_premium(update, context)
    
    if data.startswith("q_"):
        qtype = data.replace("q_", "")
        if qtype in API_URLS:
            context.user_data["query_type"] = qtype
            context.user_data["await_query"] = True
            api = API_URLS[qtype]
            await query.message.edit_text(
                f"{STICKMAN['search']}\n\n"
                f"**{api['name']}**\n━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 {api['desc']}\n"
                f"📌 **Örnek:** `{api['example']}`\n\n"
                f"💬 **Değeri gönder:**\n\n"
                f"❌ `/cancel`",
                parse_mode=ParseMode.MARKDOWN
            )
        return
    
    if not is_admin(user_id):
        return
    
    if data == "admin_panel":
        await query.message.edit_text(f"{EMOJI['gear']} **Admin**", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu())
        return
    if data == "a_stats":
        return await admin_stats(update, context, query)
    if data == "a_logs":
        return await admin_logs(update, context, query)
    if data == "a_top":
        return await admin_top(update, context, query)
    if data == "a_announce":
        return await admin_announce(update, context, query)
    if data == "a_maintenance":
        return await admin_maintenance(update, context, query)
    if data == "a_ban":
        await query.message.edit_text(f"{EMOJI['lock']} **Ban Yönetimi**", parse_mode=ParseMode.MARKDOWN, reply_markup=ban_menu())
        return
    if data == "banned_list":
        banned = get_banned_users()
        text = f"{EMOJI['lock']} **BANLILAR**\n━━━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join([f"• `{b}`" for b in banned]) if banned else f"{EMOJI['info']} Banlı yok"
        await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=ban_menu())
        return
    if data == "ban_user":
        context.user_data["admin_action"] = "ban"
        await query.message.edit_text(f"{EMOJI['lock']} **BANLA**\n━━━━━━━━━━━━━━━━━━━━━━\n\nID girin:\n\n❌ `/cancel`", parse_mode=ParseMode.MARKDOWN)
        return
    if data == "unban_user":
        context.user_data["admin_action"] = "unban"
        await query.message.edit_text(f"{EMOJI['unlock']} **BAN KALDIR**\n━━━━━━━━━━━━━━━━━━━━━━\n\nID girin:\n\n❌ `/cancel`", parse_mode=ParseMode.MARKDOWN)
        return

# ==================== MESAJ HANDLER ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else None
    
    if get_maintenance() and not is_admin(user_id):
        return await update.message.reply_text(f"{EMOJI['warning']} Bakımda!")
    
    if text and text.lower() in ["/cancel", "/iptal"]:
        context.user_data.clear()
        await update.message.reply_text(f"{EMOJI['check']} İptal edildi.", reply_markup=main_menu(is_admin(user_id)))
        return
    
    if context.user_data.get("admin_action") == "announce" and is_admin(user_id):
        msg = text
        users = get_all_users()
        success, fail = 0, 0
        status = await update.message.reply_text(f"{EMOJI['megaphone']} Gönderiliyor...")
        for uid in users:
            try:
                await update.message.bot.send_message(
                    uid,
                    f"{EMOJI['megaphone']} **DUYURU**\n━━━━━━━━━━━━━━━━━━━━━━\n\n{msg}\n\n{EMOJI['crown']} @rinexdestek",
                    parse_mode=ParseMode.MARKDOWN
                )
                success += 1
            except:
                fail += 1
            await asyncio.sleep(0.05)
        await status.edit_text(f"{EMOJI['check']} Gönderildi! ✅ {success} | ❌ {fail}", reply_markup=admin_menu())
        context.user_data.pop("admin_action", None)
        return
    
    if context.user_data.get("admin_action") in ["ban", "unban"] and is_admin(user_id):
        action = context.user_data["admin_action"]
        try:
            target = int(text)
            if action == "ban":
                ban_user(target)
                await update.message.reply_text(f"{EMOJI['check']} `{target}` banlandı!", parse_mode=ParseMode.MARKDOWN, reply_markup=ban_menu())
            else:
                unban_user(target)
                await update.message.reply_text(f"{EMOJI['check']} `{target}` banı kaldırıldı!", parse_mode=ParseMode.MARKDOWN, reply_markup=ban_menu())
        except ValueError:
            await update.message.reply_text(f"{EMOJI['error']} Geçersiz ID!", parse_mode=ParseMode.MARKDOWN, reply_markup=ban_menu())
        context.user_data.pop("admin_action", None)
        return
    
    if context.user_data.get("await_query"):
        qtype = context.user_data.get("query_type")
        if not qtype:
            return
        
        status = await update.message.reply_text(f"{STICKMAN['think']}\n\n⏳ **Sorgulanıyor...**", parse_mode=ParseMode.MARKDOWN)
        
        try:
            result, count, success = await execute_query(qtype, text)
            await status.delete()
            if success:
                log_query(user_id, qtype, text, count)
            await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN, reply_markup=result_menu())
        except Exception as e:
            await status.delete()
            await update.message.reply_text(f"{STICKMAN['error']}\n\n{EMOJI['error']} **HATA:** {str(e)[:100]}", parse_mode=ParseMode.MARKDOWN, reply_markup=result_menu())
        
        context.user_data.pop("await_query", None)
        context.user_data.pop("query_type", None)
        return
    
    await update.message.reply_text(f"{EMOJI['error']} Geçersiz!", reply_markup=main_menu(is_admin(user_id)))

# ==================== STARTUP NOTIFICATION ====================
async def startup_notification(app):
    """Bot başladığında admin'e ve tüm kullanıcılara mesaj gönder"""
    bot = app.bot
    
    # Admin'e özel mesaj
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"{EMOJI['fire']} **BOT BAŞLATILDI!** (Render)\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{EMOJI['package']} **Paket Durumu:**\n"
                f"✅ Kurulan: {', '.join(INSTALLED) if INSTALLED else 'Yok'}\n"
                f"{'❌ Başarısız: ' + ', '.join(FAILED) if FAILED else '✅ Tüm paketler hazır'}\n\n"
                f"{EMOJI['user']} **Admin:** @rinexdestek\n"
                f"{EMOJI['crown']} **Kanal:** @cksorgupanel\n"
                f"{EMOJI['time']} **Zaman:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                f"{STICKMAN['wave']}",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            print(f"Admin mesaj gönderilemedi: {e}")
    
    # Tüm kullanıcılara mesaj (adminler hariç)
    users = get_all_users()
    success_count = 0
    fail_count = 0
    
    for uid in users:
        if uid in ADMIN_IDS:
            continue
        try:
            await bot.send_message(
                uid,
                f"{STICKMAN['wave']}\n\n"
                f"{EMOJI['sparkle']} **CK SORGUBOT YENİDEN BAŞLATILDI!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{EMOJI['rocket']} **v28.0 RENDER EDITION**\n"
                f"{EMOJI['gift']} **Tüm sorgular ÜCRETSİZ!**\n"
                f"{EMOJI['crown']} **Destek:** @rinexdestek\n\n"
                f"{EMOJI['cool']} *Keyifli kullanımlar!*",
                parse_mode=ParseMode.MARKDOWN
            )
            success_count += 1
        except:
            fail_count += 1
        await asyncio.sleep(0.03)
    
    print(f"\n{EMOJI['megaphone']} Başlangıç mesajları gönderildi!")
    print(f"✅ Başarılı: {success_count} | ❌ Başarısız: {fail_count}")

# ==================== WEBHOOK SETUP ====================
async def setup_webhook(app):
    """Webhook kurulumu"""
    if WEBHOOK_URL:
        webhook_path = f"/webhook/{TOKEN}"
        full_url = f"{WEBHOOK_URL}{webhook_path}"
        
        await app.bot.set_webhook(url=full_url)
        print(f"{EMOJI['check']} Webhook kuruldu: {full_url}")
        
        # Flask benzeri web server başlat (Render için)
        from aiohttp import web
        
        async def webhook_handler(request):
            """Webhook isteklerini işle"""
            try:
                data = await request.json()
                update = Update.de_json(data, app.bot)
                await app.process_update(update)
                return web.Response(status=200)
            except Exception as e:
                print(f"Webhook hatası: {e}")
                return web.Response(status=500)
        
        app_web = web.Application()
        app_web.router.add_post(f"/webhook/{TOKEN}", webhook_handler)
        
        # Web sunucusunu başlat
        runner = web.AppRunner(app_web)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
        await site.start()
        print(f"{EMOJI['fire']} Webhook sunucusu başlatıldı: {PORT}")
        
        return runner, site

# ==================== ANA FONKSİYON ====================
def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   CK SORGUBOT ULTIMATE v28.0 - RENDER EDITION              ║")
    print("║          @rinexdestek | @cksorgupanel                       ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # Proxy temizle
    for p in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        os.environ.pop(p, None)
    
    # Veritabanını hazırla
    init_db()
    
    # Application oluştur
    app = Application.builder().token(TOKEN).build()
    
    # Handler'ları ekle
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Başlangıç bildirimleri
    async def startup_callback():
        await startup_notification(app)
    
    app.job_queue.run_once(startup_callback, 0)
    
    print(f"\n{EMOJI['fire']} Bot Başlatılıyor...")
    print(f"{EMOJI['crown']} @rinexdestek")
    print(f"{EMOJI['gift']} Premium Emojiler: AKTİF")
    print(f"{EMOJI['package']} Kurulu Paketler: {', '.join(INSTALLED)}")
    print(f"{EMOJI['sparkle']} Her şey ÜCRETSİZ!")
    print(f"{EMOJI['gear']} Port: {PORT}")
    print(f"{EMOJI['info']} Webhook: {'AKTİF' if WEBHOOK_URL else 'Polling'}\n")
    
    # Webhook veya Polling
    if WEBHOOK_URL:
        # Webhook modu
        loop = asyncio.get_event_loop()
        
        async def run_webhook():
            runner, site = await setup_webhook(app)
            try:
                # Sonsuz döngü
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                await runner.cleanup()
        
        loop.run_until_complete(run_webhook())
    else:
        # Polling modu (geliştirme için)
        app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
