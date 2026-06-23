<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  options:    { type: Array, required: true }, // [{ value, label, color? }]
  placeholder:{ type: String, default: 'Sélectionner…' },
  small:      { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const open        = ref(false)
const triggerRef  = ref(null)
const pos         = ref({ top: 0, left: 0, width: 0 })

const selected = computed(() => props.options.find(o => o.value === props.modelValue) ?? null)

async function toggleOpen() {
  if (open.value) { open.value = false; return }
  await nextTick()
  const rect       = triggerRef.value.getBoundingClientRect()
  const estHeight  = Math.min(props.options.length * 36 + 8, 232)
  const spaceBelow = window.innerHeight - rect.bottom - 8

  pos.value = {
    left:  rect.left,
    width: rect.width,
    top:   spaceBelow >= estHeight || rect.top < estHeight
      ? rect.bottom + 4
      : rect.top - estHeight - 4,
  }
  open.value = true
}

function select(value) {
  emit('update:modelValue', value)
  open.value = false
}

function onOutside(e) {
  if (!triggerRef.value?.contains(e.target)) open.value = false
}

function onKey(e) {
  if (e.key === 'Escape' && open.value) {
    open.value = false
    e.stopPropagation()
  }
}

onMounted(() => {
  document.addEventListener('mousedown', onOutside)
  document.addEventListener('keydown', onKey)
})
onUnmounted(() => {
  document.removeEventListener('mousedown', onOutside)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <div ref="triggerRef">
    <!-- Trigger button -->
    <button
      type="button"
      class="w-full flex items-center justify-between gap-2 bg-slate-800 border border-slate-700 rounded-lg px-3 text-left transition-colors hover:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
      :class="small ? 'py-1.5 text-xs' : 'py-2 text-sm'"
      @click="toggleOpen"
    >
      <div class="flex items-center gap-2 min-w-0">
        <div
          v-if="selected?.color"
          class="w-2 h-2 rounded-full flex-shrink-0"
          :style="{ backgroundColor: selected.color }"
        />
        <span class="truncate" :class="selected ? 'text-slate-200' : 'text-slate-500'">
          {{ selected?.label || placeholder }}
        </span>
      </div>
      <!-- Chevron -->
      <svg
        class="w-4 h-4 text-slate-500 flex-shrink-0 transition-transform duration-150"
        :class="{ 'rotate-180': open }"
        viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"
      >
        <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
      </svg>
    </button>

    <!-- Dropdown (teleported to body to escape overflow clipping) -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition ease-out duration-100 origin-top"
        enter-from-class="opacity-0 scale-y-95"
        enter-to-class="opacity-100 scale-y-100"
        leave-active-class="transition ease-in duration-75 origin-top"
        leave-from-class="opacity-100 scale-y-100"
        leave-to-class="opacity-0 scale-y-95"
      >
        <div
          v-if="open"
          class="fixed bg-slate-800 border border-slate-700 rounded-lg shadow-2xl overflow-hidden"
          style="z-index: 9999"
          :style="{ top: `${pos.top}px`, left: `${pos.left}px`, width: `${pos.width}px` }"
        >
          <div class="max-h-56 overflow-y-auto py-1">
            <button
              v-for="opt in options"
              :key="opt.value"
              type="button"
              class="w-full flex items-center gap-2.5 px-3 py-2 text-left transition-colors hover:bg-slate-700/80"
              :class="[
                opt.value === modelValue ? 'bg-slate-700/50' : '',
                small ? 'text-xs' : 'text-sm',
              ]"
              @click="select(opt.value)"
            >
              <div
                v-if="opt.color"
                class="w-2 h-2 rounded-full flex-shrink-0"
                :style="{ backgroundColor: opt.color }"
              />
              <span
                class="flex-1"
                :class="opt.value === modelValue ? 'text-white font-medium' : 'text-slate-300'"
              >
                {{ opt.label }}
              </span>
              <!-- Checkmark -->
              <svg
                v-if="opt.value === modelValue"
                class="w-3.5 h-3.5 text-slate-400 flex-shrink-0"
                viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"
              >
                <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
