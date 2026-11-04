import csv
import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from analyse import ROOT, CITY, AGE_TOTAL, EMP_NON, EMP_STUDENT, build_database, query, read_table, run


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.raw = Path(self.temp.name)/'raw'
        shutil.copytree(ROOT/'data/raw', self.raw)

    def tearDown(self):
        self.temp.cleanup()

    def change(self, table, edit):
        path = self.raw/(table+'.csv')
        with path.open(newline='') as f:
            reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
        edit(rows)
        with path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

    def test_real_snapshot_coverage_and_benchmarks(self):
        con,_,_=build_database(self.raw)
        self.addCleanup(con.close)
        self.assertEqual(con.execute('SELECT COUNT(*) FROM neighbourhood_comparison').fetchone()[0],61)
        r=dict(con.execute('SELECT * FROM area_indicators WHERE area_code=?',(CITY,)).fetchone())
        self.assertEqual(r['population'],486089)
        self.assertEqual(r['social_rented'],54758)
        self.assertAlmostEqual(r['social_rented_share'],54758/207491)

    def test_includes_employed_students_without_double_counting(self):
        con,_,_=build_database(self.raw);self.addCleanup(con.close)
        row=dict(con.execute("SELECT * FROM area_indicators WHERE area_name='Liverpool 001'").fetchone())
        # Independently checked against the original TS066 row: 3546 + 97.
        self.assertEqual(row['employed'],3643)
        self.assertEqual(row['residents_16_plus'],6463)
        self.assertAlmostEqual(row['employed_share'],3643/6463)

    def test_weighted_rollup_is_not_unweighted_average(self):
        con,_,_=build_database(self.raw);self.addCleanup(con.close)
        pooled=dict(con.execute('SELECT * FROM pooled_msoa_control').fetchone())
        self.assertAlmostEqual(pooled['aged_65_share'],74304/486072)
        mean=con.execute("SELECT AVG(aged_65_share) FROM area_indicators WHERE area_type='MSOA'").fetchone()[0]
        self.assertNotAlmostEqual(pooled['aged_65_share'],mean,places=5)

    def test_gap_is_percentage_points_using_published_benchmark(self):
        con,_,_=build_database(self.raw);self.addCleanup(con.close)
        row=dict(con.execute("SELECT * FROM neighbourhood_comparison WHERE area_name='Liverpool 001'").fetchone())
        self.assertAlmostEqual(row['social_rented_city_gap_pp'],100*(943/3413-54758/207491))

    def test_zero_numerator_is_valid(self):
        self.change('ts066',lambda rows: rows[0].update({EMP_NON:'0',EMP_STUDENT:'0'}))
        con,_,_=build_database(self.raw,False);self.addCleanup(con.close)
        row=con.execute('SELECT employed_share FROM area_indicators WHERE area_code=?',('E02001347',)).fetchone()
        self.assertEqual(row[0],0)

    def test_checksum_detects_changes(self):
        self.change('ts007a',lambda rows: rows[0].update({AGE_TOTAL:'9000'}))
        with self.assertRaisesRegex(ValueError,'checksum'):build_database(self.raw)

    def test_duplicate_keys_fail(self):
        self.change('ts007a',lambda rows: rows.append(rows[0].copy()))
        with self.assertRaisesRegex(ValueError,'duplicate'):build_database(self.raw,False)

    def test_missing_area_fails(self):
        self.change('ts054',lambda rows: rows.pop(0))
        with self.assertRaisesRegex(ValueError,'coverage'):build_database(self.raw,False)

    def test_wrong_period_fails(self):
        self.change('ts007a',lambda rows: rows[0].update(date='2022'))
        with self.assertRaisesRegex(ValueError,'period'):build_database(self.raw,False)

    def test_blank_count_fails(self):
        self.change('ts007a',lambda rows: rows[0].update({AGE_TOTAL:''}))
        with self.assertRaisesRegex(ValueError,'count'):build_database(self.raw,False)

    def test_fractional_or_negative_count_fails(self):
        for value in ['12.5','-1']:
            with self.subTest(value=value):
                self.change('ts007a',lambda rows: rows[0].update({AGE_TOTAL:value}))
                with self.assertRaisesRegex(ValueError,'count'):build_database(self.raw,False)

    def test_zero_denominator_fails(self):
        self.change('ts007a',lambda rows: rows[0].update({AGE_TOTAL:'0'}))
        with self.assertRaises(sqlite3.IntegrityError):build_database(self.raw,False)

    def test_numerator_above_denominator_fails(self):
        self.change('ts066',lambda rows: rows[0].update({EMP_NON:'1000000'}))
        with self.assertRaises(sqlite3.IntegrityError):build_database(self.raw,False)

    def test_conflicting_names_fail(self):
        self.change('ts054',lambda rows: rows[0].update(geography='Wrong name'))
        with self.assertRaisesRegex(ValueError,'names'):build_database(self.raw,False)

    def test_duplicate_boundary_fails(self):
        path=self.raw/'boundaries.geojson';geo=json.loads(path.read_text())
        geo['features'].append(geo['features'][0]);path.write_text(json.dumps(geo))
        with self.assertRaisesRegex(ValueError,'unique'):build_database(self.raw,False)

    def test_reconciliation_retains_disclosure_differences(self):
        p=run(self.raw,Path(self.temp.name)/'processed')
        population=next(r for r in p['reconciliation'] if r['measure']=='population')
        self.assertEqual(population,{'measure':'population','sum_msoa':486072,'published_city':486089,'difference':-17})
        self.assertEqual(p['census_date'],'2021-03-21')


if __name__=='__main__':unittest.main()
