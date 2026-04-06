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
