# Cohort KPI Dashboard

The dashboard the president and other leaders open on their own to see
how Cerritos College is doing on its KPIs, cohort by cohort -- built
directly from the richer student-level data (persistence, retention,
course completion, awards, CTE units, demographics) rather than the
smaller, pre-aggregated KPI Weekly Report workbook.

## How this differs from the other two projects

- **kpi_dashboard** reads the pre-aggregated KPI Weekly Report workbook
  directly, with a manual upload each week. Public, GitHub + Streamlit
  Community Cloud.
- **student_data_tool** is the local-only tool that holds the real
  (de-identified) student-level data in a persistent database, and is
  where `aggregate_snapshot.json` gets produced. Never meant to leave
  your machine.
- **cohort_kpi_dashboard** (this project, folder name `student_kpi_dashboard`)
  is what the president and other leaders actually look at. It never
  touches student-level data itself -- it just renders whatever
  `aggregate_snapshot.json` is committed to this repo. Public, GitHub +
  Streamlit Community Cloud.

## Why this is safe to keep public

`aggregate_snapshot.json` contains nothing but computed rates, counts,
and percentages -- by cohort, by year, by LCP/major/ethnicity/gender.
No individual student ever appears in it. That's what makes it safe to
commit to this public repo, unlike the student-level data itself (which
never leaves `student_data_tool`, running locally).

## Refreshing the data

1. In `student_data_tool` (local, your machine only), load the latest
   student-level extract(s) as usual.
2. In that project's **KPI Dashboard** tab, click **Export aggregate
   snapshot for the public dashboard**. This writes `aggregate_snapshot.json`
   -- aggregate figures only, verified to contain no row-level data.
3. Copy that file into this project's folder (replacing the old one),
   named exactly `aggregate_snapshot.json` at the repo root.
4. Commit and push:
   ```bash
   git add aggregate_snapshot.json
   git commit -m "Refresh KPI snapshot"
   git push
   ```
5. Streamlit Community Cloud picks up the change automatically within a
   minute or two -- no redeploy step needed.

There's no live upload button in this app at all -- refreshing the data
is entirely a "replace one JSON file and push" step, which keeps this
repo's only path to new data a deliberate, visible commit you make
yourself.

## Local setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

If there's no `aggregate_snapshot.json` in the folder yet, the sidebar
will show made-up sample data instead so you can see how the dashboard
looks before your first real export.

## Deploying to Streamlit Community Cloud

```bash
git init
git add .
git commit -m "Initial cohort KPI dashboard"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

Then on [share.streamlit.io](https://share.streamlit.io): New app, point
it at this repo, branch `main`, file `app.py`, deploy. Once it's live,
share that URL with the president and anyone else who should see it --
no login setup, no local install needed on their end.

## Project structure

```
app.py                        Streamlit UI: institutional overview, cohort
                               journey, breakdown table -- all rendered
                               from aggregate_snapshot.json
aggregate_snapshot.json        Not present until your first export from
                               student_data_tool -- this is the only data
                               file this app reads, and the only thing you
                               ever need to update to refresh the dashboard
sample_data/                   Made-up sample snapshot, shown automatically
                               if aggregate_snapshot.json isn't present yet
requirements.txt                Python dependencies (just streamlit + pandas
                               -- no openpyxl, since this app never reads
                               a spreadsheet)
```

## Assumptions worth knowing about

- "Completed" for English/Math means *ever* completed as of whenever the
  student-level extract was pulled, not paced to a specific week the way
  the KPI Weekly Report's snapshots are.
- The units-completed milestone and CSEP/DPP metrics are broken out by
  academic year (Year 1, 2, 3...) directly from the student-level file's
  own per-year columns, since that file already carries each student's
  full multi-year history in one row -- unlike the KPI Weekly Report,
  which needs a separate upload for each year to build the same picture.
- Goals (target %) shown alongside each metric are copied from the KPI
  Weekly Report's own annual targets, so any gap between this dashboard's
  number and the official one is a data/methodology question, worth
  investigating rather than assuming either source is "right."
