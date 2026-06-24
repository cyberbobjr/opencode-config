<script setup>
import { ref, computed } from 'vue'
import { STATUS_LABELS, STATUS_COLORS, PRIORITY_COLORS, STACK_COLORS } from '../constants.js'

const props = defineProps({
  stories: { type: Array, required: true },
})
const emit = defineEmits(['open-modal'])

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

const sorted = computed(() => {
  const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 }
  return [...props.stories].sort((a, b) => {
    let av = a[sortKey.value]
    let bv = b[sortKey.value]
    if (sortKey.value === 'priority') {
      av = PRIORITY_ORDER[av] ?? 99
      bv = PRIORITY_ORDER[bv] ?? 99
    }
    if (av === undefined) av = ''
    if (bv === undefined) bv = ''
    if (av < bv) return -sortDir.value
    if (av > bv) return sortDir.value
    return 0
  })
})

function sortIcon(key) {
  if (sortKey.value !== key) return '↕'
  return sortDir.value === 1 ? '↑' : '↓'
}

function priorityLabel(p) {
  return { low: 'Low', medium: 'Med.', high: 'High', critical: 'Crit.' }[p] ?? p
}
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="border-b border-slate-700">
          <th
            v-for="col in [
              { key: 'id', label: 'ID' },
              { key: 'title', label: 'Title' },
              { key: 'status', label: 'Status' },
              { key: 'priority', label: 'Priority' },
              { key: 'stack', label: 'Stack' },
            ]"
            :key="col.key"
            class="text-left px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider cursor-pointer hover:text-slate-300 whitespace-nowrap"
            @click="setSort(col.key)"
          >
            {{ col.label }} <span class="text-slate-600">{{ sortIcon(col.key) }}</span>
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
          <td class="px-3 py-2 whitespace-nowrap">
            <span class="text-xs font-medium" :class="PRIORITY_COLORS[s.priority]">
              {{ priorityLabel(s.priority) }}
            </span>
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
</template>
