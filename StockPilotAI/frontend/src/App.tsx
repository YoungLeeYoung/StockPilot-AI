import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Bot,
  ChartNoAxesCombined,
  Clock3,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
} from 'lucide-react'

import { getStock, type StockResponse } from './api/stock'
import { StockChart } from './components/StockChart'
import {
  buildTechnicalSnapshot,
  calculateIndicators,
} from './utils/technicalIndicators'

type ChartPeriod = '1M' | '6M' | '1Y'

const periodDays: Record<ChartPeriod, number> = {
  '1M': 30,
  '6M': 180,
  '1Y': 365,
}

const compactNumber = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 2,
})

function formatCurrency(value: number | null, maximumFractionDigits = 2) {
  if (value === null) return '--'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits,
  }).format(value)
}

function formatMetric(value: number | null, suffix = '') {
  if (value === null) return '--'
  return `${value.toFixed(2)}${suffix}`
}

function App() {
  const [query, setQuery] = useState('AAPL')
  const [stock, setStock] = useState<StockResponse | null>(null)
  const [period, setPeriod] = useState<ChartPeriod>('1Y')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const analyze = async (symbol: string) => {
    const normalized = symbol.trim().toUpperCase()
    if (!normalized) return

    setLoading(true)
    setError(null)
    try {
      setStock(await getStock(normalized))
      setQuery(normalized)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Unable to load market data.',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let active = true
    void getStock('AAPL')
      .then((result) => {
        if (active) setStock(result)
      })
      .catch((requestError: unknown) => {
        if (!active) return
        setError(
          requestError instanceof Error
            ? requestError.message
            : 'Unable to load market data.',
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  const indicators = useMemo(
    () => calculateIndicators(stock?.history ?? []),
    [stock],
  )
  const filteredIndicators = useMemo(() => {
    if (indicators.length === 0) return []
    const latestDate = new Date(indicators.at(-1)!.date)
    const cutoff = new Date(latestDate)
    cutoff.setDate(cutoff.getDate() - periodDays[period])
    return indicators.filter((item) => new Date(item.date) >= cutoff)
  }, [indicators, period])
  const technical = useMemo(
    () => buildTechnicalSnapshot(indicators),
    [indicators],
  )

  const periodChange = useMemo(() => {
    if (filteredIndicators.length < 2) return null
    const first = filteredIndicators[0].close
    const last = filteredIndicators.at(-1)!.close
    return { amount: last - first, percent: ((last - first) / first) * 100 }
  }, [filteredIndicators])

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void analyze(query)
  }

  const latestDate = stock?.history.at(-1)?.date
  const isPositive = (periodChange?.amount ?? 0) >= 0

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark"><ChartNoAxesCombined size={20} /></span>
          <div>
            <strong>StockPilot AI</strong>
            <span>Research terminal</span>
          </div>
        </div>
        <div className="market-status">
          <span className={`status-dot ${error ? 'unavailable' : loading ? 'loading' : ''}`} />
          {error ? 'Data source unavailable' : loading ? 'Connecting to market data' : 'Market data connected'}
        </div>
      </header>

      <main className="workspace">
        <section className="command-bar" aria-label="Stock search">
          <form className="symbol-search" onSubmit={handleSubmit}>
            <Search size={18} aria-hidden="true" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Enter symbol"
              aria-label="Stock symbol"
              maxLength={20}
              autoCapitalize="characters"
            />
            <button className="analyze-button" type="submit" disabled={loading}>
              {loading ? <RefreshCw className="spin" size={17} /> : <Sparkles size={17} />}
              {loading ? 'Analyzing' : 'Analyze'}
            </button>
          </form>
          <div className="as-of">
            <Clock3 size={15} />
            {latestDate ? `Data through ${latestDate}` : 'Awaiting market data'}
          </div>
        </section>

        {error && (
          <div className="error-banner" role="alert">
            <AlertCircle size={18} />
            <span>{error}</span>
            <button type="button" onClick={() => void analyze(query)} aria-label="Retry">
              <RefreshCw size={16} />
            </button>
          </div>
        )}

        <section className="quote-strip" aria-label="Stock overview">
          <div className="primary-quote">
            <div className="quote-symbol">
              <span className="exchange-tag">EQUITY</span>
              <h1>{stock?.symbol ?? query.toUpperCase()}</h1>
            </div>
            <div className="quote-price">
              <strong>{formatCurrency(stock?.basic_info.current_price ?? null)}</strong>
              {periodChange && (
                <span className={isPositive ? 'positive' : 'negative'}>
                  {isPositive ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                  {isPositive ? '+' : ''}{periodChange.amount.toFixed(2)} ({isPositive ? '+' : ''}
                  {periodChange.percent.toFixed(2)}%)
                </span>
              )}
            </div>
          </div>

          <Metric label="Market cap" value={stock?.basic_info.market_cap ? compactNumber.format(stock.basic_info.market_cap) : '--'} />
          <Metric label="P/E ratio" value={formatMetric(stock?.basic_info.trailing_pe ?? null)} />
          <Metric label="52W high" value={formatCurrency(stock?.basic_info.fifty_two_week_high ?? null)} />
          <Metric label="52W low" value={formatCurrency(stock?.basic_info.fifty_two_week_low ?? null)} />
        </section>

        <div className="analysis-grid">
          <section className="panel chart-panel">
            <div className="panel-header chart-header">
              <div>
                <span className="section-kicker">Price action</span>
                <h2>{stock?.symbol ?? 'Market'} / Daily market</h2>
              </div>
              <div className="period-control" aria-label="Chart period">
                {(Object.keys(periodDays) as ChartPeriod[]).map((item) => (
                  <button
                    type="button"
                    key={item}
                    className={period === item ? 'active' : ''}
                    onClick={() => setPeriod(item)}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
            <div className="chart-legend">
              <span><i className="legend-candle" /> OHLC</span>
              <span><i className="legend-ma20" /> MA20</span>
              <span><i className="legend-ma50" /> MA50</span>
              <span><i className="legend-volume" /> Volume</span>
            </div>
            {filteredIndicators.length ? (
              <StockChart data={filteredIndicators} />
            ) : (
              <ChartEmptyState loading={loading} />
            )}
          </section>

          <aside className="side-column">
            <section className="panel technical-panel">
              <div className="panel-header">
                <div>
                  <span className="section-kicker">Technical indicators</span>
                  <h2>Market structure</h2>
                </div>
                <span className={`trend-badge ${technical?.trend.toLowerCase() ?? 'neutral'}`}>
                  {technical?.trend ?? 'Pending'}
                </span>
              </div>

              <div className="indicator-grid">
                <Indicator label="MA20" value={formatCurrency(technical?.latest.ma20 ?? null)} />
                <Indicator label="MA50" value={formatCurrency(technical?.latest.ma50 ?? null)} />
                <Indicator label="RSI (14)" value={formatMetric(technical?.latest.rsi ?? null)} />
                <Indicator label="MACD" value={formatMetric(technical?.latest.macd ?? null)} />
              </div>

              <div className="signal-list">
                {(technical?.signals ?? ['Waiting for sufficient price history']).map((signal) => (
                  <div className="signal-row" key={signal}>
                    <span className="signal-dot" /> {signal}
                  </div>
                ))}
              </div>

              {technical?.risks.length ? (
                <div className="risk-box">
                  <ShieldAlert size={17} />
                  <div>
                    <strong>Risk flags</strong>
                    {technical.risks.map((risk) => <span key={risk}>{risk}</span>)}
                  </div>
                </div>
              ) : (
                <div className="risk-clear">No elevated technical risk flags</div>
              )}
            </section>

            <section className="panel ai-panel">
              <div className="panel-header">
                <div>
                  <span className="section-kicker">AI analysis</span>
                  <h2>Research brief</h2>
                </div>
                <Bot size={20} />
              </div>
              <div className="ai-empty">
                <Sparkles size={22} />
                <strong>LLM report not connected</strong>
                <p>
                  Market data and technical context are ready. The generated research brief will appear here when the AI endpoint is available.
                </p>
              </div>
            </section>
          </aside>
        </div>

        <footer>
          StockPilot AI provides research assistance, not investment advice. Market data may be delayed.
        </footer>
      </main>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function Indicator({ label, value }: { label: string; value: string }) {
  return (
    <div className="indicator">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function ChartEmptyState({ loading }: { loading: boolean }) {
  return (
    <div className="chart-empty">
      {loading ? <RefreshCw className="spin" size={24} /> : <BarChart3 size={28} />}
      <strong>{loading ? 'Loading price history' : 'No chart data'}</strong>
      <span>{loading ? 'Requesting daily OHLCV bars' : 'Analyze a symbol to begin'}</span>
    </div>
  )
}

export default App
