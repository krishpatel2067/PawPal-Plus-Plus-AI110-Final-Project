/**
 * src/api/client.js
 * -----------------
 * All communication with the PawPal++ FastAPI backend lives here.
 * Every function is a named async export — components and hooks import
 * only what they need and never construct URLs or handle raw fetch responses
 * themselves.
 *
 * Base URL is read from the Vite env variable VITE_API_BASE_URL so that
 * swapping to a deployed backend only requires changing one env file.
 */

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

/**
 * Internal fetch wrapper. Parses JSON on success, throws a descriptive Error
 * on non-2xx responses. Returns null for 204 No Content.
 */
async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })

  if (res.status === 204) return null

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      // response body was not JSON — use statusText as-is
    }
    throw new Error(detail)
  }

  return res.json()
}

// ── Owner ─────────────────────────────────────────────────────────────────────

/** Returns { name } or throws with status 404 if no owner exists yet. */
export const getOwner = () => request('/owner')

/** Creates a new owner. Body: { name }. Returns { name }. */
export const createOwner = (data) =>
  request('/owner', { method: 'POST', body: JSON.stringify(data) })

/** Permanently deletes all owner, pet, and task data. Returns null. */
export const deleteOwner = () => request('/owner', { method: 'DELETE' })

// ── Pets ──────────────────────────────────────────────────────────────────────

/** Returns an array of pet objects: [{ id, name, species, age_years, notes }]. */
export const getPets = () => request('/pets')

/** Creates a new pet. Body: { name, species, age_years, notes }. Returns the pet. */
export const createPet = (data) =>
  request('/pets', { method: 'POST', body: JSON.stringify(data) })

/** Removes a pet by UUID and scrubs it from all tasks. Returns null. */
export const deletePet = (petId) => request(`/pets/${petId}`, { method: 'DELETE' })

// ── Tasks ─────────────────────────────────────────────────────────────────────

/**
 * Returns all tasks unfiltered and unsorted — the frontend handles
 * filtering and sorting entirely client-side.
 */
export const getTasks = () => request('/tasks')

/**
 * Creates a new task.
 * Body: { name, description, frequency, date, priority, pet_ids,
 *         time_start, duration_minutes }
 */
export const createTask = (data) =>
  request('/tasks', { method: 'POST', body: JSON.stringify(data) })

/** Deletes a task by UUID. Returns null. */
export const deleteTask = (taskId) =>
  request(`/tasks/${taskId}`, { method: 'DELETE' })

/** Marks a task complete and schedules the next recurrence if recurring. */
export const completeTask = (taskId) =>
  request(`/tasks/${taskId}/complete`, { method: 'POST' })

// ── AI Advisor ────────────────────────────────────────────────────────────────

/**
 * Ask the RAG-powered pet-care advisor a question.
 * Body: { question: string }
 * Returns { answer: string, sources: [{ id, title, source }] }
 */
export const askAdvisor = (question) =>
  request('/ask', { method: 'POST', body: JSON.stringify({ question }) });

// ── Slot suggestion ───────────────────────────────────────────────────────────

/**
 * Suggests the earliest available time slot.
 * Body: { duration_minutes, pet_id?, starting_from? }
 * Returns { date, time_start } or null if no slot found in 30 days.
 */
export const suggestSlot = (data) =>
  request('/suggest-slot', { method: 'POST', body: JSON.stringify(data) })
