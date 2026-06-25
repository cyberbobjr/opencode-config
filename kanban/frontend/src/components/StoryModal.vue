<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import MarkdownContent from './MarkdownContent.vue'
import {
  STACK_OPTIONS, STACK_COLORS,
  STATUS_LABELS, STATUS_COLORS,
} from '../constants.js'

const props = defineProps({
  story:    { type: Object, required: true },
  position: { type: Object, default: null },
})
const emit = defineEmits(['close', 'save', 'delete'])

const activeTab = ref('spec')

const editData = ref({ stack: [] })

watch(
  () => props.story,
  (s) => {
    if (!s) return
    editData.value = { stack: [...(s.stack || [])] }
  },
  { immediate: true }
)

// ── ESC closes modal ─────────────────────────────────────────────────
function onKeydown(e) {
  if (e.key === 'Escape') emit('close')
}

// ── Copy story ID to clipboard ────────────────────────────────────────
const copied = ref(false)
async function copyId() {
  await navigator.clipboard.writeText(props.story.id)
  copied.value = true
  setTimeout(() => { copied.value = false }, 1500)
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
const secopsReport = computed(() => {
  const r = props.story.secops_report
  if (!r || typeof r !== 'object' || Array.isArray(r)) return null
  const hasContent = r.mode || r.surfaces?.length || r.risks?.length ||
                     r.recommendations?.length || r.status || r.notes || r.issues?.length
  return hasContent ? r : null
})
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
    changes: { stack: editData.value.stack },
  })
}

