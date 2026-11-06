"""AI Workforce Investment Planner: the shared Phase 3 Streamlit dashboard.

Layout follows the user's decision path:
  headline insight -> where exposure concentrates (sector views)
  -> which occupations fall in the priority zone -> why they score high
  -> ranked table -> one-occupation drill-down -> shortlist.
All calculations come from analysis/backend.py; this file only owns layout,
formatting, controls, and session state.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analysis import backend

ROOT = Path(__file__).resolve().parent
CLEAN = ROOT / "data" / "cleaned"
OCCUPATIONS = CLEAN / "occupation_clean_merged.csv"
TASKS = CLEAN / "occupation_task_matches.csv"
COMPONENTS = ["exposure_component", "decline_component", "employment_component", "task_component"]
SORT_OPTIONS = {
    "Review priority score": "priority_score",
    "Observed AI exposure": "observed_exposure",
    "Average task penetration": "average_task_penetration",
    "Employment (2025)": "employment_2025",
    "Median annual wage": "median_annual_wage_2025",
    "Projected employment change": "employment_change_percent_2025_35",
}
SCORE_HELP = ("**Score = 100 × (0.40 × exposure + 0.30 × decline + 0.20 × employment + 0.10 × task)**, "
                    "where each component runs from 0 to 1:\n"
                    "- **Exposure** = observed AI exposure ÷ 0.38496, capped at 1.\n"
                    "- **Decline** = projected decline in percentage points ÷ 11.7, capped at 1. Only a "
                    "*negative* BLS projected change counts; growth or no change scores 0.\n"
                    "- **Employment** = log1p(employment_2025 / 1000) ÷ log1p(921220 / 1000), capped at 1 "
                    "(the log keeps very large occupations from dominating).\n"
                    "- **Task** = average matched-task penetration ÷ 0.3194842391304347, capped at 1.\n\n"
                    "Reference values are the 95th percentiles of the 755-occupation snapshot and stay fixed "
                    "when you filter or sort. A missing required input makes the score unavailable (sorted last). "
                    "Wages, openings and education are context, not score inputs.\n\n"
                    "The 40/30/20/10 weights are a **provisional team screening choice**. The score ranks "
                    "occupations for further review; it is **not** a job-loss probability or an estimate of "
                    "AI-caused job loss.")
SORT_HELP = (
    "**Review priority score**: 0–100 screening score (higher = review sooner).  \n"
    "**Observed AI exposure**: % of the occupation's tasks with observed AI use (Anthropic).  \n"
    "**Average task penetration**: mean AI penetration across matched O*NET tasks (%).  \n"
    "**Employment (2025)**: BLS employment in persons.  \n"
    "**Median annual wage**: BLS 2025 median, USD.  \n"
    "**Projected employment change**: BLS % change, 2025–35.  \n\n"
    "Direction sets high-to-low or low-to-high. Exact ties (including zeros) are ordered by SOC code "
    "ascending; missing values always sort last; ranks count rows from 1 in the current view."
)

# --- Colour roles (validated reference palette; see dataviz skill) ---------------------------
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
RED, GRAY, INK, MUTED = "#e34948", "#b4b2aa", "#0b0b0b", "#52514e"
COMPONENT_META = {  # key: (label, weight, colour) — stack order validated for colour-blind separation
    "exposure_component": ("AI use", 40, BLUE),
    "decline_component": ("Shrinking", 30, RED),
    "task_component": ("AI depth in tasks", 10, YELLOW),
    "employment_component": ("Number of workers", 20, AQUA),
}
SCORE_SCALE = ["#ecebe7", "#f9cdb6", "#f19a73", "#eb6834", "#b84a1d", "#7a2c0c"]     # priority score, light→dark
EDU_ORDER = [
    "No formal educational credential", "High school diploma or equivalent", "Some college, no degree",
    "Postsecondary nondegree award", "Associate's degree", "Bachelor's degree", "Master's degree",
    "Doctoral or professional degree",
]
FILTER_DEFAULTS = {
    "groups": [], "outlooks": [], "search": "",
    "emp_lower_on": False, "emp_upper_on": False, "exp_lower_on": False, "exp_upper_on": False,
    "emp_lower": 0, "emp_upper": 0, "exp_lower": 0.0, "exp_upper": 0.0, "size": "Any size",
}


@st.cache_data(show_spinner="Loading clean occupation data")
def load_data(occupation_path: str, occupation_mtime: int, task_path: str, task_mtime: int):
    # Modification times are deliberate cache keys; backend loads the fixed-score full dataset.
    return backend.load_clean_data(Path(occupation_path).parent)


# --- Formatters ---------------------------------------------------------------------------------
def missing(value) -> bool:
    return value is None or (not isinstance(value, (dict, list, pd.DataFrame)) and pd.isna(value))


def integer(value) -> str:
    return "Not reported" if missing(value) else f"{value:,.0f}"


def percentage(value, digits=2) -> str:
    return "Not reported" if missing(value) else f"{value * 100:.{digits}f}%"


def growth(value) -> str:
    return "Not reported" if missing(value) else f"{value:.1f}%"


def points(value) -> str:
    """Percentage-point formatter (audit B5-01)."""
    return "Not reported" if missing(value) else f"{value:.1f} pp"


def score(value) -> str:
    return "Not reported" if missing(value) else f"{value:.1f}"


def wage(value) -> str:
    return "Not reported" if missing(value) else f"${value:,.0f}"


def people(value) -> str:
    """Compact worker count for headlines: 21.8M, 153.6K."""
    if missing(value):
        return "—"
    if value >= 1e6:
        return f"{value / 1e6:.1f}M"
    if value >= 1e3:
        return f"{value / 1e3:.1f}K"
    return f"{value:,.0f}"


def text_value(value, *, category=False) -> str:
    if category and value == "None":
        return "None required"
    return "Not reported" if missing(value) or value == "" else str(value)


def short_group(name: str) -> str:
    return (str(name).replace(" occupations", "").replace(", and ", " & ").replace(" and ", " & ")
            .replace("Arts, design, entertainment, sports & media", "Arts, design & media")
            .replace("Building & grounds cleaning & maintenance", "Building & grounds")
            .replace("Office & administrative support", "Office & admin")
            .replace("Computer & mathematical", "Tech & math")
            .replace("Educational instruction & library", "Education")
            .replace("Business & financial operations", "Business & finance")
            .replace("Healthcare practitioners & technical", "Healthcare (doctors, nurses…)")
            .replace("Life, physical & social science", "Science")
            .replace("Transportation & material moving", "Transport & moving")
            .replace("Installation, maintenance & repair", "Repair & maintenance")
            .replace("Food preparation & serving related", "Food service")
            .replace("Farming, fishing & forestry", "Farming & fishing"))


EDU_SHORT = {
    "No formal educational credential": "No diploma needed", "High school diploma or equivalent": "High school",
    "Some college, no degree": "Some college", "Postsecondary nondegree award": "Certificate",
    "Associate's degree": "Associate's", "Bachelor's degree": "Bachelor's", "Master's degree": "Master's",
    "Doctoral or professional degree": "Doctorate / professional",
}


# --- State helpers ------------------------------------------------------------------------------
def reset_filters():
    """Write explicit defaults so mounted widgets visibly reset (audit B2-01)."""
    for key, value in FILTER_DEFAULTS.items():
        st.session_state[key] = value


OUTLOOK_LABELS = {"Growing": "Growing", "Stable": "Stable", "Declining": "Shrinking", "Unknown": "Unknown"}
PRESETS = {  # quick view -> (SOC group codes, outlooks); None = no restriction
    "All jobs": (None, None), "Office & admin": (["43"], None), "Tech": (["15"], None),
    "Sales": (["41"], None), "Healthcare": (["29", "31"], None), "Teaching": (["25"], None),
    "Only shrinking jobs": (None, ["Declining"]),
}


SIZES = {"Any size": (None, None), "Small (< 50K workers)": (None, 49_999),
         "Medium (50K–500K)": (50_000, 499_999), "Large (500K+)": (500_000, None)}


def apply_size():
    """The sketch's 'employment size' filter: fills the exact worker range under More filters."""
    low, high = SIZES[st.session_state.get("size", "Any size")]
    st.session_state["emp_lower_on"], st.session_state["emp_lower"] = low is not None, low or 0
    st.session_state["emp_upper_on"], st.session_state["emp_upper"] = high is not None, high or 0


