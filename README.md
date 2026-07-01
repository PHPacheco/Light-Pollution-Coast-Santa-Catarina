# Light Pollution on the Coast of Santa Catarina

Final project for the Image Processing course.

Authors: Pedro Pacheco and Carlos Soler.

## Assignment

Given a dataset of satellite night-light images, the team should choose and implement a classifier using TensorFlow, Keras, or scikit-learn to investigate spatial change and growth patterns. The project has an exploratory/research character and should connect image-processing techniques with topics discussed in the course.

## Project Goal

This project investigates whether artificial light at night appears close to aquatic environments in three coastal cities of Santa Catarina, Brazil:

- Florianopolis
- Balneario Camboriu
- Itajai

The work adapts the assignment into an exploratory remote-sensing workflow focused on coastal light pollution. Instead of training a supervised neural network, the project uses an image-processing classifier/pipeline based on water segmentation, VIIRS night-light radiance, continuous gradients, qualitative exposure classes, and visual comparison between cities.

## Why It Matters

Artificial light at night can negatively affect coastal and aquatic ecosystems. In expanding metropolitan and coastal areas, urban lighting, ports, roads, tourism infrastructure, and vertical development can increase nighttime light exposure over beaches, bays, rivers, channels, and estuaries.

Possible ecological impacts include changes in orientation, feeding, reproduction, migration, predator-prey interactions, and biological cycles of aquatic and coastal organisms.

## What Was Built

The repository contains a complete image-processing workflow:

1. Satellite imagery and reference images were collected for the selected cities.
2. Water and land were separated using Sentinel-2 and MNDWI.
3. VIIRS night-light radiance was applied over the water mask.
4. Exposure maps were generated with a continuous gradient.
5. A smoother gradient version was created to reduce visible satellite-cell boundaries.
6. The three cities were compared visually and qualitatively.
7. A relative ecological-risk layer was added to connect light exposure, marine buffers, productivity, habitat proxies, and fauna sensitivity.
8. A final report was produced with methodology, model architecture, classification, tests, code explanations, inputs, outputs, and result discussion.

## Ecological-Risk Roadmap

### Summary

The project should evolve from a map of artificial light over water into an analysis of **coastal ecological risk**. The best strategy is to keep VIIRS/Black Marble as the main quantitative source and use the images already collected as visual support, validation material, and final communication outputs.

The recommended index is:

```text
risco_ecologico = exposicao_luminosa * presenca_fauna * sensibilidade * fator_habitat
```

It can be calculated by city, spatial cell, or marine buffer.

### Priority 1: Essential Core

Status: **mostly implemented with local proxies**.

- **Implemented:** Keep VIIRS/Black Marble-derived layers as the main base for `exposicao_luminosa`.
- **Implemented:** Create marine buffers by city: `0-1 km`, `1-5 km`, `5-10 km`, `10-30 km`.
- **Implemented:** Aggregate by buffer:
  - mean relative radiance;
  - P90 relative radiance as a robust high-light metric;
  - exposed water area;
  - high-risk water area.
- **Implemented:** Represent marine fauna presence with OBIS-derived weights when available, with local fallback weights for reproducibility:
  - copepods/zooplankton;
  - benthic invertebrates;
  - coastal fish;
  - sea turtles;
  - seabirds.
- **Implemented:** Generate a comparative table for Florianopolis, Balneario Camboriu, and Itajai in `Data/ecological-risk/ecological_risk_metrics.csv`.
- **Implemented:** Replace the original fauna-only proxy with `Data/ecological-risk/obis_fauna_weights.csv`, generated from OBIS counts and AquaMaps fallback where OBIS has too few local records.

### Priority 2: Stronger Ecological Relationship

Status: **implemented as a defensible proxy model; real environmental datasets are still pending**.

- **Pending:** Add GEBCO bathymetry to distinguish shallow and deep waters.
- **Pending:** Add Bio-ORACLE or OceanColor attenuation data, such as `Kd` or an equivalent optical variable.
- **Implemented as proxy:** Create a simple relative bottom-light estimate:

```text
exposicao_fundo_relativa = radiancia_viirs * exp(-Kd * profundidade)
```

In the current implementation, `Kd` and depth are relative proxies derived from the existing water mask and distance from shore.

- **Implemented:** Create ecological weights by group:
  - high: copepods/zooplankton, benthic invertebrates, sea turtles;
  - medium: coastal fish, seabirds;
  - contextual: cetaceans and southern right whale should be treated as sensitive habitat, not direct visual-threshold impact.
- **Implemented:** Generate overlay-style maps showing:
  - light over water;
  - higher relative-risk areas;
  - habitat/fauna sensitivity proxies.

### Priority 3: Environmental Enrichment and Defense

Status: **implemented with reproducible fallbacks**.

- **Implemented:** Cross results with protected-area layers:
  - coastal/marine protected areas;
  - APA da Baleia Franca;
  - REBIO Marinha do Arvoredo, when applicable.
- **Implemented:** Use chlorophyll or primary productivity as a feeding-area proxy. `fetch_chlorophyll_data.py` first tries ERDDAP/NOAA chlorophyll-a and, if network/data are unavailable, generates a local primary-productivity layer from the water mask and distance from shore.
- **Implemented:** Use AquaMaps only if OBIS has too few local records for a group.
- **Implemented:** Load protected-area geometries from `Data/ecological-risk/protected_areas/protected_areas_catalog.csv`, with automatic preference for external GeoJSON files such as `protected_areas.geojson`, `cnuc_sc.geojson`, or `cnuc_mma.geojson`.
- **Implemented:** Use current images to:
  - demonstrate water/land separation;
  - create interpretable maps for reports;
  - compare urban lighting patterns;
  - validate whether VIIRS-derived results make visual sense;
  - strengthen the image-processing part required by the course.
