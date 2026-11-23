// Take screenshots of the main screens with Playwright (headless Chromium).
// Usage (frontend/):  node scripts/shots.mjs [outDir] [width]
import { chromium } from '@playwright/test'
import { mkdirSync } from 'node:fs'

const out = process.argv[2] ?? 'screenshots'
const width = Number(process.argv[3] ?? 1440)
const base = process.env.APP_URL ?? 'http://localhost:5199'
mkdirSync(out, { recursive: true })

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width, height: 900 } })
const errors = []
page.on('pageerror', e => errors.push(String(e)))
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()) })

async function shot(name, url, action) {
  await page.goto(base + url, { waitUntil: 'networkidle' })
  if (action) await action()
  await page.waitForTimeout(500)
  await page.screenshot({ path: `${out}/${name}-${width}.png`, fullPage: true })
  console.log('saved', `${out}/${name}-${width}.png`)
}

await shot('01-queue', '/')
await shot('02-patel', '/cases/CASE-PATEL', async () => {
  const item = page.getByText('E3', { exact: true }).first()
  if (await item.count()) await item.click()
})
await shot('03-lee', '/cases/CASE-LEE')
await shot('04-awaiting-records', '/cases/CASE-BG04')

if (errors.length) console.log('PAGE ERRORS:\n' + errors.join('\n'))
await browser.close()