def apply_preset():
    """Quick-view pills fill the normal filters, so users can keep tweaking from there."""
    choice = st.session_state.get("preset")
    if choice is None:
        return
    reset_filters()
    codes, outlooks = PRESETS[choice]
    labels = st.session_state.get("_group_labels", {})
    if codes:
        st.session_state["groups"] = [label for label, code in labels.items() if code in codes]
    if outlooks:
        st.session_state["outlooks"] = list(outlooks)
    st.session_state["preset"] = None


def style(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template="plotly_white", height=height, margin=dict(l=10, r=10, t=30, b=10),
        font=dict(color=INK, size=13, family="Inter, Source Sans Pro, sans-serif"),
        hoverlabel=dict(bgcolor="white", font_size=13), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
    )
    fig.update_xaxes(gridcolor="#ecebe7", zerolinecolor="#d8d6d0")
    fig.update_yaxes(gridcolor="#ecebe7", zerolinecolor="#d8d6d0")
    return fig


# --- Charts -------------------------------------------------------------------------------------
def priority_scatter(filtered: pd.DataFrame, threshold: float, hide_zero: bool, by_score: bool = True):
    """Bubble chart from the Phase 1 sketch. Returns the SOC of a clicked bubble, if any."""
    chart = backend.comparison_data(filtered)
    omitted = len(filtered) - len(chart)
    if hide_zero:
        chart = chart.loc[chart["observed_exposure"].gt(0)]
    notes = []
    if omitted:
        notes.append(f"{omitted} jobs with missing data are left out")
    if notes:
        st.caption(" · ".join(notes))
    if chart.empty:
        st.info("Nothing to show. Try showing jobs with no AI use, or change the filters.")
        return None
    chart = chart.copy()
    in_zone = chart["observed_exposure_percent"].ge(threshold) & chart["employment_change_percent_2025_35"].lt(0)
    chart["zone"] = in_zone.map({True: "High AI + shrinking", False: "Other jobs"})
    chart["wage_label"] = chart["median_annual_wage_2025"].map(wage)
    chart["employment_label"] = chart["employment_2025"].map(integer)
    for component in COMPONENTS:
        chart[component + "_label"] = chart[component].map(score)
    fig = px.scatter(
        chart, x="employment_change_percent_2025_35", y="observed_exposure_percent",
        size="employment_2025", size_max=38, hover_name="title",
        **({"color": "priority_score", "range_color": (0, 100), "color_continuous_scale": SCORE_SCALE}
           if by_score else
           {"color": "zone", "color_discrete_map": {"High AI + shrinking": ORANGE, "Other jobs": GRAY},
            "category_orders": {"zone": ["High AI + shrinking", "Other jobs"]}}),
        custom_data=["soc_code", "priority_score"] + [x + "_label" for x in COMPONENTS] +
                    ["observed_exposure_percent", "employment_change_percent_2025_35",
                     "employment_label", "wage_label"],
    )
    fig.update_traces(marker=dict(opacity=0.85, line=dict(color="white", width=1)), hovertemplate=(
        "<b>%{hovertext}</b><br>Priority score: %{customdata[1]:.0f} / 100<br>"
        "AI use: %{customdata[6]:.0f}% of tasks<br>Job change by 2035: %{customdata[7]:.1f}%<br>"
        "Workers: %{customdata[8]}<br>Typical pay: %{customdata[9]}<extra></extra>"))
    x_min = min(chart["employment_change_percent_2025_35"].min(), -1) - 3
    y_max = max(chart["observed_exposure_percent"].max(), threshold) + 8
    fig.add_shape(type="rect", x0=x_min, x1=0, y0=threshold, y1=y_max, layer="below",
                  fillcolor="rgba(235,104,52,0.08)", line=dict(width=0))
    fig.add_annotation(x=x_min, y=y_max, xanchor="left", yanchor="top", showarrow=False,
                       text="<b>High AI + shrinking</b>",
                       font=dict(color="#b84a1d", size=12), align="left")
    fig.add_vline(x=0, line_dash="dash", line_color=GRAY)
    fig.add_hline(y=threshold, line_dash="dot", line_color=GRAY)
    # Name the five highest-scoring occupations in a label column on the empty left side,
    # ordered by height so leader lines never cross.
    top = chart.nlargest(5, "priority_score").sort_values("observed_exposure_percent", ascending=False)
    slots = [y_max - 10 - i * (y_max - 10 - threshold) / 5 for i in range(len(top))]
    for slot, row in zip(slots, top.itertuples()):
        fig.add_annotation(x=row.employment_change_percent_2025_35, y=row.observed_exposure_percent,
                           ax=x_min + 1, ay=slot, axref="x", ayref="y", xanchor="left",
                           text=f"{textwrap.shorten(row.title, 30, placeholder='…')} · {row.priority_score:.0f}",
                           arrowcolor=MUTED, arrowwidth=1, arrowhead=0, standoff=4,
                           font=dict(size=11, color=INK), bgcolor="rgba(255,255,255,0.9)")
    fig.update_xaxes(title="← shrinking          Job change by 2035          growing →", ticksuffix="%")
    fig.update_yaxes(title="AI use (% of tasks)", ticksuffix="%", range=[-2, y_max])
    fig.update_traces(marker=dict(opacity=0.85))
    fig.update_layout(coloraxis_colorbar=dict(title="Priority<br>score", thickness=12, len=0.7))
    event = st.plotly_chart(style(fig, 540), width="stretch", key="bubble", on_select="rerun",
                            selection_mode="points", config={"displayModeBar": False})
    points = event.selection.points if event is not None else []
    return points[0]["customdata"][0] if points and points[0].get("customdata") else None



