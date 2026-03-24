# Meta Ad Creative Analyzer (MVP)

Local tool to analyze Meta ads from CSV files and detect which creatives are winning, with CPI as the primary KPI.

## Features

- Upload creative images/videos into a local creative library (SQLite + local file storage).
- Upload CSV with ad metrics and use auto column mapping (advanced mapping is optional/collapsed).
- Auto-calculate `CPM`, `CTR`, `CTI`, `CPI`.
- Match creatives using normalized ad names.
- AI vision tagging for matched creative assets:
  - images are analyzed directly
  - videos are analyzed via extracted keyframes
  - results are cached in SQLite and reused in the qualitative feature sheet
- Detect "win driver" based on decomposition:
  - `CPI = CPM / (1000 * CTR * CTI)`
- Show metrics table and creative previews.

## Quick Start

1. Create and activate a virtual environment:

```bash
cd /Users/lap60572/Documents/meta-ad-analyzer
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run app:

```bash
streamlit run app.py
```

## Recommended CSV Columns

Minimum required fields:

- `ad_name`
- `spend`
- `impressions`
- `clicks`
- `installs`

You can use other column names and map them in the UI.

## Creative Matching Rule

- Creative name comes from file name (without extension) at upload time.
- Tool normalizes names (lowercase, remove symbols, normalize spaces).
- Match key: `normalize(ad_name_from_csv) == normalize(creative_name_from_library)`.

## Data Storage

- Database: `data/creative_assets.db`
- Media files: `data/media/*`
- Column alias config: `data/column_aliases.json`
- Audit skill file (runtime): `/Users/lap60572/.codex/skills/Audit ad/meta-ads-creative-analyst.md`

## Skill Runtime

- Deployed builds should use the bundled project skill:
  - `skills/audit_ad/SKILL.md`
- Local builds can still override skill path with:

```bash
export AUDIT_AD_SKILL_PATH="/path/to/your/skill.md"
```

- App resolution order:
  - `AUDIT_AD_SKILL_PATH`
  - `skills/audit_ad/SKILL.md`
  - local fallback under `~/.codex/skills/Audit ad/...`

## Skill Integration (Audit ad)

- Tool reads `Audit ad` skill file at runtime and applies the rubric for:
  - `✅ WORK`, `⚠️ TRUNG BÌNH`, `❌ KHÔNG WORK`
  - `🚀 SCALE`, `❌ TẮT`, `⏳ CHỜ THÊM DATA`
- You can change the skill path via environment variable:

```bash
export AUDIT_AD_SKILL_PATH="/path/to/your/skill.md"
```

## AI Vision Tagging

Set your OpenAI API key before running the app:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

Optional:

```bash
export OPENAI_VISION_MODEL="gpt-4.1-mini"
```

Then in the `Qualitative Creative Analysis` section, open `AI Vision Tagging` and run:
- `Analyze matched creatives with AI`

The app will:
- analyze matched image assets directly with the OpenAI Responses API
- extract keyframes from matched videos and analyze those frames
- store the returned feature tags in `creative_assets.analysis_json`

## Render Deploy

- Blueprint file: `render.yaml`
- Current Render config is **stateless**:
  - app data is written to `/tmp/meta-ad-analyzer`
  - uploads / SQLite data are lost after restart or redeploy
- Start command on Render:
  - `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

Important:
- Actual Render deploy still requires this project to be pushed to a Git remote.
- The current local repo does not yet have a remote configured.

## Notes

- If installs or clicks are zero, some metrics may be empty (`NaN`).
- For best matching quality, keep CSV `ad_name` close to media file names.
