"""
Configuration for kiwoom-daily-gainers.

⚠️ NEVER hard-code real secrets here. All credentials come from environment
variables (or a local .env file — see .env.example). This file only holds
non-secret tuning knobs + safe placeholder defaults.
"""
import os

# ─────────────────────────────────────────────────────────────
# Kiwoom OpenAPI+ (used implicitly by the OCX login; usually no key needed
# for the local OpenAPI+ desktop control — kept here for optional REST setups)
# ─────────────────────────────────────────────────────────────
APP_KEY = os.getenv("APP_KEY", "")
APP_SECRET = os.getenv("APP_SECRET", "")
CUST_ID = os.getenv("CUST_ID", "")

# ─────────────────────────────────────────────────────────────
# Naver Search API (OPTIONAL — used to fetch news headlines per stock)
# Get yours free: https://developers.naver.com  →  Register app  →  Search API
# Leave empty to skip news enrichment.
# ─────────────────────────────────────────────────────────────
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# ─────────────────────────────────────────────────────────────
# Notion (OPTIONAL — export the report to a Notion database)
# Leave empty to skip.
# ─────────────────────────────────────────────────────────────
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

# ─────────────────────────────────────────────────────────────
# Screening thresholds  (tweak to taste)
# ─────────────────────────────────────────────────────────────
FILTER_UPPER_LIMIT = 29.9           # upper-limit (상한가) cutoff, %
FILTER_MIN_CHANGE = 5.0             # only keep stocks up >= this %
TIER1_MIN_CHANGE = 15.0            # Tier 1: >= 15%
TIER2_MIN_CHANGE = 5.0             # Tier 2: 5% ~ 15%
TIER1_MIN_TRADING_VALUE = 10_000_000_000   # Tier 1: >= 10.0 B KRW turnover
TIER2_MIN_TRADING_VALUE = 50_000_000_000   # Tier 2: >= 50.0 B KRW turnover
NEWS_SEARCH_THRESHOLD = 3.0        # search news when |change| >= this %
NEWS_TOP_N = 100                   # cap news lookups to top N movers
INVESTOR_TOP_N = 150               # institutional/foreign flow lookups, top N

# 원(KRW) -> 억(0.1 B) style divider used for turnover formatting
TRADING_VALUE_DIVIDER = 10_000_000_000
