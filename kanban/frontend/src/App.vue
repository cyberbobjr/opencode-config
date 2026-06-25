<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { loadConfig, loadOCStatus, loadStories, updateStory, moveStory, reorderStories, createStory, deleteStory, triggerStory } from './api.js'
import { STATUS_LABELS } from './constants.js'
import StatsBar from './components/StatsBar.vue'
import KanbanBoard from './components/KanbanBoard.vue'
import SimpleView from './components/SimpleView.vue'
import FocusView from './components/FocusView.vue'
import JournalView from './components/JournalView.vue'
import ListView from './components/ListView.vue'
import StoryModal from './components/StoryModal.vue'

// ── State ─────────────────────────────────────────────────────────────
const stories       = ref([])
const currentView   = ref(localStorage.getItem('kanban-view') ?? 'kanban')
const modalStoryId  = ref(null)
const searchQuery   = ref('')
const autoTrigger   = ref(localStorage.getItem('kanban-auto-trigger') !== 'false')
const ocConnected   = ref(false)
const toasts        = ref([])
const loading       = ref(false)
const appTitle      = ref('Kanban')
const ocBusy        = ref(false)
const ocTotal       = ref(0)
const ocProcessing  = ref(0)

// ── Derived ───────────────────────────────────────────────────────────
const filteredStories = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return stories.value
  return stories.value.filter(s =>
    s.id.toLowerCase().includes(q) ||
    s.title.toLowerCase().includes(q) ||
    (s.stack || []).some(t => t.toLowerCase().includes(q))
  )
})

const modalStory = computed(() =>
  stories.value.find(s => s.id === modalStoryId.value) ?? null
)

const modalStoryPosition = computed(() => {
  if (!modalStory.value || modalStory.value.status !== 'pending') return null
  const pending = [...stories.value.filter(s => s.status === 'pending')]
    .sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0) || a.id.localeCompare(b.id))
  const idx = pending.findIndex(s => s.id === modalStory.value.id)
  return idx >= 0 ? { rank: idx + 1, total: pending.length } : null
})

// ── API helpers ───────────────────────────────────────────────────────
async function fetchStories() {
  try {
    stories.value = await loadStories()
  } catch {
    toast('Failed to load stories', 'error')
  }
}

function toast(message, variant = 'success') {
  const id = Date.now()
  toasts.value = [...toasts.value, { id, message, variant }]
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 4000)
}

// ── Event handlers ────────────────────────────────────────────────────
async function handleMove({ id, status }) {
  try {
    await moveStory(id, status, { noTrigger: !autoTrigger.value })
    await fetchStories()
    toast(`→ ${STATUS_LABELS[status]}`)
  } catch {
    toast('Move failed', 'error')
    await fetchStories()
  }
}

async function handleTrigger(id) {
  try {
    const result = await triggerStory(id)
    toast(`▶ ${result.command}`)
  } catch {
    toast('Trigger failed', 'error')
  }
}

async function handleReorder({ status, order }) {
  try {
    await reorderStories(status, order)
  } catch {
    /* silent — reorder is cosmetic */
  }
}

async function handleSave({ id, changes }) {
  try {
    await updateStory(id, changes)
    await fetchStories()
    toast('Saved')
    modalStoryId.value = null
  } catch {
    toast('Save failed', 'error')
  }
}

async function handleDelete({ id }) {
  try {
    await deleteStory(id)
    modalStoryId.value = null
    await fetchStories()
    toast('Story deleted')
  } catch {
    toast('Delete failed', 'error')
  }
}

async function handleCreate() {
  try {
    const story = await createStory({
      title: 'New story',
      status: 'pending',
      priority: 'medium',
    })
    await fetchStories()
    modalStoryId.value = story.id
  } catch {
    toast('Creation failed', 'error')
  }
}

watch(currentView, (v) => localStorage.setItem('kanban-view', v))

function toggleAutoTrigger() {
  autoTrigger.value = !autoTrigger.value
  localStorage.setItem('kanban-auto-trigger', String(autoTrigger.value))
}

// ── OC busy polling ───────────────────────────────────────────────────
async function pollOCStatus() {
  try {
    const { busy, total, processing } = await loadOCStatus()
    ocBusy.value = busy
    ocTotal.value = total ?? 0
    ocProcessing.value = processing ?? 0
  } catch {
    ocBusy.value = false
    ocTotal.value = 0
    ocProcessing.value = 0
  }
}

// ── SSE ───────────────────────────────────────────────────────────────
let sse = null
let ocPollTimer = null
onMounted(async () => {
  try {
    const config = await loadConfig()
    appTitle.value = config.app_title ?? 'Kanban'
    document.title = config.app_title ?? 'Kanban'
  } catch { /* keep default */ }
  await fetchStories()
  sse = new EventSource('/api/events')
  sse.addEventListener('open', () => { ocConnected.value = true })
  sse.addEventListener('error', () => { ocConnected.value = false })
  sse.onmessage = (e) => {
    if (e.data === 'refresh') fetchStories()
  }
  await pollOCStatus()
  ocPollTimer = setInterval(pollOCStatus, 2000)
})
onUnmounted(() => {
  sse?.close()
  clearInterval(ocPollTimer)
})
</script>

