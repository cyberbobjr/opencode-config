# Intégration JIRA ↔ Kanban (Multi-dev)

> **Principe directeur** : JIRA est la source de vérité et le seul point de coordination entre les Kanbans.
> Chaque développeur a son propre Kanban local, entièrement indépendant des autres.
> Les Kanbans ne se parlent pas entre eux — seul JIRA fait le lien.
>
> **Contrainte entreprise** : pas de webhooks. Toute synchronisation repose sur le polling REST JIRA.

---

## Vue d'ensemble du système

```
                    ┌─────────────────────────────┐
                    │     JIRA Sprint (Scrum)      │
                    │   Source de vérité globale   │
                    │   Point de coordination      │
                    └──┬──────────┬──────────┬────┘
                       │ poll     │ poll     │ poll
                       │ write    │ write    │ write
                       ▼          ▼          ▼
              ┌─────────────┐ ┌─────────┐ ┌─────────┐
              │   Kanban    │ │ Kanban  │ │ Kanban  │
              │  Lead 👑    │ │  Dev A  │ │  Dev B  │
              │ ROLE=lead   │ │ ROLE=dev│ │ ROLE=dev│
              │ Refinement  │ │ Dev     │ │ Dev     │
              │ pipeline    │ │pipeline │ │pipeline │
              └─────────────┘ └─────────┘ └─────────┘

  Chaque Kanban = instance locale indépendante
  user-stories/*.json = état local propre à chaque dev
  JIRA = seul canal de coordination inter-Kanbans
```

---

## Deux rôles, deux comportements

Chaque instance Kanban est configurée par une variable d'environnement `JIRA_ROLE`.

| Capacité | `ROLE=lead` | `ROLE=dev` |
|---|:---:|:---:|
| Voir toutes les stories du sprint | ✅ | ✅ |
| Démarrer le refinement IA (`refining`) | ✅ | ❌ bloqué |
| Écrire description/AC enrichis dans JIRA | ✅ | ❌ |
| Démarrer le pipeline dev (`tdd` → `qa`) | ✅ | ✅ |
| Écrire "In Progress" dans JIRA | ✅ | ✅ |
| Poster logs TDD/QA en commentaire JIRA | ✅ | ✅ |
| Transitionner "Done" / "Blocked" dans JIRA | ✅ | ✅ |

---

## Cycle de vie complet d'une story

```
JIRA                 Kanban LEAD              Kanban DEV A / B
────                 ───────────              ────────────────

[1] To Do
(story brute)
     │
     │ poll
     ▼
                     pending
                     │
                     │ (lead décide de raffiner)
                     ▼
                     refining ──────────────────────────────────
                     │ Agents IA :                              │
                     │  • description enrichie                  │ (rien ne se passe
                     │  • AC détaillés                          │  chez les autres
                     │  • implementation_guide                  │  Kanbans pendant
                     │  • test strategy                         │  ce temps)
                     │
                     │ write-back JIRA :
                     │   PUT description (enrichie)
                     │   POST comment "[KANBAN-LEAD] Refinement done"
                     │   POST comment "## Implementation Guide\n..."
                     ▼
                     pending  (local lead — story raffinée)
                     │
[2] To Do            │
(description         │
 enrichie)           │
     │               │
     │ poll ─────────┼──────────────────────────────────────────
     ▼               │                                          ▼
                     │                           pending (description enrichie
                     │                            désormais disponible)
                     │                                          │
                     │                           (dev décide de prendre la story)
                     │                                          │
[3] In Progress ◀────┼──────────────────────────────── write-back :
     │               │                            POST /transitions → "In Progress"
     │               │                                          │
     │               │                                          ▼
     │               │                                         tdd
     │               │                                          │ write-back :
     │               │                                          │ POST comment
     │               │                                          │ "[KANBAN-DEV-A] TDD: 14 tests, 88%"
     │               │                                          ▼
     │               │                                         secops_cr
     │               │                                          │ write-back :
     │               │                                          │ POST comment
     │               │                                          │ "[KANBAN-DEV-A] SecOps: passed"
     │               │                                          ▼
     │               │                                         qa
     │               │                                          │ write-back :
     │               │                                          │ POST comment
     │               │                                          │ "[KANBAN-DEV-A] QA: 7/7 AC passed"
     │               │                                          ▼
[4] Done    ◀────────┼──────────────────────────────── completed
                     │                            POST /transitions → "Done"
```

