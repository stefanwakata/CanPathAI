import { useRef, useState, type FormEvent } from "react";
import { saveProfile } from "../api";
import { searchNoc, type NocEntry } from "../data/noc";
import { PROVINCES, STATUSES, t } from "../i18n";
import type { Lang, UserProfile } from "../types";

interface Props {
  lang: Lang;
  sessionId: string | null;
  profile: UserProfile;
  onChange: (p: UserProfile) => void;
  onSession: (sid: string) => void;
}

export default function ProfilePanel({ lang, sessionId, profile, onChange, onSession }: Props) {
  const s = t(lang);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [acOpen, setAcOpen] = useState(false);
  const blurTimer = useRef<number | undefined>(undefined);

  const set = (patch: Partial<UserProfile>) => {
    setSaved(false);
    onChange({ ...profile, ...patch });
  };

  const matches = acOpen ? searchNoc(profile.occupation ?? "") : [];

  const pick = (n: NocEntry) => {
    set({ occupation: lang === "fr" ? n.fr : n.en, noc_code: n.code });
    setAcOpen(false);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await saveProfile({ ...profile, language: lang }, sessionId);
      onSession(res.session_id);
      setSaved(true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="profile" onSubmit={submit}>
      <h3>{s.profile}</h3>
      <label className="autocomplete">
        {s.occupation}
        <input
          value={profile.occupation ?? ""}
          onChange={(e) => {
            set({ occupation: e.target.value });
            setAcOpen(true);
          }}
          onFocus={() => setAcOpen(true)}
          onBlur={() => {
            blurTimer.current = window.setTimeout(() => setAcOpen(false), 150);
          }}
          placeholder={lang === "fr" ? "ex. infirmière, développeur…" : "e.g. nurse, developer…"}
          autoComplete="off"
        />
        {matches.length > 0 && (
          <ul className="ac-list" role="listbox">
            {matches.map((n) => (
              <li key={n.code} role="option" aria-selected={false}>
                <button type="button" onMouseDown={() => pick(n)}>
                  <span className="ac-code">{n.code}</span> {lang === "fr" ? n.fr : n.en}
                </button>
              </li>
            ))}
          </ul>
        )}
        <span className="hint">{s.occupationHint}</span>
      </label>
      <label>
        {s.nocCode}
        <input
          value={profile.noc_code ?? ""}
          onChange={(e) => set({ noc_code: e.target.value.replace(/\D/g, "") })}
          placeholder="21232"
          maxLength={5}
          inputMode="numeric"
        />
      </label>
      <label>
        {s.province}
        <select value={profile.province ?? ""} onChange={(e) => set({ province: e.target.value })}>
          <option value="">—</option>
          {PROVINCES.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </label>
      <label>
        {s.country}
        <input
          value={profile.country_of_citizenship ?? ""}
          onChange={(e) => set({ country_of_citizenship: e.target.value })}
        />
      </label>
      <label>
        {s.status}
        <select value={profile.status ?? ""} onChange={(e) => set({ status: e.target.value })}>
          <option value="">—</option>
          {STATUSES.map((st) => (
            <option key={st} value={st}>{st}</option>
          ))}
        </select>
      </label>
      <label>
        {s.experience}
        <input
          type="number"
          min={0}
          max={50}
          value={profile.years_experience ?? ""}
          onChange={(e) =>
            set({ years_experience: e.target.value === "" ? undefined : Number(e.target.value) })
          }
        />
      </label>
      <button type="submit" disabled={busy}>{s.saveProfile}</button>
      {saved && <p className="saved-note">{s.profileSaved}</p>}
    </form>
  );
}
