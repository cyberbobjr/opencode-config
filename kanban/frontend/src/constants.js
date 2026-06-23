export const STATUS_LABELS = {
  pending:      'En attente',
  refining:     'Raffinement',
  secops_tm:    'SecOps TM',
  tdd:          'TDD',
  secops_cr:    'SecOps CR',
  qa:           'QA',
  simplify:     'Simplify',
  commit_ready: 'Prêt commit',
  completed:    'Terminé',
  blocked:      'Bloqué',
}

export const STATUS_COLORS = {
  pending:      '#6b7280',
  refining:     '#f59e0b',
  secops_tm:    '#7c3aed',
  tdd:          '#3b82f6',
  secops_cr:    '#a78bfa',
  qa:           '#ec4899',
  simplify:     '#14b8a6',
  commit_ready: '#10b981',
  completed:    '#065f46',
  blocked:      '#ef4444',
}

export const KANBAN_COLUMNS = Object.entries(STATUS_LABELS).map(([status, label]) => ({
  status,
  label,
  color: STATUS_COLORS[status],
}))

export const SIMPLE_GROUPS = [
  { id: 'backlog',     label: 'Backlog',         color: '#6b7280', statuses: ['pending'],                                   dropTo: 'pending'      },
  { id: 'en_cours',   label: 'En cours',         color: '#3b82f6', statuses: ['refining', 'secops_tm', 'tdd', 'secops_cr'], dropTo: 'tdd'          },
  { id: 'validation', label: 'Validation',       color: '#ec4899', statuses: ['qa', 'simplify'],                            dropTo: 'qa'           },
  { id: 'pret',       label: 'Prêt',             color: '#10b981', statuses: ['commit_ready'],                              dropTo: 'commit_ready' },
  { id: 'termine',    label: 'Terminé / Bloqué', color: '#065f46', statuses: ['completed', 'blocked'],                      dropTo: 'completed'    },
]

export const PIPELINE_STEPS = [
  { status: 'refining',     label: 'Raffinement' },
  { status: 'secops_tm',    label: 'Threat Model' },
  { status: 'tdd',          label: 'TDD' },
  { status: 'secops_cr',    label: 'SecOps CR' },
  { status: 'qa',           label: 'QA' },
  { status: 'simplify',     label: 'Simplify' },
  { status: 'commit_ready', label: 'Commit' },
  { status: 'completed',    label: 'Terminé' },
]

export const STACK_OPTIONS = [
  'backend', 'frontend', 'database', 'infrastructure',
  'security', 'api', 'mobile', 'ml', 'devops',
]

export const STACK_COLORS = {
  backend:        '#3b82f6',
  frontend:       '#8b5cf6',
  database:       '#10b981',
  infrastructure: '#f59e0b',
  security:       '#ef4444',
  api:            '#06b6d4',
  mobile:         '#ec4899',
  ml:             '#f97316',
  devops:         '#6b7280',
}

export const PRIORITY_OPTIONS = [
  { value: 'low',      label: 'Basse',    color: '#60a5fa' },
  { value: 'medium',   label: 'Moyenne',  color: '#fbbf24' },
  { value: 'high',     label: 'Haute',    color: '#fb923c' },
  { value: 'critical', label: 'Critique', color: '#f87171' },
]

export const PRIORITY_COLORS = {
  low:      'text-blue-400',
  medium:   'text-yellow-400',
  high:     'text-orange-400',
  critical: 'text-red-400',
}

export const STATUS_OPTIONS = Object.entries(STATUS_LABELS).map(([value, label]) => ({
  value, label, color: STATUS_COLORS[value],
}))

export const TRIGGERABLE_STATUSES = new Set([
  'refining', 'secops_tm', 'tdd', 'secops_cr', 'qa', 'simplify', 'commit_ready',
])
