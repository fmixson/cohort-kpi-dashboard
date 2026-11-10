"""
Students First Framework completion goal, drawn from aggregate_snapshot.json.

The same panels as the top of "SFF at a Glance" (sff_dashboard/simple/progress.py):
four tiles and the baseline/goal bar for the goal cohort, and the
"X of N students who started in Fall YYYY have completed so far" panel.

Used by BOTH the public KPI Cohort Dashboard and the LCP Student Success
Dashboard. Keep the two copies identical: edit one, copy it over the other.

Nothing is computed from student records here. The counts come from the
snapshot's `completion` blocks (student_data_tool/completion_goal.py), which
already have small-cell suppression applied. A snapshot built before that
module existed has no such blocks; every function then draws nothing.

    goal_section(snapshot)                          # whole college
    goal_section(snapshot, scope="SEM", scope_name="Science, Engineering & Math")
    cohort_completed(snapshot, "Fall 2025")         # follows a cohort picker
"""

from __future__ import annotations

import datetime as dt
import html
import re

import streamlit as st

NAVY, ICE, RED, GRAY, INK = "#1E2761", "#CADCFC", "#B3261E", "#6B6B6B", "#2A2A2A"
BORDER, TRACK = "#E3E3E3", "#E6E5E0"


# ---------------------------------------------------------------- data access
def settings(snapshot: dict | None) -> dict | None:
    return (snapshot or {}).get("completion_goal")


def block(snapshot: dict | None, cohort: str, scope: str | None = None) -> dict | None:
    """The completion counts for a cohort, whole college (scope=None) or one LCP code."""
    node = ((snapshot or {}).get("cohorts") or {}).get(cohort) or {}
    if scope is not None:
        node = ((node.get("segments") or {}).get("LCP") or {}).get(scope) or {}
    return node.get("completion")


def has_completion(snapshot: dict | None) -> bool:
    return bool(settings(snapshot)) and any(
        (c or {}).get("completion") for c in ((snapshot or {}).get("cohorts") or {}).values())


def _fall(cohort: str) -> int:
    m = re.search(r"(\d{4})", cohort or "")
    return int(m.group(1)) if m else 0


def _as_of(snapshot: dict) -> dt.date:
    d = (settings(snapshot) or {}).get("as_of") or snapshot.get("data_as_of")
    try:
        return dt.date.fromisoformat(str(d)[:10])
    except (TypeError, ValueError):
        return dt.date.today()


def needed(b: dict, goal_pct: float) -> int | None:
    """More completers needed to reach the goal (same rounding as SFF at a Glance)."""
    if not b or b.get("completed") is None or not b.get("n"):
        return None
    return max(0, round(goal_pct / 100 * b["n"]) - b["completed"])


def _pct(k, n) -> float | None:
    return k / n if k is not None and n else None


# ---------------------------------------------------------------- pieces
def _banner(title: str, subtitle: str = "") -> str:
    return (f"<div style='background:{NAVY};padding:1rem 1.5rem;border-radius:8px;margin:0.4rem 0 1rem 0;'>"
            f"<div style='color:white;font-size:1.5rem;font-weight:700;line-height:1.3'>{title}</div>"
            + (f"<div style='color:{ICE};font-size:0.9rem;'>{subtitle}</div>" if subtitle else "") + "</div>")


def _tile(label: str, value: str, note: str, color: str = NAVY, tip: str = "") -> str:
    t = f" title=\"{html.escape(tip)}\"" if tip else ""
    return (f"<div{t} style='border:1px solid {BORDER};border-radius:10px;padding:0.9rem 1rem;background:white;"
            f"height:100%;margin-bottom:0.6rem;'><div style='font-size:0.85rem;color:{INK};font-weight:600'>{label}</div>"
            f"<div style='font-size:1.9rem;font-weight:700;color:{color};line-height:1.3'>{value}</div>"
            f"<div style='font-size:0.78rem;color:{GRAY}'>{note}</div></div>")


WITHHELD = ("Withheld", "too few students to report safely")


