<div align="center">

# 📈 Kiwoom Daily Gainers

### After the Korean market closes, see **every stock that popped today — and *why*** — in one click. 🚀

*Powered by the Kiwoom Securities OpenAPI+ (키움증권 OPEN API). No paid data feed. No web scraping headaches.*

![Python](https://img.shields.io/badge/Python-3.8%20(32--bit)-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![Broker](https://img.shields.io/badge/Kiwoom-OpenAPI%2B-red)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

**If this saves you 30 minutes of scrolling every evening, drop a ⭐ — it really helps!**

</div>

---

## ✨ What it does

Every trading day at the close, Korean retail investors ask the same question:

> *"What went up today, and **what was the catalyst**?"*

Answering that by hand means bouncing between the HTS, Naver Finance, news portals, and DART. **This tool does it for you in seconds.** Fire it up after 15:30 KST and get a clean, ranked board of today's movers straight from your own Kiwoom account.

| | Feature |
|---|---|
| 🥇 | **Ranked gainers board** — KOSPI + KOSDAQ, tiered by % change **and** turnover (거래대금), so you see *real* moves, not 5-share ticks |
| ⚡ | **Upper-limit (상한가) radar** — instantly flags every limit-up name |
| 💰 | **Turnover-weighted** — Tier 1 / Tier 2 filters keep the noise out (defaults: 15%+ & 5%+, with min turnover) |
| 🏦 | **Supply & demand** — institutional / foreign / program trends per name |
| 📰 | **Auto news headlines** — optional Naver Search API pulls the day's headlines behind each pop |
| 🖥️ | **One-click desktop GUI** — a clean PyQt5 launcher, live progress, copy-ready output |
| 📝 | **Optional Notion export** — archive every session to a Notion database |
| 🔒 | **100% local & private** — runs on *your* PC with *your* Kiwoom login. Nothing leaves your machine. |

<div align="center">

*💡 The core board (gainers + turnover + supply/demand) needs **zero API keys** — just your Kiwoom login.*

</div>

---

## 🎬 How it works

```
   ┌──────────────────────┐     ┌─────────────────────────┐     ┌──────────────────────┐
   │  launcher.pyw (GUI)  │ ──▶ │   market_briefing.py    │ ──▶ │  Ranked movers board │
   │  one click, 15:40    │     │  Kiwoom OpenAPI+ TR반환  │     │  + news + 수급 + CSV  │
   └──────────────────────┘     └─────────────────────────┘     └──────────────────────┘
```

1. `launcher.pyw` spawns `market_briefing.py` as a live subprocess (real-time log in the window).
2. `market_briefing.py` logs into your Kiwoom OpenAPI+ session and pulls today's all-market change ranking via TR requests.
3. It filters by your thresholds, enriches each mover with supply/demand + (optionally) news, and prints a ranked board (also saved to CSV).

---

## 🛠️ Installation

> ⚠️ **Windows only.** The Kiwoom OpenAPI+ is a 32-bit ActiveX (OCX) control, so you need **32-bit Python 3.8**. This is a hard requirement from Kiwoom, not us. 🙂

### 1️⃣ Install the Kiwoom OpenAPI+  (키움 Open API+)

1. Open a **Kiwoom Securities account** (an account is required to use the API). → https://www.kiwoom.com
2. Apply for OpenAPI+ use: **키움증권 홈페이지 → 고객서비스 → OpenAPI → OpenAPI+ 사용 신청**.
3. Download & install the module: **OpenAPI 자료실 → "OpenAPI+ 모듈 다운로드"** (installs to `C:\OpenAPI\`).
4. Run **`OpenAPI/opversionup.exe`** once **as Administrator** to pull the latest version (do this if you ever hit a *버전처리* / handle error).
5. Log in to **KOA Studio** or the OpenAPI login once to confirm your ID / password / 공인인증서 work.

> 💡 **Tip — hands-free daily runs:** in the Kiwoom OpenAPI tray icon, enable **자동로그인 (auto-login)** and save your cert password once. After that the tool logs in by itself.

### 2️⃣ Install 32-bit Python 3.8

Easiest path is a dedicated **Miniconda (32-bit)** env:

```bat
:: create a 32-bit Python 3.8 env named "py38_32"
set CONDA_FORCE_32BIT=1
conda create -n py38_32 python=3.8 -y
conda activate py38_32
```

> Verify it's really 32-bit: `python -c "import struct; print(struct.calcsize('P')*8)"` → must print **32**.

### 3️⃣ Install the tool

```bat
git clone https://github.com/<your-username>/kiwoom-daily-gainers.git
cd kiwoom-daily-gainers
conda activate py38_32
pip install -r requirements.txt
```

### 4️⃣ (Optional) Add keys for news / Notion

```bat
copy .env.example .env
:: then edit .env — add your free Naver Search API keys and/or Notion token
```

---

## ▶️ Usage

**GUI (recommended):**

```bat
conda activate py38_32
pythonw launcher.pyw
```
Click **Run**, log in to Kiwoom when prompted, and watch the board fill in.

**Headless / CLI:**

```bat
conda activate py38_32
python market_briefing.py
```
Prints the ranked board to the console and writes `market_briefing_YYYYMMDD.csv`.

**Automate it every weekday at 15:40** (after auto-login is on) with Windows Task Scheduler → point it at `run_local_auto.bat` (edit the paths inside first).

---

## ⚙️ Configuration

All knobs live in [`config.py`](config.py) (thresholds) and `.env` (secrets). A few favorites:

| Setting | Default | Meaning |
|---|---|---|
| `FILTER_MIN_CHANGE` | `5.0` | Only keep stocks up ≥ this % |
| `TIER1_MIN_CHANGE` | `15.0` | Tier 1 bucket cutoff |
| `TIER1_MIN_TRADING_VALUE` | `10 B KRW` | Min turnover to qualify as a *real* Tier-1 move |
| `NEWS_TOP_N` | `100` | Cap news lookups to the top N movers |

---

## 🧯 Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: pykiwoom` / OCX errors | You're on 64-bit Python. Recreate the env with **32-bit** Python 3.8. |
| `"버전처리를 받으시려면..."` / handle errors | Run **`C:\OpenAPI\opversionup.exe` as Administrator**, then retry. |
| Login window keeps popping | Enable **자동로그인** in the Kiwoom tray icon and save the cert password. |
| Keeps asking to join **모의투자 (mock)** | In `C:\OpenAPI\system\opcomms.ini` set `SERVERTYPE=0`, `USE_APIVTS=0`, `IMITATION=` (empty) to use the real server. |
| SSL / `ssl module is not available` (conda) | Launch through `conda activate py38_32` (not the raw `python.exe`) so the conda DLLs load. |

---

## 🗺️ Roadmap

- [ ] DART disclosure catalyst tagging (계약·수주 공시 → 급등 사유 자동 매칭)
- [ ] One-file `.exe` build (no Python setup)
- [ ] English UI toggle
- [ ] Export to Excel / Google Sheets

PRs and issues welcome — see something you'd love? [Open an issue](../../issues). 🙌

---

## ⚠️ Disclaimer

This is an **information & research tool**, not investment advice. It shows *what* moved and surfaces *possible* catalysts; it does not tell you what to buy or sell. Markets are risky — do your own research. The authors are not affiliated with Kiwoom Securities.

## 📄 License

[MIT](LICENSE) — free to use, modify, and share. If it helps you, a ⭐ is the best thank-you. 💛
