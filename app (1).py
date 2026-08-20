"""
MacroTilt — Your Worldview, Allocated
---------------------------------------
Streamlit app for the IE NYC Python for Finance final project.

Pitch: the 60/40 stock-bond portfolio was built for a world without a
geopolitical risk premium. The S&P 500 sits near all-time highs, bond
yields are near multi-decade highs (which pushed bond prices down), and
"just buy the index" ignores that every macro headline -- a ceasefire, a
Fed pivot, a shipping-lane attack -- is already re-pricing markets in real
time. MacroTilt asks the investor eight geopolitical/macro questions on a
0-10 conviction scale and mechanically translates that worldview into a
bounded portfolio tilt across six liquid, real assets, benchmarked
honestly against equal-weight and a plain S&P 500 portfolio.

Investor: a self-directed investor who thinks in macro/geopolitical terms
("is the Middle East de-escalating? is the Fed done cutting? is a
recession coming?") and wants their portfolio to reflect that view without
hand-picking individual trades.

Decision the app answers: "Given my read on eight live macro questions,
what allocation across US equities / EM equities / Treasuries / gold /
energy equities / the dollar would reflect that view -- and how would it
have performed through real historical stress events?"

Layout note: this file is organized top-to-bottom as
  config/CSS -> data load -> sidebar inputs -> model run -> headline KPIs
  -> allocation -> recommendation -> detail tabs
so the reading order matches what a user sees on screen.
"""

import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import engine

