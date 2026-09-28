import { useEffect, useRef, useState } from "react";
import { sendChat } from "./api";
import MessageBubble from "./components/MessageBubble";
import HelpPage from "./components/HelpPage";
import ProfilePanel from "./components/ProfilePanel";
import { t } from "./i18n";
import type { ChatMessage, Lang, UserProfile } from "./types";

export default function App() {
  const [lang, setLang] = useState<Lang>("fr");
  const [showHelp, setShowHelp] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfile>({});
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const s = t(lang);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const ask = async (question: string) => {
    const text = question.trim();
    if (!text || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setBusy(true);
    try {
      const res = await sendChat(text, sessionId, lang, profile);
      setSessionId(res.session_id);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: res.answer,
          citations: res.citations,
          visualizations: res.visualizations,
        },
      ]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: s.errorGeneric, error: true }]);
    } finally {
      setBusy(false);
    }
  };

  const reset = () => {
    setMessages([]);
    setSessionId(null);
    setProfile({});
  };

  return (
    <div className="layout">
      <header className="topbar">
        <div className="brand">
          <span className="leaf" aria-hidden>🍁</span>
          <div>
            <h1>{s.title}</h1>
            <p className="tagline">{s.tagline}</p>
          </div>
        </div>
        <nav className="nav">
          <button
            className={`help-btn ${showHelp ? "active" : ""}`}
            onClick={() => setShowHelp(!showHelp)}
            aria-label={s.help}
            title={s.help}
          >
            ?
          </button>
          <div className="lang-toggle" role="group" aria-label="Language">
            <button className={lang === "fr" ? "active" : ""} onClick={() => setLang("fr")}>FR</button>
            <button className={lang === "en" ? "active" : ""} onClick={() => setLang("en")}>EN</button>
          </div>
        </nav>
      </header>

      <div className="body">
        <aside className="sidebar">
          <ProfilePanel
            lang={lang}
            sessionId={sessionId}
            profile={profile}
            onChange={setProfile}
            onSession={setSessionId}
          />
          <button className="ghost" onClick={reset}>{s.newChat}</button>
          <p className="muted small disclaimer">{s.disclaimer}</p>
        </aside>

        <main className="main">
          {showHelp ? (
            <>
              <HelpPage lang={lang} />
              <p>
                <button className="ghost" onClick={() => setShowHelp(false)}>{s.backToChat}</button>
              </p>
            </>
          ) : (
          <>
              <div className="chat-scroll">
                {messages.length === 0 && (
                  <div className="empty">
                    <p>{s.tagline}</p>
                    <div className="suggestions">
                      {s.suggestions.map((q) => (
                        <button key={q} onClick={() => void ask(q)}>{q}</button>
                      ))}
                    </div>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <MessageBubble key={i} msg={msg} lang={lang} />
                ))}
                {busy && (
                  <div className="bubble-row assistant">
                    <div className="avatar" aria-hidden>🍁</div>
                    <div className="bubble bubble-ai thinking">{s.thinking}</div>
                  </div>
                )}
                <div ref={endRef} />
              </div>
              <form
                className="composer"
                onSubmit={(e) => {
                  e.preventDefault();
                  void ask(input);
                }}
              >
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={s.placeholder}
                  aria-label={s.placeholder}
                  disabled={busy}
                />
                <button type="submit" disabled={busy || !input.trim()}>
                  {s.send}
                </button>
              </form>
          </>
          )}
        </main>
      </div>
    </div>
  );
}
