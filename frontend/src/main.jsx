import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { api } from "./lib/api";
import "./styles.css";

const causes = [
  ["education", "Education"],
  ["environment", "Environment"],
  ["community", "Community Service"],
];
const skills = ["Teaching", "Communication", "Writing", "Organization", "Technical Skills", "Creative Skills"];
const equipment = [["laptop", "Laptop"], ["smartphone", "Smartphone"], ["internet", "Internet Access"], ["books", "Books or Stationery"], ["gloves", "Gloves"], ["none", "No Special Equipment"]];

function Shell({ title, kicker, children }) {
  return <section className="shell"><p className="kicker">{kicker}</p><h1>{title}</h1>{children}</section>;
}

function ToggleChips({ values, selected, onChange }) {
  return <div className="chips">{values.map(([value, label]) => (
    <button type="button" className={selected.includes(value) ? "chip selected" : "chip"} key={value}
      onClick={() => onChange(selected.includes(value) ? selected.filter(item => item !== value) : [...selected, value])}>
      {label}
    </button>
  ))}</div>;
}

function Layout({ children }) {
  return <><header><Link className="brand" to="/">Volunteer<span>Match</span><i>AI</i></Link><nav><Link to="/profile">My profile</Link><Link to="/history">History</Link></nav></header><main>{children}</main><footer>Small actions. Real community impact.</footer></>;
}

function Home() {
  return <Shell kicker="VolunteerMatchAI" title="Find a way to help that fits your day.">
    <p className="lede">A context-aware volunteering companion for realistic, meaningful action.</p>
    <div className="hero-actions"><Link className="button primary" to="/profile">Get started <b>→</b></Link><Link className="text-link" to="/history">View your impact</Link></div>
    <div className="feature-grid"><div><strong>01</strong><h3>Choose what matters</h3><p>Select causes, skills, and interests.</p></div><div><strong>02</strong><h3>Share today's context</h3><p>Time, energy, access, and participation mode.</p></div><div><strong>03</strong><h3>Make it count</h3><p>Complete activities and track your impact.</p></div></div>
  </Shell>;
}

function Profile() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", description: "", causes: ["education"], skills: [], availability: "flexible", location: "remote", accessibility_needs: [] });
  const [error, setError] = useState("");
  const update = (key, value) => setForm(current => ({ ...current, [key]: value }));
  async function submit(event) {
    event.preventDefault();
    setError("");
    if (!form.causes.length) return setError("Choose at least one cause.");
    try {
      const profile = await api("/profiles", { method: "POST", body: JSON.stringify(form) });
      localStorage.setItem("profileId", profile.id);
      navigate("/context");
    } catch (reason) { setError(reason.message); }
  }
  return <Shell kicker="Step 1 of 3" title="What kind of change feels meaningful?">
    <form onSubmit={submit} className="form">
      <label>Your name<input required value={form.name} onChange={event => update("name", event.target.value)} placeholder="Ada Lovelace" /></label>
      <label>Email<input required type="email" value={form.email} onChange={event => update("email", event.target.value)} placeholder="you@example.com" /></label>
      <label>About you<textarea value={form.description} onChange={event => update("description", event.target.value)} placeholder="What would you enjoy contributing?" /></label>
      <label>Causes <span className="hint">Pick one or more</span><ToggleChips values={causes} selected={form.causes} onChange={value => update("causes", value)} /></label>
      <label>Skills <ToggleChips values={skills.map(value => [value.toLowerCase().replaceAll(" ", "-"), value])} selected={form.skills} onChange={value => update("skills", value)} /></label>
      <label>Participation preference<select value={form.location} onChange={event => update("location", event.target.value)}><option value="remote">Remote</option><option value="local">On-site</option></select></label>
      {error && <div className="error">{error}</div>}
      <button className="button primary">Continue <b>→</b></button>
    </form>
  </Shell>;
}

