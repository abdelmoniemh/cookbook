// Renders the PNG app icons from the SVGs in public/. Needs Playwright (global install is fine:
// NODE_PATH=$(npm root -g) node scripts/icons.cjs). Run after changing an icon.
const { readFileSync } = require('node:fs')
const path = require('node:path')
const { chromium } = require('playwright')

const pub = path.join(__dirname, '..', 'public')
const out = [
  ['icon.svg', 'icon-192.png', 192],
  ['icon.svg', 'icon-512.png', 512],
  ['icon-maskable.svg', 'icon-maskable-512.png', 512],
  ['icon-maskable.svg', 'apple-touch-icon.png', 180],
]
;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage()
  for (const [src, dest, size] of out) {
    const svg = readFileSync(path.join(pub, src), 'utf8')
    await page.setViewportSize({ width: size, height: size })
    await page.setContent(`<style>html,body{margin:0}svg{width:${size}px;height:${size}px;display:block}</style>${svg}`)
    await page.screenshot({ path: path.join(pub, dest), omitBackground: true })
  }
  await browser.close()
})()
