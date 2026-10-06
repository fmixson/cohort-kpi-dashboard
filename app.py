"""
Cerritos College Cohort KPI Dashboard
======================================
A dashboard the president and other leaders can open on their own,
anytime, to see how the college is doing on its KPIs, cohort by cohort --
built directly from the richer student-level data (persistence,
retention, course completion, awards, CTE units, demographics) rather
than the smaller pre-aggregated KPI Weekly Report workbook.

SAFE-TO-PUBLISH DESIGN: this app never touches individual student
records. It reads a single bundled `aggregate_snapshot.json` file --
nothing but computed rates, counts, and percentages -- committed to this
repo. That file is produced by the separate, local-only `student_data_tool`
project, which is the only place the real (de-identified) student-level
data ever exists. Refreshing this dashboard is a matter of re-running
that export locally and replacing/committing the JSON file here; no
student data ever passes through this app or this repo.
"""

import json
from pathlib import Path

import streamlit as st
import pandas as pd

# LCP names live in their own module so this file can be replaced wholesale
# without losing them. A missing lcp_names.py degrades to bare codes rather
# than breaking the dashboard.
try:
    from lcp_names import LCP_NAMES
except ImportError:
    LCP_NAMES = {}

ALL_LCPS = "All LCPs"


def lcp_label(code: str) -> str:
    """Full name with the code in parentheses; bare code if no name is set."""
    if code == ALL_LCPS:
        return ALL_LCPS
    name = (LCP_NAMES.get(code) or "").strip()
    return f"{name} ({code})" if name else code


NAVY = "#1E2761"
ICE = "#CADCFC"
GREEN = "#1E7A46"
RED = "#B3261E"
GRAY = "#6B6B6B"
LIGHTBG = "#F2F2F2"

st.set_page_config(page_title="Cohort KPI Dashboard", layout="wide")

SNAPSHOT_PATH = Path("aggregate_snapshot.json")
SAMPLE_PATH = Path("sample_data/sample_aggregate_snapshot.json")


# ---------------------------------------------------------------- helpers
def status_color(value, target):
    if value is None:
        return GRAY
    if target is not None:
        return GREEN if value >= target else RED
    return NAVY


def metric_card(label, note, value, target, suppressed=False):
    color = status_color(value, target)
    val_txt = f"{value:.0f}%" if value is not None else "N/A"
    if value is None and suppressed:
        note = (note or "") + " — withheld: too few students in this group to report safely"
    goal_line = (f"<div style='font-size:0.8rem;color:{GRAY};font-style:italic;'>Goal: {target:.0f}%</div>"
                 if target is not None else
                 f"<div style='font-size:0.8rem;color:{GRAY};'>No comparable annual goal</div>")
    st.markdown(
        f"""
        <div style="border:1px solid #E3E3E3;border-radius:10px;padding:0.9rem 1rem;background:white;height:100%;">
            <div style="font-size:0.85rem;color:#2A2A2A;font-weight:600;">{label}</div>
            <div style="font-size:0.75rem;color:{GRAY};margin-bottom:0.35rem;">{note}</div>
            <div style="font-size:1.7rem;font-weight:700;color:{color};">{val_txt}</div>
            {goal_line}
        </div>
        """,
        unsafe_allow_html=True,
    )


