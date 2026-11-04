-- Each source is one row per area. Never join category-level rows across sources.
CREATE VIEW area_indicators AS
SELECT a.area_code, a.area_name, a.area_type,
       p.population, p.aged_65_plus,
       h.households, h.social_rented,
       e.residents_16_plus,
       e.employed_nonstudents + e.employed_students AS employed,
       1.0 * p.aged_65_plus / NULLIF(p.population, 0) AS aged_65_share,
       1.0 * h.social_rented / NULLIF(h.households, 0) AS social_rented_share,
       1.0 * (e.employed_nonstudents + e.employed_students) / NULLIF(e.residents_16_plus, 0) AS employed_share
FROM areas a
JOIN age_counts p ON p.area_code = a.area_code
JOIN tenure_counts h ON h.area_code = a.area_code
JOIN employment_counts e ON e.area_code = a.area_code;

CREATE VIEW neighbourhood_comparison AS
SELECT n.*,
       100.0 * (n.aged_65_share - c.aged_65_share) AS aged_65_city_gap_pp,
       100.0 * (n.social_rented_share - c.social_rented_share) AS social_rented_city_gap_pp,
       100.0 * (n.employed_share - c.employed_share) AS employed_city_gap_pp,
       100.0 * (n.aged_65_share - e.aged_65_share) AS aged_65_england_gap_pp,
       100.0 * (n.social_rented_share - e.social_rented_share) AS social_rented_england_gap_pp,
       100.0 * (n.employed_share - e.employed_share) AS employed_england_gap_pp
FROM area_indicators n
CROSS JOIN (SELECT * FROM area_indicators WHERE area_code = 'E08000012') c
CROSS JOIN (SELECT * FROM area_indicators WHERE area_code = 'E92000001') e
WHERE n.area_type = 'MSOA';

-- Use denominators, not an unweighted mean of area percentages.
CREATE VIEW pooled_msoa_control AS
SELECT SUM(population) AS population, SUM(aged_65_plus) AS aged_65_plus,
       SUM(households) AS households, SUM(social_rented) AS social_rented,
       SUM(residents_16_plus) AS residents_16_plus, SUM(employed) AS employed,
       1.0 * SUM(aged_65_plus) / NULLIF(SUM(population), 0) AS aged_65_share,
       1.0 * SUM(social_rented) / NULLIF(SUM(households), 0) AS social_rented_share,
       1.0 * SUM(employed) / NULLIF(SUM(residents_16_plus), 0) AS employed_share
FROM area_indicators WHERE area_type = 'MSOA';
