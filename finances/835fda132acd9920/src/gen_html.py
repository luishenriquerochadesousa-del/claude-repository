"""Generate the embeddable balance-evolution page from balances.json."""

import json

d = json.load(open("balances.json"))
accounts = d["accounts"]
by_name = {a["name"]: a for a in accounts}

# Main chart: the seven accounts that carry real weight, in fixed palette-slot order,
# plus everything else folded into "Other" (the 8-slot cap; each of those eight is
# still shown individually in the small multiples below).
FEATURED = [
    "Trade Republic Inv. - Brokerage",
    "Conta Corrente",
    "Certificados de Aforro CTT - Série F",
    "Conta Poupança",
    "Trade Republic Account",
    "Revolut",
    "Trade Republic Inv. - Crypto",
]
others = [a["name"] for a in accounts if a["name"] not in FEATURED]

series = []
for name in FEATURED:
    a = by_name[name]
    series.append({"name": name, "points": [a["start"]] + a["balances"]})
other_pts = [round(sum(by_name[n]["start"] for n in others), 2)]
for i in range(len(d["months"])):
    other_pts.append(round(sum(by_name[n]["balances"][i] for n in others), 2))
series.append({"name": f"Other ({len(others)} accounts)", "points": other_pts,
               "members": sorted(others)})

panels = [{"name": a["name"], "type": a["type"], "bank": a["bank"],
           "points": [a["start"]] + a["balances"]}
          for a in sorted(accounts, key=lambda a: -max(abs(v) for v in [a["start"]] + a["balances"]))]

inv = json.load(open("investments.json"))
payload = {
    "inv": {
        "capital": [inv["start_capital"]] + inv["capital"],
        "value": [inv["start_capital"]] + inv["value"],
        "returns": [0.0] + inv["returns"],
        "start_capital": inv["start_capital"],
        "income_to_cash_total": inv["income_to_cash_total"],
        "irr_annual": inv["irr_annual"],
        "irr_monthly": inv["irr_monthly"],
        "accounts": sorted(
            [{"name": a["name"], "bank": a["bank"],
              "capital": a["capital"][-1], "returns": a["returns"][-1],
              "value": a["value"][-1]} for a in inv["accounts"]],
            key=lambda a: -a["value"]),
    },
    "labels": ["Start", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
    "full": ["1 January 2026", "end of January 2026", "end of February 2026",
             "end of March 2026", "end of April 2026", "end of May 2026",
             "end of June 2026", "end of July 2026", "5 August 2026"],
    "series": series,
    "panels": panels,
    "totals": [d["start_total"]] + d["totals"],
    "table": [{"name": a["name"], "type": a["type"], "bank": a["bank"],
               "points": [a["start"]] + a["balances"]}
              for a in sorted(accounts, key=lambda a: -a["balances"][-1])],
}

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
           "#e87ba4", "#008300", "#4a3aa7", "#e34948"]

