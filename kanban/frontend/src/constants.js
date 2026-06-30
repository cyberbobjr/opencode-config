export const STATUS_LABELS = {
  pending:      'Pending',
  refining:     'Refining',
  secops_tm:    'SecOps TM',
  tdd:          'Ready to TDD',
  secops_cr:    'SecOps CR',
  qa:           'QA',
  simplify:     'Simplify',
  commit_ready: 'Commit Ready',
  completed:    'Done',
  blocked:      'Blocked',
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
  { id: 'backlog',     label: 'Backlog',          color: '#6b7280', statuses: ['pending'],                                   dropTo: 'pending'      },
  { id: 'en_cours',   label: 'In Progress',       color: '#3b82f6', statuses: ['refining', 'secops_tm', 'tdd', 'secops_cr'], dropTo: 'refining'     },
  { id: 'validation', label: 'Validation',        color: '#ec4899', statuses: ['qa', 'simplify'],                            dropTo: 'qa'           },
  { id: 'pret',       label: 'Ready',             color: '#10b981', statuses: ['commit_ready'],                              dropTo: 'commit_ready' },
  { id: 'termine',    label: 'Done / Blocked',    color: '#065f46', statuses: ['completed', 'blocked'],                      dropTo: 'completed'    },
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

export const AUDIENCE_OPTIONS = [
  { value: 'user',  label: 'Users'  },
  { value: 'admin', label: 'Admin'  },
]

export const AUDIENCE_COLORS = {
  user:  '#3b82f6',
  admin: '#f59e0b',
}

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

export const STATUS_OPTIONS = Object.entries(STATUS_LABELS).map(([value, label]) => ({
  value, label, color: STATUS_COLORS[value],
}))

export const TRIGGERABLE_STATUSES = new Set([
  'refining', 'secops_tm', 'tdd', 'secops_cr', 'qa', 'simplify', 'commit_ready',
])
