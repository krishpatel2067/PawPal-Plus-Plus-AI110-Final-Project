/**
 * src/screens/Dashboard.jsx
 * ---------------------------
 * Main app view shown once an owner exists.
 *
 * Layout: two columns on desktop (pets left, tasks right), single column
 * on mobile. Owns all filter/sort state and passes it down to the task
 * components. Also manages the suggestedSlot state so SuggestSlotButton
 * and TaskForm stay decoupled from each other.
 */

import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { usePets } from '@/hooks/usePets'
import { useTasks } from '@/hooks/useTasks'
import AddPetForm from '@/components/pets/AddPetForm'
import PetList from '@/components/pets/PetList'
import TaskFilters from '@/components/tasks/TaskFilters'
import TaskForm from '@/components/tasks/TaskForm'
import TaskList from '@/components/tasks/TaskList'
import SuggestSlotButton from '@/components/tasks/SuggestSlotButton'
import AskPanel from '@/components/advisor/AskPanel'
import SetupAgent from '@/components/advisor/SetupAgent'

export default function Dashboard({ owner, onDeleteOwner }) {
  // ── Filter / sort state ──────────────────────────────────────────────────
  const [filterPet,    setFilterPet]    = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  // sortBy is an ordered array of { key, dir } — earlier index = higher sort priority
  const [sortBy, setSortBy] = useState([])

  // Append { key, dir:'asc' } when enabling; remove when disabling
  const toggleSort = (key) =>
    setSortBy((prev) =>
      prev.some((s) => s.key === key)
        ? prev.filter((s) => s.key !== key)
        : [...prev, { key, dir: 'asc' }]
    )

  // Flip asc ↔ desc for an already-active sort key
  const toggleSortDir = (key) =>
    setSortBy((prev) =>
      prev.map((s) => s.key === key ? { ...s, dir: s.dir === 'asc' ? 'desc' : 'asc' } : s)
    )

  // ── Suggested slot state — cleared once TaskForm consumes it ─────────────
  const [suggestedSlot, setSuggestedSlot] = useState(null)

  // ── Data hooks ───────────────────────────────────────────────────────────
  const { pets, addPet, deletePet, refetch: refetchPets } = usePets()
  const { tasks, addTask, deleteTask, completeTask, refetch: refetchTasks } = useTasks({
    filterPet, filterStatus, sortBy,
  })

  // ── Delete-owner confirmation ────────────────────────────────────────────
  const handleDeleteOwner = () => {
    if (window.confirm('Delete all data? This cannot be undone.')) {
      onDeleteOwner()
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* ── Owner header ── */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Welcome, <span className="font-medium text-foreground">{owner.name}</span>
        </p>
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground hover:text-destructive gap-1.5"
          onClick={handleDeleteOwner}
        >
          <Trash2 className="h-3.5 w-3.5" />
          Delete all data
        </Button>
      </div>

      <Separator />

      {/* ── AI panels ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className="flex flex-col gap-4 rounded-lg border p-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <span>Setup Planner</span>
            <span className="text-xs font-normal text-muted-foreground">(powered by Gemini)</span>
          </h2>
          <SetupAgent onConfirmed={() => { refetchPets(); refetchTasks(); }} />
        </section>

        <section className="flex flex-col gap-4 rounded-lg border p-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <span>Care Advisor</span>
            <span className="text-xs font-normal text-muted-foreground">(powered by Gemini)</span>
          </h2>
          <AskPanel />
        </section>
      </div>

      <Separator />

      {/* ── Two-column layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-8 items-start">

        {/* ── Left: Pet management ── */}
        <section className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold">Pets</h2>
          <AddPetForm onAdd={addPet} />
          <PetList pets={pets} onDelete={deletePet} />
        </section>

        <Separator className="lg:hidden" />

        {/* ── Right: Task management ── */}
        <section className="flex flex-col gap-6">
          <h2 className="text-lg font-semibold">Tasks</h2>

          <SuggestSlotButton
            pets={pets}
            onSlotSuggested={(date, time) => setSuggestedSlot({ date, time_start: time })}
          />

          <TaskForm
            pets={pets}
            suggestedSlot={suggestedSlot}
            onSuggestedSlotUsed={() => setSuggestedSlot(null)}
            onAdd={addTask}
          />

          <Separator />

          <TaskFilters
            pets={pets}
            filterPet={filterPet}
            filterStatus={filterStatus}
            sortBy={sortBy}
            onFilterPetChange={setFilterPet}
            onFilterStatusChange={setFilterStatus}
            onSortToggle={toggleSort}
            onSortDirToggle={toggleSortDir}
          />

          <TaskList
            tasks={tasks}
            pets={pets}
            onComplete={completeTask}
            onDelete={deleteTask}
          />
        </section>
      </div>
    </div>
  )
}
