// Render each page of a .drawio file to PNG via the diagrams.net viewer (diagram data stays in the URL fragment).
// Usage: node render_drawio.mjs <file.drawio> <outPrefix>
import { chromium } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { deflateRawSync } from 'node:zlib'

const [file, prefix] = process.argv.slice(2)
const xml = readFileSync(file, 'utf8')
const pages = [...xml.matchAll(/<diagram [^>]*name="([^"]*)"[^>]*>([\s\S]*?)<\/diagram>/g)]
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1900, height: 1200 } })
for (let i = 0; i < pages.length; i++) {
  const one = `<mxfile><diagram name="p">${pages[i][2]}</diagram></mxfile>`
  const enc = Buffer.from(deflateRawSync(Buffer.from(encodeURIComponent(one)))).toString('base64')
  await page.goto(`https://viewer.diagrams.net/?lightbox=1&highlight=0000ff&nav=0#R${encodeURIComponent(enc)}`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(2500)
  await page.screenshot({ path: `${prefix}-${i + 1}.png`, fullPage: false })
  console.log('rendered', pages[i][1])
}
await browser.close()
