"""
Momentum Portfolio Dashboard
-----------------------------
A local, browser-based dashboard for tracking your momentum portfolio.
Runs on your own computer — Yahoo Finance data won't work in a cloud sandbox.

Setup (one time):
    pip3 install streamlit yfinance pandas plotly openpyxl

Run:
    python3 -m streamlit run momentum_dashboard.py

Edit the HOLDINGS list below whenever you buy/sell or rebalance.
"""

import os
import json
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Momentum Tracker", page_icon="📈", layout="wide")

GREEN = "#2ECC71"
RED = "#FF6B4A"
ACCENT = "#7C8CFF"
BG = "#0E0E10"
CARD = "#18181B"
CARD_ALT = "#1D1D21"      # detail / summary cards — one shade up from base
CARD_TABLE = "#1A1A1E"    # holdings / positions tables
CARD_UPLOAD = "#1D1D21"   # watchlist / paper-trade utility cards
BORDER = "#2A2A2E"
INK = "#F2F2F3"
MUTED = "#8E8E93"
PALETTE = ["#7C8CFF", "#7A8B5E", "#5B9BD5", "#E8590C", "#AE3EC9", "#2ECC71",
           "#F08C00", "#5E7FA6", "#D6336C", "#1098AD", "#A65E7A", "#6E8B9C"]

