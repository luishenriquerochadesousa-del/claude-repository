# Finance dashboard — how it is built

Regenerates `../index.html` and `../Account Balances 2026.xlsx` from the figures
pulled out of the Notion Personal Finance Tracker on 9 August 2026.

## Why this exists

Notion's `Current Balance` and `Balance to Given Date` are formula properties, and
the API returns formula *references* rather than computed values. So the balances
are rebuilt from the underlying rows instead:

```
balance(account, month) = balance(account, previous month)
                        + income − expenses + transfers in − transfers out
```

starting from each account's `Starting Balance (as of January 1st 2026)`.

## The capital / return split

The tracker already distinguishes the two, in how transfers are logged:

| Row shape | Meaning |
|---|---|
| Transfer with **both** From and To set | capital moving between your own accounts |
| One-sided transfer on an **investment** account | a gain (inflow) or a loss (outflow) |
| One-sided transfer on a **cash** account | money entering/leaving from outside the tracker |

Every one-sided row touching the eight investment accounts is a `Portfolio Delta`,
a `CTT Aforro … Delta`, or a fund delta — checked against the full transfer list,
with no exceptions — so the classification needs no heuristics. Dividends and the
Trade Republic 2% cash interest are paid into Trade Republic *Account*, a cash
account, so they are reported separately rather than as portfolio return.

## Running it

```sh
python3 build.py        # → balances.json, flows.json  (+ prints the balance table)
python3 investments.py  # → investments.json           (+ prints the capital/return split)
python3 gen_html.py     # → ../index.html and balances.html (body-only fragment)
python3 make_xlsx.py    # → ../Account Balances 2026.xlsx
```

`build.py` needs no dependencies. `make_xlsx.py` needs `openpyxl`.

## Checks

Both scripts self-check rather than asserting correctness by eye:

- `build.py` proves the balance matrix against an independent identity — net-worth
  change must equal income − expenses + net external flows. It ties to the cent.
- `investments.py` proves the capital/return split reproduces all eight investment
  account balances, and refuses negative contributions or withdrawals.
- `verify_xlsx.py` / `verify_inv.py` evaluate the *written workbook's* formulas with
  the `formulas` package (`pip install formulas`) and compare every cell against the
  JSON. 130 + 283 cells, and the workbook's own `=IRR()` is checked against a
  bisection solve in Python.

The usual `recalc.py` (LibreOffice) route was unavailable — that build could not
load `.xlsx` at all — hence the independent evaluator.

## Updating after new Notion entries

The monthly aggregates in `build.py` (`INCOME`, `EXPENSES`, `TRANSFER_IN`,
`TRANSFER_OUT`) and the delta rows in `investments.py` (`GAINS`, `LOSSES`,
`INCOME_TO_CASH`) are the only inputs. Re-query Notion, update those tables, and
re-run the four scripts. Adding a month means appending to `MONTHS` in `build.py`
and to `labels` / `full` in `gen_html.py`.

## Data notes

1. **Revolut dips negative** — −€19.36 (Jan) and −€15.48 (May). Confirmed as real
   points where the account needed a top-up, so they are drawn as they happened.
2. **Two transfers are double-tagged** — *Investimentos - Trading 212* (29 Jun) and
   *Reembolso - Trading 212* (6 Jul) each name both Trading 212 and Robinhood.
   Attributed to Trading 212; they cancel out so no end balance moves. Still open.
3. **The 30 Jun brokerage label is fixed** — it read `Portfolio Delta - June 2026 (+)`
   on a €40.68 *outflow*, and has since been corrected to `(-)` in Notion. No figure
   changed: delta rows are counted by the direction they were entered, never by label.
4. **The brokerage's June delta was entered on 31 July**, which is why June looks
   flat and July carries two months of movement.
