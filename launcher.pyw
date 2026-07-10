"""
키움 데일리 브리핑 런처
바탕화면에서 수동 실행하는 프리미엄 GUI 런처
"""
import sys
import os
import html as _html
from datetime import datetime
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextBrowser, QLabel, QMessageBox, QDesktopWidget,
    QFrame, QGraphicsDropShadowEffect, QProgressBar
)
from PyQt5.QtCore import Qt, QProcess, QTimer, QUrl, QMimeData
from PyQt5.QtGui import QFont, QColor, QIcon, QPainter, QLinearGradient, QDesktopServices


STYLE = """
* {
    font-family: 'Malgun Gothic', 'Segoe UI';
}
QMainWindow {
    background-color: #0a0e14;
}

/* ── Header ── */
QFrame#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0f1923, stop:0.5 #111d2b, stop:1 #0f1923);
    border-bottom: 2px solid #1a2636;
}
QLabel#brand_icon {
    color: #00d4aa;
    font-size: 36px;
    font-weight: 900;
    font-family: 'Consolas', 'Segoe UI';
}
QLabel#title {
    color: #e6edf3;
    font-size: 20px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#subtitle {
    color: #546a7b;
    font-size: 10px;
    letter-spacing: 2px;
}
QLabel#clock {
    color: #00d4aa;
    font-size: 13px;
    font-family: 'Consolas', 'D2Coding', monospace;
    font-weight: bold;
}

/* ── Status ── */
QFrame#status_bar {
    background-color: #111922;
    border: 1px solid #1a2636;
    border-radius: 6px;
    padding: 6px 12px;
}
QLabel#status_text {
    color: #8b9eb0;
    font-size: 12px;
}

/* ── Log ── */
QTextBrowser#log {
    background-color: #0c1018;
    color: #b0bec5;
    border: 1px solid #1a2636;
    border-radius: 6px;
    padding: 14px;
    font-family: 'D2Coding', 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    selection-background-color: #264f78;
    line-height: 1.5;
}

/* ── Progress ── */
QProgressBar {
    background-color: #111922;
    border: 1px solid #1a2636;
    border-radius: 3px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00d4aa, stop:1 #00b894);
    border-radius: 3px;
}

/* ── Buttons ── */
QPushButton#run_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00d4aa, stop:1 #00b894);
    color: #0a0e14;
    font-size: 15px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 14px 40px;
    letter-spacing: 1px;
}
QPushButton#run_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00e6b8, stop:1 #00d4aa);
}
QPushButton#run_btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00b894, stop:1 #00a383);
}
QPushButton#run_btn:disabled {
    background: #1a2636;
    color: #3d5266;
}
QPushButton#stop_btn {
    background-color: transparent;
    color: #ff6b6b;
    font-size: 14px;
    font-weight: bold;
    border: 2px solid #ff6b6b;
    border-radius: 8px;
    padding: 12px 24px;
}
QPushButton#stop_btn:hover {
    background-color: #ff6b6b;
    color: #0a0e14;
}
QPushButton#stop_btn:disabled {
    border-color: #1a2636;
    color: #3d5266;
}

/* ── Copy Markdown Button ── */
QPushButton#copy_btn {
    background-color: transparent;
    color: #6bcaff;
    font-size: 13px;
    font-weight: bold;
    border: 2px solid #254a6b;
    border-radius: 8px;
    padding: 12px 18px;
    letter-spacing: 0px;
}
QPushButton#copy_btn:hover {
    background-color: rgba(107, 202, 255, 0.08);
    border-color: #6bcaff;
}
QPushButton#copy_btn:pressed {
    background-color: rgba(107, 202, 255, 0.18);
}
QPushButton#copy_btn:disabled {
    border-color: #1a2636;
    color: #3d5266;
}

/* ── Footer ── */
QLabel#footer {
    color: #3d5266;
    font-size: 9px;
    letter-spacing: 1px;
}

/* ── Info Cards ── */
QFrame#info_card {
    background-color: #111922;
    border: 1px solid #1a2636;
    border-radius: 6px;
    padding: 8px 12px;
}
QLabel#info_label {
    color: #546a7b;
    font-size: 9px;
    letter-spacing: 1px;
}
QLabel#info_value {
    color: #e6edf3;
    font-size: 13px;
    font-weight: bold;
}
"""