function confirmDelete() {
  if (window.confirm(`Delete story ${props.story.id}?`)) {
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
          <div class="flex items-center gap-2">
            <span class="text-xs font-mono text-slate-500">{{ story.id }}</span>
            <button
              class="text-slate-600 hover:text-slate-300 transition-colors"
              :title="copied ? 'Copié !' : 'Copier le numéro d\'US'"
              @click="copyId"
            >
              <svg v-if="!copied" xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 text-green-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </button>
            <span
              v-if="position"
              class="text-xs text-slate-500"
              title="Position in backlog"
            >#{{ position.rank }} / {{ position.total }}</span>
          </div>
          <h2 class="text-base font-semibold text-slate-100 mt-0.5">{{ story.title }}</h2>
        </div>
        <button
          class="text-slate-500 hover:text-slate-200 transition-colors text-xl leading-none mt-0.5"
          title="Close (ESC)"
          @click="emit('close')"
        >×</button>
      </div>

      <!-- Tabs -->
      <div class="flex border-b border-slate-800 px-6">
        <button
          v-for="tab in [
            { id: 'spec',     label: 'Specification' },
            { id: 'refine',   label: 'Refinement'    },
            { id: 'progress', label: 'Progress'      },
            { id: 'history',  label: 'History'       },
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

          <!-- Status (read-only) -->
          <div>
            <label class="label">Status</label>
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

          <!-- Stack (editable) -->
          <div>
            <label class="label">Stack <span class="text-primary ml-1">✎</span></label><!-- stack tag unchanged -->
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
            <label class="label">Description</label><!-- en -->
            <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/60">
              <MarkdownContent :content="story.description" />
            </div>
          </div>

          <!-- Acceptance Criteria (read-only) -->
          <div>
            <label class="label">
              Acceptance Criteria
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
              <p v-if="!displayACs.length" class="text-sm text-slate-600 italic">No criteria</p>
            </div>
          </div>

        </template>

        <!-- ── Raffinement ───────────────────────────────────────── -->
        <template v-else-if="activeTab === 'refine'">
          <p v-if="!refinementDecisions.length && !implGuide" class="text-slate-500 text-sm italic">
            No refinement done yet.
          </p>

          <div v-if="refinementDecisions.length">
            <label class="label">Refinement decisions</label>
            <div class="space-y-4">
              <div
                v-for="(d, idx) in refinementDecisions"
                :key="idx"
                class="bg-slate-800 rounded-lg p-4 border border-slate-700"
              >
                <div v-if="d.role" class="text-xs text-slate-500 uppercase font-medium mb-1">{{ d.role }}</div>
                <div v-if="d.question" class="text-sm font-medium text-slate-300 mb-2">{{ d.question }}</div>
                <MarkdownContent :content="d.decision" placeholder="No decision" />
              </div>
            </div>
          </div>

          <div v-if="implGuide">
            <label class="label">Implementation guide</label>
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
            <label class="label">Notes</label><!-- en -->
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
              <label class="label text-xs">TDD Summary</label>
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
              ACs covered: <span class="text-slate-200 font-medium">{{ story.qa.ac_covered }}</span>
            </div>
            <div v-if="story.qa?.notes">
              <MarkdownContent :content="story.qa.notes" />
            </div>
          </div>

          <!-- SecOps Report (read-only) -->
          <div v-if="secopsReport">
            <label class="label">
              SecOps —
              <span class="font-normal text-slate-500">{{ secopsReport.mode === 'threat-model' ? 'Threat Model' : 'Code Review' }}</span>
              <span
                v-if="secopsReport.review_required != null || secopsReport.status"
                class="ml-2 text-xs px-1.5 py-0.5 rounded font-medium"
                :class="(secopsReport.review_required || secopsReport.status === 'failed')
                  ? 'bg-red-900/40 text-red-400'
                  : 'bg-emerald-900/40 text-emerald-400'"
              >
                {{ secopsReport.status || (secopsReport.review_required ? 'Review required' : 'OK') }}
              </span>
            </label>

            <div class="bg-slate-800/60 rounded-lg border border-slate-700 divide-y divide-slate-700/60 text-sm">

              <!-- Surfaces -->
              <div v-if="secopsReport.surfaces?.length" class="px-4 py-3">
                <p class="text-xs text-slate-500 uppercase font-medium mb-1.5">Surfaces</p>
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="s in secopsReport.surfaces" :key="s"
                    class="text-xs px-2 py-0.5 rounded-full bg-violet-900/40 text-violet-300 border border-violet-700/40"
                  >{{ s }}</span>
                </div>
              </div>

              <!-- Risks -->
              <div v-if="secopsReport.risks?.length" class="px-4 py-3">
                <p class="text-xs text-slate-500 uppercase font-medium mb-1.5">Risks</p>
                <ul class="space-y-1">
                  <li v-for="(r, i) in secopsReport.risks" :key="i" class="flex gap-2 text-slate-300">
                    <span class="text-red-500 flex-shrink-0">▲</span>{{ r }}
                  </li>
                </ul>
              </div>

              <!-- Recommendations -->
              <div v-if="secopsReport.recommendations?.length" class="px-4 py-3">
                <p class="text-xs text-slate-500 uppercase font-medium mb-1.5">Recommendations</p>
                <ul class="space-y-1">
                  <li v-for="(r, i) in secopsReport.recommendations" :key="i" class="flex gap-2 text-slate-300">
                    <span class="text-emerald-500 flex-shrink-0">✓</span>{{ r }}
                  </li>
                </ul>
              </div>

              <!-- Issues (code-review mode) -->
              <div v-if="secopsReport.issues?.length" class="px-4 py-3">
                <p class="text-xs text-slate-500 uppercase font-medium mb-1.5">Issues</p>
                <ul class="space-y-1">
                  <li v-for="(issue, i) in secopsReport.issues" :key="i" class="flex gap-2 text-slate-300">
                    <span class="text-red-500 flex-shrink-0">✗</span>{{ typeof issue === 'string' ? issue : JSON.stringify(issue) }}
                  </li>
                </ul>
              </div>

              <!-- Notes (code-review mode) -->
              <div v-if="secopsReport.notes" class="px-4 py-3">
                <p class="text-xs text-slate-500 uppercase font-medium mb-1.5">Notes</p>
                <MarkdownContent :content="secopsReport.notes" />
              </div>
            </div>
          </div>

          <!-- Simplify (read-only) -->
          <div v-if="simplifyComments || simplifyDone">
            <label class="label">Simplify — Summary</label>
            <div class="bg-slate-800/60 rounded-lg p-4 border border-slate-700">
              <MarkdownContent v-if="simplifyComments" :content="simplifyComments" />
              <p v-else class="text-sm text-slate-500 italic">Stage completed — no comments recorded.</p>
            </div>
          </div>

          <p
            v-if="!story.notes && !story.tdd?.status && !story.qa?.status && !secopsReport && !simplifyComments"
            class="text-slate-600 text-sm italic"
          >
            No progress data yet.
          </p>
        </template>

        <!-- ── Historique ─────────────────────────────────────────── -->
        <template v-else-if="activeTab === 'history'">

          <!-- Timestamps -->
          <div class="flex gap-6 text-xs text-slate-500 pb-1 border-b border-slate-800 mb-1">
            <span v-if="story.created_at">
              Created <span class="text-slate-400 font-mono">{{ formatTs(story.created_at) }}</span>
            </span>
            <span v-if="story.updated_at">
              Updated <span class="text-slate-400 font-mono">{{ formatTs(story.updated_at) }}</span>
            </span>
          </div>

          <p v-if="!storyHistory.length" class="text-slate-500 text-sm italic">No history.</p>

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
                <p v-if="!entry.changes?.length" class="text-xs text-slate-600 italic">No details</p>
              </div>
            </div>
          </div>
        </template>

      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between px-6 py-4 border-t border-slate-800">
        <button class="text-xs text-red-500 hover:text-red-400 transition-colors" @click="confirmDelete">
          Delete
        </button>
        <div class="flex items-center gap-3">
          <button
            class="text-sm text-slate-400 hover:text-slate-200 px-4 py-2 transition-colors"
            @click="emit('close')"
          >Cancel</button>
          <button
            class="text-sm bg-primary hover:bg-primary-dark text-white px-5 py-2 rounded-lg transition-colors font-medium"
            @click="handleSave"
          >Save</button>
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
