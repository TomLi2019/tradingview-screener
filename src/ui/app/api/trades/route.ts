import { NextResponse } from 'next/server';
import { getTradesCollection } from '@/lib/mongodb';

export async function GET() {
  try {
    const collection = await getTradesCollection();
    const trades = await collection.find({}).toArray();

    // Convert ObjectId to string
    const serialized = trades.map((t) => ({
      ...t,
      _id: t._id.toString(),
    }));

    return NextResponse.json(serialized);
  } catch (error) {
    console.error('Failed to fetch trades:', error);
    return NextResponse.json({ error: 'Failed to fetch trades' }, { status: 500 });
  }
}
