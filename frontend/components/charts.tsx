"use client";

// Themed recharts building blocks for the control-room dashboard.
// Colors come from our CSS variables so charts follow light/dark automatically.

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ThroughputPoint } from "@/lib/api";

type Tip = { active?: boolean; payload?: Array<{ name?: string; value?: number; color?: string; payload?: Record<string, unknown> }>; label?: string };

function ChartTooltip({ active, payload, label }: Tip) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-lg border px-3 py-2 text-xs shadow-xl"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      {label && <div className="mb-1 font-medium text-fg">{label}</div>}
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2 tabular-nums">
          <span className="h-2 w-2 rounded-full" style={{ background: p.color }} />
          <span className="text-muted capitalize">{p.name}</span>
          <span className="ml-auto font-medium text-fg">{p.value}</span>
        </div>
      ))}
    </div>
  );
}

/* ---- Throughput: 14-day stacked area (Gmail + Slack) ---- */
export function ThroughputChart({ data }: { data: ThroughputPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="gGmail" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.5} />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gSlack" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--green)" stopOpacity={0.45} />
            <stop offset="100%" stopColor="var(--green)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="label"
          tick={{ fill: "var(--muted)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
          minTickGap={28}
        />
        <YAxis tick={{ fill: "var(--muted)", fontSize: 11 }} axisLine={false} tickLine={false} width={28} allowDecimals={false} />
        <Tooltip content={<ChartTooltip />} />
        <Area isAnimationActive={false} type="monotone" dataKey="gmail" name="Gmail" stackId="1" stroke="var(--accent)" strokeWidth={2} fill="url(#gGmail)" />
        <Area isAnimationActive={false} type="monotone" dataKey="slack" name="Slack" stackId="1" stroke="var(--green)" strokeWidth={2} fill="url(#gSlack)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

/* ---- Donut with total in the center hole ---- */
export function Donut({
  data,
  centerValue,
  centerLabel,
}: {
  data: { name: string; value: number; color: string }[];
  centerValue: number | string;
  centerLabel?: string;
}) {
  const empty = data.every((d) => d.value === 0);
  return (
    <div className="relative" style={{ height: 180 }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Tooltip content={<ChartTooltip />} />
          <Pie
            isAnimationActive={false}
            data={empty ? [{ name: "none", value: 1, color: "var(--border)" }] : data}
            dataKey="value"
            nameKey="name"
            innerRadius={58}
            outerRadius={82}
            paddingAngle={empty ? 0 : 2}
            stroke="none"
            startAngle={90}
            endAngle={-270}
          >
            {(empty ? [{ color: "var(--border)" }] : data).map((d, i) => (
              <Cell key={i} fill={d.color} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-semibold tabular-nums">{centerValue}</span>
        {centerLabel && <span className="text-[10px] uppercase tracking-widest text-muted">{centerLabel}</span>}
      </div>
    </div>
  );
}

/* ---- Horizontal priority bars ---- */
export function PriorityBars({ data }: { data: { name: string; value: number; color: string }[] }) {
  return (
    <ResponsiveContainer width="100%" height={160}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }} barSize={18}>
        <XAxis type="number" hide allowDecimals={false} />
        <YAxis type="category" dataKey="name" tick={{ fill: "var(--muted)", fontSize: 12 }} axisLine={false} tickLine={false} width={64} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "var(--surface-2)" }} />
        <Bar isAnimationActive={false} dataKey="value" name="Items" radius={[4, 4, 4, 4]}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/* ---- Radial gauge (0-100) for approval rate ---- */
export function Gauge({ value, color = "var(--accent)" }: { value: number; color?: string }) {
  return (
    <div className="relative" style={{ height: 120 }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart
          innerRadius="72%"
          outerRadius="100%"
          data={[{ value }]}
          startAngle={90}
          endAngle={-270}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
          <RadialBar isAnimationActive={false} background={{ fill: "var(--surface-2)" }} dataKey="value" cornerRadius={10} fill={color} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-semibold tabular-nums">{value}%</span>
      </div>
    </div>
  );
}

/* ---- Tiny sparkline bars for KPI tiles ---- */
export function MiniBars({ data, color }: { data: number[]; color: string }) {
  const chartData = data.map((v, i) => ({ i, v }));
  return (
    <ResponsiveContainer width="100%" height={36}>
      <BarChart data={chartData} margin={{ top: 2, right: 0, left: 0, bottom: 0 }} barCategoryGap={2}>
        <Bar isAnimationActive={false} dataKey="v" radius={[2, 2, 0, 0]} fill={color} />
      </BarChart>
    </ResponsiveContainer>
  );
}
