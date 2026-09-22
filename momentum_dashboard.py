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
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Momentum Tracker", page_icon="📈", layout="wide")

GREEN = "#2E7D4F"
RED = "#B23A2E"
ACCENT = "#A9713F"
BG = "#F6F2E9"
CARD = "#FFFFFF"
BORDER = "#E6DFCF"
INK = "#211C15"
MUTED = "#8A8171"
PALETTE = ["#A9713F", "#7A8B5E", "#5B7A99", "#B3703F", "#8B6B9C", "#6E9385",
           "#C08A4F", "#5E7FA6", "#9C7A5E", "#7A9C6E", "#A65E7A", "#6E8B9C"]
WATCHLIST_FILE = "watchlist.csv"

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
    .stApp {{ background: {BG}; font-family: 'Public Sans', sans-serif; }}
    .block-container {{ padding-top: 2.2rem; padding-bottom: 2.5rem; }}
    h1, h2, h3, h4 {{ font-family: 'Source Serif 4', serif; color: {INK}; letter-spacing: -0.01em; }}
    p, span, div, label {{ color: {INK}; }}
    .stCaption, [data-testid="stCaptionContainer"] {{ color: {MUTED} !important; }}
    .num {{ font-family: 'IBM Plex Mono', monospace; font-variant-numeric: tabular-nums; }}

    [data-testid="stMetric"] {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 16px 20px;
    }}
    [data-testid="stMetricLabel"] {{ font-size: 0.78rem; letter-spacing: 0.03em; text-transform: uppercase; color: {MUTED}; }}
    [data-testid="stMetricValue"] {{ font-size: 1.5rem; font-weight: 700; color: {INK}; }}

    div[data-testid="stVerticalBlock"] div.stButton > button {{
        background: transparent; border: none; box-shadow: none;
        text-align: left; padding: 4px 8px; width: 100%;
        border-bottom: 1px solid #F1ECE0; border-radius: 0;
        font-weight: 600; color: {INK}; min-height: 0;
    }}
    div[data-testid="stVerticalBlock"] div.stButton > button:hover {{ background: {BG}; }}
    div[data-testid="stVerticalBlock"] div.stButton > button:focus:not(:active) {{ color: {INK}; }}
    div.stButton {{ margin: 0; }}

    .st-key-holdings_rows div[data-testid="stHorizontalBlock"],
    .st-key-holdings_hdr div[data-testid="stHorizontalBlock"] {{ gap: 4px !important; }}
    .st-key-holdings_rows [data-testid="column"] {{ padding-top: 0; padding-bottom: 0; }}

    .st-key-sort_pills div.stButton > button {{
        border-radius: 999px !important; height: 26px; padding: 0 12px !important;
        font-size: 11.5px !important; font-weight: 600 !important;
        border: 1px solid #E6DFCF !important; background: #FFFFFF !important;
        width: auto !important; min-height: 0 !important;
    }}
    .st-key-sort_pills div.stButton > button:hover {{ background: #EFE7D8 !important; }}
    .st-key-sort_pills div[data-testid="stHorizontalBlock"] {{ gap: 6px !important; }}

    .st-key-pv_timeframe div.stButton > button {{
        border-radius: 999px !important; height: 24px; padding: 0 11px !important;
        font-size: 11px !important; font-weight: 600 !important;
        border: 1px solid #E6DFCF !important; background: #FFFFFF !important;
        width: auto !important; min-height: 0 !important;
    }}
    .st-key-pv_timeframe div.stButton > button:hover {{ background: #EFE7D8 !important; }}

    .card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 22px 24px; }}
    .caption-box {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px;
        padding: 12px 16px; font-size: 0.82rem; color: {MUTED}; margin-top: 1rem;
    }}
    .track-wrap {{ position: relative; height: 4px; background: #F1ECE0; border-radius: 2px; margin: 30px 10px 6px; }}
    .track-dot {{ position: absolute; top: 50%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; gap: 4px; }}
    .track-dot .dot {{ width: 10px; height: 10px; border-radius: 50%; border: 2px solid #FFF; display: block; }}
    .track-dot .lbl {{ font-size: 10px; color: {MUTED}; white-space: nowrap; margin-top: 10px; }}

    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
    .stTabs [data-baseweb="tab"] {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px 8px 0 0;
        padding: 8px 18px; font-weight: 600; color: {MUTED};
    }}
    .stTabs [aria-selected="true"] {{ color: {INK} !important; border-bottom: 2px solid {ACCENT} !important; }}
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


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
c1, c2 = st.columns([5, 1])
with c1:
    st.markdown(
        f"<div style='display:flex;align-items:baseline;gap:14px'>"
        f"<h1 style='margin:0;font-size:32px'>Momentum Portfolio Tracker</h1>"
        f"<span style='font-size:13px;color:{MUTED}'>12-stock NSE momentum book</span></div>",
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

        st.markdown('<div class="card" style="padding-bottom:12px;">', unsafe_allow_html=True)

        with st.container(key="pv_timeframe"):
            tf_cols = st.columns([1.3] + [0.55] * len(TIMEFRAMES) + [0.9] + [3])
            tf_cols[0].markdown("<span style='font-size:13px;font-weight:600;padding-top:2px;display:block'>Portfolio value</span>", unsafe_allow_html=True)
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
            f"<span style='font-size:12px;color:{MUTED}'>{label_txt} · {len(pv_view)} sessions</span>"
            f"<span class='num' style='font-size:12px;font-weight:600;color:{pv_color}'>{pv_pct:+.1f}% over period</span></div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig_pv, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
        st.write("")

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

    st.write("")

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
    TABLE_BG = "#EFE6D3"   # darker beige for the holdings table
    # 7 content columns + a trailing spacer so real columns hug together instead of spreading full width
    COL_WIDTHS = [0.35, 2.1, 0.75, 0.95, 0.65, 0.65, 0.45, 1.6]

    df_sorted = df_sorted.sort_values(
        st.session_state.sort_key,
        ascending=(st.session_state.sort_dir == "asc"),
        na_position="last",
    ).reset_index(drop=True)

    col_table, col_detail = st.columns([2, 1], gap="medium")

    with col_table:
        st.markdown(f'<div class="card" style="padding:0;overflow:hidden;background:{TABLE_BG};">', unsafe_allow_html=True)

        with st.container(key="sort_pills"):
            sp_cols = st.columns([0.35, 0.32, 0.32, 0.34, 0.44, 6])
            sp_cols[0].markdown(f"<span style='font-size:11px;font-weight:600;color:{MUTED};text-transform:uppercase;padding-top:4px;display:block'>Sort</span>", unsafe_allow_html=True)
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
            for h, label in zip(hdr, ["RANK", "STOCK", "CMP", "EXPOSURE", "DAY %", "P&L %", "TREND"]):
                h.markdown(f"<span style='font-size:11px;font-weight:600;letter-spacing:0.04em;color:{MUTED};text-transform:uppercase'>{label}</span>", unsafe_allow_html=True)

        with st.container(key="holdings_rows"):
            for _, r in df_sorted.iterrows():
                pnl_val, day_val = r["P&L %"], r["Day %"]
                pnl_color = GREEN if pd.notna(pnl_val) and pnl_val >= 0 else RED
                day_color = GREEN if pd.notna(day_val) and day_val >= 0 else RED
                pnl_disp = f"{pnl_val:+.1f}%" if pd.notna(pnl_val) else "—"
                day_disp = f"{day_val:+.1f}%" if pd.notna(day_val) else "—"
                cmp_disp = f"₹{r['CMP']:.0f}" if pd.notna(r["CMP"]) else "—"
                exposure_disp = f"₹{r['Value']:,.0f}" if pd.notna(r["Value"]) else "—"
                dot = GREEN if r["EMA Cross Bearish"] is False else (RED if r["EMA Cross Bearish"] is True else MUTED)

                c1, c2, c3, c4, c5, c6, c7, _sp = st.columns(COL_WIDTHS)
                c1.markdown(f"<div class='num' style='padding-top:8px;color:{MUTED};font-size:12px'>{r['Rank']}</div>", unsafe_allow_html=True)
                with c2:
                    if st.button(r["Symbol"], key=f"btn_{r['Symbol']}", use_container_width=True):
                        st.session_state.selected_symbol = r["Symbol"]
                    st.markdown(
                        f"<div class='num' style='font-size:11px;color:{MUTED};margin-top:-14px;padding:0 8px 4px'>"
                        f"{r['Shares']} sh · avg ₹{r['Avg Price']:.2f}</div>",
                        unsafe_allow_html=True,
                    )
                c3.markdown(f"<div class='num' style='padding-top:8px'>{cmp_disp}</div>", unsafe_allow_html=True)
                c4.markdown(f"<div class='num' style='padding-top:8px'>{exposure_disp}</div>", unsafe_allow_html=True)
                c5.markdown(f"<div class='num' style='padding-top:8px;color:{day_color};font-weight:600'>{day_disp}</div>", unsafe_allow_html=True)
                c6.markdown(f"<div class='num' style='padding-top:8px;color:{pnl_color};font-weight:600'>{pnl_disp}</div>", unsafe_allow_html=True)
                c7.markdown(f"<div style='padding-top:10px'><span style='width:9px;height:9px;border-radius:50%;background:{dot};display:inline-block'></span></div>", unsafe_allow_html=True)
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
        <div class="card">
          <div style="font-size:11px;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;color:{MUTED};margin-bottom:4px">
            Selected holding · Rank {row['Rank']} of {len(df_sorted)}
          </div>
          <div style="font-family:'Source Serif 4',serif;font-size:24px;font-weight:600;color:{INK};margin-bottom:14px">{row['Symbol']}</div>
          <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:14px">
            <span class="num" style="font-size:26px;font-weight:600">₹{row['CMP']:.2f}</span>
            <span class="num" style="font-size:14px;font-weight:600;color:{day_color}">{day_str} today</span>
          </div>
          <div style="height:1px;background:#EFE9DA;margin:14px 0"></div>
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
            st.markdown(f"<div style='font-size:11px;color:{MUTED}'>Avg. price vs CMP vs EMAs</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='track-wrap'>{dots}</div>", unsafe_allow_html=True)
            st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
            st.markdown("<div style='height:1px;background:#EFE9DA;margin:8px 0'></div>", unsafe_allow_html=True)

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
                f"<div><div style='font-size:11px;color:{MUTED};margin-bottom:3px'>{label}</div>"
                f"<div class='num' style='font-size:14.5px;font-weight:600'>{value}</div></div>"
            )
        grid_html += "</div></div>"
        st.markdown(grid_html, unsafe_allow_html=True)

    st.write("")

    # -------------------------------------------------------------------
    # Charts
    # -------------------------------------------------------------------
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<div style='font-size:13px;font-weight:600;margin-bottom:16px'>P&L by stock</div>", unsafe_allow_html=True)
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
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<div style='font-size:13px;font-weight:600;margin-bottom:16px'>Allocation by stock</div>", unsafe_allow_html=True)
        alloc_df = df.dropna(subset=["Value"])
        fig2 = go.Figure(go.Pie(
            labels=alloc_df["Symbol"], values=alloc_df["Value"], hole=0.55,
            marker=dict(colors=PALETTE, line=dict(color=CARD, width=2)),
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
# TAB: Watchlist
# =============================================================================
def render_watchlist_tab():
    holding_symbols = set(df["Symbol"].tolist())

    st.markdown('<div class="card">', unsafe_allow_html=True)

    with st.expander("📤 Upload Sigma Scanner export (.xlsx / .csv)", expanded=True):
        uploaded = st.file_uploader("Sigma export", type=["xlsx", "xls", "csv"], label_visibility="collapsed")

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
                            "Reading .xlsx files needs the `openpyxl` package, which isn't installed yet. "
                            "Run `pip3 install openpyxl` in your terminal, restart the dashboard, and try again. "
                            "Or export the Sigma Scanner file as .csv instead — that works without any extra install."
                        )
            except Exception as e:
                st.error(f"Couldn't read that file: {e}")

            if src_df is not None:
                st.dataframe(src_df.head(10), use_container_width=True, hide_index=True)

                cols = src_df.columns.tolist()
                guess_symbol = next((c for c in cols if "symbol" in c.lower() or "stock" in c.lower()), cols[0])
                guess_score = next((c for c in cols if "rank" in c.lower() or "perform" in c.lower() or "return" in c.lower() or "score" in c.lower()), cols[-1])

                sc1, sc2 = st.columns(2)
                symbol_col = sc1.selectbox("Symbol column", cols, index=cols.index(guess_symbol))
                score_col = sc2.selectbox("Rank / score column", cols, index=cols.index(guess_score))

                n_top = st.slider("How many top-ranked stocks to add to the watchlist?", 1, min(30, len(src_df)), min(10, len(src_df)))

                if st.button("Build watchlist from this file"):
                    ranked = src_df[[symbol_col, score_col]].dropna()
                    ranked.columns = ["Symbol", "Score"]
                    ranked["Symbol"] = ranked["Symbol"].astype(str).str.upper().str.strip()
                    ranked = ranked.sort_values("Score", ascending=False).head(n_top).reset_index(drop=True)
                    ranked.insert(0, "Rank", ranked.index + 1)
                    ranked.to_csv(WATCHLIST_FILE, index=False)
                    st.success(f"Watchlist saved — top {len(ranked)} stocks.")
                    st.rerun()

    st.write("")

    try:
        watchlist_df = pd.read_csv(WATCHLIST_FILE)
    except FileNotFoundError:
        watchlist_df = None

    if watchlist_df is None or watchlist_df.empty:
        st.caption("No watchlist yet — upload a Sigma Scanner export above to build one.")
    else:
        wl_symbols = watchlist_df["Symbol"].tolist()
        wl_prices = fetch_watchlist_prices(tuple(wl_symbols))

        wl_cols = st.columns(3)
        for i, wrow in watchlist_df.iterrows():
            sym = wrow["Symbol"]
            in_book = sym in holding_symbols
            cmp = wl_prices.get(sym)
            cmp_str = f"₹{cmp:,.2f}" if cmp else "—"
            badge = f"<span style='font-size:9.5px;font-weight:600;color:{GREEN};background:#E9F3EC;border-radius:4px;padding:1px 5px;margin-left:6px'>in book</span>" if in_book else ""
            card_html = f"""
            <div style="border:1px dashed #DED4BC;border-radius:8px;padding:14px 16px;margin-bottom:14px">
              <div style="display:flex;align-items:baseline;justify-content:space-between">
                <span style="font-size:14px;font-weight:600">{sym}{badge}</span>
                <span class="num" style="font-size:11px;color:{MUTED}">Rank #{int(wrow['Rank'])}</span>
              </div>
              <div style="display:flex;align-items:baseline;justify-content:space-between;margin-top:4px">
                <span class="num" style="font-size:14px">{cmp_str}</span>
                <span class="num" style="font-size:12.5px;font-weight:600;color:{ACCENT}">score {wrow['Score']:.2f}</span>
              </div>
            </div>
            """
            wl_cols[i % 3].markdown(card_html, unsafe_allow_html=True)

        if st.button("🗑️ Clear watchlist"):
            os.remove(WATCHLIST_FILE)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_holdings, tab_watchlist = st.tabs(["📊 Holdings", "🔭 Watchlist"])

with tab_holdings:
    render_holdings_tab()

with tab_watchlist:
    render_watchlist_tab()
