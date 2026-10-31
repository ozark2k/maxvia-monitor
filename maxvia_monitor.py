#!/usr/bin/env python3
"""
MaxVia88 Stock Monitor & Telegram Notifier

Automated stock monitoring script for maxvia88.com with Chrome cookie decryption,
category scraping, and Telegram alerts.
"""

import glob
import json
import logging
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
import calendar
from hashlib import pbkdf2_hmac
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, "stock_state.json")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "monitor.log")
WEB_DIR = os.path.join(SCRIPT_DIR, "web")
MAXVIA_STATE_WEB_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "limpador_contas", "maxvia_state.json"))
CURRENT_MAXVIA_USER_INFO = {"username": "Itooh - ID: 4271", "balance_str": "$211.08", "balance_usd": 211.08}
LATEST_WEB_STATE = {}
IS_CLOUD_SERVER = bool(os.environ.get("RENDER") or os.environ.get("PORT"))


def check_and_sync_cookie_to_git(fresh_cookie: str):
    """If running on local Mac and fresh cookie differs from render.yaml, push to GitHub so Render auto-redeploys."""
    if IS_CLOUD_SERVER or not fresh_cookie or "laravel_session=" not in fresh_cookie:
        return
    render_yaml_path = os.path.join(SCRIPT_DIR, "render.yaml")
    if not os.path.exists(render_yaml_path):
        return
    try:
        with open(render_yaml_path, "r", encoding="utf-8") as f:
            content = f.read()
        m = re.search(r'(- key: MAXVIA_COOKIE\s*\n\s*value:\s*)"([^"]*)"', content)
        if m and m.group(2) != fresh_cookie:
            logging.info("Sessão nova do MaxVia88 detectada no Chrome! Atualizando render.yaml e enviando para o GitHub...")
            new_content = content[:m.start(2)] + fresh_cookie + content[m.end(2):]
            with open(render_yaml_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            def do_push():
                try:
                    subprocess.run(["git", "add", "render.yaml", "config.json"], cwd=SCRIPT_DIR, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(["git", "commit", "-m", "Auto-sync fresh Chrome session cookie to Render"], cwd=SCRIPT_DIR, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(["git", "push", "origin", "main"], cwd=SCRIPT_DIR, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    logging.info("Sessão nova enviada para o GitHub com sucesso! O Render reiniciará com os cookies atualizados.")
                except Exception as ex:
                    logging.warning(f"Git push cookie sync note: {ex}")
            threading.Thread(target=do_push, daemon=True).start()
    except Exception as e:
        logging.debug(f"Error checking cookie sync: {e}")


# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)


def load_config() -> dict:
    """Load configuration from config.json if exists."""
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            logging.error(f"Error loading config.json: {e}")
    return config


def save_config(config: dict):
    """Save configuration to config.json."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logging.info("Configuration saved to config.json")
    except Exception as e:
        logging.error(f"Error saving config.json: {e}")



def get_chrome_cookies() -> str:
    """Extract maxvia88 session cookies from local Google Chrome profile on macOS or config/env."""
    # First: Try live extraction from macOS Google Chrome if available
    try:
        config = load_config()
        hex_key = config.get("chrome_storage_hex_key")
        try:
            cmd = ["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage"]
            password = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).strip()
            salt = b"saltysalt"
            key = pbkdf2_hmac("sha1", password, salt, 1003, 16)
            hex_key = key.hex()
            if config.get("chrome_storage_hex_key") != hex_key:
                config["chrome_storage_hex_key"] = hex_key
                save_config(config)
        except Exception:
            pass

        if not hex_key:
            raise ValueError("No chrome key available")

        hex_iv = (b" " * 16).hex()

        paths = glob.glob(os.path.expanduser("~/Library/Application Support/Google/Chrome/*/Cookies")) + \
                glob.glob(os.path.expanduser("~/Library/Application Support/Google/Chrome/*/Network/Cookies"))
        cookies_dict = {}

        for path in paths:
            if not os.path.isfile(path):
                continue
            tmp_path = "/tmp/chrome_cookies_maxvia_tmp"
            shutil.copyfile(path, tmp_path)
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, name, value, encrypted_value FROM cookies WHERE host_key LIKE '%maxvia88%'")
            for host_key, name, val, enc_val in cursor.fetchall():
                if name not in ["laravel_session", "XSRF-TOKEN"]:
                    continue
                if val:
                    cookies_dict[name] = val
                elif enc_val and enc_val.startswith(b"v10"):
                    enc_data = enc_val[3:]
                    proc = subprocess.Popen(
                        ["openssl", "enc", "-d", "-aes-128-cbc", "-K", hex_key, "-iv", hex_iv],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    out, err = proc.communicate(input=enc_data)
                    if out:
                        pad = out[-1]
                        if isinstance(pad, int) and 1 <= pad <= 16:
                            out = out[:-pad]
                        val_str = out.decode("utf-8", errors="ignore")
                        m = re.search(r"(eyJ[A-Za-z0-9%+/=]+)", val_str)
                        if m:
                            cookies_dict[name] = m.group(1)
            conn.close()

        if cookies_dict and "laravel_session" in cookies_dict:
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
            logging.info(f"Successfully extracted live Chrome session cookies ({len(cookies_dict)} keys).")
            try:
                cfg = load_config()
                if cfg.get("cookie") != cookie_str:
                    cfg["cookie"] = cookie_str
                    save_config(cfg)
                check_and_sync_cookie_to_git(cookie_str)
            except Exception:
                pass
            return cookie_str
    except Exception as e:
        logging.debug(f"Live Chrome cookie extraction fallback: {e}")

    # Second: Fall back to environment variable (e.g. on Render)
    env_cookie = os.environ.get("MAXVIA_COOKIE")
    if env_cookie:
        return env_cookie

    # Third: Fall back to config.json
    config = load_config()
    cfg_cookie = config.get("cookie")
    if cfg_cookie:
        return cfg_cookie

    return ""


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """Send HTML message via Telegram Bot API."""
    if not bot_token or not chat_id or "YOUR_TELEGRAM" in bot_token:
        logging.warning("Telegram Bot Token or Chat ID not set in config.json. Displaying preview in console:")
        print("\n" + "=" * 50)
        print("[TELEGRAM MESSAGE PREVIEW]")
        print(message)
        print("=" * 50 + "\n")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': 'true'
    }).encode('utf-8')

    logging.info(f"Enviando mensagem para o Telegram:\n{message}")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res = response.read().decode('utf-8')
            res_json = json.loads(res)
            if res_json.get('ok'):
                logging.info("Telegram notification sent successfully.")
                return True
            else:
                logging.error(f"Telegram API error response: {res}")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")

    return False


def fetch_page_html(url: str, cookie_header: str) -> str:
    """Fetch HTML content from specified URL with retry."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    if cookie_header:
        headers['Cookie'] = cookie_header

    req = urllib.request.Request(url, headers=headers)
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logging.debug(f"Page 404 (Not found): {url}")
                return ""
            else:
                logging.warning(f"HTTP {e.code} for {url} (tentativa {attempt+1})")
        except Exception as e:
            logging.error(f"Failed to fetch {url} (tentativa {attempt+1}): {e}")
        if attempt == 0:
            time.sleep(1)
    return ""


def normalize_title(title: str) -> str:
    """Clean and normalize product title by stripping emojis, badges, and extra whitespace."""
    if not title:
        return ""
    title = re.sub(r'Hot Item\s*\(Recommended\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'Recommended', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\bNew\b', '', title, flags=re.IGNORECASE)
    title = re.sub(r'[^\w\s\(\)\-\.\+]', '', title, flags=re.UNICODE)
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def normalize_price(price_str: str) -> str:
    """Extract and normalize price string (e.g. '$0.66' or 'R$4.13')."""
    if not price_str:
        return ""
    m = re.search(r'(\$\s*[\d\.]+|R\$\s*[\d\.,]+)', price_str)
    if m:
        return re.sub(r'\s+', '', m.group(1))
    return price_str.strip()


def parse_price_val(price_str: str) -> float:
    """Parse numeric price float from price string like '$0.84', 'R$ 5,16', or '55.000 Coins'."""
    if not price_str:
        return 0.0
    if isinstance(price_str, (int, float)):
        return float(price_str)
    if 'coin' in str(price_str).lower():
        cleaned = re.sub(r'[^\d]', '', str(price_str))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    cleaned = str(price_str).replace('$', '').replace('R$', '').replace('»', '').strip()
    m = re.search(r'[\d]+(?:[.,]\d+)?', cleaned)
    if m:
        try:
            return float(m.group(0).replace(',', '.'))
        except ValueError:
            return 0.0
    return 0.0


def make_product_id(title: str, price: str) -> str:
    """Generate deterministic product ID."""
    clean_t = normalize_title(title).lower()
    clean_p = normalize_price(price)
    return f"{clean_t}_{clean_p}"


def is_buyviafb_target(item: dict) -> bool:
    """
    Retorna True para os produtos solicitados do BuyViaFB:
    1. buyviafb_194: 1000x Brazil No2fa 0-30 Fr Live Ads (45.000 Coins)
    2. buyviafb_195: 1000x Brazil No2fa 30+ Fr Live Ads (55.000 Coins)
    3. buyviafb_133: (HOT) Acc Old 1000x Soak 9 Months Full 2fa 1 Hotmail Trust 30 Friend (80.000 Coins)
    """
    if not item or not isinstance(item, dict):
        return False
    if item.get('site') != 'buyviafb':
        return False
    b_id = str(item.get('buyviafb_id', ''))
    if b_id in ['194', '195', '133']:
        return True
    p_id = str(item.get('id', ''))
    if p_id in ['buyviafb_194', 'buyviafb_195', 'buyviafb_133']:
        return True
    title = (item.get('raw_title') or item.get('title') or '').lower()
    if 'brazil' in title:
        return True
    if 'soak 9 months' in title or ('soak' in title and '9 month' in title):
        return True
    return False


def is_primary_084_profile(item: dict) -> bool:
    """
    Retorna True EXCLUSIVAMENTE para o perfil principal ⭐Acc Farmed 2026 (2FA) ($0.84) da MaxVia88.
    Nenhum outro produto/perfil (nem 902, nem XMDT, nem Scan, nem TheFBStore) pode retornar True.
    """
    if not item or not isinstance(item, dict):
        return False
    if item.get('site', 'maxvia88') != 'maxvia88':
        return False

    title = normalize_title(item.get('title', '')).lower()
    price_val = parse_price_val(item.get('price', ''))

    # Descarta explicitamente qualquer outro perfil
    for forbidden in ['902', 'xmdt', 'scan', '2025', 'combo', 'personal', 'set 5']:
        if forbidden in title:
            return False

    # Deve conter 2026 e farmed
    if '2026' not in title or 'farmed' not in title:
        return False

    # Preço do perfil principal é em torno de $0.84 - $0.88 (margem flexível de 0.70 a 1.20)
    if price_val > 0 and not (0.70 <= price_val <= 1.20):
        return False

    return True


def is_brazil_profile(item: dict) -> bool:
    """
    Perfis do Brasil desativados a pedido do usuário.
    """
    return False



def is_hot_item_target(item: dict) -> bool:
    """
    Retorna True para os 7 perfis solicitados da categoria 'Hot Item (Recommended)':
    1. ⭐Acc Farmed 902 New 2026 (2FA) ($0.74)
    2. ⭐Acc Farmed 2025 (2FA) ($1.11)
    3. ⭐Acc Farmed 2026 (2FA) ($0.88)
    4. ⭐Acc Farmed XMDT (2FA) ($0.70)
    5. S1|Personal Ads – Limit $50 ($3.13)
    6. Set 5-9 Ads Limit 50$ ($4.30)
    7. V1.0| Acc 902 OLD Loss Greentick (NO2FA) ($2.15)
    
    EXCLUI TERMINANTEMENTE:
    - Combo 1 Account + 9 Ads limit 50$ (ou qualquer Combo 1 Account)
    """
    if not item or not isinstance(item, dict):
        return False
    if item.get('site', 'maxvia88') != 'maxvia88':
        return False

    title_clean = normalize_title(item.get('title', '')).lower()
    raw_title = str(item.get('raw_title', '')).lower()
    p_id = str(item.get('id', '')).lower()
    full_text = f"{p_id} {title_clean} {raw_title}"

    # Exclusão estrita solicitada pelo usuário: "Menos esse combo, tá? Combo 1 account"
    if "combo" in full_text and "1 account" in full_text:
        return False

    # 1. Acc Farmed 902 New 2026 (2FA) ($0.74)
    if "farmed 902" in full_text or ("farmed" in full_text and "902" in full_text and "2026" in full_text):
        return True

    # 2. Acc Farmed 2025 (2FA) ($1.11)
    if "farmed 2025" in full_text and not any(x in full_text for x in ["combo", "set", "902", "xmdt"]):
        return True

    # 3. Acc Farmed 2026 (2FA) ($0.88)
    if "farmed 2026" in full_text and not any(x in full_text for x in ["combo", "set", "902", "xmdt"]):
        return True

    # 4. Acc Farmed XMDT (2FA) ($0.70)
    if "farmed xmdt" in full_text or ("xmdt" in full_text and "farmed" in full_text):
        return True

    # 5. S1|Personal Ads – Limit $50 ($3.13)
    if ("s1" in full_text or "personal ads" in full_text) and "limit" in full_text and "50" in full_text:
        if "combo" not in full_text and "set" not in full_text:
            return True

    # 6. Set 5-9 Ads Limit 50$ ($4.30)
    if "set 5-9" in full_text or ("set" in full_text and "5-9" in full_text and "limit" in full_text):
        return True

    # 7. V1.0| Acc 902 OLD Loss Greentick (NO2FA) ($2.15)
    if "902 old loss" in full_text or "greentick" in full_text or "902 old loss greentick" in full_text:
        return True

    return False


def get_hot_item_info(item: dict):
    """Retorna metadados visuais e nome limpo para os 7 perfis Hot Items monitorados."""
    if not is_hot_item_target(item):
        return None
    title_clean = normalize_title(item.get('title', '')).lower()
    raw_title = str(item.get('raw_title', '')).lower()
    p_id = str(item.get('id', '')).lower()
    full_text = f"{p_id} {title_clean} {raw_title}"

    if "farmed 902" in full_text or ("farmed" in full_text and "902" in full_text and "2026" in full_text):
        return {"name": "Acc Farmed 902 New 2026 (2FA)", "price": "$0.74", "icon": "⭐"}
    if "farmed 2025" in full_text:
        return {"name": "Acc Farmed 2025 (2FA)", "price": "$1.11", "icon": "⭐"}
    if "farmed 2026" in full_text:
        return {"name": "Acc Farmed 2026 (2FA)", "price": "$0.88", "icon": "⭐"}
    if "farmed xmdt" in full_text or ("xmdt" in full_text and "farmed" in full_text):
        return {"name": "Acc Farmed XMDT (2FA)", "price": "$0.70", "icon": "⭐"}
    if ("s1" in full_text or "personal ads" in full_text) and "limit" in full_text and "50" in full_text:
        return {"name": "S1|Personal Ads – Limit $50", "price": "$3.13", "icon": "⚡"}
    if "set 5-9" in full_text or ("set" in full_text and "5-9" in full_text and "limit" in full_text):
        return {"name": "Set 5-9 Ads Limit 50$", "price": "$4.30", "icon": "⚡"}
    if "902 old loss" in full_text or "greentick" in full_text:
        return {"name": "V1.0| Acc 902 OLD Loss Greentick (NO2FA)", "price": "$2.15", "icon": "🛡️"}
    return {"name": item.get('raw_title') or item.get('title'), "price": item.get('price', ''), "icon": "🔥"}


def is_budget_farmed_profile(item: dict) -> bool:
    """
    Retorna True para os perfis acessíveis/populares da MaxVia88:
    - ⭐Acc Farmed 2025 (2FA) ($1.11)
    - ⭐Acc Farmed 2026 (2FA) ($0.88)
    """
    if not item or not isinstance(item, dict):
        return False
    if item.get('site', 'maxvia88') != 'maxvia88':
        return False
    title = normalize_title(item.get('title', '')).lower()
    if 'farmed' in title:
        if '2025' in title or '2026' in title:
            if not any(x in title for x in ['combo', 'set', '902', 'xmdt', 'scan']):
                return True
    return False


def get_cat219_info(item: dict):
    """
    Identifica e retorna metadados visuais para os perfis prioritários da Categoria 219:
    1. Via Ramdom New (2FA) ($1.29) -> Azul 🔵
    2. Acc Farm 6 Month+ (2FA) ($1.04) -> Verde 🟢
    (Acc Scan 1 Year+ desativado a pedido do usuário)
    """
    if not item or not isinstance(item, dict):
        return None
    if item.get('site', 'maxvia88') != 'maxvia88':
        return None
    p_id = str(item.get('id', '')).lower()
    title = normalize_title(item.get('title', '')).lower()
    raw_title = str(item.get('raw_title', '')).lower()
    
    # 1. Via Ramdom New (2FA) ($1.29)
    if 'via ramdom (2fa)' in p_id or 'via ramdom new (2fa)' in p_id or (('ramdom' in raw_title or 'ramdom' in title) and '2fa' in (raw_title + title) and not any(x in (raw_title + title) for x in ['clone', 'old', 'friend'])):
        return {
            'key': 'ramdom',
            'badge': '🔵',
            'color': 'AZUL',
            'clean_name': 'Via Ramdom New (2FA)',
            'url': item.get('url') or 'https://maxvia88.com/categories/219'
        }

    # 2. Acc Farm 6 Month+ (2FA) (V1 e V2)
    if 'farm 6 month' in p_id or ('farm' in (raw_title + title) and '6 month' in (raw_title + title) and '2fa' in (raw_title + title)):
        is_v2 = 'v2' in raw_title or 'v2' in title or 'v2' in p_id
        c_name = 'V2| Acc Farm 6 Month+ (2FA)' if is_v2 else 'Acc Farm 6 Month+ (2FA)'
        return {
            'key': 'farm6m_v2' if is_v2 else 'farm6m',
            'badge': '🟢',
            'color': 'VERDE',
            'clean_name': c_name,
            'url': item.get('url') or 'https://maxvia88.com/categories/219'
        }
    return None


def is_via_random_new_profile(item: dict) -> bool:
    """Compatibilidade: retorna True se for o perfil Via Ramdom New da Categoria 219."""
    info = get_cat219_info(item)
    return bool(info and info['key'] == 'ramdom')




def parse_products_from_html(html: str) -> dict:
    """Parse products and stock numbers from maxvia88 HTML."""
    if not html:
        return {}

    soup = BeautifulSoup(html, 'html.parser')
    products = {}

    # Format 1: Public custom-control-label items (Primary catalog grid)
    labels = soup.find_all('label', class_='custom-control-label')
    for label in labels:
        stock_div = label.find('div', class_='item-circle')
        title_span = label.find('span', class_='font-w700')
        desc_span = label.find('span', class_='font-size-sm')
        price_span = label.find('strong', class_='text-danger')

        if title_span and stock_div:
            raw_title = title_span.get_text(strip=True)
            clean_t = normalize_title(raw_title)
            desc = desc_span.get_text(strip=True) if desc_span else ''
            raw_price = price_span.get_text(strip=True).replace('»', '').strip() if price_span else ''
            clean_p = normalize_price(raw_price)

            try:
                stock = int(stock_div.get_text(strip=True))
            except ValueError:
                stock = 0

            prod_id = make_product_id(clean_t, clean_p)
            if prod_id:
                products[prod_id] = {
                    'id': prod_id,
                    'title': clean_t or raw_title,
                    'raw_title': raw_title or clean_t,
                    'desc': desc,
                    'stock': stock,
                    'price': clean_p or raw_price
                }

    # Format 2: Dashboard card items (.clone-item, .item-custom, .block-link-pop)
    cards = soup.find_all(class_=lambda c: c and ('clone-item' in c or 'item-custom' in c or 'block-link-pop' in c))
    for card in cards:
        title_span = card.find(class_=lambda c: c and 'js-tooltip-enabled' in c)
        raw_title = ''
        if title_span:
            raw_title = title_span.get('data-original-title') or title_span.get_text(strip=True)
        if not raw_title:
            btn_info = card.find('button', class_=lambda c: c and 'btnShowInfoCategory' in c)
            if btn_info:
                raw_title = btn_info.get('data-type-title', '')
        
        clean_t = normalize_title(raw_title)
        if not clean_t:
            continue
        
        price_elem = card.find('strong', class_='text-danger')
        raw_price = price_elem.get_text(strip=True) if price_elem else ''
        clean_p = normalize_price(raw_price)

        stock_elem = card.find(class_=lambda c: c and 'badge' in c)
        stock = 0
        if stock_elem:
            try:
                stock = int(re.search(r'\d+', stock_elem.get_text(strip=True)).group())
            except (ValueError, AttributeError):
                stock = 0
        else:
            buy_btn = card.find('button', class_=lambda c: c and 'buy-btn' in c)
            if buy_btn and buy_btn.get('data-available'):
                try:
                    stock = int(buy_btn.get('data-available'))
                except ValueError:
                    stock = 0

        prod_id = make_product_id(clean_t, clean_p)
        if prod_id and prod_id not in products:
            products[prod_id] = {
                'id': prod_id,
                'title': clean_t,
                'raw_title': raw_title or clean_t,
                'desc': card.get_text(separator=' ', strip=True)[:100],
                'stock': stock,
                'price': clean_p or raw_price
            }

    return products


def extract_maxvia_user_info(html: str) -> dict:
    """Extract user balance and account name from MaxVia88 HTML."""
    if not html:
        return {}
    try:
        soup = BeautifulSoup(html, 'html.parser')
        balance_elem = soup.find(id='top_balance')
        user_str = ""
        for a in soup.find_all('a', href=re.compile(r'/account')):
            t = a.get_text(' ', strip=True)
            if 'ID:' in t:
                user_str = re.sub(r'\s+', ' ', t).strip()
                break

        balance_str = balance_elem.get_text(strip=True) if balance_elem else ""
        balance_val = 0.0
        if balance_str:
            m = re.search(r'[\d\.]+', balance_str)
            if m:
                balance_val = float(m.group(0))

        res = {}
        if user_str:
            res['username'] = user_str
        if balance_str:
            res['balance_str'] = balance_str
            res['balance_usd'] = balance_val
        return res
    except Exception as e:
        logging.debug(f"Error extracting user info: {e}")
        return {}


LAST_BALANCE_REFRESH_TIME = 0


def refresh_maxvia_balance(force: bool = False) -> dict:
    """Fast live balance refresh directly from MaxVia88 homepage (<1.5s)."""
    global LAST_BALANCE_REFRESH_TIME, CURRENT_MAXVIA_USER_INFO, LATEST_WEB_STATE
    now = time.time()
    # Cache for 4s unless forced to avoid flooding MaxVia88 with rapid duplicate clicks
    if not force and (now - LAST_BALANCE_REFRESH_TIME < 4) and CURRENT_MAXVIA_USER_INFO.get('balance_usd') is not None:
        return CURRENT_MAXVIA_USER_INFO

    try:
        cookie_header = get_chrome_cookies()
        html = fetch_page_html("https://maxvia88.com/", cookie_header)
        if html:
            u_info = extract_maxvia_user_info(html)
            if u_info and u_info.get('balance_usd') is not None:
                CURRENT_MAXVIA_USER_INFO.update(u_info)
                LAST_BALANCE_REFRESH_TIME = now
                if not isinstance(LATEST_WEB_STATE, dict):
                    LATEST_WEB_STATE = {}
                LATEST_WEB_STATE['balance_usd'] = u_info['balance_usd']
                LATEST_WEB_STATE['balance_str'] = u_info.get('balance_str', f"${u_info['balance_usd']:.2f}")
                if u_info.get('username'):
                    LATEST_WEB_STATE['username'] = u_info['username']
                LATEST_WEB_STATE['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Save directly to disk for web server
                web_state_path = os.path.join(WEB_DIR, "maxvia_state.json")
                try:
                    with open(web_state_path, "w", encoding="utf-8") as f:
                        json.dump(LATEST_WEB_STATE, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

                logging.info(f"[FAST SYNC] Saldo MaxVia88 sincronizado ao vivo: {u_info.get('balance_str')} ({u_info.get('username')})")
    except Exception as e:
        logging.warning(f"Erro no refresh_maxvia_balance: {e}")

    return CURRENT_MAXVIA_USER_INFO


def fetch_all_products() -> dict:
    """Fetch all products across main page and all dynamically discovered categories."""
    global CURRENT_MAXVIA_USER_INFO
    cookie_header = get_chrome_cookies()

    urls_to_scan = set(["https://maxvia88.com/"])

    # First fetch main page to discover category links
    main_html = fetch_page_html("https://maxvia88.com/", cookie_header)
    if main_html:
        u_info = extract_maxvia_user_info(main_html)
        if u_info:
            CURRENT_MAXVIA_USER_INFO.update(u_info)

    soup = BeautifulSoup(main_html, 'html.parser')
    for a in soup.find_all('a', href=True):
        m = re.search(r'/categories/(\d+)', a['href'])
        if m:
            urls_to_scan.add(f"https://maxvia88.com/categories/{m.group(1)}")

    # Active categories on MaxVia88
    for i in [1, 6, 16, 19, 118, 212, 217, 219, 220, 221]:
        urls_to_scan.add(f"https://maxvia88.com/categories/{i}")

    all_products = {}
    for url in urls_to_scan:
        html = fetch_page_html(url, cookie_header)
        if html:
            u_info = extract_maxvia_user_info(html)
            if u_info and u_info.get('balance_usd'):
                CURRENT_MAXVIA_USER_INFO.update(u_info)
        prods = parse_products_from_html(html)
        for p_id, item in prods.items():
            item['site'] = 'maxvia88'
            if url != "https://maxvia88.com/":
                item['url'] = url
            elif 'url' not in item:
                item['url'] = "https://maxvia88.com/"

            if p_id not in all_products:
                all_products[p_id] = item
            else:
                if url != "https://maxvia88.com/":
                    all_products[p_id]['url'] = url
                if item['stock'] > all_products[p_id]['stock']:
                    all_products[p_id]['stock'] = item['stock']
                    all_products[p_id]['price'] = item['price']

    return all_products


def fetch_thefbstores_products() -> dict:
    """Fetch products from TheFBStores.com via Base44 API."""
    url = "https://base44.app/api/apps/6ab5c66253ae39f6f40f80f7/entities/Product"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    products = {}
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for p in data:
                slug = p.get('slug', '')
                if not slug:
                    continue
                p_id = f"thefbstores_{slug}"
                name = p.get('name', '')
                price = p.get('price', 0)
                qty = p.get('supplier_quantity') if p.get('product_source') == 'maxvia88' else p.get('stock_available')
                stock = int(qty or 0)
                products[p_id] = {
                    'id': p_id,
                    'title': f"[TheFBStore] {name}",
                    'raw_title': name,
                    'site': 'thefbstores',
                    'slug': slug,
                    'stock': stock,
                    'price': f"${price:.2f}",
                    'desc': p.get('short_description', ''),
                    'url': f"https://thefbstores.com/product/{slug}"
                }
            logging.info(f"[TheFBStores] Coletados {len(products)} produtos com sucesso via Base44.")
    except Exception as e:
        logging.error(f"Erro ao buscar produtos TheFBStores: {e}")
    return products


KNOWN_BUYVIAFB_IDS = {
    '1000x brazil no2fa 30+ fr live ads': '195',
    '1000x brazil no2fa 0-30 fr live ads': '194',
    '(hot) acc old 1000x soak 9 months full 2fa 1 hotmail trust 30 friend': '133',
}


def _parse_buyviafb_html(html: str, page_url: str, products: dict):
    """Parse BuyViaFB cards and buttons, including Sold Out items with 0 stock."""
    soup = BeautifulSoup(html, 'html.parser')

    # 1. Parse structured product cards (handles both in-stock and Sold Out items)
    for card in soup.find_all('div', class_='card'):
        h1 = card.find('h1')
        if not h1:
            continue
        raw_title = h1.get_text(strip=True)
        if not raw_title or len(raw_title) < 3:
            continue

        btn = card.find('button')
        btn_onclick = btn.get('onclick', '') if btn else ''
        btn_text = btn.get_text(strip=True) if btn else ''

        prod_id = None
        stock_val = 0
        price_val = 0

        # Tenta obter dados do onclick showPromptMessage
        m = re.search(r"showPromptMessage\(\s*'([^']+)'\s*,\s*(\d+)\s*,\s*'([^']*)'\s*,\s*'(\d+)'\s*,\s*'(\d+)'", btn_onclick)
        if m:
            t, price, infor, stock, pid = m.groups()
            prod_id = pid
            price_val = int(price)
            stock_val = int(stock)
            raw_title = t
        else:
            # Caso Sold Out ou sem onclick
            if 'sold out' in btn_text.lower():
                stock_val = 0
            stock_badge = card.find(class_='badge')
            if stock_badge:
                m_st = re.search(r'\d+', stock_badge.get_text())
                if m_st:
                    stock_val = int(m_st.group())

            price_tag = card.find('strong', class_='text-danger')
            if price_tag:
                m_pr = re.search(r'([\d,]+)', price_tag.get_text())
                if m_pr:
                    price_val = int(m_pr.group(1).replace(',', ''))

            clean_key = re.sub(r'\s+', ' ', raw_title.strip().lower())
            prod_id = KNOWN_BUYVIAFB_IDS.get(clean_key)
            if not prod_id:
                slug = re.sub(r'[^a-z0-9]+', '_', clean_key).strip('_')
                prod_id = slug

        p_id = f"buyviafb_{prod_id}"
        price_str = f"{price_val:,} Coins".replace(',', '.')
        products[p_id] = {
            'id': p_id,
            'buyviafb_id': str(prod_id),
            'title': f"[BuyViaFB] {raw_title}",
            'raw_title': raw_title,
            'price': price_str,
            'price_val': price_val,
            'stock': stock_val,
            'site': 'buyviafb',
            'url': page_url
        }

    # 2. Parse any additional buttons with showPromptMessage not captured by card div
    buttons = soup.find_all('button', onclick=re.compile(r'showPromptMessage', re.I))
    for btn in buttons:
        m = re.search(r"showPromptMessage\(\s*'([^']+)'\s*,\s*(\d+)\s*,\s*'([^']*)'\s*,\s*'(\d+)'\s*,\s*'(\d+)'", btn['onclick'])
        if m:
            title, price, infor, stock, prod_id = m.groups()
            p_id = f"buyviafb_{prod_id}"
            if p_id not in products:
                price_int = int(price)
                stock_int = int(stock)
                price_str = f"{price_int:,} Coins".replace(',', '.')
                products[p_id] = {
                    'id': p_id,
                    'buyviafb_id': prod_id,
                    'title': f"[BuyViaFB] {title}",
                    'raw_title': title,
                    'price': price_str,
                    'price_val': price_int,
                    'stock': stock_int,
                    'site': 'buyviafb',
                    'url': page_url
                }


def fetch_buyviafb_products() -> dict:
    """Fetch products from BuyViaFB.com (homepage, category 186 VIA BRAZIL, and category 176 2FA)."""
    urls_to_scrape = [
        "https://buyviafb.com/",
        "https://buyviafb.com/category/186",
        "https://buyviafb.com/category/176"
    ]
    products = {}
    for url in urls_to_scrape:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                    _parse_buyviafb_html(html, url, products)
                    break
            except Exception as e:
                if attempt == 0:
                    time.sleep(1)
                else:
                    logging.error(f"Erro ao buscar produtos BuyViaFB ({url}, tentativa 2): {e}")

    logging.info(f"[BuyViaFB] Coletados {len(products)} produtos com sucesso.")
    return products


def load_state() -> dict:
    """Load stock state from JSON file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load state file: {e}")
    return {}


def save_state(state: dict):
    """Save stock state to JSON file."""
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Failed to save state file: {e}")


def export_maxvia_web_state(all_products: dict):
    """Export current MaxVia88 user balance and live product prices to limpador_contas/maxvia_state.json."""
    try:
        priority_items = [
            ("ramdom", "Via Ramdom New (2FA)", 1.29),
            ("farm 6 month", "Acc Farm 6 Month+ (2FA)", 1.04),
            ("scan 1 year", "Acc Scan 1 Year+ (2FA)", 2.60),
            ("farmed 2026", "Acc Farmed 2026 (2FA)", 0.88),
            ("switzerland", "Via Switzerland Old (2FA)", 4.57),
            ("canada old", "Via Canada Old (2FA)", 4.57),
            ("austria old", "Via Austria Old (2FA)", 4.57),
            ("united states old 902", "Acc USA Old 902 (2FA)", 25.39),
            ("united states old", "Via United States Old (2FA)", 20.31),
        ]

        featured = []
        for kw, fallback_name, fallback_price in priority_items:
            found = None
            for p_id, item in all_products.items():
                if item.get('site') == 'maxvia88':
                    t = (item.get('raw_title') or item.get('title') or '').lower()
                    if kw in t:
                        if not found or (item.get('stock', 0) > found.get('stock', 0)):
                            found = item
            if found:
                p_val = parse_price_val(found.get('price')) or fallback_price
                featured.append({
                    "name": found.get('title') or fallback_name,
                    "price": p_val,
                    "price_str": f"${p_val:.2f}",
                    "stock": found.get('stock', 0),
                    "url": found.get('url', 'https://maxvia88.com/')
                })
            else:
                featured.append({
                    "name": fallback_name,
                    "price": fallback_price,
                    "price_str": f"${fallback_price:.2f}",
                    "stock": 0,
                    "url": "https://maxvia88.com/"
                })

        web_state = {
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "username": CURRENT_MAXVIA_USER_INFO.get("username", "Itooh - ID: 4271"),
            "balance_str": CURRENT_MAXVIA_USER_INFO.get("balance_str", "$32.16"),
            "balance_usd": CURRENT_MAXVIA_USER_INFO.get("balance_usd", 32.16),
            "products": featured
        }

        global LATEST_WEB_STATE
        LATEST_WEB_STATE = web_state

        paths_to_save = [
            MAXVIA_STATE_WEB_PATH,
            os.path.join(WEB_DIR, "maxvia_state.json")
        ]
        for p in paths_to_save:
            try:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, 'w', encoding='utf-8') as f:
                    json.dump(web_state, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        logging.info(f"Exported MaxVia web state (Balance: {web_state['balance_str']})")
    except Exception as e:
        logging.error(f"Failed to export MaxVia web state: {e}")


def should_notify_product(item_or_title, target_keywords: list = None, site: str = "maxvia88") -> bool:
    """
    Filtra rigorosamente os produtos monitorados:
    1. Perfis do Brasil (Via Brazil Old e Via Brazil New) - COMPRAS E REPOSIÇÕES.
    2. BMs Verificadas exclusivamente da MaxVia88.
    Todos os outros perfis/produtos (902, XMDT, Scan, 2025, TheFBStore, etc.) são 100% desativados.
    """
    if isinstance(item_or_title, dict):
        item = item_or_title
        site = item.get('site', 'maxvia88')
        title = item.get('title', '')
    else:
        title = str(item_or_title)
        item = {'title': title, 'site': site}

    # Caso BuyViaFB
    if is_buyviafb_target(item):
        return True

    if site != 'maxvia88':
        return False

    title_clean = normalize_title(title).lower()

    # Caso 0: Perfis Hot Item (Recommended) da MaxVia88 solicitados pelo usuário (7 perfis)
    if is_hot_item_target(item):
        return True

    # Caso 1: Perfis do Brasil (Prioridade Máxima solicitada pelo usuário)
    if is_brazil_profile(item):
        return True

    # Caso 2: Perfis acessíveis Farmed 2025 ($1.11) e Farmed 2026 ($0.88)
    if is_budget_farmed_profile(item):
        return True

    # Caso 3: Os 3 perfis prioritários da Categoria 219 (Ramdom New, Scan 1 Year+, Farm 6 Month+)
    if get_cat219_info(item):
        return True

    # Caso 4: BM3 Verificada US solicitada pelo usuário (alerta de reposição)
    is_bm = "bm" in title_clean or "business manager" in title_clean
    if is_bm:
        is_bm3_us = ("bm3" in title_clean or ("bm" in title_clean and "3" in title_clean)) and any(term in title_clean for term in ["verified", "verificada", "verificado", "verif"]) and bool(re.search(r'\b(us|usa|eua)\b', title_clean))
        if is_bm3_us:
            return True
        return False

    return False


def get_rule_for_product(item_title: str, product_rules: dict) -> dict:
    """Retrieve custom monitoring rule for a product title if configured."""
    if not product_rules:
        return {}
    title_clean = normalize_title(item_title).lower()
    for kw, rule in sorted(product_rules.items(), key=lambda x: len(x[0]), reverse=True):
        kw_clean = normalize_title(kw).lower()
        if kw_clean and kw_clean in title_clean:
            return rule
    return {}


def compare_and_notify(old_state: dict, new_state: dict, bot_token: str, chat_id: str, is_first_run: bool = False, product_rules: dict = None):
    """Compare stock states and dispatch Telegram notifications based on custom thresholds, drop steps, and restock rules."""
    if is_first_run:
        logging.info("Estoque inicial (baseline) registrado. Alertas serão enviados no Telegram APENAS quando houver compras ou reposições.")
        for p_id, item in new_state.items():
            item['last_notified_stock'] = item['stock']
        return

    changes = []
    product_rules = product_rules or {}

    old_by_title = {
        (normalize_title(v.get('title', '')).lower(), v.get('site', 'maxvia88')): v
        for v in old_state.values()
    }

    for p_id, item in new_state.items():
        title_clean = normalize_title(item['title']).lower()
        site_source = item.get('site', 'maxvia88')
        old_item = old_state.get(p_id) or old_by_title.get((title_clean, site_source))

        rule = get_rule_for_product(item['title'], product_rules)
        threshold = rule.get("min_stock_alert_threshold")
        notify_restock = rule.get("notify_restock", True)
        drop_step_alert = rule.get("drop_step_alert")

        is_highlight = rule.get("is_highlight", False)
        is_bm = "bm" in title_clean or "business manager" in title_clean

        url = item.get('url', '')
        is_new_supplier = (site_source == 'thefbstores')
        is_buyviafb = (site_source == 'buyviafb')

        if is_buyviafb:
            tag_header = "[BUYVIAFB]"
        elif is_new_supplier:
            tag_header = "[THE FB STORE]"
        else:
            tag_header = "[MAXVIA88]"

        display_title = item.get('raw_title') or item['title']
        clean_display_title = display_title.replace('⭐', '').replace('✅', '').strip()

        if old_item:
            old_p_val = old_item.get('price_val') or parse_price_val(old_item.get('price', ''))
            new_p_val = item.get('price_val') or parse_price_val(item.get('price', ''))

            # Checagem de Alteração de Preço para BuyViaFB
            if is_buyviafb and old_p_val > 0 and new_p_val > 0 and old_p_val != new_p_val:
                p_diff = new_p_val - old_p_val
                old_p_str = f"{int(old_p_val):,} Coins".replace(',', '.')
                new_p_str = f"{int(new_p_val):,} Coins".replace(',', '.')
                diff_str = f"{abs(int(p_diff)):,} Coins".replace(',', '.')
                if new_p_val > old_p_val:
                    changes.append(
                        f"📈🚨 <b>[BUYVIAFB] AUMENTO DE PREÇO DETECTADO!</b> 🚨📈\n"
                        f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                        f"💵 <b>Preço Anterior:</b> {old_p_str}\n"
                        f"💰 <b>Novo Preço:</b> <b>{new_p_str}</b> (+{diff_str})"
                    )
                else:
                    changes.append(
                        f"📉🏷️ <b>[BUYVIAFB] REDUÇÃO DE PREÇO!</b> 🏷️📉\n"
                        f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                        f"💵 <b>Preço Anterior:</b> {old_p_str}\n"
                        f"💰 <b>Novo Preço:</b> <b>{new_p_str}</b> (-{diff_str})"
                    )

            # Checagem de Alteração de Preço para os 3 perfis prioritários da Categoria 219
            cat219 = get_cat219_info(item)
            if cat219 and old_p_val > 0 and new_p_val > 0 and abs(new_p_val - old_p_val) >= 0.01:
                p_diff = new_p_val - old_p_val
                b = cat219['badge']
                name = cat219['clean_name']
                diff_str = f"+${p_diff:.2f}" if p_diff > 0 else f"-${abs(p_diff):.2f}"
                if new_p_val > old_p_val:
                    changes.append(
                        f"📈🚨 <b>[MAXVIA88] AUMENTO DE PREÇO!</b> 🚨📈\n"
                        f"{b} <b>{name}</b>\n"
                        f"💵 <b>Preço Anterior:</b> ${old_p_val:.2f}\n"
                        f"💰 <b>Novo Preço:</b> <b>${new_p_val:.2f}</b> ({diff_str})"
                    )
                else:
                    changes.append(
                        f"📉🏷️ <b>[MAXVIA88] REDUÇÃO DE PREÇO!</b> 🏷️📉\n"
                        f"{b} <b>{name}</b>\n"
                        f"💵 <b>Preço Anterior:</b> ${old_p_val:.2f}\n"
                        f"💰 <b>Novo Preço:</b> <b>${new_p_val:.2f}</b> ({diff_str})"
                    )

            # Checagem de Alteração de Preço (Aumento ou Redução) - perfil monitorado 0.84 da MaxVia88
            elif is_primary_084_profile(item) and old_p_val > 0 and new_p_val > 0 and abs(new_p_val - old_p_val) >= 0.01:
                p_diff = new_p_val - old_p_val
                if new_p_val > old_p_val:
                    changes.append(
                        f"📈🚨 <b>{tag_header} AUMENTO DE PREÇO DETECTADO!</b> 🚨📈\n"
                        f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                        f"💵 <b>Preço Anterior:</b> ${old_p_val:.2f}\n"
                        f"💰 <b>Novo Preço:</b> <b>${new_p_val:.2f}</b> (+${p_diff:.2f})"
                    )
                else:
                    changes.append(
                        f"📉🏷️ <b>{tag_header} REDUÇÃO DE PREÇO!</b> 🏷️📉\n"
                        f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                        f"💵 <b>Preço Anterior:</b> ${old_p_val:.2f}\n"
                        f"💰 <b>Novo Preço:</b> <b>${new_p_val:.2f}</b> (-${abs(p_diff):.2f})"
                    )

            old_stock = old_item['stock']
            new_stock = item['stock']
            baseline_stock = old_item.get('last_notified_stock', old_stock)

            if new_stock < old_stock:
                # Caso BuyViaFB: Alerta compras apenas se o estoque estiver abaixo de 5.000 (ou se esgotar), ou em lotes configurados (ex: 10 em 10)
                if is_buyviafb:
                    # 1. Se o produto esgotou (bateu 0), notifica
                    if new_stock == 0:
                        if old_stock > 30 and not old_item.get('zero_confirmed'):
                            item['zero_confirmed'] = True
                            item['last_notified_stock'] = baseline_stock
                            logging.info(f"[BUYVIAFB ANTI-GLITCH] Estoque de '{clean_display_title}' caiu de {old_stock} para 0 abruptamente. Aguardando 1 ciclo de confirmação para evitar falso alarme.")
                            continue

                        diff = baseline_stock if baseline_stock > 0 else (old_stock - new_stock)
                        item['last_notified_stock'] = 0
                        changes.append(
                            f"🔥🔴 <b>[BUYVIAFB] PRODUTO ESGOTOU!</b> 🔴🔥\n"
                            f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📉 <b>Estoque:</b> {baseline_stock} ➔ <b>0 unidades</b> (-{diff})"
                        )
                        continue

                    # 2. Regra de lote de compras (ex: de 10 em 10 solicitado pelo usuário)
                    drop_step = rule.get("drop_step_alert")
                    if not drop_step and 'brazil' in clean_display_title.lower():
                        drop_step = 10

                    if drop_step:
                        accumulated_drop = baseline_stock - new_stock
                        if accumulated_drop < drop_step:
                            logging.info(f"[BUYVIAFB] Queda parcial para '{clean_display_title}': {baseline_stock} -> {new_stock} (-{accumulated_drop}). Aguardando lote de {drop_step} para notificar.")
                            item['last_notified_stock'] = baseline_stock
                            continue

                        # Atingiu o lote de compras (ex: 10)
                        diff = accumulated_drop
                        from_stock = baseline_stock
                        item['last_notified_stock'] = new_stock
                        from_stock_str = f"{from_stock:,}".replace(',', '.')
                        new_stock_str = f"{new_stock:,}".replace(',', '.')
                        diff_str = f"{diff:,}".replace(',', '.')
                        changes.append(
                            f"🛒⚡ <b>[BUYVIAFB] COMPRA DETECTADA! (-{diff_str})</b> ⚡🛒\n"
                            f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📉 <b>Estoque:</b> {from_stock_str} ➔ <b>{new_stock_str} unidades restantes</b> (-{diff_str})"
                        )
                        continue

                    # 3. Compras normais em produtos BuyViaFB sem lote específico:
                    if new_stock <= 5000:
                        diff = old_stock - new_stock
                        item['last_notified_stock'] = new_stock
                        old_stock_str = f"{old_stock:,}".replace(',', '.')
                        new_stock_str = f"{new_stock:,}".replace(',', '.')
                        diff_str = f"{diff:,}".replace(',', '.')
                        if old_stock > 5000:
                            changes.append(
                                f"⚠️📉 <b>[BUYVIAFB] ESTOQUE ENTROU ABAIXO DE 5.000! (-{diff_str})</b> 📉⚠️\n"
                                f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                                f"💵 <b>Preço:</b> {item['price']}\n"
                                f"📉 <b>Estoque:</b> {old_stock_str} ➔ <b>{new_stock_str} unidades restantes</b> (-{diff_str})"
                            )
                        else:
                            changes.append(
                                f"🛒⚡ <b>[BUYVIAFB] COMPRA DETECTADA! (-{diff_str})</b> ⚡🛒\n"
                                f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                                f"💵 <b>Preço:</b> {item['price']}\n"
                                f"📉 <b>Estoque:</b> {old_stock_str} ➔ <b>{new_stock_str} unidades restantes</b> (-{diff_str})"
                            )
                    else:
                        diff = old_stock - new_stock
                        item['last_notified_stock'] = new_stock
                        logging.info(f"[BUYVIAFB] Compra em '{clean_display_title}' ({old_stock} -> {new_stock}, -{diff}) ignorada (estoque > 5.000).")
                    continue

                # Caso 1: BMs verificadas (alertar a cada compra e quando zerar)
                if is_bm:
                    diff = old_stock - new_stock
                    item['last_notified_stock'] = new_stock
                    if new_stock == 0:
                        changes.append(
                            f"💼🔴 <b>[MAXVIA88 - BM VERIFICADA ESGOTOU!]</b>\n"
                            f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📉 <b>Estoque:</b> {old_stock} ➔ <b>0 unidades</b> (-{diff})"
                        )
                    else:
                        changes.append(
                            f"💼🛒 <b>[MAXVIA88 - BM VERIFICADA COMPRADA!] (-{diff})</b>\n"
                            f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📉 <b>Estoque:</b> {old_stock} ➔ <b>{new_stock} unidades restantes</b> (-{diff})"
                        )
                    continue

                # Caso 2: Perfis do Brasil (NOVA REGRA: Compras SOMENTE do Brasil!)
                if is_brazil_profile(item):
                    drop_step_alert = rule.get("drop_step_alert") or 5  # Notifica a cada 5 compras ou se zerar

                    if new_stock == 0:
                        if old_stock > 30 and not old_item.get('zero_confirmed'):
                            item['zero_confirmed'] = True
                            item['last_notified_stock'] = baseline_stock
                            logging.info(f"[MAXVIA88 ANTI-GLITCH] Estoque de Brasil '{clean_display_title}' caiu de {old_stock} para 0 abruptamente. Aguardando 1 ciclo de confirmação para evitar falso alarme.")
                            continue

                        diff = baseline_stock if baseline_stock > 0 else (old_stock - new_stock)
                        item['last_notified_stock'] = 0
                        changes.append(
                            f"🔥🔴 <b>[MAXVIA88] PERFIL DO BRASIL ESGOTOU!</b> 🔴🔥\n"
                            f"📦 <b>Produto:</b> 🇧🇷 <b>{clean_display_title}</b> ({item['price']}) 🇧🇷\n"
                            f"📉 <b>Estoque:</b> {baseline_stock} ➔ <b>0 unidades</b> (-{diff})"
                        )
                    else:
                        accumulated_drop = baseline_stock - new_stock
                        if accumulated_drop < drop_step_alert:
                            logging.info(f"Queda parcial de estoque Brasil para '{item['title']}': {baseline_stock} -> {new_stock} (-{accumulated_drop}). Aguardando lote de {drop_step_alert} para notificar.")
                            item['last_notified_stock'] = baseline_stock
                            continue

                        # Bateu o lote de compras do Brasil!
                        diff = accumulated_drop
                        from_stock = baseline_stock
                        item['last_notified_stock'] = new_stock
                        changes.append(
                            f"🛒🇧🇷 <b>[MAXVIA88] COMPRA DETECTADA NO BRASIL! (-{diff})</b> 🇧🇷🛒\n"
                            f"📦 <b>Produto:</b> 🇧🇷 <b>{clean_display_title}</b> ({item['price']}) 🇧🇷\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📉 <b>Estoque:</b> {from_stock} ➔ <b>{new_stock} unidades restantes</b> (-{diff})"
                        )
                    continue

                # Caso Categoria 219 (Ramdom New, Scan 1 Year+, Farm 6 Month+)
                cat219 = get_cat219_info(item)
                if cat219:
                    b = cat219['badge']
                    name = cat219['clean_name']
                    p_str = f"${parse_price_val(item['price']):.2f}"

                    # Se esgotar completamente, sempre avisa com urgência máxima!
                    if new_stock == 0:
                        if old_stock > 30 and not old_item.get('zero_confirmed'):
                            item['zero_confirmed'] = True
                            item['last_notified_stock'] = baseline_stock
                            logging.info(f"[MAXVIA88 ANTI-GLITCH] Estoque de '{name}' caiu de {old_stock} para 0 abruptamente. Aguardando 1 ciclo de confirmação para evitar falso alarme.")
                            continue

                        diff = baseline_stock if baseline_stock > 0 else (old_stock - new_stock)
                        item['last_notified_stock'] = 0
                        changes.append(
                            f"🔥🔴 <b>[MAXVIA88] PRODUTO ESGOTOU!</b> 🔴🔥\n"
                            f"{b} <b>{name}</b> <code>[{p_str}]</code>\n"
                            f"📉 <b>Estoque:</b> {baseline_stock} ➔ <b>0 unidades</b> (-{diff})"
                        )
                        continue

                    # 1. Via Ramdom New (2FA): Avisar APENAS quando estiver abaixo de 4.000 unidades
                    if cat219['key'] == 'ramdom':
                        diff = old_stock - new_stock
                        item['last_notified_stock'] = new_stock
                        if new_stock >= 4000:
                            logging.info(f"[MAXVIA88] Compra para '{name}' ({old_stock} -> {new_stock}, -{diff}) ignorada (estoque >= 4.000. Notificação silenciada até 3.999).")
                            continue

                        # Estoque está abaixo de 4.000!
                        old_stock_str = f"{old_stock:,}".replace(',', '.')
                        new_stock_str = f"{new_stock:,}".replace(',', '.')
                        diff_str = f"{diff:,}".replace(',', '.')
                        if old_stock >= 4000 and new_stock < 4000:
                            changes.append(
                                f"⚠️📉 <b>[MAXVIA88] ESTOQUE ENTROU ABAIXO DE 4.000! (-{diff_str})</b> 📉⚠️\n"
                                f"{b} <b>{name}</b> <code>[{p_str}]</code>\n"
                                f"📉 <b>Estoque:</b> {old_stock_str} ➔ <b>{new_stock_str} unidades restantes</b> (-{diff_str})"
                            )
                        else:
                            changes.append(
                                f"🛒⚡ <b>[MAXVIA88] COMPRA DETECTADA! (-{diff_str})</b> ⚡🛒\n"
                                f"{b} <b>{name}</b> <code>[{p_str}]</code>\n"
                                f"📉 <b>Estoque:</b> {old_stock_str} ➔ <b>{new_stock_str} restantes</b> (-{diff_str})"
                            )
                        continue

                    # Acc Farm 6 Month+ (2FA) (V1 e V2): Avisar em lotes de compras (ex: 60 em 60)
                    if cat219['key'] in ['farm6m', 'farm6m_v2']:
                        drop_step = rule.get("drop_step_alert") or 60
                        accumulated_drop = baseline_stock - new_stock
                        if accumulated_drop < drop_step:
                            logging.info(f"[MAXVIA88] Queda parcial de estoque para '{name}': {baseline_stock} -> {new_stock} (-{accumulated_drop}). Aguardando lote de {drop_step} para notificar.")
                            item['last_notified_stock'] = baseline_stock
                            continue

                        # Atingiu o lote de 60 (ou mais) compras acumuladas!
                        diff = accumulated_drop
                        from_stock = baseline_stock
                        item['last_notified_stock'] = new_stock
                        from_stock_str = f"{from_stock:,}".replace(',', '.')
                        new_stock_str = f"{new_stock:,}".replace(',', '.')
                        diff_str = f"{diff:,}".replace(',', '.')
                        changes.append(
                            f"🛒⚡ <b>[MAXVIA88] COMPRA DETECTADA! (-{diff_str})</b> ⚡🛒\n"
                            f"{b} <b>{name}</b> <code>[{p_str}]</code>\n"
                            f"📉 <b>Estoque:</b> {from_stock_str} ➔ <b>{new_stock_str} restantes</b> (-{diff_str})"
                        )
                        continue

                    # Demais perfis da Cat 219: Notificação padrão a cada compra
                    diff = old_stock - new_stock
                    item['last_notified_stock'] = new_stock
                    old_stock_str = f"{old_stock:,}".replace(',', '.')
                    new_stock_str = f"{new_stock:,}".replace(',', '.')
                    diff_str = f"{diff:,}".replace(',', '.')
                    changes.append(
                        f"🛒⚡ <b>[MAXVIA88] COMPRA DETECTADA! (-{diff_str})</b> ⚡🛒\n"
                        f"{b} <b>{name}</b> <code>[{p_str}]</code>\n"
                        f"📉 <b>Estoque:</b> {old_stock_str} ➔ <b>{new_stock_str} restantes</b> (-{diff_str})"
                    )
                    continue

                # REGRA CRÍTICA DO USUÁRIO: Apenas perfis do Brasil e BuyViaFB notificam compras de 1 em 1!
                logging.info(f"Queda/compra de estoque para '{item['title']}' ({old_stock} -> {new_stock}) IGNORADA. (Apenas reposição/preço/esgotamento).")
                item['last_notified_stock'] = new_stock
                continue

            elif new_stock > old_stock:
                item['last_notified_stock'] = new_stock

                if not notify_restock:
                    continue

                diff = new_stock - old_stock
                if is_buyviafb:
                    if old_stock == 0:
                        changes.append(
                            f"🎉🚨 <b>[BUYVIAFB] REPOSIÇÃO NO AR! (+{diff})</b> 🚨🎉\n"
                            f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📈 <b>Estoque:</b> 0 ➔ <b>{new_stock} unidades disponíveis!</b> (+{diff})"
                        )
                    else:
                        changes.append(
                            f"🟢⚡ <b>[BUYVIAFB] REABASTECIMENTO! (+{diff})</b> ⚡🟢\n"
                            f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📈 <b>Estoque:</b> {old_stock} ➔ <b>{new_stock} unidades</b> (+{diff})"
                        )
                    continue
                hot_info = get_hot_item_info(item)
                if hot_info:
                    p_name = hot_info['name']
                    p_price = item.get('price') or hot_info['price']
                    p_icon = hot_info['icon']
                    p_url = item.get('url') or 'https://maxvia88.com/categories/1'
                    if old_stock == 0:
                        changes.append(
                            f"🔥🚨 <b>[MAXVIA88 - ENTROU EM ESTOQUE!]</b> 🚨🔥\n"
                            f"{p_icon} <b>Perfil:</b> <b>{p_name}</b>\n"
                            f"💵 <b>Preço:</b> <b>{p_price}</b>\n"
                            f"📈 <b>Estoque:</b> 0 ➔ <b>{new_stock} unidades disponíveis!</b> (+{diff})\n"
                            f"🔗 <b>Comprar agora:</b> {p_url}"
                        )
                    else:
                        changes.append(
                            f"🎉🟢 <b>[MAXVIA88 - REABASTECIDO!]</b> 🟢🎉\n"
                            f"{p_icon} <b>Perfil:</b> <b>{p_name}</b>\n"
                            f"💵 <b>Preço:</b> <b>{p_price}</b>\n"
                            f"📈 <b>Estoque:</b> {old_stock} ➔ <b>{new_stock} unidades disponíveis!</b> (+{diff})\n"
                            f"🔗 <b>Comprar agora:</b> {p_url}"
                        )
                    continue

                cat219 = get_cat219_info(item)
                if cat219:
                    b = cat219['badge']
                    name = cat219['clean_name']
                    p_str = f"${parse_price_val(item['price']):.2f}"
                    p_url = item.get('url') or 'https://maxvia88.com/categories/219'
                    if old_stock == 0:
                        changes.append(
                            f"🎉🚨 <b>[MAXVIA88] REPOSIÇÃO NO AR! (+{diff})</b> 🚨🎉\n"
                            f"{b} <b>{name}</b> <code>[{p_str}]</code>\n"
                            f"📈 <b>Estoque:</b> 0 ➔ <b>{new_stock} unidades disponíveis!</b> (+{diff})\n"
                            f"🔗 <b>Comprar agora:</b> {p_url}"
                        )
                    else:
                        changes.append(
                            f"🎉🟢 <b>[MAXVIA88] REABASTECIDO (+{diff})!</b> 🟢🎉\n"
                            f"{b} <b>{name}</b> <code>[{p_str}]</code>\n"
                            f"📈 <b>Estoque:</b> {old_stock} ➔ <b>{new_stock} unidades disponíveis!</b> (+{diff})\n"
                            f"🔗 <b>Comprar agora:</b> {p_url}"
                        )
                    continue
                elif is_brazil_profile(item):
                    if old_stock == 0:
                        changes.append(
                            f"🎉🚨 <b>[MAXVIA88] REPOSIÇÃO DO BRASIL NO AR! (+{diff})</b> 🚨🎉\n"
                            f"📦 <b>Produto:</b> 🇧🇷 <b>{clean_display_title}</b> 🇧🇷\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📈 <b>Estoque:</b> 0 ➔ <b>{new_stock} unidades disponíveis!</b> (+{diff})"
                        )
                    else:
                        changes.append(
                            f"🟢🇧🇷 <b>[MAXVIA88] REABASTECIMENTO DO BRASIL! (+{diff})</b> 🇧🇷🟢\n"
                            f"📦 <b>Produto:</b> 🇧🇷 <b>{clean_display_title}</b> 🇧🇷\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📈 <b>Estoque:</b> {old_stock} ➔ <b>{new_stock} unidades</b> (+{diff})"
                        )
                elif is_budget_farmed_profile(item):
                    changes.append(
                        f"🎉⚡ <b>[MAXVIA88] REABASTECIDO! (+{diff})</b> ⚡🎉\n"
                        f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                        f"💵 <b>Preço:</b> {item['price']}\n"
                        f"📈 <b>Estoque:</b> {old_stock} ➔ <b>{new_stock} unidades disponíveis!</b> (+{diff})"
                    )
                elif is_new_supplier:
                    changes.append(
                        f"🟢🔥 <b>{tag_header} REABASTECIMENTO! (+{diff})</b> 🔥🟢\n"
                        f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                        f"💵 <b>Preço:</b> {item['price']}\n"
                        f"📈 <b>Estoque:</b> {old_stock} ➔ <b>{new_stock} unidades</b> (+{diff})"
                    )
                elif is_bm:
                    p_url = item.get('url') or 'https://maxvia88.com/categories/118'
                    if old_stock == 0:
                        changes.append(
                            f"💼🚨 <b>[MAXVIA88 - BM VERIFICADA EM ESTOQUE!]</b> 🚨💼\n"
                            f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📈 <b>Estoque:</b> 0 ➔ <b>{new_stock} unidades disponíveis!</b> (+{diff})\n"
                            f"🔗 <b>Comprar agora:</b> {p_url}"
                        )
                    else:
                        changes.append(
                            f"💼🎉 <b>[MAXVIA88 - BM VERIFICADA REABASTECIDA!] (+{diff})</b>\n"
                            f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📈 <b>Estoque:</b> {old_stock} ➔ <b>{new_stock} unidades disponíveis!</b> (+{diff})\n"
                            f"🔗 <b>Comprar agora:</b> {p_url}"
                        )
                elif old_stock == 0:
                    changes.append(
                        f"🎉 <b>{tag_header} REPOSIÇÃO DE ESTOQUE (+{diff})!</b>\n"
                        f"📦 <b>Produto:</b> {clean_display_title}\n"
                        f"💵 <b>Preço:</b> {item['price']}\n"
                        f"📈 <b>Estoque:</b> 0 ➔ <b>{new_stock} unidades</b>"
                    )
                else:
                    changes.append(
                        f"🟢 <b>{tag_header} REABASTECIDO (+{diff})!</b>\n"
                        f"📦 <b>Produto:</b> {clean_display_title}\n"
                        f"💵 <b>Preço:</b> {item['price']}\n"
                        f"📈 <b>Estoque:</b> {old_stock} ➔ <b>{new_stock} unidades</b>"
                    )
            else:
                # new_stock == old_stock
                item['last_notified_stock'] = baseline_stock
        else:
            # Produto novo adicionado ou recém-surgido no monitor com estoque
            new_stock = item['stock']
            item['last_notified_stock'] = new_stock
            if is_buyviafb:
                logging.info(f"[BuyViaFB] Produto '{item['title']}' registrado com estoque baseline {new_stock}.")
                continue
            if new_stock > 0 and notify_restock:
                hot_info = get_hot_item_info(item)
                if hot_info:
                    p_name = hot_info['name']
                    p_price = item.get('price') or hot_info['price']
                    p_icon = hot_info['icon']
                    p_url = item.get('url') or 'https://maxvia88.com/categories/1'
                    changes.append(
                        f"🔥🚨 <b>[MAXVIA88 - ENTROU EM ESTOQUE!]</b> 🚨🔥\n"
                        f"{p_icon} <b>Perfil:</b> <b>{p_name}</b>\n"
                        f"💵 <b>Preço:</b> <b>{p_price}</b>\n"
                        f"📈 <b>Estoque Disponível:</b> <b>{new_stock} unidades!</b>\n"
                        f"🔗 <b>Comprar agora:</b> {p_url}"
                    )
                cat219 = get_cat219_info(item)
                if cat219:
                    b = cat219['badge']
                    name = cat219['clean_name']
                    p_str = f"${parse_price_val(item['price']):.2f}"
                    p_url = item.get('url') or 'https://maxvia88.com/categories/219'
                    changes.append(
                        f"🎉🚨 <b>[MAXVIA88 - NOVO PRODUTO EM ESTOQUE!]</b> 🚨🎉\n"
                        f"{b} <b>{name}</b> <code>[{p_str}]</code>\n"
                        f"📈 <b>Estoque Disponível:</b> <b>{new_stock} unidades!</b>\n"
                        f"🔗 <b>Comprar agora:</b> {p_url}"
                    )
                elif is_bm:
                    p_url = item.get('url') or 'https://maxvia88.com/categories/118'
                    changes.append(
                        f"💼🚨 <b>[MAXVIA88 - BM VERIFICADA EM ESTOQUE!]</b> 🚨💼\n"
                        f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                        f"💵 <b>Preço:</b> {item['price']}\n"
                        f"📈 <b>Estoque Disponível:</b> <b>{new_stock} unidades!</b>\n"
                        f"🔗 <b>Comprar agora:</b> {p_url}"
                    )
                else:
                    changes.append(
                        f"🎉🆕 <b>{tag_header} NOVO PRODUTO COM ESTOQUE!</b>\n"
                        f"📦 <b>Produto:</b> <b>{clean_display_title}</b>\n"
                        f"💵 <b>Preço:</b> {item['price']}\n"
                        f"📈 <b>Estoque Disponível:</b> <b>{new_stock} unidades</b>"
                    )

    # Checagem de itens monitorados em old_state que desapareceram completamente de new_state
    for old_id, old_item in old_state.items():
        if old_id not in new_state:
            old_title_clean = normalize_title(old_item.get('title', '')).lower()
            old_site = old_item.get('site', 'maxvia88')
            found = any(
                normalize_title(it.get('title', '')).lower() == old_title_clean and it.get('site', 'maxvia88') == old_site
                for it in new_state.values()
            )
            if not found and old_item.get('stock', 0) > 0:
                missing_cycles = old_item.get('missing_cycles', 0) + 1
                if missing_cycles < 2:
                    logging.info(f"[ANTI-GLITCH] Item '{old_item.get('title')}' não veio na resposta desta rodada. Mantendo em cache e aguardando confirmação no próximo ciclo para evitar falso alarme.")
                    old_item['missing_cycles'] = missing_cycles
                    new_state[old_id] = old_item
                    continue

                clean_title = (old_item.get('raw_title') or old_item.get('title', '')).replace('⭐', '').replace('✅', '').strip()
                old_st = old_item.get('stock', 0)
                changes.append(
                    f"🔥🔴 <b>[{old_site.upper()}] PRODUTO ESGOTOU / SAIU DO AR!</b> 🔴🔥\n"
                    f"📦 <b>Produto:</b> <b>{clean_title}</b>\n"
                    f"💵 <b>Preço:</b> {old_item.get('price', '')}\n"
                    f"📉 <b>Estoque:</b> {old_st} ➔ <b>0 unidades</b> (-{old_st})"
                )

    if changes:
        # Trava permanente de duplicidade: apenas a nuvem (Render) ou flag explícita podem enviar alertas
        is_allowed_to_notify = IS_CLOUD_SERVER or ("--enable-local-telegram" in sys.argv)
        if not is_allowed_to_notify or "--no-telegram" in sys.argv or os.environ.get("NO_TELEGRAM") == "1":
            logging.info(f"[LOCAL SYNC] {len(changes)} alterações detectadas, mas alertas no Telegram são exclusivos da nuvem (Render 24/7).")
        else:
            logging.info(f"Detectadas {len(changes)} alterações de estoque. Enviando alerta Telegram...")
            send_telegram_message(bot_token, chat_id, "\n\n".join(changes))
    else:
        logging.info("Nenhuma alteração de estoque nesta rodada. Nenhuma notificação enviada.")


def check_server_billing_reminder(config: dict, bot_token: str, chat_id: str, force_test: bool = False) -> bool:
    """
    Check if the cloud server (Render) billing renewal is approaching (e.g. 1 day before or on the day),
    and send an informative notification to Telegram.
    """
    billing_cfg = config.get("server_billing", {})
    if not billing_cfg.get("enabled", True) and not force_test:
        return False

    is_allowed_to_notify = IS_CLOUD_SERVER or ("--enable-local-telegram" in sys.argv) or force_test
    if not is_allowed_to_notify or ("--no-telegram" in sys.argv and not force_test) or (os.environ.get("NO_TELEGRAM") == "1" and not force_test):
        return False

    provider = billing_cfg.get("provider", "Render")
    amount_usd = float(billing_cfg.get("amount_usd", 7.00))
    billing_day = int(billing_cfg.get("billing_day", 10))
    days_before = int(billing_cfg.get("notify_days_before", 1))

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    state_file = os.path.join(SCRIPT_DIR, "billing_state.json")
    billing_state = {}
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                billing_state = json.load(f)
        except Exception:
            billing_state = {}

    if not force_test and billing_state.get("last_notified_date") == today_str:
        return False

    current_year = now.year
    current_month = now.month
    try:
        target_billing_date = datetime(current_year, current_month, billing_day)
    except ValueError:
        import calendar
        last_day = calendar.monthrange(current_year, current_month)[1]
        target_billing_date = datetime(current_year, current_month, min(billing_day, last_day))

    if target_billing_date.date() < now.date():
        next_month = current_month + 1 if current_month < 12 else 1
        next_year = current_year if current_month < 12 else current_year + 1
        try:
            target_billing_date = datetime(next_year, next_month, billing_day)
        except ValueError:
            import calendar
            last_day = calendar.monthrange(next_year, next_month)[1]
            target_billing_date = datetime(next_year, next_month, min(billing_day, last_day))

    diff_days = (target_billing_date.date() - now.date()).days

    # Obter cotação do dólar para conversão estimada em BRL
    dolar_brl = 5.40
    try:
        req = urllib.request.Request("https://api.binance.com/api/v3/ticker/price?symbol=USDTBRL", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as r:
            data = json.loads(r.read().decode('utf-8'))
            dolar_brl = float(data.get("price", 5.40))
    except Exception:
        pass

    approx_brl = amount_usd * dolar_brl

    msg = None
    if force_test:
        msg = (
            f"🔔 <b>[TESTE] AVISO DE FATURA DO SERVIDOR ({provider.upper()})</b>\n\n"
            f"⚠️ <b>Lembrete programado para avisar 1 dia antes da renovação!</b>\n\n"
            f"📅 <b>Dia do Vencimento:</b> Todo dia {billing_day}\n"
            f"💵 <b>Valor da Assinatura:</b> ${amount_usd:.2f} USD (~R$ {approx_brl:.2f})\n"
            f"🌐 <b>Servidor Online:</b> Monitor 24/7 & Calculadora Universal\n"
            f"🔗 <b>Link do Sistema:</b> https://maxvia-monitor.onrender.com\n\n"
            f"💡 <i>Você receberá este aviso automático no Telegram todo mês (no dia {billing_day - 1} e no dia {billing_day}) para nunca deixar o servidor offline!</i>\n\n"
            f"👉 <b>Painel de Cobrança:</b> https://dashboard.render.com/billing"
        )
    elif diff_days == days_before:
        msg = (
            f"🔔 <b>AVISO DE RENOVAÇÃO DO SERVIDOR ({provider.upper()})</b>\n\n"
            f"⚠️ <b>Amanhã (Dia {billing_day}) vence a fatura do seu servidor na nuvem!</b>\n\n"
            f"📅 <b>Vencimento:</b> Amanhã, dia {billing_day}\n"
            f"💵 <b>Valor:</b> ${amount_usd:.2f} USD (~R$ {approx_brl:.2f})\n"
            f"🌐 <b>Serviço:</b> Monitor de Estoque 24/7 & Calculadora\n"
            f"🔗 <b>Link do Servidor:</b> https://maxvia-monitor.onrender.com\n\n"
            f"💡 <i>Lembrete com 1 dia de antecedência para você conferir o saldo/limite do seu cartão ou pagar no painel, garantindo que o bot do Telegram e a calculadora continuem 100% online sem interrupção!</i>\n\n"
            f"👉 <b>Painel Render:</b> https://dashboard.render.com/billing"
        )
    elif diff_days == 0:
        msg = (
            f"🚨 <b>HOJE É O DIA DE PAGAR O SERVIDOR ({provider.upper()})!</b>\n\n"
            f"⚠️ <b>A fatura do seu servidor vence HOJE (Dia {billing_day})!</b>\n\n"
            f"💵 <b>Valor:</b> ${amount_usd:.2f} USD (~R$ {approx_brl:.2f})\n"
            f"🌐 <b>Serviço:</b> Monitor 24/7 & Calculadora Universal\n"
            f"🔗 <b>Link do Servidor:</b> https://maxvia-monitor.onrender.com\n\n"
            f"👉 <b>Acessar Fatura e Pagar:</b> https://dashboard.render.com/billing"
        )

    if msg:
        logging.info(f"Enviando lembrete de pagamento do servidor {provider} (diff_days={diff_days})...")
        if send_telegram_message(bot_token, chat_id, msg):
            if not force_test:
                billing_state["last_notified_date"] = today_str
                billing_state["last_diff_days"] = diff_days
                try:
                    with open(state_file, "w", encoding="utf-8") as f:
                        json.dump(billing_state, f, indent=2)
                except Exception as e:
                    logging.warning(f"Could not save billing_state: {e}")
            return True

    return False


def run_cycle(is_startup: bool = False):
    """Run a single check cycle."""
    config = load_config()
    bot_token = config.get("telegram_bot_token") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = config.get("telegram_chat_id") or os.environ.get("TELEGRAM_CHAT_ID", "")
    product_rules = config.get("product_rules", {})

    # 1. Verifica lembrete de pagamento da fatura do servidor na nuvem (Render)
    try:
        check_server_billing_reminder(config, bot_token, chat_id)
    except Exception as e:
        logging.warning(f"Erro ao verificar lembrete de fatura do servidor: {e}")

    logging.info("Iniciando verificação de estoque MaxVia88...")
    # 0. Atualiza o saldo MaxVia88 imediatamente no início do ciclo
    try:
        refresh_maxvia_balance(force=True)
    except Exception as e:
        logging.debug(f"Erro no fast balance sync no início do ciclo: {e}")

    all_products = fetch_all_products()

    # Also fetch external stores (TheFBStores.com via Base44 API)
    thefb_products = fetch_thefbstores_products()
    all_products.update(thefb_products)

    # Fetch BuyViaFB products
    buyvia_products = fetch_buyviafb_products()
    all_products.update(buyvia_products)

    if not all_products:
        logging.warning("Nenhum produto retornado na varredura.")
        return

    old_state = load_state()
    is_first_run = (len(old_state) == 0) or is_startup

    # Anti-Glitch: Preserva produtos com estoque que sumiram temporariamente nesta varredura (ex: oscilação de rede/timeout)
    if not is_first_run:
        for old_id, old_item in old_state.items():
            if old_id not in all_products and old_item.get('stock', 0) > 0:
                old_site = old_item.get('site', 'maxvia88')
                old_title_clean = normalize_title(old_item.get('title', '')).lower()
                already_in_new = any(
                    normalize_title(it.get('title', '')).lower() == old_title_clean and it.get('site', 'maxvia88') == old_site
                    for it in all_products.values()
                )
                if not already_in_new:
                    missing_cycles = old_item.get('missing_cycles', 0) + 1
                    if missing_cycles < 2:
                        logging.info(f"[ANTI-GLITCH] '{old_item.get('title')}' não veio nesta varredura (possível oscilação de rede). Mantendo estoque {old_item.get('stock')} por 1 ciclo de confirmação.")
                        preserved_item = dict(old_item)
                        preserved_item['missing_cycles'] = missing_cycles
                        all_products[old_id] = preserved_item

    # Ensure baseline last_notified_stock is carried over from old_state for all products
    old_by_title = {
        (normalize_title(v.get('title', '')).lower(), v.get('site', 'maxvia88')): v
        for v in old_state.values()
    }

    for p_id, item in all_products.items():
        if 'missing_cycles' not in item:
            item['missing_cycles'] = 0
        title_key = (normalize_title(item.get('title', '')).lower(), item.get('site', 'maxvia88'))
        matching_old = old_state.get(p_id) or old_by_title.get(title_key)
        if matching_old and 'last_notified_stock' in matching_old:
            item['last_notified_stock'] = matching_old['last_notified_stock']
        else:
            item['last_notified_stock'] = item['stock']

    target_keywords = config.get("target_keywords") or config.get("target_products") or []
    if isinstance(target_keywords, str):
        target_keywords = [target_keywords]

    new_notify_state = {}
    for p_id, item in all_products.items():
        if should_notify_product(item):
            new_notify_state[p_id] = item

    old_notify_state = {}
    for p_id, item in old_state.items():
        if should_notify_product(item):
            old_notify_state[p_id] = item

    logging.info(f"Filtrados {len(new_notify_state)} produtos elegíveis para notificação (Regra BM Verificada e palavras-chave ativas).")

    compare_and_notify(old_notify_state, new_notify_state, bot_token, chat_id, is_first_run=is_first_run, product_rules=product_rules)
    save_state(all_products)
    export_maxvia_web_state(all_products)
    logging.info("Ciclo concluído com sucesso.")


class WebAndHealthHandler(SimpleHTTPRequestHandler):
    """Full HTTP server for Render: serves Limpador de Contas web app, static assets, and live MaxVia state API."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS, HEAD')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        req_path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if req_path.startswith('/maxvia_state.json') or req_path.startswith('/api/state') or req_path.startswith('/api/sync_maxvia'):
            force_sync = ('sync' in query or 'refresh' in query or req_path.startswith('/api/sync_maxvia'))
            # Se for force_sync ou o saldo não tiver sido checado há mais de 4s, faz a consulta ao vivo imediata (<1.5s)
            if force_sync or (time.time() - LAST_BALANCE_REFRESH_TIME > 4):
                refresh_maxvia_balance(force=force_sync)

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            data_str = json.dumps(LATEST_WEB_STATE, ensure_ascii=False) if LATEST_WEB_STATE else "{}"
            self.wfile.write(data_str.encode('utf-8'))
            return

        if self.path == '/healthz' or self.path == '/ping':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b"OK\n")
            return

        # Serve static web app (index.html, JS, banners, etc.)
        return super().do_GET()

    def log_message(self, format, *args):
        pass  # suppress noisy HTTP access logs


def start_health_server():
    """Run web server on cloud platform (serving Limpador de Contas / Calculadora AND healthcheck/state API)."""
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(('0.0.0.0', port), WebAndHealthHandler)
        logging.info(f"Web server listening on port {port} (serving Limpador de Contas SPA & MaxVia API)...")
        server.serve_forever()
    except Exception as e:
        logging.error(f"Web server error: {e}")


def keep_alive_ping():
    """Periodically ping self public URL to keep Render free web service awake."""
    while True:
        time.sleep(600)  # Every 10 minutes
        render_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("KEEP_ALIVE_URL")
        if render_url:
            try:
                urllib.request.urlopen(render_url, timeout=10)
                logging.info(f"Keep-alive self-ping sent to {render_url}")
            except Exception as e:
                logging.debug(f"Keep-alive ping note: {e}")


def main():
    if "--test-billing-alert" in sys.argv:
        config = load_config()
        bot_token = config.get("telegram_bot_token") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = config.get("telegram_chat_id") or os.environ.get("TELEGRAM_CHAT_ID", "")
        print(f"Sending test billing notification to chat {chat_id}...")
        ok = check_server_billing_reminder(config, bot_token, chat_id, force_test=True)
        print("Success!" if ok else "Failed.")
        return

    if "--once" in sys.argv:
        run_cycle()
        return

    # Start healthcheck server if PORT is provided by cloud platform (Render/Railway)
    port_env = os.environ.get("PORT")
    if port_env:
        t_srv = threading.Thread(target=start_health_server, daemon=True)
        t_srv.start()
        t_ping = threading.Thread(target=keep_alive_ping, daemon=True)
        t_ping.start()

    config = load_config()
    interval_sec = int(config.get("check_interval_seconds") or os.environ.get("CHECK_INTERVAL", "60"))

    logging.info(f"MaxVia88 Monitor Daemon starting (Interval: {interval_sec}s)...")
    first_cycle = True
    while True:
        try:
            run_cycle(is_startup=first_cycle)
            first_cycle = False
        except Exception as e:
            logging.error(f"Error in cycle loop: {e}", exc_info=True)

        logging.info(f"Sleeping for {interval_sec} seconds before next check...")
        time.sleep(interval_sec)


if __name__ == "__main__":
    main()

