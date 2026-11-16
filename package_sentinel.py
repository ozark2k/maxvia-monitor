#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Package Sentinel: Rastreamento Automático de Encomendas (J&T Express & Multi-transportadoras)
Roda 24/7 no Render em segundo plano:
  - Monitora códigos de rastreio cadastrados em package_state.json
  - Implementa a assinatura reversa nativa da J&T Express Brasil (appId + timestamp + nonce + JSON + key)
  - Dispara notificações instantâneas no Telegram a cada nova movimentação, trânsito ou entrega
"""

import os
import sys
import time
import json
import random
import hashlib
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8692174015:AAFl7TCPswrYFHoMhSbgAtb5V3F8Px1k_HA")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "11579952")

CHECK_INTERVAL_SECONDS = 300  # Checagem a cada 5 minutos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "package_state.json")
TZ_BR = timezone(timedelta(hours=-3))

# Constantes de assinatura da API oficial J&T Express Brasil
JT_APP_ID = "3B29A9C5728BF3E1DB0C4D66B79748B7"
JT_KEY = "94bbcac67ab47c736d530efe3e1dc358"
JT_API_BASE = "https://official.jtjms-br.com"

def send_telegram(text: str) -> bool:
    """Envia notificação formatada em HTML para o Telegram."""
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
            logging.warning(f"[Package Sentinel] Tentativa {attempt} Telegram falhou: {e}")
            time.sleep(2)
    return False

def load_state() -> dict:
    """Carrega o estado dos pacotes monitorados."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"[Package Sentinel] Erro ao ler {STATE_FILE}: {e}")
    
    # Estado inicial padrão com o rastreio solicitado
    default_state = {
        "packages": {
            "888002851240135": {
                "carrier": "J&T Express Brasil",
                "waybill": "888002851240135",
                "cpf": "",
                "last_event_time": "2026-11-13 22:23:18",
                "last_event_desc": "[Barueri] Saída da encomenda expressa [SP BRE] enviada para [PA ANA]",
                "status": "Em trânsito (SP BRE -> PA ANA)",
                "history": [
                    {
                        "time": "2026-11-13 10:29:58",
                        "desc": "[Barueri] [PA MELI-CJM-SP] Seu entregador L****o retirou a encomenda. Se você tiver qualquer problema ou reclamação, ligue para o número da filial: 08000550050"
                    },
                    {
                        "time": "2026-11-13 10:30:08",
                        "desc": "[Barueri] Saída da encomenda expressa [PA MELI-CJM-SP] enviada para [SP BRE]"
                    },
                    {
                        "time": "2026-11-13 18:34:00",
                        "desc": "[Barueri] Chegada da encomenda expressa [SP BRE]"
                    },
                    {
                        "time": "2026-11-13 22:23:18",
                        "desc": "[Barueri] Saída da encomenda expressa [SP BRE] enviada para [PA ANA]"
                    }
                ],
                "delivered": False
            }
        }
    }
    save_state(default_state)
    return default_state

def save_state(state: dict):
    """Persiste o estado dos pacotes monitorados."""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"[Package Sentinel] Erro ao salvar {STATE_FILE}: {e}")