def _goal_bar(value: float, baseline: float, goal: float, label: str, college: float | None = None) -> str:
    """Horizontal bar like SFF at a Glance's goal chart: the cohort's rate so far,
    a solid baseline line and a dashed goal line. Values are fractions (0.215)."""
    top = max(0.6, (value or 0) + 0.1, (college or 0) + 0.1)
    x = lambda v: f"{min(100.0, v / top * 100):.2f}%"
    ticks = "".join(
        f"<div style='position:absolute;left:{x(t / 100)};top:76px;transform:translateX(-50%);font-size:12px;"
        f"color:{GRAY}'>{t}%</div>" for t in range(0, int(top * 100) + 1, 10))
    college_mark = "" if college is None else (
        f"<div style='position:absolute;left:{x(college)};top:52px;height:12px;border-left:2px solid {GRAY};'></div>"
        f"<div style='position:absolute;left:{x(college)};top:62px;transform:translateX(-50%);font-size:11px;"
        f"color:{GRAY};white-space:nowrap'>▲ College {college:.1%}</div>")
    return (
        f"<div style='position:relative;height:100px;margin:0.6rem 0.8rem 0.2rem 0.4rem;'>"
        f"<div style='position:absolute;left:0;right:0;top:20px;height:40px;background:{TRACK};'></div>"
        f"<div title=\"{html.escape(label)}: {value:.1%}\" style='position:absolute;left:0;top:28px;height:24px;"
        f"width:{x(value)};background:{NAVY};'></div>"
        + (f"<div style='position:absolute;left:0;width:{x(value)};top:32px;text-align:right;font-size:11px;"
           f"color:white;white-space:nowrap;box-sizing:border-box;padding-right:8px;font-weight:600'>{value:.1%}</div>"
           if value / top > 0.12 else
           f"<div style='position:absolute;left:calc({x(value)} + 6px);top:32px;font-size:11px;color:{NAVY};"
           f"white-space:nowrap;font-weight:600'>{value:.1%}</div>")
        + f"<div style='position:absolute;left:{x(baseline / 100)};top:12px;height:56px;border-left:2px solid {INK};'></div>"
        f"<div style='position:absolute;left:{x(baseline / 100)};top:-6px;transform:translateX(-50%);font-size:12px;"
        f"font-weight:600;color:{INK};white-space:nowrap'>Baseline {baseline:.0f}%</div>"
        f"<div style='position:absolute;left:{x(goal / 100)};top:12px;height:56px;border-left:2px dashed {INK};'></div>"
        f"<div style='position:absolute;left:{x(goal / 100)};top:-6px;transform:translateX(-50%);font-size:12px;"
        f"font-weight:600;color:{INK};white-space:nowrap'>Goal {goal:.0f}%</div>"
        f"{college_mark}{ticks}</div>")


# ---------------------------------------------------------------- sections
def goal_section(snapshot: dict | None, scope: str | None = None, scope_name: str | None = None,
                 banner: bool = True) -> bool:
    """Four tiles and the goal bar for the goal cohort (Fall 2024). Returns False
    (and draws nothing) when the snapshot carries no completion figures."""
    cfg = settings(snapshot)
    if not has_completion(snapshot):
        return False
    goal_cohort, goal, base = cfg["goal_cohort"], cfg["goal_pct"], cfg["baseline_pct"]
    gy, fall = cfg.get("goal_year"), _fall(cfg["goal_cohort"])
    b = block(snapshot, goal_cohort, scope)
    where = "" if scope is None else f" · {html.escape(scope_name or scope)}"
    if banner:
        st.markdown(_banner("Students First Framework: five-year completion",
                            f"Cerritos College · Goal: {goal:.0f}% of students complete within five years by "
                            f"spring {gy}{where}"), unsafe_allow_html=True)
    if not b:
        st.info(f"No {goal_cohort} completion figures for {scope_name or scope} in this data.")
        return True
    n, k = b.get("n"), b.get("completed")
    rate = _pct(k, n)
    who = f"{goal_cohort} cohort"          # the banner already names the LCP
    c1, c2, c3, c4 = st.columns(4)
    if rate is None:
        c1.markdown(_tile("5-year completion to date", WITHHELD[0], WITHHELD[1], GRAY), unsafe_allow_html=True)
        c2.markdown(_tile(f"More completers needed for {goal:.0f}%", WITHHELD[0], WITHHELD[1], GRAY),
                    unsafe_allow_html=True)
    else:
        c1.markdown(_tile("5-year completion to date", f"{rate:.1%}", f"{k:,} of {n:,} · {who}",
                          RED if rate * 100 < base else NAVY,
                          f"Students who started in Fall {fall} and have already earned a degree or certificate or "
                          f"completed 60+ degree-applicable units. It keeps rising until spring {gy}."),
                    unsafe_allow_html=True)
        c2.markdown(_tile(f"More completers needed for {goal:.0f}%", f"{needed(b, goal):,}", f"by spring {gy}"),
                    unsafe_allow_html=True)
    for col, key, label, tip in [
        (c3, "active_this_year", "Active this year",
         "Attempted degree-applicable units this academic year (summer and fall onward). The student-level file has "
         "no current-term enrollment flag, so this counts students with new units attempted this year."),
        (c4, "units_45", "Completed 45+ units",
         "Completed 45 or more degree-applicable units so far, including those who have completed."),
    ]:
        v = b.get(key)
        if v is None:
            col.markdown(_tile(label, WITHHELD[0], WITHHELD[1], GRAY), unsafe_allow_html=True)
        else:
            col.markdown(_tile(label, f"{v:,}", f"{v / n:.0%} of the {who}", NAVY, tip), unsafe_allow_html=True)
    if rate is not None:
        college = None
        if scope is not None:
            cb = block(snapshot, goal_cohort)
            college = _pct((cb or {}).get("completed"), (cb or {}).get("n"))
        st.markdown(_goal_bar(rate, base, goal, f"{goal_cohort} cohort, to date", college), unsafe_allow_html=True)
        st.caption(f"The {base:.0f}% baseline and {goal:.0f}% goal are five-year rates. The {goal_cohort} cohort's "
                   f"five-year rate is in progress: it counts every completer so far and will keep rising until "
                   f"spring {gy}." + (" ▲ College marks the whole college." if college is not None else ""))
    return True


