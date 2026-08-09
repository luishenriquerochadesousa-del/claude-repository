"""Independently evaluate the workbook's formulas and compare against balances.json.

LibreOffice cannot load xlsx in this sandbox, so recalc.py is unavailable. The
`formulas` package evaluates the real formula strings out of the saved file, which
is what needs checking: the SUMIFS ranges, the month-key row anchor, and the
previous-month column offsets.
"""

import json

import formulas

FILE = "Account Balances 2026.xlsx"
LABELS = {"2026-01": "Jan 2026", "2026-02": "Feb 2026", "2026-03": "Mar 2026",
          "2026-04": "Apr 2026", "2026-05": "May 2026", "2026-06": "Jun 2026",
          "2026-07": "Jul 2026", "2026-08": "Aug 2026"}

exp = json.load(open("balances.json"))
months = exp["months"]

xl = formulas.ExcelModel().loads(FILE).finish()
sol = xl.calculate()

# Map "'[FILE]SHEET'!A1" solution keys to plain "SHEET!A1".
vals = {}
for key, cell in sol.items():
    k = key.upper()
    if "]" not in k or "!" not in k:
        continue
    sheet, _, ref = k.partition("]")[2].partition("!")
    sheet = sheet.strip("'")
    try:
        v = cell.value[0, 0]
    except Exception:
        continue
    vals[f"{sheet}!{ref}"] = v


def num(ref):
    v = vals.get(f"BALANCES!{ref}")
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


# Row order on the Balances sheet is alphabetical by account name.
names = sorted(a["name"] for a in exp["accounts"])
by_name = {a["name"]: a for a in exp["accounts"]}
COLS = ["E", "F", "G", "H", "I", "J", "K", "L"]

bad = 0
for i, name in enumerate(names, start=5):
    want = by_name[name]
    for k, col in enumerate(COLS):
        got, w = num(f"{col}{i}"), want["balances"][k]
        if got is None or abs(got - w) > 0.005:
            print(f"MISMATCH {name} {months[k]}: sheet {got} vs expected {w}")
            bad += 1

trow = 4 + len(names) + 1
for k, col in enumerate(COLS):
    got, w = num(f"{col}{trow}"), exp["totals"][k]
    if got is None or abs(got - w) > 0.005:
        print(f"MISMATCH TOTAL {months[k]}: sheet {got} vs expected {w}")
        bad += 1

start_got = num(f"D{trow}")
if start_got is None or abs(start_got - exp["start_total"]) > 0.005:
    print(f"MISMATCH start total: sheet {start_got} vs expected {exp['start_total']}")
    bad += 1

delta_got = num(f"L{trow + 2}")
delta_want = round(exp["totals"][-1] - exp["start_total"], 2)
if delta_got is None or abs(delta_got - delta_want) > 0.005:
    print(f"MISMATCH change-since-Jan: sheet {delta_got} vs expected {delta_want}")
    bad += 1

# Any formula cell that evaluated to an Excel error string.
errs = [k for k, v in vals.items() if isinstance(v, str) and v.startswith("#")]
if errs:
    print(f"FORMULA ERRORS: {errs[:20]}")

cells = len(names) * len(COLS) + len(COLS) + 2
print(f"\n{cells - bad}/{cells} checked cells match; {len(errs)} formula errors; "
      f"{'OK' if not bad and not errs else 'FAILED'}")