def component_bars(rows: pd.DataFrame, title_col: str = "title", height: int | None = None):
    """Stacked horizontal bars: how many of the 100 points each component contributes."""
    data = rows.dropna(subset=["priority_score"]).copy()
    if data.empty:
        st.info("No scored occupations to break down.")
        return
    data["label"] = data[title_col].map(lambda t: textwrap.shorten(str(t), 42, placeholder="…"))
    order = data["label"].tolist()[::-1]
    fig = go.Figure()
    for key, (label, weight, colour) in COMPONENT_META.items():
        contrib = data[key] * weight
        fig.add_trace(go.Bar(
            y=data["label"], x=contrib, name=f"{label} (up to {weight})", orientation="h",
            marker=dict(color=colour, line=dict(color="white", width=1.5)),
            customdata=pd.DataFrame({"raw": data[key], "title": data[title_col]}),
            hovertemplate="<b>%{customdata[1]}</b><br>" + label +
                          ": %{x:.1f} of " + str(weight) + " pts (component %{customdata[0]:.2f})<extra></extra>"))
    fig.add_trace(go.Scatter(
        y=data["label"], x=data["priority_score"] + 1.5, mode="text", text=data["priority_score"].map(score),
        textposition="middle right", textfont=dict(color=INK, size=12), showlegend=False, hoverinfo="skip"))
    fig.update_layout(barmode="stack", bargap=0.3)
    fig.update_layout(legend=dict(traceorder="normal"))
    fig.update_yaxes(categoryorder="array", categoryarray=order, title=None, showticklabels=len(data) > 1)
    fig.update_xaxes(title="Priority score (out of 100)", range=[0, 105])
    st.plotly_chart(style(fig, height or max(180, 32 * len(data) + 120)), width="stretch",
                    config={"displayModeBar": False})


def task_bars(top: pd.DataFrame):
    if top.empty:
        st.write("No scored tasks reported.")
        return
    data = top.copy()
    data["label"] = data["task"].map(lambda t: textwrap.shorten(t, 62, placeholder="…"))
    fig = go.Figure(go.Bar(
        x=data["penetration"] * 100, y=data["label"], orientation="h", width=0.55,
        marker=dict(color=BLUE, cornerradius=4),
        text=data["penetration"].map(lambda v: percentage(v, 0)), textposition="outside", cliponaxis=False,
        customdata=data[["task"]], hovertemplate="%{customdata[0]}<br>AI use: %{x:.1f}%<extra></extra>"))
    fig.update_yaxes(categoryorder="array", categoryarray=data["label"].tolist()[::-1], title=None)
    fig.update_xaxes(visible=False, range=[0, 112])
    fig = style(fig, 40 + 38 * len(data))
    fig.update_layout(margin=dict(l=10, r=30, t=5, b=5))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# --- Simple one-message charts ------------------------------------------------------------------
# Each chart answers ONE question. Its bold title is the answer (computed from the current
# filters); the grey line under it says how to read it. Colour meaning is fixed across the page:
# orange = priority zone (high AI use AND projected to shrink), blue = AI use, grey = everything else.
LIGHT_GRAY = "#d9d7d0"


def chart_title(title: str, note: str | None = None, help: str | None = None):
    """Bold one-line takeaway; optional very short note; details live in the ⓘ tooltip."""
    st.markdown(f"##### {title}", help=help)
    if note:
        st.caption(note)


