import { NextResponse } from 'next/server';
import clientPromise from '@/lib/mongodb';

export async function GET() {
  try {
    const client = await clientPromise;
    const db = client.db(process.env.MONGODB_DATABASE || 'next-amazona');
    const docs = await db.collection('bot_prices').find({}).toArray();

    const prices: Record<string, number> = {};
    for (const doc of docs) {
      prices[doc.ticker] = doc.price;
    }

    return NextResponse.json(prices);
  } catch (error) {
    console.error('Failed to fetch prices:', error);
    return NextResponse.json({}, { status: 500 });
  }
}
