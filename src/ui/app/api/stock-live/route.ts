import { NextRequest, NextResponse } from 'next/server';

interface YahooQuoteResult {
  regularMarketPrice?: number;
  regularMarketPreviousClose?: number;
  regularMarketDayHigh?: number;
  regularMarketDayLow?: number;
  regularMarketVolume?: number;
  marketCap?: number;
  postMarketPrice?: number;
  preMarketPrice?: number;
}

function getSession(): string {
  const now = new Date();
  const et = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }));
  const hour = et.getHours();
  const minute = et.getMinutes();
  const weekday = et.getDay(); // 0=Sun, 6=Sat

  if (weekday === 0 || weekday === 6) return 'closed';
  if (hour < 4) return 'closed';
  if (hour < 9 || (hour === 9 && minute < 30)) return 'premarket';
  if (hour < 16) return 'regular';
  if (hour < 20) return 'postmarket';
  return 'closed';
}

async function fetchYahooQuote(symbol: string): Promise<YahooQuoteResult | null> {
  const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(symbol)}&fields=regularMarketPrice,regularMarketPreviousClose,regularMarketDayHigh,regularMarketDayLow,regularMarketVolume,marketCap,postMarketPrice,preMarketPrice`;
  const res = await fetch(url, {
    headers: { 'User-Agent': 'Mozilla/5.0' },
    signal: AbortSignal.timeout(10000),
  });
  if (!res.ok) return null;
  const data = await res.json();
  const result = data?.quoteResponse?.result?.[0];
  return result || null;
}

export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get('symbol');
  if (!symbol) {
    return NextResponse.json({ error: 'Missing symbol' }, { status: 400 });
  }

  if (!/^[A-Z]+:[A-Z0-9.]+$/i.test(symbol)) {
    return NextResponse.json({ error: 'Invalid symbol format' }, { status: 400 });
  }

  const yfSymbol = symbol.includes(':') ? symbol.split(':')[1] : symbol;

  try {
    const quote = await fetchYahooQuote(yfSymbol);
    if (!quote) {
      return NextResponse.json({ error: 'No data from Yahoo Finance' }, { status: 502 });
    }

    const session = getSession();
    const prevClose = quote.regularMarketPreviousClose ?? null;
    let lastPrice: number | null = null;

    if (session === 'postmarket' && quote.postMarketPrice) {
      lastPrice = quote.postMarketPrice;
    } else if (session === 'premarket' && quote.preMarketPrice) {
      lastPrice = quote.preMarketPrice;
    }

    // Fall back to regular market price
    if (lastPrice == null) {
      lastPrice = quote.regularMarketPrice ?? null;
    }

    let changePct: number | null = null;
    let changeAbs: number | null = null;
    if (lastPrice != null && prevClose != null && prevClose > 0) {
      changeAbs = lastPrice - prevClose;
      changePct = (changeAbs / prevClose) * 100;
    }

    return NextResponse.json({
      session,
      price: lastPrice,
      change_pct: changePct,
      change_abs: changeAbs,
      high: quote.regularMarketDayHigh ?? null,
      low: quote.regularMarketDayLow ?? null,
      volume: quote.regularMarketVolume ?? null,
      market_cap: quote.marketCap ?? null,
      regular_close: prevClose,
      regular_change_pct: null,
    });
  } catch (error) {
    console.error('Failed to fetch live stock data:', error);
    return NextResponse.json({ error: 'Failed to fetch' }, { status: 500 });
  }
}
