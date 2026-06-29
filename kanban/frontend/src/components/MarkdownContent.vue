<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.use({
  gfm: true,
  breaks: true,
})

const props = defineProps({
  content: { type: String, default: '' },
  placeholder: { type: String, default: '' },
})

const html = computed(() => {
  const text = props.content?.trim()
  if (!text) return ''
  return DOMPurify.sanitize(marked.parse(text))
})
</script>

<template>
  <div v-if="html" class="md text-sm" v-html="html" />
  <p v-else-if="placeholder" class="text-sm text-slate-500 italic">{{ placeholder }}</p>
</template>
