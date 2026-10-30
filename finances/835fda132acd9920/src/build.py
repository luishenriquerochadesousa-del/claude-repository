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

MONTHS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06",
          "2026-07", "2026-08", "2026-09", "2026-10"]

ACCOUNTS = {
    "31c08fe59d8d8025bc1cf1d752004897": ("Conta Bolsas",                          "Account",    "Santander",     0.00),
    "2f308fe59d8d806b83e7d8b820819447": ("Conta Corrente",                         "Account",    "Santander",   344.63),
    "31c08fe59d8d8069bec2ca94acea5351": ("Conta Poupança",                         "Account",    "Santander",  2600.31),
    "32c08fe59d8d805e8fdeee6b04cda3fd": ("PayPal",                                 "Account",    "PayPal",        0.00),
    "2f308fe59d8d80d58b64e2fd21b32e72": ("Revolut",                                "Account",    "Revolut",       0.00),
    "31c08fe59d8d80e78746de3f0aa7b735": ("Trade Republic Account",                 "Account",    "Trade Republic", 340.94),
    "2f308fe59d8d80c5a60af26183c202ca": ("Cash Withdrawls",                        "Cash",       "—",             0.00),
    "40908fe59d8d807884e5e27045fae458": ("Flat Deposit",                           "Cash",       "—",             0.00),
    "31c08fe59d8d809395d0e7536d3be88b": ("Certificados de Aforro CTT - Série E",   "Investment", "CTT/Estado",  534.73),
    "35908fe59d8d80cba82cd787bd135470": ("Certificados de Aforro CTT - Série F",   "Investment", "CTT/Estado", 5512.73),
    "37808fe59d8d808fa8f7d7bbb5cd0b64": ("Revolut - Fundo Emergência",             "Investment", "Revolut",       0.00),
    "38f08fe59d8d80f0a482c9d74a3e4e52": ("Revolut - Wealth Build",                 "Investment", "Revolut",       0.00),
    "3b408fe59d8d80a5aba1d401da73274e": ("Robinhood (5% Yield)",                   "Investment", "Robinhood",     0.00),
    "40408fe59d8d805aaecad1087c84ac19": ("Robinhood (Crypto)",                     "Investment", "Robinhood",     0.00),
    "31c08fe59d8d803f9d4feb846c0c5cd6": ("Trade Republic Inv. - Brokerage",        "Investment", "Trade Republic", 7687.87),
    "35908fe59d8d8049b574ef9d59f54559": ("Trade Republic Inv. - Crypto",           "Investment", "Trade Republic",    0.00),
    "38f08fe59d8d800aaf90dd05fa6050ae": ("Trading 212 Account",                    "Investment", "Trading 212",   0.00),
    "40408fe59d8d80f8b6e8fa1204a5d5ec": ("Trading 212 Brokerage",                  "Investment", "Trading 212",   0.00),
}

CC, CASH, REV, TRA = ("2f308fe59d8d806b83e7d8b820819447", "2f308fe59d8d80c5a60af26183c202ca",
                      "2f308fe59d8d80d58b64e2fd21b32e72", "31c08fe59d8d80e78746de3f0aa7b735")
BOLSAS, POUP, PAYPAL = ("31c08fe59d8d8025bc1cf1d752004897", "31c08fe59d8d8069bec2ca94acea5351",
                        "32c08fe59d8d805e8fdeee6b04cda3fd")
FLAT = "40908fe59d8d807884e5e27045fae458"
CTTE, CTTF = "31c08fe59d8d809395d0e7536d3be88b", "35908fe59d8d80cba82cd787bd135470"
EMERG, WEALTH = "37808fe59d8d808fa8f7d7bbb5cd0b64", "38f08fe59d8d80f0a482c9d74a3e4e52"
ROBIN5, ROBINC = "3b408fe59d8d80a5aba1d401da73274e", "40408fe59d8d805aaecad1087c84ac19"
BROK, CRYPTO = "31c08fe59d8d803f9d4feb846c0c5cd6", "35908fe59d8d8049b574ef9d59f54559"
T212, T212BROK = "38f08fe59d8d800aaf90dd05fa6050ae", "40408fe59d8d80f8b6e8fa1204a5d5ec"

