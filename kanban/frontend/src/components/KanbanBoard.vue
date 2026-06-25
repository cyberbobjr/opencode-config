<script setup>
import { reactive, ref, watch } from 'vue'
import draggable from 'vuedraggable'
import KanbanCard from './KanbanCard.vue'
import { KANBAN_COLUMNS } from '../constants.js'

const DONE_PREVIEW = 8

const props = defineProps({
  stories:   { type: Array,   required: true },
  noSession: { type: Boolean, default: false },
})
const emit = defineEmits(['move', 'reorder', 'open-modal', 'trigger'])

const showAllDone = ref(false)

function canMove(evt) {
  if (!props.noSession) return true
  return evt.from === evt.to  // allow same-column reorder only
}

// Local mutable lists per column — vuedraggable needs to mutate them
const localCols = reactive(
  Object.fromEntries(KANBAN_COLUMNS.map(c => [c.status, []]))
)

watch(
  () => props.stories,
  (newStories) => {
    KANBAN_COLUMNS.forEach(col => {
      const filtered = newStories.filter(s => s.status === col.status)
      if (col.status === 'completed') {
        filtered.sort((a, b) => (b.updated_at ?? '').localeCompare(a.updated_at ?? ''))
      } else {
        filtered.sort((a, b) => (a.order ?? 9999) - (b.order ?? 9999))
      }
      localCols[col.status] = [...filtered]
    })
  },
  { immediate: true, deep: true }
)

function handleChange(change, status) {
  if (change.added) {
    emit('move', { id: change.added.element.id, status })
  } else if (change.moved) {
    emit('reorder', { status, order: localCols[status].map(s => s.id) })
  }
}
</script>

<template>
  <div class="flex gap-4 overflow-x-auto pb-4 min-h-[60vh]">
    <div
      v-for="col in KANBAN_COLUMNS"
      :key="col.status"
      class="flex-shrink-0 w-60"
    >
      <!-- Column header -->
      <div class="flex items-center gap-2 mb-2 px-1">
        <div class="w-2 h-2 rounded-full" :style="{ backgroundColor: col.color }" />
        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wide truncate">{{ col.label }}</span>
        <span
          v-if="localCols[col.status].length"
          class="ml-auto text-xs text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded"
        >
          {{ localCols[col.status].length }}
        </span>
      </div>

      <!-- Done column: static list with collapse -->
      <template v-if="col.status === 'completed'">
        <div class="min-h-12 rounded-lg bg-slate-800/40 p-2 space-y-2 border border-slate-800">
          <KanbanCard
            v-for="story in (showAllDone ? localCols.completed : localCols.completed.slice(0, DONE_PREVIEW))"
            :key="story.id"
            :story="story"
            :no-session="noSession"
            @click="emit('open-modal', story.id)"
            @trigger="emit('trigger', story.id)"
            @move="(status) => emit('move', { id: story.id, status })"
          />
          <button
            v-if="localCols.completed.length > DONE_PREVIEW"
            class="w-full text-xs text-slate-500 hover:text-slate-300 py-1.5 transition-colors"
            @click="showAllDone = !showAllDone"
          >
            {{ showAllDone
              ? '↑ Réduire'
              : `↓ Voir les ${localCols.completed.length - DONE_PREVIEW} autres` }}
          </button>
        </div>
      </template>

      <!-- All other columns: draggable -->
      <draggable
        v-else
        v-model="localCols[col.status]"
        group="kanban"
        item-key="id"
        class="min-h-12 rounded-lg bg-slate-800/40 p-2 space-y-2 border border-slate-800"
        ghost-class="opacity-30"
        chosen-class="drag-chosen"
        :move="canMove"
        @change="(e) => handleChange(e, col.status)"
      >
        <template #item="{ element }">
          <KanbanCard
            :story="element"
            :no-session="noSession"
            @click="emit('open-modal', element.id)"
            @trigger="emit('trigger', element.id)"
            @move="(status) => emit('move', { id: element.id, status })"
          />
        </template>
      </draggable>
    </div>
  </div>
</template>
