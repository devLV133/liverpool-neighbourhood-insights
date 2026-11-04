# Power BI project

Open **LiverpoolInsights.pbip** in a Power BI Desktop version that supports PBIP/PBIR projects. Keep the adjacent `.Report` and `.SemanticModel` folders together.

1. Run `python analyse.py` from the repository root, or use the included processed CSVs.
2. Open the PBIP file. In **Transform data → Edit parameters**, set `DataFolder` to this checkout's absolute `data/processed` folder, for example `C:/Users/Sam/liverpool-neighbourhood-insights/data/processed`.
3. Apply changes and refresh. If asked about local file access, review the displayed folder.
4. Check the **Liverpool overview** page: 15.3% aged 65+, 26.4% socially rented households and 51.1% in employment among residents aged 16+.
5. On **Area comparison**, select Liverpool 001: age 65+ should be 15.0%, social renting 27.6%, and employment 56.4%. Clear the slicer to restore all 61 areas.
6. Compare the table and gap measures with `data/processed/neighbourhoods.csv` before using screenshots on a CV.

The disconnected Benchmarks table intentionally retains published city/country rates when a neighbourhood is selected. Multi-area selection measures sum counts before division. Never average the imported percentage columns to obtain a combined-area rate.

**Validation:** 22 report/project JSON files pass Microsoft's public schemas and all visual column/measure references resolve. Power BI Desktop opening, Power Query refresh, DAX execution and rendering have not been verified in the authoring environment. Schema validation is not a substitute for those checks.

The native report has 2 pages, 14 visuals and 13 DAX measures. The selectable polygon map is in the companion `reports/dashboard.html` report. Latitude/longitude are also imported for optional mapping in Desktop.
