r"""
c:\Users\droli\kiwoom-projects\daily-briefing\market_briefing.py
일일 시장 브리핑 시스템 (Phase 1: Data Collection & CSV Backup)
"""
import sys
import time
import io
from contextlib import redirect_stdout

# 윈도우 한국어 환경 CP949 인코딩 오류 방지 + 실시간 출력(라인 버퍼링)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
import re
import json
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from notion_client import Client
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from PyQt5.QtWidgets import QApplication
from pykiwoom.kiwoom import Kiwoom
import config

# 로깅 설정: Python 3.8 환경에서 `basicConfig`의 `encoding` 인자가 지원되지 않아
# FileHandler를 직접 생성해서 인코딩을 지정합니다.
log_filename = f"briefing_{datetime.now().strftime('%Y%m%d')}.log"
handler = logging.FileHandler(log_filename, encoding='utf-8')
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

def fix_text(text):
    """
    Fix broken Korean text (Mojibake) caused by encoding mismatch.
    (Latin-1 mapped bytes -> CP949)
    """
    try:
        return text.encode('latin1').decode('cp949')
    except:
        return text

class MarketBriefing:
    def __init__(self):
        self.kiwoom = None
        self.today = datetime.now().strftime("%Y%m%d")
        self.data_list = []

    def login(self):
        """키움증권 로그인"""
        print("[로그인] 키움증권 로그인 시도...")
        print("[로그인] *** 키움 로그인 창이 열립니다. 작업표시줄을 확인하고 로그인해주세요 ***")
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)
        print("[로그인] 로그인 성공")
        logging.info("Kiwoom Connected")

    def fetch_all_stocks_sequentially(self):
        """
        전종목 조회 후 메모리 필터링 방식 (User Preferred Method)
        - opt10001 반복 조회
        - 등락률 +29% ~ 5%
        - 거래대금: 15% 이상은 100억+, 5%~15%는 500억+
        """
        print("\n🚀 전종목 시세 조회 및 필터링 시작 (opt10001 Loop)...")
        
        # 1. 전체 종목 코드 가져오기
        kospi = self.kiwoom.GetCodeListByMarket("0")
        kosdaq = self.kiwoom.GetCodeListByMarket("10")
        all_codes = kospi + kosdaq
        
        print(f"  - 총 종목 수: {len(all_codes)}개")

        stocks = []
        total = len(all_codes)
        
        # 2. 순차 조회
        for i, code in enumerate(all_codes):
            # 진행 상황 출력 (100개 단위)
            if (i + 1) % 100 == 0:
                print(f"  [{i+1}/{total}] 진행 중... (수집된 종목: {len(stocks)}개)")

            # [최적화] 종목명 미리 확인하여 불필요한 종목(SPAC, ETN 등) Skip
            name = self.kiwoom.GetMasterCodeName(code)
            
            # [필터] 특정 키워드 제외 (API 호출 전 1차 필터링으로 속도 향상)
            exclude_keywords = [
                "TIGER", "ETN", "KODEX", "HANARO", "RISE", "S&P", "KoAct",
                "미국", "채권", "배당", "글로벌",
                "스팩", "SPAC", "ACE", "리츠", "액티브", "SOL", "KBSTAR", "ARIRANG",
                "레버리지", "인버스", "곱버스", "2X", "3X", "PLUS", "FOCUS",
                "ETF", "선물", "지수"
            ]
            if any(k in name for k in exclude_keywords):
                continue
            # 우선주 제외 (종목코드 끝자리가 0이 아니면 보통 우선주/워런트)
            if not code.endswith("0"):
                continue

            # 3. 데이터 조회 (opt10001)
            # 1초당 5회 제한 고려 -> 0.25초 대기
            time.sleep(0.25)
            
            with redirect_stdout(io.StringIO()):
                df = self.kiwoom.block_request(
                    "opt10001",
                    종목코드=code,
                    output="주식기본정보",
                    next=0
                )

            if df is None or df.empty:
                continue

            try:
                row = df.iloc[0]
                name = fix_text(row['종목명'])
                price = abs(int(row['현재가']))
                volume = int(row['거래량'])
                
                # [개선] 등락률 파싱 (가독성 및 안전성 확보)
                raw_rate = str(row['등락율']).strip()
                if raw_rate.startswith('+'):
                    raw_rate = raw_rate[1:]
                change_rate = float(raw_rate)
                
                # [개선] 거래대금 계산
                # opt10001의 '거래대금' 필드는 보통 '백만' 단위입니다.
                # 필드가 존재하면 우선 사용하고(단위 보정), 없으면 계산값(price*volume)을 사용합니다.
                trading_value_won = price * volume # Default fallback
                if '거래대금' in row:
                    trading_value_won = int(row['거래대금']) * 1_000_000

                # PER 추출
                per_val = 0.0
                if 'PER' in row:
                    try:
                        per_str = str(row['PER']).replace(',', '').strip()
                        if per_str and per_str not in ('', '-', 'N/A', '--', '0'):
                            per_val = abs(float(per_str))
                    except Exception:
                        per_val = 0.0

                # [메모리 필터링] 3단계
                # - 상한가(≥29.9%): 거래대금 무관 전체 표시
                # - 15% ~ 상한가 미만: 거래대금 100억+
                # - 5% ~ 15%: 거래대금 500억+
                if change_rate >= config.FILTER_UPPER_LIMIT:
                    # 상한가: 거래대금 무관
                    passes_filter = True
                elif change_rate >= config.TIER1_MIN_CHANGE:
                    passes_filter = trading_value_won >= config.TIER1_MIN_TRADING_VALUE
                elif change_rate >= config.TIER2_MIN_CHANGE:
                    passes_filter = trading_value_won >= config.TIER2_MIN_TRADING_VALUE
                else:
                    passes_filter = False

                if passes_filter:

                    trading_value_eok = trading_value_won / 100_000_000
                    trading_value_billions = trading_value_won / 1_000_000_000

                    stocks.append({
                        "code": code,
                        "name": name,
                        "price": price,
                        "change_rate": change_rate,
                        "volume": volume,
                        "trading_value": round(trading_value_eok, 2),
                        "trading_value_won": trading_value_won,
                        "trading_value_billions": round(trading_value_billions, 3),
                        "per": per_val,
                        "reason": "",
                        "headline": "",
                        "investor_info": "",
                        "link": "-"
                    })
            except Exception:
                continue

        return stocks

    # ──────────────────────────────────────────────────────────
    #  뉴스/상승 이유 검색
    #  1순위: 네이버 Open API (공식, 안정적)
    #  2순위: 네이버 HTML 크롤링 (fallback)
    # ──────────────────────────────────────────────────────────
    WEB_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36'
    }

    def _has_naver_api_key(self):
        """네이버 API 키 설정 여부 확인"""
        return bool(getattr(config, 'NAVER_CLIENT_ID', '') and
                    getattr(config, 'NAVER_CLIENT_SECRET', ''))

    def search_naver_api(self, name, query_suffix="특징주", max_days=1):
        """
        [공식 API] 네이버 검색 Open API를 사용한 뉴스 검색
        - 종목명이 제목에 포함된 기사만 반환 (단순 언급 기사 제외)
        - max_days: 최근 N일 이내 기사만 허용 (None이면 날짜 제한 없음)
        - 반환: (reason, link, headline) - reason=짧은 이유, headline=전체 제목
        """
        if not self._has_naver_api_key():
            return None, None, None
        try:
            query = quote_plus(f"{name} {query_suffix}".strip())
            url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=20&sort=date"
            headers = {
                'X-Naver-Client-Id': config.NAVER_CLIENT_ID,
                'X-Naver-Client-Secret': config.NAVER_CLIENT_SECRET,
            }
            resp = requests.get(url, headers=headers, timeout=8)
            resp.raise_for_status()
            data = resp.json()

            cutoff = (datetime.now() - timedelta(days=max_days)) if max_days is not None else None

            for item in data.get('items', []):
                # 날짜 필터
                if cutoff:
                    try:
                        pub_dt = parsedate_to_datetime(item.get('pubDate', ''))
                        pub_dt = pub_dt.replace(tzinfo=None)
                        if pub_dt < cutoff:
                            continue
                    except Exception:
                        pass  # 날짜 파싱 실패 시 포함

                # HTML 태그 제거 (<b>, </b> 등)
                title = re.sub(r'<[^>]+>', '', item.get('title', '')).strip()
                link = item.get('link') or item.get('originallink', '')

                if not title or len(title) <= 2:
                    continue

                # [핵심] 종목명이 제목에 포함돼야 함 — 단순 언급 기사 제외
                if name not in title:
                    continue

                reason = self._extract_reason_from_title(title, name)
                return reason, link, title  # reason=짧은이유, link=URL, title=전체헤드라인

            return None, None, None
        except Exception as e:
            logging.error(f"Naver API search error for {name}: {e}")
            return None, None, None

    def _extract_reason_from_title(self, title, name):
        """
        특징주 기사 제목에서 상승 이유만 추출
        예: "[특징주] 삼성전자, 반도체 호황에 5% 급등" → "반도체 호황"
        """
        # 종목명, 특징주 태그, 등락률 제거
        reason = title
        for remove in ['[특징주]', '[마감특징주]', '[오전특징주]', '[장중특징주]',
                       '[시황]', '[코스닥]', '[코스피]', name]:
            reason = reason.replace(remove, '')

        # "~에 급등", "~에 상승", "~로 강세" 등에서 이유 부분만 추출
        import re
        # "~에 N% 급등" 패턴에서 "~" 부분 추출
        m = re.search(r'[,\s](.+?)(?:에\s*\d|으로\s*\d|로\s*\d|\d+%)', reason)
        if m:
            reason = m.group(1).strip()
        else:
            # 쉼표 이후 첫 문장 추출
            parts = reason.split(',')
            if len(parts) > 1:
                reason = parts[1].strip()
            else:
                reason = reason.strip()

        # 퍼센트, 특수문자 정리
        reason = re.sub(r'\d+(\.\d+)?%', '', reason)
        reason = re.sub(r'[…\-\|]', '', reason)
        reason = reason.strip(' ,.')

        if not reason or len(reason) < 2:
            return title.strip()[:25]

        if len(reason) > 25:
            reason = reason[:22] + "..."
        return reason

    def search_naver_featured(self, name, recent_only=False):
        """
        [Tier 1] 네이버 뉴스에서 '종목명 특징주' 검색
        특징주 기사는 상승/하락 이유를 제목에 직접 포함하므로 가장 정확함
        recent_only=True면 날짜 제한 없이 최근 기사 검색
        """
        try:
            query = quote_plus(f"{name} 특징주")
            # sort=1: 최신순 정렬
            url = f"https://search.naver.com/search.naver?where=news&query={query}&sort=1"
            resp = requests.get(url, headers=self.WEB_HEADERS, timeout=8)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            today_str = datetime.now().strftime("%Y.%m.%d")
            # 네이버 뉴스 검색 결과에서 기사 추출
            for item in soup.select('.news_area'):
                title_tag = item.select_one('.news_tit')
                info_tag = item.select_one('.info_group')
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                link = title_tag.get('href', '')

                # 날짜 확인 (당일 기사만 필터링, recent_only면 스킵)
                if not recent_only and info_tag:
                    info_text = info_tag.get_text()
                    # "n시간 전", "n분 전" → 당일 기사
                    is_today = ('시간 전' in info_text or '분 전' in info_text
                                or today_str in info_text)
                    if not is_today:
                        continue

                if '특징주' in title or name in title:
                    reason = self._extract_reason_from_title(title, name)
                    return reason, link

            return None, None
        except Exception as e:
            logging.error(f"Naver featured search error for {name}: {e}")
            return None, None

    def get_naver_stock_news(self, code):
        """
        [Tier 2] 네이버 금융 종목별 뉴스 페이지 크롤링
        해당 종목의 당일 뉴스 헤드라인 추출
        """
        try:
            url = f"https://finance.naver.com/item/news.naver?code={code}&page=1"
            resp = requests.get(url, headers=self.WEB_HEADERS, timeout=8)
            resp.encoding = 'euc-kr'
            soup = BeautifulSoup(resp.text, 'html.parser')

            today_str = datetime.now().strftime("%Y.%m.%d")

            # 뉴스 테이블에서 기사 추출
            for row in soup.select('table.type5 tr'):
                cols = row.select('td')
                if len(cols) < 2:
                    continue

                title_tag = row.select_one('td.title a')
                date_tag = row.select_one('td.date')

                if not title_tag or not date_tag:
                    continue

                date_text = date_tag.get_text(strip=True)
                if today_str not in date_text:
                    continue

                title = title_tag.get_text(strip=True)
                href = title_tag.get('href', '')
                if href and not href.startswith('http'):
                    href = 'https://finance.naver.com' + href

                if title and len(title) > 3:
                    # 제목을 25자 이내로 요약
                    reason = title[:25] + "..." if len(title) > 25 else title
                    return reason, href

            return None, None
        except Exception as e:
            logging.error(f"Naver stock news error for {code}: {e}")
            return None, None

    def find_stock_reason(self, code, name):
        """
        종목 상승 이유 검색 — (reason, link, headline) 반환
        - reason: 터미널용 짧은 이유 (25자)
        - headline: 런처용 전체 뉴스 제목 (클릭 링크)
        - link: 기사 URL

        [API 모드 — NAVER_CLIENT_ID 설정 시, 4단계]
          1. "{name} 특징주" — 당일 기사, 종목명 제목 포함 필수
          2. "{name}" — 최근 5일 기사, 종목명 제목 포함 필수
          3. "{name} 특징주" — 날짜 무제한, 종목명 제목 포함 필수
          4. "{name}" — 날짜 무제한 (최후 fallback)

        [스크래핑 모드 — API 키 없을 때]
          1~3단계 HTML 크롤링
        """
        naver_link = f"https://finance.naver.com/item/main.naver?code={code}"

        if self._has_naver_api_key():
            # ── API 모드 ──
            # 1단계: 특징주 당일 기사 (종목명 제목 포함 필수)
            reason, link, headline = self.search_naver_api(name, query_suffix="특징주", max_days=1)
            if reason:
                return reason, link or naver_link, headline
            time.sleep(0.2)

            # 2단계: 최근 5일 일반 뉴스 (주말 포함, 종목명 제목 포함 필수)
            reason, link, headline = self.search_naver_api(name, query_suffix="", max_days=5)
            if reason:
                return reason, link or naver_link, headline
            time.sleep(0.2)

            # 3단계: 과거 특징주 기사 (날짜 무제한, 종목명 제목 포함 필수)
            reason, link, headline = self.search_naver_api(name, query_suffix="특징주", max_days=None)
            if reason:
                return f"(과거){reason}", link or naver_link, headline
            time.sleep(0.2)

            # 4단계: 과거 일반 뉴스 (날짜 무제한, 최후 fallback)
            reason, link, headline = self.search_naver_api(name, query_suffix="", max_days=None)
            if reason:
                return f"(과거){reason}", link or naver_link, headline

        else:
            # ── 스크래핑 모드 (API 키 없을 때) ──
            reason, link = self.search_naver_featured(name, recent_only=False)
            if reason:
                return reason, link or naver_link, None
            time.sleep(0.3)

            reason, link = self.get_naver_stock_news(code)
            if reason:
                return reason, link or naver_link, None
            time.sleep(0.3)

            reason, link = self.search_naver_featured(name, recent_only=True)
            if reason:
                return f"(과거){reason}", link or naver_link, None

        return "특이사항없음", naver_link, None

    def find_reasons(self, df):
        """
        Phase 2: 상승/하락 이유 수집 (네이버 API 4단계 전략)
        """
        top_n = min(config.NEWS_TOP_N, len(df))
        api_mode = "네이버 Open API" if self._has_naver_api_key() else "HTML 크롤링"
        print(f"\n📰 상위 {top_n}개 종목 뉴스 검색 시작 ({api_mode})...")
        reasons = []
        links = []
        headlines = []

        for idx, (_, row) in enumerate(df.iloc[:top_n].iterrows()):
            if (idx + 1) % 5 == 0 or idx == 0:
                print(f"  [{idx+1}/{top_n}] 뉴스 검색 중... ({row['name']})")
            reason, link, headline = self.find_stock_reason(row['code'], row['name'])
            reasons.append(reason)
            links.append(link)
            headlines.append(headline or "")
            time.sleep(0.2)

        # 나머지 빈칸 채우기
        for _, row in df.iloc[top_n:].iterrows():
            reasons.append("")
            links.append(f"https://finance.naver.com/item/main.naver?code={row['code']}")
            headlines.append("")

        df['reason'] = reasons
        df['link'] = links
        df['headline'] = headlines
        print(f"  ✅ 뉴스 검색 완료 ({top_n}개 종목)")
        return df

    # ──────────────────────────────────────────────────────────
    #  투자자 동향 (기관/외인 연속 순매수 + 프로그램)
    # ──────────────────────────────────────────────────────────

    def fetch_program_trading(self):
        """
        opt90003: 프로그램순매수상위50요청 → {종목코드: 순위} dict
        코스피(P00101), 코스닥(P10102) 각각 조회 후 합산

        출력레코드: 프로그램순매수상위50
        컬럼: 순위, 종목코드, 종목명, 현재가, 등락기호, 전일대비, 등락율,
              누적거래량, 프로그램매도금액, 프로그램매수금액, 프로그램순매수금액
        """
        prog_rank = {}
        for market_code in ["P00101", "P10102"]:   # P00101=코스피, P10102=코스닥
            try:
                with redirect_stdout(io.StringIO()):
                    df_prog = self.kiwoom.block_request(
                        "opt90003",
                        매매상위구분="2",   # 2=순매수상위
                        금액수량구분="1",   # 1=금액 기준
                        시장구분=market_code,
                        output="프로그램순매수상위50",
                        next=0
                    )
                if df_prog is None or df_prog.empty:
                    continue

                for rank, (_, prow) in enumerate(df_prog.iterrows(), start=1):
                    code = str(prow.get('종목코드', '')).strip().zfill(6)
                    if code and code != '000000' and code not in prog_rank:
                        prog_rank[code] = rank
            except Exception as e:
                logging.error(f"opt90003({market_code}) error: {e}")
        return prog_rank

    def fetch_investor_streak(self, code):
        """
        opt10045: 종목별기관매매추이요청 → 연속 순매수 분석
        Returns dict(inst_streak, foreign_streak, inst_net_qty, foreign_net_qty) or None

        출력레코드: 종목별기관매매추이
        핵심 컬럼: 기관일별순매매수량, 외인일별순매매수량 (양수=순매수, 음수=순매도)
        데이터 정렬: 최신→과거 (head(10)이 최근 10거래일)
        """
        try:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            with redirect_stdout(io.StringIO()):
                df_inv = self.kiwoom.block_request(
                    "opt10045",
                    종목코드=code,
                    시작일자=start_date,
                    종료일자=self.today,
                    기관추정단가구분="1",  # 1=매수단가
                    외인추정단가구분="1",  # 1=매수단가
                    output="종목별기관매매추이",
                    next=0
                )
            if df_inv is None or df_inv.empty:
                return None

            def to_num(col):
                if col not in df_inv.columns:
                    return pd.Series([0.0] * len(df_inv))
                s = df_inv[col].astype(str).str.replace(',', '').str.strip()
                return pd.to_numeric(s, errors='coerce').fillna(0.0)

            inst_qty = to_num('기관일별순매매수량')
            for_qty  = to_num('외인일별순매매수량')

            # 최신→과거 순 → head(10) = 최근 10거래일
            recent_inst = inst_qty.head(10)
            recent_for  = for_qty.head(10)

            def count_streak(series):
                """최근부터 연속 순매수 일수 (양수인 날 연속 카운트)"""
                streak = 0
                for val in series:
                    if val > 0:
                        streak += 1
                    else:
                        break
                return streak

            return {
                'inst_streak':    count_streak(recent_inst),
                'foreign_streak': count_streak(recent_for),
                'inst_net_qty':   int(recent_inst.sum()),
                'foreign_net_qty': int(recent_for.sum()),
            }
        except Exception as e:
            logging.error(f"opt10045 error for {code}: {e}")
            return None

    def build_investor_line(self, code, per, inv_data, prog_rank):
        """
        기관/외인 연속 순매수 + 프로그램 정보 → 이모지 표시 문자열 생성
        🔥: 5일+ 연속  💰: 10만주+  ⚡: 프로그램 상위20  🚫: 순매도  ⚠️: PER100+
        """
        parts = []

        if inv_data:
            inst_s   = inv_data.get('inst_streak', 0)
            for_s    = inv_data.get('foreign_streak', 0)
            inst_qty = inv_data.get('inst_net_qty', 0)
            for_qty  = inv_data.get('foreign_net_qty', 0)

            # 기관
            if inst_s >= 5:
                qty_str = (f"+{inst_qty // 10000}만주" if abs(inst_qty) >= 10000
                           else f"+{inst_qty:,}주")
                parts.append(f"🔥기관{inst_s}일연속💰{qty_str}")
            elif inst_s >= 3:
                parts.append(f"💰기관{inst_s}일+")
            elif inst_qty < 0 and inst_s == 0:
                parts.append("🚫기관순매도")

            # 외인
            if for_s >= 5:
                qty_str = (f"+{for_qty // 10000}만주" if abs(for_qty) >= 10000
                           else f"+{for_qty:,}주")
                parts.append(f"🔥외인{for_s}일연속💰{qty_str}")
            elif for_s >= 3:
                parts.append(f"💰외인{for_s}일+")
            elif for_qty < 0 and for_s == 0:
                parts.append("🚫외인순매도")

        # 프로그램 순매수 상위20
        prog_r = prog_rank.get(code)
        if prog_r and prog_r <= 20:
            parts.append(f"프로그램{prog_r}위⚡")

        # PER 고평가 경고
        if per and per >= 100:
            parts.append(f"PER{per:.0f}⚠️")

        return " | ".join(parts)

    def find_investor_info(self, df):
        """
        Phase 2b: 기관/외인 연속 순매수 + 프로그램 동향 수집
        상위 INVESTOR_TOP_N개 종목만 조회 (속도 고려)
        """
        top_n = min(getattr(config, 'INVESTOR_TOP_N', 50), len(df))
        print(f"\n📊 상위 {top_n}개 종목 투자자 동향 조회 시작 (opt10045 + opt90003)...")

        # opt90003: 프로그램매매 1회 조회 (전체 시장)
        prog_rank = self.fetch_program_trading()
        time.sleep(0.3)

        investor_infos = []
        for idx, (_, row) in enumerate(df.iloc[:top_n].iterrows()):
            inv_data = self.fetch_investor_streak(row['code'])
            per = float(row.get('per', 0) or 0)
            inv_line = self.build_investor_line(row['code'], per, inv_data, prog_rank)
            investor_infos.append(inv_line)
            time.sleep(0.25)
            if (idx + 1) % 10 == 0:
                print(f"  [{idx+1}/{top_n}] 투자자 동향 조회 중...")

        # 나머지 종목은 빈값
        for _ in range(len(df) - top_n):
            investor_infos.append("")

        df = df.copy()
        df['investor_info'] = investor_infos
        print(f"  ✅ 투자자 동향 조회 완료 ({top_n}개 종목)")
        return df

    def upload_to_notion(self, df):
        """
        Phase 3: Notion 업로드
        """
        print("\n🚀 Notion 업로드 시작...")
        
        if not config.NOTION_API_KEY or "secret" in config.NOTION_API_KEY:
            print("⚠️ Notion API Key가 설정되지 않았습니다. config.py를 확인하세요.")
            return

        notion = Client(auth=config.NOTION_API_KEY)
        database_id = config.NOTION_DATABASE_ID
        
        count = 0
        for _, row in df.iterrows():
            try:
                # 등락률에 따른 이모지
                emoji = "➖"
                if row['change_rate'] >= config.FILTER_UPPER_LIMIT:
                    emoji = "🔴"  # 상한가
                elif row['change_rate'] > 0:
                    emoji = "🔺"
                else:
                    emoji = "🔹"

                # 거래대금(억) - 사용자 설정에 따라 변환된 값 사용
                notion_trading_value = None
                try:
                    notion_trading_value = float(row.get('trading_value', 0))
                except Exception:
                    notion_trading_value = 0

                notion.pages.create(
                    parent={"database_id": database_id},
                    properties={
                        "종목명": {"title": [{"text": {"content": row['name']}}]},
                        "등락률": {"number": round(row['change_rate'], 2)},
                        "현재가": {"number": row['price']},
                        "거래대금(억)": {"number": notion_trading_value},
                        "이유/뉴스": {"rich_text": [{"text": {"content": row['reason'] or "-"}}]},
                        "상태": {"select": {"name": emoji}}
                    }
                )
                count += 1
                if count % 10 == 0:
                    print(f"  {count}개 업로드 완료...")
                    
            except Exception as e:
                logging.error(f"Notion upload failed for {row['name']}: {e}")
                print(f"❌ {row['name']} 업로드 실패: {e}")

        print(f"✅ 총 {count}개 종목 Notion 업로드 완료!")

    def print_results(self, df):
        """터미널에 종목명 / 등락률 / 거래대금 / 상승 이유 출력"""
        today_fmt = datetime.now().strftime("%Y-%m-%d %H:%M")
        print("\n")
        print("=" * 100)
        print(f"  Daily Market Briefing  |  {today_fmt}")
        print(f"  [상한가(29.9%+)] 거래대금 무관  |  [15%~상한가] 100억+  |  [5%~15%] 500억+")
        print("=" * 100)

        if df.empty:
            print("  조건에 맞는 종목 없음")
            print("=" * 100)
            return

        # 헤더
        print(f"  {'#':>3}  {'종목명':<14} {'등락률':>8} {'거래대금':>10}  {'상승 이유 (특징주)'}")
        print("  " + "-" * 94)

        for i, row in enumerate(df.itertuples(index=False), start=1):
            name_display = f"{row.name}({row.code[-4:]})"
            rate_str = f"+{row.change_rate:.2f}%"
            tv_str = f"{row.trading_value:,.0f}억"
            reason = row.reason if row.reason else "-"
            # 상한가 표시
            tag = "[상한가]" if row.change_rate >= config.FILTER_UPPER_LIMIT else "        "
            print(f"  {i:>3}  {name_display:<14} {rate_str:>8} {tv_str:>10}  {tag}  {reason}")
            # 투자자 동향 (기관/외인/프로그램) — 데이터 있을 때만 표시
            inv_info = getattr(row, 'investor_info', '')
            if inv_info:
                print(f"           └─ {inv_info}")

        print("  " + "-" * 94)
        print(f"  총 {len(df)}개 종목")
        print("=" * 100)

        # ── GUI 런처용 머신리더블 출력 (런처가 파싱해 클릭 가능한 링크로 렌더링) ──
        print("[RESULTS_START]")
        for row in df.itertuples(index=False):
            is_upper = row.change_rate >= config.FILTER_UPPER_LIMIT
            headline_val = getattr(row, 'headline', '') or ''
            result = {
                "code": row.code,
                "name": row.name,
                "rate": round(row.change_rate, 2),
                "tv": round(row.trading_value, 0),
                "reason": (row.reason or "").strip(),
                "headline": headline_val.strip(),  # 전체 뉴스 제목 (클릭용)
                "link": (row.link or "").strip(),
                "upper": is_upper,
                "investor_info": getattr(row, 'investor_info', ''),
            }
            print(f"[RESULT]{json.dumps(result, ensure_ascii=False)}")
        print("[RESULTS_END]")

    def save_local_csv(self, df):
        """로컬 CSV 백업 (순수 저장 기능만 수행)"""

        if df.empty:
            print("⚠️ 저장할 데이터가 없습니다.")
            return

        df_to_save = df.copy()

        # Normalize trading value for CSV only (leave original df intact for Notion upload)
        # If raw 'trading_value_won' is present, use it; otherwise try to reconstruct
        if 'trading_value_won' in df_to_save.columns:
            trading_value_raw = df_to_save['trading_value_won'].astype(float)
        else:
            # assume existing 'trading_value' might be in 억 (as earlier), convert back to 원
            trading_value_raw = df_to_save['trading_value'].astype(float) * 100_000_000

        # Apply user-configured divider to produce the CSV field value
        df_to_save['trading_value'] = trading_value_raw / config.TRADING_VALUE_DIVIDER

        # CSV 저장
        filename = f"market_briefing_{self.today}.csv"
        df_to_save.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 로컬 백업 완료: {filename}")
        logging.info(f"Saved to {filename}")

    def run(self):
        """전체 프로세스 실행 (수동 실행 전용)"""
        # 2. 로그인
        self.login()

        # 3. 데이터 수집 (Rank 방식)
        # [변경] opt10027 대신 전종목 순차 조회(opt10001)로 변경
        self.data_list = self.fetch_all_stocks_sequentially()

        # 5. 데이터프레임 변환 및 필터링
        df = pd.DataFrame(self.data_list)
        
        if df.empty:
            print("\n⚠️ 조건에 맞는 종목이 없습니다.")
            return

        if not df.empty:
            # 정렬: 등락률 내림차순
            filtered_df = df.sort_values(by='change_rate', ascending=False)
        else:
            filtered_df = pd.DataFrame()

        print(f"\n📊 수집 완료: 총 {len(filtered_df)}개 종목 (상한가 ~ 5%)")

        # 5-1. 이유 수집 (Phase 2)
        filtered_df = self.find_reasons(filtered_df)

        # 5-1b. 투자자 동향 수집 (기관/외인 연속 순매수 + 프로그램)
        filtered_df = self.find_investor_info(filtered_df)

        # 5-2. 터미널 출력 (뉴스 포함)
        if filtered_df.empty:
            print("\n⚠️ 필터 후 수집된 종목이 없습니다. 작업을 종료합니다.")
            return

        self.print_results(filtered_df)

        # 6. 로컬 저장
        self.save_local_csv(filtered_df)

        # [Phase 2 - 추후] Notion 업로드는 터미널 출력 검증 완료 후 활성화
        # self.upload_to_notion(filtered_df)

        print("\n✅ 모든 작업 완료!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    briefing = MarketBriefing()

    # 전체 프로세스 실행 (데이터 수집 -> 필터링 -> 뉴스 -> 저장 -> 노션)
    briefing.run()
