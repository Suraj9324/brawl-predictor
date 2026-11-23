# Brawl Predictor

An ML system that predicts whether a Brawl Stars player will gain or lose trophies over their next 5 matches. It collects real game data from the official API, engineers features from battle history, trains an XGBoost classifier, and serves predictions through a dashboard.

Built as a companion to [Brawl Leaderboard](https://github.com/your-username/brawl-leaderboard) (data pipeline) and [Forgeblast](https://play.google.com/store/apps/details?id=com.forgeblastmobile.app&hl=fr) (production app). The narrative: I built the app, the data pipeline, and now the AI that predicts outcomes from that data.

## How it works

```
React dashboard  ──▶  FastAPI  ──▶  PostgreSQL
                         │
                    ML model (XGBoost)
                         │
                    Feature engineering
                         │
                    Brawl Stars API
```

You add players by tag. The system fetches their last 25 battles and profile from the Brawl Stars API. From that raw data, it engineers 25 features — win rates, streaks, trophy trends, brawler stats, mode diversity. An XGBoost classifier trained on historical data then predicts whether the player will gain or lose trophies in their next session.

The scheduler can run every few hours to accumulate more battle data over time. More data = better predictions.

## Setup

You'll need Python 3.11+, Node.js 18+, Docker (for Postgres), and a [Brawl Stars API key](https://developer.brawlstars.com/).

```bash
# Start Postgres
docker compose up -d

# Backend
cp .env.example .env   # add your API key
python -m venv venv
venv\Scripts\activate   # or source venv/bin/activate on Linux/Mac
pip install -r requirements.txt

# Start the API (creates tables on first run)
uvicorn api.main:app --reload --port 8000

# Frontend (separate terminal)
cd web
npm install
npm run dev
```

Frontend runs on `http://localhost:5174`, API on `:8000`. Vite proxies `/api` calls automatically.

## Collecting data & training

```bash
# Add players via the dashboard, or:
curl -X POST http://localhost:8000/api/players/ -H "Content-Type: application/json" -d "{\"tag\": \"#8YVRRJQYY\"}"

# Manually sync all tracked players (fetches latest battles)
curl -X POST http://localhost:8000/api/stats/sync

# Or via CLI
python -m pipeline.collector

# Train the model (needs ~10 players with 25+ battles each)
python -m model.train

# Evaluate
python -m model.evaluate

# Run the scheduler for continuous collection (every 2h)
python -m pipeline.scheduler
```

The model improves as you collect more data over time. With 10 players and one sync, you get ~70 training samples — enough for a first model. A few days of collection with 20+ players gives much better results.

## API

| Method | Endpoint | What it does |
|--------|----------|--------------|
| `POST` | `/api/players/` | Track a player `{ tag }` (also fetches battles) |
| `GET` | `/api/players/` | List tracked players |
| `GET` | `/api/players/:tag` | Player details + snapshots + recent battles |
| `DELETE` | `/api/players/:tag` | Stop tracking |
| `GET` | `/api/predict/:tag` | Predict trophy outcome (fetches fresh data first) |
| `GET` | `/api/predict/:tag/history` | Past predictions for a player |
| `GET` | `/api/stats/model` | Model metrics + feature importance |
| `GET` | `/api/stats/dashboard` | Overview stats (players, battles, predictions) |
| `POST` | `/api/stats/sync` | Manually trigger data sync for all players |
| `GET` | `/api/stats/sync-logs` | Sync history |

## Features used by the model

The classifier uses 25 engineered features, the most important ones being:

- **win_rate_25 / win_rate_10** — recent win rates over last 25 and 10 battles
- **trophy_ratio** — current trophies / highest trophies (how close to peak)
- **performance_trend** — slope of trophy changes (improving or declining)
- **mode_diversity** — how many different game modes the player uses
- **avg_trophy_change** — average trophies gained/lost per recent match
- **win/loss_streak** — current streak length
- **star_player_rate** — how often they're selected as star player
- **brawler-specific stats** — trophies, power, rank, win rate with their latest brawler

## Stack

**ML** — Python, XGBoost, scikit-learn, pandas, numpy
**Backend** — FastAPI, SQLAlchemy, PostgreSQL
**Frontend** — React, TypeScript, Vite, Tailwind CSS, Recharts, Framer Motion
**Pipeline** — httpx (async), APScheduler, Brawl Stars REST API
**Infra** — Docker Compose

## License

MIT