class BriefingLauncher(QMainWindow):
    NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock_notes.json")

    def __init__(self):
        super().__init__()
        self.process = None
        self.start_time = None
        self.stock_count = 0
        self.results = []          # [RESULT] 파싱된 종목 데이터
        self._in_results = False   # [RESULTS_START] ~ [RESULTS_END] 블록 여부
        self.stock_notes = self._load_stock_notes()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_elapsed)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.pulse_status)
        self.pulse_state = True
        self.init_ui()
        self.clock_timer.start(1000)

    def _load_stock_notes(self):
        """stock_notes.json 로드 (종목명 → 메모 매핑)"""
        try:
            with open(self.NOTES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def init_ui(self):
        self.setWindowTitle("Kiwoom Daily Briefing")
        self.setFixedSize(800, 620)
        self.setStyleSheet(STYLE)

        # Window icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "briefing.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ══════════════════════════════════════
        # HEADER
        # ══════════════════════════════════════
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(80)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        # Left: Brand
        brand_left = QHBoxLayout()
        brand_left.setSpacing(14)

        brand_icon = QLabel("K")
        brand_icon.setObjectName("brand_icon")
        brand_icon.setFixedSize(48, 48)
        brand_icon.setAlignment(Qt.AlignCenter)
        brand_icon.setStyleSheet("""
            QLabel {
                color: #00d4aa;
                font-size: 28px;
                font-weight: 900;
                font-family: 'Consolas';
                background-color: rgba(0, 212, 170, 0.08);
                border: 2px solid rgba(0, 212, 170, 0.3);
                border-radius: 12px;
            }
        """)
        brand_left.addWidget(brand_icon)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(2)
        title = QLabel("KIWOOM DAILY BRIEFING")
        title.setObjectName("title")
        brand_text.addWidget(title)
        subtitle = QLabel("OPEN API  \u2022  MARKET INTELLIGENCE")
        subtitle.setObjectName("subtitle")
        brand_text.addWidget(subtitle)
        brand_left.addLayout(brand_text)

        header_layout.addLayout(brand_left)
        header_layout.addStretch()

        # Right: Clock
        clock_layout = QVBoxLayout()
        clock_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.clock_label = QLabel(datetime.now().strftime("%H:%M:%S"))
        self.clock_label.setObjectName("clock")
        self.clock_label.setAlignment(Qt.AlignRight)
        clock_layout.addWidget(self.clock_label)
        date_label = QLabel(datetime.now().strftime("%Y.%m.%d"))
        date_label.setStyleSheet("color: #546a7b; font-size: 10px; font-family: Consolas;")
        date_label.setAlignment(Qt.AlignRight)
        clock_layout.addWidget(date_label)
        header_layout.addLayout(clock_layout)

        main_layout.addWidget(header)

        # ══════════════════════════════════════
        # CONTENT
        # ══════════════════════════════════════
        content = QVBoxLayout()
        content.setContentsMargins(24, 16, 24, 16)
        content.setSpacing(12)

        # ── Info Cards Row ──
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        self.card_status = self._make_info_card("STATUS", "STANDBY")
        self.card_elapsed = self._make_info_card("ELAPSED", "--:--")
        self.card_stocks = self._make_info_card("STOCKS", "0")
        cards_row.addWidget(self.card_status)
        cards_row.addWidget(self.card_elapsed)
        cards_row.addWidget(self.card_stocks)
        content.addLayout(cards_row)

        # ── Progress Bar ──
        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setVisible(False)
        content.addWidget(self.progress)

        # ── Status Bar ──
        status_frame = QFrame()
        status_frame.setObjectName("status_bar")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 8, 12, 8)

        self.status_dot = QLabel("\u25cf")
        self.status_dot.setStyleSheet("color: #546a7b; font-size: 14px;")
        self.status_dot.setFixedWidth(18)
        status_layout.addWidget(self.status_dot)

        self.status_label = QLabel("Ready  \u2014  \uc2e4\ud589 \ubc84\ud2bc\uc744 \ub20c\ub7ec \ube0c\ub9ac\ud551\uc744 \uc2dc\uc791\ud558\uc138\uc694")
        self.status_label.setObjectName("status_text")
        status_layout.addWidget(self.status_label)
        content.addWidget(status_frame)

        # ── Log Output ──
        self.log_output = QTextBrowser()
        self.log_output.setObjectName("log")
        self.log_output.setOpenLinks(False)  # 클릭을 anchorClicked 시그널로 처리
        self.log_output.anchorClicked.connect(self.open_link)
        content.addWidget(self.log_output)

        # ── Buttons ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.run_btn = QPushButton("\u25b6  \ube0c\ub9ac\ud551 \uc2e4\ud589")
        self.run_btn.setObjectName("run_btn")
        self.run_btn.setFixedHeight(52)
        self.run_btn.setCursor(Qt.PointingHandCursor)
        self.run_btn.clicked.connect(self.run_briefing)
        btn_layout.addWidget(self.run_btn, stretch=3)

        self.stop_btn = QPushButton("\u25a0  \uc911\uc9c0")
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setFixedHeight(52)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.clicked.connect(self.stop_briefing)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn, stretch=1)

        self.copy_btn = QPushButton("📋  복사 (HTML + 마크다운)")
        self.copy_btn.setObjectName("copy_btn")
        self.copy_btn.setFixedHeight(52)
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.clicked.connect(self.copy_markdown)
        self.copy_btn.setEnabled(False)
        btn_layout.addWidget(self.copy_btn, stretch=1)

        content.addLayout(btn_layout)

        # ── Footer ──
        footer = QLabel(
            "KIWOOM OPEN API  \u2022  HTS \ub9e4\ub9e4 \uc911\uc5d0\ub294 \ub3d9\uc2dc \uc811\uc18d \ubd88\uac00  \u2022  "
            "v2.0"
        )
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignCenter)
        content.addWidget(footer)

        main_layout.addLayout(content)

        # Center on screen
        screen = QDesktopWidget().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

        self.log_styled("SYSTEM", "green", "\uc2dc\uc2a4\ud15c \uc900\ube44 \uc644\ub8cc")
        self.log_styled("INFO", "dim", "\ud0a4\uc6c0 HTS \ub9e4\ub9e4 \uc911\uc774 \uc544\ub2cc\uc9c0 \ud655\uc778 \ud6c4 [\ube0c\ub9ac\ud551 \uc2e4\ud589] \ubc84\ud2bc\uc744 \ub20c\ub7ec\uc8fc\uc138\uc694")

    # ── UI Helpers ──
    def _make_info_card(self, label_text, value_text):
        card = QFrame()
        card.setObjectName("info_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        label = QLabel(label_text)
        label.setObjectName("info_label")
        layout.addWidget(label)

        value = QLabel(value_text)
        value.setObjectName("info_value")
        layout.addWidget(value)

        card._value_label = value
        return card

    def _update_card(self, card, text, color=None):
        card._value_label.setText(text)
        if color:
            card._value_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")

    # ── Logging ──
    def log_styled(self, tag, style, message):
        ts = datetime.now().strftime("%H:%M:%S")
        colors = {
            "green": "#00d4aa",
            "red": "#ff6b6b",
            "yellow": "#ffd93d",
            "blue": "#6bcaff",
            "dim": "#546a7b",
            "white": "#e6edf3",
        }
        tag_color = colors.get(style, colors["dim"])
        # HTML 특수문자 이스케이프 (& < > 등)
        import html as _html
        safe_msg = _html.escape(str(message))
        self.log_output.append(
            f"<span style='color:#3d5266'>{ts}</span> "
            f"<span style='color:{tag_color};font-weight:bold'>[{tag}]</span> "
            f"<span style='color:#b0bec5'>{safe_msg}</span>"
        )
        sb = self.log_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def log(self, message):
        self.log_styled("LOG", "dim", message)

    def open_link(self, url: QUrl):
        """뉴스 링크 클릭 시 기본 브라우저로 열기"""
        QDesktopServices.openUrl(url)

    def render_results(self):
        """수집된 [RESULT] 데이터를 클릭 가능한 HTML 테이블로 렌더링"""
        if not self.results:
            return
        import html as _html

        lines = [
            "<div style='margin-top:12px; font-family:D2Coding,Consolas,monospace; font-size:11px;'>",
            "<div style='color:#00d4aa; border-bottom:1px solid #1a2636; padding-bottom:6px; "
            "margin-bottom:8px; font-size:12px; font-weight:bold; letter-spacing:1px;'>"
            "== MARKET BRIEFING RESULTS ==</div>",
        ]
        for i, r in enumerate(self.results, 1):
            rate = r.get('rate', 0)
            tv = r.get('tv', 0)
            name = _html.escape(r.get('name', ''))
            code = r.get('code', '')
            reason = _html.escape(r.get('reason', '') or '특이사항없음')
            # headline: 전체 뉴스 제목 (없으면 reason으로 fallback)
            headline = _html.escape(r.get('headline', '') or r.get('reason', '') or '특이사항없음')
            link = r.get('link', '')
            is_upper = r.get('upper', False)

            rate_str = f"+{rate:.2f}%"
            tv_str = f"{tv:,.0f}억"
            name_display = f"{name}({code[-4:]})"

            # 색상: 상한가=노랑, 15%+=초록, 그 외=흰색
            if is_upper:
                rate_color = "#ffd93d"
                upper_tag = "<span style='color:#ffd93d; font-weight:bold;'>[상한가]</span> "
            elif rate >= 15:
                rate_color = "#00d4aa"
                upper_tag = ""
            else:
                rate_color = "#e6edf3"
                upper_tag = ""

            # 뉴스 링크: 전체 제목(headline) 표시 + 클릭 시 브라우저 오픈
            if link and link not in ('-', ''):
                reason_html = (
                    f"<a href='{link}' style='color:#6bcaff; text-decoration:underline; "
                    f"font-weight:bold;'>{headline}</a>"
                )
            else:
                reason_html = f"<span style='color:#546a7b;'>{headline}</span>"

            lines.append(
                f"<div style='margin-bottom:2px; padding:2px 0;'>"
                f"<span style='color:#3d5266; width:24px; display:inline-block;'>{i}.</span>"
                f"<span style='color:{rate_color}; font-weight:bold; display:inline-block; min-width:130px;'>"
                f"{name_display}</span>"
                f"<span style='color:{rate_color}; display:inline-block; min-width:75px;'>{rate_str}</span>"
                f"<span style='color:#546a7b; display:inline-block; min-width:75px;'>{tv_str}</span>"
                f"{upper_tag}"
                f"{reason_html}"
                f"</div>"
            )
            # 투자자 동향 라인 (기관/외인/프로그램 이모지)
            inv_info = r.get('investor_info', '')
            if inv_info:
                lines.append(
                    f"<div style='margin-bottom:5px; padding:0 0 0 24px; font-size:10px;'>"
                    f"<span style='color:#ffd93d;'>{_html.escape(inv_info)}</span>"
                    f"</div>"
                )
        lines.append("</div>")

        self.log_output.append("".join(lines))
        sb = self.log_output.verticalScrollBar()
        sb.setValue(sb.maximum())
        # 결과 있으면 마크다운 복사 버튼 활성화
        if self.results:
            self.copy_btn.setEnabled(True)

    # ── Clock / Status ──
    def update_clock(self):
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S"))

    def set_status(self, text, color):
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 14px;")
        self.status_label.setText(text)

    def pulse_status(self):
        self.pulse_state = not self.pulse_state
        if self.pulse_state:
            self.status_dot.setStyleSheet("color: #ffd93d; font-size: 14px;")
        else:
            self.status_dot.setStyleSheet("color: #3d5266; font-size: 14px;")

    def update_elapsed(self):
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).seconds
            m, s = divmod(elapsed, 60)
            self._update_card(self.card_elapsed, f"{m:02d}:{s:02d}")

    # ── Run / Stop ──
    def run_briefing(self):
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.copy_btn.setEnabled(False)
        self.log_output.clear()
        self.stock_count = 0
        self.results = []
        self._in_results = False
        self.start_time = datetime.now()
        self.timer.start(1000)
        self.pulse_timer.start(500)
        self.progress.setVisible(True)

        self._update_card(self.card_status, "RUNNING", "#ffd93d")
        self._update_card(self.card_elapsed, "00:00")
        self._update_card(self.card_stocks, "0")
        self.set_status("\uc2e4\ud589 \uc911  \u2014  \ud0a4\uc6c0 OPEN API \uc811\uc18d \uc911...", "#ffd93d")

        self.log_styled("START", "green", "\ud0a4\uc6c0 OPEN API \uc811\uc18d \uc2dc\uc791...")

        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "market_briefing.py")

        self.process = QProcess(self)
        self.process.setWorkingDirectory(script_dir)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.process_finished)
        self.process.start(sys.executable, ['-u', script_path])  # -u: 버퍼링 없이 실시간 출력

    def handle_output(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode('utf-8', errors='replace').strip()
        if text:
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # ── [RESULT] 머신리더블 라인 파싱 (로그에 표시 안 함) ──
                if line == '[RESULTS_START]':
                    self._in_results = True
                    self.results = []
                    continue
                if line == '[RESULTS_END]':
                    self._in_results = False
                    self.render_results()  # 클릭 가능한 HTML 결과 테이블 렌더링
                    continue
                if line.startswith('[RESULT]'):
                    try:
                        r = json.loads(line[len('[RESULT]'):])
                        self.results.append(r)
                    except Exception:
                        pass
                    continue

                # ── 진행 상황 파싱 ──
                if '진행 중' in line and '/' in line:
                    try:
                        part = line.split('[')[1].split(']')[0]
                        current = int(part.split('/')[0])
                        total = int(part.split('/')[1])
                        pct = int(current / total * 100)
                        self.progress.setRange(0, 100)
                        self.progress.setValue(pct)
                        self.set_status(
                            f"실행 중  \u2014  {current}/{total} 종목 조회 ({pct}%)",
                            "#ffd93d"
                        )
                    except (IndexError, ValueError):
                        pass

                if '수집된 종목' in line or '수집 완료' in line:
                    try:
                        num = ''.join(c for c in line.split('종')[0] if c.isdigit())
                        if num:
                            self.stock_count = int(num[-3:]) if len(num) > 3 else int(num)
                            self._update_card(self.card_stocks, str(self.stock_count), "#00d4aa")
                    except (ValueError, IndexError):
                        pass

                # ── 컬러 코딩 ──
                if any(k in line for k in ['완료', '성공', 'OK']):
                    self.log_styled("OK", "green", line)
                elif any(k in line for k in ['실패', '오류', 'ERROR', '없습니다']):
                    self.log_styled("ERR", "red", line)
                elif any(k in line for k in ['시작', 'START', '로그인']):
                    self.log_styled("RUN", "blue", line)
                elif '진행' in line:
                    self.log_styled("...", "yellow", line)
                else:
                    self.log_styled("LOG", "dim", line)

    def process_finished(self, exit_code, exit_status):
        self.timer.stop()
        self.pulse_timer.stop()
        self.progress.setVisible(False)
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if self.start_time:
            elapsed = (datetime.now() - self.start_time).seconds
            m, s = divmod(elapsed, 60)
            time_str = f"{m:02d}:{s:02d}"
            self._update_card(self.card_elapsed, time_str)
        else:
            time_str = ""

        if exit_code == 0:
            self.status_dot.setStyleSheet("color: #00d4aa; font-size: 14px;")
            self.set_status(f"Complete  \u2014  \ube0c\ub9ac\ud551 \uc644\ub8cc ({time_str})", "#00d4aa")
            self._update_card(self.card_status, "DONE", "#00d4aa")
            self.log_styled("DONE", "green", f"\ube0c\ub9ac\ud551 \uc644\ub8cc! (\uc18c\uc694 \uc2dc\uac04: {time_str})")
        else:
            self.status_dot.setStyleSheet("color: #ff6b6b; font-size: 14px;")
            self.set_status(f"Error  \u2014  \uc885\ub8cc \ucf54\ub4dc: {exit_code}", "#ff6b6b")
            self._update_card(self.card_status, "ERROR", "#ff6b6b")
            self.log_styled("ERR", "red", f"\uc885\ub8cc \ucf54\ub4dc: {exit_code}")

        self.start_time = None

    def stop_briefing(self):
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            self.pulse_timer.stop()
            self.timer.stop()
            self.progress.setVisible(False)
            self.status_dot.setStyleSheet("color: #ff6b6b; font-size: 14px;")
            self.set_status("Stopped  \u2014  \uc0ac\uc6a9\uc790\uc5d0 \uc758\ud574 \uc911\uc9c0\ub428", "#ff6b6b")
            self._update_card(self.card_status, "STOPPED", "#ff6b6b")
            self.log_styled("STOP", "red", "\uc0ac\uc6a9\uc790\uc5d0 \uc758\ud574 \uc911\uc9c0\ub428")

    # ── Markdown Export ──────────────────────────────────────
    def build_markdown(self):
        """
        수집된 결과를 노션/티스토리/네이버블로그에 바로 붙여넣을 수 있는
        마크다운 텍스트로 변환.
        섹터: 🔴 상한가 / 🚀 20%+ / 📈 10%+ / 📊 5%+
        """
        if not self.results:
            return ""

        today_str = datetime.now().strftime("%Y년 %m월 %d일 (%a)")
        # 한국 요일
        day_ko = ["월", "화", "수", "목", "금", "토", "일"][datetime.now().weekday()]
        today_str = datetime.now().strftime(f"%Y년 %m월 %d일 ({day_ko})")

        # 섹터 분류
        upper   = [r for r in self.results if r.get('upper', False)]
        tier20  = [r for r in self.results if not r.get('upper', False) and r.get('rate', 0) >= 20]
        tier10  = [r for r in self.results if not r.get('upper', False) and 10 <= r.get('rate', 0) < 20]
        tier5   = [r for r in self.results if not r.get('upper', False) and r.get('rate', 0) < 10]

        # ── 시간대 판단: 15:40 전 = 오전장, 15:40 이후 = 장마감 ──
        now = datetime.now()
        session = "장마감" if (now.hour > 15 or (now.hour == 15 and now.minute >= 40)) else "오전장"

        lines = []

        # ── 타이틀 ──
        lines.append(f'# 📊 데일리 "{session}" 마켓 브리핑')
        lines.append(f"")
        lines.append(f"**{today_str}** · {session} 시황 분석")
        lines.append(f"")
        lines.append(f"> 📌 **필터 기준(등락율 + 거래대금 기준)** : 상한가 (29.9%↑) | 15%↑ 100억+ | 5%↑ 500억+")
        lines.append(f"> 📦 **총 {len(self.results)}개 종목** — 상한가 {len(upper)}개 · 20%↑ {len(tier20)}개 · 10%↑ {len(tier10)}개 · 5%↑ {len(tier5)}개")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

        rank = 1
        rank = self._md_sector(lines, "## 🔴 상한가 종목", upper, rank)
        rank = self._md_sector(lines, "## 🚀 20% 이상 종목", tier20, rank)
        rank = self._md_sector(lines, "## 📈 10% 이상 종목", tier10, rank)
        rank = self._md_sector(lines, "## 📊 5% 이상 종목",  tier5,  rank)

        lines.append(f"---")
        lines.append(f"")
        lines.append(f"*🤖 Powered by CRtheHILLS · {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

        return "\n".join(lines)

    def _md_sector(self, lines, header, stocks, start_rank):
        """섹터 블록 마크다운 생성 헬퍼. 비어있으면 섹션 생략. 순위 반환."""
        if not stocks:
            return start_rank

        lines.append(f"{header} — {len(stocks)}개")
        lines.append(f"")

        for r in stocks:
            rank = start_rank
            start_rank += 1

            name = r.get('name', '')
            code = r.get('code', '')
            rate = r.get('rate', 0)
            tv   = r.get('tv', 0)
            link = r.get('link', '')
            # 전체 헤드라인 우선, 없으면 reason
            headline = (r.get('headline', '') or r.get('reason', '') or '특이사항 없음').strip()
            inv_info = r.get('investor_info', '')

            rate_str = f"+{rate:.2f}%"
            tv_str   = f"{tv:,.0f}억"
            code_short = code[-4:] if len(code) >= 4 else code

            # 종목 헤더 라인
            lines.append(f"### {rank}. {name} `{code_short}`")
            lines.append(f"")

            # 수치 라인
            lines.append(f"📈 **{rate_str}** &nbsp; · &nbsp; 💵 거래대금 **{tv_str}**")
            lines.append(f"")

            # 뉴스 라인 (전체 헤드라인)
            if headline and headline not in ('특이사항없음', '-'):
                if link and link not in ('-', ''):
                    lines.append(f"📰 [{headline}]({link})")
                else:
                    lines.append(f"📰 {headline}")
            else:
                lines.append(f"📰 *특이사항 없음*")
            lines.append(f"")

            # 투자자 동향
            if inv_info:
                lines.append(f"💼 {inv_info}")
                lines.append(f"")

            # 종목 메모 (stock_notes.json)
            note_entry = self.stock_notes.get(name)
            if note_entry and note_entry.get('notes'):
                for note in note_entry['notes']:
                    lines.append(f"📝 {note}")
                lines.append(f"")

        lines.append(f"---")
        lines.append(f"")
        return start_rank

    def build_html(self):
        """네이버 카페/블로그 WYSIWYG 에디터용 HTML 생성"""
        if not self.results:
            return ""

        day_ko = ["월", "화", "수", "목", "금", "토", "일"][datetime.now().weekday()]
        today_str = datetime.now().strftime(f"%Y년 %m월 %d일 ({day_ko})")

        now = datetime.now()
        session = "장마감" if (now.hour > 15 or (now.hour == 15 and now.minute >= 40)) else "오전장"

        # 섹터 분류 (same as build_markdown)
        upper   = [r for r in self.results if r.get('upper', False)]
        tier20  = [r for r in self.results if not r.get('upper', False) and r.get('rate', 0) >= 20]
        tier10  = [r for r in self.results if not r.get('upper', False) and 10 <= r.get('rate', 0) < 20]
        tier5   = [r for r in self.results if not r.get('upper', False) and r.get('rate', 0) < 10]

        h = []
        h.append('<div style="font-family: \'Malgun Gothic\', \'Noto Sans KR\', sans-serif; color: #222; line-height: 1.7; max-width: 700px;">')

        # Title
        h.append(f'<h2 style="font-size: 22px; margin-bottom: 4px;">&#128202; 데일리 &ldquo;{session}&rdquo; 마켓 브리핑</h2>')
        h.append(f'<p style="font-size: 15px; color: #555; margin-top: 0;">{today_str} · {session} 시황 분석</p>')

        # Filter info box
        h.append('<div style="background: #f8f9fa; border-left: 4px solid #4a90d9; padding: 12px 16px; margin: 16px 0; border-radius: 4px; font-size: 14px;">')
        h.append('&#128204; <b>필터 기준(등락율 + 거래대금 기준)</b> : 상한가 (29.9%↑) | 15%↑ 100억+ | 5%↑ 500억+<br>')
        h.append(f'&#128230; <b>총 {len(self.results)}개 종목</b> — 상한가 {len(upper)}개 · 20%↑ {len(tier20)}개 · 10%↑ {len(tier10)}개 · 5%↑ {len(tier5)}개')
        h.append('</div>')

        # Sectors
        rank = 1
        rank = self._html_sector(h, "&#128308; 상한가 종목", "#e74c3c", upper, rank)
        rank = self._html_sector(h, "&#128640; 20% 이상 종목", "#e67e22", tier20, rank)
        rank = self._html_sector(h, "&#128200; 10% 이상 종목", "#2ecc71", tier10, rank)
        rank = self._html_sector(h, "&#128202; 5% 이상 종목", "#3498db", tier5, rank)

        # Footer
        h.append(f'<p style="font-size: 12px; color: #999; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px;">&#129302; Powered by CRtheHILLS · {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>')
        h.append('</div>')

        return "\n".join(h)

    def _html_sector(self, h, title, color, stocks, start_rank):
        """섹터 블록 HTML 생성 헬퍼"""
        if not stocks:
            return start_rank

        h.append(f'<h3 style="font-size: 18px; color: {color}; border-bottom: 2px solid {color}; padding-bottom: 6px; margin-top: 28px;">{title} — {len(stocks)}개</h3>')

        for r in stocks:
            rank = start_rank
            start_rank += 1

            name = r.get('name', '')
            code = r.get('code', '')
            rate = r.get('rate', 0)
            tv   = r.get('tv', 0)
            link = r.get('link', '')
            headline = (r.get('headline', '') or r.get('reason', '') or '특이사항 없음').strip()
            inv_info = r.get('investor_info', '')

            rate_str = f"+{rate:.2f}%"
            tv_str   = f"{tv:,.0f}억"
            code_short = code[-4:] if len(code) >= 4 else code

            # HTML 특수문자 이스케이프 (이름/헤드라인의 & < > 처리)
            name_esc = _html.escape(name)
            headline_esc = _html.escape(headline) if headline else ''

            # Each stock as a card-like block
            h.append(f'<div style="margin: 16px 0; padding: 14px 16px; background: #fafbfc; border-radius: 8px; border: 1px solid #e8ecf0;">')
            h.append(f'  <p style="font-size: 16px; font-weight: bold; margin: 0 0 6px 0;">{rank}. {name_esc} <span style="font-size: 13px; color: #888; font-weight: normal;">({code_short})</span></p>')
            h.append(f'  <p style="font-size: 14px; margin: 4px 0; color: #d63031;">&#128200; <b>{rate_str}</b> &nbsp;·&nbsp; &#128181; 거래대금 <b>{tv_str}</b></p>')

            # News
            if headline and headline not in ('특이사항없음', '-'):
                if link and link not in ('-', ''):
                    h.append(f'  <p style="font-size: 14px; margin: 4px 0;">&#128240; <a href="{link}" style="color: #2980b9; text-decoration: none;">{headline_esc}</a></p>')
                else:
                    h.append(f'  <p style="font-size: 14px; margin: 4px 0;">&#128240; {headline_esc}</p>')
            else:
                h.append(f'  <p style="font-size: 14px; margin: 4px 0; color: #999;">&#128240; <i>특이사항 없음</i></p>')

            # Investor info (emoji characters pass through as-is)
            if inv_info:
                h.append(f'  <p style="font-size: 13px; margin: 4px 0; color: #555;">&#128188; {inv_info}</p>')

            # 종목 메모 (stock_notes.json)
            note_entry = self.stock_notes.get(name)
            if note_entry and note_entry.get('notes'):
                for note in note_entry['notes']:
                    note_esc = _html.escape(note)
                    h.append(f'  <p style="font-size: 13px; margin: 3px 0; color: #6c5ce7; padding-left: 8px; border-left: 3px solid #6c5ce7;">&#128221; {note_esc}</p>')

            h.append('</div>')

        return start_rank

    def copy_markdown(self):
        """마크다운 + HTML 동시 클립보드 복사 (네이버카페=HTML, 노션/티스토리=마크다운)"""
        md = self.build_markdown()
        if not md:
            self.log_styled("WARN", "yellow", "복사할 결과가 없습니다. 먼저 브리핑을 실행하세요.")
            return

        html = self.build_html()

        mime = QMimeData()
        mime.setText(md)
        mime.setHtml(html)
        QApplication.clipboard().setMimeData(mime)

        # 버튼 텍스트 일시 변경으로 복사 완료 피드백
        self.copy_btn.setText("✅  복사 완료!")
        self.copy_btn.setStyleSheet(
            "QPushButton { background-color: rgba(0,212,170,0.12); color:#00d4aa; "
            "font-size:13px; font-weight:bold; border:2px solid #00d4aa; "
            "border-radius:8px; padding:12px 18px; }"
        )
        QTimer.singleShot(2000, self._reset_copy_btn)
        self.log_styled("OK", "green",
            f"복사 완료! ({len(self.results)}개 종목) — 네이버 카페(HTML) / 노션·티스토리(마크다운) 📋")

    def _reset_copy_btn(self):
        self.copy_btn.setText("📋  복사 (HTML + 마크다운)")
        self.copy_btn.setStyleSheet("")  # STYLE 시트로 복귀

    def closeEvent(self, event):
        if self.process and self.process.state() == QProcess.Running:
            reply = QMessageBox.question(
                self, '\uc885\ub8cc \ud655\uc778',
                '\ube0c\ub9ac\ud551\uc774 \uc2e4\ud589 \uc911\uc785\ub2c8\ub2e4. \uc885\ub8cc\ud558\uc2dc\uaca0\uc2b5\ub2c8\uae4c?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.process.kill()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    launcher = BriefingLauncher()
    launcher.show()
    sys.exit(app.exec_())
