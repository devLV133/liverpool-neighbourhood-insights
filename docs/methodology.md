# Methodology and indicator dictionary

## Scope

The observation date is **21 March 2021**. The analysis covers the 61 Liverpool Middle layer Super Output Areas (MSOAs) in the 2021 Census geography. MSOAs are statistical areas. They are not Liverpool's current wards or its 13 council neighbourhoods. The project title uses “neighbourhood” informally.

There is no time series. Retrieval in November 2026 does not make these current estimates. All comparison rates use the same Census reference period and published source definitions. National and city benchmarks are independently published rows, not unweighted averages of local percentages.

## Indicators

| Field | Numerator | Denominator | Source |
|---|---|---|---|
| `aged_65_share` | Sum of 65–69, 70–74, 75–79, 80–84 and 85+ counts | All usual residents in the same TS007A row | TS007A |
| `social_rented_share` | Published **Social rented** subtotal | All households in the same TS054 row | TS054 |
| `employed_share` | In employment excluding full-time students **plus** in employment among full-time students | All usual residents aged 16+ in the same TS066 row | TS066 |

Rates are stored as fractions (0–1) and displayed as percentages to one decimal place. A benchmark gap is `100 × (area share − benchmark share)`, in percentage points. Counts remain integers. Denominators are never borrowed from another Census table.

The source files contain a hierarchy of category totals and subtotals. Adding every numeric column would double-count people or households. The pipeline explicitly selects one subtotal or a set of disjoint categories. In particular, social rented is not added to its council and housing-association subcategories, and employment parent categories are not added to employee/self-employed children.

**Employment is not the headline 16–64 employment rate or the unemployment rate.** It includes everyone aged 16+, including older residents and students. Census labour-market definitions differ from Labour Force Survey definitions. The pandemic context, age mix and student populations limit causal or current-policy interpretations.

## Source matching and controls

1. Read official ONS boundary features and obtain the exact set of area codes.
2. Extract matching rows from each Nomis MSOA file; retain the published Liverpool LTLA and England rows separately.
3. Preserve original source column names and counts, archive/member hashes and extraction metadata.
4. Check file SHA-256, unique keys, period, complete coverage, names, integer counts, positive denominators and sensible numerator bounds.
5. Load one row per area into three SQLite source tables with constraints. Join one-to-one on area code.
6. Calculate indicators and benchmark gaps in SQL. Export CSVs and a JSON dataset for presentation.

The default build is fully offline. `fetch_data.py` is an explicit refresh operation, not a dashboard side effect. The pinned coverage check intentionally fails if the number of 2021 Liverpool MSOAs changes; investigate the release before accepting a different snapshot.

## Reconciliation and uncertainty

ONS applies disclosure controls to Census tables, which can make sums across small areas differ slightly from independently published larger-area totals. `reconciliation.csv` records these differences for every headline count. No source value is adjusted to force equality. “Checks passed” means the snapshot is structurally valid, not that every count is error-free or unperturbed.

Use sums of numerators divided by sums of denominators for a multi-area selection. The Power BI selection measures follow this rule. Dashboard city cards use the published Liverpool row, so selecting all MSOAs can produce a very small difference. No statistical-significance test or confidence interval is claimed.

## Mapping and interpretation

The offline SVG uses the official generalised coastline-clipped polygons. For display only, longitude is scaled by the cosine of Liverpool's latitude and north points up. This local projection is not used for distance, area or rate calculations. No third-party map tiles or geocoding requests are made. Polygon keys and analytical keys must match exactly.

Colour indicates the selected share, using its observed minimum and maximum. The legend changes with the indicator. All bar charts in the interactive report use a 0–100% scale. Area rankings are descriptive, not a composite deprivation measure, service-priority score or judgement about residents.

Before a real allocation decision, obtain contemporary service-use data, agree the decision with the responsible team, assess coverage and investigate differences. No resident-level data is used here.
