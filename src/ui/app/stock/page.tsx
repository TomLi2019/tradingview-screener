'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';

interface Fundamentals {
  _id: string;
  symbol: string;
  trade_entry_datetime: string;
  trade_type: string;
  entry_price: number;
  name?: string;
  exchange?: string;
  description?: string;
  market_cap?: number;
  shares_outstanding?: number;
  float_shares?: number;
  current_price?: number;
  high_52w?: number;
  low_52w?: number;
  last_day_high?: number;
  last_day_low?: number;
  change_pct?: number;
  change_abs?: number;
  today_high?: number;
  today_low?: number;
  volume?: number;
  sector?: string;
  industry?: string;
  major_holders_summary?: { pct: string; description: string }[];
  institutional_pct?: number;
  insider_pct?: number;
  top_institutional_holders?: { holder: string; shares: number | null; pct_out: number | null }[];
  calendar_events?: Record<string, string> | string;
  recent_offerings?: { title: string; publisher: string; link: string; date: number }[];
  fetched_at: string;
}

function fmt(n: number | undefined | null): string {
  if (n == null) return '-';
  return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtLarge(n: number | undefined | null): string {
  if (n == null) return '-';
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  return `$${n.toLocaleString()}`;
}

function fmtShares(n: number | undefined | null): string {
  if (n == null) return '-';
  if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return n.toLocaleString();
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold mb-3 border-b border-gray-700 pb-1">{title}</h2>
      {children}
    </section>
  );
}

function Row({ label, value }: { label: string; value: string | React.ReactNode }) {
  return (
    <div className="flex justify-between py-1.5 border-b border-gray-800">
      <span className="text-gray-400">{label}</span>
      <span className="text-right">{value}</span>
    </div>
  );
}

