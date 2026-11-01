import csv
import html
import io
import time
from datetime import date, datetime, timedelta

import requests
import streamlit as st

st.set_page_config(page_title="Ticker lookup", layout="centered")

LOGO = "data:image/webp;base64,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"  # company logo, embedded so no extra file is needed
BASE = "https://api.massive.com"
HEADERS = {"Authorization": f"Bearer {st.secrets['MASSIVE_API_KEY']}"}
EXCHANGES = {"XNAS": "NASDAQ", "XNYS": "NYSE", "XASE": "NYSE American"}
BUCKETS = [(0, 10), (10, 30), (30, 50), (50, 80), (80, 250), (250, 800)]
LOOKBACK_DAYS = 427
SEC_UA = st.secrets.get("SEC_USER_AGENT", "")  # e.g. "TickerApp you@example.com"; kept in secrets, not in code
CASH_TAGS = ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "Cash"]
INVEST_TAGS = ["ShortTermInvestments", "MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesDebtSecuritiesCurrent"]
OCF_TAGS = ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"]
SHARE_TAGS = ["EntityCommonStockSharesOutstanding"]  # share count on the cover of each 10-Q / 10-K
WARRANT_TAGS = ["ClassOfWarrantOrRightOutstanding"]
EXERCISE_TAGS = ["ClassOfWarrantOrRightExercisePriceOfWarrantsOrRights"]
SHELF_FORMS = ("S-3", "F-3")  # shelf registration statements (includes the ASR variants)
OFFERING_FORMS = ("424B", "S-1", "S-3", "F-1", "F-3")  # prospectuses and registration statements

NASDAQ_FILES = {
    "th": "https://www.nasdaqtrader.com/dynamic/symdir/regsho/nasdaqth{d}.txt",     # Reg SHO threshold list (pipe-separated)
    "sh": "https://www.nasdaqtrader.com/dynamic/symdir/shorthalts/shorthalts{d}.txt",  # short sale circuit breaker list (comma-separated)
}

