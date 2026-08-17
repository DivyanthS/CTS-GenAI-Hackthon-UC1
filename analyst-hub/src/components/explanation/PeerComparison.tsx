import { cn } from "@/lib/utils";

export interface PeerMetric {
  metric: string;
  provider: number;
  peer: number;
  format: (value: number) => string;
}

export function PeerComparison({ metrics }: { metrics: PeerMetric[] }) {
  return (
    <div className="panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-secondary/60 text-xs uppercase tracking-wider text-muted-foreground">
              <th scope="col" className="px-4 py-3 text-left font-semibold">Metric</th>
              <th scope="col" className="px-4 py-3 text-right font-semibold">Provider</th>
              <th scope="col" className="px-4 py-3 text-right font-semibold">Peer average</th>
              <th scope="col" className="px-4 py-3 text-right font-semibold">Difference</th>
              <th scope="col" className="px-4 py-3 text-left font-semibold">Comparison</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((m) => {
              const diff = Math.round(((m.provider - m.peer) / m.peer) * 100);
              const max = Math.max(m.provider, m.peer);
              return (
                <tr key={m.metric} className="border-b border-border/70 last:border-0">
                  <td className="px-4 py-3 font-medium text-foreground">{m.metric}</td>
                  <td className="px-4 py-3 text-right font-semibold tabular">{m.format(m.provider)}</td>
                  <td className="px-4 py-3 text-right text-muted-foreground tabular">{m.format(m.peer)}</td>
                  <td
                    className={cn(
                      "px-4 py-3 text-right font-semibold tabular",
                      diff > 0 ? "text-risk-critical" : "text-success",
                    )}
                  >
                    {diff > 0 ? "+" : ""}
                    {diff}%
                  </td>
                  <td className="w-64 px-4 py-3">
                    <div className="space-y-1.5">
                      <div className="h-2 rounded-full bg-secondary">
                        <div
                          className="h-2 rounded-full bg-risk-critical"
                          style={{ width: `${(m.provider / max) * 100}%` }}
                          aria-hidden
                        />
                      </div>
                      <div className="h-2 rounded-full bg-secondary">
                        <div
                          className="h-2 rounded-full bg-info"
                          style={{ width: `${(m.peer / max) * 100}%` }}
                          aria-hidden
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="border-t border-border px-4 py-3 text-xs text-muted-foreground">
        <span className="mr-3 inline-flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-risk-critical" /> Provider
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-info" /> Peer average
        </span>
      </p>
    </div>
  );
}
