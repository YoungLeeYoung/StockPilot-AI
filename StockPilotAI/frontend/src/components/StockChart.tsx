import { useEffect, useRef } from 'react'
import {
  CandlestickSeries,
  ColorType,
  HistogramSeries,
  LineSeries,
  createChart,
  type Time,
} from 'lightweight-charts'

import type { IndicatorPoint } from '../utils/technicalIndicators'

interface StockChartProps {
  data: IndicatorPoint[]
}

export function StockChart({ data }: StockChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return undefined

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { type: ColorType.Solid, color: '#101412' },
        textColor: '#8f9a94',
        fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
      },
      grid: {
        vertLines: { color: '#202622' },
        horzLines: { color: '#202622' },
      },
      rightPriceScale: { borderColor: '#303733' },
      timeScale: {
        borderColor: '#303733',
        timeVisible: false,
        rightOffset: 4,
      },
      crosshair: {
        vertLine: { color: '#667069', labelBackgroundColor: '#313a35' },
        horzLine: { color: '#667069', labelBackgroundColor: '#313a35' },
      },
      localization: { priceFormatter: (price: number) => price.toFixed(2) },
    })

    const candles = chart.addSeries(CandlestickSeries, {
      upColor: '#27a86f',
      downColor: '#e05a5a',
      borderVisible: false,
      wickUpColor: '#27a86f',
      wickDownColor: '#e05a5a',
      priceLineVisible: true,
      lastValueVisible: true,
    })
    candles.setData(
      data.map((item) => ({
        time: item.date as Time,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      })),
    )

    const volume = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
      lastValueVisible: false,
      priceLineVisible: false,
    })
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    })
    volume.setData(
      data.map((item) => ({
        time: item.date as Time,
        value: item.volume,
        color: item.close >= item.open ? '#245f45' : '#713b3b',
      })),
    )

    const ma20 = chart.addSeries(LineSeries, {
      color: '#56b6c2',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    })
    ma20.setData(
      data
        .filter((item) => item.ma20 !== null)
        .map((item) => ({ time: item.date as Time, value: item.ma20! })),
    )

    const ma50 = chart.addSeries(LineSeries, {
      color: '#d7a94f',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    })
    ma50.setData(
      data
        .filter((item) => item.ma50 !== null)
        .map((item) => ({ time: item.date as Time, value: item.ma50! })),
    )

    chart.timeScale().fitContent()
    const resizeObserver = new ResizeObserver(([entry]) => {
      chart.applyOptions({ width: entry.contentRect.width })
    })
    resizeObserver.observe(containerRef.current)

    return () => {
      resizeObserver.disconnect()
      chart.remove()
    }
  }, [data])

  return <div className="chart-canvas" ref={containerRef} aria-label="Stock candlestick chart" />
}

