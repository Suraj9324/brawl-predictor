import {
  ChartBar,
  Database,
  Lightning,
  Target,
  TrendUp,
  Users,
} from "@phosphor-icons/react";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { useApi } from "../hooks/useApi";
import { fetchDashboardStats, fetchModelStats } from "../api/client";
import { SkeletonCard, SkeletonChart } from "./Skeleton";

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 120, damping: 20 } },
};

export default function Overview() {
  const { data: dashboard, loading: loadingDash } = useApi(fetchDashboardStats, []);
  const { data: model, loading: loadingModel } = useApi(fetchModelStats, []);

  const loading = loadingDash || loadingModel;

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <SkeletonChart />
          <SkeletonChart />
        </div>
      </div>
    );
  }

  const stats = [
    {
      label: "Tracked Players",
      value: dashboard?.total_players ?? 0,
      icon: Users,
      accent: false,
    },
    {
      label: "Battles Collected",
      value: dashboard?.total_battles ?? 0,
      icon: Database,
      accent: false,
    },
    {
      label: "Predictions Made",
      value: dashboard?.total_predictions ?? 0,
      icon: Lightning,
      accent: false,
    },
    {
      label: "Model Accuracy",
      value: dashboard?.model_accuracy
        ? `${(dashboard.model_accuracy * 100).toFixed(1)}%`
        : "N/A",
      icon: Target,
      accent: true,
    },
  ];

  // Feature importance chart data
  const featureData = model?.feature_importance
    ? Object.entries(model.feature_importance)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10)
        .map(([name, value]) => ({
          name: name.replace(/_/g, " ").replace(/latest brawler /g, ""),
          value: Math.round(value * 1000) / 10,
        }))
    : [];

  // Class distribution data
  const classData = model?.class_distribution
    ? [
        { name: "Trophy Gain", value: model.class_distribution.gain },
        { name: "Trophy Loss", value: model.class_distribution.loss },
      ]
    : [];

  return (
    <motion.div
      className="space-y-8"
      variants={stagger}
      initial="hidden"
      animate="show"
    >
      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((stat) => (
          <motion.div
            key={stat.label}
            variants={fadeUp}
            className="rounded-2xl border border-line/40 bg-surface-1 p-5"
          >
            <div className="mb-3 flex items-center gap-2">
              <stat.icon
                size={16}
                weight="fill"
                className={stat.accent ? "text-accent" : "text-text-muted"}
              />
              <span className="text-xs font-medium text-text-muted">
                {stat.label}
              </span>
            </div>
            <p
              className={`font-mono text-2xl font-bold tracking-tight ${
                stat.accent ? "text-accent" : "text-text-primary"
              }`}
            >
              {typeof stat.value === "number"
                ? stat.value.toLocaleString()
                : stat.value}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Feature importance */}
        <motion.div
          variants={fadeUp}
          className="rounded-2xl border border-line/40 bg-surface-1 p-6 lg:col-span-3"
        >
          <div className="mb-5 flex items-center gap-2">
            <ChartBar size={16} weight="fill" className="text-text-muted" />
            <h2 className="text-sm font-semibold text-text-primary">
              Feature Importance
            </h2>
          </div>
          {featureData.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart
                data={featureData}
                layout="vertical"
                margin={{ left: 8, right: 16, top: 4, bottom: 4 }}
              >
                <XAxis
                  type="number"
                  tick={{ fill: "#52525b", fontSize: 11, fontFamily: "Geist Mono" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fill: "#a1a1aa", fontSize: 11, fontFamily: "Geist Sans" }}
                  axisLine={false}
                  tickLine={false}
                  width={130}
                />
                <Tooltip
                  contentStyle={{
                    background: "#131316",
                    border: "1px solid #27272a",
                    borderRadius: "0.75rem",
                    fontSize: 12,
                    fontFamily: "Geist Mono",
                  }}
                  labelStyle={{ color: "#fafafa" }}
                  itemStyle={{ color: "#10b981" }}
                  cursor={{ fill: "rgba(16, 185, 129, 0.04)" }}
                />
                <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                  {featureData.map((_, i) => (
                    <Cell
                      key={i}
                      fill={i === 0 ? "#10b981" : "rgba(16, 185, 129, 0.35)"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart message="Train the model to see feature importance" />
          )}
        </motion.div>

        {/* Class distribution + model metrics */}
        <motion.div
          variants={fadeUp}
          className="space-y-6 lg:col-span-2"
        >
          <div className="rounded-2xl border border-line/40 bg-surface-1 p-6">
            <div className="mb-5 flex items-center gap-2">
              <TrendUp size={16} weight="fill" className="text-text-muted" />
              <h2 className="text-sm font-semibold text-text-primary">
                Class Distribution
              </h2>
            </div>
            {classData.length > 0 ? (
              <div className="space-y-4">
                {classData.map((item) => {
                  const total = classData.reduce((s, c) => s + c.value, 0);
                  const pct = total > 0 ? (item.value / total) * 100 : 0;
                  const isGain = item.name === "Trophy Gain";
                  return (
                    <div key={item.name}>
                      <div className="mb-1.5 flex items-center justify-between">
                        <span className="text-xs font-medium text-text-secondary">
                          {item.name}
                        </span>
                        <span className="font-mono text-xs text-text-muted">
                          {item.value.toLocaleString()} ({pct.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-surface-2">
                        <motion.div
                          className={`h-full rounded-full ${isGain ? "bg-accent" : "bg-danger"}`}
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ type: "spring", stiffness: 80, damping: 20, delay: 0.3 }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyChart message="No training data yet" />
            )}
          </div>

          {/* Model metrics */}
          {model?.is_trained && (
            <div className="rounded-2xl border border-line/40 bg-surface-1 p-6">
              <h2 className="mb-4 text-sm font-semibold text-text-primary">
                Model Metrics
              </h2>
              <div className="space-y-3">
                {[
                  { label: "Accuracy", value: model.accuracy },
                  { label: "F1 Score", value: model.f1 },
                  { label: "ROC-AUC", value: model.roc_auc },
                ].map((m) => (
                  <div key={m.label} className="flex items-center justify-between">
                    <span className="text-xs text-text-secondary">{m.label}</span>
                    <span className="font-mono text-sm font-semibold text-text-primary">
                      {m.value != null ? (m.value * 100).toFixed(1) + "%" : "N/A"}
                    </span>
                  </div>
                ))}
                <div className="flex items-center justify-between border-t border-line/40 pt-3">
                  <span className="text-xs text-text-secondary">Training Samples</span>
                  <span className="font-mono text-sm text-text-muted">
                    {model.samples?.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </div>

      {/* Last sync info */}
      {dashboard?.last_sync && (
        <motion.p
          variants={fadeUp}
          className="text-center font-mono text-xs text-text-muted"
        >
          Last sync: {new Date(dashboard.last_sync).toLocaleString()}
        </motion.p>
      )}
    </motion.div>
  );
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="flex h-40 items-center justify-center">
      <p className="text-sm text-text-muted">{message}</p>
    </div>
  );
}
