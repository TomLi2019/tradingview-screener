import { NextResponse } from 'next/server';
import { getAlertsCollection } from '@/lib/mongodb';

export async function GET() {
  try {
    const collection = await getAlertsCollection();
    const alerts = await collection.find({}).sort({ created_at: -1 }).limit(200).toArray();

    const serialized = alerts.map((a) => ({
      ...a,
      _id: a._id.toString(),
    }));

    return NextResponse.json(serialized);
  } catch (error) {
    console.error('Failed to fetch alerts:', error);
    return NextResponse.json({ error: 'Failed to fetch alerts' }, { status: 500 });
  }
}
