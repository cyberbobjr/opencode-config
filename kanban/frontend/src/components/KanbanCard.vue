<script setup>
import { PRIORITY_COLORS, STACK_COLORS, STATUS_COLORS, STATUS_LABELS, TRIGGERABLE_STATUSES } from '../constants.js'

const props = defineProps({
  story: { type: Object, required: true },
  showStatus: { type: Boolean, default: false },
})
const emit = defineEmits(['click', 'trigger'])

function prioritySymbol(p) {
  return { low: '▽', medium: '◇', high: '△', critical: '★' }[p] ?? '◇'
}
</script>

<template>
  <div
    class="group relative bg-slate-800 border border-slate-700 rounded-lg p-3 cursor-pointer hover:border-slate-500 hover:bg-slate-750 transition-colors select-none"
    @click="emit('click', story.id)"
  >
    <!-- Header row -->
    <div class="flex items-center justify-between mb-1.5 gap-1">
      <span class="text-xs text-slate-500 font-mono">{{ story.id }}</span>
      <div class="flex items-center gap-1.5">
        <span
          v-if="showStatus"
          class="text-xs px-1.5 py-0.5 rounded font-medium"
          :style="{ backgroundColor: STATUS_COLORS[story.status] + '30', color: STATUS_COLORS[story.status] }"
        >{{ STATUS_LABELS[story.status] }}</span>
        <span class="text-xs" :class="PRIORITY_COLORS[story.priority]">
          {{ prioritySymbol(story.priority) }}
        </span>
      </div>
    </div>

    <!-- Title -->
    <p class="text-sm text-slate-200 leading-snug mb-2 line-clamp-2">{{ story.title }}</p>

    <!-- Footer: stack + TDD/QA badges -->
    <div class="flex items-center gap-1.5 flex-wrap">
      <span
        v-for="tag in (story.stack || [])"
        :key="tag"
        class="text-xs px-1.5 py-0.5 rounded font-medium"
        :style="{ backgroundColor: (STACK_COLORS[tag] ?? '#6b7280') + '25', color: STACK_COLORS[tag] ?? '#9ca3af' }"
      >{{ tag }}</span>
      <span v-if="story.tdd?.status === 'done' || story.tdd?.status === 'passed'" class="ml-auto text-xs text-emerald-400" title="TDD OK">✓ TDD</span>
      <span v-if="story.qa?.status === 'done'  || story.qa?.status === 'passed'"  class="text-xs text-pink-400"    title="QA OK">✓ QA</span>
    </div>

    <!-- ▶ Trigger button — visible on hover, only for triggerable statuses -->
    <button
      v-if="TRIGGERABLE_STATUSES.has(story.status)"
      class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-md bg-slate-700 hover:bg-emerald-700 text-slate-400 hover:text-white"
      title="Lancer la commande OpenCode"
      @click.stop="emit('trigger', story.id)"
    >
      <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path d="M6.3 2.84A1.5 1.5 0 0 0 4 4.11v11.78a1.5 1.5 0 0 0 2.3 1.27l9.344-5.891a1.5 1.5 0 0 0 0-2.538L6.3 2.84Z"/>
      </svg>
    </button>
  </div>
</template>