def reports_panel(snapshot: dict, cohort_label: str, scope: str) -> None:
    """Render the approved takeaways and actions for the current selection.

    Institution reports show when no LCP is selected; the pathway's own replace
    them when one is. Silent when a snapshot carries no reports -- older
    snapshots predate this feature and should simply look the way they always
    did, not display an error.

    This function renders fixed text and computes nothing. That is the point:
    what appears here is byte-for-byte what was approved in student_data_tool.
    """
    reports = (snapshot.get("reports") or {}).get(cohort_label)
    if not reports:
        return

    body = (reports.get("institution") if scope == ALL_LCPS
            else (reports.get("LCP") or {}).get(scope))
    if not body:
        return

    takeaways = body.get("takeaways") or []
    actions = body.get("actions") or []
    if not (takeaways or actions):
        return

    suffix = "" if scope == ALL_LCPS else f" -- {lcp_label(scope)}"

    def _block(heading, items, accent):
        if not items:
            return ""
        lis = "".join(
            f"<li style='margin-bottom:0.45rem;line-height:1.45;'>{i}</li>"
            for i in items
        )
        return (
            f"<div style='flex:1 1 320px;border-left:4px solid {accent};"
            f"background:white;border-radius:0 8px 8px 0;padding:0.9rem 1.2rem;'>"
            f"<div style='font-size:0.95rem;font-weight:700;color:{accent};"
            f"margin-bottom:0.5rem;'>{heading}</div>"
            f"<ul style='margin:0;padding-left:1.2rem;font-size:0.9rem;"
            f"color:#2A2A2A;'>{lis}</ul></div>"
        )

    st.markdown(
        f"""
        <div style="display:flex;gap:1rem;flex-wrap:wrap;background:{LIGHTBG};
                    border-radius:8px;padding:1rem;margin-bottom:1rem;">
            {_block("Key Takeaways" + suffix, takeaways, NAVY)}
            {_block("Recommended Actions" + suffix, actions, GREEN)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    meta = snapshot.get("reports_meta") or {}
    if meta.get("approved_by"):
        st.caption(
            f"Reviewed and approved by {meta['approved_by']} for the "
            f"{meta.get('data_as_of', 'current')} data."
        )


def fall_year(label):
    import re
    m = re.search(r"(\d{4})", label or "")
    return int(m.group(1)) if m else 0


def load_snapshot(use_sample: bool) -> dict | None:
    path = SAMPLE_PATH if use_sample else SNAPSHOT_PATH
    if not path.exists():
        return None
    return json.loads(path.read_text())


# ---------------------------------------------------------------- sidebar
st.sidebar.title("Cerritos College")
st.sidebar.caption("Cohort KPI Dashboard")

live_exists = SNAPSHOT_PATH.exists()
use_sample = False
if not live_exists:
    st.sidebar.warning(
        "No aggregate_snapshot.json found in this deployment yet -- showing made-up sample data "
        "so you can see how this looks. Publish a real snapshot from student_data_tool to replace it."
    )
    use_sample = True
else:
    use_sample = st.sidebar.checkbox("Show sample data instead", value=False)

snapshot = load_snapshot(use_sample)
if snapshot is None:
    st.title("Cohort KPI Dashboard")
    st.write("No data available yet -- no aggregate_snapshot.json or sample data found.")
    st.stop()

# The date the DATA represents, not the date the file was built. Falling back
# to generated_at keeps older snapshots readable, but a snapshot carrying
# data_as_of is the one telling the truth.
st.sidebar.caption(
    f"Data as of: {snapshot.get('data_as_of') or snapshot.get('generated_at', 'unknown')}"
)
if use_sample:
    st.sidebar.info("Showing made-up sample data, not real Cerritos College figures.")

_dc = snapshot.get("disclosure_control") or {}
if _dc:
    _n = _dc.get("segment_cells_suppressed", 0) + _dc.get("cells_suppressed", 0)
    if _n:
        st.sidebar.caption(
            f"Disclosure control: {_n} figure(s) withheld where fewer than "
            f"{_dc.get('min_n', 10)} students sit behind them."
        )

cohorts = snapshot.get("cohorts", {})
if not cohorts:
    st.title("Cohort KPI Dashboard")
    st.write("This snapshot doesn't contain any cohorts yet.")
    st.stop()

cohort_labels = sorted(cohorts.keys(), key=fall_year, reverse=True)

OVERALL_METRIC_ORDER = ["english_attempted", "math_attempted", "cte_units_attempted",
                        "english_completed", "math_completed", "cte_units_completed",
                        "units_60_plus", "any_award", "graduated"]
AY_METRIC_ORDER = ["csep_dpp", "units_attempted", "units_completed", "persistence_fs", "persistence_ff", "persistence_s2", "persistence_f3"]


# ---------------------------------------------------------------- main
st.title("Cohort KPI Dashboard")
st.caption(
    "Computed from the student-level data, independent of the KPI Weekly Report workbook -- "
    "richer breakdowns, and a useful cross-check against the official figures."
)

st.subheader("Institutional Overview — All Cohorts")
st.caption(
    "Current standing for every tracked cohort, side by side — always institution-wide. "
    "Select a cohort below for the full year-by-year journey, filterable by LCP."
)

# This table's row order follows the same general principle as the rest
# of the dashboard: CSEP first, then each Attempted metric immediately
# followed by its own Completed metric, then the as-of-now totals last.
# CSEP is a by-year metric (not an "overall" one), so for this table we
# pull each cohort's most recent available year -- i.e. its current
# standing -- rather than a single fixed year.
OVERVIEW_ROW_ORDER = ["csep_dpp", "english_attempted", "english_completed",
                      "math_attempted", "math_completed",
                      "cte_units_attempted", "cte_units_completed",
                      "units_60_plus", "any_award", "graduated"]
BY_YEAR_OVERVIEW_KEYS = {"csep_dpp"}


def _overview_metric(cohort_data, key):
    if key in BY_YEAR_OVERVIEW_KEYS:
        by_year = cohort_data.get("by_year", {})
        if not by_year:
            return None
        latest_year = max((int(y) for y in by_year.keys()), default=None)
        if latest_year is None:
            return None
        return by_year[str(latest_year)].get(key)
    return cohort_data.get("overall", {}).get(key)


header_cells = "".join(
    f"<th style='padding:0.55rem 0.9rem;text-align:center;color:white;background:{NAVY};"
    f"font-size:0.8rem;white-space:nowrap;'>{label}<br><span style='font-weight:400;color:{ICE};'>"
    f"{cohorts[label]['n_students']:,} students</span></th>"
    for label in cohort_labels
)

metric_rows = ""
for key in OVERVIEW_ROW_ORDER:
    sample_metric = next((_overview_metric(cohorts[l], key) for l in cohort_labels if _overview_metric(cohorts[l], key)), None)
    if sample_metric is None:
        continue
    cells = (f"<td style='padding:0.55rem 0.9rem;font-weight:600;color:#2A2A2A;"
             f"background:{LIGHTBG};font-size:0.85rem;white-space:nowrap;'>{sample_metric['label']}</td>")
    for label in cohort_labels:
        m = _overview_metric(cohorts[label], key)
        val = m["value"] if m else None
        target = m["target"] if m else None
        color = status_color(val, target)
        val_txt = f"{val:.0f}%" if val is not None else "N/A"
        cells += (f"<td style='padding:0.55rem 0.9rem;text-align:center;font-weight:700;"
                  f"color:{color};font-size:1rem;'>{val_txt}</td>")
    metric_rows += f"<tr>{cells}</tr>"

st.markdown(
    f"""
    <div style="overflow-x:auto;border:1px solid #E3E3E3;border-radius:8px;">
    <table style="border-collapse:collapse;width:100%;">
        <thead><tr>
            <th style='padding:0.55rem 0.9rem;text-align:left;background:{NAVY};color:white;font-size:0.8rem;'>Metric</th>
            {header_cells}
        </tr></thead>
        <tbody>{metric_rows}</tbody>
    </table>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("Green = at/above its annual goal · Red = below goal · Navy = no goal defined for that metric · Gray = no data.")

st.divider()
st.subheader("Cohort Journey")
_default_cohort = "Fall 2024" if "Fall 2024" in cohort_labels else cohort_labels[0]
cohort_label = st.selectbox("Select a cohort", cohort_labels, index=cohort_labels.index(_default_cohort))
data = cohorts[cohort_label]

# ---- LCP scope selector -------------------------------------------------
# `segments` carries the full metric set computed per LCP, produced by the
# export in student_data_tool. Selecting one simply swaps which node feeds
# every card below -- no other change is needed. The dropdown shows full
# names via lcp_label() while the underlying value stays the code.
segments = (data.get("segments") or {}).get("LCP", {})
scope = ALL_LCPS
if segments:
    options = [ALL_LCPS] + sorted(segments.keys(), key=lcp_label)

    # Remember the chosen LCP across cohort changes. Cohorts do not all carry
    # the same LCP list (e.g. "(unknown)" is absent from some), and Streamlit
    # treats a changed option list as a brand-new widget -- which silently
    # reset the selection to All LCPs. The choice is kept in session state and
    # passed back in as the default; it falls back to All LCPs only when the
    # newly selected cohort really has no figures for that LCP.
    _choice = st.session_state.get("lcp_choice", ALL_LCPS)
    if _choice not in options:
        _choice = ALL_LCPS

    def _remember_lcp():
        st.session_state["lcp_choice"] = st.session_state["lcp_select"]

    scope = st.selectbox("LCP / Division", options, index=options.index(_choice),
                         format_func=lcp_label, key="lcp_select",
                         on_change=_remember_lcp)
    if scope != ALL_LCPS:
        data = segments[scope]
else:
    st.caption(
        "This snapshot has no per-LCP figures yet — rebuild it from student_data_tool "
        "with the segments export to enable the LCP filter."
    )

_scope_suffix = "" if scope == ALL_LCPS else f" · {lcp_label(scope)}"

st.markdown(
    f"""
    <div style="background:{NAVY};padding:1rem 1.5rem;border-radius:8px;margin-bottom:1rem;">
        <div style="color:white;font-size:1.6rem;font-weight:700;">{cohort_label}{_scope_suffix} — Cohort Journey</div>
        <div style="color:{ICE};font-size:0.9rem;">Cerritos College · {data['n_students']:,} students</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Approved takeaways and actions for whatever is currently selected --
# institution when the scope is All LCPs, that pathway's own when one is chosen.
reports_panel(snapshot, cohort_label, scope)

by_year = data.get("by_year", {})
years = sorted((int(y) for y in by_year.keys()), )
if years:
    cols = st.columns(len(years))
    for col, ay in zip(cols, years):
        with col:
            st.markdown(
                f"<div style='background:{LIGHTBG};border-radius:8px;padding:0.6rem 0.8rem;margin-bottom:0.6rem;'>"
                f"<div style='font-weight:700;color:{NAVY};'>Year {ay}</div></div>",
                unsafe_allow_html=True,
            )
            year_metrics = by_year[str(ay)]
            for key in AY_METRIC_ORDER:
                m = year_metrics.get(key)
                if m is None:
                    continue
                metric_card(m["label"], m["note"], m["value"], m["target"],
                            suppressed=m.get("suppressed", False))
                st.write("")
else:
    st.info("No year-by-year data in this snapshot for this cohort.")

st.write("")
st.markdown("**Overall (as of this data pull)**")
cols = st.columns(3)
for idx, key in enumerate(OVERALL_METRIC_ORDER):
    m = data["overall"].get(key)
    if m is None:
        continue
    with cols[idx % 3]:
        metric_card(m["label"], m["note"], m["value"], m["target"],
                    suppressed=m.get("suppressed", False))
        st.write("")

# Breakdown tables are institution-wide only. A single LCP broken down by
# LCP is meaningless, so the section hides itself when a scope is selected
# (segment nodes carry no "breakdowns" key).
breakdowns = data.get("breakdowns", {})
if breakdowns:
    st.divider()
    st.subheader("Breakdown")
    dim = st.selectbox("Break down by", list(breakdowns.keys()))
    rows = breakdowns[dim]
    if rows:
        df_rows = pd.DataFrame(rows)
        # Show full LCP names in the breakdown table too.
        if "LCP_current" in df_rows.columns:
            df_rows["LCP_current"] = df_rows["LCP_current"].map(
                lambda v: lcp_label(v) if isinstance(v, str) else v)
        st.dataframe(df_rows, width="stretch", hide_index=True)
    else:
        st.info("No data for this breakdown.")
elif scope != ALL_LCPS:
    st.divider()
    st.caption("Breakdown tables are institution-wide — switch back to All LCPs to see them.")

st.write("")
st.caption(
    "Goals shown mirror the KPI Weekly Report's own annual targets for the same metrics. Rates other than "
    "the units milestone are 'as of this data pull' rather than paced to a specific week, since student-level "
    "extracts don't carry the workbook's own weekly snapshot structure."
)