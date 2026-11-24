export function num(n: number | null | undefined, digits = 0): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '–'
  return n.toLocaleString(undefined, { maximumFractionDigits: digits })
}

/** kcal share of each macro (protein/carbs 4 kcal/g, fat 9 kcal/g). */
export function macroShares(p: number | null, c: number | null, f: number | null) {
  const pk = (p ?? 0) * 4
  const ck = (c ?? 0) * 4
  const fk = (f ?? 0) * 9
  const total = pk + ck + fk
  if (!total) return null
  return { protein: pk / total, carbs: ck / total, fat: fk / total }
}

export function plural(n: number, one: string, many = `${one}s`) {
  return `${num(n, 1)} ${n === 1 ? one : many}`
}
