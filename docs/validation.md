# Validation record

Authoring date: 4 November 2026.

| Check | Outcome | Scope |
|---|---|---|
| Python unit tests | 16 passed | Real source controls, weighted rates, inclusive employment, pp gaps and malformed inputs |
| Source snapshot | Passed | SHA-256, 63 unique rows per table, correct 2021 dates and matching names |
| Geography coverage | Passed | 61 MSOAs match exactly across 3 tables and official polygons |
| Reconciliation | Recorded | Published city count differences retained for all 6 headline counts |
| DOM interaction checks | Passed | 183 area/indicator combinations, page navigation, keyboard selection, sorting, search, empty results and CSV output |
| Power BI schema checks | Passed | 22 JSON/project files against Microsoft schemas; all visual column/measure references resolve |
| SQLite execution | Passed | All source inserts, constraints and views executed locally |
| Static chart preview | Rendered from SQL outputs | Separate analytical preview, not an HTML or Power BI screenshot |
| Native browser layout | Not verified | Local browser could not launch; cloud browser does not permit local file navigation |
| Power BI Desktop | Not verified | No native Desktop execution; opening, Power Query refresh, DAX and visual rendering require a Windows check |
| SQL Server runtime | Not verified | Setup script generated; it has not been executed against SQL Server |

## Independent source spot checks

- Liverpool 001: 1,205 residents aged 65+ out of 8,039 residents; 943 socially rented households out of 3,413 households; 3,546 employed nonstudents plus 97 employed students out of 6,463 residents aged 16+.
- Liverpool published TS007A population: 486,089. Sum of the 61 MSOA rows: 486,072. Difference: −17, retained in the reconciliation.
- Liverpool social renting: 54,758 / 207,491 = 26.3905%, shown as 26.4%.
- The default report selection is Liverpool 024, with a social-renting share displayed as 55.2%.

## Controls deliberately tested

Fail on modified snapshot hashes, duplicate keys, missing areas, conflicting names, wrong dates, blank/negative/fractional counts, zero denominators, numerators above denominators and duplicate boundaries. Accept zero numerators. Confirm weighted pooling differs from an unweighted mean of area rates. Confirm students in employment are included without adding overlapping source subtotals.

## Rebuild and CI

The workflow tests Python 3.11, 3.12 and 3.13, then rebuilds the analysis, HTML, Power BI files and SQL Server script and checks for unexpected diffs. A separate Node 22 job exercises the report DOM. See the repository Actions tab for the actual run status; the presence of a workflow file alone is not evidence that CI ran.

## Manual checks still needed

Open the HTML in a desktop and mobile browser and inspect layout, keyboard focus and downloaded CSVs. Open the native Power BI project and follow its source-value checklist. Run `sql/sql_server_setup.sql` in a **new empty** SQL Server database and reconcile `neighbourhood_comparison` with the CSV export before claiming SQL Server runtime validation.