def simple_bar(labels, values, *, colour, text, hover, x_title=None, horizontal=True, height=None,
               x_suffix=""):
    colours = colour if isinstance(colour, list) else [colour] * len(labels)
    if horizontal:
        fig = go.Figure(go.Bar(y=labels, x=values, orientation="h", marker=dict(color=colours, cornerradius=4),
                               text=text, textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK, size=12), hovertext=hover,
                               hovertemplate="%{hovertext}<extra></extra>"))
        fig.update_yaxes(categoryorder="array", categoryarray=list(labels)[::-1], title=None)
        fig.update_xaxes(title=x_title, showgrid=False, showticklabels=False, zeroline=False,
                         range=[0, max(values) * 1.28 if len(values) and max(values) > 0 else 1])
        height = height or max(220, 34 * len(labels) + 60)
    else:
        fig = go.Figure(go.Bar(x=labels, y=values, marker=dict(color=colours, cornerradius=4), text=text,
                               textposition="outside", cliponaxis=False, textfont=dict(color=INK, size=12),
                               hovertext=hover, hovertemplate="%{hovertext}<extra></extra>"))
        fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False, title=None,
                         range=[0, max(values) * 1.2 if len(values) and max(values) > 0 else 1])
        fig.update_xaxes(title=x_title, ticksuffix=x_suffix)
        height = height or 300
    fig = style(fig, height)
    fig.update_layout(showlegend=False, margin=dict(l=10, r=20, t=10, b=10))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def waffle(names, values, colours, hover):
    """10×10 grid; each square = 1% of the total. Largest-remainder rounding keeps exactly 100 squares."""
    total = sum(values)
    raw = [100 * v / total for v in values]
    cells = [int(r) for r in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - cells[i], reverse=True)[:100 - sum(cells)]:
        cells[i] += 1
    fig, idx = go.Figure(), 0
    for name, n, colour, tip in zip(names, cells, colours, hover):
        pos = list(range(idx, idx + n))
        idx += n
        fig.add_trace(go.Scatter(
            x=[p % 10 for p in pos], y=[9 - p // 10 for p in pos], mode="markers", name=name,
            marker=dict(symbol="square", size=21, color=colour, line=dict(width=0)),
            hovertext=[tip] * n, hovertemplate="%{hovertext}<extra></extra>"))
    fig.update_xaxes(visible=False, range=[-0.6, 9.6])
    fig.update_yaxes(visible=False, range=[-0.6, 9.6], scaleanchor="x")
    fig = style(fig, 300)
    fig.update_layout(legend=dict(orientation="v", x=1.02, y=0.5, yanchor="middle", xanchor="left",
                                  font=dict(size=13)), margin=dict(l=0, r=0, t=5, b=5))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def donut(names, values, colours, hover, centre: str):
    fig = go.Figure(go.Pie(
        labels=names, values=values, hole=0.62, sort=False, direction="clockwise",
        marker=dict(colors=colours, line=dict(color="white", width=2)),
        texttemplate="%{percent:.0%}", textposition="outside", textfont=dict(size=14, color=INK),
        hovertext=hover, hovertemplate="%{hovertext}<extra></extra>"))
    fig.add_annotation(text=centre, showarrow=False, font=dict(size=15, color=INK))
    fig = style(fig, 380)
    fig.update_layout(legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.05, yanchor="top",
                                  font=dict(size=13)), margin=dict(l=10, r=10, t=25, b=10))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def lollipop(labels, values, text, hover, colour=BLUE):
    fig = go.Figure()
    fig.add_trace(go.Bar(y=labels, x=values, orientation="h", width=0.12, marker=dict(color=colour),
                         hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(y=labels, x=values, mode="markers+text", text=text, textposition="middle right",
                             textfont=dict(color=INK, size=12), marker=dict(size=15, color=colour,
                             line=dict(color="white", width=2)), hovertext=hover,
                             hovertemplate="%{hovertext}<extra></extra>", showlegend=False, cliponaxis=False))
    fig.update_yaxes(categoryorder="array", categoryarray=list(labels)[::-1], title=None)
    fig.update_xaxes(visible=False, range=[0, max(values) * 1.22])
    fig = style(fig, max(240, 34 * len(labels) + 50))
    fig.update_layout(margin=dict(l=10, r=10, t=5, b=5))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def block_map(labels, values, text, hover, colour=ORANGE):
    fig = go.Figure(go.Treemap(
        labels=labels, parents=[""] * len(labels), values=values, customdata=list(zip(text, hover)),
        texttemplate="<b>%{label}</b><br>%{customdata[0]}", hovertemplate="%{customdata[1]}<extra></extra>",
        marker=dict(colors=[colour] * len(labels), line=dict(color="white", width=3)),
        textfont=dict(color="white", size=14), sort=True, tiling=dict(pad=2)))
    fig = style(fig, 330)
    fig.update_layout(margin=dict(l=0, r=0, t=5, b=5))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def zone_mask(frame: pd.DataFrame, threshold: float) -> pd.Series:
    return frame["observed_exposure"].ge(threshold / 100) & frame["employment_change_percent_2025_35"].lt(0)


def exposure_bands(filtered: pd.DataFrame):
    data = filtered.dropna(subset=["observed_exposure"])
    if data.empty:
        chart_title("No jobs match your filters")
        return
    exp = data["observed_exposure"]
    bands = [("None yet (0%)", exp.eq(0)), ("Under 10%", exp.gt(0) & exp.lt(.10)),
             ("10–20%", exp.ge(.10) & exp.lt(.20)), ("20–40%", exp.ge(.20) & exp.lt(.40)),
             ("40% or more", exp.ge(.40))]
    counts = [int(m.sum()) for _, m in bands]
    n, zero = len(data), counts[0]
    chart_title(f"{zero / n:.0%} of jobs show no AI use yet", None,
                help="Each bar counts jobs by how many of their everyday tasks people already do with AI "
                     "(source: Anthropic Economic Index).")
    labels = [b for b, _ in bands]
    simple_bar(labels, counts, colour=["#cde2fb", "#9ec5f4", "#6da7ec", "#2a78d6", "#184f95"],
               text=[f"{c}" for c in counts], horizontal=False, x_title="AI use (% of tasks)",
               hover=[f"{l}: {c} jobs ({c / n:.0%})" for l, c in zip(labels, counts)])


def worker_split(filtered: pd.DataFrame, threshold: float):
    data = filtered.dropna(subset=["employment_2025", "observed_exposure", "employment_change_percent_2025_35"])
    if data.empty:
        chart_title("No jobs match your filters")
        return
    high = data["observed_exposure"].ge(threshold / 100)
    shrink = data["employment_change_percent_2025_35"].lt(0)
    groups = [("High AI use + shrinking", high & shrink, ORANGE), ("High AI use + growing", high & ~shrink, BLUE),
              ("Low AI use + shrinking", ~high & shrink, GRAY), ("Low AI use + growing", ~high & ~shrink, LIGHT_GRAY)]
    total = data["employment_2025"].sum()
    values = [data.loc[m, "employment_2025"].sum() for _, m, _ in groups]
    zone = values[0]
    if zone == 0:
        chart_title("No workers in high-AI, shrinking jobs here", "Try a lower “High AI use” setting.")
    else:
        chart_title(f"{people(zone)} workers are in high-AI, shrinking jobs",
                    "1 square = 1% of workers",
                    help=f"High AI use = AI is used in at least {threshold:.0f}% of the job's tasks. Shrinking = "
                         "the government (BLS) expects fewer of these jobs in 2035 than today.")
    waffle([f"{g} · {people(v)}" for (g, _, _), v in zip(groups, values)], values,
           [c for _, _, c in groups],
           [f"{g}: {integer(v)} workers ({v / total:.0%}) in {int(m.sum())} jobs" for (g, m, _), v in
            zip(groups, values)])


def sector_share(filtered: pd.DataFrame, threshold: float):
    data = filtered.dropna(subset=["employment_2025", "observed_exposure"])
    if data.empty:
        chart_title("No jobs match your filters")
        return
    data = data.assign(group=data["occupation_group_name"].map(short_group),
                       high_emp=data["employment_2025"].where(data["observed_exposure"].ge(threshold / 100), 0))
    agg = data.groupby("group", as_index=False).agg(total=("employment_2025", "sum"), high=("high_emp", "sum"))
    agg["share"] = agg["high"] / agg["total"]
    agg = agg.loc[agg["share"].gt(0)].sort_values(["share", "group"], ascending=[False, True]).head(10)
    if agg.empty:
        chart_title("No high-AI jobs here", "Try a lower “High AI use” setting.")
        return
    top = agg.iloc[0]
    chart_title(f"{top['group']} uses AI the most" if len(agg) > 1 else
                f"{top['share']:.0%} of {top['group']} workers are in high-AI jobs",
                "% of workers in high-AI jobs",
                help=f"High-AI job = AI is used in at least {threshold:.0f}% of its tasks. Top 10 industries.")
    lollipop(agg["group"].tolist(), agg["share"].tolist(),
               text=[f"{s:.0%}" for s in agg["share"]],
               hover=[f"{g}: {people(h)} of {people(t)} workers" for g, h, t in
                      zip(agg["group"], agg["high"], agg["total"])])


def sector_zone_workers(filtered: pd.DataFrame, threshold: float):
    zone = filtered.loc[zone_mask(filtered, threshold)].dropna(subset=["employment_2025"])
    if zone.empty:
        chart_title("No high-AI, shrinking jobs here", "Try a lower “High AI use” setting.")
        return
    agg = (zone.assign(group=zone["occupation_group_name"].map(short_group))
           .groupby("group", as_index=False).agg(workers=("employment_2025", "sum"), jobs=("soc_code", "size"))
           .sort_values(["workers", "group"], ascending=[False, True]))
    total, top = agg["workers"].sum(), agg.iloc[0]
    chart_title(f"{top['workers'] / total:.0%} of high-AI, shrinking jobs are in {top['group']}",
                None)
    block_map(agg["group"].tolist(), agg["workers"].tolist(),
              text=[f"{people(w)} · {w / total:.0%}" for w in agg["workers"]],
              hover=[f"{g}: {integer(w)} workers in {j} jobs" for g, w, j in
                     zip(agg["group"], agg["workers"], agg["jobs"])])


def education_zone(filtered: pd.DataFrame, threshold: float):
    zone = filtered.loc[zone_mask(filtered, threshold)].dropna(subset=["employment_2025"])
    if zone.empty:
        chart_title("No high-AI, shrinking jobs here", "Try a lower “High AI use” setting.")
        return
    zone = zone.assign(education=zone["typical_education"].fillna("Not reported"))
    agg = zone.groupby("education", as_index=False).agg(workers=("employment_2025", "sum"),
                                                        jobs=("soc_code", "size"))
    order = [e for e in EDU_ORDER if e in set(agg["education"])] + sorted(set(agg["education"]) - set(EDU_ORDER))
    agg = agg.set_index("education").loc[order].reset_index()
    total = agg["workers"].sum()
    low = agg.loc[agg["education"].isin(EDU_ORDER[:2]), "workers"].sum()
    chart_title(f"{low / total:.0%} need a high-school diploma or less", None,
                help="Typical education needed to enter each job (BLS). It describes the job, not each worker.")
    buckets = {"No diploma needed": EDU_ORDER[:1], "High school": EDU_ORDER[1:2],
               "Some college / certificate / associate's": EDU_ORDER[2:5], "Bachelor's or higher": EDU_ORDER[5:]}
    names, vals, tips = [], [], []
    for name, members in list(buckets.items()) + [("Not reported", ["Not reported"])]:
        part = agg.loc[agg["education"].isin(members)]
        if part["workers"].sum() > 0:
            names.append(name)
            vals.append(part["workers"].sum())
            tips.append(f"{name}: {integer(part['workers'].sum())} workers in {int(part['jobs'].sum())} jobs")
    ramp = ["#a8431b", "#eb6834", "#f4a37d", "#fbd5c2"]  # darkest = the headline slices (≤ high school)
    donut(names, vals, ramp[:len(names) - ("Not reported" in names)] + ([GRAY] if "Not reported" in names else []),
          tips, centre=f"<b>{people(total)}</b><br>workers")


def wage_bands(filtered: pd.DataFrame, threshold: float):
    zone = filtered.loc[zone_mask(filtered, threshold)].dropna(subset=["employment_2025"])
    if zone.empty:
        chart_title("No high-AI, shrinking jobs here", "Try a lower “High AI use” setting.")
        return
    wage_col = zone["median_annual_wage_2025"]
    bands = [("Under $40K", wage_col.lt(40000)), ("$40K–50K", wage_col.ge(40000) & wage_col.lt(50000)),
             ("$50K–60K", wage_col.ge(50000) & wage_col.lt(60000)),
             ("$60K–80K", wage_col.ge(60000) & wage_col.lt(80000)), ("$80K or more", wage_col.ge(80000)),
             ("Not reported", wage_col.isna())]
    workers = [zone.loc[m, "employment_2025"].sum() for _, m in bands]
    labels = [b for b, _ in bands]
    if workers[-1] == 0:
        labels, workers, bands = labels[:-1], workers[:-1], bands[:-1]
    total = sum(workers)
    under50 = workers[0] + workers[1]
    chart_title(f"{under50 / total:.0%} earn under $50K a year", None,
                help="Uses each job's BLS median annual wage, not each person's own pay.")
    # Bars that make up the headline number are full orange; the rest are a light tint.
    simple_bar(labels, [w / 1e6 for w in workers], horizontal=False,
               colour=[ORANGE if i < 2 else "#f9cdb6" for i in range(len(labels))],
               text=[people(w) for w in workers], x_title=None,
               hover=[f"{l}: {integer(w)} workers in {int(m.sum())} occupations"
                      for l, w, (_, m) in zip(labels, workers, bands)])


# --- Tables & details ---------------------------------------------------------------------------
def display_table(rows: pd.DataFrame, height: int | None = None, select_key: str | None = None):
    """Ranked table. With select_key, clicking a row returns that row's SOC code."""
    cols = ["display_rank", "title", "soc_code", "priority_score", "observed_exposure",
            "average_task_penetration", "employment_2025", "median_annual_wage_2025",
            "employment_change_percent_2025_35", "task_match_rate"]
    table = rows[cols].copy()
    for field in ("observed_exposure", "average_task_penetration", "task_match_rate"):
        table[field] = table[field] * 100
    table["median_annual_wage_2025"] = table["median_annual_wage_2025"].map(wage)  # keeps "Not reported"
    config = {
        "display_rank": st.column_config.NumberColumn("Rank", format="%d", width="small"),
        "title": st.column_config.TextColumn("Job", width="medium"),
        "soc_code": st.column_config.TextColumn("SOC"),
        "priority_score": st.column_config.ProgressColumn("Priority score", format="%.1f", min_value=0,
                                                          max_value=100),
        "observed_exposure": st.column_config.ProgressColumn("AI use", format="%.2f%%",
                                                             min_value=0, max_value=100),
        "average_task_penetration": st.column_config.NumberColumn("AI depth in tasks", format="%.2f%%"),
        "employment_2025": st.column_config.NumberColumn("Workers", format="localized"),
        "median_annual_wage_2025": st.column_config.TextColumn("Median annual wage"),
        "employment_change_percent_2025_35": st.column_config.NumberColumn("Job change by 2035",
                                                                           format="%.1f%%"),
        "task_match_rate": st.column_config.NumberColumn("Task coverage", format="%.2f%%"),
    }
    kwargs = {"height": height} if height else {}
    if select_key is None:
        st.dataframe(table, hide_index=True, width="stretch", column_config=config, **kwargs)
        return None
    event = st.dataframe(table, hide_index=True, width="stretch", column_config=config, key=select_key,
                         on_select="rerun", selection_mode="single-row", **kwargs)
    picked = event.selection.rows if event is not None else []
    return rows["soc_code"].iloc[picked[0]] if picked else None


TRAINING_SHORT = {
    "Short-term on-the-job training": "Short-term", "Moderate-term on-the-job training": "Moderate-term",
    "Long-term on-the-job training": "Long-term", "Apprenticeship": "Apprenticeship",
    "Internship/residency": "Internship / residency",
}


def first_sentence(text: str) -> str:
    text = text_value(text)
    end = text.find(". ")
    return text if end == -1 else text[:end + 1]


def details(occupations: pd.DataFrame, tasks: pd.DataFrame, soc: str):
    """Compact job card: who it is, 5 numbers, score parts, top tasks, training needs."""
    record = backend.occupation_details(occupations, tasks, soc)
    item = record["occupation"]
    outlook = OUTLOOK_LABELS.get(item.get("labor_market_outlook"), text_value(item.get("labor_market_outlook")))
    st.markdown(
        f"<div class='job-head'><div class='eyebrow'>{short_group(item.get('occupation_group_name'))} · "
        f"{outlook}</div><h3>{item['title']}</h3>"
        f"<p>{first_sentence(item.get('occupation_description'))}</p></div>", unsafe_allow_html=True)

    change = item.get("employment_change_percent_2025_35")
    info_cards([
        ("Priority score", "—" if missing(item.get("priority_score")) else f"{item['priority_score']:.1f} / 100"),
        ("AI use", percentage(item.get("observed_exposure"), 0)),
        ("Jobs by 2035", "—" if missing(change) else f"{change:+.1f}%"),
        ("Workers", people(item.get("employment_2025"))),
        ("Median pay", wage(item.get("median_annual_wage_2025"))),
    ], big=True)

    component_bars(pd.DataFrame([item]), height=150)

    st.markdown("**Where AI is used most**")
    task_bars(record["top_tasks"])

    edu = text_value(item.get("typical_education"))
    training = text_value(item.get("on_the_job_training"), category=True)
    st.markdown(
        "<div class='chips'><span>🎓 " + EDU_SHORT.get(edu, edu) + "</span><span>🛠 Training: "
        + TRAINING_SHORT.get(training, training) + "</span><span>📈 "
        + integer(item.get("annual_openings_2025_35")) + " openings / year</span></div>", unsafe_allow_html=True)

    with st.expander("All numbers"):
        rows = {
            "Employment (2025 persons)": integer(item.get("employment_2025")),
            "Projected change (2025–35)": growth(item.get("employment_change_percent_2025_35")),
            "Projected decline (percentage points)": points(item.get("projected_decline_percent_points")),
            "Median annual wage": wage(item.get("median_annual_wage_2025")),
            "Annual openings (persons)": integer(item.get("annual_openings_2025_35")),
            "Average task penetration": percentage(item.get("average_task_penetration")),
            "Typical education": text_value(item.get("typical_education")),
            "Related work experience": text_value(item.get("related_work_experience"), category=True),
            "On-the-job training": text_value(item.get("on_the_job_training"), category=True),
            "Matched / total tasks": f"{integer(item.get('matched_task_count'))} / "
                                    f"{integer(item.get('total_task_count'))}",
            "Task match rate": percentage(item.get("task_match_rate")),
            "Description source (O*NET)": text_value(item.get("description_source_onet_code")),
        }
        st.dataframe(pd.DataFrame(rows.items(), columns=["Measure", "Value"]), hide_index=True, width="stretch")


# --- Look & feel --------------------------------------------------------------------------------
NAVY = "#13263f"
CSS = """
<style>
.block-container {padding-top: 3.2rem; max-width: 1240px;}
/* hero */
.hero {background: radial-gradient(120% 140% at 100% 0%, #24456e 0%, #13263f 55%, #0d1b2c 100%);
       border-radius: 22px; padding: 30px 36px 26px; color: #fff; margin-bottom: 18px; position: relative;
       overflow: hidden;}
.hero:after {content: ""; position: absolute; right: -60px; top: -60px; width: 240px; height: 240px;
       border-radius: 50%; background: radial-gradient(circle, rgba(235,104,52,.55), rgba(235,104,52,0) 70%);}
.hero .tag {display: inline-block; font-size: .78rem; letter-spacing: .12em; text-transform: uppercase;
       color: #f9cdb6; background: rgba(235,104,52,.18); border: 1px solid rgba(235,104,52,.45);
       padding: 3px 10px; border-radius: 999px; margin-bottom: 10px;}
.hero h1 {color: #fff; font-size: 2.3rem; margin: 0 0 6px; padding: 0; line-height: 1.15;}
.hero p {color: #c9d6e6; font-size: 1.05rem; margin: 0 0 18px;}
.steps {display: flex; gap: 10px; flex-wrap: wrap;}
.step {background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.14); border-radius: 12px;
       padding: 8px 14px; font-size: .92rem; color: #e8eef6;}
.step b {color: #eb6834; margin-right: 6px;}
/* section heads */
.sec {margin: 26px 0 6px;}
.sec .eyebrow, .job-head .eyebrow {font-size: .74rem; letter-spacing: .14em; text-transform: uppercase;
       color: #eb6834; font-weight: 700;}
.sec h2 {font-size: 1.55rem; margin: 2px 0 0; padding: 0; color: #13263f;}
/* cards */
div[data-testid="stMetric"] {background: #fff; border-radius: 16px !important;
       box-shadow: 0 1px 2px rgba(19,38,63,.06), 0 6px 18px rgba(19,38,63,.05);}
div[data-testid="stMetricValue"] {color: #13263f; font-weight: 700;}
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div > div.stPlotlyChart),
.card-like {background: #fff; border-radius: 18px;}
.cards {display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin: 6px 0 14px;}
.cards div {background: #fff; border: 1px solid #ecebe7; border-radius: 14px; padding: 12px 14px;}
.cards span {display: block; font-size: .78rem; color: #6b6a65;}
.cards b {display: block; font-size: 1.02rem; color: #13263f; margin-top: 3px;}
.cards.big b {font-size: 1.45rem; font-weight: 700;}
.chips {display: flex; gap: 8px; flex-wrap: wrap; margin: 4px 0 12px;}
.chips span {background: #fff; border: 1px solid #ecebe7; border-radius: 999px; padding: 6px 14px;
       font-size: .9rem; color: #13263f;}
.job-head {background: #fff; border: 1px solid #ecebe7; border-left: 5px solid #eb6834; border-radius: 16px;
       padding: 16px 20px; margin: 8px 0 14px;}
.job-head h3 {margin: 4px 0 6px; padding: 0; color: #13263f;}
.job-head p {margin: 0; color: #3d3c39; font-size: .95rem;}
.next {background: #fff4ee; border: 1px dashed #eb6834; border-radius: 14px; padding: 12px 16px;
       color: #7a2c0c; margin-top: 18px;}
/* step navigator */
div[data-testid="stButtonGroup"] button {border-radius: 999px !important;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero():
    st.markdown(
        "<div class='hero'><span class='tag'>Workforce planning · AI transition</span>"
        "<h1>AI Workforce Investment Planner</h1>"
        "<p>Which U.S. jobs should get AI-transition training first?</p>"
        "<div class='steps'><div class='step'>Anthropic Economic Index · O*NET · BLS 2025–35</div></div>"
        "</div>", unsafe_allow_html=True)


def section(title: str):
    st.markdown(f"<div class='sec'><h2>{title}</h2></div>", unsafe_allow_html=True)


def info_cards(items, big: bool = False):
    cells = "".join(f"<div><span>{label}</span><b>{value}</b></div>" for label, value in items)
    st.markdown(f"<div class='cards{' big' if big else ''}'>{cells}</div>", unsafe_allow_html=True)


def next_step(label: str, target: str):
    st.write("")
    st.button(label, on_click=go_to, args=(target,), type="primary", key=f"next_{target}")


STEPS = {"explore": "① Explore the landscape", "prioritize": "② Prioritize jobs",
         "shortlist": "③ Build your shortlist"}
# Widgets that only exist on one step keep their value when another step is shown.
STICKY = ["detail_soc", "hide_zero", "n_top", "sort_label", "direction"]


def go_to(target: str):
    st.session_state["step"] = target


def open_job(soc: str | None, source: str):
    """Open a job in the details panel when a bubble / table row is newly clicked."""
    last = st.session_state.get(f"_last_{source}")
    if soc and soc != last:
        st.session_state["detail_soc"] = soc
    st.session_state[f"_last_{source}"] = soc


# --- Page ---------------------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="AI Workforce Investment Planner", layout="wide", page_icon="📊")
    inject_css()
    for key in STICKY:  # re-assigning keeps a widget's value while its step is hidden
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]
    hero()
    if not OCCUPATIONS.is_file() or not TASKS.is_file():
        st.error("Required clean occupation/task CSVs are missing from data/cleaned/.")
        st.stop()
    all_rows, tasks = load_data(str(OCCUPATIONS), OCCUPATIONS.stat().st_mtime_ns,
                                str(TASKS), TASKS.stat().st_mtime_ns)
    valid_codes = set(all_rows["soc_code"])
    saved = list(dict.fromkeys(st.session_state.get("saved_socs", [])))
    removed = sorted(set(saved) - valid_codes)
    if removed:
        st.warning("Saved SOCs no longer available: " + ", ".join(removed))
    st.session_state.saved_socs = [soc for soc in saved if soc in valid_codes]
    if st.session_state.get("detail_soc") not in valid_codes:
        st.session_state.detail_soc = None
    for key, value in FILTER_DEFAULTS.items():
        st.session_state.setdefault(key, value)

    group_names = (all_rows[["occupation_group_code", "occupation_group_name"]]
                   .drop_duplicates().sort_values("occupation_group_code"))
    groups = {f"{row.occupation_group_code} · {row.occupation_group_name}": row.occupation_group_code
              for row in group_names.itertuples(index=False)}
    st.session_state["_group_labels"] = groups

    # --- Filter bar: same filters drive every step (the sketch's "choose the workforce segment") --
    # One filter bar for everything: quick views, the main filters, and exact ranges in a pop-over.
    with st.container(border=True):
        q1, q2, q3 = st.columns([8, 1.6, 1.2], vertical_alignment="center")
        q1.pills("Quick views", list(PRESETS), key="preset", on_change=apply_preset,
                 label_visibility="collapsed")
        with q2.popover("More filters", width="stretch"):
            st.caption("Exact ranges")
            emp_lower_on = st.checkbox("Minimum workers", key="emp_lower_on")
            emp_lower = st.number_input("Minimum workers", min_value=0, step=1000, disabled=not emp_lower_on,
                                        key="emp_lower", label_visibility="collapsed")
            emp_upper_on = st.checkbox("Maximum workers", key="emp_upper_on")
            emp_upper = st.number_input("Maximum workers", min_value=0, step=1000, disabled=not emp_upper_on,
                                        key="emp_upper", label_visibility="collapsed")
            exp_lower_on = st.checkbox("Minimum AI use (%)", key="exp_lower_on")
            exp_lower = st.number_input("Minimum AI use (%)", min_value=0.0, max_value=100.0, step=0.1,
                                        disabled=not exp_lower_on, key="exp_lower", label_visibility="collapsed")
            exp_upper_on = st.checkbox("Maximum AI use (%)", key="exp_upper_on")
            exp_upper = st.number_input("Maximum AI use (%)", min_value=0.0, max_value=100.0, step=0.1,
                                        disabled=not exp_upper_on, key="exp_upper", label_visibility="collapsed")
        q3.button("↺ Reset", on_click=reset_filters, width="stretch", key="reset_btn")
        f1, f2, f3, f4, f5 = st.columns([3, 2, 2, 3, 2], vertical_alignment="bottom")
        selected_groups = f1.multiselect("Industry", list(groups), key="groups", placeholder="All industries",
                                         format_func=lambda label: short_group(label.split(" · ", 1)[1]))
        f2.selectbox("Job size", list(SIZES), key="size", on_change=apply_size)
        selected_outlooks = f3.multiselect("Job outlook", ["Growing", "Stable", "Declining", "Unknown"],
                                           key="outlooks", placeholder="Any outlook",
                                           format_func=lambda o: OUTLOOK_LABELS.get(o, o))
        query = f4.text_input("Find a job", key="search", placeholder="e.g. nurse, teacher, 43-9021")
        threshold = f5.slider("“High AI use” means ≥", 5, 60, 20, step=5, key="threshold", format="%d%%",
                              help="A job counts as high-AI when AI is used in at least this share of its tasks. "
                                   "Changes the charts only, never a score.")
        size_bounds = SIZES[st.session_state.get("size", "Any size")]
        from_size = (size_bounds[0] is not None) == emp_lower_on and (size_bounds[1] is not None) == emp_upper_on \
            and st.session_state.get("size", "Any size") != "Any size"
        active = [label for on, label in [(emp_lower_on and not from_size, "min workers"),
                                          (emp_upper_on and not from_size, "max workers"),
                                          (exp_lower_on, "min AI use"), (exp_upper_on, "max AI use")] if on]
        if active:
            st.caption("Also filtering by " + ", ".join(active) + " (see More filters)")

    # Ranking order is chosen next to the ranking table (step 2) and reused by the shortlist.
    st.session_state.setdefault("sort_label", "Review priority score")
    st.session_state.setdefault("direction", "Descending")
    metric_label = st.session_state["sort_label"]
    ascending = st.session_state["direction"] == "Ascending"
    metric = SORT_OPTIONS[metric_label]
    invalid = ((emp_lower_on and emp_upper_on and emp_lower > emp_upper) or
               (exp_lower_on and exp_upper_on and exp_lower > exp_upper))
    filtered = None
    if not invalid:
        filtered = backend.filter_occupations(
            all_rows, groups=[groups[x] for x in selected_groups] if selected_groups else None,
            outlooks=selected_outlooks if selected_outlooks else None,
            employment_min=emp_lower if emp_lower_on else None,
            employment_max=emp_upper if emp_upper_on else None,
            exposure_min=exp_lower / 100 if exp_lower_on else None,
            exposure_max=exp_upper / 100 if exp_upper_on else None, query=query,
        )
        if st.session_state.get("detail_soc") and st.session_state.detail_soc not in set(filtered["soc_code"]):
            st.session_state.detail_soc = None

    # --- KPI row: always visible, always reflects the filters ------------------------------------
    if invalid:
        st.error("A minimum is bigger than its maximum. Fix the numbers under More filters.")
    else:
        summary = backend.summary_metrics(filtered)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Jobs shown", integer(summary["occupation_count"]), border=True,
                  help="Out of 755 U.S. jobs (occupations).")
        c2.metric("Workers in these jobs",
                  "—" if summary["employment_2025"] is None else people(summary["employment_2025"]),
                  border=True, help="2025 employment in the jobs shown: "
                  + ("—" if summary["employment_2025"] is None else integer(summary["employment_2025"])))
        c3.metric("Average AI use",
                  "—" if summary["mean_observed_exposure"] is None else
                  percentage(summary["mean_observed_exposure"], 1), border=True,
                  help="Average across jobs (each job counts once) of the % of tasks done with AI. "
                       "Not the % of workers using AI.")
        c4.metric("Shrinking jobs", integer(summary["declining_occupation_count"]), border=True,
                  help="Jobs the government (BLS) expects to have fewer workers in 2035 than in 2025.")
        if filtered.empty:
            st.info("No jobs match. Try fewer filters.")
            st.button("Show all jobs", on_click=reset_filters)

    # --- Step navigator ---------------------------------------------------------------------------
    st.session_state.setdefault("step", "explore")
    n_saved = len(st.session_state.saved_socs)
    st.write("")
    st.segmented_control("Step", list(STEPS), key="step", label_visibility="collapsed",
                         format_func=lambda k: STEPS[k] + (f"  ({n_saved})" if k == "shortlist" else ""))
    step = st.session_state.get("step") or "explore"

    if step == "explore" and not invalid:
        render_explore(filtered, threshold)
    elif step == "prioritize" and not invalid:
        render_prioritize(all_rows, tasks, filtered, threshold, metric, metric_label, ascending)
    elif step == "shortlist":
        render_shortlist(all_rows, filtered, metric, metric_label, ascending)


def render_explore(filtered, threshold):
    section("How much AI is in work today?")
    a, b = st.columns(2, gap="large")
    with a:
        exposure_bands(filtered)
    with b:
        worker_split(filtered, threshold)

    section("Which industries?")
    a, b = st.columns(2, gap="large")
    with a:
        sector_share(filtered, threshold)
    with b:
        sector_zone_workers(filtered, threshold)

    section("Who works in high-AI, shrinking jobs?")
    a, b = st.columns(2, gap="large")
    with a:
        education_zone(filtered, threshold)
    with b:
        wage_bands(filtered, threshold)
    next_step("Next: find the jobs to review first →", "prioritize")


def render_prioritize(all_rows, tasks, filtered, threshold, metric, metric_label, ascending):
    # 1) Comparison chart from the Phase 1 sketch ----------------------------------------------------
    section("Which jobs?")
    zone_n = int(zone_mask(filtered, threshold).sum())
    chart_title(f"{zone_n} job{'s are' if zone_n != 1 else ' is'} high-AI and shrinking (shaded corner)" if zone_n
                else "No high-AI, shrinking jobs here",
                "Click a bubble to see the job",
                help="The shaded corner = high AI use AND expected to shrink. Neither axis is the chance of "
                     "losing a job, and job change is not caused by AI alone.")
    st.session_state.setdefault("hide_zero", True)
    n_zero = int(filtered["observed_exposure"].eq(0).sum())
    st.toggle(f"Hide {n_zero} jobs with no AI use", key="hide_zero")
    open_job(priority_scatter(filtered, threshold, st.session_state.get("hide_zero", True)), "bubble")

    # 2) Why the top jobs score high ------------------------------------------------------------------
    section("Why these jobs rank high")
    ranked = backend.rank_occupations(filtered, metric, ascending=ascending)
    st.session_state.setdefault("n_top", 10)
    n_col, _ = st.columns([1, 3])
    n_col.slider("Show top", 5, 20, key="n_top", format="%d jobs")
    top_rows = (backend.rank_occupations(filtered, "priority_score", ascending=False)
                .dropna(subset=["priority_score"]).head(st.session_state.get("n_top", 10)))
    if top_rows.empty:
        chart_title("No scores to show")
    else:
        maxed = int(top_rows["exposure_component"].ge(1).sum())
        lead = top_rows.iloc[0]
        chart_title("Most top jobs max out on AI use — shrinking and size decide the order"
                    if maxed * 2 >= len(top_rows) else f"{lead['title']} scores highest here",
                    None,
                    help="Higher score = review sooner. It is a team screening rule, not the chance of losing "
                         "a job. See “How is the score calculated?” below the ranking.")
        component_bars(top_rows)

    # 3) Priority ranking table ------------------------------------------------------------------------
    section("Priority ranking")
    o1, o2, o3 = st.columns([2, 1.3, 3], vertical_alignment="bottom")
    o1.selectbox("Sort by", list(SORT_OPTIONS), key="sort_label", help=SORT_HELP)
    o2.selectbox("Order", ["Descending", "Ascending"], key="direction", help="Descending = high to low.")
    o3.caption("Click a row to see the job ↓")
    open_job(display_table(ranked, height=380, select_key="rank_table"), "table")
    with st.expander("How is the score calculated?"):
        st.markdown(SCORE_HELP)

    # 4) Occupation drill-down -------------------------------------------------------------------------
    section("Job details")
    titles = dict(zip(all_rows["soc_code"], all_rows["title"]))
    pick, add = st.columns([4, 1], vertical_alignment="bottom")
    chosen = pick.selectbox("Pick a job", ranked["soc_code"].tolist(), index=None, key="detail_soc",
                            placeholder="Type a job name",
                            format_func=lambda soc: f"{titles[soc]} ({soc})")
    if chosen:
        already = chosen in st.session_state.saved_socs
        if add.button("✓ In shortlist" if already else "⭐ Add to shortlist", disabled=already, width="stretch",
                      type="primary"):
            st.session_state.saved_socs.append(chosen)
            st.toast(f"Saved {titles[chosen]} to your shortlist")
            st.rerun()
        details(all_rows, tasks, chosen)
    if st.session_state.saved_socs:
        next_step(f"Next: review your shortlist ({len(st.session_state.saved_socs)}) →", "shortlist")


def render_shortlist(all_rows, filtered, metric, metric_label, ascending):
    section("Your shortlist")
    saved_codes = st.session_state.saved_socs
    if filtered is None:
        st.caption("Saved jobs hidden by filters: unavailable until the filters are fixed.")
    elif hidden := len(set(saved_codes) - set(filtered["soc_code"])):
        st.caption(f"{hidden} saved job(s) are outside the current filters (still kept).")
    saved_frame = backend.shortlist_data(all_rows, saved_codes, metric, ascending=ascending)
    if saved_frame.empty:
        st.info("Nothing saved yet.")
        st.button("Go to ② Prioritize", on_click=go_to, args=("prioritize",), type="primary")
    else:
        component_bars(saved_frame)
        display_table(saved_frame)
        # Export complete clean records, score components, and rank, not formatted display strings.
        st.download_button("⬇ Download shortlist (CSV)", saved_frame.to_csv(index=False).encode("utf-8-sig"),
                           file_name="occupation_shortlist.csv", mime="text/csv", type="primary",
                           help="Your list resets when you close the page — download it to keep it.")
        titles = dict(zip(all_rows["soc_code"], all_rows["title"]))
        r0, r1, r2 = st.columns([3, 1, 1], vertical_alignment="bottom")
        remove = r0.selectbox("Remove a job", saved_frame["soc_code"].tolist(),
                              format_func=lambda soc: f"{titles[soc]} ({soc})")
        if r1.button("Remove", width="stretch"):
            st.session_state.saved_socs.remove(remove)
            st.rerun()
        if r2.button("Clear shortlist", width="stretch"):
            st.session_state.saved_socs = []
            st.rerun()


if __name__ == "__main__":
    main()
