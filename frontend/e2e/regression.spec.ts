import { test, expect, type Page, type Browser } from '@playwright/test'
import type { RequestDetail, RequestPage } from '../src/requests/types'

const apiUrl = process.env.E2E_API_URL || 'http://localhost:8000'
const password = process.env.E2E_DEMO_PASSWORD || 'RequestFlow-Demo!2026'
const roleNames = ['employee', 'manager', 'finance', 'procurement', 'admin'] as const
const expectedErrors = /Failed to load resource.*(401|403|404|409|503)/

async function login(page: Page, role: string) {
  await page.goto('/login')
  await page.getByLabel('Email address').fill(`${role}@requestflow.demo`)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Log out', exact: true })).toBeVisible()
}
async function users(browser: Browser, mobile = false) {
  const errors: string[] = []
  const pages: Record<string, Page> = {}
  for (const role of roleNames) {
    const context = await browser.newContext({ viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1000 } })
    const page = await context.newPage()
    page.on('pageerror', error => errors.push(error.message))
    page.on('console', message => { if (message.type() === 'error' && !expectedErrors.test(message.text())) errors.push(message.text()) })
    await login(page, role)
    pages[role] = page
  }
  return { pages, errors, close: async () => { for (const page of Object.values(pages)) await page.context().close() } }
}
async function nav(page: Page, label: string) {
  const link = page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: label, exact: true })
  if (!await link.isVisible()) await page.getByRole('button', { name: 'Menu', exact: true }).click()
  await link.click()
}
async function api(page: Page, path: string, method = 'GET', body?: unknown) {
  return page.evaluate(async ({ apiUrl, path, method, body }) => {
    const response = await fetch(apiUrl + path, { method, headers: { Authorization: 'Bearer ' + localStorage.getItem('requestflow.access_token'), 'Content-Type': 'application/json' }, ...(body ? { body: JSON.stringify(body) } : {}) })
    return { status: response.status, data: await response.json() }
  }, { apiUrl, path, method, body })
}
async function create(page: Page, name: string, cost: string) {
  await nav(page, 'Create Request')
  await page.getByLabel('Title', { exact: true }).fill(`[Regression 9/10] ${name} ${Date.now()}`)
  await page.getByLabel('Description', { exact: true }).fill('Synthetic browser regression request. <img src=x onerror="window.unexpectedScript=true">')
  await page.getByLabel('Business justification', { exact: true }).fill('Verify the existing approval and fulfillment workflow.')
  await page.getByLabel('Estimated cost (IDR)', { exact: true }).fill(cost)
  await expect(page.locator('#cost-help')).toContainText(cost === '10000000' ? 'Rp10.000.000' : 'Rp2.000.000')
  const response = page.waitForResponse(r => r.url().endsWith('/requests') && r.request().method() === 'POST')
  await page.getByRole('button', { name: 'Submit request', exact: true }).click()
  const received = await response
  expect(received.status()).toBe(201)
  const request: RequestDetail = await received.json()
  await expect(page.getByRole('heading', { name: request.title, exact: true })).toBeVisible()
  expect(await page.evaluate(() => 'unexpectedScript' in window)).toBe(false)
  return request
}
async function action(page: Page, button: string, confirmation: string, endpoint: string, double = false) {
  await page.getByRole('button', { name: button, exact: true }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('button', { name: 'Go back', exact: true })).toBeFocused()
  let writes = 0
  const count = (r: import('@playwright/test').Request) => { if (r.url().endsWith(endpoint) && r.method() !== 'GET') writes++ }
  page.on('request', count)
  const response = page.waitForResponse(r => r.url().endsWith(endpoint) && r.request().method() !== 'GET')
  const confirm = dialog.getByRole('button', { name: confirmation, exact: true })
  if (double) await confirm.evaluate((button: HTMLButtonElement) => { button.click(); button.click() })
  else await confirm.click()
  expect((await response).status()).toBe(200)
  await expect(dialog).not.toBeVisible()
  page.off('request', count)
  expect(writes).toBe(1)
}
async function review(page: Page, request: RequestDetail, stage: 'manager' | 'finance', reject = false) {
  await nav(page, stage === 'finance' ? 'Finance Approvals' : 'Approvals')
  await page.getByRole('link', { name: new RegExp(request.request_number) }).click()
  if (reject) {
    await page.getByRole('button', { name: 'Reject request', exact: true }).click()
    await expect(page.getByText('Please enter a rejection reason.', { exact: true })).toBeVisible()
    await expect(page.getByLabel('Decision comment', { exact: false })).toBeFocused()
    await page.getByLabel('Decision comment', { exact: false }).fill('Synthetic regression: budget not justified.')
  }
  await action(page, reject ? 'Reject request' : 'Approve request', reject ? 'Confirm rejection' : 'Confirm approval', `/${stage}-approval`, !reject)
}
async function history(page: Page, id: number, labels: string[]) {
  await page.goto(`/requests/${id}`)
  const region = page.getByRole('region', { name: 'Audit timeline', exact: true })
  await expect(region.locator('h3')).toHaveText(labels)
}
async function fulfill(page: Page, request: RequestDetail) {
  await nav(page, 'Procurement Queue')
  await page.getByRole('link', { name: new RegExp(request.request_number) }).click()
  await page.getByLabel('Operational note (optional)').fill('Synthetic regression: equipment ordered.')
  await action(page, 'Start Processing', 'Confirm processing', '/start-processing', true)
  await expect(page.getByRole('button', { name: 'Complete Request', exact: true })).toBeVisible()
  await page.reload()
  await page.getByLabel('Operational note (optional)').fill('Synthetic regression: delivered and verified.')
  await action(page, 'Complete Request', 'Confirm completion', '/complete', true)
  await expect(page.getByText('Fulfillment completed.', { exact: true })).toBeVisible()
}

