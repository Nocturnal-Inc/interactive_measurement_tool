# Head & Ear Measurement Distribution & Product Fit Coverage Tool

A browser-based anthropometric analysis tool for visualizing how product designs fit across the U.S. adult population using statistical distributions of human head and ear dimensions.

## Overview

This tool is designed for **product engineers, ergonomists, and designers** working on respiratory protection equipment, headwear, or other head-mounted devices. It enables rapid assessment of population fit coverage by visualizing how a product's design dimensions align with U.S. population anthropometrics — with particular emphasis on bizygomatic breadth (face width) as the primary constraint for mask-type products.

## Files

| File | Description |
|------|-------------|
| `Measurement_Tool_Full.html` | Comprehensive population distribution and product fit analysis tool |
| `Measurement_Tool_Flex.html` | Simplified interactive mask flex geometry visualizer |

Both files are standalone HTML — open directly in a browser, no build step or server required.

## Features

### Full Tool (`Measurement_Tool_Full.html`)

- **Distribution Curves** — Gaussian PDF/CDF visualizations for 6 key head/ear dimensions, separated by sex (male/female)
- **Product Fit Coverage** — Enter product min/max ranges to calculate what percentage of the population is covered per dimension
- **Gap Callouts** — Highlights uncovered population ranges for each measurement
- **Mask Geometry Analysis** — Groove flex demand, conformance gap, and face contact zone charts across bizygomatic breadth percentiles
- **Overall Fit Score** — Weighted population fit gauge combining all dimensions, with adjustable dimension weights

**Measured Dimensions:**
1. Cranial Circumference
2. Ear Height
3. Tragus-to-Tragus (Front Arc)
4. Mastoid-to-Mastoid (Rear Arc)
5. Bizygomatic Breadth *(NIOSH primary dimension)*
6. Mask Arc Flex *(derived from BZ)*

### Flex Tool (`Measurement_Tool_Flex.html`)

- **Top-Down Face Cross-Section** — Real-time SVG visualization of head geometry
- **Interactive Controls** — Adjust cranial circumference, BZ width, skull depth, mask width, and flex/pivot angle
- **Cross-Linked Parameters** — Lock BZ or skull depth while changing circumference; values update via binary search
- **Population Percentile Cards** — Static comparison views at P5, P35, P65, and P95 bizygomatic breadth

## Data Sources

Anthropometric data is drawn from the following surveys:

- **NIOSH 2005** — "Head-and-Face Anthropometric Survey of U.S. Respirator Users" (N=3,997, weighted to U.S. workforce) — *primary source*
- **NIOSH 2003** — General anthropometric survey
- **FAA AM-93-10 (1993)** — Aviation anthropometrics
- **German Longitudinal Ear Study (2007)** — Ear dimension norms

**Key Reference Values (Bizygomatic Breadth):**

| | P5 | P50 | P95 |
|---|---|---|---|
| Male | 13.2 cm | 14.35 cm | 15.5 cm |
| Female | 12.4 cm | 13.51 cm | 14.6 cm |

## Technology Stack

- **HTML5 / CSS3 / JavaScript (ES6+)** — No framework dependencies
- **D3.js v7.8.5** — SVG-based data visualizations (loaded from CDN)
- **Google Fonts** — DM Serif Display, DM Mono, DM Sans

## Usage

1. Open `Measurement_Tool_Full.html` in a modern browser
2. Enter your product's min/max dimension ranges in the controls bar
3. Observe coverage percentages and gap callouts across the population distribution
4. Review the mask geometry section for flex and conformance analysis
5. Adjust dimension weights in the Overall Fit section to reflect design priorities

For geometry exploration, open `Measurement_Tool_Flex.html` and interactively adjust head and mask parameters to visualize fit at different population percentiles.