# Risk rating rules. Change these numbers to change how the badges are scored.
RULES = {
    "recent_days": 90,        # Offering = High if an offering filing appeared within this many days
    "freq_high": 4,           # Frequency = High at this many prospectus filings in 12 months...
    "freq_med": 2,            # ...Medium at this many
    "dilution_high": 0.50,    # Dilution = High if share count grew this much in a year (split-adjusted)
    "dilution_med": 0.15,
    "warrants_high": 0.50,    # Warrants = High if outstanding warrants are this share of shares outstanding
    "warrants_med": 0.20,
    "cash_months_high": 6,    # Cash Need = High if fewer than this many months of cash are left
    "cash_months_med": 12,
}

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
    .chart .r{float:right}
    .tbl{width:100%;border-collapse:collapse;font-size:12px;margin-top:6px}
    .tbl th{background:#444a54;font-weight:500;padding:3px;color:#f1f3f6}
    .tbl td{padding:3px 4px;text-align:center;border:1px solid #2a2e36;color:#f1f3f6}
    .tbl td:first-child{text-align:left}
    .tbl tr.hl td{background:#1d2d44}
    .flags{font-size:14px;color:#9aa1ad;margin-top:2px}
    .note{color:#6f7682;font-size:11px;line-height:1.3;margin-top:8px}
    .badges{display:grid;grid-template-columns:repeat(6,1fr);gap:6px}
    .badges small{display:block;color:#9aa1ad;font-size:12px;margin-bottom:2px;line-height:1.15}
    .badges .b{display:block;text-align:center;padding:3px 2px}
    .b{display:inline-block;padding:1px 8px;border-radius:5px;font-size:13px;color:#111}
    .b.med{background:#f2c27a}.b.high{background:#8c2340;color:#fff}.b.low{background:#a9dcb0}.b.na{background:#3a3f48;color:#9aa1ad}
    .dil{border:1px solid #6b2a3a;background:#2a1820;border-radius:12px;padding:10px 12px;margin-top:6px}
    .dil .row{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
    .dil .ttl{font-weight:700;font-size:13px;letter-spacing:.04em;color:#e8ebf0}
    .dil .lvl{font-weight:700;font-size:17px}
    .dil .bars{display:flex;gap:4px;flex:1;min-width:140px}
    .dil .bars i{flex:1;height:9px;border-radius:5px;background:#3a3f48}
    .dil .sc{font-weight:700;font-size:17px}
    .inst{display:flex;align-items:center;gap:10px;padding:9px 0;border-top:1px solid #2a2e36;font-size:13px}
    .inst .nm{font-weight:700;min-width:84px;font-size:14px}
    .inst .dt{flex:1;color:#c3c8d0;line-height:1.3}
    .inst .st{border:1px solid;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:700}
    .dm{width:9px;height:9px;transform:rotate(45deg);flex:none}
    .lv-low{color:#22e05a}.lv-mod{color:#f2c27a}.lv-high{color:#ff7a59}.lv-ext{color:#ff3b5c}
    .news{margin:6px 0;font-size:14px;line-height:1.3}
    .news a{color:#9cc9f5;text-decoration:none}
    label, .stTextInput label p{color:#9aa1ad !important}
    </style>""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def _fetch(path):
    r = requests.get(BASE + path, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def get(path, tries=5):
    """Fetch a path. If the free plan's rate limit (429) is hit, wait and retry."""
    for attempt in range(tries):
        try:
            return _fetch(path)
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else None
            if code == 429 and attempt < tries - 1:
                time.sleep(15)
                continue
            return None
        except requests.RequestException:
            return None
    return None


def first(data):
    """First item of a response's results list, or an empty dict."""
    results = (data or {}).get("results") or []
    return results[0] if results else {}


def short(n):
    if n is None:
        return "N/A"
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= limit:
            return f"{n / limit:.3g}{suffix}"
    return f"{n:.0f}"


def pct(v):
    return f"{v:.1f}%" if abs(v) >= 10 else f"{v:.2f}%"


def chart_svg(closes):
    w, h, pad = 390, 130, 8
    hi = max(closes) or 1
    n = max(len(closes) - 1, 1)
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


def gap_svg(values, avg):
    w, h, pad = 390, 100, 6
    hi = max(values) or 1
    n = max(len(values) - 1, 1)
    pts = [(i / n * w, h - pad - v / hi * (h - 2 * pad)) for i, v in enumerate(values)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    grid = ""
    for frac in (0, 0.5, 1):
        y = h - pad - frac * (h - 2 * pad)
        grid += f'<line x1="0" x2="{w}" y1="{y:.1f}" y2="{y:.1f}" stroke="#2a2e36" stroke-width="1"/>'
        grid += f'<text x="{w + 6}" y="{y + 4:.1f}" fill="#9aa1ad" font-size="11">{hi * frac:.0f}%</text>'
    ay = h - pad - avg / hi * (h - 2 * pad)
    grid += f'<line x1="0" x2="{w}" y1="{ay:.1f}" y2="{ay:.1f}" stroke="#e0a050" stroke-width="1" stroke-dasharray="4 3"/>'
    return (
        f'<svg viewBox="0 0 {w + 50} {h}" style="width:100%;display:block">{grid}'
        f'<polyline fill="none" stroke="#6db3f2" stroke-width="1.2" points="{line}"/></svg>'
    )


def split_text(s):
    a, b = s.get("split_from"), s.get("split_to")
    if a is None or b is None:
        return None
    if s.get("adjustment_type") == "stock_dividend":
        kind, ratio = "stock dividend", f"{b:g}:{a:g}"
    elif a > b:
        kind, ratio = "reverse split", f"{a:g}:{b:g}"
    else:
        kind, ratio = "split", f"{b:g}:{a:g}"
    return f"{ratio} {kind} on {s.get('execution_date', '')}"


def get_splits(ticker):
    data = get(f"/stocks/v1/splits?ticker={ticker}&limit=10")
    if data is None:  # fall back to the older endpoint
        data = get(f"/v3/reference/splits?ticker={ticker}&order=desc&limit=10")
    return data


def gap_analysis(res, up):
    """For every day: gap = open vs. previous close. Keep days gapping in the chosen direction."""
    stats, series = [], []
    for prev_bar, bar in zip(res, res[1:]):
        p, o, c = prev_bar["c"], bar["o"], bar["c"]
        if not p or not o:
            series.append(0)
            continue
        g = (o - p) / p * 100
        if (g <= 0) if up else (g >= 0):
            series.append(0)
            continue
        edge = bar["h"] if up else bar["l"]
        stats.append((abs(g), (c - o) / o * 100, (edge - o) / o * 100))
        series.append(abs(g))
    return stats, series


def bucket_label(mag):
    for lo, hi in BUCKETS:
        if lo <= mag < hi:
            return f"{lo}%-{hi}%"
    return "outside ranges"


def gap_table(stats, today_mag, up):
    def cc(v):
        return "up" if v > 0 else "down"

    rows = ""
    for lo, hi in BUCKETS:
        items = [s for s in stats if lo <= s[0] < hi]
        hl = ' class="hl"' if lo <= today_mag < hi else ""
        if items:
            n = len(items)
            ga = sum(s[0] for s in items) / n
            oc = sum(s[1] for s in items) / n
            ex = sum(s[2] for s in items) / n
            cells = (
                f"<td>{pct(ga)}</td><td class='{cc(oc)}'>{pct(oc)}</td>"
                f"<td class='{cc(ex)}'>{pct(ex)}</td><td>{n}</td>"
            )
        else:
            cells = "<td>—</td><td>—</td><td>—</td><td>0</td>"
        rows += f"<tr{hl}><td>{lo}%-{hi}%</td>{cells}</tr>"
    extreme = "HoD" if up else "LoD"
    return (
        f'<table class="tbl"><tr><th>Range</th><th>Gap Avg</th><th>O-C Avg</th>'
        f"<th>{extreme}</th><th>Freq</th></tr>{rows}</table>"
    )


@st.cache_data(ttl=86400)
def sec_cik_map():
    r = requests.get("https://www.sec.gov/files/company_tickers.json", headers={"User-Agent": SEC_UA}, timeout=20)
    r.raise_for_status()
    return {v["ticker"].upper(): int(v["cik_str"]) for v in r.json().values()}


@st.cache_data(ttl=3600)
def sec_facts(cik):
    """Download a company's SEC filing data, keeping only the few items we need."""
    r = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json", headers={"User-Agent": SEC_UA}, timeout=30)
    r.raise_for_status()
    all_facts = r.json().get("facts", {})
    keep = {}

    def collect(taxonomy, tags, unit):
        for tag in tags:
            rows = all_facts.get(taxonomy, {}).get(tag, {}).get("units", {}).get(unit, [])
            keep[tag] = [
                {"start": f.get("start"), "end": f["end"], "val": f["val"], "filed": f.get("filed", ""), "form": f.get("form", "")}
                for f in rows
                if str(f.get("form", "")).startswith(("10-K", "10-Q"))
            ]

    collect("us-gaap", CASH_TAGS + INVEST_TAGS + OCF_TAGS, "USD")
    collect("us-gaap", WARRANT_TAGS, "shares")
    collect("us-gaap", EXERCISE_TAGS, "USD/shares")
    collect("dei", SHARE_TAGS, "shares")
    return keep


@st.cache_data(ttl=3600)
def sec_filings(cik):
    """Recent offering-related filings: a list of (form, filing date)."""
    r = requests.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", headers={"User-Agent": SEC_UA}, timeout=30)
    r.raise_for_status()
    recent = r.json().get("filings", {}).get("recent", {})
    cutoff = (date.today() - timedelta(days=400)).isoformat()
    return [
        (f, d) for f, d in zip(recent.get("form", []), recent.get("filingDate", []))
        if d >= cutoff and f.startswith(OFFERING_FORMS)
    ]


US_STATES = set("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR GU VI".split())
# EDGAR uses short codes for non-US places; these are the ones I am confident about
SEC_PLACES = {"K3": "Cayman Islands", "F4": "China", "D9": "Hong Kong", "L3": "Israel", "X0": "United Kingdom",
              "A0": "Canada", "A1": "Canada", "A2": "Canada", "A3": "Canada", "A4": "Canada", "A5": "Canada",
              "A6": "Canada", "A7": "Canada", "A8": "Canada", "A9": "Canada", "B0": "Canada"}


@st.cache_data(ttl=86400)
def sec_country(ticker):
    """Country of the company's business address, from SEC filings. Returns text like 'U.S' or None."""
    if not SEC_UA:
        return None
    try:
        cik = sec_cik_map().get(ticker.upper())
        if not cik:
            return None
        r = requests.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", headers={"User-Agent": SEC_UA}, timeout=30)
        r.raise_for_status()
        biz = (r.json().get("addresses") or {}).get("business") or {}
    except Exception:
        return None
    code = (biz.get("stateOrCountry") or "").strip().upper()
    desc = (biz.get("stateOrCountryDescription") or "").strip()
    if code in US_STATES:
        return "U.S"
    if code in SEC_PLACES:
        return SEC_PLACES[code]
    if desc and desc.upper() != code:
        return desc.title()
    return None


def pdate(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def latest_instant(facts, tags):
    """Most recent balance-sheet value (end date, value) across the given tags."""
    cands = [
        (f["end"], -i, f["filed"], f["val"])
        for i, tag in enumerate(tags)
        for f in facts.get(tag, [])
        if not f.get("start")
    ]
    if not cands:
        return None
    best = max(cands)
    return best[0], best[3]


def instant_on(facts, tags, end):
    for tag in tags:
        rows = [f for f in facts.get(tag, []) if not f.get("start") and f["end"] == end]
        if rows:
            return max(rows, key=lambda f: f["filed"])["val"]
    return None


def quarterly_ocf(facts):
    """Operating cash flow for the latest quarter: (value, period end, basis) or None.
    10-Q and 10-K cash flows are cumulative for the year so far, so we subtract the earlier period."""
    for tag in OCF_TAGS:
        rows = {}
        for f in facts.get(tag, []):
            if not f.get("start"):
                continue
            key = (f["start"], f["end"])
            if key not in rows or f["filed"] > rows[key]["filed"]:
                rows[key] = f
        if not rows:
            continue
        latest_end = max(e for _, e in rows)
        ends = [k for k in rows if k[1] == latest_end]

        def days(k):
            return (pdate(k[1]) - pdate(k[0])).days

        quarter = [k for k in ends if 75 <= days(k) <= 105]
        if quarter:
            return rows[quarter[0]]["val"], latest_end, "reported"
        k = max(ends, key=days)
        prior = [
            kk for kk in rows
            if kk[0] == k[0] and 60 < (pdate(latest_end) - pdate(kk[1])).days < 120
        ]
        if prior:
            pk = max(prior, key=lambda kk: kk[1])
            return rows[k]["val"] - rows[pk]["val"], latest_end, "derived"
        if days(k) > 0:
            return rows[k]["val"] / (days(k) / 91.25), latest_end, "average"
    return None


def cash_metrics(ticker):
    if not SEC_UA:
        return {"error": "no_ua"}
    try:
        cik = sec_cik_map().get(ticker)
        if not cik:
            return {"error": "no_cik"}
        facts = sec_facts(cik)
    except (requests.RequestException, ValueError, KeyError):
        return {"error": "sec_unavailable"}
    cash_row = latest_instant(facts, CASH_TAGS)
    cash = cash_end = None
    if cash_row:
        cash_end, cash = cash_row
        invest = instant_on(facts, INVEST_TAGS, cash_end)
        if invest:
            cash += invest
    ocf = quarterly_ocf(facts)
    burn, basis = (ocf[0], ocf[2]) if ocf else (None, None)
    months = cash / (-burn / 3) if (cash is not None and burn is not None and burn < 0) else None
    return {"cash": cash, "cash_end": cash_end, "burn": burn, "basis": basis, "months": months}


@st.cache_data(ttl=3600)
def nasdaq_file(kind, day):
    """Download one daily Nasdaq Trader list. Returns its text, or None if no file exists for that day.
    Network problems raise an error (so they are not remembered)."""
    r = requests.get(NASDAQ_FILES[kind].format(d=day), headers={"User-Agent": "Mozilla/5.0 (TickerApp)"}, timeout=12)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.text


def latest_file(kind, today):
    """The newest available daily file, looking back up to a week: (date, text) or None."""
    for i in range(8):
        day = today - timedelta(days=i)
        if day.weekday() >= 5:
            continue
        text = nasdaq_file(kind, day.strftime("%Y%m%d"))
        if text:
            return day, text
    return None


def ssr_days(today):
    """Trading days whose circuit-breaker triggers are in effect today (a trigger lasts the rest of that day and the next day)."""
    def prev_weekday(d):
        d -= timedelta(days=1)
        while d.weekday() >= 5:
            d -= timedelta(days=1)
        return d
    if today.weekday() >= 5:
        return [prev_weekday(today + timedelta(days=1))]  # weekend: only Friday's triggers reach Monday
    return [today, prev_weekday(today)]


def reg_flags(ticker, exchange_code, today=None):
    """Reg SHO threshold flag and SSR flag as "Yes" / "No" / None (unknown)."""
    today = today or date.today()
    out = {"reg_sho": None, "ssr": None, "ssr_note": ""}
    # Reg SHO: Nasdaq's list only covers Nasdaq-listed securities
    if exchange_code == "XNAS":
        try:
            found = latest_file("th", today)
        except requests.RequestException:
            found = None
        if found:
            symbols = {line.split("|")[0].strip().upper() for line in found[1].splitlines()[1:] if "|" in line}
            out["reg_sho"] = "Yes" if ticker in symbols else "No"
    # SSR
    try:
        hit, seen = None, 0
        for day in ssr_days(today):
            if day.weekday() >= 5:
                continue
            text = nasdaq_file("sh", day.strftime("%Y%m%d"))
            if text is None:
                continue
            seen += 1
            for row in csv.reader(io.StringIO(text)):
                if len(row) >= 4 and row[0].strip().upper() == ticker:
                    hit = (day, row[3].strip())
        if hit:
            out["ssr"], out["ssr_note"] = "Yes", f"SSR triggered {hit[1]}"
        elif seen:
            out["ssr"] = "No"
    except requests.RequestException:
        pass
    return out


def flags_html(d, extras):
    def cell(label, value, warn=True):
        if value is None:
            return f'{label}: <span class="mute">N/A</span>'
        if not warn:  # ADR is informational, not a warning
            return f'{label}: <span class="mute">{value}</span>'
        return f'{label}: <span class="{"down" if value == "Yes" else "up"}">{value}</span>'

    typ = d.get("type")
    adr = None if not typ else ("Yes" if str(typ).startswith("ADR") else "No")
    if extras is None:
        return f'<div class="flags" style="font-size:inherit;margin:0;text-align:right">{cell("ADR", adr, warn=False)} &nbsp;•&nbsp; Reg SHO: … &nbsp;•&nbsp; SSR: …</div>'
    f = extras.get("flags") or {}
    return (
        f'<div class="flags" style="font-size:inherit;margin:0;text-align:right">{cell("ADR", adr, warn=False)} &nbsp;•&nbsp; {cell("Reg SHO", f.get("reg_sho"))}'
        f' &nbsp;•&nbsp; {cell("SSR", f.get("ssr"))}</div>'
    )


def split_factor(date_str, splits):
    """Multiply a share count reported on date_str to put it on today's (post-split) basis."""
    f = 1.0
    for s in (splits or {}).get("results", []):
        a, b, d = s.get("split_from"), s.get("split_to"), s.get("execution_date")
        if a and b and d and d > date_str:
            f *= b / a
    return f


def share_growth(facts, splits):
    """Change in shares outstanding over about a year, adjusted for splits. None if unknown."""
    by_end = {}
    for tag in SHARE_TAGS:
        for f in facts.get(tag, []):
            if f["end"] not in by_end or f["filed"] > by_end[f["end"]][0]:
                by_end[f["end"]] = (f["filed"], f["val"])
    if len(by_end) < 2:
        return None
    latest = max(by_end)
    target = pdate(latest) - timedelta(days=365)
    old = min((e for e in by_end if e != latest), key=lambda e: abs((pdate(e) - target).days))
    if abs((pdate(old) - target).days) > 75:
        return None
    new_v = by_end[latest][1] * split_factor(latest, splits)
    old_v = by_end[old][1] * split_factor(old, splits)
    return new_v / old_v - 1 if old_v else None


def level(value, high, med):
    """Higher value = higher risk."""
    return "high" if value >= high else ("med" if value >= med else "low")


def risk_metrics(ticker, cash, splits):
    if not SEC_UA:
        return {"error": "no_ua"}
    try:
        cik = sec_cik_map().get(ticker)
        if not cik:
            return {"error": "no_cik"}
        facts = sec_facts(cik)
        filings = sec_filings(cik)
    except (requests.RequestException, ValueError, KeyError):
        return {"error": "sec_unavailable"}

    today = date.today()
    d_recent = (today - timedelta(days=RULES["recent_days"])).isoformat()
    d_year = (today - timedelta(days=365)).isoformat()
    n_pros = len({d for f, d in filings if f.startswith("424B") and d >= d_year})
    offering = "high" if any(d >= d_recent for _, d in filings) else ("med" if any(d >= d_year for _, d in filings) else "low")
    frequency = level(n_pros, RULES["freq_high"], RULES["freq_med"])

    growth = share_growth(facts, splits)
    dilution = level(growth, RULES["dilution_high"], RULES["dilution_med"]) if growth is not None else "na"

    warrants, ratio = "na", None
    w, s = latest_instant(facts, WARRANT_TAGS), latest_instant(facts, SHARE_TAGS)
    if w and s and s[1]:
        ratio = (w[1] * split_factor(w[0], splits)) / (s[1] * split_factor(s[0], splits))
        warrants = level(ratio, RULES["warrants_high"], RULES["warrants_med"])

    months, burn = (cash or {}).get("months"), (cash or {}).get("burn")
    if months is not None:
        cash_need = "high" if months < RULES["cash_months_high"] else ("med" if months < RULES["cash_months_med"] else "low")
    elif burn is not None and burn >= 0:
        cash_need = "low"
    else:
        cash_need = "na"

    points = {"low": 1, "med": 2, "high": 3}
    known = [points[x] for x in (offering, dilution, frequency, cash_need, warrants) if x in points]
    if len(known) < 3:
        overall = "na"
    else:
        avg = sum(known) / len(known)
        overall = "high" if avg >= 2.4 else ("med" if avg >= 1.7 else "low")

    return {
        "overall": overall, "offering": offering, "dilution": dilution, "frequency": frequency,
        "cash_need": cash_need, "warrants": warrants,
        "growth": growth, "n_pros": n_pros, "ratio": ratio,
    }


def risk_html(extras):
    labels = [("Overall Risk", "overall"), ("Offering", "offering"), ("Dilution", "dilution"),
              ("Frequency", "frequency"), ("Cash Need", "cash_need"), ("Warrants", "warrants")]
    names = {"low": "Low", "med": "Medium", "high": "High", "na": "N/A"}

    def badges(get_level, get_text):
        return '<div class="badges">' + "".join(
            f'<div><small>{label}</small><span class="b {get_level(key)}">{get_text(key)}</span></div>'
            for label, key in labels
        ) + "</div>"

    if extras is None:
        return badges(lambda k: "na", lambda k: "…")
    r = extras.get("risk") or {}
    err = r.get("error")
    if err == "no_ua":
        return '<div class="mute">Add SEC_USER_AGENT to the app secrets to show risk ratings.</div>'
    if err == "no_cik":
        return '<div class="mute">No SEC filing data found for this ticker.</div>'
    if err:
        return '<div class="mute">SEC data is unavailable right now.</div>'
    parts = []
    if r.get("growth") is not None:
        parts.append(f"share count {r['growth']:+.0%} over about a year (split-adjusted)")
    parts.append(f"{r.get('n_pros', 0)} prospectus filings in 12 months")
    if r.get("ratio") is not None:
        parts.append(f"warrants about {r['ratio']:.0%} of shares")
    note = "Rule-based estimate from SEC filings: " + " · ".join(parts)
    return badges(lambda k: r.get(k, "na"), lambda k: names.get(r.get(k, "na"), "N/A")) + f'<div class="note">{html.escape(note)}</div>'


def money(n, sign=False):
    prefix = "-$" if n < 0 else ("+$" if sign else "$")
    return prefix + short(abs(n))


def nasdaq_cell(extras):
    """Nasdaq Composite day change, using the ONEQ ETF (tracks the Composite) because index data is not on the free plan."""
    if extras is None:
        return ("Nasdaq Comp", "…", "")
    res = (extras.get("nasdaq") or {}).get("results") or []
    if len(res) < 2 or not res[-2].get("c"):
        return ("Nasdaq Comp", "N/A", "")
    ch = (res[-1]["c"] - res[-2]["c"]) / res[-2]["c"] * 100
    return ("Nasdaq Comp", f"{ch:+.2f}%", "up" if ch >= 0 else "down")


def cash_html(extras):
    def grid(items):
        return '<div class="grid">' + "".join(
            f'<div><small>{k}</small><b class="{c}">{v}</b></div>' for k, v, c in items
        ) + "</div>"

    if extras is None:
        return grid([nasdaq_cell(None), ("Cash Left", "…", ""), ("Burn Rate", "…", ""), ("Est Cash", "…", "")])
    m = extras.get("cash") or {}
    err = m.get("error")
    if err == "no_ua":
        return grid([nasdaq_cell(extras)]) + '<div class="mute">Add SEC_USER_AGENT to the app secrets to show cash data.</div>'
    if err == "no_cik":
        return grid([nasdaq_cell(extras)]) + '<div class="mute">No SEC filing data found for this ticker.</div>'
    if err:
        return grid([nasdaq_cell(extras)]) + '<div class="mute">SEC data is unavailable right now.</div>'
    burn, cash, months = m.get("burn"), m.get("cash"), m.get("months")
    if months is not None:
        left = f"{months:,.1f} months"
    elif burn is not None and burn >= 0:
        left = "Cash flow positive"
    else:
        left = "N/A"
    burn_txt = money(burn, sign=True) if burn is not None else "N/A"
    cash_txt = money(cash) if cash is not None else "N/A"
    basis = {"reported": "as reported", "derived": "derived from year-to-date filings", "average": "estimated from a longer period"}.get(m.get("basis"), "")
    note = f'Cash as of {m.get("cash_end") or "n/a"} · Burn Rate = latest quarter operating cash flow ({basis}) · source: SEC filings · Nasdaq Comp = ONEQ ETF day change'
    return grid([
        nasdaq_cell(extras),
        ("Cash Left", left, ""),
        ("Burn Rate", burn_txt, "" if burn is None else ("down" if burn < 0 else "up")),
        ("Est Cash", cash_txt, "up" if cash else ""),
    ]) + f'<div class="note">{html.escape(note)}</div>'


def news_html(extras):
    if extras is None:
        return '<div class="mute">Loading…</div>'
    items = ((extras.get("news") or {}).get("results") or [])[:3]
    if not items:
        return '<div class="mute">No news available.</div>'
    out = ""
    for n in items:
        title = html.escape((n.get("title") or "")[:110]).replace("$", "&#36;")
        url = n.get("article_url") or ""
        if url.startswith(("http://", "https://")):
            title = f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{title}</a>'
        pub = html.escape((n.get("publisher") or {}).get("name", ""))
        day = html.escape((n.get("published_utc") or "")[:10])
        out += f'<div class="news">{title}<br><span class="mute" style="font-size:12px">{pub} · {day}</span></div>'
    return out


def finviz_own(ticker):
    """Best effort: Inst Own and Insider Own from the Finviz quote page. Returns {} if blocked or changed."""
    try:
        r = requests.get(
            f"https://finviz.com/quote.ashx?t={ticker}",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                     "Accept-Language": "en-US,en;q=0.9"},
            timeout=10,
        )
        if r.status_code != 200:
            return {}
        text = r.text
    except Exception:
        return {}
    import re
    out = {}
    for key, label in (("inst", "Inst Own"), ("insider", "Insider Own")):
        m = re.search(re.escape(label) + r"</a></td>\s*<td[^>]*>(.*?)</td>", text, re.S)
        if not m:
            m = re.search(re.escape(label) + r".{0,200}?<b>(.*?)</b>", text, re.S)
        if m:
            v = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if re.fullmatch(r"-?[\d.,]+%", v):
                out[key] = v
    return out


def et_now(now_utc=None):
    """Current date and time in US Eastern time, as ('OCT 18, 2026', '10:06 AM ET')."""
    now_utc = now_utc or datetime.utcnow()
    try:
        from zoneinfo import ZoneInfo
        from datetime import timezone
        t = now_utc.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/New_York"))
    except Exception:
        # Fallback: US daylight time runs from the 2nd Sunday of March to the 1st Sunday of November (2:00 local)
        y = now_utc.year
        mar1, nov1 = date(y, 3, 1), date(y, 11, 1)
        start = mar1 + timedelta(days=(6 - mar1.weekday()) % 7 + 7)
        end = nov1 + timedelta(days=(6 - nov1.weekday()) % 7)
        dst_start = datetime(start.year, start.month, start.day, 7)  # 2:00 EST = 07:00 UTC
        dst_end = datetime(end.year, end.month, end.day, 6)          # 2:00 EDT = 06:00 UTC
        t = now_utc + timedelta(hours=-4 if dst_start <= now_utc < dst_end else -5)
    hour = t.hour % 12 or 12
    return t.strftime("%b %d, %Y").upper(), f"{hour}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'} ET"


@st.cache_data(ttl=3600)
def sec_submissions(cik):
    """Slim list of recent filings: form, date, accession number, main document, 8-K item codes."""
    r = requests.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", headers={"User-Agent": SEC_UA}, timeout=30)
    r.raise_for_status()
    rec = r.json().get("filings", {}).get("recent", {})
    keys = ("form", "filingDate", "accessionNumber", "primaryDocument", "items")
    cols = [rec.get(k, []) for k in keys]
    return [dict(zip(keys, row)) for row in zip(*cols)]


@st.cache_data(ttl=86400)
def filing_text(cik, accession, doc):
    """First part of a filing's main document as plain text (empty string if it cannot be read)."""
    import re
    try:
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{doc}"
        r = requests.get(url, headers={"User-Agent": SEC_UA}, timeout=20, stream=True)
        r.raise_for_status()
        raw = next(r.iter_content(250000), b"").decode("utf-8", "ignore")
    except Exception:
        return ""
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))


def dollar_amount(text):
    """First 'up to $X' / 'aggregate ... $X' amount in the text, in dollars. None if not found."""
    import re
    m = re.search(r"(?:up to|aggregate offering price of(?: up to)?|aggregate of|aggregate amount of)\s+(?:an aggregate of\s+)?\$\s?([\d,]+(?:\.\d+)?)\s*(million|billion)?", text, re.I)
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    return v * {"million": 1e6, "billion": 1e9}.get((m.group(2) or "").lower(), 1)


def share_amount(text):
    """First share count (5+ digits) that appears in front of the word 'shares'. None if not found."""
    import re
    m = re.search(r"([\d]{1,3}(?:,\d{3}){1,4})\s+(?:additional\s+)?(?:[A-Za-z]+\s+){0,3}(?:shares|ADSs|ADS)", text)
    return float(m.group(1).replace(",", "")) if m else None


def dilution_panel(ticker, cash, risk, splits, today=None):
    """Active / material dilution instruments and a 0-10 dilution score."""
    if not SEC_UA:
        return {"error": "no_ua"}
    try:
        cik = sec_cik_map().get(ticker)
        if not cik:
            return {"error": "no_cik"}
        subs = sec_submissions(cik)
        facts = sec_facts(cik)
    except (requests.RequestException, ValueError, KeyError):
        return {"error": "sec_unavailable"}

    today = today or date.today()
    iso = lambda days: (today - timedelta(days=days)).isoformat()
    items = []

    # Shelf: S-3 / F-3 filed in the last 3 years; effective date from the SEC's EFFECT notice if there is one
    shelves = sorted((f for f in subs if f["form"].startswith(SHELF_FORMS) and f["filingDate"] >= iso(3 * 365)), key=lambda f: f["filingDate"], reverse=True)
    if shelves:
        f = shelves[0]
        eff = next((e["filingDate"] for e in sorted(subs, key=lambda e: e["filingDate"]) if e["form"] == "EFFECT" and e["filingDate"] >= f["filingDate"]), None)
        amt = dollar_amount(filing_text(cik, f["accessionNumber"], f["primaryDocument"])) if f["primaryDocument"] else None
        when = f"{f['form']} effective {eff}" if eff else (f"{f['form']} filed {f['filingDate']}")
        items.append({"kind": "SHELF", "detail": (f"{money(amt)} shelf · " if amt else "Shelf registration · ") + when, "status": "ACTIVE", "sev": "high"})

    # S-8: employee equity plans registered in the last 12 months
    for f in sorted((f for f in subs if f["form"] == "S-8" and f["filingDate"] >= iso(365)), key=lambda f: f["filingDate"], reverse=True)[:2]:
        n = share_amount(filing_text(cik, f["accessionNumber"], f["primaryDocument"])) if f["primaryDocument"] else None
        items.append({"kind": "S-8 PLAN", "detail": (f"{short(n)} shares registered " if n else "Equity plan registered ") + f["filingDate"], "status": "ACTIVE", "sev": "high" if not items or items[-1]["kind"] != "S-8 PLAN" else "mod"})

    # Warrants: latest count in SEC filings
    w = latest_instant(facts, WARRANT_TAGS)
    if w and w[1] > 0:
        ex = latest_instant(facts, EXERCISE_TAGS)
        items.append({"kind": "WARRANT", "detail": f"{short(w[1] * split_factor(w[0], splits))} warrants outstanding as of {w[0]}" + (f" · exercise ${ex[1]:.2f}" if ex else ""), "status": "ACTIVE", "sev": "high" if (risk or {}).get("warrants") == "high" else "mod"})

    # Private sales: 8-K item 3.02 (unregistered sale of equity) in the last 12 months
    for f in sorted((f for f in subs if f["form"].startswith("8-K") and "3.02" in str(f.get("items", "")) and f["filingDate"] >= iso(365)), key=lambda f: f["filingDate"], reverse=True)[:2]:
        items.append({"kind": "PRIVATE SALE", "detail": f"Unregistered equity sale reported {f['filingDate']} (8-K Item 3.02)", "status": "ISSUED", "sev": "mod"})

    # Score out of 10
    r = risk or {}
    pts = {"high": 2, "med": 1}
    score = (3 if shelves else 0) + (1 if any(i["kind"] == "S-8 PLAN" for i in items) else 0)
    score += pts.get(r.get("warrants"), 0) + pts.get(r.get("cash_need"), 0)
    score += 1 if any(i["kind"] == "PRIVATE SALE" for i in items) else 0
    score += 1 if r.get("dilution") == "high" else 0
    score = min(score, 10)
    label = "LOW" if score <= 2 else ("MODERATE" if score <= 4 else ("HIGH" if score <= 6 else "EXTREME"))
    reviewed = max((f["filingDate"] for f in subs), default=None)
    return {"items": items, "score": score, "label": label, "reviewed": reviewed}


def dilution_html(extras):
    head = ""
    if extras is None:
        return head + '<div class="mute">Loading…</div>'
    d = extras.get("dilution") or {}
    err = d.get("error")
    if err == "no_ua":
        return head + '<div class="mute">Add SEC_USER_AGENT to the app secrets to show dilution instruments.</div>'
    if err == "no_cik":
        return head + '<div class="mute">No SEC filing data found for this ticker.</div>'
    if err or not d:
        return head + '<div class="mute">SEC data is unavailable right now.</div>'
    score, label = d["score"], d["label"]
    cls = {"LOW": "lv-low", "MODERATE": "lv-mod", "HIGH": "lv-high", "EXTREME": "lv-ext"}[label]
    col = {"LOW": "#22e05a", "MODERATE": "#f2c27a", "HIGH": "#ff7a59", "EXTREME": "#ff3b5c"}[label]
    bars = "".join(f'<i style="background:{col}"></i>' if i < score else "<i></i>" for i in range(10))
    box = (
        f'<div class="dil"><div class="row"><div><div class="ttl">DILUTION RISK</div><div class="lvl {cls}">{label}</div></div>'
        f'<div class="bars">{bars}</div><div class="sc {cls}">{score} / 10</div></div>'
        f'<div class="mute" style="font-size:12px;margin-top:6px">Score weighs active shelf, equity plans, warrants, cash need, private sales and share growth.</div></div>'
    )
    items = d["items"]
    n = len(items)
    rev = f'Latest filing reviewed: {html.escape(d["reviewed"])}' if d.get("reviewed") else ""
    rows = ""
    for it in items:
        c = "#ff3b5c" if it["sev"] == "high" else "#d8962a"
        rows += (
            f'<div class="inst"><span class="dm" style="background:{c}"></span><span class="nm">{html.escape(it["kind"])}</span>'
            f'<span class="dt">{html.escape(it["detail"])}</span>'
            f'<span class="st" style="color:{c};border-color:{c}">{it["status"]}</span></div>'
        )
    if not rows:
        rows = '<div class="mute" style="padding:8px 0">No active or material instruments found in recent SEC filings.</div>'
    return (
        head + box
        + f'<div class="row" style="display:flex;justify-content:space-between;margin:12px 0 2px;flex-wrap:wrap;gap:4px">'
        f'<div class="ttl" style="font-weight:700;font-size:14px">{n} ACTIVE / MATERIAL INSTRUMENT{"S" if n != 1 else ""}</div>'
        f'<div class="mute" style="font-size:12px">{rev}</div></div>{rows}'
        '<div class="note">Instruments are read from SEC filings by simple rules (shelf = S-3/F-3 filed in the last 3 years, equity plan = S-8 in the last year, '
        'private sale = 8-K Item 3.02 in the last year). Amounts are taken from the filing text when found.</div>'
    )


def parse_ownership_xml(xml_text):
    """Holdings of common-type shares reported in one Form 3/4/5: a list of
    (owner id, security title, 'D' or 'I', nature of ownership, shares owned afterwards), in document order."""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    owner = (root.findtext(".//reportingOwner/reportingOwnerId/rptOwnerCik") or root.findtext(".//reportingOwner/reportingOwnerId/rptOwnerName") or "?").strip()
    out = []
    for node in root.findall(".//nonDerivativeTable/*"):
        title = (node.findtext("securityTitle/value") or "").strip()
        low = title.lower()
        if not any(w in low for w in ("common", "ordinary", "class a", "class b", "shares")) or any(w in low for w in ("warrant", "option", "preferred", "unit", "convertible", "note")):
            continue
        amt = node.findtext("postTransactionAmounts/sharesOwnedFollowingTransaction/value")
        if amt is None:
            continue
        try:
            n = float(amt)
        except ValueError:
            continue
        di = (node.findtext("ownershipNature/directOrIndirectOwnership/value") or "D").strip().upper()[:1]
        nature = (node.findtext("ownershipNature/natureOfOwnership/value") or "").strip().lower()
        out.append((owner, title.lower(), di, nature, n))
    return out


def total_insider_shares(filings):
    """filings: list of (date, accession, holdings) in any order. Latest report per holding wins; shared indirect holdings counted once."""
    latest = {}
    for _, _, holdings in sorted(filings, key=lambda f: (f[0], f[1])):
        for owner, title, di, nature, n in holdings:
            latest[(owner, title, di, nature)] = n
    total, seen = 0.0, set()
    for (owner, title, di, nature), n in latest.items():
        if di == "I":  # the same fund or trust is often reported by several insiders
            key = (title, nature, n)
            if key in seen:
                continue
            seen.add(key)
        total += n
    owners = len({k[0] for k, n in latest.items() if n > 0})
    return total, owners


@st.cache_data(ttl=21600)
def insider_holdings(ticker):
    """Shares held by insiders, from the SEC's Form 3 / 4 / 5 filings of the last 2 years. {} if unavailable."""
    from concurrent.futures import ThreadPoolExecutor
    if not SEC_UA:
        return {}
    try:
        cik = sec_cik_map().get(ticker.upper())
        if not cik:
            return {}
        subs = sec_submissions(cik)
    except Exception:
        return {}
    cutoff = (date.today() - timedelta(days=730)).isoformat()
    picks = sorted(
        (f for f in subs if f["form"] in ("3", "4", "5", "3/A", "4/A", "5/A") and f["filingDate"] >= cutoff and f["primaryDocument"]),
        key=lambda f: f["filingDate"], reverse=True,
    )[:80]
    if not picks:
        return {}

    def one(f):
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{f['accessionNumber'].replace('-', '')}/{f['primaryDocument'].split('/')[-1]}"
        try:
            r = requests.get(url, headers={"User-Agent": SEC_UA}, timeout=20)
            r.raise_for_status()
            return (f["filingDate"], f["accessionNumber"], parse_ownership_xml(r.text))
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = [x for x in pool.map(one, picks) if x]
    if not results:
        return {}
    total, owners = total_insider_shares(results)
    return {"shares": total, "owners": owners, "latest": max(r[0] for r in results), "filings": len(results)}


def build_card(ticker, res, info, splits, extras):
    last, prev = res[-1], res[-2]
    change = (last["c"] - prev["c"]) / prev["c"] * 100
    open_gap = (last["o"] - prev["c"]) / prev["c"] * 100
    up = change >= 0
    cls = "up" if up else "down"
    recent = res[-30:]
    d = (info or {}).get("results", {})
    exch = EXCHANGES.get(d.get("primary_exchange"), d.get("primary_exchange", ""))
    stamp_date, stamp_time = et_now()
    country = (extras or {}).get("country")
    country_txt = f" &nbsp;•&nbsp; {html.escape(country)}" if country else ""
    shares = d.get("share_class_shares_outstanding") or d.get("weighted_shares_outstanding")

    # Float and short interest (loaded in a second step)
    own = (extras or {}).get("own") or {}
    ins = (extras or {}).get("insider") or {}
    insider_note = ""
    if ins.get("shares") is not None and shares:
        insider_txt = f"{min(ins['shares'] / shares * 100, 100):.1f}%"
        insider_note = (f'<div class="note">Insider Own = shares held by {ins["owners"]} insider{"s" if ins["owners"] != 1 else ""} in their latest SEC Form 3/4/5 reports '
                        f'(through {html.escape(ins["latest"])}) ÷ shares outstanding.</div>')
    else:
        insider_txt = None
    if extras is None:
        float_txt = short_txt = "…"
        own = {"inst": "…", "insider": "…"}
    else:
        fl = first(extras.get("float")).get("free_float")
        si = first(extras.get("short")).get("short_interest")
        float_txt = short(fl) if fl else "N/A"
        if si is not None and fl:
            short_txt = f"{si / fl * 100:.1f}%"
        elif si is not None:
            short_txt = f"{short(si)} sh"
        else:
            short_txt = "N/A"

    if insider_txt is None:
        insider_txt = own.get("insider", "N/A")
    stats = [
        ("Prev Close", f"${prev['c']:.2f}"),
        ("Market Cap", short(d.get("market_cap"))),
        ("Float", float_txt),
        ("OS", short(shares)),
        ("Inst. Own", own.get("inst", "N/A")),
        ("Insider Own", insider_txt),
        ("Short Interest", short_txt),
        ("Vol Avg.", short(sum(b["v"] for b in recent) / len(recent))),
    ]
    cells = "".join(f"<div><small>{k}</small><b>{v}</b></div>" for k, v in stats)

    # Gap analysis
    direction = "Gap Up" if up else "Gap Down"
    gstats, gseries = gap_analysis(res, up)
    gap_head = (
        f'<div class="mute" style="font-size:12px">Today {change:+.1f}% ({bucket_label(abs(change))})'
        f" · open {open_gap:+.1f}% · {direction} · {LOOKBACK_DAYS}d lookback</div>"
    )
    if gstats:
        avg = sum(s[0] for s in gstats) / len(gstats)
        gap_html = (
            gap_head
            + gap_table(gstats, abs(change), up)
            + f'<div class="chart"><span>{direction} history (n={len(gstats)})</span>'
            + f'<span class="r">last {pct(gstats[-1][0])} &nbsp; avg {pct(avg)}</span>'
            + gap_svg(gseries, avg)
            + "</div>"
        )
    else:
        gap_html = gap_head + '<div class="mute">No gap history in the lookback period.</div>'

    split_lines = [t for t in (split_text(s) for s in (splits or {}).get("results", [])[:3]) if t]
    split_html = "".join(f"<div>• {html.escape(t)}</div>" for t in split_lines) or '<div class="mute">No recent splits.</div>'

    return (
        f'<div class="card"><div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">'
        f'<h1 style="margin:0;min-width:0">{ticker} - ${last["c"]:.2f} <span class="{cls}">({change:+.2f}%)</span></h1>'
        f'<img src="{LOGO}" alt="Stelyn Holdings" style="height:64px;width:auto;flex:none;margin:0 auto">'
        f'<div class="mute" style="text-align:right;white-space:nowrap;font-size:13px;line-height:1.35;font-weight:700">{stamp_date}<br>{stamp_time}</div></div>'
        f'<div class="mute">{html.escape(d.get("name", ""))}</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:2px 12px">'
        f'<div class="mute">{html.escape(exch)}{country_txt}</div>'
        f'{flags_html(d, extras)}</div>'
        f'<p class="desc">{html.escape(d.get("description", "")[:220])}</p><hr>'
        f'<div class="grid">{cells}</div>{insider_note}<hr>'
        f'<div class="sec">Dilution &amp; Risk Ratings</div>{risk_html(extras)}<hr>'
        f'{dilution_html(extras)}<hr>'
        f'<div class="sec">Gap Analysis · {direction}</div>{gap_html}<hr>'
        f'{cash_html(extras)}<hr>'
        f'<div class="sec">Latest News</div>{news_html(extras)}<hr>'
        f'<div class="sec">Recent Splits</div>{split_html}<hr>'
        f'<div class="chart"><span>Daily 1Y</span>{chart_svg([b["c"] for b in res[-252:]])}</div>'
        f'</div>'
    )


ticker = st.text_input("Ticker", value="AMOD", max_chars=6).strip().upper()

if ticker:
    start = date.today() - timedelta(days=LOOKBACK_DAYS)
    bars = get(f"/v2/aggs/ticker/{ticker}/range/1/day/{start}/{date.today()}?adjusted=true&sort=asc&limit=5000")
    info = get(f"/v3/reference/tickers/{ticker}")
    splits = get_splits(ticker)

    if not bars or not bars.get("results") or len(bars["results"]) < 2:
        st.write(f"No data found for {ticker}, or the free plan's request limit was hit. Wait a minute and try again.")
    else:
        res = bars["results"]
        box = st.empty()
        box.markdown(build_card(ticker, res, info, splits, None), unsafe_allow_html=True)

        with st.spinner("Loading float, short interest, news, cash, risk and short-sale flags (the free plan allows 5 requests a minute, so this can take up to a minute)..."):
            extras = {
                "float": get(f"/stocks/vX/float?ticker={ticker}"),
                "short": get(f"/stocks/v1/short-interest?ticker={ticker}&sort=settlement_date.desc&limit=1"),
                "news": get(f"/v2/reference/news?ticker={ticker}&limit=3&order=desc&sort=published_utc"),
                "nasdaq": get(f"/v2/aggs/ticker/ONEQ/range/1/day/{date.today() - timedelta(days=10)}/{date.today()}?adjusted=true&sort=asc&limit=20"),
                "cash": cash_metrics(ticker),
            }
            extras["risk"] = risk_metrics(ticker, extras["cash"], splits)
            extras["dilution"] = dilution_panel(ticker, extras["cash"], extras["risk"], splits)
            extras["own"] = finviz_own(ticker)
            extras["insider"] = insider_holdings(ticker)
            extras["country"] = sec_country(ticker)
            extras["flags"] = reg_flags(ticker, (info or {}).get("results", {}).get("primary_exchange"))
        box.markdown(build_card(ticker, res, info, splits, extras), unsafe_allow_html=True)
