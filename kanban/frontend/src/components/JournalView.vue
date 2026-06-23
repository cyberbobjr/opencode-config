<script setup>
import { ref, onMounted } from 'vue'
import { loadHistory } from '../api.js'
import { STATUS_LABELS, STATUS_COLORS } from '../constants.js'

const history = ref([])
const loading = ref(false)
const error = ref(null)

onMounted(async () => {
  loading.value = true
  try {
    history.value = await loadHistory()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

function groupByDate(items) {
  const groups = {}
  for (const item of items) {
    const date = item.ts?.slice(0, 10) ?? 'inconnu'
    if (!groups[date]) groups[date] = []
    groups[date].push(item)
  }
  return Object.entries(groups).sort(([a], [b]) => b.localeCompare(a))
}

function formatTime(ts) {
  if (!ts) return ''
  return ts.slice(11, 16)
}

function formatDate(d) {
  if (!d || d === 'inconnu') return 'Date inconnue'
  const dt = new Date(d)
  return dt.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
}
</script>

<template>
  <div class="max-w-3xl mx-auto py-6">
    <p v-if="loading" class="text-slate-500 text-sm text-center py-8">Chargement…</p>
    <p v-else-if="error" class="text-red-400 text-sm text-center py-8">{{ error }}</p>
    <p v-else-if="!history.length" class="text-slate-500 text-sm text-center py-8">Aucun historique</p>

    <div v-else class="space-y-8">
      <div v-for="[date, entries] in groupByDate(history)" :key="date">
        <!-- Date header -->
        <div class="flex items-center gap-3 mb-3">
          <div class="h-px flex-1 bg-slate-800" />
          <span class="text-xs text-slate-500 font-medium uppercase tracking-wider">{{ formatDate(date) }}</span>
          <div class="h-px flex-1 bg-slate-800" />
        </div>

        <!-- Entries -->
        <div class="space-y-2">
          <div
            v-for="(entry, idx) in entries"
            :key="idx"
            class="flex items-start gap-3 py-2"
          >
            <!-- Time -->
            <span class="text-xs text-slate-600 font-mono w-10 flex-shrink-0 mt-0.5">
              {{ formatTime(entry.ts) }}
            </span>

            <!-- Dot -->
            <div
              class="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
              :style="{ backgroundColor: STATUS_COLORS[entry.to] ?? STATUS_COLORS[entry.status] ?? '#6b7280' }"
            />

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs font-mono text-slate-400">{{ entry.story_id }}</span>
                <span class="text-xs text-slate-300">{{ entry.action ?? 'mis à jour' }}</span>
                <span v-if="entry.to" class="text-xs px-1.5 py-0.5 rounded" :style="{ backgroundColor: STATUS_COLORS[entry.to] + '25', color: STATUS_COLORS[entry.to] }">
                  → {{ STATUS_LABELS[entry.to] ?? entry.to }}
                </span>
                <span v-if="entry.actor" class="text-xs text-slate-600">par {{ entry.actor }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
