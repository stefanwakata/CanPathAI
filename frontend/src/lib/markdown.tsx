import React from "react";

/** Minimal, safe markdown renderer: bold, italics, inline code, links, lists,
 *  headings. No raw-HTML injection — everything is built as React elements. */

function renderInline(text: string, keyBase: string): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  // links | bold | italic | code
  const rx = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = rx.exec(text)) !== null) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const key = `${keyBase}-${i++}`;
    if (m[1] && m[2]) {
      out.push(
        <a key={key} href={m[2]} target="_blank" rel="noreferrer noopener">
          {m[1]}
        </a>,
      );
    } else if (m[3]) {
      out.push(<strong key={key}>{m[3]}</strong>);
    } else if (m[4]) {
      out.push(<em key={key}>{m[4]}</em>);
    } else if (m[5]) {
      out.push(<code key={key}>{m[5]}</code>);
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

export function Markdown({ text }: { text: string }): React.ReactElement {
  const blocks: React.ReactNode[] = [];
  const lines = text.split("\n");
  let list: string[] = [];
  let para: string[] = [];
  let k = 0;

  const flushList = () => {
    if (list.length) {
      blocks.push(
        <ul key={`ul-${k++}`}>
          {list.map((item, j) => (
            <li key={j}>{renderInline(item, `li-${k}-${j}`)}</li>
          ))}
        </ul>,
      );
      list = [];
    }
  };
  const flushPara = () => {
    if (para.length) {
      blocks.push(<p key={`p-${k++}`}>{renderInline(para.join(" "), `p-${k}`)}</p>);
      para = [];
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();
    const heading = /^(#{1,4})\s+(.*)$/.exec(trimmed);
    const bullet = /^[-*•]\s+(.*)$/.exec(trimmed);
    const numbered = /^\d+[.)]\s+(.*)$/.exec(trimmed);
    if (!trimmed) {
      flushPara();
      flushList();
    } else if (heading) {
      flushPara();
      flushList();
      blocks.push(<h4 key={`h-${k++}`}>{renderInline(heading[2], `h-${k}`)}</h4>);
    } else if (bullet) {
      flushPara();
      list.push(bullet[1]);
    } else if (numbered) {
      flushPara();
      list.push(numbered[1]);
    } else {
      flushList();
      para.push(trimmed);
    }
  }
  flushPara();
  flushList();
  return <div className="md">{blocks}</div>;
}
