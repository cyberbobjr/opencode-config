# Intégration JIRA ↔ Kanban (Multi-dev, lecture d'assignation + enrichissement)

> **Principe directeur** : JIRA est la source de vérité **de l'existence, de l'assignation et du statut** des tickets. Le Kanban local est un **espace de travail privé** au développeur : il possède **son propre statut de pipeline** (`pending → refining → tdd → secops_cr → qa → …`), indépendant du statut JIRA.
>
> - Chaque développeur a son propre Kanban local, entièrement indépendant des autres. Les Kanbans ne se parlent pas — seul JIRA fait le lien.
> - **Identité** : un Kanban ne voit et ne tire **que les tickets assignés à son développeur**.
> - **Le Kanban ne transitionne JAMAIS le statut JIRA.** Le workflow JIRA de l'équipe est complexe et ne doit pas être cassé ; les changements de statut (« DEV IN PROGRESS » → « TO TESTING » …) restent **manuels, faits par le développeur** dans JIRA.
> - **Write-back = commentaires uniquement** (v1). Le Kanban *annote* le ticket JIRA à chaque étape ; il n'écrit aucun champ ni statut.
> - **Contrainte entreprise** : pas de webhooks. Toute synchronisation repose sur le **polling REST JIRA**.
> - **Désactivable** : tout le mécanisme est une option activable par config/env (`JIRA_SYNC_ENABLED`, `JIRA_WRITEBACK_ENABLED`).

---

## Modèle de vérité — qui possède quoi

| Donnée | Propriétaire | Le Kanban… |
|---|---|---|
| Existence du ticket, `summary`, priorité, sprint, assignation | **JIRA** | …lit seulement (pull) |
| **Statut JIRA** (To Do / DEV IN PROGRESS / TO TESTING / Done…) | **JIRA + développeur (manuel)** | …**n'écrit jamais** — ni transition, ni statut |
| **Statut de pipeline local** (`tdd`, `secops_cr`, `qa`…) | **Kanban (local)** | …possède, indépendant de JIRA |
| `implementation_guide`, ACs raffinés, `tdd`/`qa`/`secops_report` | Kanban (local) | …publie en **commentaire** JIRA (pas de champ) |
| `history`, `priority_score` | Kanban (local) | …jamais exposé — privé |

> ⚠️ **Asymétrie clé vs versions antérieures de ce doc** : le Kanban n'importe PAS le statut JIRA dans son pipeline et ne pousse PAS de transition. Le statut JIRA n'a qu'**un seul rôle côté Kanban** : servir de **déclencheur de création** d'une US locale (voir plus bas). Toute la logique de mapping bidirectionnel et de non-régression de statut est donc supprimée.

---

## Identité : un dev ne voit que ses tickets

Chaque Kanban est configuré avec l'`accountId` JIRA de son propriétaire (`JIRA_MY_ACCOUNT_ID`). **Tous** les polls filtrent par assignation :

```
jql = sprint = {SPRINT_ID} AND assignee = "{JIRA_MY_ACCOUNT_ID}"
```

Un ticket réassigné à quelqu'un d'autre disparaît du pull (mais l'US locale déjà créée reste — le travail local n'est pas détruit ; on log un avertissement).

---

## Signal d'entrée : statut déclencheur paramétrable

Le Kanban ne tire pas tout le sprint. Une US locale n'est créée que lorsqu'un ticket **assigné au dev** atteint le **statut déclencheur configurable** :

```env
JIRA_PULL_TRIGGER_STATUS=DEV IN PROGRESS   # paramétrable (conf/env)
```

Concrètement : le dev prend son ticket dans JIRA et le passe manuellement en « DEV IN PROGRESS ». Au poll suivant, le Kanban détecte ce ticket (assigné + statut déclencheur) et **crée l'US locale si elle n'existe pas** (`status = pending`), prête à entrer dans le pipeline local. **Idempotent** : si l'US existe déjà, no-op.

> Le statut est paramétrable car il varie selon le workflow JIRA de l'équipe. Peut être étendu à une **liste** de statuts déclencheurs (`JIRA_PULL_TRIGGER_STATUS="DEV IN PROGRESS,In Development"`).

---

## Cycle de vie complet d'une story

