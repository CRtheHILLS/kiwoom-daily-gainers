# Contributing to Kiwoom Daily Gainers 🙌

Thanks for taking the time to contribute! This project thrives on community input from Korean-market retail investors and Python tinkerers alike.

## Ways to help

- 🐛 **Report a bug** — open an [issue](../../issues) with your OS, Python arch (32/64-bit), and the full traceback.
- 💡 **Request a feature** — tell us the workflow you wish existed.
- 📖 **Improve the docs** — the Kiwoom install flow is fiddly; clearer steps help everyone.
- 🌐 **Translate** — an English UI or fully-English README PR is very welcome.
- ⭐ **Star the repo** — the simplest way to help it reach more people.

## Dev setup

```bat
:: 32-bit Python 3.8 is REQUIRED (Kiwoom OpenAPI+ is a 32-bit OCX)
set CONDA_FORCE_32BIT=1
conda create -n py38_32 python=3.8 -y
conda activate py38_32
pip install -r requirements.txt
```

## Pull requests

1. Fork → create a branch (`git checkout -b feat/my-thing`).
2. Keep changes focused; match the existing style.
3. Don't commit secrets. `.env` is git-ignored — keep it that way. Never hard-code keys in `config.py`.
4. Describe **what** and **why** in the PR. Screenshots for UI changes are gold.

## Ground rules

- Be kind and constructive. 🇰🇷🌏
- This is a research/information tool, **not** investment advice — keep contributions in that spirit.

Happy hacking! 📈