export default function StockPage() {
  const searchParams = useSearchParams();
  const symbol = searchParams.get('symbol') || '';
  const [data, setData] = useState<Fundamentals | null>(null);
  const [live, setLive] = useState<{ session?: string; price?: number | null; change_pct?: number | null; change_abs?: number | null; high?: number | null; low?: number | null; volume?: number | null; market_cap?: number | null; regular_close?: number | null; regular_change_pct?: number | null } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!symbol) {
      setError('No symbol provided');
      setLoading(false);
      return;
    }
    async function fetchData() {
      try {
        const [fundRes, liveRes] = await Promise.all([
          fetch(`/api/fundamentals?symbol=${encodeURIComponent(symbol)}`),
          fetch(`/api/stock-live?symbol=${encodeURIComponent(symbol)}`),
        ]);
        if (!fundRes.ok) {
          setError('Fundamentals not found');
          return;
        }
        const json = await fundRes.json();
        setData(json);
        if (liveRes.ok) {
          const liveData = await liveRes.json();
          setLive(liveData);
        }
      } catch {
        setError('Failed to fetch data');
      } finally {
        setLoading(false);
      }
    }
    fetchData();
    const interval = setInterval(fetchData, 60 * 1000);
    return () => clearInterval(interval);
  }, [symbol]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-400 text-lg">Loading...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <main className="max-w-4xl mx-auto px-4 py-8">
        <Link href="/" className="text-blue-400 hover:underline text-sm">&larr; Back to Dashboard</Link>
        <p className="text-gray-400 mt-4">{error || 'No data available'}</p>
      </main>
    );
  }

  const displaySymbol = symbol.includes(':') ? symbol.split(':')[1] : symbol;

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <Link href="/" className="text-blue-400 hover:underline text-sm">&larr; Back to Dashboard</Link>

      <div className="mt-4 mb-6">
        <h1 className="text-3xl font-bold">
          {displaySymbol}
          {data.name && <span className="text-gray-400 text-xl ml-3">{data.name}</span>}
        </h1>
        {data.sector && data.industry && (
          <p className="text-gray-400 mt-1">{data.sector} &middot; {data.industry}</p>
        )}
        {data.exchange && (
          <p className="text-gray-500 text-sm">{data.exchange}</p>
        )}
      </div>

      {/* Price & Market Data */}
      <Section title="Market Data">
        <div className="grid grid-cols-2 gap-x-8">
          <Row
            label={live?.session === 'premarket' ? 'Pre-Market Price' : live?.session === 'postmarket' ? 'Post-Market Price' : 'Live Price'}
            value={`$${fmt(live?.price ?? data.current_price)}`}
          />
          {live?.session && live.session !== 'regular' && live.regular_close != null && (
            <Row label="Last Close" value={`$${fmt(live.regular_close)}`} />
          )}
          <Row
            label="Change %"
            value={(() => {
              const pct = live?.change_pct ?? data.change_pct;
              const abs = live?.change_abs ?? data.change_abs;
              if (pct == null) return '-';
              return (
                <span className={pct >= 0 ? 'text-green-400' : 'text-red-400'}>
                  {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
                  {abs != null && ` ($${abs >= 0 ? '+' : ''}${abs.toFixed(2)})`}
                </span>
              );
            })()}
          />
          <Row label="Market Cap" value={fmtLarge(live?.market_cap ?? data.market_cap)} />
          <Row label="Volume" value={fmtShares(live?.volume ?? data.volume)} />
          <Row label="Entry Price" value={`$${fmt(data.entry_price)}`} />
        </div>
      </Section>

      {/* Shares */}
      <Section title="Capital Structure">
        <div className="grid grid-cols-2 gap-x-8">
          <Row label="Shares Outstanding" value={fmtShares(data.shares_outstanding)} />
          <Row label="Float Shares" value={fmtShares(data.float_shares)} />
        </div>
      </Section>

      {/* Price Ranges */}
      <Section title="Price Ranges">
        <div className="grid grid-cols-2 gap-x-8">
          <Row label="52-Week High" value={`$${fmt(data.high_52w)}`} />
          <Row label="52-Week Low" value={`$${fmt(data.low_52w)}`} />
          {data.last_day_high != null && <Row label="Last Day High" value={`$${fmt(data.last_day_high)}`} />}
          {data.last_day_low != null && <Row label="Last Day Low" value={`$${fmt(data.last_day_low)}`} />}
          <Row label="Today High" value={`$${fmt(live?.high ?? data.today_high)}`} />
          <Row label="Today Low" value={`$${fmt(live?.low ?? data.today_low)}`} />
        </div>
      </Section>

      {/* Ownership */}
      {(data.institutional_pct != null || data.insider_pct != null || data.major_holders_summary) && (
        <Section title="Ownership">
          <div className="grid grid-cols-2 gap-x-8">
            {data.institutional_pct != null && (
              <Row label="Institutional Ownership" value={`${data.institutional_pct.toFixed(2)}%`} />
            )}
            {data.insider_pct != null && (
              <Row label="Insider Ownership" value={`${data.insider_pct.toFixed(2)}%`} />
            )}
          </div>
          {data.major_holders_summary && (
            <div className="mt-3">
              <p className="text-sm text-gray-400 mb-1">Major Holders Summary</p>
              {data.major_holders_summary.map((h, i) => (
                <div key={i} className="flex justify-between py-1 text-sm border-b border-gray-800">
                  <span className="text-gray-300">{h.description}</span>
                  <span>{h.pct}</span>
                </div>
              ))}
            </div>
          )}
        </Section>
      )}

      {/* Top Institutional Holders */}
      {data.top_institutional_holders && data.top_institutional_holders.length > 0 && (
        <Section title="Top Institutional Holders">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400 text-left">
                <th className="py-2 pr-4">Holder</th>
                <th className="py-2 pr-4 text-right">Shares</th>
                <th className="py-2 pr-4 text-right">% Outstanding</th>
              </tr>
            </thead>
            <tbody>
              {data.top_institutional_holders.map((h, i) => (
                <tr key={i} className="border-b border-gray-800">
                  <td className="py-1.5 pr-4">{h.holder}</td>
                  <td className="py-1.5 pr-4 text-right">{h.shares ? fmtShares(h.shares) : '-'}</td>
                  <td className="py-1.5 pr-4 text-right">{h.pct_out ? `${h.pct_out.toFixed(2)}%` : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}

      {/* Recent Offerings / PIPE */}
      {data.recent_offerings && data.recent_offerings.length > 0 && (
        <Section title="Recent PIPE / Offerings">
          {data.recent_offerings.map((o, i) => (
            <div key={i} className="py-2 border-b border-gray-800">
              <p className="font-medium">{o.title}</p>
              <p className="text-sm text-gray-400">
                {o.publisher}
                {o.date && ` - ${new Date(o.date * 1000).toLocaleDateString()}`}
              </p>
            </div>
          ))}
        </Section>
      )}

      {/* Company Description */}
      {data.description && (
        <Section title="Company Description">
          <p className="text-gray-300 text-sm leading-relaxed">{data.description}</p>
        </Section>
      )}

      {/* Trade Entry Info */}
      <Section title="Trade Entry Context">
        <div className="grid grid-cols-2 gap-x-8">
          <Row label="Trade Type" value={data.trade_type} />
          <Row label="Entry DateTime" value={data.trade_entry_datetime} />
          <Row label="Entry Price" value={`$${fmt(data.entry_price)}`} />
          <Row label="Data Fetched At" value={data.fetched_at} />
        </div>
      </Section>
    </main>
  );
}
