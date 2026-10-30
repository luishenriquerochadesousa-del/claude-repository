# Finance dashboard — how it is built

Regenerates `../index.html` and `../Account Balances 2026.xlsx` from the figures
pulled out of the Notion Personal Finance Tracker on 30 October 2026
(January–October, 18 accounts).

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
  checks (627 at the October 30 extraction), including the workbook's own `=IRR()` against a bisection solve in Python.
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

1. **October is read to the 30th**, including month-end rows already dated the 31st.
   No account carries an October portfolio-delta row except the brokerage cashback,
   so October's investment move is contributions, not a mark to market.
2. **Rows dated into November are held out** of `MONTHS` because the month has not
   started — a €1,099.00 Revolut expense and a €1,250.00 Revolut → Flat Deposit
   transfer (internal). See `NOVEMBER` in `build.py`. Net effect when November
   arrives: −€1,099.00.
3. **August and September have no income rows.** October's are in (€6,336.15 over two
   rows, Helsign AI), but the Jul→Oct gap is unrecorded pay, not only spending.
4. **Accounts that were emptied show a negative net contribution** — more came out
   than ever went in, the difference being the gains. CTT Série F, Revolut Wealth
   Build and Trading 212 Account sit at zero; Robinhood (Crypto) holds referral
   rewards rather than contributed money. No return percentage is shown for those.
5. **Two delta rows have had their Amount cleared** in Notion: `T212 Brokerage -
   Portfolio Delta` for August (inflow) and September (outflow). Both read as zero.
6. **Small negatives**: Revolut −€19.36 (Jan) and −€15.48 (May), confirmed top-up
   gaps; Robinhood (Crypto) −€1.83 at end of August, which looks like the same.
7. **Accounts added over time**: Robinhood (Crypto) and Trading 212 Brokerage in
   September, Flat Deposit (Cash) in October. Robinhood was renamed Robinhood
   (5% Yield). The Flat Deposit joins the Santander/PayPal/cash group.
8. **Dividends into Trade Republic Account**: derived as that account's one-sided
   inflows minus the refunds and adjustments paid into it, which are not returns.
