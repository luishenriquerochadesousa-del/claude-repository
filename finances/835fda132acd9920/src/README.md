# Finance dashboard — how it is built

Regenerates `../index.html` and `../Account Balances 2026.xlsx` from the figures
pulled out of the Notion Personal Finance Tracker on 28 October 2026
(January–October, 17 accounts).

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

Both models self-check rather than asserting correctness by eye:

- `build.py` proves the balance matrix against an independent identity — net-worth
  change must equal income − expenses + net external flows. It ties to the cent.
- `investments.py` proves the capital/return split reproduces all ten investment
  account balances, and refuses negative contributions or withdrawals.
- `verify_book.py` evaluates the *written workbook's* formulas with the `formulas`
  package (`pip install formulas`) and compares every cell against the JSON — 617
  checks, including the workbook's own `=IRR()` against a bisection solve in Python.
  It finds its cells by scanning sheet labels rather than hardcoding addresses, so
  adding a month or an account cannot silently point the checks at the wrong cells.
  (It replaces the earlier `verify_xlsx.py` / `verify_inv.py`, which did hardcode
  them and quietly mis-compared when the tracker grew past eight months.)

The usual `recalc.py` (LibreOffice) route was unavailable — that build could not
load `.xlsx` at all — hence the independent evaluator.

## Updating after new Notion entries

The monthly aggregates in `build.py` (`INCOME`, `EXPENSES`, `TRANSFER_IN`,
`TRANSFER_OUT`) and the delta rows in `investments.py` (`GAINS`, `LOSSES`,
`INCOME_TO_CASH`) are the only inputs. Re-query Notion, update those tables, and
re-run the four scripts. Adding a month means appending to `MONTHS` in `build.py`
and to `labels` / `full` in `gen_html.py`.

## Data notes

1. **October is still running**, and some month-end rows are already dated the 31st,
   so the last column is the month so far.
2. **No income recorded since July.** One row per month Jan–Jul (Prodigius, then
   Tesla), nothing for August or September, and an October row for Helsign AI GmbH
   with a **blank Amount**, read as zero. Part of the fall in net worth since August
   is therefore salary that has not been entered.
3. **Four accounts were emptied Aug–Oct** (CTT Série F, Revolut Wealth Build, Revolut
   Fundo Emergência, Trading 212 Account) and Conta Poupança sits at zero. Where an
   account earned something and was then fully withdrawn its net contribution goes
   negative — more came out than went in, the difference being the gains — so no
   return percentage is shown for it.
4. **One delta row is incomplete**: `T212 Brokerage - Portfolio Delta - October 2026 ()`
   has no amount and neither a From nor a To account. It contributes nothing.
5. **Small negatives**: Revolut −€19.36 (Jan) and −€15.48 (May), confirmed top-up gaps;
   Robinhood (Crypto) −€1.83 at end of August, which looks like the same.
6. **Dividends into Trade Republic Account**: the Jan–Jul monthly split is carried over
   from the 9 August extraction; August onward was re-read. It affects only that
   group's gain band and the "paid out as cash" figure, never a balance.
7. **Two accounts were added** in this period — Robinhood (Crypto) and Trading 212
   Brokerage — and Robinhood was renamed Robinhood (5% Yield).
