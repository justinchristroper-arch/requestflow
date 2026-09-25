import { chromium } from '@playwright/test'
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const output = resolve(here, '../../docs/screenshots')
const baseURL = process.env.E2E_BASE_URL || 'http://127.0.0.1:5173'
const apiURL = process.env.E2E_API_URL || 'http://localhost:8000'
const password = process.env.E2E_DEMO_PASSWORD || 'RequestFlow-Demo!2026'

await mkdir(output, { recursive: true })
const browser = await chromium.launch(process.platform === 'win32' ? { channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge' } : {})

async function signedIn(role) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
  const page = await context.newPage()
  await page.goto(`${baseURL}/login`)
  await page.getByLabel('Email address').fill(`${role}@requestflow.demo`)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await page.getByRole('button', { name: 'Log out', exact: true }).waitFor()
  return { context, page }
}

async function capture(role, path, filename) {
  const { context, page } = await signedIn(role)
  await page.goto(`${baseURL}${path}`)
  await page.locator('h1').waitFor()
  await page.getByRole('status').filter({ hasText: /^Loading/ }).waitFor({ state: 'detached' }).catch(() => {})
  await page.screenshot({ path: resolve(output, filename), fullPage: true })
  await context.close()
}

try {
  await capture('admin', '/', 'admin-dashboard.png')
  await capture('employee', '/requests/new', 'create-request.png')
  {
    const { context, page } = await signedIn('employee')
    await page.goto(`${baseURL}/requests`)
    await page.getByRole('heading', { name: 'My requests' }).waitFor()
    const next = page.getByRole('button', { name: 'Next' })
    if (await next.isEnabled()) {
      await next.click()
      await page.getByText(/^21–/).waitFor()
    }
    await page.screenshot({ path: resolve(output, 'my-requests.png'), fullPage: true })
    await context.close()
  }
  await capture('manager', '/approvals', 'manager-approval-queue.png')
  await capture('finance', '/approvals', 'finance-approval-queue.png')
  await capture('procurement', '/procurement', 'procurement-queue.png')

  const { context, page } = await signedIn('employee')
  const token = await page.evaluate(() => localStorage.getItem('requestflow.access_token'))
  const response = await fetch(`${apiURL}/requests?own=true&limit=100`, { headers: { Authorization: `Bearer ${token}` } })
  if (!response.ok) throw new Error(`Could not select screenshot request: ${response.status}`)
  const body = await response.json()
  const request = body.items.find((item) => item.status === 'COMPLETED' && item.title.startsWith('[DEMO Analytics'))
    || body.items.find((item) => item.status === 'COMPLETED')
    || body.items[0]
  if (!request) throw new Error('No visible demo request is available for the detail screenshot')
  await page.goto(`${baseURL}/requests/${request.id}`)
  await page.getByRole('heading', { name: request.title, exact: true }).waitFor()
  await page.getByRole('region', { name: 'Audit timeline' }).getByRole('status').waitFor({ state: 'detached' }).catch(() => {})
  await page.screenshot({ path: resolve(output, 'request-detail.png'), fullPage: true })
  await page.getByRole('region', { name: 'Audit timeline' }).screenshot({ path: resolve(output, 'audit-timeline.png') })
  await context.close()
} finally {
  await browser.close()
}
