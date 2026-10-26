#!/usr/bin/env python3
"""
Extrai a sessão atual do MaxVia88 do Chrome do macOS
e atualiza o repositório no GitHub para o Render redeployar automaticamente
sempre que você quiser renovar o cookie da nuvem.
"""
import os
import re
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from maxvia_monitor import get_chrome_cookies

def main():
    print("🔍 Extraindo cookies de sessão do MaxVia88 do Google Chrome...")
    cookie = get_chrome_cookies()
    if not cookie or "laravel_session=" not in cookie:
        print("❌ Não foi possível extrair a sessão ativa do Chrome.")
        print("Certifique-se de estar logado no site https://maxvia88.com no Google Chrome.")
        sys.exit(1)

    print("✅ Sessão extraída com sucesso!")
    render_yaml_path = os.path.join(SCRIPT_DIR, "render.yaml")
    if not os.path.exists(render_yaml_path):
        print("❌ render.yaml não encontrado.")
        sys.exit(1)

    with open(render_yaml_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Substitui a linha do MAXVIA_COOKIE
    pattern = r'(- key: MAXVIA_COOKIE\s*\n\s*value:\s*)"[^"]*"'
    replacement = f'\\1"{cookie}"'

    if not re.search(pattern, content):
        print("❌ Padrão MAXVIA_COOKIE não encontrado em render.yaml")
        sys.exit(1)

    new_content = re.sub(pattern, replacement, content)

    if new_content == content:
        print("ℹ️ O cookie no render.yaml já está 100% atualizado com a sessão do Chrome.")
        sys.exit(0)

    with open(render_yaml_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("📝 render.yaml atualizado com o novo cookie!")
    print("🚀 Enviando para o GitHub para atualizar o Render na nuvem...")

    try:
        subprocess.run(["git", "add", "render.yaml", "config.json"], cwd=SCRIPT_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "Auto-sync fresh Chrome session cookie to Render"], cwd=SCRIPT_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=SCRIPT_DIR, check=True)
        print("🎉 Pronto! O Render está reiniciando na nuvem com o novo cookie!")
    except Exception as e:
        print(f"⚠️ Erro ao enviar para o GitHub: {e}")

if __name__ == "__main__":
    main()
