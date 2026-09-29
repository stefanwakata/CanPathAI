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
        ↓  Ingestion
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

## Avertissement

CanPath AI fournit un contexte statistique à partir de données publiques ; ce n'est pas
un avis juridique. Pour une décision d'immigration, consultez un consultant réglementé
(CRIC) ou un avocat.
