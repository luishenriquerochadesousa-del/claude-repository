"""Evaluate the written workbook's formulas and check every value against the JSON.

LibreOffice cannot load xlsx in this sandbox, so recalc.py is unavailable; the
`formulas` package evaluates the real formula strings out of the saved file.

Cell addresses are discovered from the sheets themselves rather than hardcoded,
so adding a month or an account cannot silently point the checks at the wrong
cells — which is exactly what happened when the tracker grew to ten months.
"""

import json

import formulas
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

FILE = "Account Balances 2026.xlsx"
bal = json.load(open("balances.json"))
inv = json.load(open("investments.json"))
MONTHS = bal["months"]
NC = len(MONTHS)

wb = load_workbook(FILE)


def find_row(ws, label, col=1):
    for r in range(1, ws.max_row + 1):
        if ws.cell(row=r, column=col).value == label:
            return r
    raise AssertionError(f"{ws.title}: no row labelled {label!r}")


def block_rows(ws, title, n):
    """A block's data rows and its total row, from its title row."""
    t = find_row(ws, title)
    first = t + 2                      # title, header, then data
    return list(range(first, first + n)), first + n


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
    v = vals.get(f"{sheet.upper()}!{ref}")
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


bad = 0


def check(sheet, ref, want, what):
    global bad
    got = num(sheet, ref)
    if got is None or abs(got - want) > 0.005:
        print(f"MISMATCH {what} [{sheet}!{ref}]: {got} vs {want}")
        bad += 1


# ---------------------------------------------------------------- Balances ---
bs = wb["Balances"]
hdr = find_row(bs, "Account")
names = sorted(a["name"] for a in bal["accounts"])
by_name = {a["name"]: a for a in bal["accounts"]}
cols = [get_column_letter(5 + k) for k in range(NC)]
assert bs.cell(row=hdr, column=4).value.startswith("Start"), "start column moved"

for i, name in enumerate(names):
    r = hdr + 1 + i
    assert bs.cell(row=r, column=1).value == name, f"row {r} is not {name}"
    for k, c in enumerate(cols):
        check("Balances", f"{c}{r}", by_name[name]["balances"][k], f"balance {name} {MONTHS[k]}")

trow = find_row(bs, "TOTAL — net worth")
for k, c in enumerate(cols):
    check("Balances", f"{c}{trow}", bal["totals"][k], f"net worth {MONTHS[k]}")
check("Balances", f"D{trow}", bal["start_total"], "net worth at 1 Jan")
chg_row = find_row(bs, "Change since 1 Jan 2026")
check("Balances", f"{cols[-1]}{chg_row}", round(bal["totals"][-1] - bal["start_total"], 2),
      "change since 1 Jan")

# ------------------------------------------------------- Invested vs Returns --
iv = wb["Invested vs Returns"]
S = "Invested vs Returns"
inv_names = [a["name"] for a in inv["accounts"]]
inv_by = {a["name"]: a for a in inv["accounts"]}
n = len(inv_names)

for title, field in (("Capital invested", "capital"),
                     ("Cumulative return", "returns"),
                     ("Portfolio value", "value")):
    rows, tot = block_rows(iv, title, n)
    for i, r in enumerate(rows):
        name = iv.cell(row=r, column=1).value
        assert name in inv_by, f"{title} row {r}: unexpected {name!r}"
        for k, c in enumerate(cols):
            check(S, f"{c}{r}", inv_by[name][field][k], f"{field} {name} {MONTHS[k]}")
    for k, c in enumerate(cols):
        check(S, f"{c}{tot}", inv[field][k], f"portfolio {field} {MONTHS[k]}")
    if field == "value":          # must agree with the independently built balances
        for i, r in enumerate(rows):
            name = iv.cell(row=r, column=1).value
            for k, c in enumerate(cols):
                check(S, f"{c}{r}", by_name[name]["balances"][k],
                      f"value-vs-balance {name} {MONTHS[k]}")

for label, want in (("Capital invested", inv["capital"][-1]),
                    ("Portfolio value", inv["value"][-1]),
                    ("Return earned", inv["returns"][-1])):
    r = find_row(iv, label)
    # The summary labels repeat the block titles, so take the last occurrence.
    rows = [x for x in range(1, iv.max_row + 1) if iv.cell(row=x, column=1).value == label]
    check(S, f"E{rows[-1]}", want, f"summary {label}")

mrate = find_row(iv, "Monthly rate (IRR)")
ann = find_row(iv, "Annualised")
got_m, got_a = vals.get(f"{S.upper()}!E{mrate}"), vals.get(f"{S.upper()}!E{ann}")
print(f"\nIRR: monthly={got_m!r} annualised={got_a!r} "
      f"(python: {inv['irr_monthly']:.6f} / {inv['irr_annual']:.6f})")
for got, want, what in ((got_m, inv["irr_monthly"], "monthly IRR"),
                        (got_a, inv["irr_annual"], "annualised IRR")):
    try:
        if abs(float(got) - want) > 1e-6:
            raise ValueError
    except (TypeError, ValueError):
        print(f"MISMATCH {what}: {got!r} vs {want}")
        bad += 1

errs = [k for k, v in vals.items() if isinstance(v, str) and v.startswith("#")]
if errs:
    print(f"FORMULA ERRORS: {errs[:20]}")

total = len(names) * NC + NC + 2 + n * NC * 4 + NC * 3 + 3 + 2
print(f"\n{total - bad}/{total} checks pass; {len(errs)} formula errors; "
      f"{'OK' if not bad and not errs else 'FAILED'}")