HTML = """<title>Account balances — Personal Finance Tracker 2026</title>
<style>
  :root {
    color-scheme: light;
    --plane:      #f9f9f7;
    --surface:    #fcfcfb;
    --ink:        #0b0b0b;
    --ink-2:      #52514e;
    --muted:      #898781;
    --grid:       #e1e0d9;
    --axis:       #c3c2b7;
    --border:     rgba(11,11,11,0.10);
    --hover:      rgba(11,11,11,0.045);
    --pos:        #006300;
    --neg:        #d03b3b;
    --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --s4: #eda100;
    --s5: #e87ba4; --s6: #008300; --s7: #4a3aa7; --s8: #e34948;

    --sans: system-ui, -apple-system, "Segoe UI", sans-serif;
    --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      color-scheme: dark;
      --plane:   #0d0d0d;
      --surface: #1a1a19;
      --ink:     #ffffff;
      --ink-2:   #c3c2b7;
      --muted:   #898781;
      --grid:    #2c2c2a;
      --axis:    #383835;
      --border:  rgba(255,255,255,0.10);
      --hover:   rgba(255,255,255,0.06);
      --pos:     #0ca30c;
      --neg:     #e06060;
      --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500;
      --s5: #d55181; --s6: #008300; --s7: #9085e9; --s8: #e66767;
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --plane:   #0d0d0d;
    --surface: #1a1a19;
    --ink:     #ffffff;
    --ink-2:   #c3c2b7;
    --muted:   #898781;
    --grid:    #2c2c2a;
    --axis:    #383835;
    --border:  rgba(255,255,255,0.10);
    --hover:   rgba(255,255,255,0.06);
    --pos:     #0ca30c;
    --neg:     #e06060;
    --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500;
    --s5: #d55181; --s6: #008300; --s7: #9085e9; --s8: #e66767;
  }

  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--plane);
    color: var(--ink);
    font-family: var(--sans);
    font-size: 15px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }
  .wrap {
    max-width: 1120px;
    margin: 0 auto;
    padding: 40px 24px 72px;
    display: flex;
    flex-direction: column;
    gap: 34px;
  }
  .eyebrow {
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
  }
  h1 {
    margin: 6px 0 0;
    font-size: 30px;
    font-weight: 640;
    letter-spacing: -0.018em;
    text-wrap: balance;
  }
  .lede { margin: 8px 0 0; max-width: 62ch; color: var(--ink-2); }
  h2 {
    margin: 0;
    font-size: 17px;
    font-weight: 620;
    letter-spacing: -0.008em;
  }
  .sub { margin: 4px 0 0; font-size: 13px; color: var(--muted); max-width: 78ch; }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 22px 18px;
  }
  section { display: flex; flex-direction: column; gap: 14px; }

  /* ---- hero + stat tiles ---- */
  .hero { display: grid; grid-template-columns: minmax(240px, 1.05fr) 2fr; gap: 18px; }
  @media (max-width: 720px) { .hero { grid-template-columns: 1fr; } }
  .hero-fig { display: flex; flex-direction: column; justify-content: center; gap: 2px; }
  .hero-num {
    font-size: 50px;
    font-weight: 650;
    letter-spacing: -0.03em;
    line-height: 1.02;
  }
  .tiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
  .tiles-4 { grid-template-columns: repeat(4, 1fr); }
  @media (max-width: 900px) { .tiles-4 { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 720px) { .tiles { grid-template-columns: 1fr; gap: 14px; }
    .tiles-4 { grid-template-columns: repeat(2, 1fr); } }
  .tile-label {
    font-family: var(--mono);
    font-size: 10.5px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .tile-val {
    font-size: 24px;
    font-weight: 620;
    letter-spacing: -0.02em;
    margin-top: 3px;
  }
  .tile-note { font-size: 12.5px; color: var(--ink-2); margin-top: 2px; }
  .delta { display: inline-flex; align-items: baseline; gap: 6px; font-size: 13.5px; font-weight: 560; }
  .delta.up { color: var(--pos); }
  .delta.down { color: var(--neg); }
  .delta .since { color: var(--muted); font-weight: 400; }
  .recon {
    font-size: 12.5px;
    color: var(--ink-2);
    font-variant-numeric: tabular-nums;
  }

  /* ---- charts ---- */
  .scroller { overflow-x: auto; }
  .chart-host { position: relative; }
  svg { display: block; }
  .legend { display: flex; flex-wrap: wrap; gap: 6px 8px; margin-top: 14px; }
  .lg {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 4px 9px 4px 7px;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: none;
    color: var(--ink-2);
    font-family: var(--sans);
    font-size: 12.5px;
    cursor: pointer;
  }
  .lg:hover { background: var(--hover); }
  .lg:focus-visible { outline: 2px solid var(--s1); outline-offset: 2px; }
  .lg .key { width: 13px; height: 3px; border-radius: 2px; flex: none; }
  /* Wash swatch for the band between the two lines, matching its 10% fill. */
  .lg .key.band { height: 11px; border-radius: 3px; background: var(--s1); opacity: 0.28; }
  .lg[aria-pressed="false"] { opacity: 0.45; }
  .lg[aria-pressed="false"] .key { background: var(--axis) !important; }

  .tip {
    position: absolute;
    pointer-events: none;
    opacity: 0;
    transition: opacity .1s;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.13);
    padding: 9px 11px;
    font-size: 12.5px;
    min-width: 176px;
    z-index: 5;
  }
  .tip.on { opacity: 1; }
  .tip h4 {
    margin: 0 0 6px;
    font-family: var(--mono);
    font-size: 10.5px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    font-weight: 500;
  }
  .tip-row { display: flex; align-items: center; gap: 7px; white-space: nowrap; }
  .tip-row .key { width: 11px; height: 3px; border-radius: 2px; flex: none; }
  .tip-row .nm { color: var(--ink-2); white-space: nowrap; }
  .tip-row .vv {
    margin-left: auto;
    font-variant-numeric: tabular-nums;
    font-weight: 560;
    color: var(--ink);
  }

  /* ---- small multiples ---- */
  .grid-sm {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(228px, 1fr));
    gap: 2px;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }
  .pan { background: var(--surface); padding: 14px 15px 10px; display: flex; flex-direction: column; gap: 2px; }
  /* Two lines' worth so every panel in a row lines its chart up with its neighbours. */
  .pan-nm { font-size: 13px; font-weight: 580; letter-spacing: -0.005em; line-height: 1.3; min-height: 2.6em; }
  .pan-meta { font-family: var(--mono); font-size: 10px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); }
  .pan-row { display: flex; align-items: baseline; gap: 8px; margin-top: 4px; }
  .pan-val { font-size: 18px; font-weight: 620; letter-spacing: -0.018em; }
  .pan-d { font-size: 11.5px; font-weight: 560; }
  .pan-d.up { color: var(--pos); }
  .pan-d.down { color: var(--neg); }
  .pan-d.flat { color: var(--muted); }
  .pan-host { position: relative; margin-top: 6px; }

  /* ---- table ---- */
  table { border-collapse: collapse; font-size: 13px; width: 100%; }
  caption { caption-side: top; text-align: left; padding-bottom: 10px; font-size: 13px; color: var(--muted); }
  th, td { padding: 7px 10px; text-align: right; white-space: nowrap; }
  th:first-child, td:first-child { text-align: left; }
  thead th {
    position: sticky;
    top: 0;
    background: var(--surface);
    border-bottom: 1px solid var(--axis);
    font-family: var(--mono);
    font-size: 10.5px;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    font-weight: 500;
    color: var(--muted);
  }
  tbody td { border-bottom: 1px solid var(--grid); font-variant-numeric: tabular-nums; }
  tbody tr:hover td { background: var(--hover); }
  tbody td.nm { display: flex; align-items: center; gap: 8px; }
  tbody td .key { width: 11px; height: 3px; border-radius: 2px; flex: none; }
  tbody td .key.none { background: var(--axis); }
  tfoot td {
    border-top: 2px solid var(--axis);
    font-weight: 640;
    font-variant-numeric: tabular-nums;
    padding-top: 9px;
  }

  /* ---- notes ---- */
  .notes { display: flex; flex-direction: column; gap: 9px; font-size: 13.5px; color: var(--ink-2); }
  .notes li { margin-bottom: 7px; }
  .notes ol { margin: 0; padding-left: 20px; }
  .notes b { color: var(--ink); font-weight: 600; }
  footer { font-size: 12.5px; color: var(--muted); border-top: 1px solid var(--border); padding-top: 16px; }
  @media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">Personal Finance Tracker &middot; rebuilt from Notion, 9 Aug 2026</div>
    <h1>Where the money sits, month by month</h1>
    <p class="lede">End-of-month balance for all 15 accounts since the tracker started on
      1 January 2026, reconstructed from every income, expense and transfer row in Notion.</p>
  </header>

  <section>
    <div class="hero">
      <div class="card hero-fig">
        <div class="tile-label">Net worth &middot; 5 Aug 2026</div>
        <div class="hero-num" id="hero"></div>
        <div id="heroDelta"></div>
      </div>
      <div class="card">
        <div class="tiles">
          <div>
            <div class="tile-label">Money earned</div>
            <div class="tile-val">&euro;25,119</div>
            <div class="tile-note">7 salary &amp; freelance entries</div>
          </div>
          <div>
            <div class="tile-label">Money spent</div>
            <div class="tile-val">&euro;19,238</div>
            <div class="tile-note">423 expenses</div>
          </div>
          <div>
            <div class="tile-label">Net from outside</div>
            <div class="tile-val">+&euro;4,782</div>
            <div class="tile-note">family transfers, refunds</div>
          </div>
        </div>
        <p class="recon" style="margin:16px 0 0">
          25,118.75 &minus; 19,237.62 + 4,782.02 = <b>+10,663.15</b> &mdash; which is exactly the
          change in net worth, so nothing is unaccounted for.
        </p>
      </div>
    </div>
  </section>

  <section>
    <div>
      <h2>Balance evolution</h2>
      <p class="sub">The seven accounts that carry real weight, plus the remaining eight combined.
        Hover for a month; click a name to hide or show it &mdash; the scale follows what is on screen.</p>
    </div>
    <div class="card">
      <div class="scroller">
        <div class="chart-host" id="mainHost">
          <svg id="main" role="img" aria-label="Line chart of account balances from January to August 2026"></svg>
          <div class="tip" id="mainTip"></div>
        </div>
      </div>
      <div class="legend" id="legend"></div>
    </div>
  </section>

  <section>
    <div>
      <h2>Invested capital vs. returns</h2>
      <p class="sub">The eight investment accounts only. The gap between the two lines is what the
        market gave you rather than what you paid in &mdash; your tracker records it as monthly
        portfolio-delta rows, so it is real recorded data, not an estimate.</p>
    </div>
    <div class="card">
      <div class="tiles tiles-4" style="margin-bottom:18px">
        <div>
          <div class="tile-label">Capital invested</div>
          <div class="tile-val" id="ivCap"></div>
          <div class="tile-note" id="ivCapNote"></div>
        </div>
        <div>
          <div class="tile-label">Portfolio value</div>
          <div class="tile-val" id="ivVal"></div>
          <div class="tile-note">across 8 accounts, 5 Aug</div>
        </div>
        <div>
          <div class="tile-label">Return earned</div>
          <div class="tile-val" id="ivRet"></div>
          <div class="tile-note" id="ivRetNote"></div>
        </div>
        <div>
          <div class="tile-label">Annualised rate</div>
          <div class="tile-val" id="ivIrr"></div>
          <div class="tile-note">money-weighted, through 31 Jul</div>
        </div>
      </div>
      <div class="scroller">
        <div class="chart-host" id="invHost">
          <svg id="inv" role="img" aria-label="Portfolio value against capital invested, January to August 2026"></svg>
          <div class="tip" id="invTip"></div>
        </div>
      </div>
      <div class="legend" id="invLegend">
        <span class="lg" style="cursor:default"><span class="key" style="background:var(--s1)"></span>Portfolio value</span>
        <span class="lg" style="cursor:default"><span class="key" style="background:var(--s2)"></span>Capital invested</span>
        <span class="lg" style="cursor:default"><span class="key band"></span>Cumulative return</span>
      </div>
      <div class="scroller" style="margin-top:18px"><table id="ivTbl"></table></div>
    </div>
  </section>

  <section>
    <div>
      <h2>Every account on its own scale</h2>
      <p class="sub">One panel per account, each scaled to its own range so small accounts are readable
        next to a &euro;21k brokerage. Grey band marks zero where an account crosses it.</p>
    </div>
    <div class="grid-sm" id="panels"></div>
  </section>

  <section>
    <div>
      <h2>The numbers</h2>
      <p class="sub">End-of-month balance in euro. Ordered by current balance.</p>
    </div>
    <div class="card"><div class="scroller"><table id="tbl"></table></div></div>
  </section>

  <section>
    <div><h2>How this was built, and what to watch</h2></div>
    <div class="card notes">
      <p style="margin:0">Each balance is
        <b>previous month + income &minus; expenses + transfers in &minus; transfers out</b>,
        starting from the <i>Starting Balance (as of January 1st 2026)</i> field on each account.
        Every expense in Notion is marked Paid and every transfer Executed, so nothing was filtered out.</p>
      <p style="margin:0">The <b>capital / return split</b> comes from how you already log things:
        a transfer between two of your own accounts is capital moving, while a one-sided transfer
        &mdash; no From or no To account &mdash; is money appearing or vanishing, which for an
        investment account can only be a gain or a loss. Every such row on your eight investment
        accounts is a <i>Portfolio Delta</i>, a <i>CTT Aforro Delta</i>, or a fund delta, so the
        classification needs no guesswork. The split reproduces all eight account balances exactly.</p>
      <ol>
        <li><b>August is partial.</b> The last transaction on record is 5 August 2026.</li>
        <li><b>Returns are measured from 1 January 2026, not from when you bought.</b> The
          &euro;13,735 already invested on 1 Jan enters as opening capital at its then value, so the
          +5.70% is this year's return, not lifetime performance on those holdings.</li>
        <li><b>The rate is money-weighted and annualised from seven months.</b> It answers "what
          rate would turn my actual contributions into today's value", computed through 31 July so
          the five-day August stub doesn't distort it. Annualising a partial year assumes the rest
          of it behaves the same, which it won't &mdash; read it as a pace, not a forecast.</li>
        <li><b>Dividends and cash interest leave the portfolio.</b> &euro;24.40 of dividends and 2%
          interest was paid into Trade Republic <i>Account</i> rather than reinvested, so it sits
          outside the portfolio return and is counted separately.</li>
        <li><b>Portfolio deltas are your own monthly marks.</b> Value moves only when you record a
          delta row, so the value line steps at month ends rather than moving daily &mdash; and any
          month you skip shows as flat rather than unknown. Crypto has deltas through July but the
          brokerage's June delta was entered on 31 July, which is why June looks quiet.</li>
        <li><b>One delta row is mislabelled.</b> The 30 June brokerage row reads
          <i>Portfolio Delta - June 2026 <b>(+)</b></i> but was entered as &euro;40.68 leaving the
          account, i.e. a loss. It is counted by its direction, not its label.</li>
        <li><b>Revolut goes slightly negative</b> in January (&minus;&euro;19.36) and May
          (&minus;&euro;15.48). That almost certainly means a top-up is missing or mis-dated in
          Notion rather than a real overdraft &mdash; worth a look.</li>
        <li><b>Two transfers are double-tagged.</b> <i>Investimentos - Trading 212</i> (29 Jun,
          &euro;100 in) and <i>Reembolso - Trading 212</i> (6 Jul, &euro;100 out) each name both
          Trading 212 and Robinhood as the account. Both are counted here against Trading 212, which
          the descriptions name. They cancel out, so no end balance changes &mdash; only the Jun/Jul
          split for those two accounts.</li>
        <li><b>Transfers with a blank From or To account</b> are money entering or leaving the
          tracker from outside it, and are counted one-sided.</li>
      </ol>
    </div>
  </section>

  <footer>
    Source: Notion &mdash; Accounts, Income, Expenses and Transfer databases, read 9 August 2026.
    All figures in euro.
    <br>Unlisted page: it is excluded from search engines, but anyone holding this URL can read it.
  </footer>
</div>

<script>
const DATA = __DATA__;
const SLOTS = ["--s1","--s2","--s3","--s4","--s5","--s6","--s7","--s8"];
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const SVGNS = "http://www.w3.org/2000/svg";

const eur = n => (n < 0 ? "\\u2212" : "") + "\\u20ac" + Math.abs(n).toLocaleString("en-GB",
  { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const eur0 = n => (n < 0 ? "\\u2212" : "") + "\\u20ac" + Math.round(Math.abs(n)).toLocaleString("en-GB");
const tick = n => (n < 0 ? "\\u2212" : "") + Math.abs(n).toLocaleString("en-GB");

function el(tag, attrs, parent) {
  const n = document.createElementNS(SVGNS, tag);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(n);
  return n;
}

/* Nice round bounds and gridline values. Zero is always a gridline; a small dip
   below it gets a fine sub-step rather than a whole wasted band. */
function scale(min, max, target) {
  const top = Math.max(max, 1);
  const raw = top / target;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw) || 10 * mag;
  const hi = Math.ceil(top / step) * step;
  let lo = 0;
  const ticks = [];
  for (let v = 0; v <= hi + 1e-6; v += step) ticks.push(v);
  if (min < -1e-6) {
    const sub = step / 5;
    lo = -Math.ceil(-min / sub) * sub;
    ticks.unshift(lo);
  }
  return { lo, hi, ticks };
}

/* ---------------------------------------------------------------- hero ---- */
const totals = DATA.totals;
document.getElementById("hero").textContent = eur(totals[totals.length - 1]);
const chg = totals[totals.length - 1] - totals[0];
const pct = (chg / totals[0]) * 100;
document.getElementById("heroDelta").innerHTML =
  '<span class="delta ' + (chg >= 0 ? "up" : "down") + '">' +
  (chg >= 0 ? "\\u2191" : "\\u2193") + " " + eur(Math.abs(chg)) +
  " (" + (chg >= 0 ? "+" : "\\u2212") + Math.abs(pct).toFixed(1) + "%)" +
  '<span class="since">since 1 Jan</span></span>';

/* ---------------------------------------------------- main line chart ---- */
const hidden = new Set();
const host = document.getElementById("mainHost");
const svg = document.getElementById("main");
const tip = document.getElementById("mainTip");
let geom = null;

function drawMain() {
  const w = Math.max(700, host.clientWidth || 700);
  const h = Math.max(330, Math.min(460, Math.round(w * 0.42)));
  const pad = { t: 16, r: 74, b: 34, l: 62 };
  svg.setAttribute("width", w);
  svg.setAttribute("height", h);
  svg.setAttribute("viewBox", "0 0 " + w + " " + h);
  while (svg.firstChild) svg.removeChild(svg.firstChild);

  const vis = DATA.series.map((s, i) => ({ s, i })).filter(o => !hidden.has(o.i));
  const flat = vis.flatMap(o => o.s.points);
  const sc = scale(Math.min(0, ...flat), Math.max(0, ...flat), 5);
  const N = DATA.labels.length;
  const X = i => pad.l + (i * (w - pad.l - pad.r)) / (N - 1);
  const Y = v => pad.t + (1 - (v - sc.lo) / (sc.hi - sc.lo)) * (h - pad.t - pad.b);

  sc.ticks.forEach(v => {
    const y = Y(v);
    el("line", { x1: pad.l, x2: w - pad.r, y1: y, y2: y,
      stroke: Math.abs(v) < 1e-6 ? css("--axis") : css("--grid"), "stroke-width": 1 }, svg);
    const t = el("text", { x: pad.l - 10, y: y + 4, "text-anchor": "end",
      fill: css("--muted"), "font-size": 11, "font-family": "var(--mono)" }, svg);
    t.textContent = tick(v);
  });
  DATA.labels.forEach((lb, i) => {
    const t = el("text", { x: X(i), y: h - pad.b + 20, "text-anchor": "middle",
      fill: css("--muted"), "font-size": 11.5, "font-family": "var(--mono)" }, svg);
    t.textContent = lb;
  });

  const crosshair = el("line", { y1: pad.t, y2: h - pad.b, stroke: css("--axis"),
    "stroke-width": 1, opacity: 0 }, svg);
  const dots = [];

  vis.forEach(o => {
    const col = css(SLOTS[o.i]);
    const dpath = o.s.points.map((v, i) => (i ? "L" : "M") + X(i) + " " + Y(v)).join(" ");
    el("path", { d: dpath, fill: "none", stroke: col, "stroke-width": 2,
      "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
    const last = o.s.points[o.s.points.length - 1];
    el("circle", { cx: X(N - 1), cy: Y(last), r: 4.5, fill: col,
      stroke: css("--surface"), "stroke-width": 2 }, svg);
    dots.push({ i: o.i, col, cy: v => Y(v) });
  });

  /* Direct end-labels only where lines clearly separate; the rest rely on
     the legend and tooltip rather than a stack of nudged labels. */
  vis.filter(o => o.i === 0 || o.i === 2).forEach(o => {
    const last = o.s.points[o.s.points.length - 1];
    const t = el("text", { x: X(N - 1) + 10, y: Y(last) + 4, fill: css("--ink-2"),
      "font-size": 11.5, "font-weight": 600 }, svg);
    t.textContent = eur0(last);
  });

  const hoverDots = vis.map(o => el("circle", { r: 5, fill: css(SLOTS[o.i]),
    stroke: css("--surface"), "stroke-width": 2, opacity: 0 }, svg));

  geom = { w, h, pad, X, Y, vis, N, crosshair, hoverDots };
}

function moveTip(ev) {
  if (!geom) return;
  const r = svg.getBoundingClientRect();
  const x = ev.clientX - r.left;
  const { pad, X, Y, vis, N, w, h } = geom;
  let idx = 0, best = Infinity;
  for (let i = 0; i < N; i++) { const dd = Math.abs(X(i) - x); if (dd < best) { best = dd; idx = i; } }

  geom.crosshair.setAttribute("x1", X(idx));
  geom.crosshair.setAttribute("x2", X(idx));
  geom.crosshair.setAttribute("opacity", 1);

  const rows = vis.map((o, k) => {
    const v = o.s.points[idx];
    geom.hoverDots[k].setAttribute("cx", X(idx));
    geom.hoverDots[k].setAttribute("cy", Y(v));
    geom.hoverDots[k].setAttribute("opacity", 1);
    return { name: o.s.name, v, col: css(SLOTS[o.i]) };
  }).sort((a, b) => b.v - a.v);

  tip.innerHTML = "<h4>" + DATA.full[idx] + "</h4>" + rows.map(r2 =>
    '<div class="tip-row"><span class="key" style="background:' + r2.col + '"></span>' +
    '<span class="nm">' + r2.name + '</span><span class="vv">' + eur(r2.v) + "</span></div>").join("");
  tip.classList.add("on");
  /* Flip before the tooltip reaches the end-label gutter, so it never sits on top
     of the labels it duplicates. */
  const tw = tip.offsetWidth;
  let left = X(idx) + 16;
  if (left + tw > w - pad.r) left = X(idx) - tw - 16;
  tip.style.left = Math.max(4, left) + "px";
  tip.style.top = Math.max(4, Math.min(h - tip.offsetHeight - 4, pad.t + 4)) + "px";
}

function hideTip() {
  tip.classList.remove("on");
  if (geom) { geom.crosshair.setAttribute("opacity", 0);
    geom.hoverDots.forEach(d2 => d2.setAttribute("opacity", 0)); }
}
svg.addEventListener("pointermove", moveTip);
svg.addEventListener("pointerleave", hideTip);

/* ------------------------------------------------------------- legend ---- */
const legend = document.getElementById("legend");
DATA.series.forEach((s, i) => {
  const b = document.createElement("button");
  b.className = "lg";
  b.type = "button";
  b.setAttribute("aria-pressed", "true");
  b.title = s.members ? "Combined: " + s.members.join(", ") : s.name;
  b.innerHTML = '<span class="key" style="background:var(' + SLOTS[i] + ')"></span>' + s.name;
  b.addEventListener("click", () => {
    if (hidden.has(i)) hidden.delete(i);
    else if (hidden.size < DATA.series.length - 1) hidden.add(i);
    b.setAttribute("aria-pressed", hidden.has(i) ? "false" : "true");
    hideTip();
    drawMain();
  });
  legend.appendChild(b);
});

/* ------------------------------------ investments: capital vs value ---- */
const IV = DATA.inv;
const ivContrib = IV.capital[IV.capital.length - 1] - IV.start_capital;
const ivRet = IV.returns[IV.returns.length - 1];
const ivCapEnd = IV.capital[IV.capital.length - 1];
document.getElementById("ivCap").textContent = eur0(ivCapEnd);
document.getElementById("ivCapNote").textContent =
  eur0(IV.start_capital) + " at 1 Jan, " + eur0(ivContrib) + " added since";
document.getElementById("ivVal").textContent = eur0(IV.value[IV.value.length - 1]);
document.getElementById("ivRet").innerHTML =
  '<span class="' + (ivRet >= 0 ? "up" : "down") + '" style="color:var(' +
  (ivRet >= 0 ? "--pos" : "--neg") + ')">' + (ivRet >= 0 ? "+" : "\\u2212") +
  eur0(Math.abs(ivRet)) + "</span>";
document.getElementById("ivRetNote").textContent =
  (ivRet / ivCapEnd * 100).toFixed(2) + "% on capital, plus " +
  eur(IV.income_to_cash_total) + " paid out as cash";
document.getElementById("ivIrr").textContent =
  IV.irr_annual == null ? "\\u2014" : (IV.irr_annual * 100).toFixed(1) + "%";

const ivHost = document.getElementById("invHost");
const ivSvg = document.getElementById("inv");
const ivTip = document.getElementById("invTip");
let ivGeom = null;

function drawInv() {
  const w = Math.max(700, ivHost.clientWidth || 700);
  const h = Math.max(300, Math.min(400, Math.round(w * 0.36)));
  const pad = { t: 16, r: 74, b: 34, l: 62 };
  ivSvg.setAttribute("width", w);
  ivSvg.setAttribute("height", h);
  ivSvg.setAttribute("viewBox", "0 0 " + w + " " + h);
  while (ivSvg.firstChild) ivSvg.removeChild(ivSvg.firstChild);

  const all = IV.capital.concat(IV.value);
  const sc = scale(Math.min(0, ...all), Math.max(...all), 5);
  const N = IV.capital.length;
  const X = i => pad.l + (i * (w - pad.l - pad.r)) / (N - 1);
  const Y = v => pad.t + (1 - (v - sc.lo) / (sc.hi - sc.lo)) * (h - pad.t - pad.b);

  sc.ticks.forEach(v => {
    const y = Y(v);
    el("line", { x1: pad.l, x2: w - pad.r, y1: y, y2: y,
      stroke: Math.abs(v) < 1e-6 ? css("--axis") : css("--grid"), "stroke-width": 1 }, ivSvg);
    const t = el("text", { x: pad.l - 10, y: y + 4, "text-anchor": "end", fill: css("--muted"),
      "font-size": 11, "font-family": "var(--mono)" }, ivSvg);
    t.textContent = tick(v);
  });
  DATA.labels.forEach((lb, i) => {
    const t = el("text", { x: X(i), y: h - pad.b + 20, "text-anchor": "middle",
      fill: css("--muted"), "font-size": 11.5, "font-family": "var(--mono)" }, ivSvg);
    t.textContent = lb;
  });

  /* The band between capital and value IS the cumulative return, so it is split
     at every zero crossing and coloured by sign — a gain band and a loss band
     never share a colour. */
  let seg = [];
  const flush = () => {
    if (seg.length < 2) { seg = []; return; }
    const sign = seg.reduce((a, i) => a + (IV.value[i] - IV.capital[i]), 0) >= 0;
    const top = seg.map(i => X(i) + " " + Y(IV.value[i]));
    const bot = seg.slice().reverse().map(i => X(i) + " " + Y(IV.capital[i]));
    el("path", { d: "M" + top.join(" L") + " L" + bot.join(" L") + " Z",
      fill: css(sign ? "--s1" : "--neg"), opacity: 0.1, stroke: "none" }, ivSvg);
    seg = [];
  };
  for (let i = 0; i < N; i++) {
    const d0 = IV.value[i] - IV.capital[i];
    if (i > 0) {
      const dPrev = IV.value[i - 1] - IV.capital[i - 1];
      if ((dPrev > 0 && d0 < 0) || (dPrev < 0 && d0 > 0)) { seg.push(i); flush(); seg.push(i - 1); }
    }
    seg.push(i);
  }
  flush();

  [["--s2", IV.capital], ["--s1", IV.value]].forEach(([slot, pts]) => {
    el("path", { d: pts.map((v, i) => (i ? "L" : "M") + X(i) + " " + Y(v)).join(" "),
      fill: "none", stroke: css(slot), "stroke-width": 2,
      "stroke-linejoin": "round", "stroke-linecap": "round" }, ivSvg);
    el("circle", { cx: X(N - 1), cy: Y(pts[N - 1]), r: 4.5, fill: css(slot),
      stroke: css("--surface"), "stroke-width": 2 }, ivSvg);
    const t = el("text", { x: X(N - 1) + 10, y: Y(pts[N - 1]) + 4, fill: css("--ink-2"),
      "font-size": 11.5, "font-weight": 600 }, ivSvg);
    t.textContent = eur0(pts[N - 1]);
  });

  const cross = el("line", { y1: pad.t, y2: h - pad.b, stroke: css("--axis"),
    "stroke-width": 1, opacity: 0 }, ivSvg);
  const d1 = el("circle", { r: 5, fill: css("--s1"), stroke: css("--surface"),
    "stroke-width": 2, opacity: 0 }, ivSvg);
  const d2 = el("circle", { r: 5, fill: css("--s2"), stroke: css("--surface"),
    "stroke-width": 2, opacity: 0 }, ivSvg);
  ivGeom = { w, h, pad, X, Y, N, cross, d1, d2 };
}

ivSvg.addEventListener("pointermove", ev => {
  if (!ivGeom) return;
  const { X, Y, N, pad, w, h } = ivGeom;
  const r = ivSvg.getBoundingClientRect();
  const x = ev.clientX - r.left;
  let idx = 0, best = Infinity;
  for (let i = 0; i < N; i++) { const dd = Math.abs(X(i) - x); if (dd < best) { best = dd; idx = i; } }
  ivGeom.cross.setAttribute("x1", X(idx));
  ivGeom.cross.setAttribute("x2", X(idx));
  ivGeom.cross.setAttribute("opacity", 1);
  ivGeom.d1.setAttribute("cx", X(idx)); ivGeom.d1.setAttribute("cy", Y(IV.value[idx]));
  ivGeom.d2.setAttribute("cx", X(idx)); ivGeom.d2.setAttribute("cy", Y(IV.capital[idx]));
  ivGeom.d1.setAttribute("opacity", 1); ivGeom.d2.setAttribute("opacity", 1);
  const gain = IV.returns[idx];
  ivTip.innerHTML = "<h4>" + DATA.full[idx] + "</h4>" +
    '<div class="tip-row"><span class="key" style="background:var(--s1)"></span>' +
    '<span class="nm">Value</span><span class="vv">' + eur(IV.value[idx]) + "</span></div>" +
    '<div class="tip-row"><span class="key" style="background:var(--s2)"></span>' +
    '<span class="nm">Capital</span><span class="vv">' + eur(IV.capital[idx]) + "</span></div>" +
    '<div class="tip-row"><span class="key band"></span><span class="nm">Return</span>' +
    '<span class="vv" style="color:var(' + (gain >= 0 ? "--pos" : "--neg") + ')">' +
    (gain >= 0 ? "+" : "\\u2212") + eur(Math.abs(gain)) + "</span></div>";
  ivTip.classList.add("on");
  const tw = ivTip.offsetWidth;
  let left = X(idx) + 16;
  if (left + tw > w - pad.r) left = X(idx) - tw - 16;
  ivTip.style.left = Math.max(4, left) + "px";
  ivTip.style.top = pad.t + 4 + "px";
});
ivSvg.addEventListener("pointerleave", () => {
  ivTip.classList.remove("on");
  if (ivGeom) { ivGeom.cross.setAttribute("opacity", 0);
    ivGeom.d1.setAttribute("opacity", 0); ivGeom.d2.setAttribute("opacity", 0); }
});

document.getElementById("ivTbl").innerHTML =
  "<caption>Per account, at 5 August 2026. Return % is measured against capital in that account.</caption>" +
  "<thead><tr><th>Investment account</th><th>Capital</th><th>Return</th>" +
  "<th>Value</th><th>Return %</th></tr></thead><tbody>" +
  IV.accounts.map(a => {
    const pct = Math.abs(a.capital) > 0.005
      ? ((a.returns >= 0 ? "+" : "\\u2212") + Math.abs(a.returns / a.capital * 100).toFixed(2) + "%")
      : "\\u2014";
    const col = Math.abs(a.returns) < 0.005 ? "--muted" : a.returns > 0 ? "--pos" : "--neg";
    return "<tr><td>" + a.name + "</td><td>" + eur(a.capital) + "</td>" +
      "<td style='color:var(" + col + ")'>" + (a.returns >= 0 ? "+" : "\\u2212") +
      eur(Math.abs(a.returns)) + "</td><td>" + eur(a.value) + "</td>" +
      "<td style='color:var(" + col + ")'>" + pct + "</td></tr>";
  }).join("") + "</tbody><tfoot><tr><td>Portfolio</td><td>" + eur(ivCapEnd) +
  "</td><td style='color:var(" + (ivRet >= 0 ? "--pos" : "--neg") + ")'>" +
  (ivRet >= 0 ? "+" : "\\u2212") + eur(Math.abs(ivRet)) + "</td><td>" +
  eur(IV.value[IV.value.length - 1]) + "</td><td style='color:var(" +
  (ivRet >= 0 ? "--pos" : "--neg") + ")'>" + (ivRet >= 0 ? "+" : "\\u2212") +
  Math.abs(ivRet / ivCapEnd * 100).toFixed(2) + "%</td></tr></tfoot>";

/* ----------------------------------------------- small multiples ---- */
const panels = document.getElementById("panels");
const minis = [];
DATA.panels.forEach(p => {
  const d0 = p.points[0], dN = p.points[p.points.length - 1], dd = dN - d0;
  const dir = Math.abs(dd) < 0.005 ? "flat" : dd > 0 ? "up" : "down";
  const arrow = dir === "flat" ? "\\u2192" : dir === "up" ? "\\u2191" : "\\u2193";
  const wrap = document.createElement("div");
  wrap.className = "pan";
  wrap.innerHTML =
    '<div class="pan-nm">' + p.name + "</div>" +
    '<div class="pan-meta">' + p.type + " \\u00b7 " + p.bank + "</div>" +
    '<div class="pan-row"><span class="pan-val">' + eur0(dN) + "</span>" +
    '<span class="pan-d ' + dir + '">' + arrow + " " + eur0(Math.abs(dd)) + "</span></div>" +
    '<div class="pan-host"><svg role="img" aria-label="' + p.name +
    ' balance from January to August 2026"></svg><div class="tip"></div></div>';
  panels.appendChild(wrap);
  minis.push({ p, svg: wrap.querySelector("svg"), tip: wrap.querySelector(".tip"),
               host: wrap.querySelector(".pan-host") });
});

/* Blank panels so the last row never shows the grid's own background through a
   half-filled row. Count follows the live column count. */
const fillers = [];
function refill() {
  const cols = getComputedStyle(panels).gridTemplateColumns.split(" ").length;
  const need = (cols - (DATA.panels.length % cols)) % cols;
  while (fillers.length > need) panels.removeChild(fillers.pop());
  while (fillers.length < need) {
    const f = document.createElement("div");
    f.className = "pan";
    f.setAttribute("aria-hidden", "true");
    panels.appendChild(f);
    fillers.push(f);
  }
}

function drawMini(m) {
  const w = Math.max(150, m.host.clientWidth || 190), h = 62, padB = 14, padT = 8;
  const s = m.svg;
  s.setAttribute("width", w); s.setAttribute("height", h);
  s.setAttribute("viewBox", "0 0 " + w + " " + h);
  while (s.firstChild) s.removeChild(s.firstChild);

  const pts = m.p.points;
  const lo0 = Math.min(...pts), hi0 = Math.max(...pts);
  const span = hi0 - lo0 || Math.max(1, Math.abs(hi0) || 1);
  const lo = lo0 - span * 0.14, hi = hi0 + span * 0.14;
  const N = pts.length;
  const X = i => 2 + (i * (w - 4)) / (N - 1);
  const Y = v => padT + (1 - (v - lo) / (hi - lo)) * (h - padT - padB);
  const col = css("--s1");

  if (lo0 < -0.005) {
    el("line", { x1: 0, x2: w, y1: Y(0), y2: Y(0), stroke: css("--axis"), "stroke-width": 1 }, s);
  }
  const line = pts.map((v, i) => (i ? "L" : "M") + X(i) + " " + Y(v)).join(" ");
  /* An account that never moved gets a bare line — an area wash under a flat
     zero line reads as a quantity that isn't there. */
  if (hi0 - lo0 > 0.005) {
    el("path", { d: line + " L" + X(N - 1) + " " + (h - padB) + " L" + X(0) + " " + (h - padB) + " Z",
      fill: col, opacity: 0.1, stroke: "none" }, s);
  }
  el("path", { d: line, fill: "none", stroke: col, "stroke-width": 2,
    "stroke-linejoin": "round", "stroke-linecap": "round" }, s);
  el("circle", { cx: X(N - 1), cy: Y(pts[N - 1]), r: 4, fill: col,
    stroke: css("--surface"), "stroke-width": 2 }, s);
  const dot = el("circle", { r: 4, fill: col, stroke: css("--surface"),
    "stroke-width": 2, opacity: 0 }, s);
  m.geom = { X, Y, N, dot, w };
}

minis.forEach(m => {
  m.svg.addEventListener("pointermove", ev => {
    if (!m.geom) return;
    const r = m.svg.getBoundingClientRect();
    const x = ev.clientX - r.left;
    let idx = 0, best = Infinity;
    for (let i = 0; i < m.geom.N; i++) {
      const dd = Math.abs(m.geom.X(i) - x); if (dd < best) { best = dd; idx = i; }
    }
    m.geom.dot.setAttribute("cx", m.geom.X(idx));
    m.geom.dot.setAttribute("cy", m.geom.Y(m.p.points[idx]));
    m.geom.dot.setAttribute("opacity", 1);
    m.tip.innerHTML = "<h4>" + DATA.full[idx] + "</h4>" +
      '<div class="tip-row"><span class="key" style="background:var(--s1)"></span>' +
      '<span class="vv">' + eur(m.p.points[idx]) + "</span></div>";
    m.tip.classList.add("on");
    const tw = m.tip.offsetWidth;
    let left = m.geom.X(idx) + 12;
    if (left + tw > m.geom.w) left = m.geom.X(idx) - tw - 12;
    m.tip.style.left = Math.max(0, left) + "px";
    m.tip.style.top = "-6px";
  });
  m.svg.addEventListener("pointerleave", () => {
    m.tip.classList.remove("on");
    if (m.geom) m.geom.dot.setAttribute("opacity", 0);
  });
});

/* -------------------------------------------------------------- table ---- */
const featured = new Map(DATA.series.map((s, i) => [s.name, SLOTS[i]]));
const tbl = document.getElementById("tbl");
const head = ["Account", "Type", "1 Jan"].concat(DATA.labels.slice(1));
tbl.innerHTML =
  "<caption>Full data — the same values plotted above, for reading exact figures. " +
  "Scroll the table sideways for the later months.</caption>" +
  "<thead><tr>" + head.map(x => "<th>" + x + "</th>").join("") + "</tr></thead>" +
  "<tbody>" + DATA.table.map(r => {
    const slot = featured.get(r.name);
    return "<tr><td class='nm'><span class='key" + (slot ? "" : " none") + "'" +
      (slot ? " style='background:var(" + slot + ")'" : "") + "></span>" + r.name + "</td>" +
      "<td style='text-align:left;color:var(--muted)'>" + r.type + "</td>" +
      r.points.map(v => "<td>" + eur(v) + "</td>").join("") + "</tr>";
  }).join("") + "</tbody>" +
  "<tfoot><tr><td>Net worth</td><td></td>" +
  DATA.totals.map(v => "<td>" + eur(v) + "</td>").join("") + "</tr></tfoot>";

/* --------------------------------------------------------- draw & resize -- */
function drawAll() { drawMain(); drawInv(); refill(); minis.forEach(drawMini); }
drawAll();
let raf = 0;
new ResizeObserver(() => {
  cancelAnimationFrame(raf);
  raf = requestAnimationFrame(drawAll);
}).observe(document.body);
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", drawAll);
new MutationObserver(drawAll).observe(document.documentElement,
  { attributes: true, attributeFilter: ["data-theme"] });
</script>
"""

body = HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False))

# Body-only fragment, for hosts that supply their own document shell.
with open("balances.html", "w") as fh:
    fh.write(body)

# Standalone document, for GitHub Pages / opening straight off disk.
# noindex+nofollow is what actually keeps this page out of search results: a
# project site's robots.txt lives under /<repo>/ and crawlers only read the one
# at the domain root, so the meta tag is the load-bearing part.
STANDALONE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
<meta name="referrer" content="no-referrer">
<meta name="color-scheme" content="light dark">
<style>*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }</style>
__BODY__
</head>
<body>
</body>
</html>
"""
# <title> and <style> come from the fragment and belong in <head>; everything
# after them is markup, so split the fragment at the end of its style block.
cut = body.index("</style>") + len("</style>")
doc = (STANDALONE
       .replace("__BODY__", body[:cut])
       .replace("<body>\n</body>", "<body>" + body[cut:] + "</body>"))
with open("index.html", "w") as fh:
    fh.write(doc)
print("balances.html + index.html written")
