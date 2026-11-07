#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Sentinel: OKX & Binance Network Monitor
Roda 24/7 no Render (na nuvem) monitorando:
  - OKX: USDT (Polygon), POL (Polygon), USDT (TRC20), TRX (TRON)
  - Binance: BSC BNB Smart Chain (BEP20) para BNB e USDT
Dispara alertas instantâneos no Telegram se qualquer rede for suspensa ou normalizada.
"""

import os
import sys
import time
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8692174015:AAFl7TCPswrYFHoMhSbgAtb5V3F8Px1k_HA")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "11579952")

CHECK_INTERVAL_SECONDS = 180  # 3 minutos

TARGET_SYMBOLS = {
    # OKX
    "USDT-Polygon": {
        "exchange": "OKX",
        "name": "USDT (Polygon)",
        "network": "Polygon",
        "emoji": "🟣",
        "query_sym": "USDT",
        "link": "https://www.okx.com/pt-br/status"
    },
    "USDT-TRC20": {
        "exchange": "OKX",
        "name": "USDT (TRC20 / TRON)",
        "network": "TRON",
        "emoji": "🔴",
        "query_sym": "USDT",
        "link": "https://www.okx.com/pt-br/status"
    },
    "POL-Polygon": {
        "exchange": "OKX",
        "name": "POL (Polygon Nativo)",
        "network": "Polygon",
        "emoji": "🟣",
        "query_sym": "POL",
        "link": "https://www.okx.com/pt-br/status"
    },
    "TRX-TRC20": {
        "exchange": "OKX",
        "name": "TRX (TRON Nativo)",
        "network": "TRON",
        "emoji": "🔴",
        "query_sym": "TRX",
        "link": "https://www.okx.com/pt-br/status"
    },
    # BINANCE
    "BINANCE-BSC-BNB": {
        "exchange": "Binance",
        "name": "BSC BNB Smart Chain (BEP20)",
        "network": "BSC",
        "emoji": "🟡",
        "query_sym": "BNB",
        "link": "https://www.binance.com/pt-BR/network"
    },
    "BINANCE-BSC-USDT": {
        "exchange": "Binance",
        "name": "USDT (BSC / BEP20)",
        "network": "BSC",
        "emoji": "🟡",
        "query_sym": "USDT",
        "link": "https://www.binance.com/pt-BR/network"
    }
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "okx_state.json")
TZ_BR = timezone(timedelta(hours=-3))

def send_telegram(text: str) -> bool:
    """Envia mensagem formatada em HTML para o Telegram."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or TELEGRAM_BOT_TOKEN
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true"
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"}
    )
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("ok"):
                    return True
        except Exception as e:
            logging.warning(f"[Cloud OKX/Binance] Tentativa {attempt} Telegram falhou: {e}")
            time.sleep(2)
    return False

def fetch_okx_symbol_status(symbol_query: str) -> dict:
    url = f"https://www.okx.com/v2/asset/currency/status?symbol={symbol_query}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = {}
            for item in data.get("data", []):
                for sub in item.get("depositSubCurrencyList", []):
                    s = sub.get("symbol")
                    result[s] = {
                        "deposit": sub.get("rechargeable"),
                        "deposit_remark": sub.get("depositRemark") or "",
                        "withdraw": sub.get("withdrawable"),
                        "withdraw_remark": sub.get("withdrawRemark") or ""
                    }
            return result
    except Exception as e:
        logging.error(f"[Cloud OKX] Erro ao buscar {symbol_query}: {e}")
        return {}

def fetch_binance_symbols_status() -> dict:
    url = "https://www.binance.com/bapi/capital/v1/public/capital/getNetworkCoinAll"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "clienttype": "web"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = {}
            for item in data.get("data", []):
                coin = item.get("coin")
                if coin in ["BNB", "USDT"]:
                    for net in item.get("networkList", []):
                        network = net.get("network") or ""
                        net_name = net.get("name") or ""
                        if "BSC" in network or "BEP20" in net_name:
                            key = f"BINANCE-BSC-{coin}"
                            deposit_enable = bool(net.get("depositEnable"))
                            withdraw_enable = bool(net.get("withdrawEnable"))
                            d_desc = net.get("depositDesc") or net.get("depositMsgCategoryDesc") or "Indisponível no momento"
                            w_desc = net.get("withdrawDesc") or net.get("withdrawMsgCategoryDesc") or "Indisponível no momento"
                            result[key] = {
                                "deposit": deposit_enable,
                                "deposit_remark": "Normal" if deposit_enable else d_desc,
                                "withdraw": withdraw_enable,
                                "withdraw_remark": "Normal" if withdraw_enable else w_desc
                            }
            return result
    except Exception as e:
        logging.error(f"[Cloud Binance] Erro ao buscar BSC: {e}")
        return {}

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def format_suspension_alert(key: str, info: dict, status: dict) -> str:
    now_str = datetime.now(TZ_BR).strftime("%d/%m/%Y às %H:%M")
    name = info["name"]
    emoji = info["emoji"]
    exchange = info.get("exchange", "OKX")
    link = info.get("link", "https://www.okx.com/pt-br/status")

    withdraw_ok = status.get("withdraw", True)
    w_remark = status.get("withdraw_remark") or "Em manutenção temporária"
    deposit_ok = status.get("deposit", True)
    d_remark = status.get("deposit_remark") or "Em manutenção temporária"

    msg = [
        f"🚨 <b>ALERTA {exchange.upper()}: {emoji} REDE {name.upper()} SUSPENSA!</b> 🚨\n",
        f"⚠️ <b>Atenção:</b> A rede <b>{name}</b> teve operações temporariamente suspensas na {exchange}!",
        f"⏱ <b>Detectado em:</b> {now_str}\n",
        f"📤 <b>Saques:</b> " + ("🟢 Normal" if withdraw_ok else f"🔴 <b>SUSPENSO</b> (<i>{w_remark}</i>)"),
        f"📥 <b>Depósitos:</b> " + ("🟢 Normal" if deposit_ok else f"🔴 <b>SUSPENSO</b> (<i>{d_remark}</i>)"),
        f"\n🛑 <b>Aviso Importante:</b>",
        f"<i>Evite fazer Pix para a {exchange} para converter e enviar nesta rede até que o serviço seja restabelecido!</i>\n",
        f"🔗 <a href=\"{link}\">Acompanhar Status na {exchange}</a>"
    ]
    return "\n".join(msg)

