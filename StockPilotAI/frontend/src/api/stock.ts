export interface StockBasicInfo {
  current_price: number | null
  market_cap: number | null
  trailing_pe: number | null
  fifty_two_week_high: number | null
  fifty_two_week_low: number | null
}

export interface StockHistoryItem {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface StockResponse {
  symbol: string
  basic_info: StockBasicInfo
  history: StockHistoryItem[]
}

interface ApiErrorBody {
  detail?: string | { message?: string }
}

const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export async function getStock(symbol: string): Promise<StockResponse> {
  const response = await fetch(`${apiBaseUrl}/stock/${encodeURIComponent(symbol)}`)

  if (!response.ok) {
    let message = 'Unable to load market data.'
    try {
      const body = (await response.json()) as ApiErrorBody
      if (typeof body.detail === 'string') {
        message = body.detail
      } else if (body.detail?.message) {
        message = body.detail.message
      }
    } catch {
      // Keep the safe fallback when the upstream response is not JSON.
    }
    throw new Error(message)
  }

  return (await response.json()) as StockResponse
}

