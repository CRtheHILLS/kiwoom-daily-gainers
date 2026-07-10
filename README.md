<div align="center">

# 📈 Kiwoom Daily Gainers

### See **every Korean stock that popped today — and *why*** — one click after the close. 🚀
#### 장마감 후, 오늘 급등한 종목과 **그 이유**를 한 번에. 키움 OpenAPI 기반.

<em>A post-market <strong>KOSPI / KOSDAQ surge-stock screener</strong> built on the Kiwoom Securities OpenAPI+.<br/>No paid data feed. No scraping. Runs 100% locally on your own account.</em>

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.8 (32-bit)](https://img.shields.io/badge/Python-3.8%20(32--bit)-blue?logo=python&logoColor=white)](#-installation)
![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![Kiwoom OpenAPI+](https://img.shields.io/badge/Kiwoom-OpenAPI%2B-red)
[![Stars](https://img.shields.io/github/stars/CRtheHILLS/kiwoom-daily-gainers?style=social)](https://github.com/CRtheHILLS/kiwoom-daily-gainers/stargazers)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**⭐ If this saves you 30 minutes of scrolling every evening, a star really helps it reach more investors.**

</div>

---

```text
============================================================
  📈  KIWOOM DAILY GAINERS   ·   2026-07-10 (Fri) close
============================================================
  KOSPI  7,246.79 (-5.35%)     KOSDAQ  785.00 (-5.56%)
  상한가 12  ·  15%+ 9  ·  5%+ 65        (86 movers total)
------------------------------------------------------------
 🥇 TIER 1   change ≥ 15%  &  turnover ≥ 10.0B KRW
  263800  데이타솔루션  +29.98   1,240억   외 -120 / 기 +55 / 개 +71
  058730  다스코        +30.00     903억   외  +81 / 기 -33 / 개 -50
 📰 데이타솔루션 · "삼성SDS와 4,381억 규모 AI 인프라 공급계약"
 📰 다스코       · "그린테크시티 532억 태양광 발전 수주"
============================================================
```
<div align="center"><sub>▲ Illustrative console output — see <a href="examples/sample_output.md">examples/sample_output.md</a>. A real GUI screenshot PR is very welcome! 🙌</sub></div>

---

## 📑 Table of Contents
- [Why this tool?](#-why-this-tool)
- [Features](#-features)
- [How it compares](#-how-it-compares)
- [Installation](#-installation)
- [Usage](#-usage)
- [How it works](#-how-it-works)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap) · [Contributing](#-contributing) · [Disclaimer](#-disclaimer) · [License](#-license)

---

## 💡 Why this tool?

Every trading day at the close, Korean retail investors ask the same question:

> *"오늘 뭐가 올랐고, **왜 올랐지?** / What moved today, and **what was the catalyst?**"*

Answering that by hand means bouncing between the HTS, Naver Finance, news portals, and DART. **This tool does it in seconds** — straight from *your own* Kiwoom account.

**How it's different from `pykiwoom` / `koapy` / `pykrx`:** those are excellent *raw-data wrappers*. This is a **finished, one-click product** on top of them — it doesn't just hand you a dataframe, it **ranks today's real movers, weights them by turnover, pulls the supply/demand & news behind each pop, and gives you a ready-to-read board.** Batteries included.

---

## ✨ Features

| | Feature |
|---|---|
| 🥇 | **Ranked gainers board** — KOSPI + KOSDAQ, tiered by % change **and** turnover (거래대금), so you see *real* moves, not 5-share ticks |
| ⚡ | **Upper-limit (상한가) radar** — instantly flags every limit-up name |
| 🏦 | **Supply & demand** — institutional / foreign / program net flow per stock |
| 📰 | **Auto news headlines** — optional Naver Search API surfaces the catalyst behind each pop |
| 🖥️ | **One-click desktop GUI** — a clean PyQt5 launcher with live progress |
| 📊 | **CSV export** — every session saved as `market_briefing_YYYYMMDD.csv` |
| 📝 | **Optional Notion export** — archive sessions to a Notion database |
| 🔒 | **100% local & private** — your PC, your Kiwoom login. Nothing leaves your machine. |

> 💡 The core board (gainers + turnover + supply/demand) needs **zero API keys** — just your Kiwoom login.

---

## ⚖️ How it compares

| | Manual (HTS + portals) | `pykiwoom` / `koapy` (raw) | **Kiwoom Daily Gainers** |
|---|:---:|:---:|:---:|
| Today's ranked movers | 🟡 scroll & sort | 🟡 you code it | ✅ one click |
| Turnover-weighted tiers | 🟡 manual | ❌ | ✅ |
| Upper-limit radar | 🟡 | ❌ | ✅ |
| Supply/demand per stock | 🟡 many clicks | 🟡 you code it | ✅ |
| News catalyst attached | ❌ separate search | ❌ | ✅ optional |
| Desktop GUI | — | ❌ library only | ✅ |
| Setup | none | pip | pip + this |

---

## 🛠️ Installation

> ⚠️ **Windows only.** The Kiwoom OpenAPI+ is a 32-bit ActiveX (OCX) control, so you need **32-bit Python 3.8**. This is Kiwoom's requirement, not ours. 🙂

### 1️⃣ Install the Kiwoom OpenAPI+ (키움 Open API+)

1. Open a **Kiwoom Securities account** (required to use the API) → https://www.kiwoom.com
2. Apply for OpenAPI+ use: **키움증권 → 고객서비스 → OpenAPI → OpenAPI+ 사용 신청**.
3. Download & install the module (**OpenAPI 자료실 → "OpenAPI+ 모듈 다운로드"**) → installs to `C:\OpenAPI\`.
4. Run **`C:\OpenAPI\opversionup.exe` as Administrator** once (fixes any *버전처리* / handle errors).
5. Log in via KOA Studio or the OpenAPI login once to confirm your ID / password / 공인인증서.

> 💡 **Hands-free daily runs:** in the Kiwoom OpenAPI tray icon, enable **자동로그인 (auto-login)** and save your cert password once. After that the tool logs in by itself.

### 2️⃣ Install 32-bit Python 3.8 (via Miniconda)

```bat
set CONDA_FORCE_32BIT=1
conda create -n py38_32 python=3.8 -y
conda activate py38_32
```
Verify it's really 32-bit: `python -c "import struct;print(struct.calcsize('P')*8)"` → must print **32**.

### 3️⃣ Install the tool

```bat
git clone https://github.com/CRtheHILLS/kiwoom-daily-gainers.git
cd kiwoom-daily-gainers
conda activate py38_32
pip install -r requirements.txt
```

### 4️⃣ (Optional) news / Notion keys

```bat
copy .env.example .env
:: edit .env — add your free Naver Search API keys and/or Notion token
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
Prints the ranked board and writes `market_briefing_YYYYMMDD.csv`. → see [examples/sample_output.md](examples/sample_output.md).

**Automate at 15:40 every weekday** (once auto-login is on): edit the paths in `run_local_auto.bat`, then point Windows Task Scheduler at it.

---

## 🎬 How it works

```
   ┌──────────────────────┐     ┌─────────────────────────┐     ┌──────────────────────┐
   │  launcher.pyw (GUI)  │ ──▶ │   market_briefing.py    │ ──▶ │  Ranked movers board │
   │  one click @ 15:40   │     │  Kiwoom OpenAPI+ TR반환  │     │  + 수급 + news + CSV  │
   └──────────────────────┘     └─────────────────────────┘     └──────────────────────┘
```
1. `launcher.pyw` spawns `market_briefing.py` as a live subprocess (real-time log in the window).
2. `market_briefing.py` logs into your Kiwoom OpenAPI+ session and pulls today's all-market change ranking via TR requests.
3. It filters by your thresholds, enriches each mover with supply/demand + (optionally) news, and prints a ranked board (also saved to CSV).

---

## ⚙️ Configuration

Thresholds live in [`config.py`](config.py); secrets in `.env`. Favorites:

| Setting | Default | Meaning |
|---|---|---|
| `FILTER_MIN_CHANGE` | `5.0` | Only keep stocks up ≥ this % |
| `TIER1_MIN_CHANGE` | `15.0` | Tier 1 bucket cutoff |
| `TIER1_MIN_TRADING_VALUE` | `10 B KRW` | Min turnover for a *real* Tier-1 move |
| `NEWS_TOP_N` | `100` | Cap news lookups to the top N movers |

---

## 🧯 Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: pykiwoom` / OCX errors | You're on 64-bit Python. Recreate the env with **32-bit** Python 3.8. |
| `"버전처리를 받으시려면..."` / handle errors | Run **`C:\OpenAPI\opversionup.exe` as Administrator**, then retry. |
| Login window keeps popping | Enable **자동로그인** in the Kiwoom tray icon and save the cert password. |
| Keeps asking to join **모의투자 (mock)** | In `C:\OpenAPI\system\opcomms.ini` set `SERVERTYPE=0`, `USE_APIVTS=0`, `IMITATION=` (empty). |
| `ssl module is not available` (conda) | Launch through `conda activate py38_32` so the conda DLLs load. |

---

## 🗺️ Roadmap
- [ ] DART disclosure catalyst tagging (계약·수주 공시 → 급등 사유 자동 매칭)
- [ ] One-file `.exe` build (no Python setup)
- [ ] English UI toggle
- [ ] Export to Excel / Google Sheets

See [CHANGELOG.md](CHANGELOG.md) for release history.

## 📈 Star history

<a href="https://star-history.com/#CRtheHILLS/kiwoom-daily-gainers&Date">
  <img src="https://api.star-history.com/svg?repos=CRtheHILLS/kiwoom-daily-gainers&type=Date" alt="Star History Chart" width="600">
</a>

## 🤝 Contributing
PRs and issues welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). A real GUI screenshot/GIF is the single most valuable contribution right now. 🙌

## ⚠️ Disclaimer
This is an **information & research tool, not investment advice.** It shows *what* moved and surfaces *possible* catalysts; it does not tell you what to buy or sell. Markets are risky — do your own research. Not affiliated with Kiwoom Securities. 투자 손실에 대한 책임은 이용자 본인에게 있습니다.

## 📄 License
[MIT](LICENSE) — free to use, modify, and share. A ⭐ is the best thank-you. 💛

---

<div align="center"><sub>

**Keywords:** Korean stock screener · KOSPI screener · KOSDAQ screener · Kiwoom OpenAPI · 키움 OpenAPI · 급등주 · 상한가 · 장마감 급등주 · 주식 스크리너 · surge stock scanner · after-market gainers · 거래대금 · 수급 · Korean stock market · KRX · day trading Korea · stock catalyst finder

</sub></div>