- **Deferred:** ERA5/clouds and World Atlas sky brightness, because they add complexity and are not essential for the first ecological-risk version.

### Use of Current Images

The current images should be used as support layers, not as the strongest quantitative source.

They are useful to:

- visually demonstrate water/land separation;
- create interpretable report maps;
- compare urban lighting patterns;
- validate whether VIIRS results make visual sense;
- strengthen the image-processing component required by the course.

They should not fully replace VIIRS/Black Marble when the objective is to measure light intensity, because visual images usually do not preserve calibrated radiance, standardized spatial scale, reliable georeferencing, or temporal comparability.

### Tests and Acceptance Criteria

- **Implemented:** The generated report presents a table by city and buffer with light and ecological-risk metrics.
- **Implemented:** The risk index produces relative values comparable across the three cities.
- **Implemented:** The maps show where artificial light, water, and ecological sensitivity coincide.
- **Implemented:** The reports state that the index measures relative risk/proxy, not proven biological causality.
- **Implemented:** Current images are used as visual support while VIIRS/Black Marble-derived layers remain the quantitative basis.
- **Implemented:** Priority 3 reports explicitly identify whether productivity came from ERDDAP chlorophyll-a or local fallback, and whether protected-area limits came from CSV fallback or external GeoJSON.

### Assumptions

- The project remains focused on Florianopolis, Balneario Camboriu, and Itajai.
- The first ecological-risk version prioritizes simplicity and methodological defensibility.
- OBIS should be the first real fauna dataset integrated; AquaMaps is a fallback.
- The index is relative, not an absolute measure of biological impact.
- `AGENTS.local.md` exists locally, is updated with project state, and is ignored by Git.

## Main Result

The maps indicate that all three cities have artificial night light close to aquatic environments.

- Florianopolis shows the largest apparent exposed water extent, mainly around bays and the central strait.
- Balneario Camboriu shows concentrated exposure along the verticalized tourist waterfront and the Camboriu River mouth.
- Itajai shows concentrated exposure around the port area and the Itajai-Acu channel/river mouth.

![Smooth gradient comparison](Images/comparisons/comparison-cities-smooth-gradient.png)

## Individual Smooth Gradient Outputs

### Florianopolis

![Florianopolis smooth gradient](Images/smooth-gradient/florianopolis-smooth-gradient.png)

### Balneario Camboriu

![Balneario Camboriu smooth gradient](Images/smooth-gradient/balneario-camboriu-smooth-gradient.png)

### Itajai

![Itajai smooth gradient](Images/smooth-gradient/itajai-smooth-gradient.png)

## Repository Structure

```text
.
|-- Article.pdf
|-- README.md
|-- Relatorio_Completo_Degrade_Suave.docx
|-- collect_sentinel_water_images.py
|-- download_viirs_night_lights.py
|-- water_land_separation.py
|-- water_light_exposure.py
|-- city_comparison.py
|-- generate_smooth_gradient.py
|-- ecological_risk_analysis.py
|-- fetch_obis_data.py
|-- fetch_chlorophyll_data.py
|-- protected_areas_overlay.py
|-- Data/
|   `-- ecological-risk/
|       |-- ecological_risk_metrics.csv
|       |-- obis_fauna_weights.csv
|       |-- chlorophyll/
|       `-- protected_areas/
|-- EcologicalRiskImages/
`-- Images/
    |-- input/
    |-- mndwi/
    |-- water-masks/
    |-- viirs-water/
    |-- exposure-gradient/
    |-- smooth-gradient/
    |-- comparisons/
    `-- reference/
```

## Image Outputs

- `Images/input/`: original day and night reference images.
- `Images/mndwi/`: MNDWI visualizations used to support water identification.
- `Images/water-masks/`: binary water masks.
- `Images/viirs-water/`: VIIRS night-light radiance over water.
- `Images/exposure-gradient/`: continuous gradient exposure maps.
- `Images/smooth-gradient/`: smoothed gradient maps for each city.
- `Images/comparisons/`: side-by-side city comparisons.
- `Images/reference/`: reference images used during development.

## How To Reproduce The Main Outputs

The Google Earth Engine scripts require an authenticated Earth Engine environment and the project id configured in `.env`.

Create `.env` from `.env.example` and set:

```text
EARTH_ENGINE_PROJECT_ID=your-google-cloud-project-id
```

Generate water/land and VIIRS layers:

```bash
python water_land_separation.py
python water_light_exposure.py
```

Generate the city comparison:

```bash
python city_comparison.py
```

Generate the smoother gradient images:

```bash
python generate_smooth_gradient.py
```

Optionally refresh Priority 3 environmental inputs:

```bash
python fetch_obis_data.py
python fetch_chlorophyll_data.py
```

Generate the ecological-risk extension:

```bash
python ecological_risk_analysis.py
```

This creates step-by-step outputs in:

```text
EcologicalRiskImages/
|-- 01-light-exposure/
|-- 02-marine-buffers/
|-- 03-habitat-and-bottom-light/
|-- 04-ecological-risk-index/
|-- 05-comparisons/
`-- 06-protected-areas/
```

The generated metrics are saved to `Data/ecological-risk/ecological_risk_metrics.csv`, the productivity metadata are saved to `Data/ecological-risk/chlorophyll/chlorophyll_sources.csv`, protected-area catalog inputs are under `Data/ecological-risk/protected_areas/`, and the explanation/validation reports are saved under `Reports/`.

## Final Report

The final report used as project base is:

```text
Relatorio_Completo_Degrade_Suave.docx
```

It includes the problem description, dataset setup, preprocessing, model/pipeline architecture, calibration/training discussion, classification, tests, source-code explanations, input/output demonstrations, and discussion of the results.
