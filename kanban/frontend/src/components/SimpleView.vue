<script setup>
import { reactive, ref, watch } from 'vue'
import draggable from 'vuedraggable'
import KanbanCard from './KanbanCard.vue'
import { SIMPLE_GROUPS } from '../constants.js'

const DONE_PREVIEW = 8

const props = defineProps({
  stories:   { type: Array,   required: true },
  noSession: { type: Boolean, default: false },
})
const emit = defineEmits(['move', 'open-modal', 'trigger'])

const showAllDone = ref(false)

function canMove(evt) {
  if (!props.noSession) return true
  return evt.from === evt.to
}

const localCols = reactive(
  Object.fromEntries(SIMPLE_GROUPS.map(g => [g.id, []]))
)

watch(
  () => props.stories,
  (newStories) => {
    SIMPLE_GROUPS.forEach(group => {
      const filtered = newStories.filter(s => group.statuses.includes(s.status))
      if (group.id === 'termine') {
        filtered.sort((a, b) => (b.updated_at ?? '').localeCompare(a.updated_at ?? ''))
      } else {
        filtered.sort((a, b) => (a.order ?? 9999) - (b.order ?? 9999))
      }
      localCols[group.id] = [...filtered]
    })
  },
  { immediate: true, deep: true }
)

function handleChange(change, group) {
  if (change.added) {
    emit('move', { id: change.added.element.id, status: group.dropTo })
  }
}
</script>

<template>
  <div class="grid grid-cols-5 gap-4 min-h-[60vh]">
    <div v-for="group in SIMPLE_GROUPS" :key="group.id" class="flex flex-col">
      <!-- Header -->
      <div
        class="flex items-center gap-2 mb-2 px-2 py-1.5 rounded-t-lg"
        :style="{ backgroundColor: group.color + '20', borderBottom: `2px solid ${group.color}` }"
      >
        <span class="text-sm font-semibold truncate" :style="{ color: group.color }">{{ group.label }}</span>
        <span class="ml-auto text-xs px-1.5 rounded-full" :style="{ backgroundColor: group.color + '30', color: group.color }">
          {{ localCols[group.id].length }}
        </span>
      </div>

      <!-- Done/Blocked column: drop-only draggable (pull:false prevents dragging out) -->
      <template v-if="group.id === 'termine'">
        <draggable
          :model-value="showAllDone ? localCols.termine : localCols.termine.slice(0, DONE_PREVIEW)"
          :group="{ name: 'simple', pull: false, put: true }"
          item-key="id"
          :sort="false"
          class="flex-1 min-h-12 rounded-b-lg bg-slate-800/40 p-2 space-y-2 border border-t-0 border-slate-800"
          ghost-class="opacity-30"
          chosen-class="drag-chosen"
          :move="canMove"
          @change="(e) => handleChange(e, group)"
        >
          <template #item="{ element }">
            <KanbanCard
              :story="element"
              :show-status="true"
              :no-session="noSession"
              @click="emit('open-modal', element.id)"
              @trigger="emit('trigger', element.id)"
              @move="(status) => emit('move', { id: element.id, status })"
            />
          </template>
          <template #footer>
            <button
              v-if="localCols.termine.length > DONE_PREVIEW"
              class="w-full text-xs text-slate-500 hover:text-slate-300 py-1.5 transition-colors"
              @click="showAllDone = !showAllDone"
            >
              {{ showAllDone
                ? '↑ Réduire'
                : `↓ Voir les ${localCols.termine.length - DONE_PREVIEW} autres` }}
            </button>
          </template>
        </draggable>
      </template>

      <!-- All other columns: draggable -->
      <draggable
        v-else
        v-model="localCols[group.id]"
        group="simple"
        item-key="id"
        class="flex-1 min-h-12 rounded-b-lg bg-slate-800/40 p-2 space-y-2 border border-t-0 border-slate-800"
        ghost-class="opacity-30"
        chosen-class="drag-chosen"
        :move="canMove"
        @change="(e) => handleChange(e, group)"
      >
        <template #item="{ element }">
          <KanbanCard
            :story="element"
            :show-status="true"
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
