export interface Trade {
  _id: string;
  entry_datetime: string;
  type: 'buy' | 'short';
  symbol: string;
  shares: number;
  entry_price: number;
  commission: number;
  close_datetime: string | null;
  close_type: 'sell' | 'cover' | null;
  close_price: number | null;
  pnl: number | null;
  close_commission: number;
  status: 'open' | 'closed';
}
