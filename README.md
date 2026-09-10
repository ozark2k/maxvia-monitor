# 📦 MaxVia88 Telegram Stock Monitor

Script em Python para monitorar o estoque da plataforma **[https://maxvia88.com/](https://maxvia88.com/)** e enviar alertas em tempo real para o **Telegram** sempre que houver:
- 🟢 **Reposição de estoque** (Restock)
- 🔴 **Produtos esgotados** (Out of stock)
- 📉 **Vendas / Queda de estoque**
- ✨ **Novos produtos adicionados**

---

## 🛠️ Requisitos

- Python 3.8 ou superior
- Bibliotecas Python: `beautifulsoup4`, `python-dotenv` (opcional)

---

## 🚀 Como Configurar e Executar

### 1. Clonar ou Baixar os Arquivos
Certifique-se de que os arquivos do projeto estejam em uma pasta no seu computador ou servidor:
- `maxvia_monitor.py`
- `requirements.txt`
- `.env` (a ser criado a partir de `.env.example`)

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

---

## 🤖 Criando o Bot no Telegram e Obtendo as Chaves

### Passos para obter o `TELEGRAM_BOT_TOKEN`:
1. No Telegram, pesquise pelo usuário `@BotFather`.
2. Envie o comando `/newbot`.
3. Escolha um nome e um usuário para o seu bot (ex: `MaxViaMonitorBot`).
4. O `@BotFather` responderá com o seu **HTTP API Token**. Guarde essa chave!

### Passos para obter o seu `TELEGRAM_CHAT_ID`:
1. Inicie uma conversa com o bot que você acabou de criar enviando `/start` ou qualquer mensagem.
2. Em seguida, pesquise no Telegram pelo bot `@userinfobot` ou `@getidsbot` e envie qualquer mensagem para ele.
3. Ele responderá com o seu `Id` numérico (ex: `123456789`). Se quiser receber os alertas em um canal/grupo, adicione o bot ao grupo e use o bot `@GetIDBot` dentro do grupo para pegar o Chat ID do grupo (começa com `-100...`).

---

## ⚙️ Configuração do Arquivo `.env`

Crie um arquivo `.env` na mesma pasta do script (copie do `.env.example`):

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
CHECK_INTERVAL=60
```

---

## 🏃 Como Executar

### Testar Execução Única (Simulação)
```bash
python3 maxvia_monitor.py --once
```

### Executar em Loop Contínuo
```bash
python3 maxvia_monitor.py
```

### Executar via Argumentos de Linha de Comando (sem arquivo .env)
```bash
python3 maxvia_monitor.py --token "SEU_BOT_TOKEN" --chat-id "SEU_CHAT_ID" --interval 60
```

---

## 🖥️ Executando em Segundo Plano no Servidor (Linux / VPS)

### Opção 1: Usando `nohup`
```bash
nohup python3 maxvia_monitor.py > monitor.log 2>&1 &
```

### Opção 2: Usando `systemd` (Recomendado para VPS/Linux)
Crie o arquivo `/etc/systemd/system/maxvia-monitor.service`:

```ini
[Unit]
Description=MaxVia88 Telegram Stock Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/caminho/para/pasta/maxvia_monitor
ExecStart=/usr/bin/python3 /caminho/para/pasta/maxvia_monitor/maxvia_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ative o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable maxvia-monitor
sudo systemctl start maxvia-monitor
```

---

## 📊 Formato dos Alertas no Telegram

```
🔔 MaxVia88 Atualização de Estoque (27/08/2026 10:51:04)

🟢 REPOSIÇÃO DE ESTOQUE! (+10)
📦 Produto: 50 Page Created 2021
💵 Preço: $18.71
📈 Estoque: 10 ➔ 20
```

---

## 📁 Estrutura de Arquivos

```
maxvia_monitor/
├── maxvia_monitor.py   # Script principal do monitor
├── stock_state.json    # Histórico do estoque (gerado automaticamente)
├── requirements.txt    # Dependências do Python
├── .env.example        # Modelo de configuração das credenciais
└── README.md           # Guia de uso
```
