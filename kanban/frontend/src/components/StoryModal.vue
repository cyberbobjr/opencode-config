<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import MarkdownContent from './MarkdownContent.vue'
import SelectField from './SelectField.vue'
import {
  STACK_OPTIONS, STACK_COLORS, PRIORITY_OPTIONS, STATUS_OPTIONS,
  STATUS_LABELS, STATUS_COLORS,
} from '../constants.js'

const props = defineProps({
  story: { type: Object, required: true },
})
const emit = defineEmits(['close', 'save', 'delete'])

const activeTab = ref('spec')

// Only user-editable fields
const editData = ref({ priority: 'medium', stack: [] })

watch(
  () => props.story,
  (s) => {
    if (!s) return
    editData.value = {
      priority: s.priority || 'medium',
      stack:    [...(s.stack || [])],
    }
  },
  { immediate: true }
)

// ── ESC closes modal ─────────────────────────────────────────────────
function onKeydown(e) {
  if (e.key === 'Escape') emit('close')
}
onMounted(()  => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))

// ── Read-only display helpers ─────────────────────────────────────────
function normalizeAC(ac) {
  if (typeof ac === 'string') return { text: ac, checked: false }
  if (!ac || typeof ac !== 'object' || Array.isArray(ac)) return null
  return { text: ac.text || ac.description || '', checked: Boolean(ac.checked) }
}

function normalizeDecision(d) {
  if (typeof d === 'string') return { role: '', question: '', decision: d }
  if (!d || typeof d !== 'object') return null
  return {
    role:     d.role     || '',
    question: d.question || '',
    decision: d.decision || d.answer || d.text || '',
  }
}

const displayACs = computed(() =>
  (props.story.acceptance_criteria || []).map(normalizeAC).filter(Boolean)
)
const refinementDecisions = computed(() =>
  (props.story.refine_decisions || []).map(normalizeDecision).filter(Boolean)
)
const implGuide   = computed(() => props.story.implementation_guide || null)
const secopsNotes = computed(() =>
  props.story.secops_report?.notes ||
  props.story.secops_report?.note  ||
  props.story.secops_report?.comments || ''
)
const simplifyComments = computed(() => props.story.simplify_comments || '')
const simplifyDone = computed(() =>
  !simplifyComments.value &&
  (props.story.history || []).some(e => e.by === 'simplify')
)
const tddNotes         = computed(() => props.story.tdd?.notes || '')
const storyHistory     = computed(() => [...(props.story.history || [])].reverse())

// ── History display ───────────────────────────────────────────────────
const ACTOR_COLORS = {
  dashboard:   '#60a5fa',
  refine:      '#fbbf24',
  'secops-tm': '#7c3aed',
  tdd:         '#3b82f6',
  'secops-cr': '#a78bfa',
  qa:          '#ec4899',
  simplify:    '#14b8a6',
  commit:      '#10b981',
  prioritize:  '#f97316',
  agent:       '#6b7280',
  user:        '#60a5fa',
}

function actorColor(by) {
  return ACTOR_COLORS[by] ?? '#6b7280'
}

function isStatusChange(change) {
  return /^status:\s*\S+\s*→\s*\S+$/.test(change)
}

function parseStatusChange(change) {
  const m = change.match(/^status:\s*(\S+)\s*→\s*(\S+)$/)
  return m ? { from: m[1], to: m[2] } : null
}

function formatTs(ts) {
  if (!ts) return ''
  return ts.replace('T', ' ').slice(0, 16)
}

// ── Stack toggle ──────────────────────────────────────────────────────
function toggleStack(tag) {
  const idx = editData.value.stack.indexOf(tag)
  editData.value.stack = idx >= 0
    ? editData.value.stack.filter(t => t !== tag)
    : [...editData.value.stack, tag]
}

// ── Save / Delete ─────────────────────────────────────────────────────
function handleSave() {
  emit('save', {
    id: props.story.id,
    changes: {
      priority: editData.value.priority,
      stack:    editData.value.stack,
    },
  })
}

function confirmDelete() {
  if (window.confirm(`Supprimer la story ${props.story.id} ?`)) {
    emit('delete', { id: props.story.id })
  }
}
</script>

