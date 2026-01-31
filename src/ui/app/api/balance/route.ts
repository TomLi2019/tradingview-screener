import { NextResponse } from 'next/server';
import { getTradesCollection } from '@/lib/mongodb';

const STARTING_CAPITAL = 10000;

export async function GET() {
  try {
    const collection = await getTradesCollection();

    // Sum P&L from all closed trades
    const result = await collection
      .aggregate([
        { $match: { status: 'closed', pnl: { $ne: null } } },
        { $group: { _id: null, totalPnl: { $sum: '$pnl' } } },
      ])
      .toArray();

    const totalPnl = result.length > 0 ? result[0].totalPnl : 0;
    const balance = STARTING_CAPITAL + totalPnl;

    // Count open positions
    const openCount = await collection.countDocuments({ status: 'open' });

    return NextResponse.json({
      startingCapital: STARTING_CAPITAL,
      totalPnl,
      balance,
      openPositions: openCount,
    });
  } catch (error) {
    console.error('Failed to fetch balance:', error);
    return NextResponse.json({ error: 'Failed to fetch balance' }, { status: 500 });
  }
}
