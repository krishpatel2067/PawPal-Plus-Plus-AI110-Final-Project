/**
 * src/hooks/useTasks.js
 * ---------------------
 * Fetches all tasks once and applies filtering, sorting, and conflict
 * detection entirely client-side. The backend is never asked to filter or
 * sort — it only stores and mutates data.
 *
 * Each returned task gets a `conflicted: boolean` field indicating whether
 * its time window overlaps with another task that shares a pet on the same day.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  getTasks,
  createTask as apiCreateTask,
  deleteTask as apiDeleteTask,
  completeTask as apiCompleteTask,
} from '@/api/client'

// Priority sort order: lower number = higher priority
const PRIORITY_ORDER = { HIGH: 1, MEDIUM: 2, LOW: 3 }

/**
 * Returns true when two timed tasks overlap on the same date and share a pet.
 */
function overlaps(a, b) {
  if (a.date !== b.date) return false
  if (!a.time_start || !a.duration_minutes) return false
  if (!b.time_start || !b.duration_minutes) return false
  if (!a.pet_ids.some((id) => b.pet_ids.includes(id))) return false

  const toMin = (hhmm) => {
    const [h, m] = hhmm.split(':').map(Number)
    return h * 60 + m
  }
  const aStart = toMin(a.time_start)
  const bStart = toMin(b.time_start)
  return aStart < bStart + b.duration_minutes && bStart < aStart + a.duration_minutes
}

/** Adds a `conflicted` boolean to every task. Runs over the full raw list so
 *  conflicts between tasks in different filter groups are still caught. */
function detectConflicts(tasks) {
  return tasks.map((task) => ({
    ...task,
    conflicted: tasks.some((other) => other.id !== task.id && overlaps(task, other)),
  }))
}

/** Filter by pet: 'all' | 'unassigned' | <pet_uuid> */
function filterByPet(tasks, filterPet) {
  if (!filterPet || filterPet === 'all') return tasks
  if (filterPet === 'unassigned') return tasks.filter((t) => t.pet_ids.length === 0)
  return tasks.filter((t) => t.pet_ids.includes(filterPet))
}

/** Filter by completion status: 'all' | 'completed' | 'incomplete' */
function filterByStatus(tasks, filterStatus) {
  if (!filterStatus || filterStatus === 'all') return tasks
  if (filterStatus === 'completed') return tasks.filter((t) => t.completed)
  if (filterStatus === 'incomplete') return tasks.filter((t) => !t.completed)
  return tasks
}

/**
 * Sort by an ordered list of { key, dir } entries. Entries are applied
 * left-to-right so the first is the primary sort, the second is the
 * tiebreaker, etc. Untimed tasks sort after timed tasks within the same date
 * regardless of direction (direction flips the date order, not the timed/untimed rule).
 *
 * @param {{ key: string, dir: 'asc'|'desc' }[]} sortBy
 */
function sortTasks(tasks, sortBy) {
  if (!sortBy.length) return tasks

  return [...tasks].sort((a, b) => {
    for (const { key, dir } of sortBy) {
      const flip = dir === 'desc' ? -1 : 1

      if (key === 'Priority') {
        const diff = (PRIORITY_ORDER[a.priority] ?? 99) - (PRIORITY_ORDER[b.priority] ?? 99)
        if (diff !== 0) return diff * flip
      }

      if (key === 'Date & Time') {
        if (a.date < b.date) return -1 * flip
        if (a.date > b.date) return  1 * flip
        // Same date — timed tasks always come before untimed (direction-independent)
        if (a.time_start && !b.time_start) return -1
        if (!a.time_start && b.time_start) return  1
        if (a.time_start && b.time_start && a.time_start !== b.time_start) {
          return (a.time_start < b.time_start ? -1 : 1) * flip
        }
      }
    }
    return 0
  })
}

/**
 * @param {Object} params
 * @param {string}   params.filterPet    - 'all' | 'unassigned' | <pet_uuid>
 * @param {string}   params.filterStatus - 'all' | 'completed' | 'incomplete'
 * @param {string[]} params.sortBy       - ordered keys, e.g. ['Priority', 'Date & Time']
 */
export function useTasks({ filterPet = 'all', filterStatus = 'all', sortBy = [] } = {}) {
  const [allTasks, setAllTasks] = useState([])   // raw from server, with conflict flags
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const raw = await getTasks()
      // Conflict detection runs on the full unfiltered list so a conflict
      // between tasks in different pet groups is still visible.
      setAllTasks(detectConflicts(raw))
    } catch (err) {
      setError(err.message)
      console.error('[useTasks] fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refetch() }, [refetch])

  // Derive the displayed list from allTasks whenever filters/sort change —
  // no extra API call needed.
  const tasks = sortTasks(
    filterByStatus(filterByPet(allTasks, filterPet), filterStatus),
    sortBy
  )

  const addTask = async (data) => {
    await apiCreateTask(data)
    await refetch()
  }

  const deleteTask = async (taskId) => {
    await apiDeleteTask(taskId)
    await refetch()
  }

  const completeTask = async (taskId) => {
    await apiCompleteTask(taskId)
    await refetch()
  }

  return { tasks, loading, error, addTask, deleteTask, completeTask, refetch }
}