WATCHLISTS_FILE = "watchlists.json"
PORTFOLIOS_FILE = "portfolios.json"
PAPER_TRADES_FILE = "paper_trades.csv"
DEFAULT_STARTING_CASH = 100000.0

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
    .stApp {{ background: {BG}; font-family: 'Inter', sans-serif; }}
    .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }}
    h1, h2, h3, h4 {{ font-family: 'Inter', sans-serif; color: {INK}; letter-spacing: -0.01em; font-weight: 700; }}
    h1 {{ font-size: 2.1rem !important; }}
    h2 {{ font-size: 1.5rem !important; }}
    h3 {{ font-size: 1.2rem !important; }}
    p, span, div, label {{ color: {INK}; font-size: 15.5px; }}
    .stCaption, [data-testid="stCaptionContainer"] {{ color: {MUTED} !important; font-size: 14px !important; }}
    .num {{ font-family: 'IBM Plex Mono', monospace; font-variant-numeric: tabular-nums; }}
    .element-container {{ margin-bottom: 0.2rem !important; }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{ margin-bottom: 0.3rem; }}

    [data-testid="stMetric"] {{
        background: {CARD_ALT}; border: 1px solid {BORDER}; border-radius: 10px; padding: 16px 20px;
    }}
    [data-testid="stMetricLabel"] {{ font-size: 0.85rem; letter-spacing: 0.03em; text-transform: uppercase; color: {MUTED}; }}
    [data-testid="stMetricValue"] {{ font-size: 1.9rem; font-weight: 700; color: {INK}; }}

    /* ---- Form controls: force white/light backgrounds with dark text everywhere ---- */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    .stTextInput input, .stNumberInput input,
    [data-baseweb="select"] input,
    div[data-baseweb="popover"] ul,
    [data-baseweb="menu"],
    .stSelectbox div[role="listbox"],
    [data-testid="stFileUploaderDropzone"],
    [data-testid="stFileUploaderDropzoneInstructions"] {{
        background-color: {CARD} !important;
        color: {INK} !important;
        border-color: {BORDER} !important;
    }}
    [data-baseweb="select"] span, [data-baseweb="select"] div,
    [data-baseweb="menu"] li, [data-baseweb="menu"] li span,
    [data-testid="stFileUploaderDropzoneInstructions"] span,
    [data-testid="stFileUploaderDropzoneInstructions"] div {{
        color: {INK} !important;
    }}
    .stTextInput input, .stNumberInput input, [data-baseweb="select"] input {{
        font-size: 15.5px !important;
    }}
    [data-baseweb="select"] > div, .stTextInput input, .stNumberInput input {{
        border: 1px solid {BORDER} !important; border-radius: 8px !important;
    }}
    li[aria-selected="true"] {{ background-color: {CARD_UPLOAD} !important; }}
    [data-baseweb="menu"] li:hover {{ background-color: {BG} !important; }}

    div[data-testid="stVerticalBlock"] div.stButton > button {{
        background: transparent; border: none; box-shadow: none;
        text-align: left; padding: 5px 8px; width: 100%;
        border-bottom: 1px solid {BORDER}; border-radius: 0;
        font-weight: 600; color: {INK}; min-height: 0; font-size: 14px;
    }}
    div[data-testid="stVerticalBlock"] div.stButton > button:hover {{ background: {CARD_ALT}; }}
    div[data-testid="stVerticalBlock"] div.stButton > button:focus:not(:active) {{ color: {INK}; }}
    div.stButton {{ margin: 0; }}

    .st-key-holdings_rows div[data-testid="stHorizontalBlock"],
    .st-key-holdings_hdr div[data-testid="stHorizontalBlock"] {{ gap: 4px !important; }}
    .st-key-holdings_rows [data-testid="column"] {{ padding-top: 0; padding-bottom: 0; }}

    .st-key-sort_pills div.stButton > button,
    .st-key-pv_timeframe div.stButton > button {{
        border-radius: 999px !important; height: 27px; padding: 0 13px !important;
        font-size: 12.5px !important; font-weight: 600 !important;
        border: 1px solid {BORDER} !important; background: {CARD} !important;
        width: auto !important; min-height: 0 !important; color: {INK} !important;
        white-space: nowrap !important; overflow: visible !important;
    }}
    .st-key-sort_pills div.stButton > button:hover,
    .st-key-pv_timeframe div.stButton > button:hover {{ background: {CARD_ALT} !important; }}
    .st-key-sort_pills div[data-testid="stHorizontalBlock"] {{ gap: 6px !important; align-items: center !important; }}
    .st-key-sort_pills [data-testid="column"] {{ width: fit-content !important; flex: none !important; min-width: fit-content !important; }}

    .card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 20px 22px; margin-bottom: 6px; }}
    .card-alt {{ background: {CARD_ALT}; border: 1px solid {BORDER}; border-radius: 10px; padding: 20px 22px; margin-bottom: 6px; }}
    .card-upload {{ background: {CARD_UPLOAD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 18px 20px; margin-bottom: 6px; }}
    .caption-box {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px;
        padding: 12px 16px; font-size: 0.86rem; color: {MUTED}; margin-top: 0.5rem;
    }}
    .track-wrap {{ position: relative; height: 4px; background: {BORDER}; border-radius: 2px; margin: 30px 10px 6px; }}
    .track-dot {{ position: absolute; top: 50%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; gap: 4px; }}
    .track-dot .dot {{ width: 10px; height: 10px; border-radius: 50%; border: 2px solid #FFF; display: block; }}
    .track-dot .lbl {{ font-size: 10.5px; color: {MUTED}; white-space: nowrap; margin-top: 10px; }}

    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
    .stTabs [data-baseweb="tab"] {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px 8px 0 0;
        padding: 9px 20px; font-weight: 600; color: {MUTED}; font-size: 14.5px;
    }}
    .stTabs [aria-selected="true"] {{ color: {INK} !important; border-bottom: 2px solid {ACCENT} !important; }}

    .stSelectbox label, .stTextInput label, .stNumberInput label, .stSlider label {{ font-size: 14px !important; color: {MUTED} !important; font-weight: 600; }}

    /* row-select buttons (holdings list) — quiet, left-aligned */
    div[data-testid="stVerticalBlock"] div.stButton > button {{
        background: transparent; border: none; box-shadow: none;
        text-align: left; padding: 5px 8px; width: 100%;
        border-bottom: 1px solid {BORDER}; border-radius: 0;
        font-weight: 600; color: {INK}; min-height: 0; font-size: 15px;
    }}
    div[data-testid="stVerticalBlock"] div.stButton > button:hover {{ background: {BG}; }}
    div[data-testid="stVerticalBlock"] div.stButton > button:focus:not(:active) {{ color: {INK}; }}
    div.stButton {{ margin: 0; }}

    /* Buy / Sell action buttons — bigger, colored, easy to hit */
    .st-key-buy_btn button, [class*="st-key-wl_buy_"] button, [class*="st-key-pos_buy_"] button {{
        background: {GREEN} !important; color: #FFFFFF !important; border: 1px solid {GREEN} !important;
        font-weight: 700 !important; font-size: 15px !important; min-height: 2.6rem !important;
        border-radius: 8px !important; width: 100% !important; text-align: center !important;
    }}
    .st-key-sell_btn button, [class*="st-key-wl_sell_"] button, [class*="st-key-pos_sell_"] button {{
        background: {RED} !important; color: #FFFFFF !important; border: 1px solid {RED} !important;
        font-weight: 700 !important; font-size: 15px !important; min-height: 2.6rem !important;
        border-radius: 8px !important; width: 100% !important; text-align: center !important;
    }}
    [class*="st-key-wl_buytrig_"] button, [class*="st-key-wl_selltrig_"] button,
    [class*="st-key-pos_buytrig_"] button, [class*="st-key-pos_selltrig_"] button {{
        min-height: 34px !important; height: 34px !important; width: 34px !important;
        padding: 0 !important; border-radius: 50% !important; font-size: 13px !important;
        margin-top: 6px;
    }}
    [class*="st-key-wl_buytrig_"] button, [class*="st-key-pos_buytrig_"] button {{
        background: {GREEN} !important; color: #FFFFFF !important; border: 1px solid {GREEN} !important;
    }}
    [class*="st-key-wl_selltrig_"] button, [class*="st-key-pos_selltrig_"] button {{
        background: {RED} !important; color: #FFFFFF !important; border: 1px solid {RED} !important;
    }}
    [class*="st-key-wl_remove_"] button {{
        background: transparent !important; border: 1px solid {BORDER} !important; color: {MUTED} !important;
        min-height: 34px !important; height: 34px !important; width: 34px !important;
        padding: 0 !important; border-radius: 50% !important; font-size: 13px !important;
        margin-top: 6px; text-align: center !important;
    }}

    /* Card-styled containers (st.container(key=...)) — avoids the empty-bar
       bug that literal <div>...</div> markdown pairs cause around widgets */
    .st-key-pp_selector, .st-key-pp_create, [class*="st-key-pp_trade_ticket_"],
    [class*="st-key-pp_delete_"], .st-key-wl_create_row, .st-key-pp_create_row {{
        background: {CARD_UPLOAD}; border: 1px solid {BORDER}; border-radius: 10px;
        padding: 18px 20px; margin-bottom: 10px;
    }}
    .st-key-pp_metrics, [class*="st-key-pp_metrics_"] {{
        background: {CARD_ALT}; border: 1px solid {BORDER}; border-radius: 10px;
        padding: 18px 20px; margin-bottom: 6px;
    }}

    [data-testid="stExpander"] {{
        background: {CARD_TABLE}; border: 1px solid {BORDER}; border-radius: 10px;
    }}
    [data-testid="stExpander"] summary {{ font-weight: 600; font-size: 15px; }}
</style>
""", unsafe_allow_html=True)

# ---- Your holdings: (Yahoo ticker, shares, avg buy price) ----
HOLDINGS = [
    ("EMMVEE.NS",     1, 340.00),
    ("REDINGTON.NS",  1, 392.00),
    ("ACMESOLAR.NS",  1, 458.00),
    ("AEGISLOG.NS",   1, 1475.00),
    ("ATHERENERG.NS", 1, 1591.00),   # Ather Energy
    ("SYRMA.NS",      1, 1611.00),
    ("PAYTM.NS",      1, 1815.00),
    ("LAURUSLABS.NS", 1, 1952.90),
    ("WELCORP.NS",    1, 2742.00),
    ("FINCABLES.NS",  2, 1406.00),
    ("GLAND.NS",      1, 2965.00),
    ("ACUTAAS.NS",    1, 3438.00),
]


@st.cache_data(ttl=60)
def fetch_prices(holdings):
    rows = []
    price_series = {}   # ticker -> Series of Close, indexed by date (up to 1y)
    for ticker, shares, avg_price in holdings:
        cmp, prev_close, ema20, ema50 = None, None, None, None
        volume, avg_volume, vol_ratio = None, None, None
        spark = []
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="1y")
            if not hist.empty:
                cmp = round(float(hist["Close"].iloc[-1]), 2)
                prev_close = round(float(hist["Close"].iloc[-2]), 2) if len(hist) > 1 else cmp
                volume = int(hist["Volume"].iloc[-1])
                avg_volume = int(hist["Volume"].iloc[:-1].tail(20).mean()) if len(hist) > 1 else None
                if avg_volume:
                    vol_ratio = round(volume / avg_volume, 2)
                spark = hist["Close"].tail(15).tolist()
                price_series[ticker] = hist["Close"]

            hist_long = t.history(period="4mo")
            if len(hist_long) >= 50:
                ema20 = round(float(hist_long["Close"].ewm(span=20, adjust=False).mean().iloc[-1]), 2)
                ema50 = round(float(hist_long["Close"].ewm(span=50, adjust=False).mean().iloc[-1]), 2)
        except Exception:
            pass

        invested = shares * avg_price
        current_value = shares * cmp if cmp else None
        pnl = (current_value - invested) if current_value else None
        pnl_pct = (pnl / invested * 100) if pnl is not None else None
        day_chg_pct = ((cmp - prev_close) / prev_close * 100) if (cmp and prev_close) else None

        below20 = (cmp is not None and ema20 is not None and cmp < ema20)
        below50 = (cmp is not None and ema50 is not None and cmp < ema50)
        ema_cross_bearish = (ema20 is not None and ema50 is not None and ema20 < ema50)

        rows.append({
            "Symbol": ticker.replace(".NS", ""),
            "Shares": shares,
            "Avg Price": avg_price,
            "CMP": cmp,
            "Day %": day_chg_pct,
            "Invested": invested,
            "Value": current_value,
            "P&L ₹": pnl,
            "P&L %": pnl_pct,
            "EMA20": ema20,
            "EMA50": ema50,
            "Below EMA20": below20,
            "Below EMA50": below50,
            "EMA Cross Bearish": ema_cross_bearish,
            "Volume": volume,
            "Vol Ratio": vol_ratio,
            "Spark": spark,
        })

    # Build the portfolio value history: sum(shares_i * close_i(t)) over dates all tickers share
    shares_map = {tkr: sh for tkr, sh, _ in holdings}
    portfolio_value_series = None
    if price_series:
        combined = pd.DataFrame(price_series).dropna()  # inner-join on shared trading dates
        if not combined.empty:
            weighted = combined.mul(pd.Series(shares_map), axis=1)
            portfolio_value_series = weighted.sum(axis=1)

    return pd.DataFrame(rows), portfolio_value_series


@st.cache_data(ttl=300)
def fetch_watchlist_prices(symbols):
    out = {}
    for sym in symbols:
        try:
            t = yf.Ticker(sym + ".NS")
            h = t.history(period="2d")
            out[sym] = round(float(h["Close"].iloc[-1]), 2) if not h.empty else None
        except Exception:
            out[sym] = None
    return out


@st.cache_data(ttl=300)
def fetch_watchlist_detail(symbols):
    """Richer per-symbol data for the watchlist table: cmp, day change, volume, sparkline."""
    out = {}
    for sym in symbols:
        cmp, prev_close, volume, spark = None, None, None, []
        try:
            t = yf.Ticker(sym + ".NS")
            hist = t.history(period="1mo")
            if not hist.empty:
                cmp = round(float(hist["Close"].iloc[-1]), 2)
                prev_close = round(float(hist["Close"].iloc[-2]), 2) if len(hist) > 1 else cmp
                volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist else None
                spark = hist["Close"].tail(15).tolist()
        except Exception:
            pass
        day_abs = (cmp - prev_close) if (cmp is not None and prev_close) else None
        day_pct = (day_abs / prev_close * 100) if (day_abs is not None and prev_close) else None
        out[sym] = {"cmp": cmp, "day_abs": day_abs, "day_pct": day_pct, "volume": volume, "spark": spark}
    return out


def sparkline_svg(values, color, width=90, height=28):
    if not values or len(values) < 2:
        return f"<svg width='{width}' height='{height}'></svg>"
    vmin, vmax = min(values), max(values)
    vrange = (vmax - vmin) or 1
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        x = (i / (n - 1)) * width
        y = height - ((v - vmin) / vrange) * (height - 4) - 2
        pts.append(f"{x:.1f},{y:.1f}")
    baseline_y = height - ((values[0] - vmin) / vrange) * (height - 4) - 2
    return (
        f"<svg width='{width}' height='{height}' style='display:block'>"
        f"<line x1='0' y1='{baseline_y:.1f}' x2='{width}' y2='{baseline_y:.1f}' "
        f"stroke='#3A3A40' stroke-width='1' stroke-dasharray='2,2'/>"
        f"<polyline points='{' '.join(pts)}' fill='none' stroke='{color}' stroke-width='1.6'/>"
        f"</svg>"
    )


AVATAR_COLORS = ["#4C6EF5", "#E8590C", "#2F9E44", "#AE3EC9", "#1098AD", "#F08C00", "#D6336C", "#5F3DC4"]


def avatar_html(symbol, size=34):
    letter = symbol[0].upper()
    color = AVATAR_COLORS[sum(ord(c) for c in symbol) % len(AVATAR_COLORS)]
    return (
        f"<div style='width:{size}px;height:{size}px;border-radius:50%;background:{color};"
        f"display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;"
        f"font-size:{size*0.42:.0f}px;flex-shrink:0'>{letter}</div>"
    )


@st.cache_data(ttl=300)
def fetch_technicals(symbols):
    """EMA20/EMA50 for arbitrary NSE symbols (used by paper portfolios)."""
    out = {}
    for sym in symbols:
        try:
            t = yf.Ticker(sym + ".NS")
            hist = t.history(period="4mo")
            if len(hist) >= 50:
                ema20 = round(float(hist["Close"].ewm(span=20, adjust=False).mean().iloc[-1]), 2)
                ema50 = round(float(hist["Close"].ewm(span=50, adjust=False).mean().iloc[-1]), 2)
                out[sym] = {"ema20": ema20, "ema50": ema50}
        except Exception:
            pass
    return out


# ---------------------------------------------------------------------------
# Watchlist store (multiple, named watchlists) — watchlists.json
# { "name": {"stocks": [{"Symbol","Rank","Score"}], "linked_portfolio": "name or null"} }
# ---------------------------------------------------------------------------
def load_watchlists():
    try:
        with open(WATCHLISTS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_watchlists(data):
    with open(WATCHLISTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Portfolio store (multiple paper-trading portfolios) — portfolios.json
# { "name": {"starting_cash": float} }
# ---------------------------------------------------------------------------
def load_portfolios():
    try:
        with open(PORTFOLIOS_FILE) as f:
            data = json.load(f)
            if data:
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    default = {"Default": {"starting_cash": DEFAULT_STARTING_CASH}}
    save_portfolios(default)
    return default


def save_portfolios(data):
    with open(PORTFOLIOS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_paper_trades():
    try:
        t = pd.read_csv(PAPER_TRADES_FILE, parse_dates=["Timestamp"])
        if "Portfolio" not in t.columns:
            t["Portfolio"] = "Default"
        return t
    except FileNotFoundError:
        return pd.DataFrame(columns=["Timestamp", "Portfolio", "Symbol", "Side", "Qty", "Price", "Amount"])


def save_paper_trade(portfolio, symbol, side, qty, price):
    trades = load_paper_trades()
    new_row = pd.DataFrame([{
        "Timestamp": datetime.now(),
        "Portfolio": portfolio,
        "Symbol": symbol,
        "Side": side,
        "Qty": qty,
        "Price": price,
        "Amount": qty * price,
    }])
    trades = pd.concat([trades, new_row], ignore_index=True)
    trades.to_csv(PAPER_TRADES_FILE, index=False)


def compute_paper_positions(trades, portfolio, starting_cash):
    """Weighted-average-cost method, scoped to one portfolio. Returns (positions, cash, realized_pnl)."""
    positions = {}
    cash = starting_cash
    realized_pnl = 0.0

    port_trades = trades[trades["Portfolio"] == portfolio] if not trades.empty else trades
    for _, tr in port_trades.sort_values("Timestamp").iterrows():
        sym, side, qty, price = tr["Symbol"], tr["Side"], tr["Qty"], tr["Price"]
        pos = positions.setdefault(sym, {"qty": 0, "avg": 0.0})

        if side == "BUY":
            new_qty = pos["qty"] + qty
            pos["avg"] = ((pos["qty"] * pos["avg"]) + (qty * price)) / new_qty if new_qty else 0
            pos["qty"] = new_qty
            cash -= qty * price
        else:  # SELL
            realized_pnl += (price - pos["avg"]) * qty
            pos["qty"] -= qty
            cash += qty * price
            if pos["qty"] <= 0:
                pos["qty"] = 0
                pos["avg"] = 0.0

    return positions, cash, realized_pnl


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
c1, c2 = st.columns([5, 1])
with c1:
    st.markdown(
        f"<div style='display:flex;align-items:baseline;gap:14px'>"
        f"<h1 style='margin:0;font-size:32px'>Momentum Portfolio Tracker</h1>"
        f"<span style='font-size:13.5px;color:{MUTED}'>12-stock NSE momentum book</span></div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Last refreshed: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
with c2:
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        fetch_prices.clear()

df, portfolio_value_series = fetch_prices(HOLDINGS)


# =============================================================================
# TAB: Holdings
# =============================================================================
def render_holdings_tab():
    # -------------------------------------------------------------------
    # Portfolio value history — with timeframe filter
    # -------------------------------------------------------------------
    if portfolio_value_series is not None and len(portfolio_value_series) > 1:
        TIMEFRAMES = [("1W", 7), ("2W", 14), ("1M", 30), ("3M", 90), ("6M", 180), ("1Y", 365), ("All", None)]

        if "pv_timeframe" not in st.session_state:
            st.session_state.pv_timeframe = "1M"

        st.markdown('<div class="card-alt" style="padding-bottom:12px;">', unsafe_allow_html=True)

        with st.container(key="pv_timeframe"):
            tf_cols = st.columns([1.3] + [0.55] * len(TIMEFRAMES) + [0.9] + [3])
            tf_cols[0].markdown("<span style='font-size:14px;font-weight:600;padding-top:2px;display:block'>Portfolio value</span>", unsafe_allow_html=True)
            for i, (label, _) in enumerate(TIMEFRAMES):
                if tf_cols[i + 1].button(label, key=f"tf_{label}"):
                    st.session_state.pv_timeframe = label
            if tf_cols[len(TIMEFRAMES) + 1].button("Custom", key="tf_Custom"):
                st.session_state.pv_timeframe = "Custom"

        if st.session_state.pv_timeframe == "Custom":
            max_days = max((portfolio_value_series.index.max() - portfolio_value_series.index.min()).days, 1)
            custom_days = st.slider("Custom lookback (days)", 1, max_days, min(30, max_days), key="pv_custom_days", label_visibility="collapsed")
            lookback_days = custom_days
        else:
            lookback_days = dict(TIMEFRAMES)[st.session_state.pv_timeframe]

        if lookback_days is None:
            pv_view = portfolio_value_series
        else:
            cutoff = portfolio_value_series.index.max() - pd.Timedelta(days=lookback_days)
            pv_view = portfolio_value_series[portfolio_value_series.index >= cutoff]
            if len(pv_view) < 2:
                pv_view = portfolio_value_series.tail(2)

        pv_start = pv_view.iloc[0]
        pv_end = pv_view.iloc[-1]
        pv_pct = (pv_end - pv_start) / pv_start * 100 if pv_start else 0
        pv_color = GREEN if pv_pct >= 0 else RED

        fig_pv = go.Figure(go.Scatter(
            x=pv_view.index, y=pv_view.values,
            mode="lines", line=dict(color=pv_color, width=2),
            fill="tozeroy", fillcolor=pv_color + "22",
        ))
        fig_pv.update_layout(
            height=100, margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(visible=False), yaxis=dict(visible=False),
        )

        label_txt = st.session_state.pv_timeframe if st.session_state.pv_timeframe != "Custom" else f"last {lookback_days}d"
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin:4px 0'>"
            f"<span style='font-size:12.5px;color:{MUTED}'>{label_txt} · {len(pv_view)} sessions</span>"
            f"<span class='num' style='font-size:12.5px;font-weight:600;color:{pv_color}'>{pv_pct:+.1f}% over period</span></div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig_pv, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------
    # Summary cards
    # -------------------------------------------------------------------
    total_invested = df["Invested"].sum()
    total_current = df["Value"].sum(skipna=True)
    total_pnl = total_current - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0
    n_below20 = int(df["Below EMA20"].sum())
    n_below50 = int(df["Below EMA50"].sum())

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Invested", f"₹{total_invested:,.0f}")
    k2.metric("Current Value", f"₹{total_current:,.0f}")
    k3.metric("Total P&L (unrealized)", f"₹{total_pnl:,.0f}", f"{total_pnl_pct:+.2f}%")
    k4.metric("Below EMA20", f"{n_below20} of {len(df)}")
    k5.metric("Below EMA50", f"{n_below50} of {len(df)}")

    # -------------------------------------------------------------------
    # Holdings — ranked table with sort pills, detail panel on the right
    # -------------------------------------------------------------------
    st.subheader("Holdings")

    df_sorted = df.sort_values("P&L %", ascending=False, na_position="last").reset_index(drop=True)
    df_sorted.insert(0, "Rank", df_sorted.index + 1)
    df_sorted["Allocation %"] = (df_sorted["Value"] / total_current * 100) if total_current else 0

    if "selected_symbol" not in st.session_state:
        st.session_state.selected_symbol = df_sorted.iloc[0]["Symbol"]
    if "sort_key" not in st.session_state:
        st.session_state.sort_key, st.session_state.sort_dir = "Rank", "asc"

    SORT_OPTIONS = [("Rank", "Rank"), ("Day %", "Day %"), ("P&L %", "P&L %"), ("Allocation", "Allocation %")]
    COL_WIDTHS = [2.6, 1.0, 1.25, 1.05, 1.3, 0.6]

    df_sorted = df_sorted.sort_values(
        st.session_state.sort_key,
        ascending=(st.session_state.sort_dir == "asc"),
        na_position="last",
    ).reset_index(drop=True)

    col_table, col_detail = st.columns([2, 1], gap="medium")

    with col_table:
        st.markdown(f'<div class="card" style="padding:0;overflow:hidden;background:{CARD_TABLE};">', unsafe_allow_html=True)

        with st.container(key="sort_pills"):
            sp_cols = st.columns([0.5, 0.85, 0.95, 0.95, 1.3, 4])
            sp_cols[0].markdown(f"<span style='font-size:12px;font-weight:600;color:{MUTED};text-transform:uppercase;padding-top:4px;display:block'>Sort</span>", unsafe_allow_html=True)
            for i, (label, col) in enumerate(SORT_OPTIONS):
                active = st.session_state.sort_key == col
                arrow = ("↑" if st.session_state.sort_dir == "asc" else "↓") if active else ""
                if sp_cols[i + 1].button(f"{label} {arrow}".strip(), key=f"sortpill_{col}"):
                    if active:
                        st.session_state.sort_dir = "desc" if st.session_state.sort_dir == "asc" else "asc"
                    else:
                        st.session_state.sort_key, st.session_state.sort_dir = col, "asc" if col == "Rank" else "desc"

        with st.container(key="holdings_hdr"):
            hdr = st.columns(COL_WIDTHS)
            for h, label in zip(hdr, ["COMPANY", "TREND", "MARKET PRICE (1D%)", "RETURNS %", "CURRENT (INVESTED)"]):
                h.markdown(f"<span style='font-size:12px;font-weight:600;letter-spacing:0.04em;color:{MUTED};text-transform:uppercase'>{label}</span>", unsafe_allow_html=True)

        with st.container(key="holdings_rows"):
            for _, r in df_sorted.iterrows():
                pnl_val, day_val = r["P&L %"], r["Day %"]
                pnl_color = GREEN if pd.notna(pnl_val) and pnl_val >= 0 else RED
                day_color = GREEN if pd.notna(day_val) and day_val >= 0 else RED
                pnl_disp = f"{pnl_val:+.1f}%" if pd.notna(pnl_val) else "—"
                cmp_val = r["CMP"] if pd.notna(r["CMP"]) else None
                prev_close = (cmp_val / (1 + day_val / 100)) if (cmp_val is not None and pd.notna(day_val)) else None
                day_abs = (cmp_val - prev_close) if (cmp_val is not None and prev_close is not None) else None
                cmp_disp = f"₹{cmp_val:,.2f}" if cmp_val is not None else "—"
                day_line = (f"{day_abs:+,.2f} ({day_val:+.2f}%)" if day_abs is not None else "—")
                pnl_rupee = r["P&L ₹"] if pd.notna(r["P&L ₹"]) else None
                value_disp = f"₹{r['Value']:,.2f}" if pd.notna(r["Value"]) else "—"
                invested_disp = f"₹{r['Invested']:,.2f}" if pd.notna(r["Invested"]) else "—"
                spark = r.get("Spark") or []
                spark_color = GREEN if (spark and spark[-1] >= spark[0]) else RED

                c1, c2, c3, c4, c5, _sp = st.columns(COL_WIDTHS)
                with c1:
                    ac1, ac2 = st.columns([0.5, 3])
                    ac1.markdown(avatar_html(r["Symbol"]), unsafe_allow_html=True)
                    with ac2:
                        if st.button(r["Symbol"], key=f"btn_{r['Symbol']}", use_container_width=True):
                            st.session_state.selected_symbol = r["Symbol"]
                        st.markdown(
                            f"<div class='num' style='font-size:13px;color:{MUTED};margin-top:-14px;padding:0 8px 4px'>"
                            f"{r['Shares']} share{'s' if r['Shares'] != 1 else ''} · avg ₹{r['Avg Price']:.2f}</div>",
                            unsafe_allow_html=True,
                        )
                c2.markdown(f"<div style='padding-top:6px'>{sparkline_svg(spark, spark_color)}</div>", unsafe_allow_html=True)
                c3.markdown(
                    f"<div class='num' style='padding-top:8px;font-size:15px;font-weight:600'>{cmp_disp}</div>"
                    f"<div class='num' style='font-size:13px;color:{day_color}'>{day_line}</div>",
                    unsafe_allow_html=True,
                )
                c4.markdown(
                    f"<div class='num' style='padding-top:8px;color:{pnl_color};font-weight:600;font-size:15px'>{pnl_disp}</div>"
                    + (f"<div class='num' style='font-size:13px;color:{pnl_color}'>{pnl_rupee:+,.2f}</div>" if pnl_rupee is not None else ""),
                    unsafe_allow_html=True,
                )
                c5.markdown(
                    f"<div class='num' style='padding-top:8px;font-size:15px'>{value_disp}</div>"
                    f"<div class='num' style='font-size:13px;color:{MUTED}'>{invested_disp}</div>",
                    unsafe_allow_html=True,
                )
        st.markdown('</div>', unsafe_allow_html=True)

    row = df_sorted[df_sorted["Symbol"] == st.session_state.selected_symbol].iloc[0]

    day_str = f"{row['Day %']:+.2f}%" if pd.notna(row["Day %"]) else "—"
    pnl_str = f"{row['P&L %']:+.2f}%" if pd.notna(row["P&L %"]) else "—"
    pnl_color = GREEN if pd.notna(row["P&L %"]) and row["P&L %"] >= 0 else RED
    day_color = GREEN if pd.notna(row["Day %"]) and row["Day %"] >= 0 else RED
    trend_bullish = not row["EMA Cross Bearish"] if pd.notna(row["EMA Cross Bearish"]) else None
    trend_label = "Bullish" if trend_bullish else ("Bearish" if trend_bullish is False else "N/A")
    trend_dot = GREEN if trend_bullish else (RED if trend_bullish is False else MUTED)
    vol_ratio_str = f"{row['Vol Ratio']:.1f}x" if pd.notna(row["Vol Ratio"]) else "—"

    with col_detail:
        detail = f"""
        <div class="card-alt">
          <div style="font-size:13px;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;color:{MUTED};margin-bottom:4px">
            Selected holding · Rank {row['Rank']} of {len(df_sorted)}
          </div>
          <div style="font-family:'Inter',sans-serif;font-size:24px;font-weight:700;color:{INK};margin-bottom:14px">{row['Symbol']}</div>
          <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:14px">
            <span class="num" style="font-size:26px;font-weight:600">₹{row['CMP']:.2f}</span>
            <span class="num" style="font-size:14px;font-weight:600;color:{day_color}">{day_str} today</span>
          </div>
          <div style="height:1px;background:{BORDER};margin:14px 0"></div>
        """
        st.markdown(detail, unsafe_allow_html=True)

        if pd.notna(row["EMA20"]) and pd.notna(row["EMA50"]):
            vals = [
                ("Avg", row["Avg Price"], MUTED),
                ("EMA50", row["EMA50"], "#5B7A99"),
                ("EMA20", row["EMA20"], "#7A8B5E"),
                ("CMP", row["CMP"], ACCENT),
            ]
            vmin, vmax = min(v[1] for v in vals), max(v[1] for v in vals)
            vrange = (vmax - vmin) or 1
            pad = 8
            dots = ""
            for label, val, color in vals:
                pct = pad + ((val - vmin) / vrange) * (100 - 2 * pad)
                dots += (
                    f"<div class='track-dot' style='left:{pct:.1f}%'>"
                    f"<span class='dot' style='background:{color};box-shadow:0 0 0 1px {color}'></span>"
                    f"<span class='lbl'>{label}</span></div>"
                )
            st.markdown(f"<div style='font-size:13px;color:{MUTED}'>Avg. price vs CMP vs EMAs</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='track-wrap'>{dots}</div>", unsafe_allow_html=True)
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.markdown("<div style='height:1px;background:{BORDER};margin:8px 0'></div>", unsafe_allow_html=True)

        grid_items = [
            ("Unrealized P&L", f"<span style='color:{pnl_color}'>{pnl_str}</span> (₹{row['P&L ₹']:+,.0f})" if pd.notna(row["P&L %"]) else "—"),
            ("Volume vs 20d avg", vol_ratio_str),
            ("Trend", f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:{trend_dot};margin-right:6px'></span>{trend_label}"),
            ("Shares", f"{row['Shares']}"),
            ("Avg. price", f"₹{row['Avg Price']:.2f}"),
            ("Invested", f"₹{row['Invested']:,.0f}"),
            ("Current value", f"₹{row['Value']:,.0f}" if pd.notna(row["Value"]) else "—"),
            ("EMA20", f"₹{row['EMA20']:.2f}" if pd.notna(row["EMA20"]) else "—"),
            ("EMA50", f"₹{row['EMA50']:.2f}" if pd.notna(row["EMA50"]) else "—"),
        ]
        grid_html = "<div style='display:grid;grid-template-columns:1fr 1fr;gap:14px 16px'>"
        for label, value in grid_items:
            grid_html += (
                f"<div><div style='font-size:13px;color:{MUTED};margin-bottom:3px'>{label}</div>"
                f"<div class='num' style='font-size:15px;font-weight:600'>{value}</div></div>"
            )
        grid_html += "</div></div>"
        st.markdown(grid_html, unsafe_allow_html=True)

    # -------------------------------------------------------------------
    # Charts
    # -------------------------------------------------------------------
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="card-alt">', unsafe_allow_html=True)
        st.markdown("<div style='font-size:14px;font-weight:600;margin-bottom:14px'>P&L by stock</div>", unsafe_allow_html=True)
        chart_df = df.dropna(subset=["P&L %"]).sort_values("P&L %")
        fig = go.Figure(go.Bar(
            x=chart_df["P&L %"], y=chart_df["Symbol"], orientation="h",
            marker_color=[GREEN if v >= 0 else RED for v in chart_df["P&L %"]],
            text=[f"{v:+.1f}%" for v in chart_df["P&L %"]], textposition="outside",
        ))
        fig.update_layout(
            showlegend=False, height=420,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color=INK, margin=dict(l=0, r=30, t=10, b=0),
            xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="card-alt">', unsafe_allow_html=True)
        st.markdown("<div style='font-size:14px;font-weight:600;margin-bottom:14px'>Allocation by stock</div>", unsafe_allow_html=True)
        alloc_df = df.dropna(subset=["Value"])
        fig2 = go.Figure(go.Pie(
            labels=alloc_df["Symbol"], values=alloc_df["Value"], hole=0.55,
            marker=dict(colors=PALETTE, line=dict(color=CARD_ALT, width=2)),
            textinfo="label+percent", textfont_size=11,
        ))
        fig2.update_layout(
            height=420, showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)", font_color=INK,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------
    # Footer note
    # -------------------------------------------------------------------
    st.markdown(
        """
        <div class="caption-box">
        Edit <code>HOLDINGS</code> in the script whenever you rebalance. Verify tickers on finance.yahoo.com if any row shows blank prices.<br>
        <b>EMA flags are informational only</b> — your backtests showed EMA-based exits are unvalidated and can hurt returns.
        Your tested exit rule is rank-based (drop from top-25), not EMA.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# TAB: Watchlist (multiple, named)
# =============================================================================
def render_watchlist_tab():
    holding_symbols = set(df["Symbol"].tolist())
    watchlists = load_watchlists()
    portfolios = load_portfolios()
    portfolio_names = list(portfolios.keys())

    if not watchlists:
        watchlists = {"My Watchlist": {"stocks": [], "linked_portfolio": None}}
        save_watchlists(watchlists)

    names = list(watchlists.keys())

    # -- Create a new watchlist (compact row above the tabs) -------------
    with st.container(key="wl_create_row"):
        cr1, cr2 = st.columns([4, 1])
        new_name = cr1.text_input("Create new watchlist", key="wl_new_name", placeholder="e.g. Sigma Top 10", label_visibility="collapsed")
        if cr2.button("➕ New watchlist", use_container_width=True) and new_name.strip():
            if new_name.strip() not in watchlists:
                watchlists[new_name.strip()] = {"stocks": [], "linked_portfolio": None}
                save_watchlists(watchlists)
                st.rerun()
            else:
                st.warning("A watchlist with that name already exists.")

    # -- Browse between watchlists via tabs at the top --------------------
    tabs = st.tabs(names)
    for tab, active_name in zip(tabs, names):
        with tab:
            _render_one_watchlist(active_name, watchlists, portfolios, portfolio_names, holding_symbols)


def _render_one_watchlist(active_name, watchlists, portfolios, portfolio_names, holding_symbols):
    active_wl = watchlists[active_name]
    stocks = active_wl.get("stocks", [])

    col_main, col_tools = st.columns([2.6, 1], gap="medium")

    # ======================================================================
    # RIGHT: tools — link portfolio, delete, upload / add manually
    # ======================================================================
    with col_tools:
        st.markdown('<div class="card-upload">', unsafe_allow_html=True)
        current_link = active_wl.get("linked_portfolio")
        link_options = ["— none —"] + portfolio_names
        link_idx = link_options.index(current_link) if current_link in portfolio_names else 0
        chosen_link = st.selectbox(
            f"Portfolio linked to \"{active_name}\"",
            link_options, index=link_idx, key=f"wl_link_{active_name}",
        )
        if chosen_link != (current_link or "— none —"):
            active_wl["linked_portfolio"] = None if chosen_link == "— none —" else chosen_link
            watchlists[active_name] = active_wl
            save_watchlists(watchlists)
            st.rerun()
        st.caption("Buy/Sell on the left trades this linked portfolio.")

        if len(watchlists) > 1 and st.button("🗑️ Delete this watchlist", key=f"wl_delete_{active_name}", use_container_width=True):
            del watchlists[active_name]
            save_watchlists(watchlists)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card-upload">', unsafe_allow_html=True)
        up_tab, manual_tab = st.tabs(["📤 Upload", "✍️ Manual"])

        with up_tab:
            uploaded = st.file_uploader("Sigma export", type=["xlsx", "xls", "csv"], label_visibility="collapsed", key=f"uploader_{active_name}")
            src_df = None
            if uploaded is not None:
                try:
                    if uploaded.name.lower().endswith(".csv"):
                        src_df = pd.read_csv(uploaded)
                    else:
                        try:
                            src_df = pd.read_excel(uploaded)
                        except ImportError:
                            st.error(
                                "Reading .xlsx needs the `openpyxl` package. Run `pip3 install openpyxl` and retry, "
                                "or export as .csv instead."
                            )
                except Exception as e:
                    st.error(f"Couldn't read that file: {e}")

                if src_df is not None:
                    cols = src_df.columns.tolist()
                    PRICE_WORDS = ("price", "ltp", "close", "cmp", "open", "high", "low", "value")
                    guess_symbol = next((c for c in cols if "symbol" in c.lower() or "stock" in c.lower()), cols[0])
                    guess_score_candidates = [
                        c for c in cols
                        if ("rank" in c.lower() or "perform" in c.lower() or "return" in c.lower() or "score" in c.lower())
                        and not any(w in c.lower() for w in PRICE_WORDS)
                    ]
                    score_options = ["— none (just add symbols) —"] + cols
                    guess_score = guess_score_candidates[0] if guess_score_candidates else score_options[0]

                    symbol_col = st.selectbox("Symbol column", cols, index=cols.index(guess_symbol), key=f"symcol_{active_name}")
                    score_col_choice = st.selectbox(
                        "Rank / score column (never price — live price is always fetched separately)",
                        score_options, index=score_options.index(guess_score), key=f"scorecol_{active_name}",
                    )
                    n_top = st.slider("Top N to add", 1, min(30, len(src_df)), min(10, len(src_df)), key=f"ntop_{active_name}")

                    if st.button(f"Build \"{active_name}\"", key=f"build_{active_name}", use_container_width=True):
                        if score_col_choice == score_options[0]:
                            ranked = src_df[[symbol_col]].dropna().copy()
                            ranked.columns = ["Symbol"]
                            ranked["Score"] = 0.0
                            ranked = ranked.head(n_top).reset_index(drop=True)
                        else:
                            ranked = src_df[[symbol_col, score_col_choice]].dropna()
                            ranked.columns = ["Symbol", "Score"]
                            ranked = ranked.sort_values("Score", ascending=False).head(n_top).reset_index(drop=True)
                        ranked["Symbol"] = ranked["Symbol"].astype(str).str.upper().str.strip()
                        ranked.insert(0, "Rank", ranked.index + 1)
                        active_wl["stocks"] = ranked.to_dict("records")
                        watchlists[active_name] = active_wl
                        save_watchlists(watchlists)
                        st.success(f"\"{active_name}\" saved — top {len(ranked)} stocks. Prices are always fetched live.")
                        st.rerun()

        with manual_tab:
            manual_sym = st.text_input("Symbol (NSE, no .NS)", key=f"manual_sym_{active_name}", placeholder="e.g. TCS")
            manual_score = st.number_input("Score (optional)", value=0.0, step=0.1, key=f"manual_score_{active_name}")
            if st.button("➕ Add to watchlist", key=f"manual_add_{active_name}", use_container_width=True) and manual_sym.strip():
                sym = manual_sym.strip().upper()
                if any(s["Symbol"] == sym for s in stocks):
                    st.warning(f"{sym} is already in \"{active_name}\".")
                else:
                    stocks.append({"Rank": len(stocks) + 1, "Symbol": sym, "Score": manual_score})
                    active_wl["stocks"] = stocks
                    watchlists[active_name] = active_wl
                    save_watchlists(watchlists)
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ======================================================================
    # LEFT: the watchlist's stock table (always visible, tools out of the way)
    # ======================================================================
    with col_main:
        if not stocks:
            st.caption(f"\"{active_name}\" is empty — use the panel on the right to upload a Sigma export or add a symbol manually.")
            return

        wl_symbols = [s["Symbol"] for s in stocks]
        wl_detail = fetch_watchlist_detail(tuple(wl_symbols))

        linked_portfolio = active_wl.get("linked_portfolio")
        session_active_portfolio = st.session_state.get("active_portfolio")
        if linked_portfolio in portfolio_names:
            trade_portfolio = linked_portfolio
        elif session_active_portfolio in portfolio_names:
            trade_portfolio = session_active_portfolio
        elif portfolio_names:
            trade_portfolio = portfolio_names[0]
        else:
            trade_portfolio = None

        trades = load_paper_trades()
        if trade_portfolio:
            positions, cash, _ = compute_paper_positions(trades, trade_portfolio, portfolios[trade_portfolio]["starting_cash"])
        else:
            positions, cash = {}, 0

        if trade_portfolio:
            st.caption(f"Buy/Sell below trade the **{trade_portfolio}** paper portfolio.")
        else:
            st.caption("No paper portfolio exists yet — create one in the Paper Trading tab to enable Buy/Sell here.")

        st.markdown(f'<div class="card" style="padding:0;overflow:hidden;background:{CARD_TABLE};">', unsafe_allow_html=True)
        WL_COL_WIDTHS = [2.4, 0.9, 1.15, 1.15, 0.9, 0.55, 0.55, 0.35]
        hdr = st.columns(WL_COL_WIDTHS)
        for h, label in zip(hdr, ["COMPANY", "TREND", "MKT PRICE", "1D CHANGE", "1D VOL", "", "", ""]):
            h.markdown(f"<span style='font-size:12px;font-weight:600;letter-spacing:0.04em;color:{MUTED};text-transform:uppercase'>{label}</span>", unsafe_allow_html=True)

        for wrow in stocks:
            sym = wrow["Symbol"]
            in_book = sym in holding_symbols
            d = wl_detail.get(sym, {})
            cmp, day_abs, day_pct, volume, spark = d.get("cmp"), d.get("day_abs"), d.get("day_pct"), d.get("volume"), d.get("spark") or []
            cmp_str = f"₹{cmp:,.2f}" if cmp else "—"
            day_color = GREEN if (day_pct is not None and day_pct >= 0) else RED
            day_str = f"{day_abs:+,.2f} ({day_pct:+.2f}%)" if day_abs is not None else "—"
            vol_str = f"{volume:,}" if volume else "—"
            held_qty = positions.get(sym, {"qty": 0})["qty"]
            badge = f"<span style='font-size:10px;font-weight:600;color:{GREEN};background:#1B3B2A;border-radius:4px;padding:1px 5px;margin-left:6px'>in book</span>" if in_book else ""
            paper_badge = f"<span style='font-size:10px;font-weight:600;color:{ACCENT};background:#33304D;border-radius:4px;padding:1px 5px;margin-left:6px'>paper: {held_qty}</span>" if held_qty else ""
            spark_color = GREEN if (spark and spark[-1] >= spark[0]) else RED

            rc1, rc2, rc3, rc4, rc5, rc6, rc7, rc8 = st.columns(WL_COL_WIDTHS)
            with rc1:
                a1, a2 = st.columns([0.5, 3])
                a1.markdown(avatar_html(sym), unsafe_allow_html=True)
                with a2:
                    a2.markdown(f"<div style='padding-top:4px;font-weight:600;font-size:15px'>{sym}{badge}{paper_badge}</div>", unsafe_allow_html=True)
                    a2.markdown(f"<div class='num' style='font-size:12.5px;color:{MUTED}'>Rank #{wrow['Rank']} · score {wrow['Score']:.2f}</div>", unsafe_allow_html=True)
            rc2.markdown(f"<div style='padding-top:10px'>{sparkline_svg(spark, spark_color, width=64)}</div>", unsafe_allow_html=True)
            rc3.markdown(f"<div class='num' style='padding-top:12px;font-size:15px;font-weight:600'>{cmp_str}</div>", unsafe_allow_html=True)
            rc4.markdown(f"<div class='num' style='padding-top:12px;font-size:14px;color:{day_color};font-weight:600'>{day_str}</div>", unsafe_allow_html=True)
            rc5.markdown(f"<div class='num' style='padding-top:12px;font-size:14px;color:{MUTED}'>{vol_str}</div>", unsafe_allow_html=True)

            with rc6:
                with st.container(key=f"wl_buytrig_{active_name}_{sym}"):
                    with st.popover("B", use_container_width=True):
                        st.markdown(f"<div style='font-weight:600;margin-bottom:6px'>Buy {sym}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='num' style='font-size:13px;color:{MUTED};margin-bottom:8px'>Live CMP: {cmp_str}</div>", unsafe_allow_html=True)
                        if trade_portfolio is None:
                            st.caption("No paper portfolio exists yet — create one in the Paper Trading tab.")
                        buy_qty = st.number_input("Qty", min_value=1, value=1, step=1, key=f"wl_buyqty_{active_name}_{sym}")
                        buy_click = st.button("🟢 Confirm Buy", key=f"wl_buy_{active_name}_{sym}", use_container_width=True, disabled=trade_portfolio is None)
            with rc7:
                with st.container(key=f"wl_selltrig_{active_name}_{sym}"):
                    with st.popover("S", use_container_width=True):
                        st.markdown(f"<div style='font-weight:600;margin-bottom:6px'>Sell {sym}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='num' style='font-size:13px;color:{MUTED};margin-bottom:8px'>Live CMP: {cmp_str} · Held: {held_qty}</div>", unsafe_allow_html=True)
                        if trade_portfolio is None:
                            st.caption("No paper portfolio exists yet — create one in the Paper Trading tab.")
                        elif held_qty < 1:
                            st.caption("You don't hold any shares of this stock in the linked portfolio.")
                        sell_qty = st.number_input("Qty", min_value=1, max_value=max(held_qty, 1), value=1, step=1, key=f"wl_sellqty_{active_name}_{sym}")
                        sell_click = st.button("🔴 Confirm Sell", key=f"wl_sell_{active_name}_{sym}", use_container_width=True, disabled=trade_portfolio is None or held_qty < 1)
            with rc8:
                remove_click = st.button("✕", key=f"wl_remove_{active_name}_{sym}", use_container_width=True, help=f"Remove {sym} from this watchlist")

            if buy_click:
                if cmp is None:
                    st.error(f"No live price for {sym} — can't trade.")
                elif buy_qty * cmp > cash:
                    st.error(f"Not enough paper cash (₹{cash:,.0f}) to buy {buy_qty} {sym} @ ₹{cmp:.2f}.")
                else:
                    save_paper_trade(trade_portfolio, sym, "BUY", buy_qty, cmp)
                    st.success(f"Paper-bought {buy_qty} {sym} @ ₹{cmp:.2f} in {trade_portfolio}")
                    st.rerun()
            if sell_click:
                if cmp is None:
                    st.error(f"No live price for {sym} — can't trade.")
                else:
                    save_paper_trade(trade_portfolio, sym, "SELL", sell_qty, cmp)
                    st.success(f"Paper-sold {sell_qty} {sym} @ ₹{cmp:.2f} in {trade_portfolio}")
                    st.rerun()
            if remove_click:
                active_wl["stocks"] = [s for s in stocks if s["Symbol"] != sym]
                watchlists[active_name] = active_wl
                save_watchlists(watchlists)
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)