function Context() {
  const navigate = useNavigate();
  const [presets, setPresets] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ time: "30m", energy: "medium", environment: "any", mode: "any", skills: [], equipment: [], causes: [] });
  const update = (key, value) => setForm(current => ({ ...current, [key]: value }));
  useEffect(() => { api("/contexts").then(setPresets).catch(reason => setError(reason.message)); }, []);
  async function submit(event) {
    event.preventDefault();
    const profileId = localStorage.getItem("profileId");
    if (!profileId) return navigate("/profile");
    try {
      const saved = await api(`/profiles/${profileId}/contexts`, { method: "POST", body: JSON.stringify(form) });
      localStorage.setItem("contextId", saved.id);
      navigate("/recommendation");
    } catch (reason) { setError(reason.message); }
  }
  return <Shell kicker="Step 2 of 3" title="What does today look like?">
    <p className="lede">The best match starts with what you can genuinely give today.</p>
    {error && <div className="error">{error}</div>}
    <div className="context-grid">{presets.map(preset => <button type="button" className="context-card" key={preset.id} onClick={() => setForm(current => ({ ...current, time: preset.time, environment: preset.environment, mode: preset.mode }))}><strong>{preset.label}</strong><small>{preset.description}</small></button>)}</div>
    <form onSubmit={submit} className="form context-form">
      <label>Available time<select value={form.time} onChange={event => update("time", event.target.value)}><option value="15m">15 minutes</option><option value="30m">30 minutes</option><option value="1h">60 minutes</option><option value="90m">90 minutes</option><option value="2h">120 minutes</option><option value="weekend">Weekend window</option><option value="flexible">Flexible</option></select></label>
      <label>Energy level<select value={form.energy} onChange={event => update("energy", event.target.value)}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label>
      <label>Environment<select value={form.environment} onChange={event => update("environment", event.target.value)}><option value="any">Any</option><option value="indoors">Home / Hostel / Campus</option><option value="outdoors">Outside</option></select></label>
      <label>Participation mode<select value={form.mode} onChange={event => update("mode", event.target.value)}><option value="any">Any</option><option value="remote">Remote</option><option value="in-person">On-site</option></select></label>
      <label>Causes for today<ToggleChips values={causes} selected={form.causes} onChange={value => update("causes", value)} /></label>
      <label>Available skills<input placeholder="e.g. teaching, writing" onChange={event => update("skills", event.target.value.split(",").map(value => value.trim().toLowerCase()).filter(Boolean))} /></label>
      <label>Available equipment<ToggleChips values={equipment} selected={form.equipment} onChange={value => update("equipment", value)} /></label>
      <button className="button primary">Find my match <b>→</b></button>
    </form>
  </Shell>;
}

function Recommendation() {
  const navigate = useNavigate();
  const [state, setState] = useState({ loading: true, error: "", data: null });
  useEffect(() => {
    const profileId = localStorage.getItem("profileId");
    const contextId = localStorage.getItem("contextId");
    if (!profileId || !contextId) return navigate("/profile");
    api("/recommendations", { method: "POST", body: JSON.stringify({ profile_id: Number(profileId), context_id: contextId }) })
      .then(data => setState({ loading: false, data, error: "" })).catch(error => setState({ loading: false, data: null, error: error.message }));
  }, [navigate]);
  if (state.loading) return <Shell kicker="Step 3 of 3" title="Finding your fit…"><div className="loading">Checking opportunities against your constraints.</div></Shell>;
  if (state.error) return <Shell kicker="Sorry" title="We hit a snag."><div className="error">{state.error}</div><Link className="button" to="/context">Try again</Link></Shell>;
  const data = state.data;
  if (!data.matched) return <Shell kicker="No exact match" title="Nothing quite fits today."><p className="lede">{data.reason}</p><Link className="button primary" to="/context">Modify context</Link></Shell>;
  const opportunity = data.opportunity;
  return <Shell kicker="Your thoughtful match" title={opportunity.title}>
    <div className="match-card"><div className="match-meta">{opportunity.organization} · {opportunity.format} · {opportunity.duration}</div><p>{opportunity.description}</p><div className="tags">{[opportunity.cause, opportunity.energy, opportunity.mode, ...opportunity.skills].map(tag => <span key={tag}>{tag}</span>)}</div><div className="impact"><b>Why it fits</b><span>{data.reason}</span></div><h3>Task breakdown</h3><ul>{opportunity.task_breakdown.map(task => <li key={task}>{task}</li>)}</ul><p><strong>Equipment:</strong> {opportunity.equipment.join(", ") || "No special equipment"}</p><p><strong>Impact:</strong> {opportunity.impact}</p><button className="button primary" onClick={() => navigate("/complete", { state: { opportunity, recommendationId: data.recommendation_id } })}>Accept recommendation <b>→</b></button></div>
    <button className="text-button" onClick={() => navigate("/alternatives", { state: { items: data.alternatives, recommendationId: data.recommendation_id } })}>Get another suggestion</button><Link className="text-link" to="/context">Modify daily context</Link>
  </Shell>;
}

