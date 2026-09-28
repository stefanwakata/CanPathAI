import { useEffect, useRef } from "react";
import type { Visualization } from "../types";

/** Renders a Plotly figure spec produced by the agent's visualization tool.
 *  plotly.js is imported dynamically to keep the initial bundle light. */
export default function PlotlyChart({ viz }: { viz: Visualization }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    let node: HTMLDivElement | null = null;
    import("plotly.js-dist-min").then((mod) => {
      const Plotly = (mod as { default?: unknown }).default ?? mod;
      if (cancelled || !ref.current) return;
      node = ref.current;
      (Plotly as {
        newPlot: (el: HTMLElement, data: unknown, layout: unknown, config: unknown) => void;
      }).newPlot(node, viz.figure.data, viz.figure.layout, {
        responsive: true,
        displaylogo: false,
        modeBarButtonsToRemove: ["lasso2d", "select2d"],
      });
    });
    return () => {
      cancelled = true;
      if (node) {
        import("plotly.js-dist-min").then((mod) => {
          const Plotly = (mod as { default?: unknown }).default ?? mod;
          (Plotly as { purge: (el: HTMLElement) => void }).purge(node as HTMLElement);
        });
      }
    };
  }, [viz]);

  return <div className="chart" ref={ref} aria-label={viz.title} />;
}
