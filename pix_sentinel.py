#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Sentinel: Pix, Meta Ads & Fast Invite BM Monitor
Roda 24/7 no Render (na nuvem) monitorando:
  - 8 Gateways SPI Pix + Radar de Imprensa de Bancos Brasileiros
  - metastatus.com (Facebook Ads Manager, Marketing API, Ads Delivery, Meta Business Suite)
  - Extensão Chrome Fast Invite BM (Chrome Web Store)
Dispara alertas instantâneos no Telegram para proteger campanhas e contas de anúncios.
"""

import os
import sys
import time
import json
import html
import logging
import urllib.request
import urllib.parse
import email.utils
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8692174015:AAFl7TCPswrYFHoMhSbgAtb5V3F8Px1k_HA")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "11579952")

CHECK_INTERVAL_SECONDS = 120  # 2 minutos

FAST_INVITE_BM_ID = "mchodachnhhbijgofpnlipgdkoamgoia"
FAST_INVITE_BM_URL = f"https://chromewebstore.google.com/detail/fast-invite-bm/{FAST_INVITE_BM_ID}?hl=pt-BR"
FAST_INVITE_BM_STORE_URL = f"https://chromewebstore.google.com/detail/fast-invite-bm/{FAST_INVITE_BM_ID}"

GATEWAYS = [
    {"id": "mercadopago", "name": "Mercado Pago", "base_url": "https://status.mercadopago.com", "icon": "💙"},
    {"id": "asaas", "name": "Asaas", "base_url": "https://status.asaas.com", "icon": "🔵"},
    {"id": "efi", "name": "Efí (Gerencianet)", "base_url": "https://status.sejaefi.com.br", "icon": "🟠"},
    {"id": "pagarme", "name": "Pagar.me (Stone)", "base_url": "https://status.pagar.me", "icon": "🟢"},
    {"id": "iugu", "name": "Iugu", "base_url": "https://status.iugu.com", "icon": "🟣"},
    {"id": "starkbank", "name": "Stark Bank", "base_url": "https://status.starkbank.com", "icon": "⬛"},
    {"id": "yampi", "name": "Yampi Checkout", "base_url": "https://status.yampi.com.br", "icon": "🛒"},
    {"id": "kiwify", "name": "Kiwify Checkout", "base_url": "https://status.kiwify.com.br", "icon": "🥝"}
]

META_TARGET_ORGS = {
    "ads-manager": {"name": "Facebook Ads Manager", "icon": "📢"},
    "marketing-api": {"name": "Marketing API", "icon": "⚙️"},
    "fbs": {"name": "Meta Business Suite", "icon": "💼"},
    "ctx": {"name": "Messaging Ads", "icon": "💬"},
    "catalog": {"name": "Catalog", "icon": "📦"},
    "audience-network": {"name": "Meta Audience Network", "icon": "🌐"},
    "ig-boost": {"name": "Instagram Boost", "icon": "📸"}
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "pix_cloud_state.json")
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
            logging.warning(f"[Cloud Pix Sentinel] Tentativa {attempt} Telegram falhou: {e}")
            time.sleep(2)
    return False

def check_gateway_incidents() -> list:
    active_incidents = []
    for gw in GATEWAYS:
        url = f"{gw['base_url']}/api/v2/incidents/unresolved.json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=7) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for inc in data.get("incidents", []):
                    name = inc.get("name", "")
                    impact = inc.get("impact", "")
                    status = inc.get("status", "")
                    inc_id = inc.get("id", "")
                    updates = inc.get("incident_updates", [])
                    latest_body = updates[0].get("body", "") if updates else ""

                    lower_text = f"{name} {latest_body}".lower()
                    is_pix_related = any(k in lower_text for k in ["pix", "pagamento", "transfer", "banco", "spi", "checkout", "transacion"])

                    if is_pix_related or impact in ["major", "critical"]:
                        active_incidents.append({
                            "source_id": gw["id"],
                            "source_name": gw["name"],
                            "icon": gw["icon"],
                            "id": inc_id,
                            "title": name,
                            "status": status,
                            "impact": impact,
                            "body": latest_body
                        })
        except Exception:
            pass
    return active_incidents

def check_breaking_news_outages() -> list:
    rss_url = "https://news.google.com/rss/search?q=(pix+OR+nubank+OR+itau+OR+bradesco)+AND+(fora+do+ar+OR+instabilidade+OR+caiu)&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    outage_news = []
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read()
            root = ET.fromstring(content)
            now_dt = datetime.now(timezone.utc)

            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""

                if not pub_date:
                    continue
                try:
                    dt = email.utils.parsedate_to_datetime(pub_date)
                    diff_mins = (now_dt - dt).total_seconds() / 60
                    if diff_mins <= 35:
                        lower_title = title.lower()
                        keywords = ["fora do ar", "instabilidade", "apresenta instabilidade", "caiu", "com problemas", "reclamações", "downdetector", "pix falha", "pix fora"]
                        if any(k in lower_title for k in keywords):
                            outage_news.append({
                                "title": title,
                                "link": link,
                                "age_minutes": int(diff_mins)
                            })
                except Exception:
                    continue
    except Exception:
        pass
    return outage_news

def check_meta_status() -> tuple:
    url = "https://metastatus.com/data/orgs.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    meta_issues = []
    orgs_summary = {}
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for org in data:
                org_id = org.get("id")
                if org_id in META_TARGET_ORGS:
                    meta_info = META_TARGET_ORGS[org_id]
                    org_name = meta_info["name"]
                    org_icon = meta_info["icon"]
                    services = org.get("services", [])
                    services_list = []
                    org_has_issue = False

                    for s in services:
                        s_name = s.get("name")
                        s_st = s.get("status", "No known issues")
                        services_list.append({"name": s_name, "status": s_st})
                        if s_st != "No known issues":
                            org_has_issue = True
                            meta_issues.append({
                                "org_id": org_id,
                                "org_name": org_name,
                                "icon": org_icon,
                                "service_name": s_name,
                                "status": s_st,
                                "description": ""
                            })

                    orgs_summary[org_id] = {
                        "name": org_name,
                        "icon": org_icon,
                        "has_issue": org_has_issue,
                        "services": services_list
                    }
    except Exception:
        pass
    return meta_issues, orgs_summary

def check_chrome_extension_status() -> dict:
    req = urllib.request.Request(
        FAST_INVITE_BM_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html_doc = resp.read().decode("utf-8", errors="ignore")

        version = None
        update_date = None
        size = None
        timestamp = None

        m_data = re.search(r'\"(\d+\.\d+(?:\.\d+)*)\",\[(\d{9,11}),\d+\],\"([^\"]+)\"', html_doc)
        if m_data:
            version = m_data.group(1).strip()
            timestamp = int(m_data.group(2))
            size = m_data.group(3).strip()
            dt_br = datetime.fromtimestamp(timestamp, tz=TZ_BR)
            update_date = dt_br.strftime("%d de %B de %Y").lower()

        v_match = re.search(r'>(?:Vers[aã]o|Version)</div>\s*<div[^>]*>([^<]+)</div>', html_doc, re.IGNORECASE)
        d_match = re.search(r'>(?:Atualiza[cç][aã]o|Updated)</div>\s*<div[^>]*>([^<]+)</div>', html_doc, re.IGNORECASE)
        s_match = re.search(r'>(?:Tamanho|Size)</div>\s*<div[^>]*>([^<]+)</div>', html_doc, re.IGNORECASE)

        if v_match:
            version = v_match.group(1).strip()
        if d_match:
            update_date = d_match.group(1).strip()
        if s_match:
            size = s_match.group(1).strip()

        if version or update_date:
            return {
                "name": "Fast Invite BM",
                "extension_id": FAST_INVITE_BM_ID,
                "version": version or "1.1.0",
                "updated_at": update_date or "20 de julho de 2026",
                "size": size or "45.49KiB",
                "timestamp": timestamp,
                "url": FAST_INVITE_BM_STORE_URL
            }
    except Exception as e:
        logging.error(f"[Cloud Sentinel] Erro ao verificar Chrome Web Store: {e}")
    return None

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

def format_pix_outage_alert(gateway_issues: list, news_issues: list) -> str:
    now_str = datetime.now(TZ_BR).strftime("%d/%m/%Y às %H:%M")
    msg = [
        "🚨 <b>ALERTA FACEBOOK ADS: INSTABILIDADE NO PIX / BANCOS!</b> 🚨",
        f"⚠️ <b>Atenção:</b> Detectada instabilidade no sistema de pagamentos ({now_str})!\n"
    ]
    if gateway_issues:
        msg.append("🏢 <b>Gateways & Processadores em Alerta:</b>")
        for iss in gateway_issues:
            source = iss["source_name"]
            title = html.escape(iss["title"])
            impact = iss.get("impact", "").upper()
            icon = iss.get("icon", "⚠️")
            msg.append(f"• {icon} <b>{source}:</b> {title} <code>[{impact}]</code>")
        msg.append("")
    if news_issues:
        msg.append("📰 <b>Radar de Imprensa (Últimos minutos):</b>")
        for n in news_issues[:3]:
            t = html.escape(n["title"])
            age = n["age_minutes"]
            msg.append(f"• 🔴 <i>{t}</i> (há {age} min)")
        msg.append("")
    msg.append("🛑 <b>RECOMENDAÇÃO FACEBOOK ADS:</b>")
    msg.append("<i>Considere pausar ou diminuir o orçamento de suas campanhas de conversão no Brasil para não queimar verba enquanto clientes não conseguem concluir o Pix!</i>\n")
    msg.append("🔔 <i>Você receberá uma nova notificação assim que o sistema normalizar.</i>")
    return "\n".join(msg)

def format_pix_recovery_alert() -> str:
    now_str = datetime.now(TZ_BR).strftime("%d/%m/%Y às %H:%M")
    return (
        "✅ <b>PIX & BANCOS NORMALIZADOS NO BRASIL!</b> ✅\n\n"
        "🟢 <b>Operações de pagamento restabelecidas com sucesso!</b>\n"
        f"⏱ <b>Horário:</b> {now_str}\n\n"
        "💡 <b>Você já pode reativar suas campanhas de Facebook Ads com segurança!</b>"
    )

def format_meta_outage_alert(issues: list) -> str:
    now_str = datetime.now(TZ_BR).strftime("%d/%m/%Y às %H:%M")
    msg = [
        "🚨 <b>ALERTA META ADS: INSTABILIDADE DETECTADA NA META!</b> 🚨",
        f"⚠️ <b>Atenção:</b> O painel oficial <b>metastatus.com</b> registrou instabilidade ({now_str})!\n",
        "📊 <b>Produtos e Serviços Afetados:</b>"
    ]
    for iss in issues:
        org = iss["org_name"]
        srv = iss["service_name"]
        st = iss["status"]
        icon = iss.get("icon", "⚠️")
        msg.append(f"• 🔴 {icon} <b>{org}:</b> {srv} ➔ <code>{st}</code>")
    msg.append("\n🛑 <b>RECOMENDAÇÃO FACEBOOK ADS:</b>")
    msg.append("<i>Evite publicar novos anúncios ou alterar orçamentos enquanto a Meta estiver instável!</i>\n")
    msg.append("🔗 <a href=\"https://metastatus.com\">Acompanhar Status Oficial na Meta</a>")
    return "\n".join(msg)

def format_meta_recovery_alert() -> str:
    now_str = datetime.now(TZ_BR).strftime("%d/%m/%Y às %H:%M")
    return (
        "✅ <b>META ADS NORMALIZADO!</b> ✅\n\n"
        "🟢 <b>Todos os serviços de anúncios da Meta voltaram a operar sem problemas!</b>\n"
        f"⏱ <b>Horário:</b> {now_str}\n\n"
        "💡 <i>Facebook Ads Manager e Meta Business Suite 100% operacionais.</i>\n"
        "🔗 <a href=\"https://metastatus.com\">Ver Meta Status</a>"
    )

def format_extension_update_alert(old_ver: str, new_ver: str, old_date: str, new_date: str, size: str) -> str:
    now_str = datetime.now(TZ_BR).strftime("%d/%m/%Y às %H:%M")
    msg = [
        "🚀 <b>ATUALIZAÇÃO DETECTADA: EXTENSÃO FAST INVITE BM!</b> 🚀\n",
        "📦 <b>Extensão:</b> Fast Invite BM (Chrome Web Store)",
        f"🆕 <b>Nova Versão:</b> <code>{new_ver}</code> " + (f"(era <code>{old_ver}</code>)" if old_ver != new_ver else "(inalterada)"),
        f"📅 <b>Nova Data de Atualização:</b> <code>{new_date}</code> " + (f"(era <code>{old_date}</code>)" if old_date != new_date else ""),
        f"💾 <b>Tamanho:</b> {size}",
        f"⏱ <b>Detectado em:</b> {now_str}\n",
        "💡 <i>Acesse a Chrome Web Store para atualizar ou verificar as mudanças na extensão de BMs:</i>\n",
        f"🔗 <a href=\"{FAST_INVITE_BM_STORE_URL}\">Abrir Fast Invite BM na Chrome Web Store</a>"
    ]
    return "\n".join(msg)

def check_pix_sentinel_cycle(allow_telegram: bool = True):
    state = load_state()

    # 1. PIX
    gateway_issues = check_gateway_incidents()
    news_issues = check_breaking_news_outages()
    pix_has_incident = (len(gateway_issues) > 0 or len(news_issues) > 0)
    pix_was_in_incident = state.get("pix_in_incident", False)

    if pix_has_incident and not pix_was_in_incident:
        logging.warning("[Cloud Pix] Instabilidade no Pix/Bancos detectada!")
        if allow_telegram:
            send_telegram(format_pix_outage_alert(gateway_issues, news_issues))
        state["pix_in_incident"] = True
    elif not pix_has_incident and pix_was_in_incident:
        logging.info("[Cloud Pix] Pix normalizado!")
        if allow_telegram:
            send_telegram(format_pix_recovery_alert())
        state["pix_in_incident"] = False

    # 2. META STATUS
    meta_issues, _ = check_meta_status()
    meta_has_incident = (len(meta_issues) > 0)
    meta_was_in_incident = state.get("meta_in_incident", False)

    if meta_has_incident and not meta_was_in_incident:
        logging.warning("[Cloud Meta] Instabilidade na Meta detectada!")
        if allow_telegram:
            send_telegram(format_meta_outage_alert(meta_issues))
        state["meta_in_incident"] = True
    elif not meta_has_incident and meta_was_in_incident:
        logging.info("[Cloud Meta] Meta normalizada!")
        if allow_telegram:
            send_telegram(format_meta_recovery_alert())
        state["meta_in_incident"] = False

    # 3. FAST INVITE BM EXTENSION
    ext_state = state.get("fast_invite_bm", {
        "version": "1.1.0",
        "updated_at": "20 de julho de 2026",
        "size": "45.49KiB"
    })
    ext_info = check_chrome_extension_status()
    if ext_info:
        old_ver = ext_state.get("version", "1.1.0")
        old_date = ext_state.get("updated_at", "20 de julho de 2026")
        new_ver = ext_info.get("version", old_ver)
        new_date = ext_info.get("updated_at", old_date)

        if (new_ver and new_ver != old_ver) or (new_date and new_date != old_date):
            logging.warning(f"[Cloud Extension] Fast Invite BM atualizada: {old_ver}->{new_ver}")
            if allow_telegram:
                send_telegram(format_extension_update_alert(old_ver, new_ver, old_date, new_date, ext_info.get("size", "")))
            ext_state["version"] = new_ver
            ext_state["updated_at"] = new_date
            ext_state["size"] = ext_info.get("size")

        ext_state["last_checked"] = datetime.now(TZ_BR).isoformat()
        state["fast_invite_bm"] = ext_state

    state["last_checked"] = datetime.now(TZ_BR).isoformat()
    save_state(state)

def run_pix_sentinel_loop():
    """Loop contínuo para rodar em background thread no Render."""
    logging.info("[Cloud Sentinel] Iniciando monitor Pix, Meta Ads & Fast Invite BM (Render 24/7)...")
    while True:
        try:
            is_cloud = bool(os.environ.get("RENDER") or os.environ.get("PORT"))
            allow_notify = is_cloud or ("--enable-local-telegram" in sys.argv)
            check_pix_sentinel_cycle(allow_telegram=allow_notify)
        except Exception as e:
            logging.error(f"[Cloud Sentinel Pix] Erro no ciclo: {e}")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    check_pix_sentinel_cycle(allow_telegram=True)
