# Source register

Source snapshot retrieved **4 November 2026**. Observation date: **21 March 2021**. Exact retrieval timestamps, archive hashes, member hashes, subset hashes and download URLs are in [`data/raw/provenance.json`](../data/raw/provenance.json).

| Source | Publisher | Use |
|---|---|---|
| [TS007A: age in five-year bands](https://www.nomisweb.co.uk/datasets/c2021ts007a) | ONS via Nomis | Population and residents aged 65+ |
| [TS054: tenure](https://www.nomisweb.co.uk/datasets/c2021ts054) | ONS via Nomis | All households and social renting |
| [TS066: economic activity](https://www.nomisweb.co.uk/datasets/c2021ts066) | ONS via Nomis | Residents aged 16+ and employed students/nonstudents |
| [Census bulk data](https://www.nomisweb.co.uk/census/2021/bulk) | ONS via Nomis | Downloadable national archives, with extracted Liverpool MSOA/LTLA and England rows |
| [MSOA 2021 boundaries, BGC V3](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V3/FeatureServer/0) | ONS Open Geography Portal | 61 matching polygons and representative coordinates; 2024 maintenance release of 2021 geography |

## Interpretation references

- [ONS TS066 definition and quality notice](https://www.ons.gov.uk/datasets/TS066/editions/2021/versions/6): employment includes both student and nonstudent categories; the Census labour-market context and definition limit comparison with current or LFS measures.
- [Census 2021 quality and methodology](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/methodologies/qualityandmethodologyinformationqmiforcensus2021): disclosure control can make tables non-additive.
- [Liverpool ward profiles](https://liverpool.gov.uk/council/key-statistics-and-data/ward-information/ward-profiles/) and [neighbourhood profiles](https://liverpool.gov.uk/council/key-statistics-and-data/ward-information/neighbourhood-profiles/): council reporting context only. No council internal figures or dashboards were copied.

This project uses the Nomis bulk extracts as its numerical source, not the linked ONS interactive page's output. Original archive metadata is retained where the archive provides it. Upstream sources may be revised; the checked-in snapshot and hashes identify exactly what this report used.

## Reuse and attribution

Code is MIT licensed. The ONS data and boundary products retain their original licensing; they are not relicensed under MIT.

Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

Contains OS data © Crown copyright and database right 2026. Contains National Statistics data © Crown copyright and database right 2026. See the [ONS geography licence guidance](https://www.ons.gov.uk/methodology/geography/licences/).

This is an independent portfolio demonstration, not an ONS or Liverpool City Council product or endorsement.
