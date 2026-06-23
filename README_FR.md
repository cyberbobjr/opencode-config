# opencode-config

Un template de configuration prêt à l'emploi pour [OpenCode](https://opencode.ai) qui donne à votre agent de développement IA un **pipeline structuré et traçable**.

Au cœur du système : un serveur Kanban qui fonctionne simultanément comme **tableau de bord web**, **API REST** et **serveur MCP** — permettant à l'agent de lire et mettre à jour l'état du projet, pendant que le développeur pilote depuis une interface drag-and-drop.

---

## Ce que ça apporte

- **Un tableau Kanban** connecté à l'agent via MCP — les stories avancent dans les colonnes au fil du travail
- **Un pont bidirectionnel** — déplacer une carte dans le tableau injecte une commande slash dans l'interface OpenCode
- **Des commandes slash** pour chaque étape du cycle de développement (raffinement, TDD, revue sécurité, QA, commit)
- **Des sous-agents isolés** pour le TDD, la QA, la revue SecOps et la simplification du code — chacun s'exécute dans son propre contexte avec les données de la story injectées
- **Un pipeline structuré** qui impose TDD, revue SecOps et validation QA avant chaque commit
- **Qualification des stories** — `/fix`, `/feature`, `/change` scannent le code et produisent un draft normalisé avant de persister

---

## Structure du dépôt

```
.opencode/
├── opencode.json          — Configuration MCP (lue par OpenCode)
├── package.json           — Dépendances Node (outillage optionnel)
│
├── commands/              — Commandes slash (prompts injectés dans l'agent principal OpenCode)
│   ├── next-story.md      — Coordinateur : cycle complet ou étapes individuelles
│   ├── refine.md          — Raffinement : 8–12 questions, 4 rôles (PO/Architecte/Dev/DevSecOps)
│   ├── tdd.md             — Wrapper fin → lance le sous-agent tdd via Task tool
│   ├── secops.md          — Threat model (inline) + code review wrapper → lance le sous-agent secops-cr
│   ├── qa.md              — Wrapper fin → lance le sous-agent qa via Task tool
│   ├── simplify.md        — Lance 3 sous-agents simplify en parallèle via Task tool
│   ├── architect.md       — Conception architecture (cycle questions/réponses)
│   ├── review-pr.md       — Revue de PR GitHub et réponses
│   ├── commit.md          — Assistant commit conventionnel
│   ├── feature.md         — Créer une story de fonctionnalité avec phase de qualification
│   ├── fix.md             — Créer une story de bug avec phase de qualification
│   └── change.md          — Créer une story de modification avec analyse d'impact
│
├── agents/                — Sous-agents (mode: subagent, contexte isolé, permissions propres)
│   ├── tdd.md             — Cycle ROUGE/VERT/REFACTOR — écrit les tests en premier
│   ├── qa.md              — Validation des AC par tests d'intégration et E2E
│   ├── secops-cr.md       — Revue OWASP du code (read+bash uniquement, non-invasif)
│   ├── code-simplify-reuse.md
│   ├── code-simplify-quality.md
│   └── code-simplify-efficiency.md
│
└── kanban/                — Serveur Kanban MCP
    ├── server.py          — Serveur principal (FastAPI + FastMCP)
    ├── requirements.txt
    ├── migrate.py         — Migration de schéma pour les stories existantes
    ├── templates/
    │   └── dashboard.html
    └── static/
        └── app.js
```

Les données des stories vivent **en dehors** de ce dépôt, dans `user-stories/*.json` à la racine du projet — un fichier JSON par story, servis par le serveur Kanban.

---

## Démarrage rapide

### 1. Installer les dépendances Python

```bash
pip install -r .opencode/kanban/requirements.txt
```

### 2. Démarrer le serveur Kanban

OpenCode démarre automatiquement le serveur via MCP. Vous pouvez aussi le lancer manuellement :

```bash
# Dashboard + MCP (mode standard)
python .opencode/kanban/server.py --mcp

# Mode debug — log chaque appel MCP avec ses paramètres
python .opencode/kanban/server.py --mcp --debug
```