# --- monthly aggregates pulled from Notion (SQL GROUP BY account, month) -----
# Re-extracted 30 October 2026. Two rows are dated November in Notion — the rent
# and the second half of the flat deposit — and are treated here as already paid,
# so they are folded into October and the tracker ends there. Each is written as
# "<what Notion has for October> + <the November row>" so the adjustment stays
# visible and is trivial to undo.
INCOME = {
    CC: {"2026-01": 330.00, "2026-02": 6928.70, "2026-03": 3402.11, "2026-04": 5012.96,
         "2026-05": 3499.29, "2026-06": 3499.29, "2026-07": 2446.40, "2026-10": 6336.15},
}

EXPENSES = {
    CC:   {"2026-01": 1863.43, "2026-02": 2955.16, "2026-03": 811.12, "2026-04": 552.79,
           "2026-05": 970.97, "2026-06": 940.35, "2026-07": 954.40, "2026-08": 1025.00,
           "2026-09": 295.10, "2026-10": 129.23},
    CASH: {"2026-03": 45.89},
    REV:  {"2026-01": 1795.52, "2026-02": 987.69, "2026-03": 648.82, "2026-04": 638.08,
           "2026-05": 586.02, "2026-06": 308.23, "2026-07": 310.90, "2026-08": 192.52,
           "2026-09": 70.97, "2026-10": 1302.23 + 1099.00},  # + rent dated Nov
    TRA:  {"2026-03": 302.75, "2026-04": 361.93, "2026-05": 1021.65, "2026-06": 1599.89,
           "2026-07": 227.93, "2026-08": 976.31, "2026-09": 1781.48, "2026-10": 742.29},
}

TRANSFER_OUT = {
    CC:       {"2026-01": 1786.16, "2026-02": 1315.24, "2026-03": 3207.48, "2026-04": 2454.30,
               "2026-05": 4775.90, "2026-06": 7742.35, "2026-07": 2470.71, "2026-08": 3194.86,
               "2026-09": 3632.27, "2026-10": 13030.46},
    CASH:     {"2026-04": 6.89, "2026-05": 1.99, "2026-10": 1.20},
    REV:      {"2026-01": 5.00, "2026-03": 106.58, "2026-04": 17.00, "2026-05": 97.76,
               "2026-06": 1454.53, "2026-07": 673.50, "2026-08": 910.38, "2026-09": 25.00,
               "2026-10": 4055.81 + 1250.00},  # + 1/2 flat deposit dated Nov
    BOLSAS:   {"2026-03": 4.00},
    BROK:     {"2026-03": 242.81, "2026-06": 40.68},
    POUP:     {"2026-01": 1600.00, "2026-02": 1010.24, "2026-07": 20.00, "2026-08": 3188.56,
               "2026-09": 2403.22, "2026-10": 329.32},
    CTTE:     {"2026-10": 329.32},
    CTTF:     {"2026-08": 3183.49, "2026-09": 2398.22, "2026-10": 0.12},
    TRA:      {"2026-01": 341.00, "2026-03": 1385.00, "2026-04": 2308.53, "2026-05": 3424.57,
               "2026-06": 2375.52, "2026-07": 1983.58, "2026-08": 1700.21, "2026-09": 1205.10,
               "2026-10": 810.91},
    PAYPAL:   {"2026-01": 5.00, "2026-03": 40.99, "2026-05": 75.80, "2026-06": 23.46,
               "2026-07": 42.50},
    CRYPTO:   {"2026-05": 23.43, "2026-06": 38.09, "2026-07": 49.86},
    EMERG:    {"2026-06": 345.00, "2026-07": 209.00, "2026-08": 446.86, "2026-10": 10.00},
    WEALTH:   {"2026-07": 25.00, "2026-08": 475.71},
    T212:     {"2026-07": 100.00, "2026-08": 100.06, "2026-09": 10.00, "2026-10": 252.21},
    # The September delta row's Amount has been cleared in Notion, so it is zero here.
    T212BROK: {"2026-10": 42.00},
    ROBIN5:   {"2026-08": 10.00, "2026-09": 1381.51, "2026-10": 4189.00},
    ROBINC:   {"2026-07": 39.59, "2026-08": 12.24, "2026-09": 59.19},
}