```
JIRA (statuts pilotés MANUELLEMENT par le dev)      Kanban local du dev
──────────────────────────────────────────────      ───────────────────

[ ] To Do  (ticket assigné au dev)
     │
     │  le dev passe manuellement le ticket en :
     ▼
[▶] DEV IN PROGRESS  ◄── statut déclencheur (JIRA_PULL_TRIGGER_STATUS)
     │
     │ poll (assignee = moi AND status = trigger)
     ▼
                                                     création US locale → pending
                                                     │
                                                     │ (le dev lance le pipeline local)
                                                     ▼
                                                     refining / tdd / secops_cr / qa …
                                                     │   à chaque étape clé :
     │ ◄───────────── POST comment (enrichissement) ─┤   "[KANBAN-<id>] TDD: 14 tests, 88%"
     │                (JAMAIS de transition)          │   "[KANBAN-<id>] QA: 7/7 AC ✓"
     │                                                ▼
     │                                               completed  (statut LOCAL)
     │
     │  le dev passe manuellement le ticket en :
     ▼
[✔] TO TESTING / Done  ◄── décision humaine, hors Kanban
```

Le statut local `completed` **ne pousse pas** JIRA vers « Done ». Le dev décide.

---

## Write-back Kanban → JIRA : commentaires uniquement (v1)

Déclenché par le hook local sur les changements d'étape du pipeline (`PATCH /api/stories/{sid}` / `/move`). **Chemin direct, hors poll.** Aucune transition, aucun `PUT` de champ.

```
Étape pipeline local          →   Action JIRA
─────────────────────────────────────────────────────────────
tdd.status = passed           →   POST /issue/{key}/comment
secops_report.status = ...    →   POST /issue/{key}/comment
qa.status = passed            →   POST /issue/{key}/comment
move → blocked                →   POST /issue/{key}/comment (raison)
move → completed              →   POST /issue/{key}/comment (récap)
```

**Format des commentaires** (namespacés pour tracer la source multi-dev) :

```
[KANBAN-a1b2c3d4] TDD — 2026-06-25T14:20:00
────────────────────────────────────────────
Tests : 14 | Couverture : 88% | Statut : passed
Notes : all green, edge cases covered
```

Le préfixe `[KANBAN-{ACCOUNT_ID_SHORT}]` permet d'identifier quel dev a écrit, et de ne pas confondre les logs de deux devs sur une même issue.

> **v1 = commentaires seulement.** L'enrichissement de champs JIRA (description, ACs) est **différé** : on valide d'abord le flux commentaires ; si ça fonctionne bien, on ouvrira l'écriture de champs derrière un flag dédié. Le rôle « lead » (refinement écrit dans JIRA) de la conception initiale est lui aussi **différé** — non requis tant que chaque dev ne voit que ses propres tickets et qu'on n'écrit aucun champ partagé.

---

## Architecture de synchronisation

### Flux JIRA → Kanban (delta polling)

```
┌──────────────────────────────────────────────────────────────────┐
│                        Sync Worker (asyncio)                     │
│                                                                  │
│  Au démarrage :                                                  │
│    1. GET /agile/1.0/board/{BOARD_ID}/sprint?state=active        │
│    2. Full sync : GET issues (assignee = moi) → init sync_state  │
│                                                                  │
│  Delta loop (toutes les POLL_INTERVAL secondes) :               │
│    1. last_ts = MIN(last_jira_ts) FROM sync_state               │
│    2. GET /api/3/search                                          │
│         ?jql=sprint={id} AND assignee="{MY_ACCOUNT_ID}"          │
│               AND updated >= "{last_ts}"                         │
│         &fields=summary,status,priority,updated,assignee         │
│    3. Pour chaque issue modifiée :                              │
│         a. skip_until[key] > now() ? → skip (notre propre write) │
│         b. status ∈ JIRA_PULL_TRIGGER_STATUS ET US absente ?     │
│              → créer US locale (pending)   [idempotent]          │
│         c. réassignée hors de moi ? → log warning (US conservée) │
│         d. maj sync_state[key]                                   │
│                                                                  │
│    ⚠ On N'APPLIQUE PAS le statut JIRA sur le statut du Kanban.   │
└──────────────────────────────────────────────────────────────────┘
```

### Anti-collision `skip_until` (léger)

Nos commentaires bumpent le champ `updated` de l'issue. Au poll suivant on risque de retraiter l'issue. Comme le seul traitement est « créer l'US si absente » (idempotent), l'impact est nul, mais on garde `skip_until` pour éviter le bruit de logs :

```python
def process_jira_update(jira_key: str, jira_issue: dict) -> None:
    state = sync_state.get(jira_key)
    if state and state.skip_until and datetime.now() < state.skip_until:
        return  # cooldown après notre propre commentaire
    # ... détection trigger + création US idempotente
```

On pose `skip_until[key] = now() + 120s` après chaque commentaire posté.

---

## Schema SQLite (`sync.db`)

