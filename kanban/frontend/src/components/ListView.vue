<script setup>
import { ref, computed } from 'vue'
import { STATUS_LABELS, STATUS_COLORS, STACK_COLORS, AUDIENCE_COLORS, AUDIENCE_OPTIONS } from '../constants.js'

const props = defineProps({
  stories: { type: Array, required: true },
})
const emit = defineEmits(['open-modal'])

const STATUS_ORDER = Object.fromEntries(
  Object.keys(STATUS_LABELS).map((k, i) => [k, i])
)

// ── Filters ───────────────────────────────────────────────────────────
const activeStatuses = ref(new Set())
const activeStacks   = ref(new Set())
const activeAudience = ref(new Set())

const availableStatuses = computed(() => {
  const seen = new Set(props.stories.map(s => s.status))
  return Object.keys(STATUS_LABELS).filter(k => seen.has(k))
})

const availableStacks = computed(() => {
  const seen = new Set(props.stories.flatMap(s => s.stack || []))
  return [...seen].sort()
})

const availableAudience = computed(() => {
  const seen = new Set(props.stories.flatMap(s => s.audience || []))
  return AUDIENCE_OPTIONS.filter(o => seen.has(o.value))
})

function toggleStatus(s) {
  const next = new Set(activeStatuses.value)
  next.has(s) ? next.delete(s) : next.add(s)
  activeStatuses.value = next
}

function toggleStack(t) {
  const next = new Set(activeStacks.value)
  next.has(t) ? next.delete(t) : next.add(t)
  activeStacks.value = next
}

function toggleAudience(val) {
  const next = new Set(activeAudience.value)
  next.has(val) ? next.delete(val) : next.add(val)
  activeAudience.value = next
}

function clearFilters() {
  activeStatuses.value = new Set()
  activeStacks.value   = new Set()
  activeAudience.value = new Set()
}

const hasFilters = computed(() => activeStatuses.value.size > 0 || activeStacks.value.size > 0 || activeAudience.value.size > 0)

// ── Sort ──────────────────────────────────────────────────────────────
const sortKey = ref('id')
const sortDir = ref(1)

function setSort(key) {
  if (sortKey.value === key) {
    sortDir.value = -sortDir.value
  } else {
    sortKey.value = key
    sortDir.value = 1
  }
}

// ── Filter → Sort ─────────────────────────────────────────────────────
const sorted = computed(() => {
  let rows = props.stories
  if (activeStatuses.value.size)
    rows = rows.filter(s => activeStatuses.value.has(s.status))
  if (activeStacks.value.size)
    rows = rows.filter(s => (s.stack || []).some(t => activeStacks.value.has(t)))
  if (activeAudience.value.size)
    rows = rows.filter(s => (s.audience || []).some(a => activeAudience.value.has(a)))

  return [...rows].sort((a, b) => {
    const av = sortKey.value === 'status' ? (STATUS_ORDER[a.status] ?? 99) : (a[sortKey.value] ?? '')
    const bv = sortKey.value === 'status' ? (STATUS_ORDER[b.status] ?? 99) : (b[sortKey.value] ?? '')
    if (av < bv) return -sortDir.value
    if (av > bv) return sortDir.value
    return 0
  })
})

function sortIcon(key) {
  if (sortKey.value !== key) return '↕'
  return sortDir.value === 1 ? '↑' : '↓'
}

function formatTs(ts) {
  if (!ts) return '—'
  return ts.replace('T', ' ').slice(0, 16)
}
</script>

