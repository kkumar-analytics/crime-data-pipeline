{{ config(
    materialized='table',
    schema='mart_reporting',
    tags=['reporting', 'summary']
) }}

SELECT
    CASE
        WHEN dv.age BETWEEN 0 AND 10 THEN '0-10'
        WHEN dv.age BETWEEN 11 AND 20 THEN '11-20'
        WHEN dv.age BETWEEN 21 AND 30 THEN '21-30'
        WHEN dv.age BETWEEN 31 AND 40 THEN '31-40'
        WHEN dv.age BETWEEN 41 AND 50 THEN '41-50'
        WHEN dv.age BETWEEN 51 AND 60 THEN '51-60'
        WHEN dv.age BETWEEN 61 AND 70 THEN '61-70'
        WHEN dv.age BETWEEN 71 AND 80 THEN '71-80'
        WHEN dv.age BETWEEN 81 AND 90 THEN '81-90'
        WHEN dv.age > 90 THEN '91+'
        ELSE 'Unknown'
    END AS age_range,
    dv.sex AS victim_sex,
    dv.descent AS victim_descent,
    COUNT(*) AS incident_count
FROM
    {{ ref('fct_crime_events') }} AS fce
    JOIN {{ ref('dim_victim') }} AS dv ON fce.victims_id = dv.id
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
