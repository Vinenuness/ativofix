<div align="center">

<img src="templates/static/logo.png" alt="AtivoFix — Tecnologia em Movimento" width="420"/>

**Tecnologia em Movimento**

*Gestão de inventário de TI e chamados para empresas multi-unidade*

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-Proprietary-red)

[Funcionalidades](#-funcionalidades) · [Arquitetura](#-arquitetura) · [Instalação](#-instalação) · [Produção](#-deploy-em-produção) · [API](#-api-pública-v1) · [Agente](#-agente-windows)

</div>

---

## 📦 O que é

O **AtivoFix** centraliza todo o parque de TI da empresa em um só painel:

- **Inventário automático** — um agente leve instalado nos PCs reporta hardware, software e status em tempo real
- **Chamados organizados por unidade** — usuários abrem chamados pelo portal público e cada solicitação chega ao técnico certo, com SLA, histórico e anexos
- **Estrutura hierárquica** — Empresa → Unidade → Local, com isolamento total entre empresas (multi-tenant)
- **Relatórios profissionais** — PDF com marca, filtro por período/unidade, prontos para a diretoria

## ✨ Funcionalidades

| Módulo | Recursos |
|---|---|
| 🖥️ **Inventário** | Coleta automática de CPU, RAM, disco, SO e programas; status online; etiqueta TAG por máquina |
| 🎫 **Chamados (OS)** | Portal público sem login; cascata Empresa→Unidade→Local; prioridade e SLA; início de atendimento com observação; conclusão; anexos (fotos/prints); CPF obrigatório; CSAT |
| 🏢 **Multi-tenant** | Várias empresas no mesmo servidor; usuários, unidades, locais e máquinas isolados por empresa |
| 👥 **Usuários** | Papéis (Admin Master, Admin da Empresa, Admin da Unidade, Técnico); escopo por unidade — cada um só vê o que é dele; reset de senha via e-mail |
| 📄 **Relatórios** | PDF de inventário e de chamados com cabeçalho/rodapé da marca; filtros por período e unidade |
| 🔧 **Scripts remotos** | Execução de scripts `.bat` nos PCs via agente |
| 📊 **Dashboard** | KPIs em tempo real, gráficos, máquinas offline, chamados por unidade |
| 🔔 **Notificações** | E-mail por unidade: quem é vinculado a uma unidade recebe só os chamados dela |
| 🔐 **Segurança** | bcrypt, rate limit, headers CSP/HSTS, sessão com escopo, chaves de API com hash |
| 📣 **Divulgação** | Gerador de cartaz A4 300 DPI com QR Code do portal, personalizado pela marca |

## 🏗️ Arquitetura

```
┌──────────────┐   HTTPS    ┌─────────────────────────────────────────┐
│ Agente (PCs) │──────────► │              VPS (Ubuntu)               │
│  agente.py   │  /api/...  │  ┌─────────┐  ┌──────────────────────┐  │
└──────────────┘            │  │  Nginx  │─►│ Gunicorn × Flask     │  │
                            │  │ + TLS   │  │ (templates/server.py)│  │
┌──────────────┐            │  └─────────┘  └──────────┬───────────┘  │
│  Navegador   │──────────► │                          │              │
│ Painel/Portal│            │              ┌───────────▼───────────┐  │
└──────────────┘            │              │      SQLite (WAL)     │  │
                            │              └───────────────────────┘  │
┌──────────────┐            │  SMTP (Gmail) → notificações e recovery │
│ Sistema do   │──X-API-KEY─└─────────────────────────────────────────┘
│ cliente      │  /api/v1/...
└──────────────┘
```

**Stack:** Python · Flask · SQLite · Gunicorn · Nginx · Chart.js · fpdf2 · bcrypt · PyInstaller

## 🚀 Instalação (desenvolvimento)

```bash
# 1. Clonar
git clone https://github.com/Vinenuness/invpro.git
cd invpro/templates

# 2. Ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# 3. Dependências
pip install -r ../requirements.txt

# 4. Rodar
python server.py
```

| Acesso | Valor |
|---|---|
| Painel | `http://localhost:5000` |
| Login padrão dev | `admin` / `admin` |
| Portal público | `http://localhost:5000/abrir-chamado` |
| Login alternativo | `/login2` (variante fullscreen) |

> ⚙️ Em produção **nunca** use `admin/admin` — defina `PANEL_USER`/`PANEL_PASS` no `.env`.

## 📦 Deploy em produção

Guia completo em **[DEPLOY.md](DEPLOY.md)**. Resumo do fluxo na VPS:

```bash
cd /opt/ativofix && git pull          # atualizar código
systemctl restart ativofix            # serviço systemd (auto-start no boot)
journalctl -u ativofix -f             # logs
```

Componentes: **systemd** (serviço sempre ativo) · **Nginx + Let's Encrypt** (HTTPS) · **UFW** (firewall) · **cron** (backup diário do banco às 03:00).

## 🔌 API pública v1

Integração para sistemas externos (ERP, helpdesk do cliente) — **isolada por empresa** via chave `X-API-KEY`:

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/v1/ping` | Testar a chave |
| `GET` | `/api/v1/computers` | Máquinas da empresa (unidade, local, status) |
| `GET` | `/api/v1/units` | Unidades + contagens |
| `GET` | `/api/v1/locations` | Locais por unidade |
| `GET` | `/api/v1/tickets` | Chamados (filtros: `status`, `since`, página) |
| `POST` | `/api/v1/tickets` | **Abrir chamado** pelo sistema do cliente |

```python
import requests

r = requests.post(
    "https://ativofix.com.br/api/v1/tickets",
    headers={"X-API-KEY": "afk_..."},
    json={
        "title": "Impressora não imprime",
        "priority": "high",
        "unit_name": "HSL Garca",
        "location_name": "triagem",
        "cpf": "000.000.000-00",
    },
)
print(r.json())   # {"ok": true, "ticket_id": 23}
```

Gerencie as chaves em **Painel → Menu → API** (`/api-docs`): gerar, desativar e ver último uso. A chave é exibida uma única vez; no banco existe apenas o hash SHA-256.

## 💻 Agente Windows

Coleta inventário e executa scripts remotos. Compilado com PyInstaller (`AtivoFixAgente.spec`).

```bash
pip install -r requirements-agent.txt
python agente.py                  # modo console p/ desenvolvimento
```

Distribuição: `dist/AtivoFix-Agente-Windows.zip` → instalar e informar a **TAG** da máquina. A configuração fica em `C:\ProgramData\AgenteTI` — atualizar o `.exe` não perde o vínculo.

## 🗂️ Estrutura do projeto

```
invpro/
├── templates/                  # aplicação (APP_DIR aponta para cá)
│   ├── server.py               # servidor Flask completo (~5k linhas)
│   ├── *.html                  # 25 telas (painel, portal, relatórios...)
│   ├── static/
│   │   ├── brand.css           # design system global (todas as páginas)
│   │   ├── logo*.png           # kit da marca (web, print, dark)
│   │   ├── favicon*            # kit de ícones
│   │   └── divulgacao/         # cartaz A4 + versão digital (QR code)
│   ├── agente.py               # agente de coleta (mesmo código do root)
│   ├── db.sqlite3              # banco (dev)
│   └── .venv/                  # ambiente virtual (não versionado)
├── deploy/
│   ├── ativofix.service        # unidade systemd
│   └── nginx-ativofix.conf     # reverse proxy + TLS
├── DEPLOY.md                   # guia de produção
├── requirements*.txt           # dependências (servidor / prod / agente)
└── instalar-agente.ps1         # instalador do agente
```

## 🛠️ Manutenção

Scripts utilitários em `templates/` (rodar com o Python da venv):

| Script | Função |
|---|---|
| `_rebrand_assets.py` | Regenera todo o kit da marca a partir de `static/brand-src/` (logo, print, dark, `agent.ico`) |
| `_gen_favicon.py` | Gera `favicon.ico` multi-tamanho + `favicon-32.png` + `apple-touch-icon.png` |
| `_cache_bust.py` | Versiona os assets (`?v=YYYYMMDDx`) nas 25 páginas — **rode após trocar qualquer asset** |
| `_gen_poster.py` | Gera o cartaz A4 300 DPI e a arte digital com QR code do portal |

## 📄 Licença

© 2026 **AtivoFix** — Tecnologia em Movimento. Todos os direitos reservados.

<div align="center">
<img src="templates/static/logo-icon.png" alt="AtivoFix" width="72"/>
</div>
