"""Rebuild per-account monthly balances for the Notion Personal Finance Tracker.

Balance(account, month-end) =
    Starting Balance (2026-01-01)
  + sum(Income      up to month)
  - sum(Expenses    up to month)
  + sum(Transfers IN  up to month)
  - sum(Transfers OUT up to month)

All expense rows are "Paid" and all transfer rows are "Executed", so no status
filtering is needed. Transfers with an empty From/To are external flows
(money in from outside / money out to outside) and are counted one-sided.
"""

import json
from collections import defaultdict

MONTHS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05",
          "2026-06", "2026-07", "2026-08"]

ACCOUNTS = {
    "31c08fe59d8d8025bc1cf1d752004897": ("Conta Bolsas",                          "Account",    "Santander",     0.00),
    "2f308fe59d8d806b83e7d8b820819447": ("Conta Corrente",                         "Account",    "Santander",   344.63),
    "31c08fe59d8d8069bec2ca94acea5351": ("Conta Poupança",                         "Account",    "Santander",  2600.31),
    "32c08fe59d8d805e8fdeee6b04cda3fd": ("PayPal",                                 "Account",    "PayPal",        0.00),
    "2f308fe59d8d80d58b64e2fd21b32e72": ("Revolut",                                "Account",    "Revolut",       0.00),
    "31c08fe59d8d80e78746de3f0aa7b735": ("Trade Republic Account",                 "Account",    "Trade Republic", 340.94),
    "2f308fe59d8d80c5a60af26183c202ca": ("Cash Withdrawls",                        "Cash",       "—",             0.00),
    "31c08fe59d8d809395d0e7536d3be88b": ("Certificados de Aforro CTT - Série E",   "Investment", "CTT/Estado",  534.73),
    "35908fe59d8d80cba82cd787bd135470": ("Certificados de Aforro CTT - Série F",   "Investment", "CTT/Estado", 5512.73),
    "37808fe59d8d808fa8f7d7bbb5cd0b64": ("Revolut - Fundo Emergência",             "Investment", "Revolut",       0.00),
    "38f08fe59d8d80f0a482c9d74a3e4e52": ("Revolut - Wealth Build",                 "Investment", "Revolut",       0.00),
    "3b408fe59d8d80a5aba1d401da73274e": ("Robinhood",                              "Investment", "Robinhood",     0.00),
    "31c08fe59d8d803f9d4feb846c0c5cd6": ("Trade Republic Inv. - Brokerage",        "Investment", "Trade Republic", 7687.87),
    "35908fe59d8d8049b574ef9d59f54559": ("Trade Republic Inv. - Crypto",           "Investment", "Trade Republic",    0.00),
    "38f08fe59d8d800aaf90dd05fa6050ae": ("Trading 212 Account",                    "Investment", "Trading 212",   0.00),
}

CC, CASH, REV, TRA = ("2f308fe59d8d806b83e7d8b820819447", "2f308fe59d8d80c5a60af26183c202ca",
                      "2f308fe59d8d80d58b64e2fd21b32e72", "31c08fe59d8d80e78746de3f0aa7b735")
BOLSAS, POUP, PAYPAL = ("31c08fe59d8d8025bc1cf1d752004897", "31c08fe59d8d8069bec2ca94acea5351",
                        "32c08fe59d8d805e8fdeee6b04cda3fd")
CTTE, CTTF = "31c08fe59d8d809395d0e7536d3be88b", "35908fe59d8d80cba82cd787bd135470"
EMERG, WEALTH = "37808fe59d8d808fa8f7d7bbb5cd0b64", "38f08fe59d8d80f0a482c9d74a3e4e52"
ROBIN, BROK, CRYPTO = ("3b408fe59d8d80a5aba1d401da73274e", "31c08fe59d8d803f9d4feb846c0c5cd6",
                       "35908fe59d8d8049b574ef9d59f54559")
T212 = "38f08fe59d8d800aaf90dd05fa6050ae"

# --- monthly aggregates pulled from Notion (SQL GROUP BY account, month) -----
INCOME = {
    CC: {"2026-01": 330.00, "2026-02": 6928.70, "2026-03": 3402.11, "2026-04": 5012.96,
         "2026-05": 3499.29, "2026-06": 3499.29, "2026-07": 2446.40},
}