```sql
CREATE TABLE sync_state (
    jira_key          TEXT PRIMARY KEY,   -- "PROJ-42"
    kanban_id         TEXT,               -- "US 7.33" (null tant que non créée)
    sprint_id         TEXT,
    jira_status       TEXT,               -- dernier statut JIRA vu (info seulement)
    jira_assignee_id  TEXT,
    last_jira_ts      TEXT,               -- champ "updated" JIRA (ISO 8601)
    last_poll_ts      TEXT,
    skip_until        TEXT,               -- cooldown après notre write
    us_created        INTEGER DEFAULT 0,  -- 1 si l'US locale a déjà été créée
    created_at        TEXT DEFAULT (datetime('now')),
    updated_at        TEXT DEFAULT (datetime('now'))
);

CREATE TABLE poll_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    polled_at       TEXT,
    sprint_id       TEXT,
    issues_seen     INTEGER,
    us_created      INTEGER,
    comments_posted INTEGER,
    duration_ms     INTEGER,
    error           TEXT
);
```

---

## Configuration par Kanban (`.opencode/.env`)

```env
# ── Connexion JIRA ──────────────────────────────────────────────
JIRA_BASE_URL=https://your-org.atlassian.net
JIRA_USER_EMAIL=prenom.nom@company.com
JIRA_API_TOKEN=your_api_token_here        # généré sur id.atlassian.com

# ── Identité (le dev ne voit que SES tickets) ────────────────────
JIRA_MY_ACCOUNT_ID=a1b2c3d4e5f6           # accountId JIRA du propriétaire

# ── Projet & Board ──────────────────────────────────────────────
JIRA_BOARD_ID=123
JIRA_PROJECT_KEY=PROJ

# ── Signal d'entrée (paramétrable) ──────────────────────────────
# Statut(s) JIRA qui déclenche(nt) la création d'une US locale absente.
JIRA_PULL_TRIGGER_STATUS=DEV IN PROGRESS

# ── Sync behavior (désactivable) ────────────────────────────────
JIRA_SYNC_ENABLED=1                        # master switch (pull)
JIRA_WRITEBACK_ENABLED=1                   # commentaires Kanban → JIRA
JIRA_POLL_INTERVAL_SECONDS=120
```

> ❌ Volontairement **absent** : aucune variable de mapping de statut descendant, aucune transition. Le Kanban n'écrit jamais de statut JIRA.

---

## Budget API (indicatif)

Sprint de 30 issues, 10 devs, poll toutes les 2 min, filtre par assignee (donc peu d'issues par dev) :

| Opération | Fréquence | Req/heure par Kanban |
|---|---|---|
| Delta JQL (assignee = moi) | toutes les 2 min | 30 |
| GET sprint actif (démarrage) | 1×/session | ~0 |
| POST comment | par étape clé (tdd, qa, secops) | < 5 |
| **Total par Kanban** | | **~35 req/heure** |

Limite burst JIRA ≈ 100 req/s, points ≥ 65 000/heure → large marge même à 10 devs.

---

## Périmètre v1 & étapes d'implémentation

**Dans le périmètre v1**
- Pull filtré par assignee + statut déclencheur paramétrable → création d'US locales idempotente.
- Write-back **commentaires uniquement**, namespacés.
- Désactivable (`JIRA_SYNC_ENABLED`, `JIRA_WRITEBACK_ENABLED`).

**Hors périmètre v1 (différé)**
- Écriture de champs JIRA (description, ACs) — à ouvrir plus tard derrière un flag si le flux commentaires convient.
- Rôle `lead`/`dev` et refinement écrit dans JIRA.
- Toute transition de statut JIRA (rester **manuel** côté dev — potentiellement définitif).

### Fichiers à créer

```
.opencode/kanban/
├── jira_sync.py          — worker polling (delta) + création d'US idempotente
├── jira_client.py        — wrapper HTTP JIRA (retry/backoff, GET search + POST comment)
├── jira_writeback.py     — hook étapes pipeline → commentaires namespacés
└── sync.db               — SQLite (gitignored)
```

### Intégration dans `server.py`

```python
from jira_sync import JiraSyncWorker

@app.on_event("startup")
async def start_jira_sync():
    if os.environ.get("JIRA_SYNC_ENABLED") == "1":
        asyncio.create_task(JiraSyncWorker().run())
```

### Ordre recommandé

0. **Config & artefacts** : ajouter `kanban/*.db` (+ `-wal`/`-shm`/`-journal`) au `.opencode/.gitignore` — la `sync.db` est un état **local jamais committé** — et documenter les variables JIRA dans `.opencode/.env.example` (déjà fait, section « JIRA ↔ Kanban integration »).
1. `jira_client.py` — GET sprint + GET search (assignee) + POST comment.
2. `sync_state` SQLite — lecture/écriture.
3. Full sync au démarrage (lecture seule, aucun write).
4. `--dry-run` — valider la détection du statut déclencheur sans rien écrire.
5. Création d'US idempotente sur trigger.
6. Write-back commentaires (TDD, QA, SecOps).
