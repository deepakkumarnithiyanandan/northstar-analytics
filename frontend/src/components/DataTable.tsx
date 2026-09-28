import type { SaleRecord } from '../types'

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

export function DataTable({ rows, total, offset, onPage }: { rows: SaleRecord[]; total: number; offset: number; onPage: (offset: number) => void }) {
  return (
    <section className="table-card">
      <div className="table-scroll"><table><thead><tr><th>Order</th><th>Date</th><th>Customer</th><th>Product</th><th>Category</th><th>Region</th><th>Qty</th><th>Revenue</th></tr></thead><tbody>
        {rows.map((row) => <tr key={row.id}><td className="mono">{row.order_id}</td><td>{row.order_date}</td><td>{row.customer_id}</td><td className="table-product">{row.product}</td><td>{row.category}</td><td><span className="region-cell">{row.region}</span></td><td>{row.quantity}</td><td className="revenue-cell">{currency.format(row.revenue)}</td></tr>)}
        {!rows.length && <tr><td colSpan={8} className="empty-row">No sales rows match the current filters.</td></tr>}
      </tbody></table></div>
      <div className="table-footer"><span>{total ? `${offset + 1}–${Math.min(offset + rows.length, total)} of ${total.toLocaleString()} rows` : 'No rows'}</span><div><button disabled={offset === 0} onClick={() => onPage(Math.max(0, offset - 50))}>Previous</button><button disabled={offset + 50 >= total} onClick={() => onPage(offset + 50)}>Next</button></div></div>
    </section>
  )
}