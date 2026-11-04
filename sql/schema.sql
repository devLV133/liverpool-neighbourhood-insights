CREATE TABLE areas (
    area_code TEXT PRIMARY KEY,
    area_name TEXT NOT NULL,
    area_type TEXT NOT NULL CHECK(area_type IN ('MSOA', 'City', 'Country'))
);
CREATE TABLE age_counts (
    area_code TEXT PRIMARY KEY REFERENCES areas(area_code),
    population INTEGER NOT NULL CHECK(population > 0),
    aged_65_plus INTEGER NOT NULL CHECK(aged_65_plus BETWEEN 0 AND population)
);
CREATE TABLE tenure_counts (
    area_code TEXT PRIMARY KEY REFERENCES areas(area_code),
    households INTEGER NOT NULL CHECK(households > 0),
    social_rented INTEGER NOT NULL CHECK(social_rented BETWEEN 0 AND households)
);
CREATE TABLE employment_counts (
    area_code TEXT PRIMARY KEY REFERENCES areas(area_code),
    residents_16_plus INTEGER NOT NULL CHECK(residents_16_plus > 0),
    employed_nonstudents INTEGER NOT NULL CHECK(employed_nonstudents >= 0),
    employed_students INTEGER NOT NULL CHECK(employed_students >= 0),
    CHECK(employed_nonstudents + employed_students <= residents_16_plus)
);
