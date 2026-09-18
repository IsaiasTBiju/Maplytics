# Maplytics

**MACS Athena SWAN Undergraduate Research Bursary Project (2026)**

Analysing gendered urban inclusion in Dubai using geospatial computing.

## Overview

Maplytics computes a **Gender Inclusivity Score (GIUS)** for urban areas based on proxies including:
- Access to services (POI density)
- Public transport accessibility
- Walkability (street network density)

Scores are computed via spatial analysis in PostGIS, patterns are explored using
unsupervised ML clustering, and results are presented on an interactive dashboard.

## Project structure

- `pipeline/` — data processing, PostGIS spatial analysis, GIUS scoring, ML clustering
- `site/` — interactive map dashboard (deployed via GitHub Pages)
- `docs/` — methodology notes and write-up

## Status

🚧 Work in progress.