#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Sentinel: Microsoft 365 & Outlook Global Outage Monitor
Monitora 24/7 no Render:
  1. Feed oficial de incidentes da Microsoft: https://status.cloud.microsoft/api/feed/mac
  2. Conectividade direta de resposta do Outlook Web Access (OWA) e Login Microsoft.
Dispara alerta instantâneo no Telegram assim que os serviços do Outlook / Hotmail forem restabelecidos.
"""

import os
import sys
import time
import json
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8692174015:AAFl7TCPswrYFHoMhSbgAtb5V3F8Px1k_HA")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "11579952")

CHECK_INTERVAL_SECONDS = 60  # Checagem a cada 1 minuto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "microsoft_state.json")
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
            logging.warning(f"[Cloud Microsoft Sentinel] Tentativa {attempt} Telegram falhou: {e}")
            time.sleep(2)
    return False

def check_microsoft_feed() -> dict:
    """Consulta o feed oficial de status da Microsoft Cloud."""
    url = "https://status.cloud.microsoft/api/feed/mac"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/rss+xml, text/xml"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            xml_data = r.read()
        root = ET.fromstring(xml_data)
        items = root.findall(".//item")
        
        has_degradation = False
        incident_titles = []
        for it in items:
            status_el = it.find("status")
            status_text = (status_el.text or "").strip() if status_el is not None else ""
            title_el = it.find("title")
            title_text = (title_el.text or "").strip() if title_el is not None else ""
            
            if "degradation" in status_text.lower() or "outage" in status_text.lower() or "incident" in status_text.lower():
                has_degradation = True
                incident_titles.append(f"{title_text} ({status_text})")
                
        return {
            "success": True,
            "has_degradation": has_degradation,
            "active_incidents": incident_titles,
            "total_items": len(items)
        }
    except Exception as e:
        logging.error(f"[Cloud Microsoft Sentinel] Erro ao consultar feed oficial: {e}")
        return {"success": False, "has_degradation": None, "error": str(e)}

def check_outlook_live_connection() -> dict:
    """Testa resposta HTTP direta do Outlook e Login Microsoft."""
    endpoints = [
        ("Login Microsoft", "https://login.live.com/"),
        ("Outlook Web", "https://outlook.live.com/owa/")
    ]
    all_ok = True
    details = {}
    
    for name, url in endpoints:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )
        try:
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=8) as r:
                latency_ms = round((time.time() - t0) * 1000)
                details[name] = {"ok": True, "status": r.status, "latency_ms": latency_ms}
        except Exception as e:
            all_ok = False
            details[name] = {"ok": False, "error": str(e)}
            
    return {"all_ok": all_ok, "details": details}

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Estado inicial: a pane começou e está em andamento (is_degraded = True)
    return {
        "is_degraded": True,
        "first_detected": datetime.now(TZ_BR).isoformat(),
        "healthy_consecutive_cycles": 0,
        "last_checked": None
    }

def save_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"[Cloud Microsoft Sentinel] Erro ao salvar state: {e}")

def format_recovery_alert(now_str: str, feed_info: dict, live_info: dict) -> str:
    msg = [
        "🎉🟢 <b>MICROSOFT 365 & OUTLOOK: SERVIÇOS RESTABELECIDOS!</b> 🟢🎉\n",
        "✅ <b>A Microsoft normalizou os servidores do Outlook e Exchange Online!</b>",
        f"⏱ <b>Detectado em:</b> {now_str}\n",
        "📊 <b>Status da Infraestrutura:</b>",
        "• <b>Painel Oficial Microsoft:</b> 🟢 Operacional (Incidentes mitigados)",
        "• <b>Outlook Web (OWA):</b> 🟢 Respondendo normalmente",
        "• <b>Login Microsoft / Live:</b> 🟢 Online e autenticando\n",
        "💡 <b>Tudo liberado:</b>",
        "<i>Você já pode acessar e-mails, receber códigos de verificação 2FA e fazer login em contas Hotmail / Outlook normalmente!</i>\n",
        "🔗 <a href=\"https://status.cloud.microsoft/\">Ver Status Oficial da Microsoft</a>"
    ]
    return "\n".join(msg)

def check_microsoft_cycle(allow_telegram: bool = True):
    state = load_state()
    now_dt = datetime.now(TZ_BR)
    now_str = now_dt.strftime("%d/%m/%Y às %H:%M")
    
    feed_res = check_microsoft_feed()
    live_res = check_outlook_live_connection()
    
    # Determina se os serviços estão 100% saudáveis:
    # 1. O feed oficial não pode acusar degradação ativa (ou deve estar acessível e limpo)
    # 2. As conexões diretas do Outlook devem responder sem timeout
    feed_clean = (feed_res.get("success") is True and feed_res.get("has_degradation") is False)
    live_healthy = (live_res.get("all_ok") is True)
    
    is_healthy = feed_clean and live_healthy
    
    logging.info(f"[Cloud Microsoft Sentinel] Check: Feed clean={feed_clean}, Live healthy={live_healthy} (Degraded state: {state.get('is_degraded')})")
    
    if is_healthy:
        consecutive = state.get("healthy_consecutive_cycles", 0) + 1
        state["healthy_consecutive_cycles"] = consecutive
        
        # Exige 2 ciclos consecutivos saudáveis (2 minutos) para garantir estabilidade real
        if state.get("is_degraded", True) and consecutive >= 2:
            logging.info("[Cloud Microsoft Sentinel] 🔥 RECUPERAÇÃO DETECTADA! Enviando alerta Telegram...")
            if allow_telegram:
                send_telegram(format_recovery_alert(now_str, feed_res, live_res))
            state["is_degraded"] = False
            state["recovered_at"] = now_dt.isoformat()
    else:
        state["healthy_consecutive_cycles"] = 0
        state["is_degraded"] = True
        
    state["last_checked"] = now_dt.isoformat()
    save_state(state)

def run_microsoft_sentinel_loop():
    """Loop contínuo em background no Render."""
    logging.info("[Cloud Microsoft Sentinel] Iniciando monitoramento 24/7 de recuperação da Microsoft / Outlook...")
    while True:
        try:
            is_cloud = bool(os.environ.get("RENDER") or os.environ.get("PORT"))
            allow_notify = is_cloud or ("--enable-local-telegram" in sys.argv)
            check_microsoft_cycle(allow_telegram=allow_notify)
        except Exception as e:
            logging.error(f"[Cloud Microsoft Sentinel] Erro no ciclo: {e}")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    check_microsoft_cycle(allow_telegram=True)
