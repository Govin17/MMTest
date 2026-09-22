"""
Momentum Portfolio Dashboard
-----------------------------
A local, browser-based dashboard for tracking your momentum portfolio.
Runs on your own computer — Yahoo Finance data won't work in a cloud sandbox.

Setup (one time):
    pip3 install streamlit yfinance pandas plotly

Run:
    python3 -m streamlit run momentum_dashboard.py

Edit the HOLDINGS list below whenever you buy/sell or rebalance.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Momentum Tracker", page_icon="📈", layout="wide")

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {
        background: #1a1c23;
        border: 1px solid #2d2f39;
        border-radius: 10px;
        padding: 16px 20px;
    }
    [data-testid="stMetricLabel"] {font-size: 0.85rem; opacity: 0.7;}
    [data-testid="stMetricValue"] {font-size: 1.6rem; font-weight: 700;}
    h1 {font-weight: 800; letter-spacing: -0.5px;}
    h3 {margin-top: 0.5rem;}
    .stDataFrame {border-radius: 10px; overflow: hidden;}
    .badge {
        display: inline-block; padding: 3px 10px; border-radius: 12px;
        font-size: 0.78rem; font-weight: 700;
    }
    .badge-red {background: #3a1a1a; color: #ff6b6b;}
    .badge-green {background: #1a3a24; color: #4ade80;}
    .caption-box {
        background: #1a1c23; border-radius: 8px; padding: 12px 16px;
        font-size: 0.82rem; opacity: 0.75; margin-top: 1rem;
    }
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
    for ticker, shares, avg_price in holdings:
        cmp, prev_close, ema20, ema50 = None, None, None, None
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            cmp = round(float(hist["Close"].iloc[-1]), 2) if not hist.empty else None
            prev_close = round(float(hist["Close"].iloc[-2]), 2) if len(hist) > 1 else cmp

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
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
c1, c2 = st.columns([5, 1])
with c1:
    st.title("📈 Momentum Portfolio Tracker")
    st.caption(f"Last refreshed: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
with c2:
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        fetch_prices.clear()

df = fetch_prices(HOLDINGS)

# ---------------------------------------------------------------------------
# Summary cards
# ---------------------------------------------------------------------------
total_invested = df["Invested"].sum()
total_current = df["Value"].sum(skipna=True)
total_pnl = total_current - total_invested
total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0
n_below20 = int(df["Below EMA20"].sum())
n_below50 = int(df["Below EMA50"].sum())

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Invested", f"₹{total_invested:,.0f}")
k2.metric("Current Value", f"₹{total_current:,.0f}")
k3.metric("Total P&L", f"₹{total_pnl:,.0f}", f"{total_pnl_pct:+.2f}%")
k4.metric("Below EMA20", f"{n_below20} stocks", delta=None, delta_color="off")
k5.metric("Below EMA50", f"{n_below50} stocks", delta=None, delta_color="off")

st.write("")

# ---------------------------------------------------------------------------
# Holdings table
# ---------------------------------------------------------------------------
st.subheader("Holdings")

display_df = df.copy()
display_df["Below EMA20"] = display_df["Below EMA20"].map({True: "🔴 Yes", False: "🟢 No"})
display_df["Below EMA50"] = display_df["Below EMA50"].map({True: "🔴 Yes", False: "🟢 No"})
display_df["EMA Cross Bearish"] = display_df["EMA Cross Bearish"].map({True: "🔴 Bearish", False: "🟢 Bullish"})


def highlight_pnl(val):
    if pd.isna(val):
        return ""
    return "color:#4ade80; font-weight:600" if val >= 0 else "color:#ff6b6b; font-weight:600"


def highlight_day(val):
    if pd.isna(val):
        return ""
    return "color:#4ade80" if val >= 0 else "color:#ff6b6b"


styled = display_df.style.format({
    "Avg Price": "₹{:.2f}", "CMP": "₹{:.2f}", "Day %": "{:+.2f}%",
    "Invested": "₹{:.0f}", "Value": "₹{:.0f}",
    "P&L ₹": "₹{:+.0f}", "P&L %": "{:+.2f}%",
    "EMA20": "₹{:.2f}", "EMA50": "₹{:.2f}",
}).map(highlight_pnl, subset=["P&L ₹", "P&L %"]) \
  .map(highlight_day, subset=["Day %"])

st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
    height=460,
    column_config={
        "Symbol": st.column_config.TextColumn(width="small"),
    },
)

st.write("")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("P&L by Stock")
    chart_df = df.dropna(subset=["P&L %"]).sort_values("P&L %")
    fig = px.bar(
        chart_df, x="P&L %", y="Symbol", orientation="h",
        color="P&L %", color_continuous_scale=["#ff6b6b", "#3a3d47", "#4ade80"],
        color_continuous_midpoint=0, text="P&L %",
    )
    fig.update_traces(texttemplate="%{text:+.1f}%", textposition="outside")
    fig.update_layout(
        showlegend=False, height=420, coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=20, t=10, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("Allocation by Stock")
    alloc_df = df.dropna(subset=["Value"])
    fig2 = px.pie(
        alloc_df, values="Value", names="Symbol", hole=0.5,
    )
    fig2.update_traces(textinfo="label+percent", textfont_size=11)
    fig2.update_layout(
        height=420, showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------------------------
# Footer note
# ---------------------------------------------------------------------------
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
