<script setup>
import { computed } from 'vue'
import { STACK_COLORS, STATUS_COLORS, STATUS_LABELS, TRIGGERABLE_STATUSES, KANBAN_COLUMNS, AUDIENCE_COLORS, AUDIENCE_OPTIONS } from '../constants.js'

const props = defineProps({
  story:     { type: Object,  required: true },
  showStatus: { type: Boolean, default: false },
  noSession:  { type: Boolean, default: false },
})
const emit = defineEmits(['click', 'trigger', 'move'])

const colIndex = computed(() => KANBAN_COLUMNS.findIndex(c => c.status === props.story.status))
const prevCol  = computed(() => colIndex.value > 0 ? KANBAN_COLUMNS[colIndex.value - 1] : null)
const nextCol  = computed(() => colIndex.value < KANBAN_COLUMNS.length - 1 ? KANBAN_COLUMNS[colIndex.value + 1] : null)
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
        <!-- Agent status: only show for active (non-terminal) stories -->
        <template v-if="story.agent_status && story.status !== 'completed' && story.status !== 'blocked'">
          <span
            v-if="story.agent_status === 'awaiting_input'"
            class="flex items-center gap-0.5 text-xs text-blue-400 px-1.5 py-0.5 rounded bg-blue-950 border border-blue-700 animate-pulse font-medium"
            title="OpenCode is waiting for your input"
          >⚡ Action</span>
          <svg
            v-else
            class="w-3.5 h-3.5 text-amber-400 animate-spin flex-shrink-0"
            :title="`OpenCode: ${story.agent_status}`"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"
          ><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
        </template>
        <span
          v-if="showStatus"
          class="text-xs px-1.5 py-0.5 rounded font-medium"
          :style="{ backgroundColor: STATUS_COLORS[story.status] + '30', color: STATUS_COLORS[story.status] }"
        >{{ STATUS_LABELS[story.status] }}</span>
      </div>
    </div>

    <!-- Title -->
    <p class="text-sm text-slate-200 leading-snug mb-2 line-clamp-2">{{ story.title }}</p>

    <!-- Footer: audience + stack + TDD/QA badges -->
    <div class="flex items-center gap-1.5 flex-wrap">
      <span
        v-for="val in (story.audience || [])"
        :key="val"
        class="text-xs px-1.5 py-0.5 rounded font-medium"
        :style="{ backgroundColor: (AUDIENCE_COLORS[val] ?? '#6b7280') + '25', color: AUDIENCE_COLORS[val] ?? '#9ca3af' }"
      >{{ AUDIENCE_OPTIONS.find(o => o.value === val)?.label ?? val }}</span>
      <span
        v-for="tag in (story.stack || [])"
        :key="tag"
        class="text-xs px-1.5 py-0.5 rounded font-medium"
        :style="{ backgroundColor: (STACK_COLORS[tag] ?? '#6b7280') + '25', color: STACK_COLORS[tag] ?? '#9ca3af' }"
      >{{ tag }}</span>
      <span v-if="story.tdd?.status === 'done' || story.tdd?.status === 'passed'" class="ml-auto text-xs text-emerald-400" title="TDD OK">✓ TDD</span>
      <span v-if="story.qa?.status === 'done'  || story.qa?.status === 'passed'"  class="text-xs text-pink-400"    title="QA OK">✓ QA</span>
    </div>

    <!-- Move buttons — visible on hover -->
    <div class="opacity-0 group-hover:opacity-100 transition-opacity flex justify-between gap-1 mt-2 -mx-0.5">
      <button
        v-if="prevCol"
        class="flex-1 text-xs px-1.5 py-1 rounded truncate text-left transition-colors"
        :class="noSession
          ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
          : 'bg-slate-700 hover:bg-slate-600 text-slate-400 hover:text-slate-200'"
        :title="noSession ? 'No OpenCode session' : `← ${prevCol.label}`"
        :disabled="noSession"
        @click.stop="!noSession && emit('move', prevCol.status)"
      >← {{ prevCol.label }}</button>
      <div v-else class="flex-1" />
      <button
        v-if="nextCol"
        class="flex-1 text-xs px-1.5 py-1 rounded truncate text-right transition-colors"
        :class="noSession
          ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
          : 'bg-slate-700 hover:bg-slate-600 text-slate-400 hover:text-slate-200'"
        :title="noSession ? 'No OpenCode session' : `${nextCol.label} →`"
        :disabled="noSession"
        @click.stop="!noSession && emit('move', nextCol.status)"
      >{{ nextCol.label }} →</button>
    </div>

    <!-- ▶ Trigger button — visible on hover, only for triggerable statuses -->
    <button
      v-if="TRIGGERABLE_STATUSES.has(story.status)"
      class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-md transition-colors"
      :class="noSession
        ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
        : 'bg-slate-700 hover:bg-emerald-700 text-slate-400 hover:text-white'"
      :title="noSession ? 'No OpenCode session' : 'Run OpenCode command'"
      :disabled="noSession"
      @click.stop="!noSession && emit('trigger', story.id)"
    >
      <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path d="M6.3 2.84A1.5 1.5 0 0 0 4 4.11v11.78a1.5 1.5 0 0 0 2.3 1.27l9.344-5.891a1.5 1.5 0 0 0 0-2.538L6.3 2.84Z"/>
      </svg>
    </button>
  </div>
</template>
