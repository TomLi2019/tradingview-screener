import { NextRequest, NextResponse } from 'next/server';
import clientPromise from '@/lib/mongodb';

export async function GET(req: NextRequest) {
  try {
    const symbol = req.nextUrl.searchParams.get('symbol');
    const client = await clientPromise;
    const db = client.db(process.env.MONGODB_DATABASE || 'next-amazona');
    const collection = db.collection('bot_fundamentals');

    if (symbol) {
      // Get latest fundamentals for a specific symbol
      const doc = await collection
        .find({ symbol })
        .sort({ fetched_at: -1 })
        .limit(1)
        .toArray();
      if (doc.length === 0) {
        return NextResponse.json({ error: 'Not found' }, { status: 404 });
      }
      const serialized = { ...doc[0], _id: doc[0]._id.toString() };
      return NextResponse.json(serialized);
    }

    // Get latest fundamentals for all symbols (deduplicated by symbol)
    const pipeline = [
      { $sort: { fetched_at: -1 as const } },
      { $group: { _id: '$symbol', doc: { $first: '$$ROOT' } } },
      { $replaceRoot: { newRoot: '$doc' } },
      { $sort: { symbol: 1 as const } },
    ];
    const docs = await collection.aggregate(pipeline).toArray();
    const serialized = docs.map((d) => ({ ...d, _id: d._id.toString() }));
    return NextResponse.json(serialized);
  } catch (error) {
    console.error('Failed to fetch fundamentals:', error);
    return NextResponse.json({ error: 'Failed to fetch fundamentals' }, { status: 500 });
  }
}
