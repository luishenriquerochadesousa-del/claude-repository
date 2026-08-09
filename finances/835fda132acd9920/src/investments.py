"""Split the investment portfolio into capital contributed vs. investment returns.

The tracker records returns explicitly, as one-sided transfers (no From / no To
account) whose description names them: "Portfolio Delta", "… - Delta - <month>",
"Cash Dividends - <company>", "Trade Republic - Account Interest (2%)" and
"Cashback Savings Plan". Checked against the full transfer list, EVERY one-sided
flow touching an Investment-type account is one of these — so for those accounts:

    one-sided inflow   = gain        two-sided inflow  = capital contributed
    one-sided outflow  = loss        two-sided outflow = capital withdrawn

Dividends and the 2% cash interest are paid into Trade Republic *Account* (a cash
account, not the portfolio), so they leave the portfolio and are reported
separately as investment income received in cash.

    capital(t) = capital(t-1) + contributions(t) - withdrawals(t)
    returns(t) = returns(t-1) + gains(t)        - losses(t)
    value(t)   = capital(t) + returns(t)        <- asserted against the balances
"""

import json

from build import (ACCOUNTS, BROK, CRYPTO, CTTE, CTTF, EMERG, MONTHS, TRANSFER_IN,
                   TRANSFER_OUT, WEALTH)

# One-sided inflows into investment accounts — gains.
GAINS = {
    BROK:   {"2026-01": 189.53,          # Portfolio Delta - January
             "2026-02": 0.10,            # Portfolio Delta - February
             "2026-04": 3.02 + 910.06,   # Cashback savings plan + Portfolio Delta
             "2026-05": 3.61 + 648.49,
             "2026-06": 10.21,
             "2026-07": 15.00 + 10.93,   # cashback + June delta, entered 31 Jul
             "2026-08": 2.27},
    CRYPTO: {"2026-04": 15.81},
    CTTE:   {"2026-02": 3.37, "2026-05": 3.44},        # CTT Aforro interest
    CTTF:   {"2026-02": 20.90, "2026-04": 1.57, "2026-05": 21.30},
    WEALTH: {"2026-07": 0.54},
    EMERG:  {"2026-07": 0.82},
}

# One-sided outflows from investment accounts — losses.
LOSSES = {
    BROK:   {"2026-03": 242.81,   # Portfolio Delta - March
             "2026-06": 40.68},   # labelled "(+)" in Notion but entered as an outflow
    CRYPTO: {"2026-05": 23.43, "2026-06": 38.09, "2026-07": 49.86},
}

# Dividends and the 2% cash interest, credited to Trade Republic Account.
INCOME_TO_CASH = {"2026-01": 0.76, "2026-02": 3.32, "2026-03": 0.52, "2026-04": 0.66,
                  "2026-05": 5.95, "2026-06": 6.80, "2026-07": 2.14, "2026-08": 4.25}

PORTFOLIO = [aid for aid, (_n, kind, _b, _s) in ACCOUNTS.items() if kind == "Investment"]


def get(tbl, aid, m):
    return tbl.get(aid, {}).get(m, 0.0)


rows, problems = [], []
for aid in PORTFOLIO:
    name, _kind, bank, start = ACCOUNTS[aid]
    cap, ret = start, 0.0
    caps, rets, vals, contribs, gains_m = [], [], [], [], []
    for m in MONTHS:
        gain, loss = get(GAINS, aid, m), get(LOSSES, aid, m)
        contribution = get(TRANSFER_IN, aid, m) - gain
        withdrawal = get(TRANSFER_OUT, aid, m) - loss
        if contribution < -0.005 or withdrawal < -0.005:
            problems.append(f"{name} {m}: contribution {contribution:.2f}, withdrawal {withdrawal:.2f}")
        cap += contribution - withdrawal
        ret += gain - loss
        caps.append(round(cap, 2))
        rets.append(round(ret, 2))
        vals.append(round(cap + ret, 2))
        contribs.append(round(contribution - withdrawal, 2))
        gains_m.append(round(gain - loss, 2))
    rows.append({"name": name, "bank": bank, "start": round(start, 2),
                 "capital": caps, "returns": rets, "value": vals,
                 "net_contrib": contribs, "net_gain": gains_m})