---

## Asymétrie des statuts JIRA ↔ Kanban

```
JIRA Scrum              Kanban (lead)         Kanban (dev)
──────────              ─────────────         ────────────
To Do      ──────────▶  pending               pending
           ┌──────────▶ refining              (bloqué, ROLE=lead uniquement)
           │            secops_tm             secops_tm
In Progress├──────────▶ tdd             ────▶ tdd
           ├──────────▶ secops_cr             secops_cr
           ├──────────▶ qa                    qa
           └──────────▶ simplify              simplify
In Review  ──────────▶  commit_ready          commit_ready
Done       ──────────▶  completed             completed
Blocked    ──────────▶  blocked               blocked
```

**Règle de non-régression :**
JIRA "In Progress" ne rétrograde JAMAIS un Kanban déjà plus avancé dans le pipeline.
Si le Kanban est en `tdd` et JIRA dit "In Progress" (mappé `refining`), le Kanban gagne.

```python
STATUS_ORDER = [
    "pending", "refining", "secops_tm", "tdd",
    "secops_cr", "qa", "simplify", "commit_ready",
    "completed", "blocked"
]

def should_apply_jira_status(mapped_status: str, current_kanban: str) -> bool:
    if mapped_status in ("completed", "blocked"):
        return True  # statuts terminaux : JIRA gagne toujours
    return STATUS_ORDER.index(mapped_status) > STATUS_ORDER.index(current_kanban)
```

---

## Répartition des responsabilités par champ

| Champ | Propriétaire | Qui écrit dans JIRA |
|---|---|---|
| Titre (`summary`) | JIRA | Personne depuis Kanban |
| Priorité | JIRA | Personne depuis Kanban |
| Sprint membership | JIRA | Personne depuis Kanban |
| Statut JIRA | JIRA + Kanban | Kanban (transitions In Progress / Done / Blocked) |
| Description (enrichie) | Kanban Lead | ROLE=lead uniquement |
| Acceptance Criteria | Kanban Lead | Postés en commentaire JIRA |
| `implementation_guide` | Kanban (local) | Postés en commentaire JIRA (lead) |
| `tdd` / `qa` / `secops_report` | Kanban (local) | Postés en commentaire JIRA (dev) |
| `history` | Kanban (local) | Jamais — privé au Kanban |
| `priority_score` | Kanban (local) | Jamais — privé au Kanban |

---

## Architecture de synchronisation

### Flux JIRA → Kanban (Delta Polling)

```
┌──────────────────────────────────────────────────────────────────┐
│                        Sync Worker (asyncio)                     │
│                                                                  │
│  Au démarrage :                                                  │
│    1. GET /agile/1.0/board/{BOARD_ID}/sprint?state=active        │
│    2. GET /agile/1.0/sprint/{id}/issue?fields=...&maxResults=100 │
│       → Full sync : initialise sync_state pour chaque issue      │
│    3. Démarre la delta loop                                      │
│                                                                  │
│  Delta loop (toutes les POLL_INTERVAL secondes) :               │
│    1. last_ts = MIN(last_jira_ts) FROM sync_state               │
│    2. GET /api/3/search                                          │
│           ?jql=sprint={id} AND updated >= "{last_ts}"           │
│           &fields=summary,status,priority,updated,               │
│                   assignee,customfield_10016,description         │
│    3. Pour chaque issue modifiée :                               │
│         a. sync_state[key].skip_until > now() ? → skip          │
│            (changement causé par notre propre write)             │
│         b. should_apply_jira_status() ?                          │
│              OUI → apply_update() sur story Kanban locale        │
│              NON → log "non-régression appliquée"                │
│         c. ROLE=lead ET status="pending" ET pas de guide ?       │
│              → proposer refinement dans le dashboard             │
│         d. Mise à jour sync_state[key]                           │
└──────────────────────────────────────────────────────────────────┘
```

### Flux Kanban → JIRA (Write-back)

Déclenché par le hook `PostToolUse` sur `PATCH /api/stories/{sid}/move` et `PATCH /api/stories/{sid}`.
**Ne passe pas par le poll** — chemin direct et immédiat.