EXPENSES = {
    CC:   {"2026-01": 1863.43, "2026-02": 2955.16, "2026-03": 811.12, "2026-04": 552.79,
           "2026-05": 970.97, "2026-06": 940.35, "2026-07": 954.40, "2026-08": 895.00},
    CASH: {"2026-03": 45.89},
    REV:  {"2026-01": 1795.52, "2026-02": 987.69, "2026-03": 648.82, "2026-04": 638.08,
           "2026-05": 586.02, "2026-06": 308.23, "2026-07": 310.90, "2026-08": 102.02},
    TRA:  {"2026-03": 302.75, "2026-04": 361.93, "2026-05": 1021.65, "2026-06": 1599.89,
           "2026-07": 227.93, "2026-08": 357.08},
}

# Transfers leaving the account ("From Account").
TRANSFER_OUT = {
    CC:     {"2026-01": 1786.16, "2026-02": 1315.24, "2026-03": 3207.48, "2026-04": 2454.30,
             "2026-05": 4775.90, "2026-06": 7742.35, "2026-07": 2470.71, "2026-08": 1751.30},
    CASH:   {"2026-04": 6.89, "2026-05": 1.99},
    REV:    {"2026-01": 5.00, "2026-03": 106.58, "2026-04": 17.00, "2026-05": 97.76,
             "2026-06": 1454.53, "2026-07": 673.50, "2026-08": 371.00},
    BOLSAS: {"2026-03": 4.00},
    BROK:   {"2026-03": 242.81, "2026-06": 40.68},
    POUP:   {"2026-01": 1600.00, "2026-02": 1010.24, "2026-07": 20.00, "2026-08": 1850.00},
    TRA:    {"2026-01": 341.00, "2026-03": 1385.00, "2026-04": 2308.53, "2026-05": 3424.57,
             "2026-06": 2375.52, "2026-07": 1983.58, "2026-08": 965.97},
    PAYPAL: {"2026-01": 5.00, "2026-03": 40.99, "2026-05": 75.80, "2026-06": 23.46,
             "2026-07": 42.50},
    CRYPTO: {"2026-05": 23.43, "2026-06": 38.09, "2026-07": 49.86},
    CTTF:   {"2026-08": 1851.19},
    EMERG:  {"2026-06": 345.00, "2026-07": 209.00, "2026-08": 396.00},
    # "Reembolso - Trading 212" (2026-07-06) is tagged to Trading 212 AND Robinhood;
    # attributed to Trading 212, which the description names. It reverses the
    # 2026-06-29 inflow below, so the net effect on either account is zero.
    T212:   {"2026-07": 100.00 + 25.00 * 0},
    WEALTH: {"2026-07": 25.00, "2026-08": 35.00},
}

# Transfers arriving in the account ("To Account").
TRANSFER_IN = {
    CC:     {"2026-01": 4114.70, "2026-02": 2821.54, "2026-03": 4.00, "2026-04": 0.45,
             "2026-05": 28.46, "2026-06": 1011.87, "2026-07": 252.26, "2026-08": 1850.00},
    CASH:   {"2026-02": 10.00, "2026-03": 45.99},
    REV:    {"2026-01": 1781.16, "2026-02": 1007.63, "2026-03": 1731.48, "2026-04": 39.43,
             "2026-05": 307.29, "2026-06": 1815.00, "2026-07": 959.00, "2026-08": 531.00},
    BOLSAS: {"2026-03": 4.00},
    BROK:   {"2026-01": 530.53, "2026-02": 0.10, "2026-03": 1385.00, "2026-04": 2470.67,
             "2026-05": 4076.67, "2026-06": 2285.73, "2026-07": 1909.51, "2026-08": 868.23},
    POUP:   {"2026-01": 5.00, "2026-02": 5.00, "2026-03": 5.00, "2026-04": 5.00,
             "2026-05": 5.00, "2026-06": 5.00, "2026-07": 5.00, "2026-08": 1851.19},
    CTTE:   {"2026-02": 3.37, "2026-05": 3.44},
    TRA:    {"2026-01": 0.76, "2026-02": 303.32, "2026-03": 2480.52, "2026-04": 2444.50,
             "2026-05": 4505.95, "2026-06": 4038.74, "2026-07": 1337.25, "2026-08": 1526.55},
    PAYPAL: {"2026-01": 5.00, "2026-03": 99.03, "2026-05": 17.76, "2026-06": 23.46,
             "2026-07": 42.50},
    CRYPTO: {"2026-04": 766.75, "2026-06": 100.00, "2026-07": 100.00, "2026-08": 100.01},
    CTTF:   {"2026-02": 20.90, "2026-04": 1.57, "2026-05": 21.30},
    EMERG:  {"2026-06": 750.00, "2026-07": 250.82},
    T212:   {"2026-06": 100.00, "2026-07": 10.00},   # 2026-06 row double-tagged, see above
    WEALTH: {"2026-06": 250.00, "2026-07": 250.54},
    ROBIN:  {"2026-07": 50.00, "2026-08": 500.00},
}

