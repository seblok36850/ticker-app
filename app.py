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
    .sec{color:#6db3f2;font-size:21px;font-weight:500;margin:0 0 4px}
    .chart{border:1px solid #2a2e36;border-radius:10px;padding:6px 8px;margin-top:6px}
    .chart span{font-size:12px;color:#9aa1ad}
    label, .stTextInput label p{color:#9aa1ad !important}
    </style>""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def _fetch(path):
    r = requests.get(BASE + path, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def get(path):
    try:
        return _fetch(path)
    except requests.RequestException:
        return None


def short(n):
    if n is None:
        return "N/A"
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= limit:
            return f"{n / limit:.3g}{suffix}"
    return f"{n:.0f}"


def chart_svg(closes):
    w, h, pad = 390, 130, 8
    hi = max(closes) or 1
    n = len(closes) - 1
    pts = [(i / n * w, h - pad - c / hi * (h - 2 * pad)) for i, c in enumerate(closes)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    fmt = (lambda v: f"${v:,.0f}") if hi >= 10 else (lambda v: f"${v:.2f}")
    grid = ""
    for frac in (0, 0.5, 1):
        y = h - pad - frac * (h - 2 * pad)
        grid += f'<line x1="0" x2="{w}" y1="{y:.1f}" y2="{y:.1f}" stroke="#2a2e36" stroke-width="1"/>'
        grid += f'<text x="{w + 6}" y="{y + 4:.1f}" fill="#9aa1ad" font-size="11">{fmt(hi * frac)}</text>'
    end_x, end_y = pts[-1]
    return (
        f'<svg viewBox="0 0 {w + 50} {h}" style="width:100%;display:block">{grid}'
        f'<polyline fill="none" stroke="#d8dce3" stroke-width="1.2" points="{line}"/>'
        f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="3" fill="#6db3f2"/></svg>'
    )


def split_text(s):
    a, b = s.get("split_from"), s.get("split_to")
    if a is None or b is None:
        return None
    if a > b:
        kind, ratio = "reverse split", f"{a:g}:{b:g}"
    else:
        kind, ratio = "split", f"{b:g}:{a:g}"
    return f"{ratio} {kind} on {s.get('execution_date', '')}"


ticker = st.text_input("Ticker", value="AMOD", max_chars=6).strip().upper()

if ticker:
    start = date.today() - timedelta(days=365)
    bars = get(f"/v2/aggs/ticker/{ticker}/range/1/day/{start}/{date.today()}?adjusted=true&sort=asc&limit=5000")
    info = get(f"/v3/reference/tickers/{ticker}")
    splits = get(f"/v3/reference/splits?ticker={ticker}&order=desc&limit=3")

    if not bars or not bars.get("results") or len(bars["results"]) < 2:
        st.write(f"No data found for {ticker}, or the free plan's 5-requests-per-minute limit was hit. Wait a minute and try again.")
    else:
        res = bars["results"]
        last, prev = res[-1], res[-2]
        change = (last["c"] - prev["c"]) / prev["c"] * 100
        recent = res[-30:]
        d = (info or {}).get("results", {})
        exch = EXCHANGES.get(d.get("primary_exchange"), d.get("primary_exchange", ""))
        shares = d.get("share_class_shares_outstanding") or d.get("weighted_shares_outstanding")
        stats = [
            ("Prev Close", f"${prev['c']:.2f}"),
            ("Market Cap", short(d.get("market_cap"))),
            ("OS", short(shares)),
            ("Vol Avg.", short(sum(b["v"] for b in recent) / len(recent))),
        ]
        cells = "".join(f"<div><small>{k}</small><b>{v}</b></div>" for k, v in stats)
        cls = "up" if change >= 0 else "down"

        split_lines = [t for t in (split_text(s) for s in (splits or {}).get("results", [])) if t]
        split_html = "".join(f"<div>• {html.escape(t)}</div>" for t in split_lines) or '<div class="mute">No recent splits.</div>'

        card = (
            f'<div class="card"><h1>{ticker} - ${last["c"]:.2f} '
            f'<span class="{cls}">({change:+.2f}%)</span></h1>'
            f'<div class="mute">{html.escape(d.get("name", ""))}</div>'
            f'<div class="mute">{html.escape(exch)}</div>'
            f'<p class="desc">{html.escape(d.get("description", "")[:220])}</p><hr>'
            f'<div class="grid">{cells}</div><hr>'
            f'<div class="sec">Recent Splits</div>{split_html}<hr>'
            f'<div class="chart"><span>Daily 1Y</span>{chart_svg([b["c"] for b in res])}</div></div>'
        )
        st.markdown(card, unsafe_allow_html=True)
