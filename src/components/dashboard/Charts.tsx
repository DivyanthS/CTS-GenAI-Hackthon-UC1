import type { ReactNode } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { RiskLevel } from "@/types";
import { riskColor } from "@/components/common/RiskBadge";

export function ChartPanel({
  title,
  description,
  children,
  actions,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <section className="panel p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          {description && <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>}
        </div>
        {actions}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

const axisProps = {
  stroke: "var(--muted-foreground)",
  fontSize: 11,
  tickLine: false,
  axisLine: false,
};

const tooltipStyle = {
  contentStyle: {
    borderRadius: 8,
    border: "1px solid var(--border)",
    fontSize: 12,
    background: "var(--card)",
    color: "var(--foreground)",
  },
};

export function RiskDistributionChart({
  data,
}: {
  data: { level: RiskLevel; count: number }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ left: -12 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
        <XAxis dataKey="level" {...axisProps} />
        <YAxis {...axisProps} tickFormatter={(v: number) => v.toLocaleString()} />
        <Tooltip {...tooltipStyle} formatter={(v: number) => v.toLocaleString()} />
        <Bar dataKey="count" radius={[6, 6, 0, 0]}>
          {data.map((d) => (
            <Cell key={d.level} fill={riskColor(d.level)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ClaimTypeChart({ data }: { data: { type: string; count: number }[] }) {
  const colors = ["var(--info)", "var(--risk-low)"];
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie data={data} dataKey="count" nameKey="type" innerRadius={62} outerRadius={92} paddingAngle={2}>
          {data.map((d, i) => (
            <Cell key={d.type} fill={colors[i % colors.length]} />
          ))}
        </Pie>
        <Tooltip {...tooltipStyle} formatter={(v: number) => v.toLocaleString()} />
        <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function ReimbursementByRiskChart({
  data,
}: {
  data: { level: RiskLevel; amount: number }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} layout="vertical" margin={{ left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border)" />
        <XAxis
          type="number"
          {...axisProps}
          tickFormatter={(v: number) => `$${(v / 1_000_000).toFixed(0)}M`}
        />
        <YAxis type="category" dataKey="level" width={70} {...axisProps} />
        <Tooltip
          {...tooltipStyle}
          formatter={(v: number) => `$${(v / 1_000_000).toFixed(1)}M`}
        />
        <Bar dataKey="amount" radius={[0, 6, 6, 0]}>
          {data.map((d) => (
            <Cell key={d.level} fill={riskColor(d.level)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
