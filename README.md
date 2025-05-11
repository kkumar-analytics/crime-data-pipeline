# LAPD Crime Data Pipeline Project

This is a full-stack data pipeline project built as a portfolio to demonstrate end-to-end data engineering and analytics skills using modern tools and best practices. The dataset used includes Los Angeles Police Department (LAPD) crime reports and code mappings. The pipeline processes data from raw ingestion to analytics and reporting.

---

## 📐 Data Model & ERD

The Snowflake data warehouse uses a star schema centered around the `fact_crime` table. Key design features include:

- Surrogate keys across all dimension tables
- Slowly Changing Dimensions (Type 2) where applicable
- Bridge tables for many-to-many relationships (e.g., crime ↔ MOCODE)

### Entity-Relationship Diagram (ERD)

You can view the full data model:

- [📄 PDF version](docs/lapd_data_model.pdf)
- [💻 Editable dbdiagram.io file](data_model/lapd_star_schema.dbml)

This diagram captures the fact and dimension tables, bridge relationships, and final reporting tables derived via dbt.

---

## 🔧 Project Architecture

```
CSV → Python (Data Loader) → Snowflake (Raw + Star Schema)
    → dbt (Transformations, SCD2, Incremental Models, Seeds, Tests)
    → Elementary (Data Quality & Testing Observability)
    → Airflow (Orchestration via Astro CLI)
    → Looker (BI Dashboards)
```

---

## 🧱 Snowflake Schema Design (Star Schema)

### Dimension Tables

* **dim\_area**: Area code and name (25 police reporting districts).
* **dim\_crime\_code**: Crime codes with detailed description and category.
* **dim\_location**: Geographical location info, cross streets, lat/lon.
* **dim\_mocode**: Behavioral patterns associated with the crime (multi-valued, normalized via bridge).
* **dim\_premise**: Type of premises where the crime occurred.
* **dim\_status**: Status of the crime (e.g., Cleared, Open).
* **dim\_time**: Date/time breakdown for fact partitioning and seasonal trends.
* **dim\_victim**: Victim demographics, including gender, descent, and age group.
* **dim\_weapon**: Weapon used in the crime.

### Bridge Table

* **bridge\_crime\_mocode**: Connects crimes to one or more modus operandi codes (many-to-many).

### Fact Table

* **fact\_crime**: Central grain is one record per crime report (`dr_no`). Links to all dimensions via surrogate keys. Contains measures such as:

  * Number of victims
  * Domestic violence flag
  * Crime occurrence timestamp

### Reporting Tables (for BI Layer)

* `area_monthly_crime_summary`
* `crime_code_seasonality`
* `location_crime_density`
* `victim_demographics_summary`
* `weapon_type_distribution`

---

## ⚙️ Data Pipeline Components

### Ingestion

* Python script reads LAPD CSV data.
* Uploads to Snowflake using the Snowflake Connector.
* Supports incremental loading and duplicate handling.

### Transformation with dbt

* All raw tables modeled as staging (`stg_*`), then transformed to dimension/fact layers.
* SCD Type 2 implemented for dimension changes (e.g., `dim_status`, `dim_crime_code`).
* Incremental load logic applied to fact and some dimensions.
* `seeds/` used for static reference data (e.g., `vict_descent` codes).

### Testing and Observability

* Built-in `dbt tests` for schema and data validation.
* [Elementary](https://elementary-data.github.io/) used for:

  * Test result lineage and alerts
  * Data freshness
  * Run history & coverage

### Orchestration

* [Astro CLI](https://docs.astronomer.io/astro/cli/overview) used to run DAGs locally.
* Orchestrates Python ingest job, dbt transformations, and tests.

### Reporting with Looker

* Dashboards built using the final reporting tables.
* Use cases include crime hotspots, weapon trends, and victim demographics.

---

## 📁 Project Structure

```
├── data_loader/             # Python scripts to load CSV into Snowflake
├── dbt_lapd_crime/          # dbt Core project
│   ├── models/
│   │   ├── staging/
│   │   ├── dimensions/
│   │   ├── facts/
│   │   ├── bridge/
│   │   ├── reporting/
│   ├── seeds/
│   ├── snapshots/
│   └── tests/
├── airflow/                 # DAG to orchestrate loading & transformations
├── dashboards/              # Looker dashboard definitions (if included)
└── README.md
```

---

## 📊 Sample Use Cases

* How does weapon usage vary by crime type?
* What are the trends in victim demographics over time?

---

## 🛠️ Tech Stack

| Layer             | Tool/Service                 |
| ----------------- | ---------------------------- |
| Storage & Compute | Snowflake                    |
| Orchestration     | Apache Airflow (Astro CLI)   |
| Transformation    | dbt Core                     |
| Data Validation   | Elementary Data              |
| Ingestion         | Python + Snowflake Connector |
| Visualization     | Looker                       |