def query_jt_official_api(waybill: str, cpf: str) -> list:
    """
    Consulta a API oficial assinada da J&T Express Brasil (v2/getDetailByWaybillNo).
    Retorna a lista de eventos de rastreamento ordenados cronologicamente.
    """
    if not waybill:
        return []
        
    url = f"{JT_API_BASE}/official/logisticsTracking/v2/getDetailByWaybillNo"
    now_ms = int(time.time() * 1000)
    nonce = str(random.random())

    body = {"waybillNo": str(waybill), "langType": "pt-br"}
    if cpf:
        body["cpf"] = str(cpf).replace(".", "").replace("-", "").strip()

    # Ordenação de chaves para cálculo da assinatura
    sorted_keys = sorted(body.keys())
    sorted_dict = {k: body[k] for k in sorted_keys}
    body_json = json.dumps(sorted_dict, separators=(",", ":"))

    raw_sign_str = f"{JT_APP_ID}{now_ms}{nonce}{body_json}{JT_KEY}"
    sign = hashlib.md5(raw_sign_str.encode("utf-8")).hexdigest().upper()

    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Cache-Control": "max-age=2, must-revalidate",
        "langType": "pt-br",
        "clientSource": "web",
        "timezone": "GMT-0300",
        "timeZone": "GMT-0300",
        "countryId": "1",
        "token": "",
        "appId": JT_APP_ID,
        "key": JT_KEY,
        "nonce": nonce,
        "timestamp": str(now_ms),
        "sign": sign,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://jtexpress.com.br",
        "Referer": "https://jtexpress.com.br/"
    }

    try:
        req = urllib.request.Request(url, data=body_json.encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("succ") and data.get("data"):
                details = data["data"].get("details") or []
                return details
            else:
                msg = data.get("msg", "")
                if msg and "cpf" not in msg.lower():
                    logging.info(f"[Package Sentinel] J&T resposta: {msg}")
    except Exception as e:
        logging.warning(f"[Package Sentinel] Erro ao consultar API oficial J&T: {e}")
    return []

def check_package_updates():
    """Verifica todos os pacotes ativos e dispara alertas se houver novos eventos."""
    state = load_state()
    packages = state.get("packages", {})
    state_modified = False

    for waybill, pkg in list(packages.items()):
        if pkg.get("delivered", False):
            continue  # Já entregue, não precisa consultar

        carrier = pkg.get("carrier", "J&T Express")
        cpf = pkg.get("cpf", "")
        last_event_time = pkg.get("last_event_time", "")
        last_event_desc = pkg.get("last_event_desc", "")
        existing_history = pkg.get("history", [])

        events = []
        if "j&t" in carrier.lower() or "jt" in carrier.lower():
            if cpf:
                events = query_jt_official_api(waybill, cpf)

        if not events:
            continue

        # Ordenar eventos por scanTime/data
        # J&T details format: [{"scanTime": "2026-11-13 22:23:18", "desc": "...", "cityName": "Barueri"}, ...]
        new_events = []
        for ev in events:
            ev_time = ev.get("scanTime") or ev.get("time") or ""
            ev_desc = ev.get("desc") or ev.get("scanNetworkName") or ""
            ev_city = ev.get("cityName") or ""
            if ev_city and ev_city not in ev_desc:
                full_desc = f"[{ev_city}] {ev_desc}"
            else:
                full_desc = ev_desc

            # Se evento é mais novo que o último registrado
            if ev_time and ev_time > last_event_time:
                new_events.append({"time": ev_time, "desc": full_desc})

        if new_events:
            logging.info(f"[Package Sentinel] {len(new_events)} nova(s) movimentação(ões) para {waybill}!")
            # Disparar alertas para cada novo evento (ou o mais recente)
            for nev in new_events:
                msg = (
                    f"📦🚚 <b>[RASTREIO {carrier.upper()}] NOVA ATUALIZAÇÃO!</b>\n\n"
                    f"<b>Código:</b> <code>{waybill}</code>\n"
                    f"<b>Data e Hora:</b> 📅 <i>{nev['time']}</i>\n"
                    f"<b>Status:</b> 📍 {nev['desc']}\n\n"
                    f"🔗 <a href='https://jtexpress.com.br/trajectoryQuery?waybillNo={waybill}'>Ver no Site Oficial J&T Express</a>"
                )
                send_telegram(msg)
                time.sleep(1)

                existing_history.append(nev)
                last_event_time = nev["time"]
                last_event_desc = nev["desc"]

            pkg["last_event_time"] = last_event_time
            pkg["last_event_desc"] = last_event_desc
            pkg["history"] = existing_history

            # Verifica se foi entregue
            lower_desc = last_event_desc.lower()
            if any(k in lower_desc for k in ["entregue", "entrega realizada", "destinatário recebeu", "concluída"]):
                pkg["delivered"] = True
                pkg["status"] = "Entregue"
                delivered_msg = (
                    f"🎉📦 <b>[RASTREIO {carrier.upper()}] ENCOMENDA ENTREGUE!</b>\n\n"
                    f"<b>Código:</b> <code>{waybill}</code>\n"
                    f"<b>Status Final:</b> {last_event_desc}\n"
                    f"<b>Data de Entrega:</b> {last_event_time}"
                )
                send_telegram(delivered_msg)

            state_modified = True

    if state_modified:
        save_state(state)

def run_package_sentinel_loop():
    """Loop contínuo 24/7 para execução em background thread no Render."""
    logging.info("[Render Cloud] Package Sentinel Loop iniciado 24/7.")
    while True:
        try:
            check_package_updates()
        except Exception as e:
            logging.error(f"[Package Sentinel] Erro inesperado no ciclo de checagem: {e}")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("Testando Package Sentinel...")
    state = load_state()
    print("Pacotes carregados:", json.dumps(state, indent=2, ensure_ascii=False))
    check_package_updates()
    print("Checagem concluída.")
