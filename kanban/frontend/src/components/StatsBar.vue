<script setup>
import { computed } from 'vue'
import { STATUS_LABELS, STATUS_COLORS } from '../constants.js'

const props = defineProps({
  stories: { type: Array, required: true },
})

const stats = computed(() => {
  const counts = {}
  for (const s of props.stories) {
    counts[s.status] = (counts[s.status] ?? 0) + 1
  }
  return Object.entries(STATUS_LABELS).map(([status, label]) => ({
    status,
    label,
    color: STATUS_COLORS[status],
    count: counts[status] ?? 0,
  })).filter(s => s.count > 0)
})
</script>

<template>
  <div class="flex items-center gap-3 px-6 py-2 border-b border-slate-800 flex-wrap">
    <span class="text-xs text-slate-500">
      {{ stories.length }} stories
    </span>
    <div class="flex items-center gap-2 flex-wrap">
      <span
        v-for="s in stats"
        :key="s.status"
        class="text-xs px-2 py-0.5 rounded-full font-medium"
        :style="{ backgroundColor: s.color + '25', color: s.color }"
      >
        {{ s.label }} {{ s.count }}
      </span>
    </div>
  </div>
</template>