# --- build the running-balance matrix ---------------------------------------
rows = []
for aid, (name, kind, bank, start) in ACCOUNTS.items():
    bal, series, flows = start, [], []
    for m in MONTHS:
        inflow = INCOME.get(aid, {}).get(m, 0.0) + TRANSFER_IN.get(aid, {}).get(m, 0.0)
        outflow = EXPENSES.get(aid, {}).get(m, 0.0) + TRANSFER_OUT.get(aid, {}).get(m, 0.0)
        bal += inflow - outflow
        series.append(round(bal, 2))
        flows.append(round(inflow - outflow, 2))
    rows.append({"id": aid, "name": name, "type": kind, "bank": bank,
                 "start": round(start, 2), "balances": series, "net": flows})

rows.sort(key=lambda r: -r["balances"][-1])
totals = [round(sum(r["balances"][i] for r in rows), 2) for i in range(len(MONTHS))]
start_total = round(sum(r["start"] for r in rows), 2)

out = {"months": MONTHS, "accounts": rows, "totals": totals, "start_total": start_total}
with open("balances.json", "w") as fh:
    json.dump(out, fh, indent=1)

# Flat per-account/per-month flow table, for the spreadsheet's input sheet.
flows = []
for aid, (name, kind, bank, start) in ACCOUNTS.items():
    for m in MONTHS:
        inc = INCOME.get(aid, {}).get(m, 0.0)
        exp = EXPENSES.get(aid, {}).get(m, 0.0)
        tin = TRANSFER_IN.get(aid, {}).get(m, 0.0)
        tout = TRANSFER_OUT.get(aid, {}).get(m, 0.0)
        if inc or exp or tin or tout:
            flows.append([name, m, round(inc, 2), round(exp, 2), round(tin, 2), round(tout, 2)])
with open("flows.json", "w") as fh:
    json.dump({"months": MONTHS,
               "accounts": [[n, k, b, round(s, 2)] for n, k, b, s in ACCOUNTS.values()],
               "flows": flows}, fh, indent=1)

if __name__ == "__main__":
    # --- report -----------------------------------------------------------------
    w = max(len(r["name"]) for r in rows)
    print(f"{'Account':<{w}} {'Jan 1':>9} " + " ".join(f"{m[5:]:>9}" for m in MONTHS))
    for r in rows:
        print(f"{r['name']:<{w}} {r['start']:>9,.2f} " + " ".join(f"{v:>9,.2f}" for v in r["balances"]))
    print("-" * (w + 10 * (len(MONTHS) + 1)))
    print(f"{'TOTAL (net worth)':<{w}} {start_total:>9,.2f} " + " ".join(f"{v:>9,.2f}" for v in totals))
    print()
    print("Sanity check — net worth change should equal income - expenses + external net:")
    inc = sum(v for d in INCOME.values() for v in d.values())
    exp = sum(v for d in EXPENSES.values() for v in d.values())
    ext_in = 2704.99 + 1846.38 + 1071.56 + 971.00 + 761.64 + 1061.92 + 136.69 + 6.52   # From Account empty
    ext_out = 5.00 + 303.40 + 29.35 + 195.22 + 2701.75 + 543.96                        # To Account empty
    print(f"  income {inc:,.2f} - expenses {exp:,.2f} + external in {ext_in:,.2f} - external out {ext_out:,.2f}"
          f" = {inc - exp + ext_in - ext_out:,.2f}")
    print(f"  matrix: {totals[-1]:,.2f} - {start_total:,.2f} = {totals[-1] - start_total:,.2f}")

