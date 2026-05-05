# Interactive Measurement Tools

Design and engineering tools for head anthropometry analysis and mask fit evaluation across diverse populations.

## Tools

### Population Distribution & Product Fit

`Measurement_Tool_Full.html`

Visualize population distributions across 6 head measurement dimensions with interactive D3.js charts. Input your product's design ranges to calculate weighted fit coverage, identify uncovered population gaps, and validate against NIOSH 2005 survey data.

**Dimensions analyzed:** Cranial Circumference, Ear Height, Tragus-to-Tragus Front Arc, Mastoid-to-Mastoid Rear Arc, Bizygomatic Breadth, and Mask Arc Flex.

### Face Cross-Section & Mask Flexibility

`Measurement_Tool_Flex.html`

Explore the geometric relationship between skull shape and mask dimensions with an interactive top-down cross-section view. Adjust cranial circumference, bizygomatic width, mask flex angles, and visualize wing panel gaps across population percentiles (P5, P35, P65, P95).

## Tech Stack

- **D3.js 7.8.5** — data visualization and interactive charts
- **Vanilla JavaScript / HTML5 / CSS3** — no frameworks, no build step
- Shared design tokens in `theme.css`

## Getting Started

No installation required. Open `index.html` in a browser to access both tools.

## Deployment

The site auto-deploys to AWS S3 + CloudFront via GitHub Actions on push to `main`.

The following GitHub secrets are required:

| Secret | Description |
|--------|-------------|
| `AWS_KEY` | AWS access key ID |
| `AWS_SECRET` | AWS secret access key |
| `S3_BUCKET` | S3 bucket name |
| `S3_BUCKET_REGION` | AWS region |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront distribution ID |

## Data Sources

- **NIOSH 2005** — Head-and-Face Anthropometric Survey (N=3,997) for bizygomatic breadth
- **FAA AM-93-10 (1993)** — cranial circumference measurements
- **Zhuang & Bradtmiller** — supplementary bizygomatic breadth data
- **Tollefson et al.** — ear height and related facial measurements

## Data Files

The Full tool's data is **derived from research CSVs** in `data/data_from_research_files/` (one file per measurement: head circumference, ear height, mastoid-to-mastoid, bizygomatic breadth). Each row is a study with `Mean`, `SD`, `Sample Size`, demographic columns. The build script pools studies per `(Region, Gender)` and emits `data/full/measurements.us-adult.json` plus a `.js` shim that the HTML loads via `<script src>` (no `fetch()` — works on `file://`).

To regenerate after editing the CSVs:

```bash
python3 scripts/build_data.py
```

The Flex tool's data file (`data/flex/profiles.us-adult.json`) is hand-edited.

See `data/schema.md` for the canonical data layout, units per file, and pooling math.