# The split must reproduce the balances computed independently in build.py.
balances = {a["name"]: a for a in json.load(open("balances.json"))["accounts"]}
for r in rows:
    want = balances[r["name"]]["balances"]
    for k, m in enumerate(MONTHS):
        if abs(r["value"][k] - want[k]) > 0.005:
            problems.append(f"{r['name']} {m}: split {r['value'][k]} vs balance {want[k]}")

cap_t = [round(sum(r["capital"][k] for r in rows), 2) for k in range(len(MONTHS))]
ret_t = [round(sum(r["returns"][k] for r in rows), 2) for k in range(len(MONTHS))]
val_t = [round(c + s, 2) for c, s in zip(cap_t, ret_t)]
start_cap = round(sum(r["start"] for r in rows), 2)


def irr(flows):
    """Money-weighted monthly rate solving NPV = 0; None if it doesn't bracket."""
    def npv(r):
        return sum(cf / (1 + r) ** t for t, cf in enumerate(flows))
    lo, hi = -0.95, 2.0
    if npv(lo) * npv(hi) > 0:
        return None
    for _ in range(300):
        mid = (lo + hi) / 2
        if npv(lo) * npv(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


# Cash flows from the investor's side: opening capital and each month's net
# contribution are money in; the closing value is what it is worth now.
# Run through 31 July — August is only 5 days and would distort the rate.
n = MONTHS.index("2026-07") + 1
flows = [-start_cap] + [-(sum(r["net_contrib"][k] for r in rows)) for k in range(n)]
flows[n] += val_t[n - 1]
monthly = irr(flows)
annual = (1 + monthly) ** 12 - 1 if monthly is not None else None

out = {
    "months": MONTHS, "accounts": rows,
    "capital": cap_t, "returns": ret_t, "value": val_t, "start_capital": start_cap,
    "income_to_cash": INCOME_TO_CASH,
    "income_to_cash_total": round(sum(INCOME_TO_CASH.values()), 2),
    "irr_monthly": monthly, "irr_annual": annual, "irr_through": "2026-07",
}
with open("investments.json", "w") as fh:
    json.dump(out, fh, indent=1)

if __name__ == "__main__":
    w = max(len(r["name"]) for r in rows)
    print(f"{'Account':<{w}} {'capital':>10} {'returns':>10} {'value':>11} {'ret %':>8}")
    for r in sorted(rows, key=lambda r: -r["value"][-1]):
        c, s, v = r["capital"][-1], r["returns"][-1], r["value"][-1]
        pct = f"{s / c * 100:+.2f}%" if abs(c) > 0.005 else "—"
        print(f"{r['name']:<{w}} {c:>10,.2f} {s:>10,.2f} {v:>11,.2f} {pct:>8}")
    print("-" * (w + 43))
    print(f"{'PORTFOLIO':<{w}} {cap_t[-1]:>10,.2f} {ret_t[-1]:>10,.2f} {val_t[-1]:>11,.2f} "
          f"{ret_t[-1] / cap_t[-1] * 100:>+7.2f}%")
    print()
    print(f"Opening capital 1 Jan      {start_cap:>10,.2f}")
    print(f"Net contributed since      {cap_t[-1] - start_cap:>10,.2f}")
    print(f"Returns inside portfolio   {ret_t[-1]:>10,.2f}")
    print(f"Dividends/interest to cash {out['income_to_cash_total']:>10,.2f}"
          "   (paid into Trade Republic Account)")
    print(f"Total investment gain      {ret_t[-1] + out['income_to_cash_total']:>10,.2f}")
    if annual is not None:
        print(f"\nMoney-weighted return through 31 Jul: {monthly * 100:.2f}%/month "
              f"= {annual * 100:.1f}% annualised")
    print("\ncapital:", cap_t)
    print("returns:", ret_t)
    print("value:  ", val_t)
    print("\n" + ("PROBLEMS:\n  " + "\n  ".join(problems) if problems
                  else "All checks pass: split reproduces every account balance exactly."))