TRANSFER_IN = {
    CC:       {"2026-01": 4114.70, "2026-02": 2821.54, "2026-03": 4.00, "2026-04": 0.45,
               "2026-05": 28.46, "2026-06": 1011.87, "2026-07": 252.26, "2026-08": 3323.56,
               "2026-09": 5745.01, "2026-10": 5015.90},
    CASH:     {"2026-02": 10.00, "2026-03": 45.99},
    # The deposit is money you still own, just parked where you cannot spend it,
    # so the transfer into it is internal and does not change net worth.
    FLAT:     {"2026-10": 1250.00 + 1250.00},
    REV:      {"2026-01": 1781.16, "2026-02": 1007.63, "2026-03": 1731.48, "2026-04": 39.43,
               "2026-05": 307.29, "2026-06": 1815.00, "2026-07": 959.00, "2026-08": 1092.56,
               "2026-09": 172.17, "2026-10": 5290.82},
    BOLSAS:   {"2026-03": 4.00},
    BROK:     {"2026-01": 530.53, "2026-02": 0.10, "2026-03": 1385.00, "2026-04": 2470.67,
               "2026-05": 4076.67, "2026-06": 2285.73, "2026-07": 1909.51, "2026-08": 2040.45,
               "2026-09": 2063.97, "2026-10": 815.91},
    POUP:     {"2026-01": 5.00, "2026-02": 5.00, "2026-03": 5.00, "2026-04": 5.00,
               "2026-05": 5.00, "2026-06": 5.00, "2026-07": 5.00, "2026-08": 3183.49,
               "2026-09": 2403.22, "2026-10": 329.32},
    CTTE:     {"2026-02": 3.37, "2026-05": 3.44, "2026-08": 3.54},
    CTTF:     {"2026-02": 20.90, "2026-04": 1.57, "2026-05": 21.30, "2026-07": 1.54,
               "2026-08": 23.79},
    TRA:      {"2026-01": 0.76, "2026-02": 303.32, "2026-03": 2480.52, "2026-04": 2444.50,
               "2026-05": 4505.95, "2026-06": 4038.73, "2026-07": 1337.25, "2026-08": 2761.11,
               "2026-09": 2804.80, "2026-10": 1705.20},
    PAYPAL:   {"2026-01": 5.00, "2026-03": 99.03, "2026-05": 17.76, "2026-06": 23.46,
               "2026-07": 42.50},
    CRYPTO:   {"2026-04": 766.75, "2026-06": 100.00, "2026-07": 100.00, "2026-08": 281.95,
               "2026-09": 228.58},
    EMERG:    {"2026-06": 750.34, "2026-07": 250.42, "2026-08": 0.10, "2026-10": 2360.96},
    WEALTH:   {"2026-06": 250.03, "2026-07": 250.40, "2026-08": 0.28},
    T212:     {"2026-06": 100.00, "2026-07": 10.00, "2026-08": 100.26, "2026-09": 0.01,
               "2026-10": 252.00},
    T212BROK: {"2026-07": 40.98, "2026-08": 100.06, "2026-09": 10.00, "2026-10": 252.21},
    ROBIN5:   {"2026-07": 89.59, "2026-08": 839.58, "2026-09": 1221.53, "2026-10": 6346.23},
    ROBINC:   {"2026-07": 50.00, "2026-09": 101.51},
}

# One-sided transfers, by month (From Account empty = money in from outside the
# tracker; To Account empty = money out of it). Pulled with the rest.
EXT_IN = [2704.99, 1846.38, 1071.56, 971.00, 761.64, 1062.28, 228.67, 714.70,
          3831.39, 576.57, 0.00]
EXT_OUT = [5.00, 0.00, 303.40, 29.35, 195.22, 2701.75, 543.96, 186.34, 195.10, 8.37]
ext_in, ext_out = sum(EXT_IN), sum(EXT_OUT)

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
    print(f"  income {inc:,.2f} - expenses {exp:,.2f} + external in {ext_in:,.2f} - external out {ext_out:,.2f}"
          f" = {inc - exp + ext_in - ext_out:,.2f}")
    print(f"  matrix: {totals[-1]:,.2f} - {start_total:,.2f} = {totals[-1] - start_total:,.2f}")

