import csv
import html
import io
import time
from datetime import date, datetime, timedelta

import requests
import streamlit as st

st.set_page_config(page_title="Ticker lookup", layout="centered")

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
    .badges{display:flex;gap:12px;flex-wrap:wrap}
    .badges small{display:block;color:#9aa1ad;font-size:12px;margin-bottom:2px}
    .b{display:inline-block;padding:1px 8px;border-radius:5px;font-size:13px;color:#111}
    .b.med{background:#f2c27a}.b.high{background:#8c2340;color:#fff}.b.low{background:#a9dcb0}.b.na{background:#3a3f48;color:#9aa1ad}
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
        return f'<div class="flags">{cell("ADR", adr, warn=False)} &nbsp;•&nbsp; Reg SHO: … &nbsp;•&nbsp; SSR: …</div>'
    f = extras.get("flags") or {}
    return (
        f'<div class="flags">{cell("ADR", adr, warn=False)} &nbsp;•&nbsp; {cell("Reg SHO", f.get("reg_sho"))}'
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


def build_card(ticker, res, info, splits, extras):
    last, prev = res[-1], res[-2]
    change = (last["c"] - prev["c"]) / prev["c"] * 100
    open_gap = (last["o"] - prev["c"]) / prev["c"] * 100
    up = change >= 0
    cls = "up" if up else "down"
    recent = res[-30:]
    d = (info or {}).get("results", {})
    exch = EXCHANGES.get(d.get("primary_exchange"), d.get("primary_exchange", ""))
    shares = d.get("share_class_shares_outstanding") or d.get("weighted_shares_outstanding")

    # Float and short interest (loaded in a second step)
    own = (extras or {}).get("own") or {}
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

    stats = [
        ("Prev Close", f"${prev['c']:.2f}"),
        ("Market Cap", short(d.get("market_cap"))),
        ("Float", float_txt),
        ("OS", short(shares)),
        ("Inst. Own", own.get("inst", "N/A")),
        ("Insider Own", own.get("insider", "N/A")),
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
        f'<div class="card"><h1>{ticker} - ${last["c"]:.2f} '
        f'<span class="{cls}">({change:+.2f}%)</span></h1>'
        f'<div class="mute">{html.escape(d.get("name", ""))}</div>'
        f'<div class="mute">{html.escape(exch)}</div>'
        f'{flags_html(d, extras)}'
        f'<p class="desc">{html.escape(d.get("description", "")[:220])}</p><hr>'
        f'<div class="grid">{cells}</div><hr>'
        f'<div class="sec">Dilution &amp; Risk Ratings</div>{risk_html(extras)}<hr>'
        f'<div class="sec">Gap Analysis · {direction}</div>{gap_html}<hr>'
        f'{cash_html(extras)}<hr>'
        f'<div class="sec">Latest News</div>{news_html(extras)}<hr>'
        f'<div class="sec">Recent Splits</div>{split_html}<hr>'
        f'<div class="chart"><span>Daily 1Y</span>{chart_svg([b["c"] for b in res[-252:]])}</div></div>'
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
            extras["own"] = finviz_own(ticker)
            extras["flags"] = reg_flags(ticker, (info or {}).get("results", {}).get("primary_exchange"))
        box.markdown(build_card(ticker, res, info, splits, extras), unsafe_allow_html=True)
