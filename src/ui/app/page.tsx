'use client';

import { useEffect, useState, useMemo, useCallback } from 'react';
import Link from 'next/link';
import type { Trade } from '@/lib/types';

interface Balance {
  startingCapital: number;
  totalPnl: number;
  balance: number;
  openPositions: number;
}

type SortDir = 'asc' | 'desc';
interface SortState {
  key: string;
  dir: SortDir;
}

function useSort(defaultKey: string, defaultDir: SortDir = 'asc') {
  const [sort, setSort] = useState<SortState>({ key: defaultKey, dir: defaultDir });
  const toggle = useCallback(
    (key: string) => {
      setSort((prev) =>
        prev.key === key ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' }
      );
    },
    []
  );
  return { sort, toggle };
}

function SortHeader({
  label,
  sortKey,
  current,
  onSort,
}: {
  label: string;
  sortKey: string;
  current: SortState;
  onSort: (key: string) => void;
}) {
  const active = current.key === sortKey;
  return (
    <th
      className="py-2 pr-4 cursor-pointer select-none hover:text-gray-200 transition-colors"
      onClick={() => onSort(sortKey)}
    >
      {label}
      {active ? (current.dir === 'asc' ? ' ▲' : ' ▼') : ''}
    </th>
  );
}

export default function Dashboard() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [balance, setBalance] = useState<Balance | null>(null);
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  // Filters
  const [stockFilter, setStockFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const openSort = useSort('entry_datetime');
  const closedSort = useSort('close_datetime');

  useEffect(() => {
    async function fetchData() {
      try {
        const [tradesRes, balanceRes, pricesRes] = await Promise.all([
          fetch('/api/trades'),
          fetch('/api/balance'),
          fetch('/api/prices'),
        ]);
        const tradesData = await tradesRes.json();
        const balanceData = await balanceRes.json();
        const pricesData = await pricesRes.json();
        setTrades(Array.isArray(tradesData) ? tradesData : []);
        setBalance(balanceData);
        setPrices(pricesData || {});
        setLastUpdated(new Date().toLocaleTimeString());
      } catch (err) {
        console.error('Failed to fetch data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
    const interval = setInterval(fetchData, 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const getUnrealizedPnl = useCallback(
    (t: Trade): number | null => {
      const cur = prices[t.symbol];
      if (cur == null) return null;
      return t.type === 'buy'
        ? (cur - t.entry_price) * t.shares
        : (t.entry_price - cur) * t.shares;
    },
    [prices]
  );

  const filterTrades = useCallback(
    (list: Trade[]) => {
      return list.filter((t) => {
        if (stockFilter && !t.symbol.toLowerCase().includes(stockFilter.toLowerCase())) return false;
        const entryDate = t.entry_datetime?.slice(0, 10) ?? '';
        if (dateFrom && entryDate < dateFrom) return false;
        if (dateTo && entryDate > dateTo) return false;
        return true;
      });
    },
    [stockFilter, dateFrom, dateTo]
  );

  const openTrades = useMemo(() => {
    const list = filterTrades(trades.filter((t) => t.status === 'open'));
    const { key, dir } = openSort.sort;
    const mult = dir === 'asc' ? 1 : -1;
    return list.sort((a, b) => {
      let va: string | number;
      let vb: string | number;
      if (key === 'unrealized_pnl') {
        va = getUnrealizedPnl(a) ?? -Infinity;
        vb = getUnrealizedPnl(b) ?? -Infinity;
      } else {
        va = (a as Record<string, unknown>)[key] as string | number ?? '';
        vb = (b as Record<string, unknown>)[key] as string | number ?? '';
      }
      if (typeof va === 'string' && typeof vb === 'string') return va.localeCompare(vb) * mult;
      return ((va as number) - (vb as number)) * mult;
    });
  }, [trades, openSort.sort, getUnrealizedPnl, filterTrades]);

  const { totalUnrealizedPnl, todayBiggestWin, todayLargestLoss } = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    const allOpen = trades.filter((t) => t.status === 'open');
    let total = 0;
    let hasAny = false;
    for (const t of allOpen) {
      const pnl = getUnrealizedPnl(t);
      if (pnl != null) { total += pnl; hasAny = true; }
    }

    // Today's closed trades
    const todayClosed = trades.filter(
      (t) => t.status === 'closed' && t.pnl != null && t.close_datetime?.slice(0, 10) === today
    );
    // Also include open positions with unrealized P&L
    const todayOpenPnls = allOpen
      .map((t) => ({ symbol: t.symbol, pnl: getUnrealizedPnl(t) }))
      .filter((x) => x.pnl != null) as { symbol: string; pnl: number }[];

    const allToday = [
      ...todayClosed.map((t) => ({ symbol: t.symbol, pnl: t.pnl! })),
      ...todayOpenPnls,
    ];

    let biggestWin: { symbol: string; pnl: number } | null = null;
    let largestLoss: { symbol: string; pnl: number } | null = null;
    for (const item of allToday) {
      if (!biggestWin || item.pnl > biggestWin.pnl) biggestWin = item;
      if (!largestLoss || item.pnl < largestLoss.pnl) largestLoss = item;
    }

    return {
      totalUnrealizedPnl: hasAny ? total : null,
      todayBiggestWin: biggestWin && biggestWin.pnl > 0 ? biggestWin : null,
      todayLargestLoss: largestLoss && largestLoss.pnl < 0 ? largestLoss : null,
    };
  }, [trades, getUnrealizedPnl]);

  const closedTrades = useMemo(() => {
    const list = filterTrades(trades.filter((t) => t.status === 'closed'));
    const { key, dir } = closedSort.sort;
    const mult = dir === 'asc' ? 1 : -1;
    return list.sort((a, b) => {
      const va = (a as Record<string, unknown>)[key] as string | number ?? '';
      const vb = (b as Record<string, unknown>)[key] as string | number ?? '';
      if (typeof va === 'string' && typeof vb === 'string') return va.localeCompare(vb) * mult;
      return ((va as number) - (vb as number)) * mult;
    });
  }, [trades, closedSort.sort, filterTrades]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-400 text-lg">Loading...</p>
      </div>
    );
  }

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Trading Dashboard</h1>
        <Link href="/alerts" className="text-blue-400 hover:underline text-sm">View Alerts &rarr;</Link>
      </div>

      {/* Balance Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-4 mb-10">
        <Card label="Account Balance" value={fmt(balance?.balance)} />
        <Card label="Starting Capital" value={fmt(balance?.startingCapital)} />
        <Card
          label="Total P&L"
          value={fmt(balance?.totalPnl)}
          color={balance && balance.totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}
        />
        <Card label="Open Positions" value={String(balance?.openPositions ?? 0)} />
        <Card
          label="Unrealized P&L"
          value={totalUnrealizedPnl != null ? fmt(totalUnrealizedPnl) : '-'}
          color={totalUnrealizedPnl != null ? (totalUnrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400') : undefined}
        />
        <Card
          label="Today Biggest Win"
          value={todayBiggestWin ? `${todayBiggestWin.symbol.split(':').pop()} ${fmt(todayBiggestWin.pnl)}` : '-'}
          color="text-green-400"
        />
        <Card
          label="Today Largest Loss"
          value={todayLargestLoss ? `${todayLargestLoss.symbol.split(':').pop()} ${fmt(todayLargestLoss.pnl)}` : '-'}
          color="text-red-400"
        />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-8 items-end">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Stock</label>
          <input
            type="text"
            placeholder="e.g. AAPL"
            value={stockFilter}
            onChange={(e) => setStockFilter(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-100 w-40 focus:outline-none focus:border-gray-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">From</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-gray-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">To</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-gray-500"
          />
        </div>
        {(stockFilter || dateFrom || dateTo) && (
          <button
            onClick={() => { setStockFilter(''); setDateFrom(''); setDateTo(''); }}
            className="text-xs text-gray-400 hover:text-gray-200 underline pb-1.5"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Open Positions */}
      <section className="mb-10">
        <h2 className="text-xl font-semibold mb-3">
          Open Positions
          {lastUpdated && (
            <span className="text-sm text-gray-500 font-normal ml-3">
              Updated: {lastUpdated}
            </span>
          )}
        </h2>
        {openTrades.length === 0 ? (
          <p className="text-gray-500">No open positions</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 text-left">
                  <SortHeader label="Symbol" sortKey="symbol" current={openSort.sort} onSort={openSort.toggle} />
                  <SortHeader label="Type" sortKey="type" current={openSort.sort} onSort={openSort.toggle} />
                  <th className="py-2 pr-4">Shares</th>
                  <th className="py-2 pr-4">Entry Price</th>
                  <th className="py-2 pr-4">Current Price</th>
                  <SortHeader label="Unrealized P&L" sortKey="unrealized_pnl" current={openSort.sort} onSort={openSort.toggle} />
                  <SortHeader label="Entry Time" sortKey="entry_datetime" current={openSort.sort} onSort={openSort.toggle} />
                </tr>
              </thead>
              <tbody>
                {openTrades.map((t) => {
                  const curPrice = prices[t.symbol];
                  const hasPrice = curPrice != null;
                  const unrealizedPnl = getUnrealizedPnl(t);
                  return (
                    <tr key={t._id} className="border-b border-gray-800 hover:bg-gray-900">
                      <td className="py-2 pr-4 font-medium">
                        <Link href={`/stock?symbol=${encodeURIComponent(t.symbol)}`} className="text-blue-400 hover:underline">
                          {t.symbol}
                        </Link>
                      </td>
                      <td className="py-2 pr-4">
                        <TypeBadge type={t.type} />
                      </td>
                      <td className="py-2 pr-4">{t.shares}</td>
                      <td className="py-2 pr-4">${t.entry_price.toFixed(2)}</td>
                      <td className="py-2 pr-4">
                        {hasPrice ? `$${curPrice.toFixed(2)}` : '-'}
                      </td>
                      <td
                        className={`py-2 pr-4 font-medium ${
                          unrealizedPnl != null && unrealizedPnl >= 0
                            ? 'text-green-400'
                            : 'text-red-400'
                        }`}
                      >
                        {unrealizedPnl != null ? `$${unrealizedPnl.toFixed(2)}` : '-'}
                      </td>
                      <td className="py-2 pr-4 text-gray-400">{t.entry_datetime}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Closed Trades */}
      <section>
        <h2 className="text-xl font-semibold mb-3">Closed Trades</h2>
        {closedTrades.length === 0 ? (
          <p className="text-gray-500">No closed trades</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 text-left">
                  <SortHeader label="Symbol" sortKey="symbol" current={closedSort.sort} onSort={closedSort.toggle} />
                  <SortHeader label="Type" sortKey="type" current={closedSort.sort} onSort={closedSort.toggle} />
                  <th className="py-2 pr-4">Shares</th>
                  <th className="py-2 pr-4">Entry Price</th>
                  <th className="py-2 pr-4">Close Price</th>
                  <th className="py-2 pr-4">Close Type</th>
                  <SortHeader label="P&L" sortKey="pnl" current={closedSort.sort} onSort={closedSort.toggle} />
                  <SortHeader label="Entry Time" sortKey="entry_datetime" current={closedSort.sort} onSort={closedSort.toggle} />
                  <SortHeader label="Close Time" sortKey="close_datetime" current={closedSort.sort} onSort={closedSort.toggle} />
                </tr>
              </thead>
              <tbody>
                {closedTrades.map((t) => (
                  <tr key={t._id} className="border-b border-gray-800 hover:bg-gray-900">
                    <td className="py-2 pr-4 font-medium">
                      <Link href={`/stock?symbol=${encodeURIComponent(t.symbol)}`} className="text-blue-400 hover:underline">
                        {t.symbol}
                      </Link>
                    </td>
                    <td className="py-2 pr-4">
                      <TypeBadge type={t.type} />
                    </td>
                    <td className="py-2 pr-4">{t.shares}</td>
                    <td className="py-2 pr-4">${t.entry_price.toFixed(2)}</td>
                    <td className="py-2 pr-4">${t.close_price?.toFixed(2) ?? '-'}</td>
                    <td className="py-2 pr-4">{t.close_type ?? '-'}</td>
                    <td
                      className={`py-2 pr-4 font-medium ${
                        t.pnl != null && t.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {t.pnl != null ? `$${t.pnl.toFixed(2)}` : '-'}
                    </td>
                    <td className="py-2 pr-4 text-gray-400">{t.entry_datetime}</td>
                    <td className="py-2 pr-4 text-gray-400">{t.close_datetime ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}

function Card({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <p className="text-gray-400 text-sm mb-1">{label}</p>
      <p className={`text-xl font-bold truncate ${color || 'text-white'}`}>{value}</p>
    </div>
  );
}

function TypeBadge({ type }: { type: string }) {
  const isBuy = type === 'buy';
  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-medium ${
        isBuy ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
      }`}
    >
      {type.toUpperCase()}
    </span>
  );
}

function fmt(n: number | undefined | null): string {
  if (n == null) return '-';
  return `$${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
