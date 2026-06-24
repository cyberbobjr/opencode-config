<script setup>
import { reactive, watch } from 'vue'
import draggable from 'vuedraggable'
import KanbanCard from './KanbanCard.vue'
import { KANBAN_COLUMNS } from '../constants.js'

const props = defineProps({
  stories: { type: Array, required: true },
})
const emit = defineEmits(['move', 'reorder', 'open-modal', 'trigger'])

// Local mutable lists per column — vuedraggable needs to mutate them
const localCols = reactive(
  Object.fromEntries(KANBAN_COLUMNS.map(c => [c.status, []]))
)

watch(
  () => props.stories,
  (newStories) => {
    KANBAN_COLUMNS.forEach(col => {
      localCols[col.status] = [...newStories
        .filter(s => s.status === col.status)
        .sort((a, b) => (a.order ?? 9999) - (b.order ?? 9999))]
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

      <!-- Draggable column body -->
      <draggable
        v-model="localCols[col.status]"
        group="kanban"
        item-key="id"
        class="min-h-12 rounded-lg bg-slate-800/40 p-2 space-y-2 border border-slate-800"
        ghost-class="opacity-30"
        chosen-class="drag-chosen"
        @change="(e) => handleChange(e, col.status)"
      >
        <template #item="{ element }">
          <KanbanCard
            :story="element"
            @click="emit('open-modal', element.id)"
            @trigger="emit('trigger', element.id)"
            @move="(status) => emit('move', { id: element.id, status })"
          />
        </template>
      </draggable>
    </div>
  </div>
</template>
