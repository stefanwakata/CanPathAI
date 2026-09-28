import type { ChatMessage, Lang } from "../types";
import { t } from "../i18n";
import { Markdown } from "../lib/markdown";
import PlotlyChart from "./PlotlyChart";

export default function MessageBubble({ msg, lang }: { msg: ChatMessage; lang: Lang }) {
  const s = t(lang);
  const isUser = msg.role === "user";
  return (
    <div className={`bubble-row ${isUser ? "user" : "assistant"}`}>
      {!isUser && <div className="avatar" aria-hidden>🍁</div>}
      <div className={`bubble ${isUser ? "bubble-user" : "bubble-ai"} ${msg.error ? "bubble-error" : ""}`}>
        {isUser ? <p>{msg.content}</p> : <Markdown text={msg.content} />}
        {msg.visualizations?.map((viz, i) => (
          <PlotlyChart key={i} viz={viz} />
        ))}
        {!isUser && msg.citations && msg.citations.length > 0 && (
          <div className="citations">
            <span className="citations-title">{s.sources}</span>
            <div className="chips">
              {msg.citations.map((c, i) =>
                c.url ? (
                  <a key={i} className="chip" href={c.url} target="_blank" rel="noreferrer noopener">
                    {c.label}
                  </a>
                ) : (
                  <span key={i} className="chip chip-plain">{c.label}</span>
                ),
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
