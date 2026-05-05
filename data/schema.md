# Data files

The interactive tools load their data from JSON in this directory. To swap a tool to a different dataset, change one `<script src>` line in the corresponding HTML file (e.g. swap `data/full/measurements.us-adult.js` for `data/full/measurements.pediatric.js`).

Each `.js` file is a thin shim that reads the matching `.json` and assigns it to a global. The `.json` is the canonical artifact — regenerate the `.js` whenever the JSON changes:

```bash
python3 -c "
raw = open('data/full/measurements.us-adult.json').read()
open('data/full/measurements.us-adult.js','w').write('window.IMT_DATA = ' + raw.rstrip() + ';\n')
"
```

## `data/full/measurements.*.json` — consumed by `Measurement_Tool_Full.html`

Top-level keys:

- **`measurements`** — array of 6 dimensions. Each entry: `{ id, name, unit, desc, male: {p5,p50,p95}, female: {p5,p50,p95}, productDefault: {min,max}, xRange: [lo,hi], isNiosh?, isMaskFlex? }`. The `id` must be referenced consistently elsewhere (`demographics`, `dimWeights`).
- **`demographics`** — `{ age: { "<bin>": { "<measId>": { male/female: {p5,p50,p95} } } }, ethnicity: {...} }`. Bins can be omitted; the renderer falls back gracefully.
- **`bzProfiles`** — array used by the bizygomatic NIOSH inspection widget. Each: `{ label, bz, colorVar }` where `colorVar` is a CSS custom-property name from `theme.css` (e.g. `"--female"`).
- **`bzCross`** — short array of cross-section breakpoints, `{ label, bz }`.
- **`mgState`** — initial mask-geometry slider values (object).
- **`mgControls`** — slider configs: `{ key, label, unit, min, max, step }`.
- **`dimWeights`** — `{ <measId>: weight }`. Used for combined-coverage computation.
- **`groupColors`** — `{ <groupKey>: { male: "#hex", female: "#hex" } }`. `groupKey` is `"total"`, an age-bin label, or an ethnicity label.

The `.js` shim assigns this object to `window.IMT_DATA`.

## `data/flex/profiles.*.json` — consumed by `Measurement_Tool_Flex.html`

- **`profiles`** — 4 percentile entries: `{ label, bz, colorVar }`. Drives the static thumbnail row.

The `.js` shim assigns this object to `window.IMT_FLEX_DATA`.