```
Kanban move / update
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│                      Write-back Router                        │
│                                                               │
│  Événement : story passe à "refining" (ROLE=lead uniquement) │
│    → Pas de write JIRA immédiat (refinement en cours)         │
│    → Après refinement complet :                               │
│        PUT  /api/3/issue/{key}  { description: enriched }     │
│        POST /api/3/issue/{key}/comment  "[KANBAN-LEAD] ..."   │
│        skip_until[key] = now() + 120s                         │
│                                                               │
│  Événement : story sort de "pending" vers un état dev         │
│    → POST /api/3/issue/{key}/transitions → "In Progress"      │
│       (seulement si JIRA est encore "To Do")                  │
│        skip_until[key] = now() + 120s                         │
│                                                               │
│  Événement : tdd.status passe à "passed"                      │
│    → POST /api/3/issue/{key}/comment                          │
│       body: "[KANBAN-{ACCOUNT_ID}] TDD: {tests} tests, {cov}" │
│                                                               │
│  Événement : secops_report.status = "passed" / "failed"       │
│    → POST /api/3/issue/{key}/comment                          │
│       body: "[KANBAN-{ACCOUNT_ID}] SecOps: {status} ..."      │
│                                                               │
│  Événement : qa.status passe à "passed"                       │
│    → POST /api/3/issue/{key}/comment                          │
│       body: "[KANBAN-{ACCOUNT_ID}] QA: {ac_covered} AC ✓"    │
│                                                               │
│  Événement : move → "completed"                               │
│    → POST /api/3/issue/{key}/transitions → "Done"             │
│        skip_until[key] = now() + 120s                         │
│                                                               │
│  Événement : move → "blocked"                                 │
│    → POST /api/3/issue/{key}/transitions → "Blocked"          │
│    → POST /api/3/issue/{key}/comment  (raison du blocage)     │
│        skip_until[key] = now() + 120s                         │
└───────────────────────────────────────────────────────────────┘
```

**Format des commentaires JIRA** (namespace pour identifier la source) :

```
[KANBAN-LEAD] Refinement terminé — 2026-06-25T10:30:00
───────────────────────────────────────────────────────
## Acceptance Criteria
1. ...
2. ...

## Implementation Guide
Approche : ...
Fichiers à créer : ...
```

```
[KANBAN-a1b2c3d4] TDD — 2026-06-25T14:20:00
────────────────────────────────────────────
Tests : 14 | Couverture : 88% | Statut : passed
Notes : All tests green, edge cases covered
```

Le préfixe `[KANBAN-{ACCOUNT_ID_SHORT}]` permet :
- d'identifier quel Kanban a écrit le commentaire
- au poll suivant, de détecter que c'est NOUS qui avons écrit (→ `skip_until`)
- de ne jamais confondre les logs de deux devs sur la même issue

---

## Anti-collision : mécanisme `skip_until`

Le problème : quand le Kanban écrit dans JIRA, JIRA met à jour son champ `updated`.
Au poll suivant, le Kanban détecte ce changement et risque de réimporter sa propre écriture.

```
Timeline sans skip_until (boucle infinie) :
  t=0   Kanban écrit "In Progress" dans JIRA
  t=2s  JIRA updated = "2026-06-25T10:00:02"
  t=5s  Poll : detected JIRA updated > last_poll_ts
  t=5s  Kanban applique "In Progress" sur lui-même (no-op mais log pollué)
  t=5s  PATCH Kanban → updated locale → re-poll → ...

Timeline avec skip_until :
  t=0   Kanban écrit "In Progress" dans JIRA
  t=0   skip_until[key] = now() + 120s
  t=5s  Poll : issue dans le delta
  t=5s  skip_until[key] > now() → SKIP
  t=120s Poll : skip_until expiré → traitement normal
```

```python
# Dans le delta processor :
def process_jira_update(jira_key: str, jira_issue: dict) -> None:
    state = sync_state.get(jira_key)
    if state and state.skip_until and datetime.now() < state.skip_until:
        log.debug(f"[skip] {jira_key} — write-back cooldown actif")
        return
    # ... traitement normal
```

---

## Schema SQLite (`sync.db`)