<template>
  <div class="flex flex-col gap-3">

    <!-- Filter bar -->
    <div class="flex flex-wrap gap-3 items-start">

      <!-- Status chips -->
      <div class="flex flex-wrap gap-1 items-center">
        <span class="text-xs text-slate-500 mr-1">Status</span>
        <button
          v-for="s in availableStatuses"
          :key="s"
          class="text-xs px-2 py-0.5 rounded-full border transition-all"
          :style="activeStatuses.has(s)
            ? { backgroundColor: STATUS_COLORS[s] + '30', color: STATUS_COLORS[s], borderColor: STATUS_COLORS[s] }
            : { borderColor: '#334155', color: '#64748b' }"
          @click="toggleStatus(s)"
        >{{ STATUS_LABELS[s] }}</button>
      </div>

      <!-- Audience chips -->
      <div v-if="availableAudience.length" class="flex flex-wrap gap-1 items-center">
        <span class="text-xs text-slate-500 mr-1">Audience</span>
        <button
          v-for="opt in availableAudience"
          :key="opt.value"
          class="text-xs px-2 py-0.5 rounded-full border transition-all"
          :style="activeAudience.has(opt.value)
            ? { backgroundColor: (AUDIENCE_COLORS[opt.value] ?? '#6b7280') + '30', color: AUDIENCE_COLORS[opt.value] ?? '#9ca3af', borderColor: AUDIENCE_COLORS[opt.value] ?? '#6b7280' }
            : { borderColor: '#334155', color: '#64748b' }"
          @click="toggleAudience(opt.value)"
        >{{ opt.label }}</button>
      </div>

      <!-- Stack chips -->
      <div v-if="availableStacks.length" class="flex flex-wrap gap-1 items-center">
        <span class="text-xs text-slate-500 mr-1">Stack</span>
        <button
          v-for="t in availableStacks"
          :key="t"
          class="text-xs px-2 py-0.5 rounded-full border transition-all"
          :style="activeStacks.has(t)
            ? { backgroundColor: (STACK_COLORS[t] ?? '#6b7280') + '30', color: STACK_COLORS[t] ?? '#9ca3af', borderColor: STACK_COLORS[t] ?? '#6b7280' }
            : { borderColor: '#334155', color: '#64748b' }"
          @click="toggleStack(t)"
        >{{ t }}</button>
      </div>

      <!-- Clear -->
      <button
        v-if="hasFilters"
        class="text-xs text-slate-500 hover:text-slate-300 underline ml-auto"
        @click="clearFilters"
      >Clear filters</button>
    </div>

  <div class="overflow-x-auto">
    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="border-b border-slate-700">
          <th
            v-for="col in [
              { key: 'id',         label: 'ID',      sortable: true  },
              { key: 'title',      label: 'Title',   sortable: true  },
              { key: 'status',     label: 'Status',  sortable: true  },
              { key: 'updated_at', label: 'Updated', sortable: true  },
              { key: 'audience',   label: 'Audience', sortable: false },
              { key: 'stack',      label: 'Stack',   sortable: false },
            ]"
            :key="col.key"
            class="text-left px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap"
            :class="col.sortable ? 'cursor-pointer hover:text-slate-300' : ''"
            @click="col.sortable && setSort(col.key)"
          >
            {{ col.label }}
            <span v-if="col.sortable" class="text-slate-600">{{ sortIcon(col.key) }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="s in sorted"
          :key="s.id"
          class="border-b border-slate-800 hover:bg-slate-800/50 cursor-pointer transition-colors"
          @click="emit('open-modal', s.id)"
        >
          <td class="px-3 py-2 font-mono text-xs text-slate-400 whitespace-nowrap">{{ s.id }}</td>
          <td class="px-3 py-2 text-slate-200 max-w-xs truncate">{{ s.title }}</td>
          <td class="px-3 py-2 whitespace-nowrap">
            <span
              class="text-xs px-2 py-0.5 rounded-full font-medium"
              :style="{ backgroundColor: STATUS_COLORS[s.status] + '25', color: STATUS_COLORS[s.status] }"
            >
              {{ STATUS_LABELS[s.status] }}
            </span>
          </td>
          <td class="px-3 py-2 font-mono text-xs text-slate-500 whitespace-nowrap">{{ formatTs(s.updated_at) }}</td>
          <td class="px-3 py-2">
            <div class="flex gap-1 flex-wrap">
              <span
                v-for="val in (s.audience || [])"
                :key="val"
                class="text-xs px-1.5 py-0.5 rounded"
                :style="{ backgroundColor: (AUDIENCE_COLORS[val] ?? '#6b7280') + '25', color: AUDIENCE_COLORS[val] ?? '#9ca3af' }"
              >
                {{ AUDIENCE_OPTIONS.find(o => o.value === val)?.label ?? val }}
              </span>
            </div>
          </td>
          <td class="px-3 py-2">
            <div class="flex gap-1 flex-wrap">
              <span
                v-for="tag in (s.stack || [])"
                :key="tag"
                class="text-xs px-1.5 py-0.5 rounded"
                :style="{ backgroundColor: (STACK_COLORS[tag] ?? '#6b7280') + '25', color: STACK_COLORS[tag] ?? '#9ca3af' }"
              >
                {{ tag }}
              </span>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!sorted.length" class="text-slate-500 text-sm text-center py-8">No stories</p>
  </div>
  </div>
</template>