test('A–E: mobile lifecycle, rejection, cancellation, confirmation and audit regression', async ({ browser }) => {
  const { pages: p, errors, close } = await users(browser, true)
  try {
    const low = await create(p.employee, 'Low-cost monitor', '2000000')
    await review(p.manager, low, 'manager')
    await fulfill(p.procurement, low)
    await history(p.employee, low.id, ['Request submitted', 'Manager approved', 'Processing started', 'Request completed'])
    await expect(p.employee.getByRole('region', { name: 'Service deadline' }).getByText('Completed On Time', { exact: true })).toBeVisible()
    const high = await create(p.employee, 'High-cost laptop', '10000000')
    await review(p.manager, high, 'manager')
    await review(p.finance, high, 'finance')
    await fulfill(p.procurement, high)
    await history(p.employee, high.id, ['Request submitted', 'Manager approved', 'Finance approval required', 'Finance approved', 'Processing started', 'Request completed'])
    await expect(p.employee.getByText('Automatic', { exact: true })).toBeVisible()
    const rejected = await create(p.employee, 'Manager rejection', '2000000')
    await review(p.manager, rejected, 'manager', true)
    await history(p.employee, rejected.id, ['Request submitted', 'Manager rejected'])
    await expect(p.employee.getByText('Synthetic regression: budget not justified.', { exact: true }).first()).toBeVisible()
    const financeRejected = await create(p.employee, 'Finance rejection', '10000000')
    await review(p.manager, financeRejected, 'manager')
    await review(p.finance, financeRejected, 'finance', true)
    await history(p.employee, financeRejected.id, ['Request submitted', 'Manager approved', 'Finance approval required', 'Finance rejected'])
    const cancelled = await create(p.employee, 'Cancellation', '2000000')
    await p.employee.getByRole('button', { name: 'Cancel request', exact: true }).click()
    await p.employee.getByRole('dialog').press('Escape')
    await expect(p.employee.getByRole('button', { name: 'Cancel request', exact: true })).toBeFocused()
    expect((await api(p.employee, `/requests/${cancelled.id}`)).data.status).toBe('PENDING_MANAGER_APPROVAL')
    await action(p.employee, 'Cancel request', 'Confirm cancellation', '/cancel')
    await history(p.employee, cancelled.id, ['Request submitted', 'Request cancelled'])
    expect((await api(p.manager, `/requests/${cancelled.id}/manager-approval`, 'POST', { decision: 'APPROVE' })).status).toBe(409)
    const queue: RequestPage = (await api(p.procurement, '/procurement/queue?limit=100')).data
    for (const request of [low, high, rejected, financeRejected, cancelled]) expect(queue.items.some(item => item.id === request.id)).toBe(false)
    for (const page of Object.values(p)) expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    expect(errors).toEqual([])
  } finally { await close() }
})

