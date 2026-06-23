<script setup>
import { ref, computed, watch } from 'vue'
import { PIPELINE_STEPS, STATUS_LABELS, STATUS_COLORS } from '../constants.js'

const props = defineProps({
  stories: { type: Array, required: true },
})
const emit = defineEmits(['open-modal'])

const selectedId = ref(null)

const inProgressStories = computed(() =>
  props.stories.filter(s => !['pending', 'completed', 'blocked'].includes(s.status))
    .sort((a, b) => {
      const aLast = a.history?.at(-1)?.ts ?? ''
      const bLast = b.history?.at(-1)?.ts ?? ''
      return bLast.localeCompare(aLast)
    })
)

const activeStory = computed(() =>
  props.stories.find(s => s.id === selectedId.value) ??
  inProgressStories.value[0] ??
  null
)

watch(inProgressStories, (stories) => {
  if (!selectedId.value || !stories.find(s => s.id === selectedId.value)) {
    selectedId.value = stories[0]?.id ?? null
  }
}, { immediate: true })

function stepIndex(story) {
  return PIPELINE_STEPS.findIndex(p => p.status === story?.status)
}
</script>

<template>
  <div class="max-w-3xl mx-auto py-8">
    <!-- Story selector -->
    <div v-if="inProgressStories.length > 1" class="flex items-center gap-3 mb-6">
      <span class="text-sm text-slate-400">Story active :</span>
      <select
        v-model="selectedId"
        class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:border-slate-500 focus:outline-none"
      >
        <option v-for="s in inProgressStories" :key="s.id" :value="s.id">
          {{ s.id }} — {{ s.title }}
        </option>
      </select>
    </div>

    <div v-if="!activeStory" class="text-center text-slate-500 py-16">
      Aucune story en cours
    </div>

    <template v-else>
      <!-- Story header -->
      <div
        class="bg-slate-800 rounded-xl border border-slate-700 p-6 mb-6 cursor-pointer hover:border-slate-500 transition-colors"
        @click="emit('open-modal', activeStory.id)"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <span class="text-xs font-mono text-slate-500 mb-1 block">{{ activeStory.id }}</span>
            <h2 class="text-lg font-semibold text-slate-100">{{ activeStory.title }}</h2>
          </div>
          <span
            class="text-xs px-2 py-1 rounded-full font-medium flex-shrink-0"
            :style="{ backgroundColor: STATUS_COLORS[activeStory.status] + '30', color: STATUS_COLORS[activeStory.status] }"
          >
            {{ STATUS_LABELS[activeStory.status] }}
          </span>
        </div>
      </div>

      <!-- Pipeline steps -->
      <div class="flex items-center gap-0 overflow-x-auto pb-2">
        <template v-for="(step, idx) in PIPELINE_STEPS" :key="step.status">
          <!-- Step -->
          <div
            class="flex flex-col items-center flex-shrink-0 px-3"
            :class="{
              'opacity-30': idx < stepIndex(activeStory),
              'opacity-100': idx >= stepIndex(activeStory),
            }"
          >
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold mb-1 border-2 transition-all"
              :style="idx === stepIndex(activeStory)
                ? { backgroundColor: STATUS_COLORS[step.status], borderColor: STATUS_COLORS[step.status], color: '#fff' }
                : idx < stepIndex(activeStory)
                  ? { backgroundColor: '#1e293b', borderColor: '#334155', color: '#475569' }
                  : { backgroundColor: '#1e293b', borderColor: STATUS_COLORS[step.status] + '60', color: STATUS_COLORS[step.status] + '80' }
              "
            >
              <span v-if="idx < stepIndex(activeStory)">✓</span>
              <span v-else>{{ idx + 1 }}</span>
            </div>
            <span
              class="text-xs text-center leading-tight"
              :class="idx === stepIndex(activeStory) ? 'text-slate-200 font-semibold' : 'text-slate-600'"
              style="max-width: 60px"
            >
              {{ step.label }}
            </span>
          </div>
          <!-- Connector -->
          <div
            v-if="idx < PIPELINE_STEPS.length - 1"
            class="flex-1 h-0.5 min-w-3 flex-shrink-0"
            :class="idx < stepIndex(activeStory) ? 'bg-slate-700' : 'bg-slate-800'"
          />
        </template>
      </div>

      <!-- Notes preview -->
      <div v-if="activeStory.notes" class="mt-6 bg-slate-800/60 border border-slate-700 rounded-lg p-4">
        <p class="text-xs text-slate-500 mb-1">Notes</p>
        <p class="text-sm text-slate-300 line-clamp-3">{{ activeStory.notes }}</p>
      </div>
    </template>
  </div>
</template>
