"""Evaluate the workbook and check the Invested vs Returns sheet against investments.json."""

import json

import formulas

FILE = "Account Balances 2026.xlsx"
inv = json.load(open("investments.json"))
names = [a["name"] for a in inv["accounts"]]
by = {a["name"]: a for a in inv["accounts"]}
COLS = ["E", "F", "G", "H", "I", "J", "K", "L"]

xl = formulas.ExcelModel().loads(FILE).finish()
sol = xl.calculate()
vals = {}
for key, cell in sol.items():
    k = key.upper()
    if "]" not in k or "!" not in k:
        continue
    sheet, _, ref = k.partition("]")[2].partition("!")
    try:
        vals[f"{sheet.strip(chr(39))}!{ref}"] = cell.value[0, 0]
    except Exception:
        pass


def num(sheet, ref):
    v = vals.get(f"{sheet}!{ref}")
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


S = "INVESTED VS RETURNS"
BLOCKS = {"capital": 6, "returns": 19, "value": 32}
bad = 0
for field, first in BLOCKS.items():
    for i, name in enumerate(names):
        for k, col in enumerate(COLS):
            got, want = num(S, f"{col}{first + i}"), by[name][field][k]
            if got is None or abs(got - want) > 0.005:
                print(f"MISMATCH {field} {name} {inv['months'][k]}: {got} vs {want}")
                bad += 1

TOT = {"capital": 14, "returns": 27, "value": 40}
for field, r in TOT.items():
    for k, col in enumerate(COLS):
        got, want = num(S, f"{col}{r}"), inv[field][k]
        if got is None or abs(got - want) > 0.005:
            print(f"MISMATCH total {field} {inv['months'][k]}: {got} vs {want}")
            bad += 1

# Value block must agree with the independently built Balances sheet.
bal = {a["name"]: a for a in json.load(open("balances.json"))["accounts"]}
for i, name in enumerate(names):
    for k, col in enumerate(COLS):
        got, want = num(S, f"{col}{32 + i}"), bal[name]["balances"][k]
        if got is None or abs(got - want) > 0.005:
            print(f"MISMATCH value-vs-balance {name} {inv['months'][k]}: {got} vs {want}")
            bad += 1

checks = [("summary capital", "E44", inv["capital"][-1]),
          ("summary value", "E45", inv["value"][-1]),
          ("summary return", "E46", inv["returns"][-1])]
for label, ref, want in checks:
    got = num(S, ref)
    if got is None or abs(got - want) > 0.005:
        print(f"MISMATCH {label}: {got} vs {want}")
        bad += 1

pct = num(S, "E47")
want_pct = round(inv["returns"][-1] / inv["capital"][-1], 4)
if pct is None or abs(pct - round(want_pct, 2)) > 0.01:
    print(f"note: return-on-capital cell reads {vals.get(S + '!E47')!r} (expected ~{want_pct})")

irr_m = vals.get(f"{S}!E52")
irr_a = vals.get(f"{S}!E53")
print(f"\nIRR cells: monthly={irr_m!r} annualised={irr_a!r} "
      f"(python: {inv['irr_monthly']:.6f} / {inv['irr_annual']:.6f})")

errs = [k for k, v in vals.items() if isinstance(v, str) and v.startswith("#")]
if errs:
    print(f"FORMULA ERRORS: {errs[:20]}")

n = len(names) * len(COLS) * 4 + len(COLS) * 3 + 3
print(f"\n{n - bad}/{n} checked cells match; {len(errs)} formula errors; "
      f"{'OK' if not bad and not errs else 'FAILED'}")