test('F–G: all pages, roles, SLA states and four responsive widths', async ({ browser }, testInfo) => {
  const { pages: p, errors, close } = await users(browser)
  try {
    const requests: RequestPage = (await api(p.admin, '/requests?limit=100')).data
    const completed = requests.items.find(item => item.status === 'COMPLETED')!
    for (const state of ['ON_TRACK', 'DUE_SOON', 'BREACHED', 'COMPLETED_ON_TIME', 'COMPLETED_LATE']) {
      const request = requests.items.find(item => item.sla_status === state)
      // Active fixtures age: exercise absent active states through a controlled response, not data rewrites.
      const candidate = request || requests.items[0]
      if (!request) {
        const detail = (await api(p.admin, `/requests/${candidate.id}`)).data
        await p.admin.route(`**/requests/${candidate.id}`, route => route.fulfill({ json: { ...detail, sla_status: state } }))
      }
      await p.admin.goto(`/requests/${candidate.id}`)
      await expect(p.admin.getByRole('region', { name: 'Service deadline' }).locator(`[aria-label="SLA: ${state === 'ON_TRACK' ? 'On Track' : state === 'DUE_SOON' ? 'Due Soon' : state === 'BREACHED' ? 'Breached' : state === 'COMPLETED_ON_TIME' ? 'Completed On Time' : 'Completed Late'}"]`)).toBeVisible()
      if (!request) await p.admin.unroute(`**/requests/${candidate.id}`)
    }
    const screens: [Page, string, string][] = [[p.employee, '/', 'overview'], [p.employee, '/requests', 'requests'], [p.employee, '/requests/new', 'create'], [p.employee, `/requests/${completed.id}`, 'detail'], [p.manager, '/approvals', 'manager'], [p.finance, '/approvals', 'finance'], [p.procurement, '/procurement', 'procurement'], [p.admin, '/', 'analytics']]
    for (const width of [1440, 1280, 768, 390]) {
      for (const [page, path, name] of screens) {
        await page.setViewportSize({ width, height: 900 })
        await page.goto(path)
        await expect(page.locator('h1')).toBeVisible()
        await expect(page.getByRole('status').filter({ hasText: /^Loading/ })).toHaveCount(0)
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${name} at ${width}`).toBe(true)
        if (name === 'detail' && width === 390) expect((await page.locator('h1').boundingBox())!.width).toBeGreaterThan(300)
        if (name === 'analytics') await expect(page.locator('svg.recharts-surface')).toHaveCount(5)
        if (width === 1440 || width === 390) await page.screenshot({ path: testInfo.outputPath(`${name}-${width}.png`), fullPage: true })
      }
    }
    for (const role of ['employee', 'manager', 'finance', 'procurement']) expect((await api(p[role], '/analytics/summary')).status).toBe(403)
    await p.employee.goto('/procurement')
    await expect(p.employee).toHaveURL(/\/$/)
    expect((await api(p.employee, '/procurement/queue')).status).toBe(403)
    await p.admin.goto(`/requests/${completed.id}`)
    await expect(p.admin.getByRole('heading', { name: completed.title, exact: true })).toBeVisible()
    await expect(p.admin.getByRole('heading', { name: 'Available actions' })).toHaveCount(0)
    expect(errors).toEqual([])
  } finally { await close() }
})

test('Form validation, keyboard focus, loading, empty and recoverable error states', async ({ page }) => {
  await login(page, 'employee')
  await page.goto('/requests/new')
  await page.getByRole('button', { name: 'Submit request', exact: true }).click()
  await expect(page.getByLabel('Title', { exact: true })).toBeFocused()
  await expect(page.getByText('Title is required.', { exact: true })).toBeVisible()
  await page.getByLabel('Title', { exact: true }).fill('Draft retained after focus')
  await page.evaluate(() => window.dispatchEvent(new Event('focus')))
  await expect(page.getByLabel('Title', { exact: true })).toHaveValue('Draft retained after focus')
  await page.route('**/requests?*', route => route.fulfill({ json: { items: [], total: 0, offset: 0, limit: 20 } }))
  await nav(page, 'My Requests')
  await expect(page.getByRole('heading', { name: "You haven't submitted any requests yet", exact: true })).toBeVisible()
  await expect(page.getByRole('main').getByRole('link', { name: 'Create request', exact: true })).toHaveCount(2)
  await page.unroute('**/requests?*')
  await page.route('**/requests?*', async route => { await new Promise(resolve => setTimeout(resolve, 700)); await route.fulfill({ status: 503, json: { detail: 'internal stack should never render' } }) })
  await page.reload()
  await expect(page.getByText('Loading requests…', { exact: true })).toBeVisible()
  await expect(page.getByRole('alert')).toContainText("We couldn't load requests.")
  await expect(page.getByText('internal stack should never render')).toHaveCount(0)
  await page.unroute('**/requests?*')
  await page.getByRole('button', { name: 'Try again', exact: true }).click()
  await expect(page.getByRole('table')).toBeVisible()
})

test('Late old-session response does not log out a newly signed-in user', async ({ page }) => {
  await login(page, 'employee')
  await page.goto('/requests/new')
  for (const [label, value] of [['Title', 'Uncommitted race test'], ['Description', 'Synthetic'], ['Business justification', 'Synthetic'], ['Estimated cost (IDR)', '0']]) await page.getByLabel(label, { exact: true }).fill(value)
  let release!: () => void
  const held = new Promise<void>(resolve => { release = resolve })
  let arrived!: () => void
  const started = new Promise<void>(resolve => { arrived = resolve })
  await page.route('**/requests', async route => {
    if (route.request().method() !== 'POST') return route.continue()
    arrived(); await held
    await route.fulfill({ status: 401, json: { detail: 'Expired old token' } })
  })
  await page.getByRole('button', { name: 'Submit request', exact: true }).click()
  await started
  await page.getByRole('button', { name: 'Log out', exact: true }).click()
  // Client-side navigation keeps the old fetch alive, reproducing the race.
  await page.getByLabel('Email address').fill('manager@requestflow.demo')
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByText('Morgan Manager', { exact: true })).toBeVisible()
  const oldResponse = page.waitForResponse(response => response.url().endsWith('/requests') && response.status() === 401)
  release(); await oldResponse
  await expect(page.getByText('Morgan Manager', { exact: true })).toBeVisible()
  expect((await api(page, '/auth/me')).data.role).toBe('MANAGER')
})

test('Session expiry and cross-tab logout clear authenticated UI', async ({ page, context }) => {
  await login(page, 'employee')
  const second = await context.newPage()
  await second.goto('/')
  await expect(second.getByRole('button', { name: 'Log out', exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Log out', exact: true }).click()
  await expect(second).toHaveURL(/\/login$/)
  await login(page, 'employee')
  await page.evaluate(() => {
    const token = localStorage.getItem('requestflow.access_token')!
    const pieces = token.split('.')
    pieces[1] = btoa(JSON.stringify({ exp: 1 }))
    localStorage.setItem('requestflow.access_token', pieces.join('.'))
  })
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Welcome back', exact: true })).toBeVisible()
  await expect.poll(() => page.evaluate(() => localStorage.getItem('requestflow.access_token'))).toBeNull()
})
