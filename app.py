import html
from datetime import date, timedelta

import requests
import streamlit as st

st.set_page_config(page_title="Ticker lookup", layout="centered")

BASE = "https://api.massive.com"
HEADERS = {"Authorization": f"Bearer {st.secrets['MASSIVE_API_KEY']}"}
EXCHANGES = {"XNAS": "NASDAQ", "XNYS": "NYSE", "XASE": "NYSE American"}

st.markdown(
    """<style>
    .stApp{background:#0f1115}
    .card{background:#181b21;border:1px solid #2a2e36;border-radius:18px;padding:16px;color:#f1f3f6;font-family:system-ui,sans-serif}
    .card h1{font-size:28px;font-weight:500;margin:0;padding:0;color:#f1f3f6}
    .up{color:#22e05a}.down{color:#ff3b3b}.mute{color:#9aa1ad}
    .desc{color:#6f7682;font-size:14px;line-height:1.35}
    .card hr{border:0;border-top:1px solid #2a2e36;margin:12px 0}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 16px}
    .grid small{color:#9aa1ad;font-size:13px;display:block}.grid b{font-weight:400;font-size:20px}
    label, .stTextInput label p{color:#9aa1ad !important}
    </style>""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def get(path):
    r = requests.get(BASE + path, headers=HEADERS, timeout=15)
    return r.json() if r.status_code == 200 else None


def short(n):
    if n is None:
        return "N/A"
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= limit:
            return f"{n / limit:.3g}{suffix}"
    return f"{n:.0f}"


ticker = st.text_input("Ticker", value="AMOD", max_chars=6).strip().upper()

if ticker:
    start = date.today() - timedelta(days=60)
    bars = get(f"/v2/aggs/ticker/{ticker}/range/1/day/{start}/{date.today()}?adjusted=true&sort=desc&limit=30")
    info = get(f"/v3/reference/tickers/{ticker}")

    if not bars or not bars.get("results") or len(bars["results"]) < 2:
        st.write(f"No data found for {ticker}, or the free plan's 5-requests-per-minute limit was hit. Wait a minute and try again.")
    else:
        res = bars["results"]
        last, prev = res[0], res[1]
        change = (last["c"] - prev["c"]) / prev["c"] * 100
        d = (info or {}).get("results", {})
        exch = EXCHANGES.get(d.get("primary_exchange"), d.get("primary_exchange", ""))
        shares = d.get("share_class_shares_outstanding") or d.get("weighted_shares_outstanding")
        stats = [
            ("Prev Close", f"${prev['c']:.2f}"),
            ("Market Cap", short(d.get("market_cap"))),
            ("OS", short(shares)),
            ("Vol Avg.", short(sum(b["v"] for b in res) / len(res))),
        ]
        cells = "".join(f"<div><small>{k}</small><b>{v}</b></div>" for k, v in stats)
        cls = "up" if change >= 0 else "down"
        card = (
            f'<div class="card"><h1>{ticker} - ${last["c"]:.2f} '
            f'<span class="{cls}">({change:+.2f}%)</span></h1>'
            f'<div class="mute">{html.escape(d.get("name", ""))}</div>'
            f'<div class="mute">{html.escape(exch)}</div>'
            f'<p class="desc">{html.escape(d.get("description", "")[:220])}</p><hr>'
            f'<div class="grid">{cells}</div></div>'
        )
        st.markdown(card, unsafe_allow_html=True)