st.set_page_config(
    page_title="MacroTilt — Your Worldview, Allocated",
    page_icon="\U0001F30D",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
# Streamlit's defaults are intentionally generic and pack elements tightly.
# This layer adds breathing room and a consistent visual identity, using the
# same validated categorical palette as the charts (engine.ASSET_COLORS).
# Selectors target stable data-testid hooks rather than internal class names.
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    /* ---------- Layout rhythm ---------- */
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px; }
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] { gap: 0.9rem; }

    /* ---------- Hero ---------- */
    .mt-hero {
        background: linear-gradient(120deg, #0d2b4e 0%, #14406e 55%, #1a5c8f 100%);
        border-radius: 16px;
        padding: 32px 38px 30px 38px;
        margin-bottom: 30px;
        color: #f5f6f7;
    }
    .mt-hero h1 { margin: 0 0 10px 0; font-size: 2.3rem; color: #ffffff; letter-spacing: -0.5px; }
    .mt-hero .mt-tagline {
        font-size: 1.12rem; font-weight: 600; color: #9fc6e8;
        margin-bottom: 14px; letter-spacing: 0.2px;
    }
    .mt-hero .mt-copy {
        font-size: 0.97rem; color: #d7e3ee; max-width: 820px; line-height: 1.65; margin: 0;
    }

    /* ---------- Section headers ---------- */
    .mt-section {
        font-size: 1.3rem; font-weight: 700; color: #0b0b0b;
        margin: 34px 0 4px 0; padding-bottom: 8px;
        border-bottom: 2px solid #e1e0d9;
    }
    .mt-section-sub { font-size: 0.9rem; color: #52514e; margin: 6px 0 18px 0; }

    /* ---------- KPI tiles ---------- */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e1e0d9;
        border-left: 4px solid #2a78d6;
        border-radius: 12px;
        padding: 18px 20px 14px 20px;
        box-shadow: 0 1px 3px rgba(11,11,11,0.06);
    }
    [data-testid="stMetricLabel"] {
        font-weight: 600; color: #52514e; font-size: 0.88rem; letter-spacing: 0.2px;
    }
    [data-testid="stMetricValue"] { font-size: 2rem; letter-spacing: -1px; }

    /* ---------- Recommendation card ---------- */
    .mt-reco {
        background: #f4f8fd;
        border: 1px solid #c8ddf3;
        border-left: 5px solid #2a78d6;
        border-radius: 12px;
        padding: 22px 26px;
        margin: 26px 0 10px 0;
        line-height: 1.7;
        font-size: 0.98rem;
        color: #0b0b0b;
    }
    .mt-reco .mt-reco-head {
        font-weight: 700; font-size: 1.05rem; color: #14406e;
        display: block; margin-bottom: 8px;
    }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] { background: #f7f7f5; }
    section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
    .mt-sb-title {
        font-size: 1.15rem; font-weight: 700; color: #0b0b0b; margin-bottom: 4px;
    }
    .mt-sb-group {
        font-size: 0.78rem; font-weight: 700; color: #14406e;
        text-transform: uppercase; letter-spacing: 0.9px;
        margin: 22px 0 2px 0; padding-bottom: 6px; border-bottom: 1px solid #dcdbd4;
    }
    .mt-badge {
        display: inline-block; background: #eaf2fc; color: #14406e;
        border-radius: 999px; padding: 5px 14px; font-size: 0.83rem; font-weight: 600;
        margin: 16px 0 6px 0; border: 1px solid #c8ddf3;
    }
    .mt-badge-neutral {
        background: #f0efec; color: #52514e; border-color: #dcdbd4;
    }
    /* Give each slider room so its value bubble never collides with the label */
    section[data-testid="stSidebar"] [data-testid="stSlider"] { padding-top: 6px; }
    section[data-testid="stSidebar"] [data-testid="stSlider"] label { font-size: 0.92rem; font-weight: 600; }
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        margin-top: -4px; margin-bottom: 12px;
    }
    section[data-testid="stSidebar"] [data-testid="stButton"] button {
        font-size: 0.82rem; padding: 6px 8px; line-height: 1.25; min-height: 46px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data loading (cached so we don't re-hit yfinance on every slider move)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60 * 60 * 12, show_spinner="Pulling market data (SPY, EEM, TLT, GLD, XLE, UUP)...")
def get_prices():
    return engine.load_prices()


st.markdown(
    """
    <div class="mt-hero">
        <h1>\U0001F30D MacroTilt</h1>
        <div class="mt-tagline">Your worldview, allocated.</div>
        <p class="mt-copy">The S&amp;P 500 is at all-time highs. Yields just hit multi-decade highs.
        60/40 was built for a world without a geopolitical risk premium — and it has no mechanism
        to express what you actually think about the Middle East, the Fed, or the next recession.
        Answer eight questions. We translate your read of the world into a real, bounded allocation.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    prices = get_prices()
except RuntimeError as e:
    st.error(f"Data load failed: {e}")
    st.stop()

returns = engine.daily_returns(prices)
retrieval_date = dt.date.today().isoformat()

# ---------------------------------------------------------------------------
# Preset scenarios
# ---------------------------------------------------------------------------
# Each preset is a coherent macro narrative -- a set of views a real investor
# might hold together -- plus a plain-English explanation of WHY each slider
# sits where it does. The explanation matters: a preset the user can't
# interrogate is just a magic button.
# ---------------------------------------------------------------------------

PRESET_SCENARIOS = {
    "Peace Breaks Out": {
        "icon": "\U0001F54A️",
        "summary": "Conflicts wind down, inflation cools, growth holds up.",
        "detail": (
            "The optimistic case. Middle East tensions resolve and supply lines normalize, "
            "so the geopolitical premium in energy deflates. With inflation cooling, the Fed "
            "has room to keep cutting, and growth avoids a hard stop — a supportive backdrop "
            "for risk assets and a mild headwind for the safe-haven dollar."
        ),
        "scores": {
            "mideast_deescalation": 9, "supply_disruption": 2, "trade_tensions": 3,
            "fed_cuts": 7, "dollar_strength": 3,
            "recession_risk": 2, "inflation_persistence": 2, "em_growth": 7,
        },
    },
    "Conflict Escalates": {
        "icon": "⚔️",
        "summary": "Geopolitical shock: energy spikes, capital runs to safety.",
        "detail": (
            "The tail-risk case. Regional conflict widens and shipping lanes are threatened, "
            "pushing crude and energy equities higher. Capital flees to the dollar and gold, "
            "trade routes get disrupted, and the growth outlook deteriorates as an energy price "
            "shock feeds through to the real economy."
        ),
        "scores": {
            "mideast_deescalation": 1, "supply_disruption": 9, "trade_tensions": 7,
            "fed_cuts": 6, "dollar_strength": 8,
            "recession_risk": 7, "inflation_persistence": 7, "em_growth": 2,
        },
    },
    "Sticky Inflation": {
        "icon": "\U0001F525",
        "summary": "Inflation won't die, the Fed can't cut, growth stalls.",
        "detail": (
            "The stagflation case — the hardest regime for a traditional 60/40. Inflation stays "
            "above target, so the Fed is boxed in and cuts fewer times than markets hope. Real "
            "assets like gold and energy hold value while both stocks and long bonds struggle, "
            "and a high-rate dollar stays firm."
        ),
        "scores": {
            "mideast_deescalation": 4, "supply_disruption": 6, "trade_tensions": 6,
            "fed_cuts": 1, "dollar_strength": 7,
            "recession_risk": 7, "inflation_persistence": 9, "em_growth": 3,
        },
    },
    "Soft Landing Rally": {
        "icon": "\U0001F680",
        "summary": "Inflation beaten without a recession — risk assets rip.",
        "detail": (
            "The goldilocks case. Inflation returns to target without breaking the labor market, "
            "so the Fed cuts into a still-growing economy. Risk appetite broadens out beyond US "
            "large caps into emerging markets, the safe-haven dollar bid fades, and defensive "
            "hedges underperform."
        ),
        "scores": {
            "mideast_deescalation": 7, "supply_disruption": 3, "trade_tensions": 3,
            "fed_cuts": 8, "dollar_strength": 2,
            "recession_risk": 1, "inflation_persistence": 2, "em_growth": 8,
        },
    },
    "Hard Landing": {
        "icon": "\U0001F9CA",
        "summary": "Recession hits, the Fed slashes rates, duration wins.",
        "detail": (
            "The deflationary bust case. Growth rolls over decisively, forcing the Fed into "
            "aggressive cuts — the single best environment for long-duration Treasuries. "
            "Earnings contract, demand destruction pulls energy down with it, and the dollar "
            "catches a defensive bid as global growth disappoints."
        ),
        "scores": {
            "mideast_deescalation": 5, "supply_disruption": 3, "trade_tensions": 5,
            "fed_cuts": 9, "dollar_strength": 7,
            "recession_risk": 9, "inflation_persistence": 2, "em_growth": 2,
        },
    },
    "Trade War": {
        "icon": "\U0001F6A2",
        "summary": "Tariffs escalate, supply chains fracture, EM takes the hit.",
        "detail": (
            "The fragmentation case. Tariff escalation between major economies hits "
            "export-driven emerging markets hardest while re-routing supply chains raises "
            "costs everywhere. Inflation is stickier than it would otherwise be, growth is "
            "slower, and the dollar benefits from both safe-haven demand and relative US insulation."
        ),
        "scores": {
            "mideast_deescalation": 5, "supply_disruption": 6, "trade_tensions": 9,
            "fed_cuts": 4, "dollar_strength": 8,
            "recession_risk": 6, "inflation_persistence": 7, "em_growth": 1,
        },
    },
    "Dollar Doubt": {
        "icon": "\U0001F4B1",
        "summary": "Confidence in the dollar erodes — gold and EM benefit.",
        "detail": (
            "The de-dollarization case. Fiscal concerns and reserve diversification weigh on the "
            "dollar. Gold is the primary beneficiary as a non-sovereign store of value, and a "
            "weaker dollar mechanically eases financial conditions for emerging markets, which "
            "borrow and trade heavily in USD."
        ),
        "scores": {
            "mideast_deescalation": 5, "supply_disruption": 5, "trade_tensions": 5,
            "fed_cuts": 7, "dollar_strength": 1,
            "recession_risk": 4, "inflation_persistence": 7, "em_growth": 7,
        },
    },
    "No View (Neutral)": {
        "icon": "\U0001F610",
        "summary": "Reset every slider — see the pure equilibrium baseline.",
        "detail": (
            "Every slider at 5 means you're expressing no opinion at all. The model falls back to "
            "the historical-equilibrium allocation, which is mathematically identical to equal "
            "weight. This is the control case, and it's checked as a hard identity in "
            "verify_calculations.py — if this ever stopped equalling equal weight, something in "
            "the model is broken."
        ),
        "scores": {cfg["key"]: 5 for cfg in engine.VIEWS_CONFIG},
    },
}

# ---------------------------------------------------------------------------
# Sidebar: the macro questionnaire
# ---------------------------------------------------------------------------

st.sidebar.markdown('<div class="mt-sb-title">\U0001F30D Your macro read</div>', unsafe_allow_html=True)
st.sidebar.caption(
    "Rate each question 0-10. **5 = neutral**, meaning no view — leave it there and it "
    "won't move your portfolio at all. These are the kinds of questions traded as contracts "
    "on prediction markets (Polymarket, Kalshi); MacroTilt doesn't pull their live odds — "
    "this is your call."
)

st.sidebar.markdown('<div class="mt-sb-group">Quick scenarios</div>', unsafe_allow_html=True)
st.sidebar.caption("One click sets all eight sliders to a coherent macro narrative.")

preset_cols = st.sidebar.columns(2)
for i, (name, preset) in enumerate(PRESET_SCENARIOS.items()):
    if preset_cols[i % 2].button(f"{preset['icon']} {name}", use_container_width=True, key=f"preset_{i}"):
        for k, v in preset["scores"].items():
            st.session_state[f"slider_{k}"] = v

with st.sidebar.expander("\U0001F4D6  What do these scenarios mean?"):
    for name, preset in PRESET_SCENARIOS.items():
        st.markdown(f"**{preset['icon']} {name}** — *{preset['summary']}*")
        st.caption(preset["detail"])
        st.markdown("")

# --- The sliders themselves, grouped by category ---------------------------
# Note: each slider passes its real label to st.slider rather than using a
# separate markdown heading with label_visibility="collapsed". That earlier
# approach caused Streamlit's value bubble to render on top of the custom
# heading text. Letting Streamlit own the label fixes the collision.

scores = {}
for category in engine.VIEW_CATEGORIES:
    st.sidebar.markdown(f'<div class="mt-sb-group">{category}</div>', unsafe_allow_html=True)
    for cfg in [c for c in engine.VIEWS_CONFIG if c["category"] == category]:
        slider_key = f"slider_{cfg['key']}"
        scores[cfg["key"]] = st.sidebar.slider(
            f"{cfg['icon']} {cfg['label']}",
            min_value=0,
            max_value=10,
            value=st.session_state.get(slider_key, 5),
            key=slider_key,
            help=f"{cfg['question']}\n\n**Why it matters:** {cfg['rationale']}",
        )
        st.sidebar.caption(f"{cfg['low_caption']} · {cfg['high_caption']}")

active_count = sum(1 for v in scores.values() if v != 5)
badge_class = "mt-badge" if active_count else "mt-badge mt-badge-neutral"
st.sidebar.markdown(
    f'<div class="{badge_class}">\U0001F4CD {active_count} of {len(scores)} views active</div>',
    unsafe_allow_html=True,
)

with st.sidebar.expander("⚙️  Advanced settings"):
    tau = st.slider(
        "View conviction weight (tau)",
        min_value=0.01, max_value=0.20, value=0.05, step=0.01,
        help="Standard Black-Litterman tuning parameter: how much weight the model gives "
             "your stated views versus the historical-equilibrium baseline. "
             "Higher = your views move the allocation more.",
    )
    st.caption(
        "Tau scales the uncertainty of the equilibrium prior. 0.05 is the conventional "
        "default in the Black-Litterman literature; we expose it so you can see how "
        "sensitive the allocation is to that choice."
    )

# ---------------------------------------------------------------------------
# Run the Black-Litterman pipeline
# ---------------------------------------------------------------------------

result = engine.run_macrotilt(returns, scores, tau=tau)
tilt_weights = result["weights"]
eq_weights = dict(result["w_eq"])
spy_only_weights = {t: (1.0 if t == "SPY" else 0.0) for t in returns.columns}

if result["solver_warning"]:
    st.warning(f"Optimizer warning: {result['solver_warning']}")

portfolios = {
    "MacroTilt (your view)": tilt_weights,
    "Equal-Weight": eq_weights,
    "100% SPY (the boring baseline)": spy_only_weights,
}

metric_rows = []
port_return_series = {}
for name, w in portfolios.items():
    pr = engine.portfolio_returns(returns, w)
    port_return_series[name] = pr
    metric_rows.append({
        "Portfolio": name,
        "Max Drawdown": engine.max_drawdown(pr),
        "Ann. Return": engine.annualized_return(pr),
        "Ann. Volatility": engine.annualized_vol(pr),
        "Sharpe": engine.sharpe_ratio(pr),
        "Tracking Error vs SPY": engine.tracking_error(pr, returns["SPY"]),
    })
metrics_df = pd.DataFrame(metric_rows).set_index("Portfolio")

tilt_row = metrics_df.loc["MacroTilt (your view)"]
eq_row = metrics_df.loc["Equal-Weight"]
spy_row = metrics_df.loc["100% SPY (the boring baseline)"]

# ---------------------------------------------------------------------------
# Headline KPIs
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="mt-section">Portfolio performance, backtested</div>'
    f'<div class="mt-section-sub">Real daily data from Yahoo Finance, '
    f'{prices.index.min().date()} to {prices.index.max().date()} '
    f'({len(returns):,} trading days). Deltas compare against the equal-weight baseline.</div>',
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Annualized Return", f"{tilt_row['Ann. Return']:.1%}",
    delta=f"{(tilt_row['Ann. Return'] - eq_row['Ann. Return']):.1%}",
)
col2.metric(
    "Annualized Volatility", f"{tilt_row['Ann. Volatility']:.1%}",
    delta=f"{(tilt_row['Ann. Volatility'] - eq_row['Ann. Volatility']):.1%}",
    delta_color="inverse",
)
col3.metric(
    "Max Drawdown", f"{tilt_row['Max Drawdown']:.1%}",
    delta=f"{(tilt_row['Max Drawdown'] - eq_row['Max Drawdown']):.1%}",
    delta_color="inverse",
)
col4.metric(
    "Sharpe Ratio", f"{tilt_row['Sharpe']:.2f}",
    delta=f"{(tilt_row['Sharpe'] - eq_row['Sharpe']):.2f}",
)

# ---------------------------------------------------------------------------
# Allocation
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="mt-section">Your MacroTilt allocation</div>'
    '<div class="mt-section-sub">Long-only, capped at 40% per asset so no single macro '
    'bet can dominate the portfolio.</div>',
    unsafe_allow_html=True,
)

alloc_col, view_col = st.columns([1.1, 1])

with alloc_col:
    labels = [engine.ASSET_LABELS[t] for t in tilt_weights]
    values = [tilt_weights[t] for t in tilt_weights]
    colors = [engine.ASSET_COLORS[t] for t in tilt_weights]
    pie = go.Figure(
        data=[go.Pie(
            labels=labels, values=values,
            marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
            hole=0.5, sort=False, textinfo="percent",
            hovertemplate="%{label}<br>%{percent}<extra></extra>",
        )]
    )
    pie.update_layout(
        height=400, margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="v", x=1.0, y=0.5, font=dict(size=12)),
        annotations=[dict(
            text=f"<b>{max(tilt_weights.values()):.0%}</b><br><span style='font-size:11px'>largest</span>",
            x=0.5, y=0.5, font_size=22, showarrow=False,
        )],
    )
    st.plotly_chart(pie, use_container_width=True)

with view_col:
    st.markdown("**Active views this run**")
    if result["active_views"]:
        for v in result["active_views"]:
            st.markdown(f"- {v}")
    else:
        st.info(
            "No active views — every slider is at neutral, so this is the pure "
            "historical-equilibrium allocation. Mathematically this equals equal weight, "
            "and that identity is verified in `verify_calculations.py`."
        )

    st.markdown("**Tilt vs. equal-weight**")
    tickers = list(returns.columns)
    deltas = [tilt_weights[t] - eq_weights[t] for t in tickers]
    delta_fig = go.Figure(go.Bar(
        x=deltas, y=[engine.ASSET_LABELS[t] for t in tickers], orientation="h",
        marker_color=[engine.ASSET_COLORS[t] for t in tickers],
        hovertemplate="%{y}<br>%{x:+.1%} vs equal weight<extra></extra>",
    ))
    delta_fig.add_vline(x=0, line_width=1, line_color="#898781")
    delta_fig.update_layout(
        height=300, xaxis_tickformat="+.0%", margin=dict(t=10, b=10, l=10, r=10),
        xaxis_title="Overweight / underweight vs equal weight",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    delta_fig.update_xaxes(gridcolor="#e1e0d9", zeroline=False)
    st.plotly_chart(delta_fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Narrative recommendation (rule-based, deterministic -- defensible in Q&A)
# ---------------------------------------------------------------------------

dd_vs_spy = spy_row["Max Drawdown"] - tilt_row["Max Drawdown"]
ret_vs_spy = tilt_row["Ann. Return"] - spy_row["Ann. Return"]
top_asset = max(tilt_weights, key=tilt_weights.get)
sorted_w = sorted(tilt_weights.items(), key=lambda kv: kv[1], reverse=True)
second_asset = sorted_w[1][0]

st.markdown(
    f"""
    <div class="mt-reco">
        <span class="mt-reco-head">Recommendation</span>
        Based on your macro read, MacroTilt's largest position is
        <b>{engine.ASSET_LABELS[top_asset]} at {tilt_weights[top_asset]:.0%}</b>,
        followed by <b>{engine.ASSET_LABELS[second_asset]} at {tilt_weights[second_asset]:.0%}</b>.
        Held over the full sample, this allocation would have posted a maximum drawdown of
        <b>{tilt_row['Max Drawdown']:.1%}</b> — {"shallower" if dd_vs_spy > 0 else "deeper"} than
        100% SPY's <b>{spy_row['Max Drawdown']:.1%}</b> by <b>{abs(dd_vs_spy):.1%}</b> —
        with an annualized return {"shortfall" if ret_vs_spy < 0 else "premium"} of
        <b>{abs(ret_vs_spy):.1%}</b> versus pure equities, at a Sharpe ratio of
        <b>{tilt_row['Sharpe']:.2f}</b> against SPY's <b>{spy_row['Sharpe']:.2f}</b>.
        <br><br>
        This is a mechanical translation of your stated views through historical data —
        not a return forecast, and not investment advice.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Detail tabs
# ---------------------------------------------------------------------------

tab_perf, tab_stress, tab_views, tab_assets, tab_corr, tab_method, tab_data = st.tabs([
    "\U0001F4C8 Performance",
    "\U0001F6A8 Stress Tests",
    "\U0001F3AF View Impact",
    "\U0001F50D Asset Detail",
    "\U0001F517 Correlations",
    "\U0001F9EE How It Works",
    "\U0001F4C4 Data & Limitations",
])

line_colors = {
    "MacroTilt (your view)": engine.ASSET_COLORS["SPY"],
    "Equal-Weight": engine.EQUAL_WEIGHT_COLOR,
    "100% SPY (the boring baseline)": engine.BENCHMARK_COLOR,
}

with tab_perf:
    growth_fig = go.Figure()
    for name, pr in port_return_series.items():
        curve = engine.cumulative_value(pr)
        growth_fig.add_trace(go.Scatter(
            x=curve.index, y=curve.values, mode="lines", name=name,
            line=dict(color=line_colors.get(name), width=2.5 if "MacroTilt" in name else 1.5),
            hovertemplate="%{x|%b %Y}<br>$%{y:.2f}<extra>" + name + "</extra>",
        ))
    growth_fig.update_layout(
        title="Growth of $1 invested (log scale)", yaxis_type="log", height=440,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
    )
    growth_fig.update_xaxes(gridcolor="#e1e0d9")
    growth_fig.update_yaxes(gridcolor="#e1e0d9")
    st.plotly_chart(growth_fig, use_container_width=True)

    dd_fig = go.Figure()
    for name, pr in port_return_series.items():
        dd = engine.drawdown_series(pr)
        dd_fig.add_trace(go.Scatter(
            x=dd.index, y=dd.values, mode="lines", name=name,
            line=dict(color=line_colors.get(name), width=2 if "MacroTilt" in name else 1.3),
            fill="tozeroy" if "MacroTilt" in name else None,
            hovertemplate="%{x|%b %Y}<br>%{y:.1%}<extra>" + name + "</extra>",
        ))
    for label, (start, end) in engine.STRESS_PERIODS.items():
        dd_fig.add_vrect(x0=start, x1=end, fillcolor="#898781", opacity=0.12, line_width=0)
    dd_fig.update_layout(
        title="Drawdown from prior peak — shaded bands are historical stress windows",
        yaxis_tickformat=".0%", height=420, plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    dd_fig.update_xaxes(gridcolor="#e1e0d9")
    dd_fig.update_yaxes(gridcolor="#e1e0d9")
    st.plotly_chart(dd_fig, use_container_width=True)

with tab_stress:
    st.markdown("**Maximum drawdown realized within each historical stress window.** "
                "These are real, dated market events — not simulated shocks.")
    stress_rows = []
    for name, w in portfolios.items():
        dd_by_period = engine.stress_period_drawdowns(returns, w)
        dd_by_period["Portfolio"] = name
        stress_rows.append(dd_by_period)
    stress_df = pd.DataFrame(stress_rows).set_index("Portfolio")
    st.dataframe(stress_df.style.format("{:.1%}"), use_container_width=True)

    stress_bar = go.Figure()
    for name in portfolios:
        stress_bar.add_trace(go.Bar(
            name=name,
            x=list(engine.STRESS_PERIODS.keys()),
            y=[stress_df.loc[name, p] for p in engine.STRESS_PERIODS],
            marker_color=line_colors.get(name),
            hovertemplate="%{x}<br>%{y:.1%}<extra>" + name + "</extra>",
        ))
    stress_bar.update_layout(
        barmode="group", height=400, yaxis_tickformat=".0%",
        title="Drawdown by stress event (less negative is better)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    stress_bar.update_yaxes(gridcolor="#e1e0d9")
    st.plotly_chart(stress_bar, use_container_width=True)

    st.markdown("**Full-period summary metrics**")
    fmt = {"Max Drawdown": "{:.1%}", "Ann. Return": "{:.1%}", "Ann. Volatility": "{:.1%}",
           "Sharpe": "{:.2f}", "Tracking Error vs SPY": "{:.1%}"}
    st.dataframe(metrics_df.style.format(fmt), use_container_width=True)

with tab_views:
    st.markdown(
        "**How your views moved expected returns.** The model starts from an equilibrium "
        "baseline (reverse-engineered from historical risk and correlations, with no opinion "
        "in it), then your slider positions shift those expectations. The gap between the two "
        "bars is the entire mechanism by which your worldview reaches the portfolio."
    )
    tickers = list(returns.columns)
    view_fig = go.Figure()
    view_fig.add_trace(go.Bar(
        name="Equilibrium baseline (no views)",
        x=[engine.ASSET_LABELS[t] for t in tickers],
        y=[result["pi"][t] for t in tickers],
        marker_color=engine.BENCHMARK_COLOR,
        hovertemplate="%{x}<br>%{y:.2%}<extra>Baseline</extra>",
    ))
    view_fig.add_trace(go.Bar(
        name="After your views",
        x=[engine.ASSET_LABELS[t] for t in tickers],
        y=[result["pi_post"][t] for t in tickers],
        marker_color=engine.ASSET_COLORS["SPY"],
        hovertemplate="%{x}<br>%{y:.2%}<extra>After views</extra>",
    ))
    view_fig.update_layout(
        barmode="group", height=420, yaxis_tickformat=".1%",
        yaxis_title="Expected excess return (annualized)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    view_fig.update_yaxes(gridcolor="#e1e0d9")
    st.plotly_chart(view_fig, use_container_width=True)

    if result["active_views"]:
        impact = pd.DataFrame({
            "Equilibrium baseline": result["pi"],
            "After your views": result["pi_post"],
        })
        impact["Change"] = impact["After your views"] - impact["Equilibrium baseline"]
        impact.index = [engine.ASSET_LABELS[t] for t in impact.index]
        st.dataframe(impact.style.format("{:.2%}"), use_container_width=True)
    else:
        st.info(
            "With no active views, the two bars are identical by construction — the posterior "
            "equals the prior exactly. Move a slider off 5 to see the mechanism work."
        )

with tab_assets:
    st.markdown(
        "**The raw inputs.** Every portfolio number in this app is derived from these six "
        "return streams. Shown here so the underlying data can be audited directly."
    )
    summary = engine.asset_summary_table(returns)
    st.dataframe(
        summary.style.format({
            "Ann. Return": "{:.1%}", "Ann. Volatility": "{:.1%}",
            "Sharpe": "{:.2f}", "Max Drawdown": "{:.1%}",
        }),
        use_container_width=True,
    )

    asset_growth = go.Figure()
    for t in returns.columns:
        curve = engine.cumulative_value(returns[t])
        asset_growth.add_trace(go.Scatter(
            x=curve.index, y=curve.values, mode="lines",
            name=engine.ASSET_LABELS[t], line=dict(color=engine.ASSET_COLORS[t], width=1.8),
            hovertemplate="%{x|%b %Y}<br>$%{y:.2f}<extra>" + t + "</extra>",
        ))
    asset_growth.update_layout(
        title="Growth of $1 by asset (log scale)", yaxis_type="log", height=440,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
    )
    asset_growth.update_xaxes(gridcolor="#e1e0d9")
    asset_growth.update_yaxes(gridcolor="#e1e0d9")
    st.plotly_chart(asset_growth, use_container_width=True)

    st.markdown("**Which slider moves which asset**")
    mapping = pd.DataFrame([
        {
            "View": f"{c['icon']} {c['label']}",
            "Category": c["category"],
            "Target asset": engine.ASSET_LABELS[c["asset"]],
            "A high score (10) means": ("higher" if c["direction"] > 0 else "lower")
                                        + " expected return",
            "Max tilt": f"{c['tilt_scale']:.0%}",
        }
        for c in engine.VIEWS_CONFIG
    ]).set_index("View")
    st.dataframe(mapping, use_container_width=True)

with tab_corr:
    corr = returns.corr()
    heat_fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=[engine.ASSET_LABELS[t] for t in corr.columns],
        y=[engine.ASSET_LABELS[t] for t in corr.index],
        zmin=-1, zmax=1, colorscale="RdBu", reversescale=True,
        text=corr.round(2).values, texttemplate="%{text}",
        hovertemplate="%{y} vs %{x}<br>correlation %{z:.2f}<extra></extra>",
    ))
    heat_fig.update_layout(title="Daily-return correlation matrix (full history)", height=480)
    st.plotly_chart(heat_fig, use_container_width=True)
    st.caption(
        "Diversification only helps if correlations stay low **during** a crisis, which is "
        "exactly when they tend to rise. The Stress Tests tab shows whether these "
        "relationships actually held when it mattered."
    )

with tab_method:
    st.markdown(f"""
#### The method: Black-Litterman, in plain English

**1. Start from a neutral baseline.** Take the equal-weight portfolio across all six assets
and ask: *what expected returns would make this portfolio mathematically optimal?* That
reverse-engineered answer becomes the "equilibrium" baseline — derived from historical risk
and correlations alone, with no opinion baked in.

**2. Layer in your views.** Each slider off neutral is a statement like *"I think energy
equities should earn a few percentage points more than that baseline."* The further from 5
you move, the more conviction the model assigns.

**3. Blend them mathematically.** The Black-Litterman formula combines baseline and views,
weighting each by its stated confidence. At exactly neutral on every slider, your views
contribute nothing and the blend equals the baseline exactly — an identity checked in
`verify_calculations.py`.

**4. Re-optimize.** The blended expected returns feed a standard long-only mean-variance
(max-Sharpe) optimizer, capped at 40% per asset so no single macro bet can dominate.

---

**Why Black-Litterman rather than a lookup table?** A hard-coded rule ("if escalation, then
35% energy") is easy to build but impossible to defend — *why 35% and not 30%?* has no
principled answer. Black-Litterman ties every tilt to the actual covariance structure of
these six assets, and it degrades gracefully: small view, small tilt; no view, no change.

**Live parameters:** view-conviction weight (tau) = **{tau:.2f}** ·
implied risk aversion (delta), estimated from the equal-weight portfolio's realized
Sharpe = **{result['delta']:.2f}** · assets = **{len(returns.columns)}** ·
views available = **{len(engine.VIEWS_CONFIG)}** · active right now = **{active_count}**
""")

with tab_data:
    st.markdown("#### Data provenance")
    st.markdown(f"""
| Field | Value |
|---|---|
| Source | Yahoo Finance, via the `yfinance` Python library |
| Instruments | {', '.join(f'{t}' for t in returns.columns)} |
| Field used | Daily adjusted close (`auto_adjust=True`) |
| Date range | {prices.index.min().date()} to {prices.index.max().date()} |
| Observations | {len(returns):,} daily returns |
| Retrieved | {retrieval_date} (live at app load, cached 12h) |
| Risk-free rate | {engine.RISK_FREE_RATE:.1%} annualized — a disclosed assumption, not fetched live |

**Why this start date:** UUP (the dollar-index fund) launched 2007-02-20 and is the youngest
fund in the universe, so it sets the floor on shared history. That still leaves the backtest
spanning the 2008 Global Financial Crisis, the 2020 COVID crash, the 2022 rate-hike bear
market, and the 2023 banking mini-crisis.
""")
    st.markdown("#### Design choices we made on purpose")
    st.markdown("""
- **XLE instead of USO/BNO for energy exposure.** Futures-based commodity ETFs suffer
  contango and roll-yield decay that distorts long-horizon buy-and-hold returns. XLE
  (equity-based) avoids that, at the cost of being an imperfect, equity-beta proxy for
  spot crude moves.
- **No live prediction-market API (Polymarket/Kalshi).** We considered wiring sliders to
  live market-implied odds but scoped it out: it adds an external dependency,
  authentication, and a second point of failure, for a feature that doesn't change the
  method's defensibility. The user's own conviction is a legitimate input either way.
- **Deterministic narrative, not an LLM.** The recommendation text is generated from
  computed numbers by fixed rules, so it can never assert something the model didn't
  actually produce.
""")
    st.markdown("#### Known limitations")
    st.markdown("""
- **Tilt magnitudes are a disclosed modeling assumption**, not derived from an event-study
  regression of historical geopolitical shocks. A further iteration could calibrate them
  from realized asset moves around dated historical events.
- **No transaction costs, taxes, or rebalancing frictions** are modeled; the backtest
  assumes frictionless rebalancing to target weights.
- **Historical covariance is assumed to approximate future covariance** — standard in
  mean-variance optimization, and still a real assumption that fails precisely in crises.
- **Long-only, static weights** for a single evaluation date — no shorting, no
  time-varying allocation.
- **Backtest, not forecast.** Every number here describes how this allocation *would have*
  behaved, which is not evidence of how it *will* behave.
""")