<template>
  <div class="min-h-screen bg-slate-900 text-slate-200 flex flex-col">

    <!-- Header -->
    <header class="sticky top-0 z-30 bg-slate-900/95 backdrop-blur border-b border-slate-800">
      <div class="flex items-center gap-4 px-6 py-3 flex-wrap">
        <!-- Title -->
        <h1 class="text-base font-bold text-white mr-2 flex-shrink-0">
          {{ appTitle }}
        </h1>

        <!-- Search -->
        <input
          v-model="searchQuery"
          type="search"
          placeholder="Search…"
          class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-slate-500 focus:outline-none w-48"
        />

        <!-- View toggle -->
        <div class="flex items-center gap-1 bg-slate-800 border border-slate-700 rounded-lg p-0.5">
          <button
            v-for="view in [
              { id: 'kanban',  label: 'Kanban'   },
              { id: 'simple',  label: 'Simple'   },
              { id: 'focus',   label: 'Focus'    },
              { id: 'journal', label: 'Journal'  },
              { id: 'list',    label: 'List'     },
            ]"
            :key="view.id"
            class="text-xs px-3 py-1.5 rounded transition-colors"
            :class="currentView === view.id
              ? 'bg-primary text-white font-medium'
              : 'text-slate-400 hover:text-slate-200'"
            @click="currentView = view.id"
          >
            {{ view.label }}
          </button>
        </div>

        <!-- Spacer -->
        <div class="flex-1" />

        <!-- Auto-trigger -->
        <button
          class="text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-colors"
          :class="autoTrigger
            ? 'border-emerald-700 text-emerald-400 bg-emerald-900/20'
            : 'border-slate-700 text-slate-500'"
          @click="toggleAutoTrigger"
        >
          <span class="w-2 h-2 rounded-full" :class="autoTrigger ? 'bg-emerald-400' : 'bg-slate-600'" />
          Auto-trigger
        </button>

        <!-- OC sessions indicator -->
        <div
          class="flex items-center gap-2 text-xs px-2.5 py-1.5 rounded-lg border"
          :class="ocConnected ? 'border-slate-700 text-slate-400' : 'border-slate-800 text-slate-600'"
          :title="`${ocTotal} session(s) connected · ${ocProcessing} processing`"
        >
          <!-- connected dot -->
          <span
            class="w-2 h-2 rounded-full flex-shrink-0"
            :class="ocConnected ? 'bg-emerald-400' : 'bg-slate-600'"
          />
          <!-- session count -->
          <span>{{ ocTotal }}</span>
          <!-- processing badge -->
          <span
            v-if="ocProcessing > 0"
            class="flex items-center gap-1 text-amber-400 animate-pulse"
          >
            <i class="ti ti-loader-2 animate-spin" />
            {{ ocProcessing }}
          </span>
        </div>

        <!-- New story -->
        <button
          class="text-xs bg-primary hover:bg-primary-dark text-white px-4 py-1.5 rounded-lg transition-colors font-medium"
          @click="handleCreate"
        >
          + Story
        </button>
      </div>
    </header>

    <!-- Stats bar -->
    <StatsBar :stories="stories" />

    <!-- Views -->
    <main class="flex-1 px-6 py-5 overflow-hidden">
      <KanbanBoard
        v-if="currentView === 'kanban'"
        :stories="filteredStories"
        @move="handleMove"
        @reorder="handleReorder"
        @open-modal="modalStoryId = $event"
        @trigger="handleTrigger"
      />
      <SimpleView
        v-else-if="currentView === 'simple'"
        :stories="filteredStories"
        @move="handleMove"
        @open-modal="modalStoryId = $event"
        @trigger="handleTrigger"
      />
      <FocusView
        v-else-if="currentView === 'focus'"
        :stories="filteredStories"
        @open-modal="modalStoryId = $event"
      />
      <JournalView v-else-if="currentView === 'journal'" />
      <ListView
        v-else-if="currentView === 'list'"
        :stories="filteredStories"
        @open-modal="modalStoryId = $event"
      />
    </main>

    <!-- Modal -->
    <StoryModal
      v-if="modalStory"
      :story="modalStory"
      :position="modalStoryPosition"
      @close="modalStoryId = null"
      @save="handleSave"
      @delete="handleDelete"
    />

    <!-- Toasts -->
    <div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 items-end">
      <transition-group name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="text-sm px-4 py-2.5 rounded-lg shadow-lg pointer-events-none"
          :class="t.variant === 'error'
            ? 'bg-red-900/90 text-red-200 border border-red-700'
            : 'bg-emerald-900/90 text-emerald-200 border border-emerald-700'"
        >
          {{ t.message }}
        </div>
      </transition-group>
    </div>
  </div>
</template>

<style>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(1rem);
}
</style>
