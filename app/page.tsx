"use client";

import { FormEvent, useState } from "react";

type Source = { title: string; url: string; excerpt: string };
type Risk = { category: string; level: "low" | "medium" | "high"; finding: string; action: string; sources: Source[] };
type Brief = { decision: "GO" | "CAUTION" | "REROUTE"; summary: string; uncertainty: string; risks: Risk[]; generatedAt: string };

const labels = { low: "Low", medium: "Caution", high: "High" };

export default function Home() {
  const [brief, setBrief] = useState<Brief | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setError(null); setBrief(null);
    const data = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const response = await fetch("/api/brief", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(data) });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Could not create a live brief.");
      setBrief(body);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not create a live brief."); }
    finally { setLoading(false); }
  }

  return <main>
    <section className="hero"><p className="eyebrow">AGENTIC CINEMA · PARALLEL TRACK</p><h1>Know before<br />the crew moves.</h1><p className="lede">ShootSignal turns a call sheet into a live, cited go / caution / reroute brief—so a production team can react before a shoot day unravels.</p></section>
    <section className="workspace">
      <form onSubmit={submit} className="form"><h2>Create a live shoot brief</h2><label>Location<input name="location" defaultValue="Gamla Stan, Stockholm" required /></label><div className="split"><label>Shoot date<input name="shootDate" type="date" defaultValue="2026-08-20" required /></label><label>Call time<input name="callTime" type="time" defaultValue="07:00" required /></label></div><label>Scene needs<textarea name="sceneNeeds" defaultValue="Exterior dialogue scene. Quiet sound, pedestrian access, a small lighting truck, and rain cover." required /></label><button disabled={loading}>{loading ? "Researching live conditions…" : "Generate cited brief"}</button><p className="caption">Live evidence is researched with Parallel Search. ShootSignal is planning support—not legal, safety, or permit advice.</p></form>
      <div className="result" aria-live="polite">{error && <p className="error">{error}</p>}{!brief && !error && <div className="placeholder"><span>01</span><h2>Decision-ready, not search-result-heavy.</h2><p>Every claim will be attached to its live web evidence, with uncertainty made visible.</p></div>}{brief && <><div className={`decision ${brief.decision.toLowerCase()}`}><span>SHOOT STATUS</span><strong>{brief.decision}</strong><p>{brief.summary}</p></div><p className="uncertainty">{brief.uncertainty} · Generated {new Date(brief.generatedAt).toLocaleString()}</p><div className="risks">{brief.risks.map((risk, index) => <article key={index}><div><span className={`pill ${risk.level}`}>{labels[risk.level]}</span><h3>{risk.category}</h3></div><p>{risk.finding}</p><p className="action"><b>Move:</b> {risk.action}</p><div className="sources">{risk.sources.map((source) => <a key={source.url} href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a>)}</div></article>)}</div></>}</div>
    </section>
  </main>;
}
