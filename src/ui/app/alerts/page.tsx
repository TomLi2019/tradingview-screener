'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';

interface Alert {
  _id: string;
  ticker: string;
  action: string;
  category?: string;
  price: number;
  entry_price?: number;
  shares?: number;
  trade_type?: string;
  pnl?: number;
  pnl_pct?: number;
  ema_short?: number;
  ema_long?: number;
  ema_trend?: number;
  vwap?: number | null;
  rsi?: number | null;
  message: string;
  created_at: string;
}

type SortKey = 'created_at' | 'ticker' | 'action';
type SortDir = 'asc' | 'desc';

function isProfit(a: Alert) {
  return a.category === 'unrealized_profit' || a.category === 'realized_profit';
}

function getActionLabel(a: Alert): string {
  if (a.category === 'unrealized_profit') return 'UNREALIZED PROFIT';
  if (a.category === 'realized_profit') return 'REALIZED PROFIT';
  return a.action.replaceAll('_', ' ').toUpperCase();
}

function ActionBadge({ alert }: { alert: Alert }) {
  if (alert.category === 'unrealized_profit') {
    return <span className="px-2 py-0.5 rounded text-xs font-medium bg-yellow-900 text-yellow-300">UNREALIZED PROFIT</span>;
  }
  if (alert.category === 'realized_profit') {
    return <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-900 text-emerald-300">REALIZED PROFIT</span>;
  }
  const isBuy = alert.action === 'strong_buy';
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${isBuy ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
      {alert.action.replaceAll('_', ' ').toUpperCase()}
    </span>
  );
}

function SortHeader({ label, sortKey, current, onSort }: {
  label: string;
  sortKey: SortKey;
  current: { key: SortKey; dir: SortDir };
  onSort: (key: SortKey) => void;
}) {
  const arrow = current.key === sortKey ? (current.dir === 'asc' ? ' ▲' : ' ▼') : '';
  return (
    <th
      className="py-2 pr-4 cursor-pointer select-none hover:text-gray-200"
      onClick={() => onSort(sortKey)}
    >
      {label}{arrow}
    </th>
  );
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'signal' | 'profit'>('all');
  const [sort, setSort] = useState<{ key: SortKey; dir: SortDir }>({ key: 'created_at', dir: 'desc' });
  const [symbolFilter, setSymbolFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  useEffect(() => {
    async function fetchAlerts() {
      try {
        const res = await fetch('/api/alerts');
        const data = await res.json();
        setAlerts(Array.isArray(data) ? data : []);
      } catch {
        console.error('Failed to fetch alerts');
      } finally {
        setLoading(false);
      }
    }
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const uniqueTypes = useMemo(() => {
    const types = new Set<string>();
    for (const a of alerts) types.add(a.category || a.action);
    return Array.from(types).sort();
  }, [alerts]);

  const handleSort = (key: SortKey) => {
    setSort((prev) =>
      prev.key === key ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' }
    );
  };

  const filtered = useMemo(() => {
    let list = alerts;

    // category filter
    if (filter === 'signal') list = list.filter((a) => !isProfit(a));
    if (filter === 'profit') list = list.filter((a) => isProfit(a));

    // symbol filter
    if (symbolFilter) {
      const q = symbolFilter.toUpperCase();
      list = list.filter((a) => a.ticker.toUpperCase().includes(q));
    }

    // type filter
    if (typeFilter) {
      list = list.filter((a) => (a.category || a.action) === typeFilter);
    }

    // date range
    if (dateFrom) list = list.filter((a) => a.created_at >= dateFrom);
    if (dateTo) list = list.filter((a) => a.created_at <= dateTo + 'T23:59:59');

    // sort
    const { key, dir } = sort;
    const mult = dir === 'asc' ? 1 : -1;
    list = [...list].sort((a, b) => {
      let va: string, vb: string;
      if (key === 'action') {
        va = getActionLabel(a);
        vb = getActionLabel(b);
      } else {
        va = a[key];
        vb = b[key];
      }
      return va.localeCompare(vb) * mult;
    });

    return list;
  }, [alerts, filter, symbolFilter, typeFilter, dateFrom, dateTo, sort]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-400 text-lg">Loading...</p>
      </div>
    );
  }

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <Link href="/" className="text-blue-400 hover:underline text-sm">&larr; Back to Dashboard</Link>
      <h1 className="text-3xl font-bold mt-4 mb-6">Alerts</h1>

      {/* Category tabs */}
      <div className="flex gap-2 mb-4">
        {(['all', 'signal', 'profit'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded text-sm ${filter === f ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-gray-200'}`}
          >
            {f === 'all' ? 'All' : f === 'signal' ? 'Signals' : 'Profit'}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6 items-end">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Symbol</label>
          <input
            type="text"
            placeholder="e.g. AAPL"
            value={symbolFilter}
            onChange={(e) => setSymbolFilter(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm w-28"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Type</label>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm"
          >
            <option value="">All</option>
            {uniqueTypes.map((t) => (
              <option key={t} value={t}>{t.replaceAll('_', ' ').toUpperCase()}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">From</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">To</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm"
          />
        </div>
        {(symbolFilter || typeFilter || dateFrom || dateTo) && (
          <button
            onClick={() => { setSymbolFilter(''); setTypeFilter(''); setDateFrom(''); setDateTo(''); }}
            className="text-xs text-gray-400 hover:text-white underline pb-1"
          >
            Clear filters
          </button>
        )}
      </div>

      {filtered.length === 0 ? (
        <p className="text-gray-500">No alerts yet</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400 text-left">
                <SortHeader label="Time" sortKey="created_at" current={sort} onSort={handleSort} />
                <SortHeader label="Symbol" sortKey="ticker" current={sort} onSort={handleSort} />
                <SortHeader label="Type" sortKey="action" current={sort} onSort={handleSort} />
                <th className="py-2 pr-4">Price</th>
                <th className="py-2 pr-4">Details</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => (
                <tr key={a._id} className="border-b border-gray-800 hover:bg-gray-900">
                  <td className="py-2 pr-4 text-gray-400 whitespace-nowrap">{a.created_at}</td>
                  <td className="py-2 pr-4 font-medium">
                    <Link href={`/stock?symbol=${encodeURIComponent(a.ticker)}`} className="text-blue-400 hover:underline">
                      {a.ticker}
                    </Link>
                  </td>
                  <td className="py-2 pr-4"><ActionBadge alert={a} /></td>
                  <td className="py-2 pr-4">${a.price.toFixed(2)}</td>
                  <td className="py-2 pr-4 text-gray-300">
                    {isProfit(a) ? (
                      <span>
                        {a.trade_type} {a.shares} shares | entry ${a.entry_price?.toFixed(2)} |{' '}
                        <span className="text-green-400">+{a.pnl_pct?.toFixed(1)}% (${a.pnl?.toFixed(2)})</span>
                      </span>
                    ) : (
                      <span>
                        EMA {a.ema_short?.toFixed(2)}/{a.ema_long?.toFixed(2)} | EMA200 {a.ema_trend?.toFixed(2)}
                        {a.vwap != null && ` | VWAP ${a.vwap.toFixed(2)}`}
                        {a.rsi != null && ` | RSI ${a.rsi.toFixed(1)}`}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
