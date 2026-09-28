import { useEffect, useState } from "react";
import { fetchStats } from "../api";
import { t } from "../i18n";
import type { Lang, StatsResponse } from "../types";

const METRIC_LABELS: Record<string, { fr: string; en: string }> = {
  faithfulness: { fr: "Fidélité", en: "Faithfulness" },
  answer_relevancy: { fr: "Pertinence des réponses", en: "Answer relevancy" },
  context_precision: { fr: "Précision du contexte", en: "Context precision" },
};

export default function StatsDashboard({ lang }: { lang: Lang }) {
  const s = t(lang);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchStats().then(setStats).catch(() => setError(true));
  }, []);

  if (error) return <p className="muted">{s.errorGeneric}</p>;
  if (!stats) return <p className="muted">…</p>;

  return (
    <div className="stats">
      <h3>{s.stats}</h3>
      {stats.ragas.length === 0 ? (
        <p className="muted">{s.noEval}</p>
      ) : (
        <>
          <div className="metric-cards">
            {stats.ragas.map((m) => {
              const label = METRIC_LABELS[m.name]?.[lang] ?? m.name;
              const pct = Math.round(m.value * 100);
              return (
                <div key={m.name} className="metric-card">
                  <div className="metric-value" data-grade={pct >= 80 ? "good" : pct >= 60 ? "mid" : "low"}>
                    {pct}%
                  </div>
                  <div className="metric-label">{label}</div>
                  <div className="metric-bar">
                    <div className="metric-fill" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
          {stats.evaluated_at && (
            <p className="muted small">
              {s.evaluatedAt}: {new Date(stats.evaluated_at).toLocaleString(lang === "fr" ? "fr-CA" : "en-CA")}
              {" · "}n={stats.n_questions}
            </p>
          )}
        </>
      )}
      {stats.ingestion.length > 0 && (
        <>
          <h4>{s.ingestionTitle}</h4>
          <table className="ingestion-table">
            <tbody>
              {stats.ingestion.slice(0, 8).map((run, i) => (
                <tr key={i}>
                  <td>{run.dataset}</td>
                  <td className={`status-${run.status}`}>{run.status}</td>
                  <td>{run.rows_loaded.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
