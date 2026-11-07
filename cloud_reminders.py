#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Reminders Engine
Permite agendar lembretes customizados para envio no Telegram na data e hora exatas (Horário de Brasília).
Roda 24/7 no Render em segundo plano.
"""

import os
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REMINDERS_FILE = os.path.join(BASE_DIR, "reminders.json")
TZ_BR = timezone(timedelta(hours=-3))

def send_telegram_reminder(bot_token: str, chat_id: str, text: str) -> bool:
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
            logging.warning(f"[Cloud Reminders] Tentativa {attempt} Telegram falhou: {e}")
    return False

def load_reminders() -> list:
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_reminders(reminders: list):
    try:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def add_reminder(reminder_id: str, target_datetime_str: str, message_text: str):
    """
    Adiciona um lembrete.
    target_datetime_str formato: "YYYY-MM-DD HH:MM"
    """
    reminders = load_reminders()
    # Remove duplicados com mesmo ID
    reminders = [r for r in reminders if r.get("id") != reminder_id]
    reminders.append({
        "id": reminder_id,
        "target_datetime": target_datetime_str,
        "text": message_text,
        "sent": False,
        "created_at": datetime.now(TZ_BR).isoformat()
    })
    save_reminders(reminders)
    logging.info(f"[Cloud Reminders] Lembrete '{reminder_id}' agendado para {target_datetime_str} (BRT).")

def check_and_dispatch_reminders(bot_token: str, chat_id: str, allow_telegram: bool = True):
    reminders = load_reminders()
    if not reminders:
        return

    now_br = datetime.now(TZ_BR)
    updated = False

    for r in reminders:
        if r.get("sent"):
            continue
        target_str = r.get("target_datetime")
        try:
            target_dt = datetime.strptime(target_str, "%Y-%m-%d %H:%M").replace(tzinfo=TZ_BR)
            if now_br >= target_dt:
                text = r.get("text", "")
                logging.info(f"[Cloud Reminders] Disparando lembrete '{r.get('id')}'...")
                if allow_telegram and text:
                    send_telegram_reminder(bot_token, chat_id, text)
                r["sent"] = True
                r["sent_at"] = now_br.isoformat()
                updated = True
        except Exception as e:
            logging.error(f"[Cloud Reminders] Erro no lembrete {r.get('id')}: {e}")

    if updated:
        save_reminders(reminders)