Dashboard accessible sur : `http://localhost:8765`

> **Important** : laissez OpenCode démarrer le serveur — il bind à la fois MCP (stdio) et HTTP (port 8765) dans le même processus. Lancer une deuxième instance crée deux processus avec des états désynchronisés.

### 3. Configurer OpenCode

Le fichier `opencode.json` de ce dépôt connecte déjà le serveur Kanban comme fournisseur MCP :

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "kanban": {
      "type": "local",
      "command": ["python", ".opencode/kanban/server.py", "--mcp", "--debug"],
      "enabled": true
    }
  }
}
```

Copiez-le à la racine de votre projet (ou fusionnez avec votre `opencode.json` existant).

### 4. Ajouter vos conventions projet

Les commandes référencent `AGENTS.md` à la racine du projet pour les détails spécifiques à votre stack (runner de tests, commandes lint, chemins de fichiers, design system). Créez-en un si vous n'en avez pas — voir la section [Template AGENTS.md](#template-agentsmd) ci-dessous.

---

## Le pipeline

Chaque user story suit une séquence fixe d'étapes. L'agent suit lui-même sa position ; le développeur peut observer ou intervenir depuis le tableau de bord.

```
pending → refining → secops_tm → tdd → secops_cr → qa → simplify → commit_ready → completed
```

| Étape | Ce qui se passe |
|-------|----------------|
| `pending` | La story attend — pas encore raffinée |
| `refining` | `/refine` challenge les AC via un dialogue de 8–12 questions |
| `secops_tm` | `/secops mode=threat-model` identifie les surfaces d'attaque avant le code |
| `tdd` | Le sous-agent `tdd` implémente la story avec Rouge → Vert → Refactor |
| `secops_cr` | Le sous-agent `secops-cr` audite le diff contre une checklist OWASP |
| `qa` | Le sous-agent `qa` valide chaque AC avec des tests d'intégration ou E2E |
| `simplify` | 3 sous-agents passent le code en revue en parallèle (qualité, réutilisabilité, efficacité) |
| `commit_ready` | Le développeur approuve le message de commit |
| `completed` | Story committée et terminée |

Lancer le cycle complet :

```
/next-story US X.Y
```

Ou piloter les étapes individuelles depuis le tableau de bord en déplaçant les cartes — le serveur injecte automatiquement la bonne commande dans OpenCode.

---

## Trois modes d'interaction

Le même pipeline peut être piloté de trois façons, avec des niveaux d'automatisation différents :

### 1. `/next-story US X.Y` — Entièrement automatique

Le pipeline s'exécute de bout en bout avec un minimum d'interruptions :
- Les sous-agents s'exécutent en séquence, chacun reçoit le contexte de la story via injection dans le Task tool
- **2 points d'arrêt fixes** : après le raffinement (avant le code) et avant le commit
- **1 arrêt conditionnel** : si la QA échoue — le développeur décide comment continuer
- Les sous-agents ne demandent pas à passer à l'étape suivante

### 2. Commandes manuelles — Étape par étape

`/tdd US X.Y`, `/qa US X.Y`, `/secops US X.Y mode=code-review`, etc.

Chaque commande exécute une seule étape, puis demande :
> "✅ Terminé — passer à [étape suivante] ? [yes / no]"

Cela donne un contrôle granulaire pour inspecter les résultats entre les étapes.

### 3. Drag-and-drop sur le tableau de bord

Chaque déplacement de colonne passe par `/next-story` avec le sous-commande correspondant :

| Colonne de destination | Commande injectée |
|------------------------|-------------------|
| `refining` | `/next-story refine US X.Y` |
| `secops_tm` | `/next-story secops-tm US X.Y` |
| `tdd` | `/next-story implement US X.Y` |
| `secops_cr` | `/next-story secops-cr US X.Y` |
| `qa` | `/next-story qa US X.Y` |
| `simplify` | `/next-story simplify US X.Y` |
| `commit_ready` | `/next-story commit US X.Y` |

---

## Commandes vs Agents

OpenCode distingue deux concepts :

| | Commandes | Agents |
|--|-----------|--------|
| Définis dans | `commands/*.md` | `agents/*.md` |
| Contexte | Injecté dans l'**agent principal** | **Isolé** — fenêtre de contexte propre |
| Invocation | `/nom-commande` par l'utilisateur | Task tool (`subagent_type`) par une commande |
| Outil `question` | ✅ Disponible | ❌ Non disponible |
| Permissions | Héritées de l'agent principal | Définies dans le frontmatter de l'agent |
| Usage | Orchestration, Q&A interactif | Exécution avec contexte isolé et injecté |

**Ce que ça implique en pratique :**

- `refine.md` et `secops.md` (mode threat-model) restent des **commandes** — ils ont besoin de l'outil `question` pour le dialogue interactif
- `tdd.md`, `qa.md`, `secops.md` (mode code-review) sont des **wrappers fins** : ils assemblent le contexte (JSON story + AGENTS.md), puis lancent leur sous-agent correspondant via Task tool
- Les sous-agents reçoivent tout leur contexte dans le prompt du Task tool — ils ne lisent pas `$ARGUMENTS` directement

---

## Communication bidirectionnelle

Le serveur Kanban est l'**état partagé** entre le développeur et l'agent.

```
Développeur (tableau de bord)     Agent (OpenCode)
       │                               │
       │  drag carte → colonne         │
       │────────────────────────────▶  │
       │   POST /tui/submit-prompt     │
       │   → /next-story refine US X   │
       │                               │
       │                    Appel MCP  │
       │  ◀────────────────────────────│
       │  kanban-move-story(US X, tdd) │
       │  kanban-update-story(...)     │
       │                               │
       │  SSE : data: refresh          │
       │────────────────────────────▶  │
       │  (tableau se rafraîchit)      │
```

Règle clé : **les déplacements faits par l'agent ne déclenchent pas de commandes** (les agents avancent d'eux-mêmes). Seuls les drags humains déclenchent l'injection de commandes.

---

## Outils MCP

Le serveur Kanban expose 7 outils :

| Outil | Description |
|-------|-------------|
| `kanban-get-story` | Lire une story complète avec tous ses champs |
| `kanban-list-stories` | Lister les stories, filtrées par statut ou phase |
| `kanban-update-story` | Mise à jour partielle (résultats TDD, AC, guide d'implémentation…) |
| `kanban-move-story` | Déplacer une story vers une nouvelle colonne + log de la transition |
| `kanban-create-story` | Créer une nouvelle story — toujours avec `status: pending` |
| `kanban-get-next-pending` | Obtenir la prochaine story en attente (priorité la plus haute) |
| `kanban-get-stats` | Obtenir les compteurs globaux du pipeline |

Voir [`kanban/README.md`](kanban/README.md) pour le schéma complet, les règles de fusion et la référence du debug logging.

---

## Référence des commandes

Toutes les commandes sont agnostiques à la stack. Elles référencent `AGENTS.md` dans votre projet pour les noms d'outils, chemins de fichiers et conventions.

| Commande | Rôle |
|----------|------|
| `/next-story` | Afficher le statut du projet et la prochaine story en attente |
| `/next-story US X.Y` | Lancer le pipeline complet pour une story (2 points d'arrêt) |
| `/refine US X.Y` | Challenger les AC via un dialogue structuré (4 rôles, 8–12 questions via l'outil `question`) |
| `/tdd US X.Y` | Assembler le contexte → lancer le sous-agent `tdd` → gérer l'avancement |
| `/secops US X.Y` | Threat model (inline, interactif) ou code review (lance le sous-agent `secops-cr`) |
| `/qa US X.Y` | Assembler le contexte → lancer le sous-agent `qa` → gérer l'avancement |
| `/simplify [US X.Y]` | Lancer 3 sous-agents en parallèle, corriger les trouvailles, persister le rapport |
| `/architect` | Concevoir une fonctionnalité avant d'implémenter (cycle questions/réponses) |
| `/review-pr [numéro]` | Récupérer les commentaires GitHub PR, classer, corriger, répondre |
| `/commit` | Proposer et créer un commit conventionnel |
| `/feature "..."` | Qualifier (scan + titre + description + stack) → preview → créer story pending |
| `/fix "..."` | Qualifier le bug (scan + titre "Fix — " + Bug/Contexte/Attendu + stack) → créer pending |
| `/change "..."` | Qualifier le changement (scan impact + Motivation/Périmètre/Risques + stack) → créer pending |

---

## Création et qualification des stories

`/fix`, `/feature` et `/change` exécutent une **phase de qualification** avant de créer la story :

1. **Scan du contexte** — grep dans le code, `kanban-list-stories` (pour `/change`), lecture de `AGENTS.md`
2. **Remplissage du schéma** :

| Champ | Règle |
|-------|-------|
| `title` | Normalisé, ≤60 chars, format propre au type (voir ci-dessous) |
| `description` | Template propre au type (voir ci-dessous) |
| `priority` | P1 pour les bugs, P2 pour features/changes — ajustable |
| `stack` | Inféré depuis le scan du code — toujours rempli |
| `notes` | Contexte de reproduction, stories impactées, questions ouvertes |

3. **Preview + confirmation** — un seul bloc de confirmation avant de persister
4. **Création** — `kanban-create-story` (titre, priorité, phase) puis `kanban-update-story` (description, stack, notes)

**Formats de titre :**

| Commande | Format | Exemple |
|----------|--------|---------|
| `/feature` | Verbe impératif + sujet | `"Exporter les briefings en CSV"` |
| `/fix` | `"Fix — [description du bug]"` | `"Fix — refresh token expiré prématurément"` |
| `/change` | `"Change — [ce qui change]"` | `"Change — migration SQLite vers PostgreSQL"` |

**Templates de description :**

- `/feature` → `"En tant que [rôle], je veux [feature], afin de [bénéfice]."`
- `/fix` → `"**Bug:** [...]. **Contexte:** [...]. **Attendu:** [...]."` (3 parties)
- `/change` → `"**Motivation:** [...]. **Périmètre:** [...]. **Risques:** [...]."` (3 parties)

---

## Template AGENTS.md

Les commandes attendent un `AGENTS.md` à la racine de votre projet avec au minimum :

```markdown
## Commandes Dev

### Backend (`cd backend`)
| Commande | Action |
|----------|--------|
| `<commande de tests>` | Lancer les tests |
| `<commande lint>` | Lint |
| `<commande typecheck>` | Vérification des types |

### Frontend (`cd frontend`)
| Commande | Action |
|----------|--------|
| `<commande de tests>` | Lancer les tests |
| `<commande lint>` | Lint |

## Quality Gates

### Avant chaque commit
```bash
<lint + typecheck backend>
<lint + typecheck frontend>
```

### Avant chaque push / PR
```bash
<tests backend avec couverture>
<tests frontend avec couverture>
<tests E2E>
```
```

---

## Schéma JSON d'une story

Chaque story est stockée dans `user-stories/us-X-Y.json` :

```jsonc
{
  "id": "US 1.3",
  "phase": 1,
  "phase_name": "...",
  "title": "...",
  "description": "...",        // rempli par /feature, /fix, /change ou /refine
  "status": "pending",
  "priority": "P0",            // P0 | P1 | P2
  "stack": ["backend"],        // rempli par /feature, /fix, /change ou /refine
  "acceptance_criteria": [
    {"id": 1, "text": "...", "checked": false}
  ],
  "tdd": {"status": "pending", "tests": 0, "coverage": "0%", "notes": ""},
  "qa":  {"status": "pending", "ac_covered": "0/0", "notes": "", "ac_failures": []},
  "implementation_guide": {},  // rempli par /refine
  "refine_decisions": [],      // rempli par /refine
  "secops_report": {},         // rempli par /secops (les deux modes)
  "simplify_report": {},       // rempli par /simplify
  "notes": "",
  "history": []                // journal d'audit — append-only
}
```

---

## Licence

MIT — utilisation, fork et adaptation libres.
