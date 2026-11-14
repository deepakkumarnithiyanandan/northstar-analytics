const form = document.querySelector('#goal-form')
const goalInput = document.querySelector('#goal')
const submitButton = document.querySelector('#submit')
const latest = document.querySelector('#latest')
const savedPlans = document.querySelector('#saved-plans')
let activePlanId = null

document.querySelectorAll('.examples button').forEach((button) => {
  button.addEventListener('click', () => {
    goalInput.value = button.textContent
    goalInput.focus()
  })
})

function node(tag, className, text) {
  const element = document.createElement(tag)
  if (className) element.className = className
  if (text !== undefined) element.textContent = text
  return element
}

function renderPlan(plan) {
  activePlanId = plan.id
  document.querySelector('#plan-title').textContent = plan.title
  document.querySelector('#plan-goal').textContent = `Your goal: ${plan.goal}`
  const tasks = document.querySelector('#task-list')
  tasks.replaceChildren()
  let completedCount = 0
  let minutes = 0
  plan.tasks.forEach((task, index) => {
    if (task.completed) completedCount += 1
    minutes += task.estimate_minutes
    const row = node('label', `task-row ${task.completed ? 'is-complete' : ''}`)
    const checkbox = document.createElement('input')
    checkbox.type = 'checkbox'
    checkbox.checked = Boolean(task.completed)
    checkbox.setAttribute('aria-label', `Mark ${task.title} complete`)
    checkbox.addEventListener('change', () => updateTask(task.id, checkbox.checked))
    const number = node('span', 'task-number', String(index + 1).padStart(2, '0'))
    const title = node('span', 'task-title', task.title)
    const estimate = node('span', 'task-estimate', `${task.estimate_minutes} min`)
    row.append(checkbox, number, title, estimate)
    tasks.append(row)
  })
  document.querySelector('#progress').textContent = `${completedCount} / ${plan.tasks.length} DONE`
  document.querySelector('#total-time').textContent = minutes >= 60
    ? `${Math.floor(minutes / 60)}h ${minutes % 60 ? `${minutes % 60}m` : ''}`.trim()
    : `${minutes} minutes`
  latest.hidden = false
}

function renderSaved(plans) {
  savedPlans.replaceChildren()
  if (!plans.length) {
    savedPlans.append(node('p', 'empty-note', 'Your plans will show up here.'))
    return
  }
  plans.forEach((plan) => {
    const button = node('button', 'saved-item')
    button.type = 'button'
    button.append(node('span', 'saved-item-title', plan.title))
    const done = plan.tasks.filter((task) => task.completed).length
    button.append(node('span', 'saved-item-meta', `${done}/${plan.tasks.length} steps`))
    button.addEventListener('click', () => renderPlan(plan))
    savedPlans.append(button)
  })
}

function renderTrace(items) {
  const container = document.querySelector('#trace-items')
  container.replaceChildren()
  items.forEach((item, index) => {
    const row = node('div', 'trace-row')
    row.append(node('span', 'trace-index', String(index + 1).padStart(2, '0')))
    row.append(node('strong', '', item.tool.replaceAll('_', ' ')))
    row.append(node('code', '', JSON.stringify(item.observation)))
    container.append(row)
  })
  document.querySelector('#trace-count').textContent = `${items.length} action${items.length === 1 ? '' : 's'}`
}

async function updateTask(taskId, completed) {
  try {
    const response = await fetch(`/api/tasks/${taskId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ completed }),
    })
    if (!response.ok) throw new Error('Could not update this task.')
    await loadPlans()
  } catch (error) {
    document.querySelector('#status-text').textContent = error.message
  }
}

async function loadPlans() {
  const response = await fetch('/api/plans')
  if (!response.ok) throw new Error('Could not load saved plans.')
  const plans = await response.json()
  renderSaved(plans)
  if (activePlanId !== null) {
    const active = plans.find((plan) => plan.id === activePlanId)
    if (active) renderPlan(active)
  } else if (plans.length) {
    renderPlan(plans[0])
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault()
  submitButton.disabled = true
  submitButton.querySelector('span').textContent = 'Planning…'
  try {
    const response = await fetch('/api/agent/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal: goalInput.value }),
    })
    const body = await response.json()
    if (!response.ok) throw new Error(body.detail || 'The plan could not be created.')
    renderPlan(body.plan)
    renderTrace(body.trace)
    document.querySelector('#trace-toggle').setAttribute('aria-expanded', 'false')
    document.querySelector('#trace-items').hidden = true
    document.querySelector('#status-text').textContent = body.mode === 'agent' ? 'Model agent ready' : 'Local planner ready'
    await loadPlans()
    latest.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } catch (error) {
    document.querySelector('#status-text').textContent = error.message
  } finally {
    submitButton.disabled = false
    submitButton.querySelector('span').textContent = 'Build my plan'
  }
})

document.querySelector('#trace-toggle').addEventListener('click', (event) => {
  const button = event.currentTarget
  const expanded = button.getAttribute('aria-expanded') === 'true'
  button.setAttribute('aria-expanded', String(!expanded))
  document.querySelector('#trace-items').hidden = expanded
})

async function initialize() {
  try {
    const health = await fetch('/api/health').then((response) => response.json())
    document.querySelector('#status-dot').classList.add('online')
    document.querySelector('#status-text').textContent = 'Local workspace'
    document.querySelector('#mode-note').textContent = health.model_configured
      ? 'Model-powered planning is enabled.'
      : 'Local planner is ready · Add an API key to enable model planning.'
    await loadPlans()
  } catch (error) {
    document.querySelector('#status-text').textContent = error.message
  }
}

initialize()