```sql
CREATE TABLE sync_state (
    jira_key          TEXT PRIMARY KEY,   -- "PROJ-42"
    kanban_id         TEXT,               -- "US 7.33"
    sprint_id         TEXT,               -- "123"
    jira_status       TEXT,               -- "In Progress"
    kanban_status     TEXT,               -- "tdd"
    jira_assignee_id  TEXT,               -- accountId JIRA de l'assignee
    last_jira_ts      TEXT,               -- champ "updated" de JIRA (ISO 8601)
    last_poll_ts      TEXT,               -- notre dernier poll réussi
    skip_until        TEXT,               -- ignore les updates JIRA avant cette ts
    refinement_done   INTEGER DEFAULT 0,  -- 1 si raffinée (lead a écrit dans JIRA)
    conflict_count    INTEGER DEFAULT 0,
    created_at        TEXT DEFAULT (datetime('now')),
    updated_at        TEXT DEFAULT (datetime('now'))
);

CREATE TABLE poll_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    polled_at       TEXT,
    sprint_id       TEXT,
    jira_role       TEXT,        -- "lead" | "dev"
    issues_seen     INTEGER,
    issues_changed  INTEGER,
    writes_jira     INTEGER,
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
JIRA_API_TOKEN=your_api_token_here    # Généré sur id.atlassian.com

# ── Identité de ce Kanban ────────────────────────────────────────
JIRA_MY_ACCOUNT_ID=a1b2c3d4e5f6      # accountId JIRA du propriétaire
JIRA_ROLE=dev                         # "lead" ou "dev"

# ── Projet & Board ────────────────────────────────────────────────
JIRA_BOARD_ID=123
JIRA_PROJECT_KEY=PROJ

# ── Sync behavior ────────────────────────────────────────────────
JIRA_SYNC_ENABLED=1
JIRA_POLL_INTERVAL_SECONDS=120        # 2 min en runtime
JIRA_WRITEBACK_ENABLED=1

# ── Mapping des statuts (à adapter au workflow JIRA réel) ─────────
# Format JSON : statut JIRA exact → statut Kanban
JIRA_STATUS_MAP={"To Do":"pending","In Progress":"refining","In Review":"commit_ready","Done":"completed","Blocked":"blocked"}
```

---

## Budget API — estimation réelle

Pour un sprint de 30 issues, 3 Kanbans actifs, poll toutes les 2 min :

| Opération | Fréquence | Req/heure par Kanban |
|---|---|---|
| Delta JQL query | toutes les 2 min | 30 |
| GET sprint actif (démarrage) | 1 fois/session | ~0 |
| POST transition JIRA | par story complétée | < 1 |
| POST comment JIRA | par étape clé (tdd, qa, secops) | < 5 |
| **Total par Kanban** | | **~35 req/heure** |
| **Total 3 Kanbans** | | **~105 req/heure** |

Limite burst JIRA : 100 req/s.
Limite points : 65 000/heure minimum.
**→ Largement dans les marges, même avec 10 développeurs.**

---

## Prochaines étapes pour l'implémentation

### Fichiers à créer

```
.opencode/kanban/
├── jira_sync.py          — module principal (polling + write-back)
├── jira_client.py        — wrapper HTTP JIRA avec retry/backoff
├── jira_status_map.py    — logique de mapping et non-régression
└── sync.db               — SQLite (gitignored)
```

### Intégration dans `server.py`

```python
# À ajouter dans le startup de server.py
from jira_sync import JiraSyncWorker

@app.on_event("startup")
async def start_jira_sync():
    if os.environ.get("JIRA_SYNC_ENABLED") == "1":
        worker = JiraSyncWorker()
        asyncio.create_task(worker.run())
```

### Ordre d'implémentation recommandé

1. `jira_client.py` — GET sprint + GET search + POST transitions + POST comment
2. `sync_state` SQLite — lecture/écriture simple
3. Full sync au démarrage — importer le sprint actif sans écrire dans JIRA
4. `--dry-run` — valider le mapping statuts sans rien écrire
5. Write-back "In Progress" et "Done" — les deux transitions les plus visibles
6. Write-back commentaires (TDD, QA, SecOps) — enrichissement progressif
7. Refinement lead (ROLE=lead) — écriture description enrichie dans JIRA