function Alternatives() {
  const navigate = useNavigate();
  const { state } = useLocation();
  const [items, setItems] = useState(state?.items || []);
  const [error, setError] = useState("");
  useEffect(() => {
    if (items.length || !state?.recommendationId) return;
    api(`/recommendations/${state.recommendationId}/alternatives`, { method: "POST" }).then(setItems).catch(reason => setError(reason.message));
  }, [items.length, state?.recommendationId]);
  return <Shell kicker="Explore more" title="Other good fits">{error && <div className="error">{error}</div>}<div className="alt-list">{items.length ? items.map(item => <button className="alt-card" key={item.id} onClick={() => navigate("/complete", { state: { opportunity: item } })}><b>{item.title}</b><span>{item.duration} · {item.mode}</span></button>) : <p className="empty">No other qualifying opportunities were found.</p>}</div><Link className="text-link" to="/recommendation">← Back to match</Link></Shell>;
}

function Complete() {
  const navigate = useNavigate();
  const { state } = useLocation();
  const opportunity = state?.opportunity;
  const [status, setStatus] = useState({ loading: false, done: false, error: "" });
  if (!opportunity) return <Shell title="No opportunity selected"><Link to="/context">Start again</Link></Shell>;
  async function finish() {
    setStatus({ loading: true, done: false, error: "" });
    try {
      await api(state?.recommendationId ? `/recommendations/${state.recommendationId}/completion` : "/completions", { method: "POST", body: state?.recommendationId ? undefined : JSON.stringify({ profile_id: Number(localStorage.getItem("profileId")), opportunity_id: opportunity.id }) });
      setStatus({ loading: false, done: true, error: "" });
    } catch (reason) { setStatus({ loading: false, done: false, error: reason.message }); }
  }
  return <Shell kicker="One last step" title={status.done ? "You made an impact." : "Ready to make it real?"}>{status.done ? <><p className="lede">Your completion is saved.</p><Link className="button primary" to="/history">See my history</Link></> : <><div className="match-card"><div className="match-meta">{opportunity.organization} · {opportunity.duration}</div><h2>{opportunity.title}</h2><p>{opportunity.description}</p></div>{status.error && <div className="error">{status.error}</div>}<button disabled={status.loading} className="button primary" onClick={finish}>{status.loading ? "Saving…" : "Mark as completed"} <b>✓</b></button></>}</Shell>;
}

function History() {
  const [state, setState] = useState({ loading: true, data: null, error: "" });
  useEffect(() => { const id = localStorage.getItem("profileId"); if (!id) return setState({ loading: false, data: { total_completed: 0, total_minutes: 0, items: [] }, error: "" }); api(`/profiles/${id}/history`).then(data => setState({ loading: false, data, error: "" })).catch(error => setState({ loading: false, data: null, error: error.message })); }, []);
  if (state.loading) return <Shell kicker="Your impact" title="A record of showing up."><div className="loading">Loading history…</div></Shell>;
  if (state.error) return <Shell kicker="Your impact" title="History unavailable"><div className="error">{state.error}</div></Shell>;
  return <Shell kicker="Your impact" title="A record of showing up."><div className="feature-grid"><div><strong>{state.data.total_completed}</strong><p>completed activities</p></div><div><strong>{state.data.total_minutes}</strong><p>estimated minutes</p></div></div>{state.data.items.length ? <div className="history-list">{state.data.items.map(item => <article key={`${item.kind}-${item.id}`}><span>{item.kind === "completed" ? new Date(item.completed_at).toLocaleDateString() : new Date(item.created_at).toLocaleDateString()}</span><b>{item.opportunity?.title || "Opportunity"}</b><small>{item.kind === "completed" ? "Completed" : "Recommended"} · {item.opportunity?.cause || ""}</small></article>)}</div> : <div className="empty">Your completed actions will appear here.<br /><Link className="text-link" to="/profile">Find your first match →</Link></div>}</Shell>;
}

function App() { return <Layout><Routes><Route path="/" element={<Home />} /><Route path="/profile" element={<Profile />} /><Route path="/context" element={<Context />} /><Route path="/recommendation" element={<Recommendation />} /><Route path="/alternatives" element={<Alternatives />} /><Route path="/complete" element={<Complete />} /><Route path="/history" element={<History />} /></Routes></Layout>; }
createRoot(document.getElementById("root")).render(<BrowserRouter><App /></BrowserRouter>);
