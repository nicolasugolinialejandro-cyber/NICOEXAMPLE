# AI-Use Disclosure

**Group:** ___ (fill in) | **Members:** ___ (fill in)

## Tools used

- **Claude** (Anthropic), used in an agentic coding session (Cowork), for:
  - Drafting the full project — `engine.py` (data pipeline, Black-Litterman
    implementation, portfolio math), `app.py` (Streamlit UI), and
    `verify_calculations.py` (independent verification script).
  - Researching ETF inception dates via web search (UUP: Feb 20, 2007) to
    correctly bound the backtest period, rather than guessing it.
  - Applying an internal design-system methodology for the categorical
    chart palette (asset colors) to keep the allocation chart colorblind-
    accessible rather than picking colors by eye.
  - Running smoke tests against synthetic price data — including a
    mathematical identity check (neutral views must reduce exactly to
    equal weight) — that caught a real bug during development: the
    max-Sharpe optimizer was subtracting the risk-free rate a second time,
    which silently shifted the "neutral" allocation away from equal
    weight even though each individual function looked correct in
    isolation. That check is now part of `verify_calculations.py`.
  - Validating all eight preset scenarios programmatically: confirming
    each sets every slider key (a typo would silently no-op), that all
    resulting weight vectors sum to 1, respect the 40% position cap, stay
    non-negative, and produce eight distinct allocations.

*(Fill in any other tools any team member used — e.g. ChatGPT for a
specific deployment error, Perplexity for sourcing example prediction-
market question formats — with what each was used for.)*

## How the work was verified

- **Edge-case identity check:** with every geopolitical slider at neutral
  (5/10), the optimizer must recover equal weight to within 1e-6 — a real
  mathematical property of Black-Litterman reverse optimization, not a
  tautology. See `verify_calculations.py` Check 1.
- **Independent recomputation:** the Black-Litterman posterior-return
  formula is recomputed via a different numerical path (explicit matrix
  inverse vs. `np.linalg.solve`) and checked to agree to within 1e-8.
  See `verify_calculations.py` Check 2.
- **Manual spot-check:** *(team to fill in — e.g. "we independently priced
  SPY's known 2008 or 2020 max drawdown from an outside source like
  portfoliovisualizer.com or stockanalysis.com and confirmed it matched
  the app's reported figure to within rounding.")*
- **Team review:** every member read `engine.py` line by line and can
  explain, in their own words, what a Black-Litterman "view" is and why a
  slider left at neutral does nothing. *(Confirm this is true before
  submitting — you will be asked about it in the Q&A.)*

## Known limitations

- The AI-drafted Black-Litterman implementation is a standard,
  well-documented method, but the specific choices inside it — which
  assets get views, how large the tilt magnitudes are, the tau default,
  the 40% position cap — are modeling assumptions the team is responsible
  for defending, not values the AI "knew" were correct for this use case.
- The AI helped scope OUT a live prediction-market API integration
  (Polymarket/Kalshi) for time reasons; a future version could pull live
  market-implied odds as a default starting point for each slider.
- AI assistance accelerated the initial build and caught a real numerical
  bug via the verification checks described above, but the team is
  responsible for, and independently verified, the correctness of the
  financial logic — not just that the code runs.
