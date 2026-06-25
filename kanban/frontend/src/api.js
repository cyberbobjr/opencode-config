const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
  return res.json()
}

export function loadConfig() {
  return request('/config')
}

export function loadOCStatus() {
  return request('/opencode/status')
}

export function loadSessions() {
  return request('/sessions')
}

export function loadStories() {
  return request('/stories')
}

export function loadHistory() {
  return request('/history')
}

export function loadStats() {
  return request('/stats')
}

export function updateStory(id, changes) {
  return request(`/stories/${id}`, {
    method: 'PUT',
    body: JSON.stringify(changes),
  })
}

export function moveStory(id, status, { actor = 'dashboard', noTrigger = false } = {}) {
  const qs = noTrigger ? '?no_trigger=true' : ''
  return request(`/stories/${id}/move${qs}`, {
    method: 'PATCH',
    body: JSON.stringify({ status, actor }),
  })
}

export function triggerStory(id) {
  return request(`/stories/${id}/trigger`, { method: 'POST' })
}

export function reorderStories(status, order) {
  return request('/reorder', {
    method: 'POST',
    body: JSON.stringify({ status, order }),
  })
}

export function createStory(data) {
  return request('/stories', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function deleteStory(id) {
  return request(`/stories/${id}`, { method: 'DELETE' })
}
