import type { StockHistoryItem } from '../api/stock'

export interface IndicatorPoint extends StockHistoryItem {
  ma20: number | null
  ma50: number | null
  rsi: number | null
  macd: number
  macdSignal: number
  bollingerUpper: number | null
  bollingerLower: number | null
}

export interface TechnicalSnapshot {
  trend: 'Bullish' | 'Bearish' | 'Neutral'
  signals: string[]
  risks: string[]
  latest: IndicatorPoint
}

function simpleMovingAverage(
  values: number[],
  index: number,
  period: number,
): number | null {
  if (index + 1 < period) return null
  const window = values.slice(index + 1 - period, index + 1)
  return window.reduce((sum, value) => sum + value, 0) / period
}

function standardDeviation(
  values: number[],
  index: number,
  period: number,
): number | null {
  const average = simpleMovingAverage(values, index, period)
  if (average === null) return null
  const window = values.slice(index + 1 - period, index + 1)
  const variance =
    window.reduce((sum, value) => sum + (value - average) ** 2, 0) / period
  return Math.sqrt(variance)
}

function exponentialMovingAverage(values: number[], period: number): number[] {
  if (values.length === 0) return []
  const multiplier = 2 / (period + 1)
  const result = [values[0]]
  for (let index = 1; index < values.length; index += 1) {
    result.push(values[index] * multiplier + result[index - 1] * (1 - multiplier))
  }
  return result
}

function relativeStrengthIndex(values: number[], period = 14): (number | null)[] {
  const result: (number | null)[] = new Array(values.length).fill(null)
  if (values.length <= period) return result

  let averageGain = 0
  let averageLoss = 0
  for (let index = 1; index <= period; index += 1) {
    const change = values[index] - values[index - 1]
    averageGain += Math.max(change, 0)
    averageLoss += Math.max(-change, 0)
  }
  averageGain /= period
  averageLoss /= period

  const toRsi = (gain: number, loss: number) => {
    if (loss === 0) return gain === 0 ? 50 : 100
    return 100 - 100 / (1 + gain / loss)
  }
  result[period] = toRsi(averageGain, averageLoss)

  for (let index = period + 1; index < values.length; index += 1) {
    const change = values[index] - values[index - 1]
    averageGain =
      (averageGain * (period - 1) + Math.max(change, 0)) / period
    averageLoss =
      (averageLoss * (period - 1) + Math.max(-change, 0)) / period
    result[index] = toRsi(averageGain, averageLoss)
  }

  return result
}

export function calculateIndicators(history: StockHistoryItem[]): IndicatorPoint[] {
  const sortedHistory = [...history].sort((left, right) =>
    left.date.localeCompare(right.date),
  )
  const closes = sortedHistory.map((item) => item.close)
  const ema12 = exponentialMovingAverage(closes, 12)
  const ema26 = exponentialMovingAverage(closes, 26)
  const macd = closes.map((_, index) => ema12[index] - ema26[index])
  const macdSignal = exponentialMovingAverage(macd, 9)
  const rsi = relativeStrengthIndex(closes)

  return sortedHistory.map((item, index) => {
    const ma20 = simpleMovingAverage(closes, index, 20)
    const deviation = standardDeviation(closes, index, 20)
    return {
      ...item,
      ma20,
      ma50: simpleMovingAverage(closes, index, 50),
      rsi: rsi[index],
      macd: macd[index],
      macdSignal: macdSignal[index],
      bollingerUpper:
        ma20 !== null && deviation !== null ? ma20 + deviation * 2 : null,
      bollingerLower:
        ma20 !== null && deviation !== null ? ma20 - deviation * 2 : null,
    }
  })
}

export function buildTechnicalSnapshot(
  indicators: IndicatorPoint[],
): TechnicalSnapshot | null {
  const latest = indicators.at(-1)
  if (!latest || latest.ma20 === null || latest.ma50 === null) return null

  const signals = [
    `Price ${latest.close >= latest.ma20 ? 'above' : 'below'} MA20`,
    `MA20 ${latest.ma20 >= latest.ma50 ? 'above' : 'below'} MA50`,
    `MACD ${latest.macd >= latest.macdSignal ? 'above' : 'below'} signal`,
  ]
  const risks: string[] = []
  if (latest.rsi !== null && latest.rsi >= 70) risks.push('RSI overbought')
  if (latest.rsi !== null && latest.rsi <= 30) risks.push('RSI oversold')
  if (
    latest.bollingerUpper !== null &&
    latest.close > latest.bollingerUpper
  ) {
    risks.push('Price above upper Bollinger Band')
  }
  if (
    latest.bollingerLower !== null &&
    latest.close < latest.bollingerLower
  ) {
    risks.push('Price below lower Bollinger Band')
  }

  const score =
    Math.sign(latest.close - latest.ma20) +
    Math.sign(latest.ma20 - latest.ma50) +
    Math.sign(latest.macd - latest.macdSignal)
  const trend = score >= 2 ? 'Bullish' : score <= -2 ? 'Bearish' : 'Neutral'

  return { trend, signals, risks, latest }
}

