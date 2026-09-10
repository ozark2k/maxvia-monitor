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
from hashlib import pbkdf2_hmac
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from bs4 import BeautifulSoup

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("monitor.log", encoding="utf-8")
    ]
)

STATE_FILE = "stock_state.json"
CONFIG_FILE = "config.json"


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
    """Extract maxvia88 session cookies from local Google Chrome profile on macOS."""
    env_cookie = os.environ.get("MAXVIA_COOKIE")
    if env_cookie:
        return env_cookie

    try:
        cmd = ["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage"]
        password = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).strip()

        salt = b"saltysalt"
        key = pbkdf2_hmac("sha1", password, salt, 1003, 16)
        hex_key = key.hex()
        hex_iv = (b" " * 16).hex()

        paths = glob.glob(os.path.expanduser("~/Library/Application Support/Google/Chrome/*/Cookies"))
        cookies_dict = {}

        for path in paths:
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

        if cookies_dict:
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
            logging.info(f"Successfully extracted Chrome session cookies ({len(cookies_dict)} keys).")
            return cookie_str
    except Exception as e:
        logging.debug(f"Chrome cookie extraction note: {e}")

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
    """Fetch HTML content from specified URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    if cookie_header:
        headers['Cookie'] = cookie_header

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logging.debug(f"Page 404 (Not found): {url}")
        else:
            logging.warning(f"HTTP {e.code} for {url}")
        return ""
    except Exception as e:
        logging.error(f"Failed to fetch {url}: {e}")
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


def make_product_id(title: str, price: str) -> str:
    """Generate deterministic product ID."""
    clean_t = normalize_title(title).lower()
    clean_p = normalize_price(price)
    return f"{clean_t}_{clean_p}"


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
                'desc': card.get_text(separator=' ', strip=True)[:100],
                'stock': stock,
                'price': clean_p or raw_price
            }

    return products


def fetch_all_products() -> dict:
    """Fetch all products across main page and all dynamically discovered categories."""
    cookie_header = get_chrome_cookies()

    urls_to_scan = set(["https://maxvia88.com/"])

    # First fetch main page to discover category links
    main_html = fetch_page_html("https://maxvia88.com/", cookie_header)
    soup = BeautifulSoup(main_html, 'html.parser')
    for a in soup.find_all('a', href=True):
        m = re.search(r'/categories/(\d+)', a['href'])
        if m:
            urls_to_scan.add(f"https://maxvia88.com/categories/{m.group(1)}")

    # Fallback/common categories if discovery missed any
    for i in [1, 2, 3, 4, 5, 6, 16, 19, 118, 212, 217, 219, 220, 221]:
        urls_to_scan.add(f"https://maxvia88.com/categories/{i}")

    all_products = {}
    for url in urls_to_scan:
        html = fetch_page_html(url, cookie_header)
        prods = parse_products_from_html(html)
        for p_id, item in prods.items():
            if p_id not in all_products or item['stock'] > all_products[p_id]['stock']:
                all_products[p_id] = item

    return all_products


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


def should_notify_product(item_title: str, target_keywords: list = None) -> bool:
    """Check if a product title satisfies notification criteria (strict profile whitelist + BM rules)."""
    title_clean = normalize_title(item_title).lower()

    # Case 1: Product is a BM (Business Manager)
    is_bm = "bm" in title_clean or "business manager" in title_clean
    if is_bm:
        # Match if explicitly in target keywords
        if target_keywords:
            for kw in target_keywords:
                kw_clean = normalize_title(kw).lower()
                if kw_clean and ("bm" in kw_clean or "business manager" in kw_clean) and kw_clean in title_clean:
                    return True
        # Or match if it's a verified BM
        return any(term in title_clean for term in ["verified", "verificada", "verificado", "verif"])

    # Case 2: Product is a Profile (strictly check allowed target profile keywords)
    if target_keywords:
        for kw in target_keywords:
            kw_clean = normalize_title(kw).lower()
            if not kw_clean or "bm" in kw_clean or "business manager" in kw_clean:
                continue
            if kw_clean in title_clean:
                return True

    return False


def get_rule_for_product(item_title: str, product_rules: dict) -> dict:
    """Retrieve custom monitoring rule for a product title if configured."""
    if not product_rules:
        return {}
    title_clean = normalize_title(item_title).lower()
    for kw, rule in product_rules.items():
        kw_clean = normalize_title(kw).lower()
        if kw_clean and kw_clean in title_clean:
            return rule
    return {}


def compare_and_notify(old_state: dict, new_state: dict, bot_token: str, chat_id: str, is_first_run: bool = False, product_rules: dict = None):
    """Compare stock states and dispatch Telegram notifications based on custom thresholds and restock rules."""
    if is_first_run:
        logging.info("Estoque inicial (baseline) registrado. Alertas serão enviados no Telegram APENAS quando houver compras ou reposições.")
        return

    changes = []
    product_rules = product_rules or {}

    for p_id, item in new_state.items():
        if p_id in old_state:
            old_stock = old_state[p_id]['stock']
            new_stock = item['stock']

            rule = get_rule_for_product(item['title'], product_rules)
            threshold = rule.get("min_stock_alert_threshold")
            notify_restock = rule.get("notify_restock", True)

            is_highlight = rule.get("is_highlight", False)

            if new_stock < old_stock:
                diff = old_stock - new_stock

                # If a low-stock threshold is configured, ignore stock drops when new_stock is still >= threshold
                if threshold is not None and new_stock >= threshold:
                    logging.info(f"Queda de estoque para '{item['title']}' ignorada: {old_stock} -> {new_stock} (ainda acima do limite de {threshold}).")
                    continue

                if new_stock == 0:
                    if is_highlight:
                        changes.append(
                            f"🔥🔴 <b>[DESTAQUE] ESGOTOU COMPLETAMENTE!</b> 🔴🔥\n"
                            f"📦 <b>Produto:</b> ⭐ <b>{item['title']}</b> ⭐\n"
                            f"📉 <b>Estoque:</b> {old_stock} ➔ <b>0 unidades</b> (-{diff})\n"
                            f"🔔 <i>Alerta de reposição VIP ativado para este perfil!</i>"
                        )
                    else:
                        changes.append(
                            f"🔴 <b>ESGOTOU COMPLETAMENTE!</b>\n"
                            f"📦 <b>Produto:</b> {item['title']}\n"
                            f"📉 <b>Estoque:</b> {old_stock} ➔ <b>0 unidades</b> (-{diff})"
                        )
                elif threshold is not None and old_stock >= threshold and new_stock < threshold:
                    if is_highlight:
                        changes.append(
                            f"⚡⚠️ <b>[DESTAQUE VIP] ESTOQUE CRÍTICO (&lt; {threshold} perfis)!</b> ⚠️⚡\n"
                            f"📦 <b>Produto:</b> ⭐ <b>{item['title']}</b> ⭐\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📉 <b>Estoque Restante:</b> {old_stock} ➔ <b>{new_stock} unidades</b> (-{diff})"
                        )
                    else:
                        changes.append(
                            f"⚠️ <b>ALERTA DE ESTOQUE CRÍTICO (&lt; {threshold} perfis)!</b>\n"
                            f"📦 <b>Produto:</b> {item['title']}\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📉 <b>Estoque Restante:</b> {old_stock} ➔ <b>{new_stock} unidades</b> (-{diff})"
                        )
                else:
                    changes.append(
                        f"🛒 <b>COMPRA DETECTADA (-{diff})!</b>\n"
                        f"📦 <b>Produto:</b> {item['title']}\n"
                        f"💵 <b>Preço:</b> {item['price']}\n"
                        f"📉 <b>Estoque Restante:</b> {old_stock} ➔ <b>{new_stock} unidades</b>"
                    )

            elif new_stock > old_stock:
                if not notify_restock:
                    continue

                diff = new_stock - old_stock
                if old_stock == 0:
                    if is_highlight:
                        changes.append(
                            f"🔥🚨 <b>[REPOSIÇÃO VIP - DESTAQUE]</b> 🚨🔥\n"
                            f"⭐ <b>PRODUTO FAVORITO REABASTECIDO!</b> ⭐\n"
                            f"📦 <b>Produto:</b> <b>{item['title']}</b>\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📈 <b>Estoque:</b> 0 ➔ <b>{new_stock} unidades</b> (+{diff})\n"
                            f"⚡ <i>Os perfis foram reabastecidos! Garanta o seu rápido!</i>"
                        )
                    else:
                        changes.append(
                            f"🎉 <b>REPOSIÇÃO DE ESTOQUE (+{diff})!</b>\n"
                            f"📦 <b>Produto:</b> {item['title']}\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📈 <b>Estoque:</b> 0 ➔ <b>{new_stock} unidades</b>"
                        )
                else:
                    if is_highlight:
                        changes.append(
                            f"🟢🔥 <b>[REABASTECIMENTO VIP - DESTAQUE]</b> 🔥🟢\n"
                            f"📦 <b>Produto:</b> ⭐ <b>{item['title']}</b> ⭐\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📈 <b>Estoque:</b> {old_stock} ➔ <b>{new_stock} unidades</b> (+{diff})"
                        )
                    else:
                        changes.append(
                            f"🟢 <b>REABASTECIDO (+{diff})!</b>\n"
                            f"📦 <b>Produto:</b> {item['title']}\n"
                            f"💵 <b>Preço:</b> {item['price']}\n"
                            f"📈 <b>Estoque:</b> {old_stock} ➔ <b>{new_stock} unidades</b>"
                        )

    if changes:
        logging.info(f"Detectadas {len(changes)} alterações de estoque. Enviando alerta Telegram...")
        send_telegram_message(bot_token, chat_id, "\n\n".join(changes))
    else:
        logging.info("Nenhuma alteração de estoque nesta rodada. Nenhuma notificação enviada.")


def run_cycle():
    """Run a single check cycle."""
    config = load_config()
    bot_token = config.get("telegram_bot_token") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = config.get("telegram_chat_id") or os.environ.get("TELEGRAM_CHAT_ID", "")
    product_rules = config.get("product_rules", {})

    logging.info("Iniciando verificação de estoque MaxVia88...")
    all_products = fetch_all_products()

    if not all_products:
        logging.warning("Nenhum produto retornado na varredura.")
        return

    old_state = load_state()
    is_first_run = len(old_state) == 0

    target_keywords = config.get("target_keywords") or config.get("target_products") or []
    if isinstance(target_keywords, str):
        target_keywords = [target_keywords]

    new_notify_state = {}
    for p_id, item in all_products.items():
        if should_notify_product(item['title'], target_keywords):
            new_notify_state[p_id] = item

    old_notify_state = {}
    for p_id, item in old_state.items():
        if should_notify_product(item.get('title', ''), target_keywords):
            old_notify_state[p_id] = item

    logging.info(f"Filtrados {len(new_notify_state)} produtos elegíveis para notificação (Regra BM Verificada e palavras-chave ativas).")

    compare_and_notify(old_notify_state, new_notify_state, bot_token, chat_id, is_first_run=is_first_run, product_rules=product_rules)
    save_state(all_products)
    logging.info("Ciclo concluído com sucesso.")


class HealthHandler(BaseHTTPRequestHandler):
    """Simple HTTP healthcheck handler for Render Web Service."""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"MaxVia88 Monitor is Active and Monitoring 24/7!\n")

    def log_message(self, format, *args):
        pass  # suppress noisy HTTP access logs


def start_health_server():
    """Run lightweight HTTP server for Render health checks."""
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        logging.info(f"Health server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        logging.error(f"Health server error: {e}")


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
    while True:
        try:
            run_cycle()
        except Exception as e:
            logging.error(f"Error in cycle loop: {e}", exc_info=True)

        logging.info(f"Sleeping for {interval_sec} seconds before next check...")
        time.sleep(interval_sec)


if __name__ == "__main__":
    main()

