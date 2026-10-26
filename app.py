"""AI Workforce Investment Planner: the shared Phase 3 Streamlit dashboard."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
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


@st.cache_data(show_spinner="Loading clean occupation data")
def load_data(occupation_path: str, occupation_mtime: int, task_path: str, task_mtime: int):
    # Modification times are deliberate cache keys; backend loads the fixed-score full dataset.
    return backend.load_clean_data(Path(occupation_path).parent)


def missing(value) -> bool:
    return value is None or (not isinstance(value, (dict, list, pd.DataFrame)) and pd.isna(value))


def integer(value) -> str:
    return "Not reported" if missing(value) else f"{value:,.0f}"


def percentage(value, digits=2) -> str:
    return "Not reported" if missing(value) else f"{value * 100:.{digits}f}%"


def growth(value) -> str:
    return "Not reported" if missing(value) else f"{value:.1f}%"


def score(value) -> str:
    return "Not reported" if missing(value) else f"{value:.1f}"


def wage(value) -> str:
    return "Not reported" if missing(value) else f"${value:,.0f}"


def text_value(value, *, category=False) -> str:
    if category and value == "None":
        return "None required"
    return "Not reported" if missing(value) or value == "" else str(value)


def reset_filters():
    for key in ["groups", "outlooks", "emp_lower_on", "emp_upper_on", "exp_lower_on", "exp_upper_on", "search"]:
        st.session_state.pop(key, None)
    for key in ["emp_lower", "emp_upper", "exp_lower", "exp_upper"]:
        st.session_state.pop(key, None)


def display_table(rows: pd.DataFrame):
    cols = ["display_rank", "title", "soc_code", "priority_score", "observed_exposure",
            "average_task_penetration", "employment_2025", "median_annual_wage_2025",
            "employment_change_percent_2025_35", "task_match_rate"]
    table = rows[cols].copy()
    for field in ("observed_exposure", "average_task_penetration", "task_match_rate"):
        table[field] = table[field].map(percentage)
    table["priority_score"] = table["priority_score"].map(score)
    table["employment_2025"] = table["employment_2025"].map(integer)
    table["median_annual_wage_2025"] = table["median_annual_wage_2025"].map(wage)
    table["employment_change_percent_2025_35"] = table["employment_change_percent_2025_35"].map(growth)
    table.columns = ["Rank", "Occupation", "SOC", "Score", "AI exposure", "Task mean", "Employment",
                     "Annual wage", "Projected change", "Task coverage"]
    st.dataframe(table, hide_index=True, width="stretch")


def details(occupations: pd.DataFrame, tasks: pd.DataFrame, soc: str):
    record = backend.occupation_details(occupations, tasks, soc)
    item = record["occupation"]
    st.subheader(f"{item['title']} ({soc})")
    st.write(text_value(item.get("occupation_description")))
    st.caption(f"Description source: {text_value(item.get('description_source_onet_code'))}")
    a, b, c = st.columns(3)
    a.metric("Review priority score / 100", score(item.get("priority_score")))
    b.metric("Observed AI exposure", percentage(item.get("observed_exposure")))
    c.metric("Average task penetration", percentage(item.get("average_task_penetration")))
    st.write("Score components (0–1): " + "; ".join(
        f"{name.replace('_', ' ')}: {score(item.get(name))}" for name in COMPONENTS
    ))
    st.caption("The score is a screening choice for further review, not a job-loss probability.")
    rows = {
        "Employment (2025 persons)": integer(item.get("employment_2025")),
        "Projected change (2025–35)": growth(item.get("employment_change_percent_2025_35")),
        "Projected decline (percentage points)": growth(item.get("projected_decline_percent_points")),
        "Median annual wage": wage(item.get("median_annual_wage_2025")),
        "Annual openings (persons)": integer(item.get("annual_openings_2025_35")),
        "Typical education": text_value(item.get("typical_education")),
        "Related work experience": text_value(item.get("related_work_experience"), category=True),
        "On-the-job training": text_value(item.get("on_the_job_training"), category=True),
        "Matched / total tasks": f"{integer(item.get('matched_task_count'))} / {integer(item.get('total_task_count'))}",
        "Task match rate": percentage(item.get("task_match_rate")),
    }
    st.dataframe(pd.DataFrame(rows.items(), columns=["Measure", "Value"]), hide_index=True, width="stretch")
    st.caption("‘None required’ describes typical entry requirements, not AI-training need.")
    st.markdown("**Highest-penetration matched tasks**")
    top = record["top_tasks"]
    if top.empty:
        st.write("No scored tasks reported.")
    else:
        view = top[["task_rank", "task", "penetration"]].copy()
        view["penetration"] = view["penetration"].map(percentage)
        view.columns = ["Rank", "Task", "Penetration"]
        st.dataframe(view, hide_index=True, width="stretch")


def main():
    st.set_page_config(page_title="AI Workforce Investment Planner", layout="wide")
    st.title("AI Workforce Investment Planner")
    st.caption("National occupation screening for further training review. Sources: Anthropic, O*NET and BLS.")
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

    with st.sidebar:
        st.header("Filters")
        group_names = (all_rows[["occupation_group_code", "occupation_group_name"]]
                       .drop_duplicates().sort_values("occupation_group_code"))
        groups = {f"{row.occupation_group_code} · {row.occupation_group_name}": row.occupation_group_code
                  for row in group_names.itertuples(index=False)}
        selected_groups = st.multiselect("SOC major group", list(groups), key="groups")
        selected_outlooks = st.multiselect("Projected outlook", sorted(backend.OUTLOOKS), key="outlooks")
        st.caption("Cleared group/outlook selections include all occupations.")
        emp_lower_on = st.checkbox("Use minimum employment", key="emp_lower_on")
        emp_lower = st.number_input("Minimum employment (persons)", min_value=0, step=1000,
                                    disabled=not emp_lower_on, key="emp_lower")
        emp_upper_on = st.checkbox("Use maximum employment", key="emp_upper_on")
        emp_upper = st.number_input("Maximum employment (persons)", min_value=0, step=1000,
                                    disabled=not emp_upper_on, key="emp_upper")
        exp_lower_on = st.checkbox("Use minimum exposure", key="exp_lower_on")
        exp_lower = st.number_input("Minimum AI exposure (%)", min_value=0.0, max_value=100.0,
                                    step=0.1, disabled=not exp_lower_on, key="exp_lower")
        exp_upper_on = st.checkbox("Use maximum exposure", key="exp_upper_on")
        exp_upper = st.number_input("Maximum AI exposure (%)", min_value=0.0, max_value=100.0,
                                    step=0.1, disabled=not exp_upper_on, key="exp_upper")
        query = st.text_input("Search title or SOC (literal)", key="search")
        st.button("Reset filters", on_click=reset_filters)
        st.divider()
        metric_label = st.selectbox("Sort by", list(SORT_OPTIONS), key="sort_label")
        ascending = st.selectbox("Direction", ["Descending", "Ascending"], key="direction") == "Ascending"
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
    compare, shortlist = st.tabs(["Compare occupations", "Shortlist"])
    with compare:
        if invalid:
            st.error("Minimum cannot exceed maximum. Correct the filter bounds to see comparisons.")
        else:
            summary = backend.summary_metrics(filtered)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Included occupations", integer(summary["occupation_count"]))
            c2.metric("Employment in included occupations (2025)",
                      "—" if summary["employment_2025"] is None else integer(summary["employment_2025"]))
            c3.metric("Mean occupation AI exposure (unweighted)",
                      "—" if summary["mean_observed_exposure"] is None else percentage(summary["mean_observed_exposure"]))
            c4.metric("Declining occupations", integer(summary["declining_occupation_count"]))
            if filtered.empty:
                st.info("No occupations match these filters")
                st.button("Reset filters to see all occupations", on_click=reset_filters)
            st.subheader("Occupation comparison")
            chart = backend.comparison_data(filtered)
            st.caption(f"Chart omits {len(filtered) - len(chart)} occupations missing a required chart value or positive employment.")
            if not chart.empty:
                chart = chart.copy()
                chart["wage_label"] = chart["median_annual_wage_2025"].map(wage)
                chart["exposure_label"] = chart["observed_exposure"].map(percentage)
                chart["change_label"] = chart["employment_change_percent_2025_35"].map(growth)
                chart["employment_label"] = chart["employment_2025"].map(integer)
                chart["score_label"] = chart["priority_score"].map(score)
                for component in COMPONENTS:
                    chart[component + "_label"] = chart[component].map(score)
                fig = px.scatter(
                    chart, x="employment_change_percent_2025_35", y="observed_exposure_percent",
                    size="employment_2025", size_max=55, color="priority_score",
                    range_color=(0, 100), color_continuous_scale="Viridis",
                    hover_name="title", custom_data=["soc_code", "score_label"] +
                    [x + "_label" for x in COMPONENTS] +
                    ["exposure_label", "change_label", "employment_label", "wage_label"],
                    labels={"employment_change_percent_2025_35": "BLS projected employment change (%)",
                            "observed_exposure_percent": "Observed AI exposure (%)",
                            "priority_score": "Review priority score"},
                )
                fig.update_traces(hovertemplate=(
                    "%{hovertext} (%{customdata[0]})<br>Score: %{customdata[1]}<br>"
                    "Exposure / decline / employment / task components: %{customdata[2]} / "
                    "%{customdata[3]} / %{customdata[4]} / %{customdata[5]}<br>"
                    "AI exposure: %{customdata[6]}<br>Projected change: %{customdata[7]}<br>"
                    "Employment: %{customdata[8]}<br>Wage: %{customdata[9]}<extra></extra>"))
                fig.add_vline(x=0, line_dash="dash", line_color="gray")
                st.plotly_chart(fig, width="stretch")
            st.caption("Neither axis is an individual job-loss probability. BLS change does not isolate AI effects; bubble area represents employment.")
            groups_frame = backend.group_summary(filtered)
            declining = groups_frame.loc[groups_frame["declining_occupation_count"].gt(0)].sort_values(
                ["declining_occupation_count", "occupation_group_code"], ascending=[False, True])
            st.subheader("Declining occupations by SOC major group")
            if declining.empty:
                st.caption("No declining occupations in the current selection.")
            else:
                bar = px.bar(declining, x="declining_occupation_count", y="occupation_group_name",
                             orientation="h", labels={"declining_occupation_count": "Number of occupations",
                                                       "occupation_group_name": "SOC major group"})
                bar.update_layout(yaxis={"categoryorder": "array", "categoryarray": declining["occupation_group_name"].iloc[::-1].tolist()})
                st.plotly_chart(bar, width="stretch")
            st.caption("Bars count occupations, not displaced workers; both charts use the current filters.")
            st.subheader("Occupation ranking")
            ranked = backend.rank_occupations(filtered, metric, ascending=ascending)
            display_table(ranked)
            with st.expander("How the review score works"):
                st.write("Score = 100 × (40% observed exposure component + 30% projected decline component "
                         "+ 20% employment component + 10% matched-task component). References are fixed across filters; "
                         "missing required inputs give an unavailable score. Wages are context, not a score input.")
            with st.expander("SOC group summary"):
                group_view = groups_frame[["occupation_group_name", "occupation_count", "employment_2025",
                                           "mean_observed_exposure", "declining_occupation_count"]].copy()
                group_view["employment_2025"] = group_view["employment_2025"].map(integer)
                group_view["mean_observed_exposure"] = group_view["mean_observed_exposure"].map(percentage)
                group_view.columns = ["Group", "Occupations", "Employment", "Mean exposure", "Declining occupations"]
                st.dataframe(group_view, hide_index=True, width="stretch")
            st.subheader("Occupation details")
            options = ranked["soc_code"].tolist()
            chosen = st.selectbox("Select an occupation", options, index=None, key="detail_soc",
                                  placeholder="Select an occupation", format_func=lambda soc: (
                                      f"{all_rows.loc[all_rows.soc_code.eq(soc), 'title'].iloc[0]} ({soc})"))
            if chosen:
                details(all_rows, tasks, chosen)
                if st.button("Add to shortlist", disabled=chosen in st.session_state.saved_socs):
                    st.session_state.saved_socs.append(chosen)
                    st.rerun()
            else:
                st.caption("Select an occupation to inspect its measures and tasks.")
    with shortlist:
        st.subheader("Saved occupations")
        saved_codes = st.session_state.saved_socs
        if filtered is None:
            st.caption("Saved occupations outside current filters: unavailable until filter bounds are valid.")
        else:
            st.caption(f"Saved occupations outside current filters: {len(set(saved_codes) - set(filtered['soc_code']))}")
        saved_frame = backend.shortlist_data(all_rows, saved_codes, metric, ascending=ascending)
        display_table(saved_frame)
        if saved_frame.empty:
            st.caption("Add an occupation from Compare occupations to enable CSV export.")
        else:
            # Export complete clean records, score components, and rank, not formatted display strings.
            st.download_button("Download shortlist CSV", saved_frame.to_csv(index=False).encode("utf-8-sig"),
                               file_name="occupation_shortlist.csv", mime="text/csv")
            remove = st.selectbox("Remove an occupation", saved_frame["soc_code"].tolist(),
                                  format_func=lambda soc: f"{all_rows.loc[all_rows.soc_code.eq(soc), 'title'].iloc[0]} ({soc})")
            if st.button("Remove selected occupation"):
                st.session_state.saved_socs.remove(remove)
                st.rerun()
            if st.button("Clear shortlist"):
                st.session_state.saved_socs = []
                st.rerun()
        st.caption("The shortlist lasts for this browser session; download the CSV to keep it.")


if __name__ == "__main__":
    main()