def cohort_completed(snapshot: dict | None, cohort: str, scope: str | None = None,
                     scope_name: str | None = None) -> bool:
    """'X of the N students who started in Fall YYYY have completed so far', with the
    0-100% bar, the goal line, and how many more need to complete."""
    cfg = settings(snapshot)
    if not has_completion(snapshot):
        return False
    b = block(snapshot, cohort, scope)
    goal = cfg["goal_pct"]
    fall = _fall(cohort)
    as_of = _as_of(snapshot)
    who = "" if scope is None else f" in {html.escape(scope_name or scope)}"
    if not b or b.get("completed") is None or not b.get("n"):
        msg = ("Withheld: too few students to report safely." if b and b.get("n")
               else "No completion figures for this group yet.")
        st.markdown(f"<div style='border:1px solid {BORDER};border-radius:10px;padding:1rem 1.2rem;background:white;"
                    f"color:{GRAY};margin-bottom:1rem;'>Completed so far · {html.escape(cohort)}{who}: {msg}</div>",
                    unsafe_allow_html=True)
        return True
    n, k = b["n"], b["completed"]
    rate = k / n
    yrs_in = (as_of - dt.date(fall, 8, 15)).days / 365.25
    yrs = round(yrs_in)
    stage = ("in their first term" if yrs_in < 0.5 else
             f"about {yrs} year{'s' if yrs != 1 else ''} into their five years")
    left = fall + 5 - as_of.year
    need = needed(b, goal)
    if left > 0:
        reach = (f"To reach the goal, <b>{need:,} more</b> of these students need to complete in the next "
                 f"{left} year{'s' if left != 1 else ''}." if need else "These students have reached the goal.")
    else:
        reach = f"Their five-year mark has passed. {'They reached the goal.' if not need else f'{need:,} short of the goal.'}"
    parts = [("degree", "earned a degree"), ("certificate", "earned a certificate (no degree)"),
             ("units_60", "completed 60+ units (no award yet)")]
    how = " · ".join(f"{b[f]:,} {txt}" if b.get(f) is not None else f"{txt}: withheld" for f, txt in parts)
    st.markdown(
        f"<div style='border:1px solid {BORDER};border-radius:10px;padding:1rem 1.2rem 0.9rem 1.2rem;"
        f"background:white;margin-bottom:1rem;'>"
        f"<div style='font-size:1.45rem;font-weight:600;color:{INK};line-height:1.35'>{k:,} of the {n:,} students"
        f"{who} who started in Fall {fall} have completed so far.</div>"
        f"<div style='font-size:0.85rem;color:{GRAY};margin:0.6rem 0 1rem 0'>As of {as_of:%B} {as_of.day}, "
        f"{as_of.year} these students are {stage}. Their five-year mark is spring {fall + 5}.</div>"
        f"<div style='font-size:15px;color:{GRAY}'>That is <b style='color:{INK}'>{rate:.0%}</b>. "
        f"The goal is <b style='color:{INK}'>{goal:.0f}%</b> by spring {fall + 5}.</div>"
        f"<div style='position:relative;height:30px;background:rgba(128,128,128,.16);border-radius:6px;"
        f"margin:10px 0 28px 0'>"
        f"<div style='width:{rate * 100:.1f}%;min-width:3px;height:100%;background:{NAVY};border-radius:6px'></div>"
        f"<div style='position:absolute;left:{goal}%;top:-6px;height:42px;border-left:2px dashed {INK}'></div>"
        f"<div style='position:absolute;left:{goal}%;top:40px;transform:translateX(-50%);font-size:13px;"
        f"color:{INK}'>Goal {goal:.0f}%</div>"
        f"<div style='position:absolute;left:0;top:40px;font-size:13px;color:{GRAY}'>0%</div>"
        f"<div style='position:absolute;right:0;top:40px;font-size:13px;color:{GRAY}'>100%</div></div>"
        f"<div style='font-size:15px;color:{INK}'>{reach}</div>"
        f"<div style='font-size:0.8rem;color:{GRAY};margin-top:0.4rem'>How they completed: {how}.</div></div>",
        unsafe_allow_html=True)
    return True
