# opencode-config

Un template de configuration prêt à l'emploi pour [OpenCode](https://opencode.ai) qui donne à votre agent de développement IA un **pipeline structuré et traçable**.

Au cœur du système : un serveur Kanban qui fonctionne simultanément comme **tableau de bord web**, **API REST** et **serveur MCP** — permettant à l'agent de lire et mettre à jour l'état du projet, pendant que le développeur pilote depuis une interface drag-and-drop.

---

## Ce que ça apporte

- **Un tableau Kanban** connecté à l'agent via MCP — les stories avancent dans les colonnes au fil du travail
- **Un pont bidirectionnel** — déplacer une carte dans le tableau injecte une commande slash dans l'interface OpenCode
- **Des commandes slash** pour chaque étape du cycle de développement (raffinement, TDD, revue sécurité, QA, commit)
- **Des sous-agents** pour la revue qualité, réutilisabilité et efficacité du code
- **Un pipeline structuré** qui impose TDD, revue SecOps et validation QA avant chaque commit

---

## Structure du dépôt

```
.opencode/
├── opencode.json          — Configuration MCP (lue par OpenCode)
├── package.json           — Dépendances Node (outillage optionnel)
│
├── commands/              — Commandes slash disponibles dans OpenCode
│   ├── next-story.md      — Coordinateur : cycle complet ou étapes individuelles
│   ├── refine.md          — Agent raffinement (8–12 questions, 4 rôles)
│   ├── tdd.md             — Agent TDD (rouge → vert → refactor)
│   ├── secops.md          — Agent DevSecOps (threat model + code review)
│   ├── qa.md              — Agent QA (validation des AC par les tests)
│   ├── architect.md       — Conception architecture (cycle questions/réponses)
│   ├── simplify.md        — Revue qualité du code (3 sous-agents)
│   ├── review-pr.md       — Revue de PR GitHub et réponses
│   ├── commit.md          — Assistant commit conventionnel
│   ├── feature.md         — Créer + implémenter une story de fonctionnalité
│   ├── fix.md             — Créer + corriger une story de bug
│   └── change.md          — Créer une story de modification avec analyse d'impact
│
├── agents/                — Sous-agents réutilisables (appelés par les commandes)
│   ├── code-simplify-quality.md
│   ├── code-simplify-reuse.md
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

```bash
# Dashboard + MCP (mode standard)
python .opencode/kanban/server.py --mcp

# Mode debug — log chaque appel MCP avec ses paramètres
python .opencode/kanban/server.py --mcp --debug
```

Dashboard accessible sur : `http://localhost:8765`

### 3. Configurer OpenCode

Le fichier `opencode.json` de ce dépôt connecte déjà le serveur Kanban comme fournisseur MCP :

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "kanban": {
      "type": "local",
      "command": ["python", ".opencode/kanban/server.py", "--mcp"],
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
| `tdd` | `/tdd` implémente la story avec Rouge → Vert → Refactor |
| `secops_cr` | `/secops mode=code-review` audite le diff contre une checklist OWASP |
| `qa` | `/qa` valide chaque AC avec des tests d'intégration ou E2E |
| `simplify` | 3 sous-agents passent le code en revue (qualité, réutilisabilité, efficacité) |
| `commit_ready` | Le développeur approuve le message de commit |
| `completed` | Story committée et terminée |

Lancer le cycle complet :

```
/next-story US X.Y
```

Ou piloter les étapes individuelles depuis le tableau de bord en déplaçant les cartes — le serveur injecte automatiquement la bonne commande dans OpenCode.

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

Le serveur Kanban expose 7 outils sous le nom `kanban-stories` :

| Outil | Description |
|-------|-------------|
| `kanban-get-story` | Lire une story complète avec tous ses champs |
| `kanban-list-stories` | Lister les stories, filtrées par statut ou phase |
| `kanban-update-story` | Mise à jour partielle (résultats TDD, AC, guide d'implémentation…) |
| `kanban-move-story` | Déplacer une story vers une nouvelle colonne + log de la transition |
| `kanban-create-story` | Créer une nouvelle story (utilisé par `/feature`, `/fix`, `/change`) |
| `kanban-get-next-pending` | Obtenir la prochaine story en attente (priorité la plus haute) |
| `kanban-get-stats` | Obtenir les compteurs globaux du pipeline |

Voir [`kanban/README.md`](kanban/README.md) pour le schéma complet, les règles de fusion et la référence du debug logging.

---

## Référence des commandes

Toutes les commandes sont agnostiques à la stack. Elles référencent `AGENTS.md` dans votre projet pour les noms d'outils, chemins de fichiers et conventions.

| Commande | Rôle |
|----------|------|
| `/next-story` | Afficher le statut du projet et la prochaine story en attente |
| `/next-story US X.Y` | Lancer le cycle complet pour une story |
| `/refine US X.Y` | Challenger les AC via un dialogue structuré (4 rôles, 8–12 questions) |
| `/tdd US X.Y` | Implémenter avec TDD (délègue à l'`implementation_guide` de la story) |
| `/secops US X.Y` | Revue sécurité — mode threat model ou code review |
| `/qa US X.Y` | Valider chaque AC avec des tests |
| `/architect` | Concevoir une fonctionnalité avant d'implémenter (cycle questions/réponses) |
| `/simplify` | Revue de code par 3 sous-agents |
| `/review-pr [numéro]` | Récupérer les commentaires GitHub PR, classer, corriger, répondre |
| `/commit` | Proposer et créer un commit conventionnel |
| `/feature "..."` | Créer une story de fonctionnalité et l'implémenter |
| `/fix "..."` | Créer une story de bug et le corriger |
| `/change "..."` | Créer une story de modification avec analyse d'impact |

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
  "title": "...",
  "status": "pending",
  "priority": "P0",
  "acceptance_criteria": [
    {"id": 1, "text": "...", "checked": false}
  ],
  "tdd": {"status": "pending", "tests": 0, "coverage": "0%"},
  "qa":  {"status": "pending", "ac_covered": "0/0"},
  "implementation_guide": {},   // rempli par /refine
  "secops_report": {},          // rempli par /secops
  "history": []                 // journal d'audit — append-only
}
```

---

## Licence

MIT — utilisation, fork et adaptation libres.