def format_recovery_alert(key: str, info: dict, status: dict) -> str:
    now_str = datetime.now(TZ_BR).strftime("%d/%m/%Y às %H:%M")
    name = info["name"]
    emoji = info["emoji"]
    exchange = info.get("exchange", "OKX")
    link = info.get("link", "https://www.okx.com/pt-br/status")

    msg = [
        f"✅ <b>{exchange.upper()}: {emoji} {name.upper()} NORMALIZADO!</b> ✅\n",
        f"🟢 <b>Operações liberadas novamente na {exchange}!</b>\n",
        f"🏷 <b>Ativo/Rede:</b> <b>{name}</b>",
        f"⏱ <b>Horário:</b> {now_str}",
        f"📤 <b>Saques:</b> 🟢 Liberados",
        f"📥 <b>Depósitos:</b> 🟢 Liberados\n",
        f"💡 <i>Você já pode depositar via Pix e realizar transferências normalmente na {exchange}.</i>\n",
        f"🔗 <a href=\"{link}\">Abrir {exchange}</a>"
    ]
    return "\n".join(msg)

def check_networks_cycle(allow_telegram: bool = True):
    state = load_state()
    has_changes = False

    usdt_data = fetch_okx_symbol_status("USDT")
    pol_data = fetch_okx_symbol_status("POL")
    trx_data = fetch_okx_symbol_status("TRX")
    binance_data = fetch_binance_symbols_status()

    all_fetched = {}
    all_fetched.update(usdt_data)
    all_fetched.update(pol_data)
    all_fetched.update(trx_data)
    all_fetched.update(binance_data)

    current_statuses = {}
    for key, info in TARGET_SYMBOLS.items():
        if key in all_fetched:
            current_statuses[key] = all_fetched[key]

    if not current_statuses:
        return

    is_first_run = (len(state) == 0)
    if is_first_run:
        for k, v in current_statuses.items():
            state[k] = v
        state["last_checked"] = datetime.now(TZ_BR).isoformat()
        save_state(state)
        return

    for key, info in TARGET_SYMBOLS.items():
        curr = current_statuses.get(key)
        if not curr:
            continue
        prev = state.get(key)
        if not prev:
            state[key] = curr
            has_changes = True
            continue

        prev_w = prev.get("withdraw")
        prev_d = prev.get("deposit")
        curr_w = curr.get("withdraw")
        curr_d = curr.get("deposit")

        # Suspensão detectada
        if (prev_w is True and curr_w is False) or (prev_d is True and curr_d is False):
            logging.warning(f"[Cloud {info.get('exchange', 'OKX')}] SUSPENSÃO: {key}")
            if allow_telegram:
                send_telegram(format_suspension_alert(key, info, curr))
            state[key] = curr
            has_changes = True

        # Normalização detectada
        elif (prev_w is False and curr_w is True) or (prev_d is False and curr_d is True):
            logging.info(f"[Cloud {info.get('exchange', 'OKX')}] RECUPERAÇÃO: {key}")
            if allow_telegram:
                send_telegram(format_recovery_alert(key, info, curr))
            state[key] = curr
            has_changes = True
        else:
            state[key] = curr

    state["last_checked"] = datetime.now(TZ_BR).isoformat()
    if has_changes:
        save_state(state)

def run_okx_sentinel_loop():
    """Loop contínuo para rodar em background thread no Render."""
    logging.info("[Cloud Sentinel] Iniciando monitor OKX & Binance BSC (Render 24/7)...")
    while True:
        try:
            # No Render ou cloud, allow_telegram é True
            is_cloud = bool(os.environ.get("RENDER") or os.environ.get("PORT"))
            allow_notify = is_cloud or ("--enable-local-telegram" in sys.argv)
            check_networks_cycle(allow_telegram=allow_notify)
        except Exception as e:
            logging.error(f"[Cloud Sentinel OKX] Erro no ciclo: {e}")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    check_networks_cycle(allow_telegram=True)