<template>
  <!-- Backdrop -->
  <div
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 flex items-center justify-center p-4"
    @click.self="emit('close')"
  >
    <div class="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl">

      <!-- Header -->
      <div class="flex items-start justify-between gap-4 px-6 pt-5 pb-4 border-b border-slate-800">
        <div class="flex-1 min-w-0">
          <span class="text-xs font-mono text-slate-500">{{ story.id }}</span>
          <h2 class="text-base font-semibold text-slate-100 mt-0.5">{{ story.title }}</h2>
        </div>
        <button
          class="text-slate-500 hover:text-slate-200 transition-colors text-xl leading-none mt-0.5"
          title="Fermer (ESC)"
          @click="emit('close')"
        >×</button>
      </div>

      <!-- Tabs -->
      <div class="flex border-b border-slate-800 px-6">
        <button
          v-for="tab in [
            { id: 'spec',     label: 'Spécification' },
            { id: 'refine',   label: 'Raffinement'   },
            { id: 'progress', label: 'Avancement'    },
            { id: 'history',  label: 'Historique'    },
          ]"
          :key="tab.id"
          class="text-sm px-4 py-2.5 border-b-2 transition-colors"
          :class="activeTab === tab.id
            ? 'border-primary text-white font-medium'
            : 'border-transparent text-slate-500 hover:text-slate-300'"
          @click="activeTab = tab.id"
        >{{ tab.label }}</button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">

        <!-- ── Spec ──────────────────────────────────────────────── -->
        <template v-if="activeTab === 'spec'">

          <!-- Priority (editable) + Status (read-only) -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">Priorité <span class="text-primary ml-1">✎</span></label>
              <SelectField v-model="editData.priority" :options="PRIORITY_OPTIONS" />
            </div>
            <div>
              <label class="label">Statut</label>
              <div
                class="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-700 bg-slate-800/50"
              >
                <div
                  class="w-2 h-2 rounded-full flex-shrink-0"
                  :style="{ backgroundColor: STATUS_COLORS[story.status] }"
                />
                <span class="text-sm text-slate-300">{{ STATUS_LABELS[story.status] ?? story.status }}</span>
              </div>
            </div>
          </div>

          <!-- Stack (editable) -->
          <div>
            <label class="label">Stack <span class="text-primary ml-1">✎</span></label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="tag in STACK_OPTIONS"
                :key="tag"
                class="text-xs px-2.5 py-1 rounded-full border transition-all"
                :class="editData.stack.includes(tag)
                  ? 'border-transparent'
                  : 'border-slate-700 text-slate-500 hover:border-slate-500'"
                :style="editData.stack.includes(tag)
                  ? { backgroundColor: (STACK_COLORS[tag] ?? '#6b7280') + '30', color: STACK_COLORS[tag] ?? '#9ca3af', borderColor: STACK_COLORS[tag] }
                  : {}"
                @click="toggleStack(tag)"
              >{{ tag }}</button>
            </div>
          </div>

          <!-- Description (read-only markdown) -->
          <div v-if="story.description">
            <label class="label">Description</label>
            <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/60">
              <MarkdownContent :content="story.description" />
            </div>
          </div>

          <!-- Acceptance Criteria (read-only) -->
          <div>
            <label class="label">
              Critères d'acceptation
              <span
                v-if="displayACs.length"
                class="ml-2 text-slate-600 font-normal"
              >{{ displayACs.filter(a => a.checked).length }}/{{ displayACs.length }}</span>
            </label>
            <div class="space-y-1.5">
              <div
                v-for="(ac, idx) in displayACs"
                :key="idx"
                class="flex items-start gap-2.5 py-1"
              >
                <div
                  class="w-4 h-4 mt-0.5 flex-shrink-0 rounded border flex items-center justify-center"
                  :class="ac.checked
                    ? 'bg-emerald-600 border-emerald-600'
                    : 'bg-transparent border-slate-600'"
                >
                  <svg v-if="ac.checked" class="w-2.5 h-2.5 text-white" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd"/>
                  </svg>
                </div>
                <span class="text-sm" :class="ac.checked ? 'text-slate-500 line-through' : 'text-slate-300'">
                  {{ ac.text }}
                </span>
              </div>
              <p v-if="!displayACs.length" class="text-sm text-slate-600 italic">Aucun critère</p>
            </div>
          </div>

        </template>

        <!-- ── Raffinement ───────────────────────────────────────── -->
        <template v-else-if="activeTab === 'refine'">
          <p v-if="!refinementDecisions.length && !implGuide" class="text-slate-500 text-sm italic">
            Pas encore de raffinement effectué.
          </p>

          <div v-if="refinementDecisions.length">
            <label class="label">Décisions de raffinement</label>
            <div class="space-y-4">
              <div
                v-for="(d, idx) in refinementDecisions"
                :key="idx"
                class="bg-slate-800 rounded-lg p-4 border border-slate-700"
              >
                <div v-if="d.role" class="text-xs text-slate-500 uppercase font-medium mb-1">{{ d.role }}</div>
                <div v-if="d.question" class="text-sm font-medium text-slate-300 mb-2">{{ d.question }}</div>
                <MarkdownContent :content="d.decision" placeholder="Pas de décision" />
              </div>
            </div>
          </div>

          <div v-if="implGuide">
            <label class="label">Guide d'implémentation</label>
            <div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <template v-if="typeof implGuide === 'string'">
                <MarkdownContent :content="implGuide" />
              </template>
              <template v-else>
                <div v-for="(val, key) in implGuide" :key="key" class="mb-3 last:mb-0">
                  <p class="text-xs text-slate-500 uppercase font-medium mb-1">{{ key }}</p>
                  <MarkdownContent :content="typeof val === 'string' ? val : JSON.stringify(val, null, 2)" />
                </div>
              </template>
            </div>
          </div>
        </template>

        <!-- ── Avancement ────────────────────────────────────────── -->
        <template v-else-if="activeTab === 'progress'">

          <!-- Notes (read-only) -->
          <div v-if="story.notes">
            <label class="label">Notes</label>
            <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/60">
              <MarkdownContent :content="story.notes" />
            </div>
          </div>

          <!-- TDD (read-only) -->
          <div class="bg-slate-800/60 rounded-lg p-4 border border-slate-700 space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm font-semibold text-slate-300">TDD</span>
              <span
                v-if="story.tdd?.status"
                class="text-xs px-2 py-0.5 rounded-full font-medium"
                :class="{
                  'bg-emerald-900/50 text-emerald-400 border border-emerald-800': story.tdd.status === 'done' || story.tdd.status === 'passed',
                  'bg-blue-900/50 text-blue-400 border border-blue-800': story.tdd.status === 'in_progress',
                  'bg-red-900/50 text-red-400 border border-red-800': story.tdd.status === 'failed',
                  'bg-slate-700 text-slate-400 border border-slate-600': !['done','passed','in_progress','failed'].includes(story.tdd.status),
                }"
              >{{ story.tdd.status }}</span>
            </div>
            <div v-if="story.tdd?.tests_count || story.tdd?.coverage" class="flex gap-6 text-sm">
              <div v-if="story.tdd?.tests_count" class="text-slate-400">
                Tests : <span class="text-slate-200 font-medium">{{ story.tdd.tests_count }}</span>
              </div>
              <div v-if="story.tdd?.coverage" class="text-slate-400">
                Couverture : <span class="text-slate-200 font-medium">{{ story.tdd.coverage }}%</span>
              </div>
            </div>
            <div v-if="tddNotes">
              <label class="label text-xs">Résumé TDD</label>
              <div class="bg-slate-900/60 rounded-lg p-3 border border-slate-700/50">
                <MarkdownContent :content="tddNotes" />
              </div>
            </div>
          </div>

          <!-- QA (read-only) -->
          <div class="bg-slate-800/60 rounded-lg p-4 border border-slate-700 space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm font-semibold text-slate-300">QA</span>
              <span
                v-if="story.qa?.status"
                class="text-xs px-2 py-0.5 rounded-full font-medium"
                :class="{
                  'bg-emerald-900/50 text-emerald-400 border border-emerald-800': story.qa.status === 'done' || story.qa.status === 'passed',
                  'bg-blue-900/50 text-blue-400 border border-blue-800': story.qa.status === 'in_progress',
                  'bg-red-900/50 text-red-400 border border-red-800': story.qa.status === 'failed',
                  'bg-slate-700 text-slate-400 border border-slate-600': !['done','passed','in_progress','failed'].includes(story.qa.status),
                }"
              >{{ story.qa.status }}</span>
            </div>
            <div v-if="story.qa?.ac_covered" class="text-sm text-slate-400">
              ACs couverts : <span class="text-slate-200 font-medium">{{ story.qa.ac_covered }}</span>
            </div>
            <div v-if="story.qa?.notes">
              <MarkdownContent :content="story.qa.notes" />
            </div>
          </div>

          <!-- SecOps CR (read-only) -->
          <div v-if="secopsNotes">
            <label class="label">SecOps CR — Rapport</label>
            <div class="bg-slate-800/60 rounded-lg p-4 border border-slate-700">
              <MarkdownContent :content="secopsNotes" />
            </div>
          </div>

          <!-- Simplify (read-only) -->
          <div v-if="simplifyComments || simplifyDone">
            <label class="label">Simplify — Résumé</label>
            <div class="bg-slate-800/60 rounded-lg p-4 border border-slate-700">
              <MarkdownContent v-if="simplifyComments" :content="simplifyComments" />
              <p v-else class="text-sm text-slate-500 italic">Stage complété — aucun commentaire enregistré.</p>
            </div>
          </div>

          <p
            v-if="!story.notes && !story.tdd?.status && !story.qa?.status && !secopsNotes && !simplifyComments"
            class="text-slate-600 text-sm italic"
          >
            Aucune donnée d'avancement pour l'instant.
          </p>
        </template>

        <!-- ── Historique ─────────────────────────────────────────── -->
        <template v-else-if="activeTab === 'history'">

          <!-- Timestamps -->
          <div class="flex gap-6 text-xs text-slate-500 pb-1 border-b border-slate-800 mb-1">
            <span v-if="story.created_at">
              Créée le <span class="text-slate-400 font-mono">{{ formatTs(story.created_at) }}</span>
            </span>
            <span v-if="story.updated_at">
              Mise à jour <span class="text-slate-400 font-mono">{{ formatTs(story.updated_at) }}</span>
            </span>
          </div>

          <p v-if="!storyHistory.length" class="text-slate-500 text-sm italic">Pas d'historique.</p>

          <div v-else class="space-y-3">
            <div
              v-for="(entry, idx) in storyHistory"
              :key="idx"
              class="rounded-lg border border-slate-800 bg-slate-800/30 overflow-hidden"
            >
              <!-- Entry header -->
              <div class="flex items-center gap-2 px-3 py-2 border-b border-slate-800/80 bg-slate-800/50">
                <span class="text-xs font-mono text-slate-600">{{ formatTs(entry.ts) }}</span>
                <span
                  class="ml-1 text-xs font-medium px-2 py-0.5 rounded-full border"
                  :style="{
                    backgroundColor: actorColor(entry.by) + '20',
                    color: actorColor(entry.by),
                    borderColor: actorColor(entry.by) + '40',
                  }"
                >{{ entry.by || 'agent' }}</span>
              </div>

              <!-- Changes -->
              <div class="px-3 py-2.5 space-y-1.5">
                <template v-for="(change, ci) in entry.changes" :key="ci">
                  <!-- Status transition → colored pills -->
                  <div v-if="isStatusChange(change)" class="flex items-center gap-2 flex-wrap">
                    <span
                      class="text-xs px-2 py-0.5 rounded"
                      :style="{
                        backgroundColor: (STATUS_COLORS[parseStatusChange(change)?.from] ?? '#6b7280') + '25',
                        color: STATUS_COLORS[parseStatusChange(change)?.from] ?? '#6b7280',
                      }"
                    >{{ STATUS_LABELS[parseStatusChange(change)?.from] ?? parseStatusChange(change)?.from }}</span>
                    <span class="text-slate-600 text-xs">→</span>
                    <span
                      class="text-xs px-2 py-0.5 rounded font-medium"
                      :style="{
                        backgroundColor: (STATUS_COLORS[parseStatusChange(change)?.to] ?? '#6b7280') + '30',
                        color: STATUS_COLORS[parseStatusChange(change)?.to] ?? '#6b7280',
                      }"
                    >{{ STATUS_LABELS[parseStatusChange(change)?.to] ?? parseStatusChange(change)?.to }}</span>
                  </div>

                  <!-- Other changes -->
                  <div v-else class="flex items-start gap-1.5">
                    <span class="text-slate-700 text-xs mt-0.5 flex-shrink-0">•</span>
                    <span class="text-xs text-slate-400">{{ change }}</span>
                  </div>
                </template>
                <p v-if="!entry.changes?.length" class="text-xs text-slate-600 italic">Aucun détail</p>
              </div>
            </div>
          </div>
        </template>

      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between px-6 py-4 border-t border-slate-800">
        <button class="text-xs text-red-500 hover:text-red-400 transition-colors" @click="confirmDelete">
          Supprimer
        </button>
        <div class="flex items-center gap-3">
          <button
            class="text-sm text-slate-400 hover:text-slate-200 px-4 py-2 transition-colors"
            @click="emit('close')"
          >Annuler</button>
          <button
            class="text-sm bg-primary hover:bg-primary-dark text-white px-5 py-2 rounded-lg transition-colors font-medium"
            @click="handleSave"
          >Sauvegarder</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.label {
  @apply block text-xs font-medium text-slate-400 mb-1.5;
}
.input {
  @apply w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200
         focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500
         placeholder:text-slate-600 transition-colors;
}
</style>
