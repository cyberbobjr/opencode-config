# Architecture & Décisions Clés

> Détail complet : `docs/SPECIFICATIONS.md`

| Décision | Valeur |
|----------|--------|
| Pipeline résilience | 3 retries → fallback GPT-5.5 (OpenRouter) → alerte admin |
| Langue | FR/EN au choix dans le profil, i18n interface |
| Onboarding | Wizard 3 étapes (skippable) |
| Génération briefings | Par clusters de profils (1 appel LLM / cluster) |
| Tracking | Opt-in explicite, désactivé par défaut |
| Sources | Import 1100+ flux + trust score LLM + super admin |
| Prix | Gratuit / 5,99€/mois / 59,90€/an |
| Pricing équipe | 29€/mois (10 membres) + 2€/membre supplémentaire |
| Rétention données | Illimitée |
| Tests | Pyramide : unitaires 60% + intégration 30% + E2E 10% |
| Template email | Script `markdown-to-email.py` (`~/.hermes/scripts/`) |
| Redis/Celery | Dès le MVP — broker Redis, queue Celery, Beat, Flower |
| Document store | SQLite WAL, switchable PostgreSQL via SQLAlchemy |
| Graphe temporel | Graphiti + Neo4j (7 deps, EpisodicNode natif) |
| Pipeline scraping | Continu adaptatif (fréquence variable selon trust_score) |
| Design system | Tokens dans `docs/design-system.md`, rendu dans `docs/designs/d-hybrid.html` |