# =============================================================================
# TAB: Paper Trading (multiple portfolios)
# =============================================================================
def render_paper_trading_tab():
    portfolios = load_portfolios()
    names = list(portfolios.keys())

    # -- Create a new portfolio (compact row above the tabs) --------------
    with st.container(key="pp_create_row"):
        cr1, cr2, cr3 = st.columns([3, 1.3, 1])
        new_port_name = cr1.text_input("New portfolio name", key="new_port_name", placeholder="e.g. Aggressive Momentum", label_visibility="collapsed")
        new_port_cash = cr2.number_input("Starting cash", min_value=1000.0, value=100000.0, step=5000.0, key="new_port_cash")
        if cr3.button("➕ New portfolio", use_container_width=True) and new_port_name.strip():
            if new_port_name.strip() not in portfolios:
                portfolios[new_port_name.strip()] = {"starting_cash": new_port_cash}
                save_portfolios(portfolios)
                st.session_state.active_portfolio = new_port_name.strip()
                st.rerun()
            else:
                st.warning("A portfolio with that name already exists.")

    # -- Browse between portfolios via tabs at the top ---------------------
    tabs = st.tabs(names)
    for tab, name in zip(tabs, names):
        with tab:
            _render_one_portfolio(name, portfolios, names)


def _render_one_portfolio(active_portfolio, portfolios, portfolio_names):
    st.session_state.active_portfolio = active_portfolio

    col_main, col_tools = st.columns([2.6, 1], gap="medium")

    # ======================================================================
    # RIGHT: delete + trade ticket
    # ======================================================================
    with col_tools:
        if len(portfolio_names) > 1:
            with st.container(key=f"pp_delete_{active_portfolio}"):
                if st.button(f"🗑️ Delete \"{active_portfolio}\"", key=f"del_portfolio_{active_portfolio}", use_container_width=True):
                    del portfolios[active_portfolio]
                    save_portfolios(portfolios)
                    st.session_state.active_portfolio = list(portfolios.keys())[0]
                    st.rerun()

    starting_cash = portfolios[active_portfolio]["starting_cash"]
    trades = load_paper_trades()
    positions, cash, realized_pnl = compute_paper_positions(trades, active_portfolio, starting_cash)
    open_symbols = [s for s, p in positions.items() if p["qty"] > 0]

    live_prices = fetch_watchlist_prices(tuple(open_symbols)) if open_symbols else {}

    invested_value = sum(positions[s]["qty"] * positions[s]["avg"] for s in open_symbols)
    holdings_value = sum((positions[s]["qty"] * (live_prices.get(s) or positions[s]["avg"])) for s in open_symbols)
    unrealized_pnl = sum(
        (positions[s]["qty"] * ((live_prices.get(s) or positions[s]["avg"]) - positions[s]["avg"]))
        for s in open_symbols
    )
    total_value = cash + holdings_value
    total_pnl = total_value - starting_cash
    returns_pct = (holdings_value - invested_value) / invested_value * 100 if invested_value else 0

    with col_tools:
        with st.container(key=f"pp_trade_ticket_{active_portfolio}"):
            watchlists = load_watchlists()
            universe = sorted(set(df["Symbol"].tolist()) | set(open_symbols))
            for wl in watchlists.values():
                universe = sorted(set(universe) | {s["Symbol"] for s in wl.get("stocks", [])})

            st.markdown(f"<div style='font-size:14px;font-weight:600;margin-bottom:10px'>Place a trade — {active_portfolio}</div>", unsafe_allow_html=True)

            symbol_choice = st.selectbox("Symbol", universe if universe else ["—"], key=f"paper_symbol_{active_portfolio}")
            manual_symbol = st.text_input("Or type a symbol not listed", key=f"paper_symbol_manual_{active_portfolio}", placeholder="e.g. TCS")
            trade_symbol = manual_symbol.strip().upper() if manual_symbol.strip() else symbol_choice

            qty = st.number_input("Qty", min_value=1, value=1, step=1, key=f"paper_qty_{active_portfolio}")

            live_price = fetch_watchlist_prices((trade_symbol,)).get(trade_symbol) if trade_symbol and trade_symbol != "—" else None
            st.markdown(
                f"<div style='font-size:13px;color:{MUTED};margin-bottom:2px'>Live CMP</div>"
                f"<div class='num' style='font-size:17px;font-weight:600;margin-bottom:10px'>{f'₹{live_price:.2f}' if live_price else '—'}</div>",
                unsafe_allow_html=True,
            )

            bcol, scol = st.columns(2)
            buy_clicked = bcol.button("🟢 Buy", use_container_width=True, key=f"buy_btn_{active_portfolio}")
            sell_clicked = scol.button("🔴 Sell", use_container_width=True, key=f"sell_btn_{active_portfolio}")

            if (buy_clicked or sell_clicked) and trade_symbol and trade_symbol != "—":
                if live_price is None:
                    st.error(f"Couldn't fetch a live price for {trade_symbol} — check the ticker.")
                elif buy_clicked and qty * live_price > cash:
                    st.error(f"Not enough paper cash: need ₹{qty * live_price:,.0f}, have ₹{cash:,.0f}.")
                elif sell_clicked and positions.get(trade_symbol, {"qty": 0})["qty"] < qty:
                    st.error(f"Can't sell {qty} — you only hold {positions.get(trade_symbol, {'qty': 0})['qty']} of {trade_symbol} in {active_portfolio}.")
                else:
                    save_paper_trade(active_portfolio, trade_symbol, "BUY" if buy_clicked else "SELL", qty, live_price)
                    st.success(f"{'Bought' if buy_clicked else 'Sold'} {qty} {trade_symbol} @ ₹{live_price:.2f} in {active_portfolio}")
                    st.rerun()

    # ======================================================================
    # LEFT: metrics, open positions, trade history — always visible
    # ======================================================================
    with col_main:
        with st.container(key=f"pp_metrics_{active_portfolio}"):
            st.caption(f"\"{active_portfolio}\" — practice with virtual money, trades execute at the live CMP, no real capital involved.")

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Cash", f"₹{cash:,.0f}")
            k2.metric("Total Value", f"₹{total_value:,.0f}", f"{(total_pnl / starting_cash * 100):+.2f}%")
            k3.metric("Invested", f"₹{invested_value:,.0f}")
            k4.metric("Returns", f"{returns_pct:+.2f}%")

            j1, j2, j3 = st.columns(3)
            j1.metric("Stocks Held", f"{len(open_symbols)}")
            j2.metric("Realized P&L", f"₹{realized_pnl:,.0f}")
            j3.metric("Unrealized P&L", f"₹{unrealized_pnl:,.0f}")

        # -- Open positions ----------------------------------------------------
        st.subheader(f"Open Positions — {active_portfolio}")
        if not open_symbols:
            st.caption("No open positions yet — place a trade on the right or from a linked Watchlist.")
        else:
            technicals = fetch_technicals(tuple(open_symbols))

            st.markdown(f'<div class="card" style="padding:0;overflow:hidden;background:{CARD_TABLE};">', unsafe_allow_html=True)
            pos_cols = [1.4, 0.7, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.5, 0.5]
            pcols = st.columns(pos_cols)
            for h, label in zip(pcols, ["STOCK", "QTY", "BUY PRICE", "CMP", "P&L %", "BELOW EMA20", "BELOW EMA50", "DEAD CROSS", "", ""]):
                h.markdown(f"<span style='font-size:12px;font-weight:600;letter-spacing:0.04em;color:{MUTED};text-transform:uppercase'>{label}</span>", unsafe_allow_html=True)

            for sym in open_symbols:
                pos = positions[sym]
                cmp = live_prices.get(sym) or pos["avg"]
                pnl_pct = ((cmp - pos["avg"]) / pos["avg"] * 100) if pos["avg"] else 0
                pnl_color = GREEN if pnl_pct >= 0 else RED

                tech = technicals.get(sym)
                if tech:
                    below20_str = "🔴 Yes" if cmp < tech["ema20"] else "🟢 No"
                    below50_str = "🔴 Yes" if cmp < tech["ema50"] else "🟢 No"
                    dead_cross_str = "🔴 Yes" if tech["ema20"] < tech["ema50"] else "🟢 No"
                else:
                    below20_str = below50_str = dead_cross_str = "—"

                pc = st.columns(pos_cols)
                pc[0].markdown(f"<div style='padding-top:6px;font-weight:600'>{sym}</div>", unsafe_allow_html=True)
                pc[1].markdown(f"<div class='num' style='padding-top:6px'>{pos['qty']}</div>", unsafe_allow_html=True)
                pc[2].markdown(f"<div class='num' style='padding-top:6px'>₹{pos['avg']:.2f}</div>", unsafe_allow_html=True)
                pc[3].markdown(f"<div class='num' style='padding-top:6px'>₹{cmp:.2f}</div>", unsafe_allow_html=True)
                pc[4].markdown(f"<div class='num' style='padding-top:6px;color:{pnl_color};font-weight:600'>{pnl_pct:+.1f}%</div>", unsafe_allow_html=True)
                pc[5].markdown(f"<div style='padding-top:6px;font-size:13.5px'>{below20_str}</div>", unsafe_allow_html=True)
                pc[6].markdown(f"<div style='padding-top:6px;font-size:13.5px'>{below50_str}</div>", unsafe_allow_html=True)
                pc[7].markdown(f"<div style='padding-top:6px;font-size:13.5px'>{dead_cross_str}</div>", unsafe_allow_html=True)

                with pc[8]:
                    with st.container(key=f"pos_buytrig_{active_portfolio}_{sym}"):
                        with st.popover("B", use_container_width=True):
                            st.markdown(f"<div style='font-weight:600;margin-bottom:6px'>Buy {sym}</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='num' style='font-size:13px;color:{MUTED};margin-bottom:8px'>Live CMP: ₹{cmp:.2f}</div>", unsafe_allow_html=True)
                            pos_buy_qty = st.number_input("Qty", min_value=1, value=1, step=1, key=f"pos_buyqty_{active_portfolio}_{sym}")
                            pos_buy_click = st.button("🟢 Confirm Buy", key=f"pos_buy_{active_portfolio}_{sym}", use_container_width=True)
                with pc[9]:
                    with st.container(key=f"pos_selltrig_{active_portfolio}_{sym}"):
                        with st.popover("S", use_container_width=True):
                            st.markdown(f"<div style='font-weight:600;margin-bottom:6px'>Sell {sym}</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='num' style='font-size:13px;color:{MUTED};margin-bottom:8px'>Live CMP: ₹{cmp:.2f} · Held: {pos['qty']}</div>", unsafe_allow_html=True)
                            pos_sell_qty = st.number_input("Qty", min_value=1, max_value=max(pos['qty'], 1), value=1, step=1, key=f"pos_sellqty_{active_portfolio}_{sym}")
                            pos_sell_click = st.button("🔴 Confirm Sell", key=f"pos_sell_{active_portfolio}_{sym}", use_container_width=True)

                if pos_buy_click:
                    if cmp is None:
                        st.error(f"No live price for {sym} — can't trade.")
                    elif pos_buy_qty * cmp > cash:
                        st.error(f"Not enough paper cash (₹{cash:,.0f}) to buy {pos_buy_qty} {sym} @ ₹{cmp:.2f}.")
                    else:
                        save_paper_trade(active_portfolio, sym, "BUY", pos_buy_qty, cmp)
                        st.success(f"Bought {pos_buy_qty} {sym} @ ₹{cmp:.2f} in {active_portfolio}")
                        st.rerun()
                if pos_sell_click:
                    save_paper_trade(active_portfolio, sym, "SELL", pos_sell_qty, cmp)
                    st.success(f"Sold {pos_sell_qty} {sym} @ ₹{cmp:.2f} in {active_portfolio}")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # -- Trade history --------------------------------------------------
        port_trades = trades[trades["Portfolio"] == active_portfolio] if not trades.empty else trades
        with st.expander(f"Trade History — {active_portfolio} ({len(port_trades)})", expanded=False):
            if port_trades.empty:
                st.caption("No trades yet in this portfolio.")
            else:
                hist = port_trades.sort_values("Timestamp", ascending=False).copy()
                hist["Timestamp"] = hist["Timestamp"].dt.strftime("%d %b %Y, %H:%M")
                st.dataframe(hist.drop(columns=["Portfolio"]), use_container_width=True, hide_index=True)

                if st.button(f"🗑️ Reset \"{active_portfolio}\" (clear its trades)", key=f"reset_{active_portfolio}"):
                    trades = trades[trades["Portfolio"] != active_portfolio]
                    trades.to_csv(PAPER_TRADES_FILE, index=False)
                    st.rerun()


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_holdings, tab_watchlist, tab_paper = st.tabs(["📊 Holdings", "🔭 Watchlist", "📝 Paper Trading"])

with tab_holdings:
    render_holdings_tab()

with tab_watchlist:
    render_watchlist_tab()

with tab_paper:
    render_paper_trading_tab()
