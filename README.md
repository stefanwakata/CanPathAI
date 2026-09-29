# 🍁 CanPath AI — Canadian Immigration & Labour Market Agent

Agent conversationnel bilingue (FR/EN) qui croise les **données ouvertes IRCC** et les
**statistiques du marché du travail** (StatCan, Guichet-Emplois) pour aider les immigrants
qualifiés, étudiants PTPD/PGWP et professionnels en reconversion à comprendre leurs
perspectives d'emploi réelles au Canada.

**🔗 Démo en ligne : [canpath-frontend.onrender.com](https://canpath-frontend.onrender.com/)**

> Le backend est hébergé sur un plan gratuit et se met en veille après 15 minutes
> d'inactivité — la première réponse après une pause peut prendre ~1 minute le temps
> qu'il redémarre.

## Architecture

```
IRCC CSV + StatCan WDS + Rapports PDF/HTML
        ↓  Ingestion (manuelle pour l'instant — voir section Déploiement)
CSV → PostgreSQL          PDF/HTML → chunking → all-MiniLM-L6-v2 → ChromaDB
        ↓
Agent LangChain (claude-sonnet-4-6)
  ├─ query_database    — SQL SELECT gardé (allowlist tables, LIMIT forcé)
  ├─ search_documents  — RAG ChromaDB avec métadonnées de source
  └─ create_visualization — specs Plotly attachées à la réponse
  + mémoire conversationnelle + citations obligatoires
        ↓
FastAPI  /api/chat  /api/profile  /api/stats  /api/health
        ↓
React 18 + TS (chat bilingue, profil, sources cliquables, Plotly inline, dashboard RAGAS)
```

## Démarrage rapide (Docker)

```bash
cp .env.example .env        # ajouter votre ANTHROPIC_API_KEY
docker compose up --build -d
docker compose run --rm ingest              # première ingestion (seeds si hors-ligne)
# UI:  http://localhost:8080   API docs: http://localhost:8000/docs
```

Sans clé API, l'application démarre et `/api/chat` renvoie 503 ; tout le reste fonctionne.

## Développement local

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/make_seeds.py                      # régénérer les seeds si besoin
DATABASE_URL=sqlite:///dev.db python -m app.ingestion.run_ingestion --csv
DATABASE_URL=sqlite:///dev.db uvicorn app.main:app --reload
# UI Streamlit temporaire (Phase 1) :
streamlit run streamlit_app.py

# Frontend
cd frontend
npm install && npm run dev                        # http://localhost:5173 (proxy → :8000)
```

## Tests

```bash
cd backend
pytest tests -v            # suite complète (API, ingestion, RAG, guards)
python tests/test_pure_logic.py   # sous-ensemble sans dépendances lourdes
```

## Évaluation RAGAS

```bash
cd backend
python -m app.eval.ragas_eval          # faithfulness, answer relevancy, context precision
```

Les résultats sont écrits dans `data/ragas_results.json`, exposés par `GET /api/stats`
et affichés dans l'onglet **Qualité (RAGAS)** du frontend. **Non exécuté à ce jour** —
tant que ce fichier n'existe pas, le frontend affiche le message de repli plutôt que
des scores réels.

## Sources de données (licence ouverte)

| Donnée | Source | Mode |
|---|---|---|
| Admissions RP par province/catégorie | IRCC `ODP-PR-PT_IMMCAT.csv` | CSV → PostgreSQL |
| Admissions RP par pays | IRCC `ODP-PR-Citz.csv` | CSV → PostgreSQL |
| Admissions RP par profession (CNP) | IRCC `ODP-PR-PT_NOC4.csv` | CSV → PostgreSQL |
| Population active (EPA) | StatCan 14-10-0287 (WDS) | CSV → PostgreSQL |
| Salaires par profession | StatCan 14-10-0417 (WDS) | CSV → PostgreSQL |
| Immigrants sur le marché du travail | StatCan 14-10-0083 (WDS) | CSV → PostgreSQL |
| Admissibilité PTPD, Entrée express, tendances | Pages IRCC / Guichet-Emplois / analyses StatCan | HTML/PDF → ChromaDB |

Des **seeds réalistes** (mêmes schémas que les fichiers IRCC) sont embarqués : le produit
fonctionne hors-ligne et les tests CI n'ont pas besoin du réseau. L'ingestion réelle les
remplace au premier run.

## Déploiement

L'app tourne actuellement en production sur une infrastructure 100 % gratuite :

| Composant | Plateforme | Détail |
|---|---|---|
| Frontend (React) | [Render](https://render.com) — Static Site | build auto à chaque push sur `main` |
| Backend (FastAPI) | [Render](https://render.com) — Web Service (Docker) | plan Free, se met en veille après 15 min d'inactivité |
| Base de données | [Neon](https://neon.tech) — PostgreSQL serverless | palier gratuit, sans expiration |
| Documents RAG | ChromaDB, embarqué dans l'image Docker (`backend/data/chroma_seed`) | pas de disque persistant sur le plan gratuit, donc l'index est pré-construit et versionné plutôt que reconstruit à chaque déploiement |

Pour mettre à jour les données (nouvelles CSV IRCC/StatCan ou documents RAG), on relance
localement les commandes d'ingestion contre la base Neon, puis on commit/push le résultat :

```bash
cd backend
set DATABASE_URL=<connection string Neon>
python -m app.ingestion.run_ingestion --csv       # tables PostgreSQL

set CHROMA_PERSIST_DIR=data\chroma_seed
set EMBEDDING_BACKEND=chroma-onnx
python -m app.ingestion.run_ingestion --rag       # régénère l'index ChromaDB embarqué
```

Workflows GitHub Actions disponibles (`.github/workflows/`) :

- `ci.yml` — lint (ruff) + pytest + typecheck/build frontend + build Docker.
- `data-refresh.yml` — cron hebdomadaire (lundi 06:00 UTC) prévu pour automatiser
  l'ingestion ; **non branché à ce jour** (pas de secret `DATABASE_URL` configuré),
  la mise à jour se fait donc manuellement pour l'instant (voir ci-dessus).
- `deploy-azure.yml` — pipeline de déploiement Azure gardé en réserve, déclenchement
  manuel uniquement (`workflow_dispatch`). Le déploiement réel se fait sur Render/Neon,
  pas Azure.

## Notes de conception

- **Sécurité SQL** : l'agent n'exécute que des `SELECT` mono-instruction sur des tables
  allowlistées (`app/agent/sql_guard.py`), `LIMIT 200` forcé.
- **Citations obligatoires** : chaque tool enregistre ses sources ; si le modèle omet la
  section Sources, elle est ajoutée automatiquement (`app/agent/citations.py`).
- **Robustesse ingestion** : détection d'encodage (les CSV IRCC sont servis en binaire
  UTF-8 BOM/UTF-16), résolution de colonnes par motifs (survit aux dérives de schéma),
  runs idempotents + table d'audit `ingestion_runs`.
- **Embeddings** : `all-MiniLM-L6-v2` via sentence-transformers (défaut) ou via l'ONNX
  intégré de Chroma (`EMBEDDING_BACKEND=chroma-onnx`, sans torch — utilisé en CI).

## Avertissement

CanPath AI fournit un contexte statistique à partir de données publiques ; ce n'est pas
un avis juridique. Pour une décision d'immigration, consultez un consultant réglementé
(CRIC) ou un avocat.
