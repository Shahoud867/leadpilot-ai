import React, { useState, useEffect, useRef, useCallback } from "react";
import { createRoot } from "react-dom/client";
import {
  LayoutDashboard,
  Inbox,
  Users,
  Flame,
  ScanLine,
  GitBranch,
  Columns3,
  Clock3,
  LifeBuoy,
  BarChart3,
  Workflow,
  FlaskConical,
  Settings,
  Search,
  Bell,
  ChevronDown,
  ChevronRight,
  ArrowUpRight,
  ArrowRight,
  Plus,
  Download,
  Upload,
  X,
  Check,
  AlertCircle,
  LogOut,
  Menu,
  ArrowLeft,
  RefreshCw,
  Play,
  Timer,
  ShieldCheck,
  Sparkles,
  Send,
  Calendar,
  MessageSquare,
  SlidersHorizontal,
  MoreHorizontal,
  CheckCircle2,
  MapPin,
  Target,
  Scale,
  Activity,
  FileText,
  Copy,
  Briefcase,
  Command,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  Legend,
} from "recharts";
import {
  api,
  setCsrf,
  Row,
  money,
  num,
  date,
  initials,
  label,
  stages,
  nextStages,
} from "./lib";
import "./style.css";
const nav = [
  ["Overview", LayoutDashboard],
  ["Lead inbox", Inbox],
  ["All leads", Users],
  ["Smart priority", Flame],
  ["Qualification", ScanLine],
  ["Assignment board", GitBranch],
  ["Sales pipeline", Columns3],
  ["Follow-ups", Clock3],
  ["Recovery ledger", LifeBuoy],
  ["Analytics", BarChart3],
  ["Decision trace", Workflow],
  ["Demo Lab", FlaskConical],
  ["Team & settings", Settings],
] as const;
const subtitles: Record<string, string> = {
  Overview: "A clear view of your leads, your team, and what needs attention.",
  "Lead inbox": "Turn every incoming inquiry into an owned next action.",
  "All leads": "One reliable source of truth for every opportunity.",
  "Smart priority": "Know who needs your attention next, and why.",
  Qualification: "Evidence-based scoring with every contribution explained.",
  "Assignment board": "The right inquiry. The right adviser. A fair workload.",
  "Sales pipeline": "Move real conversations toward verified outcomes.",
  "Follow-ups": "Keep your promises, one timely conversation at a time.",
  "Recovery ledger":
    "Make missed opportunities visible, owned, and recoverable.",
  Analytics: "Understand the journey from first inquiry to verified outcome.",
  "Decision trace": "Open the reasoning behind every automated decision.",
  "Demo Lab": "Explore a complete sales journey in a safe simulation.",
  "Team & settings": "Shape the workspace around the way your team works.",
};
function Button({
  children,
  onClick,
  kind = "",
  disabled = false,
  type = "button",
  ...props
}: any) {
  return (
    <button
      type={type}
      className={"btn " + kind}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
}
function Badge({ children, tone = "" }: any) {
  return <span className={"badge " + tone}>{children}</span>;
}
function Stage({ value }: any) {
  return (
    <Badge
      tone={
        value === "won"
          ? "green"
          : value === "lost" || value === "dormant"
            ? "gray"
            : value === "appointment"
              ? "purple"
              : value === "qualified"
                ? "blue"
                : "amber"
      }
    >
      {label(value)}
    </Badge>
  );
}
function Score({ value }: any) {
  return (
    <span
      className={
        "score " + (value >= 80 ? "hot" : value >= 60 ? "warm" : "cool")
      }
    >
      <span /> {value}
    </span>
  );
}
function Empty({
  title = "Nothing here yet",
  text = "Create a lead or run a scenario in the Demo Lab to get started.",
  action,
}: any) {
  return (
    <div className="empty">
      <Inbox size={30} />
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  );
}
function Modal({ title, children, close, wide = false }: any) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const prev = document.activeElement as HTMLElement;
    const el = ref.current;
    el?.querySelector<HTMLElement>("input,select,textarea,button")?.focus();
    function key(e: KeyboardEvent) {
      if (e.key === "Escape") close();
      if (e.key === "Tab") {
        const fs = el?.querySelectorAll<HTMLElement>(
          "button:not([disabled]),input,select,textarea,a[href]",
        );
        if (!fs?.length) return;
        const a = fs[0],
          b = fs[fs.length - 1];
        if (e.shiftKey && document.activeElement === a) {
          b.focus();
          e.preventDefault();
        } else if (!e.shiftKey && document.activeElement === b) {
          a.focus();
          e.preventDefault();
        }
      }
    }
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      prev?.focus();
    };
  }, []);
  return (
    <div
      className="overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <div
        className={"modal " + (wide ? "wide" : "")}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        ref={ref}
      >
        <div className="modal-head">
          <h2>{title}</h2>
          <button className="icon" aria-label="Close dialog" onClick={close}>
            <X size={20} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
function Field({ label: lab, name, children, ...props }: any) {
  const id = React.useId();
  return (
    <div className="field">
      <label htmlFor={id}>{lab}</label>
      {children ? (
        React.cloneElement(children, { id })
      ) : (
        <input id={id} name={name} {...props} />
      )}
    </div>
  );
}
function Panel({ title, caption, action, children, className = "" }: any) {
  return (
    <section className={"panel " + className}>
      <div className="panel-head">
        <div>
          <h3>{title}</h3>
          {caption && <p>{caption}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
function Login({ ready }: { ready: () => void }) {
  const [email, E] = useState("owner@margalla.example"),
    [password, P] = useState("Demo@2026!"),
    [busy, B] = useState(false),
    [error, err] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    B(true);
    err("");
    try {
      await api("/auth/login", { email, password });
      ready();
    } catch (e: any) {
      err(e.message);
    } finally {
      B(false);
    }
  }
  return (
    <div className="login">
      <div className="login-story">
        <div className="brand">
          <span className="logo">
            <Workflow />
          </span>
          LeadPilot <span className="ai">AI</span>
        </div>
        <Badge tone="glass">BUILT FOR PAKISTAN'S GROWING TEAMS</Badge>
        <h1>
          Every inquiry.
          <br />A clear next step.
        </h1>
        <p>A calmer, smarter way to turn conversations into opportunities.</p>
        <div className="login-flow">
          Capture <ArrowRight /> Qualify <ArrowRight /> Assign <ArrowRight />{" "}
          Grow
        </div>
        <div className="login-disclosure">
          <ShieldCheck size={18} /> Local demo · Synthetic data · No external
          messages
        </div>
      </div>
      <div className="login-form">
        <form onSubmit={submit}>
          <Badge tone="blue">INTERACTIVE DEMO</Badge>
          <h2>Welcome to your workspace</h2>
          <p>Explore LeadPilot with a fictional Islamabad business.</p>
          <Field label="Demo account">
            <select value={email} onChange={(e) => E(e.target.value)}>
              <option value="owner@margalla.example">
                Margalla Skills — Owner
              </option>
              <option value="manager@margalla.example">
                Margalla Skills — Manager
              </option>
              <option value="ayesha@margalla.example">
                Margalla Skills — Adviser
              </option>
              <option value="owner@estates.example">
                Twin Cities Estates — Owner
              </option>
              <option value="viewer@estates.example">
                Twin Cities Estates — Viewer
              </option>
            </select>
          </Field>
          <Field
            label="Password"
            type="password"
            value={password}
            onChange={(e: any) => P(e.target.value)}
            required
          />
          <Button type="submit" kind="primary full" disabled={busy}>
            {busy ? "Signing in…" : "Enter workspace"}
            <ArrowRight size={17} />
          </Button>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <p className="small">
            Demo password: <code>Demo@2026!</code>
            <br />
            All names, conversations, and outcomes are synthetic.
          </p>
        </form>
      </div>
    </div>
  );
}
function App() {
  const [user, U] = useState<Row | null>(null),
    [auth, A] = useState(true),
    [page, P] = useState("Overview"),
    [metrics, M] = useState<Row | null>(null),
    [team, T] = useState<Row[]>([]),
    [days, D] = useState(30),
    [source, S] = useState(""),
    [revision, R] = useState(0),
    [search, Q] = useState(""),
    [toast, Toast] = useState<Row | null>(null),
    [busy, B] = useState(false),
    [mobile, Mobile] = useState(false),
    [capture, C] = useState(false),
    [selected, Sel] = useState<string | null>(null),
    [notifications, N] = useState(false),
    [error, Err] = useState("");
  const loadUser = useCallback(async () => {
    try {
      const u = await api("/auth/me");
      setCsrf(u.csrf);
      U(u);
    } catch {
      U(null);
    } finally {
      A(false);
    }
  }, []);
  useEffect(() => {
    loadUser();
  }, [loadUser]);
  useEffect(() => {
    if (!user) return;
    let alive = true;
    Promise.all([
      api(`/analytics?days=${days}&source=${encodeURIComponent(source)}`),
      api("/team"),
    ])
      .then(([m, t]) => {
        if (alive) {
          M(m);
          T(t);
          Err("");
        }
      })
      .catch((e) => Err(e.message));
    return () => {
      alive = false;
    };
  }, [user?.id, days, source, revision]);
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => Toast(null), 5000);
    return () => clearTimeout(t);
  }, [toast]);
  const refresh = () => R((x) => x + 1);
  const notify = (message: string, tone = "success") =>
    Toast({ message, tone });
  const act = async (fn: () => Promise<any>, success = "Changes saved") => {
    B(true);
    try {
      const result = await fn();
      notify(success);
      refresh();
      return result;
    } catch (e: any) {
      notify(e.message, "error");
      return null;
    } finally {
      B(false);
    }
  };
  const go = (p: string) => {
    P(p);
    Mobile(false);
  };
  const canManage = !!user && ["owner", "manager"].includes(user.role),
    canEdit = !!user && user.role !== "viewer";
  async function logout() {
    await act(() => api("/auth/logout", {}), "Signed out");
    U(null);
    setCsrf("");
    M(null);
  }
  if (auth)
    return (
      <div className="boot">
        <span className="logo">
          <Workflow />
        </span>
        <p>Opening your workspace…</p>
      </div>
    );
  if (!user) return <Login ready={loadUser} />;
  const ctx = {
    user,
    metrics,
    team,
    revision,
    refresh,
    act,
    busy,
    notify,
    canManage,
    canEdit,
    open: Sel,
    go,
    search,
  };
  return (
    <div className="app">
      <a href="#content" className="skip">
        Skip to content
      </a>
      {mobile && <div className="mobile-shade" onClick={() => Mobile(false)} />}
      <aside className={mobile ? "sidebar open" : "sidebar"}>
        <button className="brand" onClick={() => go("Overview")}>
          <span className="logo">
            <Workflow size={23} />
          </span>
          LeadPilot <span className="ai">AI</span>
        </button>
        <div className="workspace">
          <span className="workspace-logo">
            {user.tenant.name.includes("Skills") ? "MS" : "TC"}
          </span>
          <div>
            <strong>{user.tenant.name.split(" ·")[0]}</strong>
            <small>
              {user.tenant.name.includes("Skills")
                ? "Education & training"
                : "Property & real estate"}
            </small>
          </div>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {nav.map(([n, Icon], i) => (
            <React.Fragment key={n}>
              {i === 9 && (
                <div className="nav-label second">INSIGHTS & CONTROL</div>
              )}
              <button
                className={page === n ? "nav active" : "nav"}
                onClick={() => {
                  Q("");
                  go(n);
                }}
                aria-label={n}
                aria-current={page === n ? "page" : undefined}
              >
                <Icon size={18} />
                <span>{n}</span>
                {n === "Recovery ledger" && metrics?.overdue > 0 && (
                  <b className="nav-count">{metrics?.overdue}</b>
                )}
                {n === "Demo Lab" && <span className="new">TRY IT</span>}
              </button>
            </React.Fragment>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="simulation">
            <span className="live-dot" />
            SIMULATION MODE<p>No live customer messages</p>
          </div>
          <div className="profile">
            <span className="avatar">{initials(user.name)}</span>
            <div>
              <strong>{user.name}</strong>
              <small>{label(user.role)} workspace</small>
            </div>
            <button className="icon" aria-label="Sign out" onClick={logout}>
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      <div className="shell">
        <header className="topbar">
          <div className="crumb">
            <button
              className="icon mobile-only"
              aria-label="Open navigation"
              onClick={() => Mobile(!mobile)}
            >
              <Menu size={20} />
            </button>
            <span>Workspace</span>
            <ChevronRight size={14} />
            <strong>{page}</strong>
          </div>
          <div className="top-actions">
            <form
              className="global-search"
              onSubmit={(e) => {
                e.preventDefault();
                go("All leads");
              }}
            >
              <Search size={16} />
              <input
                aria-label="Search all leads"
                placeholder="Search leads…"
                value={search}
                onChange={(e) => Q(e.target.value)}
              />
              <kbd>↵</kbd>
            </form>
            <span className="pkt">
              PKT <span className="live-dot" />
            </span>
            <div className="notification-wrap">
              <button
                className="icon notification"
                aria-label="Notifications"
                onClick={() => N(!notifications)}
              >
                <Bell size={19} />
                {metrics?.overdue > 0 && <i />}
              </button>
              {notifications && (
                <div className="notification-pop">
                  <h3>Needs your attention</h3>
                  <p>{num(metrics?.overdue)} overdue tasks in this cohort.</p>
                  <Button
                    onClick={() => {
                      go("Recovery ledger");
                      N(false);
                    }}
                  >
                    Open recovery ledger <ArrowRight size={15} />
                  </Button>
                </div>
              )}
            </div>
            <span className="avatar small-avatar">{initials(user.name)}</span>
          </div>
        </header>
        <main id="content">
          <div className="page-head">
            <div>
              <div className="eyebrow">
                {page === "Overview"
                  ? "YOUR SALES, IN FOCUS"
                  : page === "Demo Lab"
                    ? "SAFE TO EXPLORE"
                    : "LEADPILOT WORKSPACE"}
              </div>
              <h1>
                {page === "Overview"
                  ? "Good afternoon, " + user.name.split(" ")[0] + "."
                  : page}
                <span className="heading-dot">
                  {page === "Overview" ? " ✧" : ""}
                </span>
              </h1>
              <p>{subtitles[page]}</p>
            </div>
            <div className="head-actions">
              {page === "Overview" || page === "Analytics" ? (
                <>
                  <select
                    aria-label="Reporting range"
                    className="select-btn"
                    value={days}
                    onChange={(e) => D(+e.target.value)}
                  >
                    <option value={7}>Last 7 days</option>
                    <option value={30}>Last 30 days</option>
                    <option value={90}>Last 90 days</option>
                    <option value={0}>All history</option>
                  </select>
                  <Button
                    onClick={() =>
                      window.location.assign("/api/v1/leads/export")
                    }
                  >
                    <Download size={16} />
                    Export
                  </Button>
                </>
              ) : null}
              {canManage && (
                <Button kind="primary" onClick={() => C(true)}>
                  <Plus size={17} />
                  New lead
                </Button>
              )}
            </div>
          </div>
          <div className="disclosure">
            <span>
              <span className="live-dot" />
              <b>SIMULATED DATA</b>
              <span className="disclosure-text">
                Fictional businesses. Real workflows. All outcomes are
                hypothetical.
              </span>
            </span>
            <span className="virtual-time">
              <Clock3 size={13} />
              {date(metrics?.clock || user.tenant.clock, true)} PKT
            </span>
          </div>
          {error && (
            <div className="error-banner" role="alert">
              <AlertCircle size={18} />
              {error}
              <Button onClick={refresh}>Retry</Button>
            </div>
          )}
          {!metrics ? (
            <div className="skeleton-grid">
              {[0, 1, 2, 3].map((x) => (
                <div className="skeleton" key={x} />
              ))}
            </div>
          ) : (
            <>
              {page === "Overview" && (
                <Overview ctx={ctx} source={source} setSource={S} />
              )}
              {[
                "All leads",
                "Lead inbox",
                "Smart priority",
                "Qualification",
              ].includes(page) && (
                <LeadWorkspace ctx={ctx} page={page} capture={() => C(true)} />
              )}{" "}
              {page === "Assignment board" && <Assignments ctx={ctx} />}{" "}
              {page === "Sales pipeline" && <Pipeline ctx={ctx} />}{" "}
              {page === "Follow-ups" && <Followups ctx={ctx} />}{" "}
              {page === "Recovery ledger" && <Recovery ctx={ctx} />}{" "}
              {page === "Analytics" && <Analytics ctx={ctx} />}{" "}
              {page === "Decision trace" && <Traces ctx={ctx} />}{" "}
              {page === "Demo Lab" && <DemoLab ctx={ctx} />}{" "}
              {page === "Team & settings" && <Admin ctx={ctx} />}
            </>
          )}
          <footer>
            <span>
              LeadPilot AI <span className="footer-dot">•</span> A little more
              clarity. A lot less missed opportunity.
            </span>
            <span>LP-1 · Local demonstration</span>
          </footer>
        </main>
      </div>
      {toast && (
        <div
          role={toast.tone === "error" ? "alert" : "status"}
          className={"toast " + toast.tone}
        >
          {toast.tone === "error" ? (
            <AlertCircle size={19} />
          ) : (
            <CheckCircle2 size={19} />
          )}
          <span>{toast.message}</span>
          <button
            className="icon"
            aria-label="Dismiss notification"
            onClick={() => Toast(null)}
          >
            <X size={16} />
          </button>
        </div>
      )}
      {capture && <Capture ctx={ctx} close={() => C(false)} />}{" "}
      {selected && (
        <LeadDetail ctx={ctx} id={selected} close={() => Sel(null)} />
      )}
    </div>
  );
}
function KPI({ title, value, detail, icon: Icon, tone = "blue" }: any) {
  return (
    <div className="kpi">
      <div className="kpi-label">
        {title}
        <span className={"kpi-icon " + tone}>
          <Icon size={18} />
        </span>
      </div>
      <strong>{value}</strong>
      <div className="kpi-detail">{detail}</div>
    </div>
  );
}
function Overview({ ctx, source, setSource }: any) {
  const m = ctx.metrics;
  const [recent, L] = useState<Row[]>([]);
  useEffect(() => {
    api("/leads?page_size=5")
      .then((r) => L(r.items))
      .catch((e: any) => ctx.notify(e.message, "error"));
  }, [ctx.revision]);
  return (
    <div className="page-stack">
      <section className="hero">
        <div>
          <Badge tone="glass">
            <Sparkles size={13} /> YOUR NEXT BEST ACTION
          </Badge>
          <h2>
            Good leads deserve
            <br />
            great follow-through.
          </h2>
          <p>
            {m.overdue
              ? `${num(m.overdue)} follow-ups need attention. Give every conversation a clear next step.`
              : "Your team has a clear runway. Bring in an inquiry and let the workflow begin."}
          </p>
          <Button
            kind="white"
            onClick={() => ctx.go(m.overdue ? "Recovery ledger" : "Demo Lab")}
          >
            {m.overdue
              ? "Review missed opportunities"
              : "Explore a live scenario"}
            <ArrowRight size={16} />
          </Button>
        </div>
        <div className="hero-orbit" aria-hidden="true">
          <div className="orbit one" />
          <div className="orbit two" />
          <div className="orbit three" />
          <div className="orbit-center">
            <Workflow size={37} />
          </div>
          <div className="floating f1">
            <ScanLine size={18} />
            <span>
              Qualified with context<small>Every factor explained</small>
            </span>
            <Check size={15} />
          </div>
          <div className="floating f2">
            <Users size={18} />
            <span>
              Balanced by design<small>Capacity-aware assignment</small>
            </span>
            <Check size={15} />
          </div>
        </div>
      </section>
      <div className="section-heading">
        <h2>
          At a glance <span>Persisted cohort metrics</span>
        </h2>
        <select
          aria-label="Overview source"
          value={source}
          onChange={(e) => setSource(e.target.value)}
        >
          <option value="">All lead sources</option>
          {["WhatsApp", "Instagram", "Website", "Walk-in"].map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </div>
      <div className="kpis">
        <KPI
          title="Total inquiries"
          value={num(m.total)}
          detail={
            <>
              <span className="mini-dot blue-dot" />
              Captured in selected period
            </>
          }
          icon={Inbox}
        />
        <KPI
          title="Verified conversions"
          value={num(m.won)}
          detail={
            <>
              <span className="positive">{m.conversion}%</span> of captured
              inquiries
            </>
          }
          icon={Target}
          tone="green"
        />
        <KPI
          title="Won value"
          value={money(m.revenue)}
          detail="Synthetic deals · not realized client revenue"
          icon={Briefcase}
          tone="purple"
        />
        <KPI
          title="Needs attention"
          value={num(m.overdue)}
          detail={<span className="warning">Overdue pending follow-ups</span>}
          icon={Timer}
          tone="amber"
        />
      </div>
      <div className="chart-row">
        <Panel
          title="Inquiry momentum"
          caption="Captured inquiries and verified wins by creation date · simulated"
          action={<Badge tone="gray">PKT</Badge>}
        >
          <div className="chart">
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart
                data={m.trend}
                margin={{ left: -20, right: 12, top: 12, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="inquiries" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0" stopColor="#5263df" stopOpacity={0.22} />
                    <stop offset="1" stopColor="#5263df" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 5"
                  vertical={false}
                  stroke="#edf0f6"
                />
                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  minTickGap={35}
                  tick={{ fontSize: 11, fill: "#7a8296" }}
                />
                <YAxis
                  allowDecimals={false}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: "#7a8296" }}
                />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="inquiries"
                  name="Inquiries"
                  stroke="#5263df"
                  strokeWidth={2.5}
                  fill="url(#inquiries)"
                />
                <Area
                  type="monotone"
                  dataKey="won"
                  name="Verified wins"
                  stroke="#24a084"
                  strokeWidth={2}
                  fill="transparent"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-legend">
            <span>
              <i style={{ background: "#5263df" }} />
              Inquiries
            </span>
            <span>
              <i style={{ background: "#24a084" }} />
              Verified wins
            </span>
          </div>
        </Panel>
        <Panel
          title="Where leads begin"
          caption="Source mix in selected cohort"
          action={<ArrowUpRight size={18} className="muted" />}
        >
          <div className="source-total">
            <strong>{num(m.total)}</strong>
            <span>total inquiries</span>
          </div>
          <div className="source-stack">
            {m.sources.map((s: Row, i: number) => (
              <div
                key={s.source}
                style={{
                  width: `${(s.leads / Math.max(1, m.total)) * 100}%`,
                  background: ["#4e60d8", "#989bf0", "#35b59f", "#f0b75d"][i],
                }}
              />
            ))}
          </div>
          <div className="source-list">
            {m.sources.map((s: Row, i: number) => (
              <div key={s.source}>
                <span>
                  <i
                    style={{
                      background: ["#4e60d8", "#989bf0", "#35b59f", "#f0b75d"][
                        i
                      ],
                    }}
                  />
                  {s.source}
                </span>
                <b>{num(s.leads)}</b>
                <small>
                  {Math.round((s.leads / Math.max(m.total, 1)) * 100)}%
                </small>
              </div>
            ))}
          </div>
        </Panel>
      </div>
      <div className="chart-row bottom-row">
        <Panel
          title="Latest inquiries"
          caption="Every lead has a next step"
          action={
            <button className="text-btn" onClick={() => ctx.go("All leads")}>
              View all leads <ArrowRight size={14} />
            </button>
          }
        >
          <LeadTable leads={recent} ctx={ctx} compact />
        </Panel>
        <Panel
          title="Team pulse"
          caption="Today's assigned workload · PKT"
          action={
            <Badge tone="green">
              <span className="live-dot" />
              Live from data
            </Badge>
          }
        >
          <div className="team-pulse">
            {ctx.team.map((r: Row) => (
              <div key={r.id}>
                <span className="avatar colored">{initials(r.name)}</span>
                <div className="pulse-body">
                  <div>
                    <b>{r.name}</b>
                    <small>
                      {r.load}/{r.capacity}
                    </small>
                  </div>
                  <div className="progress">
                    <i
                      style={{
                        width: `${Math.min(100, (r.load / r.capacity) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
          <button
            className="panel-link"
            onClick={() => ctx.go("Assignment board")}
          >
            Manage allocation <ArrowRight size={15} />
          </button>
        </Panel>
      </div>
      <div className="insight-note">
        <ShieldCheck size={21} />
        <div>
          <b>Decisions you can explain. Outcomes you can verify.</b>
          <p>
            Six deterministic agents coordinate each step. Every recommendation
            has a reason and a human override.
          </p>
        </div>
        <Button onClick={() => ctx.go("Decision trace")}>
          See the reasoning
          <ArrowRight size={15} />
        </Button>
      </div>
    </div>
  );
}
function LeadTable({ leads, ctx, compact = false }: any) {
  if (!leads.length) return <Empty />;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Lead / interest</th>
            <th>Source</th>
            {!compact && <th>Owner</th>}
            <th>Priority</th>
            <th>Stage</th>
            {!compact && <th>Received</th>}
            <th>
              <span className="sr-only">Details</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {leads.map((l: Row) => (
            <tr key={l.id}>
              <td>
                <button className="lead-cell" onClick={() => ctx.open(l.id)}>
                  <span className="avatar lead-avatar">{initials(l.name)}</span>
                  <span>
                    <strong>{l.name}</strong>
                    <small>{l.interest}</small>
                  </span>
                </button>
              </td>
              <td>
                <span
                  className={
                    "source-tag " + l.source.toLowerCase().replace("-", "")
                  }
                >
                  {l.source}
                </span>
              </td>
              {!compact && (
                <td>
                  <span className="owner-label">
                    {ctx.team.find((r: Row) => r.id === l.owner_id)?.name ||
                      "Unassigned"}
                  </span>
                </td>
              )}
              <td>
                <Score value={l.score} />
              </td>
              <td>
                <Stage value={l.stage} />
              </td>
              {!compact && (
                <td className="muted nowrap">{date(l.created_at, true)}</td>
              )}
              <td>
                <button
                  className="icon"
                  aria-label={"Open " + l.name}
                  onClick={() => ctx.open(l.id)}
                >
                  <ChevronRight size={16} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
function LeadWorkspace({ ctx, page, capture }: any) {
  const [list, L] = useState<Row[]>([]),
    [total, Total] = useState(0),
    [pg, PG] = useState(1),
    [q, Q] = useState(ctx.search),
    [stage, ST] = useState(""),
    [source, SO] = useState(""),
    [owner, O] = useState(""),
    [sort, Sort] = useState("created_at"),
    [loading, B] = useState(true),
    [err, E] = useState(""),
    [importer, I] = useState(false);
  useEffect(() => {
    Q(ctx.search);
    PG(1);
  }, [ctx.search]);
  useEffect(() => {
    PG(1);
  }, [page, stage, source, owner, sort]);
  useEffect(() => {
    let alive = true;
    B(true);
    const t = setTimeout(() => {
      const params = new URLSearchParams({
        q,
        stage,
        source,
        owner,
        sort: ["Smart priority", "Qualification"].includes(page)
          ? "score"
          : sort,
        page: String(pg),
        page_size: "20",
      });
      api("/leads?" + params)
        .then((r) => {
          if (alive) {
            L(r.items);
            Total(r.total);
            E("");
          }
        })
        .catch((e) => alive && E(e.message))
        .finally(() => alive && B(false));
    }, 180);
    return () => {
      alive = false;
      clearTimeout(t);
    };
  }, [page, q, stage, source, owner, sort, pg, ctx.revision]);
  return (
    <div className="page-stack">
      {page === "Lead inbox" && (
        <div className="intake-banner">
          <div>
            <Badge tone="blue">CAPTURE AGENT</Badge>
            <h2>A better beginning for every inquiry.</h2>
            <p>
              Capture manually or import a CSV. Duplicates are linked for
              review, never silently overwritten.
            </p>
          </div>
          {ctx.canManage && (
            <div className="row">
              <Button onClick={() => I(true)}>
                <Upload size={16} />
                Import CSV
              </Button>
              <Button kind="primary" onClick={capture}>
                <Plus size={16} />
                Capture inquiry
              </Button>
            </div>
          )}
        </div>
      )}
      {page === "Qualification" && (
        <div className="info-strip">
          <ScanLine size={22} />
          <div>
            <b>A score with evidence, not a prediction.</b>
            <p>
              Interest 30 · budget evidence 20 · urgency up to 30 · context 10 ·
              local fit up to 10. Unknown budget is shown explicitly. Open a
              lead to rerun scoring.
            </p>
          </div>
        </div>
      )}
      {page === "Smart priority" && (
        <div className="info-strip">
          <Flame size={22} />
          <div>
            <b>Highest priority first.</b>
            <p>
              Review evidence, approve a simulated follow-up, snooze a task, or
              record a manager override from each lead.
            </p>
          </div>
        </div>
      )}
      <Panel
        title={
          page === "Lead inbox"
            ? "Incoming inquiries"
            : page === "Smart priority"
              ? "Your next best conversations"
              : page === "Qualification"
                ? "Qualification workbench"
                : "Your lead directory"
        }
        caption={`${num(total)} synthetic records`}
        action={
          ctx.canManage && (
            <Button onClick={() => I(true)}>
              <Upload size={15} />
              Import CSV
            </Button>
          )
        }
      >
        <div className="filters">
          <div className="search-input">
            <Search size={16} />
            <input
              aria-label="Filter leads"
              placeholder="Search name, interest or contact…"
              value={q}
              onChange={(e) => {
                Q(e.target.value);
                PG(1);
              }}
            />
          </div>
          <select
            aria-label="Stage filter"
            value={stage}
            onChange={(e) => ST(e.target.value)}
          >
            <option value="">All stages</option>
            {stages.map((s) => (
              <option key={s} value={s}>
                {label(s)}
              </option>
            ))}
          </select>
          <select
            aria-label="Source filter"
            value={source}
            onChange={(e) => SO(e.target.value)}
          >
            <option value="">All sources</option>
            {["WhatsApp", "Instagram", "Website", "Walk-in"].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          <select
            aria-label="Owner filter"
            value={owner}
            onChange={(e) => O(e.target.value)}
          >
            <option value="">All owners</option>
            {ctx.team.map((r: Row) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
          <select
            aria-label="Sort leads"
            value={sort}
            onChange={(e) => Sort(e.target.value)}
          >
            <option value="created_at">Newest first</option>
            <option value="score">Highest priority</option>
            <option value="name">Name A–Z</option>
          </select>
        </div>
        {err ? (
          <div className="empty error" role="alert">
            {err}
            <Button onClick={ctx.refresh}>Retry</Button>
          </div>
        ) : loading ? (
          <div className="loading-line">Loading inquiries…</div>
        ) : (
          <LeadTable leads={list} ctx={ctx} />
        )}
        <div className="pagination">
          <span>
            {total
              ? `${(pg - 1) * 20 + 1}–${Math.min(pg * 20, total)} of ${num(total)}`
              : "0 results"}
          </span>
          <div>
            <Button disabled={pg === 1 || loading} onClick={() => PG(pg - 1)}>
              <ArrowLeft size={14} />
              Previous
            </Button>
            <span>Page {pg}</span>
            <Button
              disabled={pg * 20 >= total || loading}
              onClick={() => PG(pg + 1)}
            >
              Next
              <ArrowRight size={14} />
            </Button>
          </div>
        </div>
      </Panel>
      {importer && <ImportModal ctx={ctx} close={() => I(false)} />}
    </div>
  );
}
function Capture({ ctx, close }: any) {
  const [campaigns, C] = useState<Row[]>([]);
  useEffect(() => {
    api("/campaigns")
      .then(C)
      .catch((e: any) => ctx.notify(e.message, "error"));
  }, []);
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.currentTarget));
    const r = await ctx.act(
      () =>
        api("/leads", {
          ...d,
          budget: d.budget ? +d.budget : null,
          campaign_id: d.campaign_id || null,
        }),
      "Inquiry captured and agents executed",
    );
    if (r) {
      close();
      ctx.open(r.lead.id);
    }
  }
  return (
    <Modal title="Capture a new inquiry" close={close} wide>
      <form onSubmit={submit}>
        <p className="modal-intro">
          Capture → qualify → prioritize → assign → schedule. Every step is
          persisted.
        </p>
        <div className="form-grid">
          <Field
            label="Display name"
            name="name"
            required
            minLength={2}
            placeholder="Ayesha · Test"
          />
          <Field
            label="Synthetic contact ID"
            name="contact"
            required
            defaultValue={"SYN-MANUAL-" + Date.now().toString().slice(-8)}
            pattern="SYN-.+"
          />
          <Field
            label="Email (optional, .example only)"
            name="email"
            placeholder="ayesha@synthetic.example"
          />
          <Field label="City" name="city" defaultValue="Islamabad" required />
          <Field
            label="Interest"
            name="interest"
            defaultValue={
              ctx.user.tenant.name.includes("Skills")
                ? "Data Science"
                : "DHA Plot"
            }
            required
          />
          <Field
            label="Budget (PKR, optional)"
            name="budget"
            type="number"
            min={0}
            max={2000000000}
          />
          <Field label="Lead source">
            <select name="source">
              <option>Website</option>
              <option>WhatsApp</option>
              <option>Instagram</option>
              <option>Walk-in</option>
            </select>
          </Field>
          <Field label="Urgency">
            <select name="urgency">
              <option value="today">Today</option>
              <option value="this_week">This week</option>
              <option value="this_month">This month</option>
            </select>
          </Field>
          <Field label="Consent">
            <select name="consent">
              <option value="unknown">Unknown — outreach suppressed</option>
              <option value="granted">Explicitly granted (simulated)</option>
              <option value="opted_out">Opted out</option>
            </select>
          </Field>
          <Field label="Campaign">
            <select name="campaign_id">
              <option value="">No campaign</option>
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <Field label="Inquiry text" name="inquiry">
          <textarea
            name="inquiry"
            required
            minLength={5}
            rows={3}
            defaultValue="Assalam-o-Alaikum, please share course details. I would like to discuss enrollment this week."
          />
        </Field>
        <div className="modal-actions">
          <Button onClick={close}>Cancel</Button>
          <Button type="submit" kind="primary" disabled={ctx.busy}>
            <Sparkles size={16} />
            Capture & run agents
          </Button>
        </div>
      </form>
    </Modal>
  );
}
const sampleCSV =
  "name,contact,email,source,city,interest,inquiry,budget,urgency,consent\nAyesha CSV Test,SYN-CSV-001,ayesha@synthetic.example,Website,Islamabad,IELTS,Please share the next IELTS session details,35000,today,granted\nAyesha CSV Test,SYN-CSV-001,ayesha@synthetic.example,Website,Islamabad,IELTS,Duplicate inquiry for manager review,35000,today,granted";
function ImportModal({ ctx, close }: any) {
  const [text, T] = useState(sampleCSV),
    [result, R] = useState<Row | null>(null),
    [validated, V] = useState("");
  async function run(dry: boolean) {
    const r = await ctx.act(
      () => api("/leads/import", { csv_text: text, dry_run: dry }),
      dry ? "CSV validation finished" : "CSV import finished",
    );
    if (r) {
      R(r);
      if (dry && r.valid) V(text);
      else V("");
    }
  }
  return (
    <Modal title="Import synthetic leads" close={close} wide>
      <p className="modal-intro">
        Up to 1,000 rows / 1 MiB. Preview validates every row. Contacts must use
        SYN- IDs and .example emails.
      </p>
      <Field label="Choose a CSV file">
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (f) {
              if (f.size > 900000) {
                ctx.notify("Maximum file size is 900 KB", "error");
                return;
              }
              T(await f.text());
              V("");
              R(null);
            }
          }}
        />
      </Field>
      <Field label="CSV content">
        <textarea
          value={text}
          onChange={(e) => {
            T(e.target.value);
            V("");
            R(null);
          }}
          rows={9}
          className="code-area"
        />
      </Field>
      {result && (
        <div
          className={result.valid ? "info-strip" : "error-banner"}
          role="status"
        >
          {result.valid ? (
            <span>
              {result.dry_run ? "Preview" : "Imported"}: {result.created} new ·{" "}
              {result.duplicates} duplicates · {result.rows} rows
            </span>
          ) : (
            <div>
              {result.errors.map((e: Row) => (
                <p key={e.row}>
                  Row {e.row}: {e.error}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
      <div className="modal-actions">
        <Button
          onClick={() => {
            T(sampleCSV);
            V("");
            R(null);
          }}
        >
          Load sample
        </Button>
        <Button disabled={ctx.busy} onClick={() => run(true)}>
          Validate CSV
        </Button>
        <Button
          kind="primary"
          disabled={ctx.busy || validated !== text}
          onClick={() => run(false)}
        >
          <Upload size={15} />
          Confirm import
        </Button>
      </div>
    </Modal>
  );
}
function LeadDetail({ ctx, id, close }: any) {
  const [data, D] = useState<Row | null>(null),
    [tab, T] = useState("Overview"),
    [edit, E] = useState(false),
    [move, M] = useState(false),
    [override, O] = useState(false),
    [reply, R] = useState(false),
    [redact, Redact] = useState(false),
    [scheduling, Scheduling] = useState(false),
    [error, Err] = useState("");
  useEffect(() => {
    let alive = true;
    api("/leads/" + id)
      .then((r) => {
        if (alive) {
          D(r);
          Err("");
        }
      })
      .catch((e) => alive && Err(e.message));
    return () => {
      alive = false;
    };
  }, [id, ctx.revision]);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    const drawer = document.querySelector<HTMLElement>(".drawer");
    drawer?.querySelector<HTMLElement>("button")?.focus();
    function key(e: KeyboardEvent) {
      if (document.querySelector(".overlay")) return;
      if (e.key === "Escape") {
        close();
        return;
      }
      if (e.key === "Tab") {
        const all = drawer?.querySelectorAll<HTMLElement>(
          "button:not([disabled]),input,select,textarea,a[href]",
        );
        if (!all?.length) return;
        const first = all[0],
          last = all[all.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          last.focus();
          e.preventDefault();
        } else if (!e.shiftKey && document.activeElement === last) {
          first.focus();
          e.preventDefault();
        }
      }
    }
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      previous?.focus();
    };
  }, [id]);
  const l = data?.lead;
  async function replySubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const body = new FormData(e.currentTarget).get("body");
    if (
      await ctx.act(
        () => api(`/leads/${id}/reply`, { body }),
        "Customer reply recorded",
      )
    )
      R(false);
  }
  return (
    <div className="drawer-overlay">
      <div className="drawer-backdrop" onClick={close} />
      <section
        className="drawer"
        role="dialog"
        aria-modal="true"
        aria-label="Lead details"
      >
        <div className="drawer-top">
          <button className="text-btn" onClick={close}>
            <ArrowLeft size={16} />
            Back to workspace
          </button>
          <Button
            onClick={() => window.location.assign("/api/v1/leads/export")}
          >
            <Download size={15} />
            Export
          </Button>
          <button
            className="icon"
            aria-label="Close lead details"
            onClick={close}
          >
            <X size={20} />
          </button>
        </div>
        {error ? (
          <Empty title={error} />
        ) : !data ? (
          <div className="loading-line">Loading lead history…</div>
        ) : (
          <>
            <div className="lead-heading">
              <span className="avatar large-avatar">{initials(l.name)}</span>
              <div>
                <Badge tone="gray">SYNTHETIC CONTACT</Badge>
                <h2>{l.name}</h2>
                <p>
                  <MapPin size={14} />
                  {l.city}
                  <span>·</span>
                  {l.interest}
                </p>
              </div>
              <Score value={l.score} />
            </div>
            <div className="lead-status-row">
              <Stage value={l.stage} />
              <span className="source-tag">{l.source}</span>
              <Badge tone={l.consent === "granted" ? "green" : "amber"}>
                {label(l.consent)} consent
              </Badge>
            </div>
            <div className="tabs">
              {["Overview", "Timeline", "Messages", "Decisions", "Tasks"].map(
                (x) => (
                  <button
                    key={x}
                    className={x === tab ? "active" : ""}
                    onClick={() => T(x)}
                  >
                    {x}
                  </button>
                ),
              )}
            </div>
            <div className="drawer-content">
              {tab === "Overview" && (
                <>
                  <div className="lead-facts">
                    <div>
                      <small>OWNER</small>
                      <b>
                        {ctx.team.find((r: Row) => r.id === l.owner_id)?.name ||
                          "Unassigned"}
                      </b>
                    </div>
                    <div>
                      <small>BUDGET</small>
                      <b>{l.budget === null ? "Unknown" : money(l.budget)}</b>
                    </div>
                    <div>
                      <small>CONTACT ID</small>
                      <b>{l.contact}</b>
                    </div>
                    <div>
                      <small>RECEIVED · PKT</small>
                      <b>{date(l.created_at, true)}</b>
                    </div>
                    <div>
                      <small>URGENCY</small>
                      <b>{label(l.urgency)}</b>
                    </div>
                    <div>
                      <small>APPOINTMENT · PKT</small>
                      <b>
                        {l.appointment_at
                          ? date(l.appointment_at, true)
                          : "Not booked"}
                      </b>
                    </div>
                  </div>
                  <Panel title="The original inquiry">
                    <blockquote>{l.inquiry}</blockquote>
                  </Panel>
                  <Panel
                    title="Qualification evidence"
                    caption="Rule-based · not predicted conversion probability"
                  >
                    <div className="evidence">
                      {data.recommendations
                        .filter((r: Row) => r.agent === "Qualification")
                        .slice(-1)
                        .map((r: Row) => (
                          <TraceEvidence key={r.id} row={r} />
                        ))}
                    </div>
                    {ctx.canEdit && (
                      <div className="panel-padding">
                        <Button
                          onClick={() =>
                            ctx.act(
                              () => api(`/leads/${id}/qualify`, {}),
                              "Scoring refreshed",
                            )
                          }
                          disabled={ctx.busy}
                        >
                          <RefreshCw size={15} />
                          Recalculate score
                        </Button>
                      </div>
                    )}
                  </Panel>
                  {ctx.canEdit && (
                    <div className="action-grid">
                      <Button onClick={() => E(true)}>
                        <SlidersHorizontal size={16} />
                        Edit facts & consent
                      </Button>
                      <Button
                        onClick={() => Scheduling(true)}
                        disabled={["won", "lost", "archived"].includes(l.stage)}
                      >
                        <Calendar size={16} />
                        Schedule follow-up
                      </Button>
                      <Button
                        onClick={() => M(true)}
                        disabled={!nextStages[l.stage]?.length}
                      >
                        <Columns3 size={16} />
                        Move stage
                      </Button>
                      <Button
                        onClick={() => R(true)}
                        disabled={["won", "lost", "archived"].includes(l.stage)}
                      >
                        <MessageSquare size={16} />
                        Simulate reply
                      </Button>
                      {ctx.canManage && (
                        <Button onClick={() => O(true)}>
                          <GitBranch size={16} />
                          Override assignment
                        </Button>
                      )}
                    </div>
                  )}
                  {ctx.user.role === "owner" && (
                    <Button kind="danger" onClick={() => Redact(true)}>
                      Redact contact
                    </Button>
                  )}
                </>
              )}
              {tab === "Timeline" && (
                <div className="timeline">
                  {data.events.map((e: Row) => (
                    <div className="timeline-event" key={e.id}>
                      <span className="timeline-icon">
                        <Activity size={14} />
                      </span>
                      <div>
                        <b>{label(e.kind)}</b>
                        <small>
                          {date(e.created_at, true)} PKT ·{" "}
                          {e.actor === "system"
                            ? "System"
                            : e.actor === "seed"
                              ? "Synthetic history"
                              : "Workspace user"}
                        </small>
                        <pre>{JSON.stringify(e.payload, null, 2)}</pre>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {tab === "Messages" && (
                <>
                  <div className="info-strip">
                    <ShieldCheck size={18} />
                    <p>
                      All conversations are simulated. No message leaves this
                      application.
                    </p>
                  </div>
                  <div className="messages">
                    {data.messages.length ? (
                      data.messages.map((m: Row) => (
                        <div key={m.id} className={"message " + m.direction}>
                          <small>
                            {m.direction === "inbound"
                              ? "Customer simulator"
                              : "Adviser simulator"}{" "}
                            · {m.channel}
                          </small>
                          <p>{m.body}</p>
                          <span>
                            {label(m.status)} · {date(m.created_at, true)} PKT
                          </span>
                        </div>
                      ))
                    ) : (
                      <Empty
                        title="No conversation yet"
                        text="Approve a simulated follow-up from Tasks, or inject a customer reply."
                      />
                    )}
                  </div>
                  {ctx.canEdit && (
                    <Button onClick={() => R(true)}>
                      <MessageSquare size={16} />
                      Simulate customer reply
                    </Button>
                  )}
                </>
              )}
              {tab === "Decisions" && (
                <div className="trace-stack">
                  {data.recommendations.map((r: Row) => (
                    <Panel
                      key={r.id}
                      title={`${r.agent} · ${r.action}`}
                      caption={`${r.policy_version} · ${date(r.created_at, true)} PKT`}
                      action={<Badge tone="blue">{label(r.status)}</Badge>}
                    >
                      <TraceEvidence row={r} />
                    </Panel>
                  ))}
                </div>
              )}
              {tab === "Tasks" && (
                <div className="task-list">
                  {data.tasks.map((t: Row) => (
                    <div className="task-card" key={t.id}>
                      <div>
                        <b>{label(t.kind)}</b>
                        <small>{date(t.due_at, true)} PKT</small>
                      </div>
                      <Badge tone={t.status === "pending" ? "amber" : "gray"}>
                        {label(t.status)}
                      </Badge>
                      {ctx.canEdit && t.status === "pending" && (
                        <div className="row">
                          <Button
                            disabled={ctx.busy}
                            onClick={() =>
                              ctx.act(
                                () =>
                                  api(`/tasks/${t.id}/action`, {
                                    action: "send",
                                  }),
                                "Message approved; process queue in Follow-ups",
                              )
                            }
                          >
                            <Send size={14} />
                            Approve simulated send
                          </Button>
                          <Button
                            onClick={() =>
                              ctx.act(
                                () =>
                                  api(`/tasks/${t.id}/action`, {
                                    action: "snooze",
                                    minutes: 60,
                                  }),
                                "Snoozed for 60 simulated minutes",
                              )
                            }
                          >
                            Snooze 1h
                          </Button>
                          <Button
                            onClick={() =>
                              ctx.act(
                                () =>
                                  api(`/tasks/${t.id}/action`, {
                                    action: "complete",
                                  }),
                                "Task completed",
                              )
                            }
                          >
                            Complete
                          </Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
        {edit && l && (
          <Modal title="Edit lead facts" close={() => E(false)}>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const d = Object.fromEntries(new FormData(e.currentTarget));
                if (
                  await ctx.act(
                    () =>
                      api(
                        "/leads/" + id,
                        { ...d, budget: d.budget ? +d.budget : null },
                        "PATCH",
                      ),
                    "Lead updated",
                  )
                )
                  E(false);
              }}
            >
              <Field label="Name" name="name" defaultValue={l.name} required />
              <Field
                label="Interest"
                name="interest"
                defaultValue={l.interest}
                required
              />
              <Field
                label="Budget (PKR, blank = unknown)"
                name="budget"
                type="number"
                min={0}
                defaultValue={l.budget ?? ""}
              />
              <Field label="Urgency">
                <select name="urgency" defaultValue={l.urgency}>
                  <option value="today">Today</option>
                  <option value="this_week">This week</option>
                  <option value="this_month">This month</option>
                </select>
              </Field>
              <Field label="Consent">
                <select name="consent" defaultValue={l.consent}>
                  <option value="unknown">Unknown</option>
                  <option value="granted">
                    Granted explicitly (simulated)
                  </option>
                  <option value="opted_out">Opted out</option>
                </select>
              </Field>
              <Field
                label="Reason for change"
                name="reason"
                required
                minLength={3}
              />
              <div className="modal-actions">
                <Button type="submit" kind="primary" disabled={ctx.busy}>
                  Save & rescore
                </Button>
              </div>
            </form>
          </Modal>
        )}
        {move && l && <MoveModal ctx={ctx} lead={l} close={() => M(false)} />}{" "}
        {override && l && (
          <OverrideModal ctx={ctx} lead={l} close={() => O(false)} />
        )}{" "}
        {reply && (
          <Modal title="Simulate customer reply" close={() => R(false)}>
            <form onSubmit={replySubmit}>
              <p className="modal-intro">
                Creates an inbound simulated message and advances an assigned
                lead to contacted.
              </p>
              <Field label="Reply text">
                <textarea
                  name="body"
                  required
                  minLength={3}
                  rows={4}
                  defaultValue="Simulated: Thank you! I would like to book a consultation this week."
                />
              </Field>
              <div className="modal-actions">
                <Button type="submit" kind="primary" disabled={ctx.busy}>
                  Record reply
                </Button>
              </div>
            </form>
          </Modal>
        )}
        {scheduling && (
          <Modal title="Schedule a follow-up" close={() => Scheduling(false)}>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const d = Object.fromEntries(new FormData(e.currentTarget));
                if (
                  await ctx.act(
                    () =>
                      api("/tasks", {
                        lead_id: id,
                        due_at: new Date(String(d.due_at)).toISOString(),
                        kind: d.kind,
                      }),
                    "Follow-up scheduled",
                  )
                )
                  Scheduling(false);
              }}
            >
              <Field
                label="Due time (your local time)"
                name="due_at"
                type="datetime-local"
                required
              />
              <Field label="Task type">
                <select name="kind">
                  <option value="follow_up">Follow-up</option>
                  <option value="consultation">Consultation</option>
                </select>
              </Field>
              <p className="small">
                Choose a future time relative to the virtual clock. This
                schedules a task; sending still requires explicit approval.
              </p>
              <div className="modal-actions">
                <Button type="submit" kind="primary" disabled={ctx.busy}>
                  Schedule task
                </Button>
              </div>
            </form>
          </Modal>
        )}
        {redact && (
          <Modal
            title="Redact this synthetic contact?"
            close={() => Redact(false)}
          >
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const reason = new FormData(e.currentTarget).get("reason");
                if (
                  await ctx.act(
                    () => api(`/leads/${id}/delete`, { reason }),
                    "Contact redacted",
                  )
                ) {
                  Redact(false);
                  close();
                }
              }}
            >
              <p>
                Identifying text will be removed, pending outreach suppressed,
                and the action audited. This cannot be undone.
              </p>
              <Field label="Reason" name="reason" required minLength={5} />
              <div className="modal-actions">
                <Button onClick={() => Redact(false)}>Cancel</Button>
                <Button type="submit" kind="danger" disabled={ctx.busy}>
                  Confirm redaction
                </Button>
              </div>
            </form>
          </Modal>
        )}
      </section>
    </div>
  );
}
function MoveModal({ ctx, lead, close, target }: any) {
  const [stage, S] = useState(
    target || (nextStages[lead.stage] || [])[0] || "",
  );
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.currentTarget));
    const appt = d.appointment_at
      ? new Date(String(d.appointment_at)).toISOString()
      : null;
    const r = await ctx.act(
      () =>
        api(`/leads/${lead.id}/transition`, {
          stage,
          reason: d.reason || "",
          verified: d.verified === "on",
          value: d.value ? +d.value : 0,
          appointment_at: appt,
        }),
      "Pipeline updated",
    );
    if (r) close();
  }
  return (
    <Modal title="Move opportunity" close={close}>
      <form onSubmit={submit}>
        <p className="modal-intro">
          {lead.name} · currently {label(lead.stage)}. Customer reply evidence
          is required before progression.
        </p>
        <Field label="Next stage">
          <select value={stage} onChange={(e) => S(e.target.value)}>
            {(nextStages[lead.stage] || []).map((s) => (
              <option key={s} value={s}>
                {label(s)}
              </option>
            ))}
          </select>
        </Field>
        {stage === "appointment" && (
          <Field
            label="Appointment (your local time)"
            type="datetime-local"
            name="appointment_at"
            required
            defaultValue={new Date(Date.now() + 86400000)
              .toISOString()
              .slice(0, 16)}
          />
        )}{" "}
        {stage === "won" && (
          <>
            <Field
              label="Verified deal value (PKR)"
              name="value"
              type="number"
              min={1}
              required
              defaultValue={lead.budget || 65000}
            />
            <label className="check-field">
              <input type="checkbox" name="verified" required />I verified this
              simulated outcome.
            </label>
          </>
        )}
        <Field
          label="Reason / context"
          name="reason"
          required={["lost", "dormant", "archived", "reopened"].includes(stage)}
          minLength={3}
        />
        <div className="modal-actions">
          <Button onClick={close}>Cancel</Button>
          <Button type="submit" kind="primary" disabled={ctx.busy || !stage}>
            Confirm stage
          </Button>
        </div>
      </form>
    </Modal>
  );
}
function OverrideModal({ ctx, lead, close }: any) {
  return (
    <Modal title="Override assignment" close={close}>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          const d = Object.fromEntries(new FormData(e.currentTarget));
          if (
            await ctx.act(
              () => api(`/leads/${lead.id}/override`, d),
              "Assignment override recorded with audit trail",
            )
          )
            close();
        }}
      >
        <p className="modal-intro">
          Your reason, previous owner, and new owner are recorded. Availability
          and capacity are rechecked by the server.
        </p>
        <Field label="Assign to">
          <select name="rep_id" required>
            <option value="">Choose an adviser</option>
            {ctx.team
              .filter((r: Row) => r.id !== lead.owner_id)
              .map((r: Row) => (
                <option
                  key={r.id}
                  value={r.id}
                  disabled={!r.active || r.load >= r.capacity}
                >
                  {r.name} · {r.load}/{r.capacity}
                  {!r.active ? " · unavailable" : ""}
                </option>
              ))}
          </select>
        </Field>
        <Field
          label="Manager's reason"
          name="reason"
          required
          minLength={3}
          placeholder="Adviser has prior context for this inquiry"
        />
        <div className="modal-actions">
          <Button type="submit" kind="primary" disabled={ctx.busy}>
            Approve override
          </Button>
        </div>
      </form>
    </Modal>
  );
}
function TraceEvidence({ row }: any) {
  return (
    <div className="trace-evidence">
      <div className="trace-parts">
        <div>
          <small>INPUT SNAPSHOT</small>
          <dl>
            {Object.entries(row.inputs || {}).map(([k, v]) => (
              <div key={k}>
                <dt>{label(k)}</dt>
                <dd>{v === null ? "Unknown" : String(v)}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div>
          <small>DECISION FACTORS</small>
          <dl>
            {Object.entries(row.explanation || {}).map(([k, v]) => (
              <div key={k}>
                <dt>{label(k)}</dt>
                <dd>
                  {v === null
                    ? "Unknown"
                    : typeof v === "object"
                      ? Object.entries(v as any)
                          .map(([key, val]) => `${label(key)}: ${val}`)
                          .join(" · ")
                      : String(v)}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
      {row.alternatives?.length > 0 && (
        <div className="table-wrap">
          <table className="alternatives">
            <thead>
              <tr>
                <th>Alternative</th>
                <th>Utility</th>
                <th>Load / cap</th>
                <th>Assessment</th>
              </tr>
            </thead>
            <tbody>
              {row.alternatives.map((a: Row) => (
                <tr key={a.rep_id}>
                  <td>{a.name}</td>
                  <td>{a.utility}</td>
                  <td>
                    {a.load}/{a.capacity}
                  </td>
                  <td>{a.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
function Assignments({ ctx }: any) {
  const [preview, P] = useState<Row | null>(null),
    [edit, E] = useState<Row | null>(null);
  return (
    <div className="page-stack">
      <div className="info-strip">
        <Scale size={23} />
        <div>
          <b>Cooperative allocation, with human control.</b>
          <p>
            Capacity and on-duty availability are hard constraints. Fairness
            keeps load ratios within 0.25 when feasible. Preview compares the
            same inquiries with lowest-load greedy assignment.
          </p>
        </div>
      </div>
      <div className="team-grid">
        {ctx.team.map((r: Row) => (
          <Panel
            key={r.id}
            title={r.name}
            caption={
              r.active
                ? "Available during configured shift"
                : "Marked unavailable"
            }
            action={<span className="avatar colored">{initials(r.name)}</span>}
          >
            <div className="rep-body">
              <div className="row wrap">
                {r.skills.map((s: string) => (
                  <Badge key={s} tone="blue">
                    {s}
                  </Badge>
                ))}
              </div>
              <div className="rep-stat">
                <strong>
                  {r.load}
                  <small> / {r.capacity}</small>
                </strong>
                <span>Today's active assignments</span>
              </div>
              <div className="progress">
                <i
                  style={{
                    width: `${Math.min(100, (r.load / r.capacity) * 100)}%`,
                  }}
                />
              </div>
              <p className="small">
                {r.open} open in cohort · Shift {r.shift_start}:00–{r.shift_end}
                :00 PKT
              </p>
              {ctx.canManage && (
                <Button onClick={() => E(r)}>
                  <Settings size={14} />
                  Adjust availability
                </Button>
              )}
            </div>
          </Panel>
        ))}
      </div>
      <Panel
        title="Assignment optimizer"
        caption="Preview up to 100 unassigned inquiries; the server recomputes on commit."
        action={
          ctx.canManage && (
            <Button
              kind="primary"
              disabled={ctx.busy}
              onClick={async () => {
                const r = await ctx.act(
                  () => api("/assignments/preview", { lead_ids: [] }),
                  "Assignment preview generated",
                );
                if (r) P(r);
              }}
            >
              <Sparkles size={15} />
              Preview assignment
            </Button>
          )
        }
      >
        {preview ? (
          <div className="panel-padding">
            <div className="comparison-grid">
              <div>
                <small>GREEDY BASELINE UTILITY</small>
                <strong>{preview.baseline_utility}</strong>
              </div>
              <div>
                <small>OPTIMIZED UTILITY</small>
                <strong>{preview.optimized_utility}</strong>
              </div>
              <div>
                <small>PROPOSED / UNASSIGNED</small>
                <strong>
                  {preview.assignments.length} / {preview.unassigned || 0}
                </strong>
              </div>
            </div>
            <p>{preview.formula}</p>
            <div className="info-strip">{preview.explanation}</div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Lead</th>
                    <th>Proposed owner</th>
                    <th>Utility</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.assignments.map((a: Row) => (
                    <tr key={a.lead_id}>
                      <td>
                        <button
                          className="text-btn"
                          onClick={() => ctx.open(a.lead_id)}
                        >
                          {a.lead_name}
                        </button>
                      </td>
                      <td>{a.rep_name}</td>
                      <td>{a.utility}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {ctx.canManage && (
              <Button
                kind="primary"
                disabled={ctx.busy || !preview.assignments.length}
                onClick={async () => {
                  const r = await ctx.act(
                    () =>
                      api("/assignments/commit", {
                        lead_ids: preview.assignments.map(
                          (a: Row) => a.lead_id,
                        ),
                      }),
                    "Assignments confirmed",
                  );
                  if (r) P(null);
                }}
              >
                <Check size={16} />
                Confirm recommended allocation
              </Button>
            )}
          </div>
        ) : (
          <Empty
            title="Ready to balance the workload"
            text="Preview unassigned inquiries against specialization, capacity, response expectations, and fairness."
          />
        )}
      </Panel>
      {edit && <RepModal ctx={ctx} rep={edit} close={() => E(null)} />}
    </div>
  );
}
function RepModal({ ctx, rep, close }: any) {
  return (
    <Modal title={"Availability · " + rep.name} close={close}>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          const d = Object.fromEntries(new FormData(e.currentTarget));
          if (
            await ctx.act(
              () =>
                api(
                  "/team/" + rep.id,
                  {
                    capacity: +d.capacity,
                    active: d.active === "on",
                    shift_start: +d.shift_start,
                    shift_end: +d.shift_end,
                    skills: String(d.skills)
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean),
                  },
                  "PATCH",
                ),
              "Adviser configuration saved",
            )
          )
            close();
        }}
      >
        <Field
          label="Daily capacity"
          type="number"
          name="capacity"
          min={1}
          max={200}
          required
          defaultValue={rep.capacity}
        />
        <div className="form-grid">
          <Field
            label="Shift start (PKT hour)"
            name="shift_start"
            type="number"
            min={0}
            max={23}
            required
            defaultValue={rep.shift_start}
          />
          <Field
            label="Shift end (PKT hour)"
            name="shift_end"
            type="number"
            min={1}
            max={24}
            required
            defaultValue={rep.shift_end}
          />
        </div>
        <Field
          label="Specializations (comma separated)"
          name="skills"
          required
          defaultValue={rep.skills.join(", ")}
        />
        <label className="check-field">
          <input type="checkbox" name="active" defaultChecked={rep.active} />
          Available for new assignments
        </label>
        <div className="modal-actions">
          <Button type="submit" kind="primary" disabled={ctx.busy}>
            Save availability
          </Button>
        </div>
      </form>
    </Modal>
  );
}
function Pipeline({ ctx }: any) {
  const [columns, C] = useState<Row>({}),
    [moving, M] = useState<Row | null>(null),
    [loading, B] = useState(true);
  const [pages, PG] = useState<Record<string, number>>({});
  useEffect(() => {
    B(true);
    Promise.all(
      stages.map(async (s) => [
        s,
        await api(
          "/leads?stage=" + s + "&page_size=12&page=" + (pages[s] || 1),
        ),
      ]),
    )
      .then((v) => C(Object.fromEntries(v)))
      .catch((e) => ctx.notify(e.message, "error"))
      .finally(() => B(false));
  }, [ctx.revision, pages]);
  return (
    <div className="page-stack">
      <div className="info-strip">
        <Columns3 size={21} />
        <p>
          Drag a card into its next stage, or open it to log a reply, book an
          appointment, and verify a win. Invalid transitions are rejected and
          explained.
        </p>
      </div>
      {loading && (
        <div role="status" className="loading-line">
          Refreshing pipeline…
        </div>
      )}
      <div className="kanban">
        {stages.map((s, i) => (
          <section
            className="kanban-column"
            key={s}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              try {
                const l = JSON.parse(e.dataTransfer.getData("text/plain"));
                if (!nextStages[l.stage]?.includes(s)) {
                  ctx.notify(
                    `Move ${label(l.stage)} through its next valid stage first.`,
                    "error",
                  );
                  return;
                }
                M({ ...l, target: s });
              } catch {
                ctx.notify("Open the card to move this lead", "error");
              }
            }}
          >
            <div className="column-head">
              <span className={"column-dot dot-" + i} />
              <b>{label(s)}</b>
              <Badge tone="gray">{columns[s]?.total || 0}</Badge>
            </div>
            <div className="kanban-cards">
              {columns[s]?.items.map((l: Row) => (
                <article
                  className="kanban-card"
                  key={l.id}
                  draggable={ctx.canEdit}
                  onDragStart={(e) =>
                    e.dataTransfer.setData("text/plain", JSON.stringify(l))
                  }
                >
                  <div className="between">
                    <span className="source-tag">{l.source}</span>
                    <Score value={l.score} />
                  </div>
                  <button className="card-title" onClick={() => ctx.open(l.id)}>
                    {l.name}
                  </button>
                  <p>{l.interest}</p>
                  <b>
                    {l.deal_value
                      ? money(l.deal_value)
                      : l.budget
                        ? money(l.budget)
                        : "Budget unknown"}
                  </b>
                  <div className="card-bottom">
                    <span className="avatar small-avatar">
                      {initials(
                        ctx.team.find((r: Row) => r.id === l.owner_id)?.name ||
                          "?",
                      )}
                    </span>
                    <small>{date(l.created_at)}</small>
                    <button
                      className="icon"
                      aria-label={"Open " + l.name}
                      onClick={() => ctx.open(l.id)}
                    >
                      <ArrowUpRight size={14} />
                    </button>
                  </div>
                </article>
              ))}
            </div>
            {!columns[s]?.total && (
              <p className="column-empty">No opportunities in this stage</p>
            )}
            {columns[s]?.total > 12 && (
              <div className="column-pagination">
                <button
                  className="icon"
                  aria-label={"Previous " + s + " page"}
                  disabled={(pages[s] || 1) === 1}
                  onClick={() => PG({ ...pages, [s]: (pages[s] || 1) - 1 })}
                >
                  <ArrowLeft size={15} />
                </button>
                <small>Page {pages[s] || 1}</small>
                <button
                  className="icon"
                  aria-label={"Next " + s + " page"}
                  disabled={(pages[s] || 1) * 12 >= columns[s].total}
                  onClick={() => PG({ ...pages, [s]: (pages[s] || 1) + 1 })}
                >
                  <ArrowRight size={15} />
                </button>
              </div>
            )}
          </section>
        ))}
      </div>
      {moving && (
        <MoveModal
          ctx={ctx}
          lead={moving}
          target={moving.target}
          close={() => M(null)}
        />
      )}
    </div>
  );
}
function Followups({ ctx }: any) {
  const [tasks, T] = useState<Row[]>([]),
    [jobs, J] = useState<Row[]>([]),
    [filter, F] = useState("all"),
    [page, P] = useState(1),
    [selected, S] = useState<Row | null>(null);
  useEffect(() => {
    Promise.all([api("/tasks"), api("/jobs")])
      .then(([t, j]) => {
        T(t);
        J(j);
      })
      .catch((e) => ctx.notify(e.message, "error"));
  }, [ctx.revision]);
  const filtered = tasks.filter(
      (t) =>
        filter === "all" || (filter === "overdue" ? t.overdue : !t.overdue),
    ),
    visible = filtered.slice((page - 1) * 15, page * 15);
  return (
    <div className="page-stack">
      <div className="kpis three">
        <KPI
          title="Pending actions"
          value={num(tasks.length)}
          detail="Persisted tasks requiring attention"
          icon={Clock3}
        />
        <KPI
          title="Missed deadlines"
          value={num(tasks.filter((t) => t.overdue).length)}
          detail="Compared with the virtual clock"
          icon={Timer}
          tone="amber"
        />
        <KPI
          title="Queued / retrying"
          value={
            jobs.filter((j) => ["queued", "retry"].includes(j.status)).length
          }
          detail="Approved, awaiting simulation worker tick"
          icon={Send}
          tone="purple"
        />
      </div>
      <Panel
        title="Follow-up center"
        caption="Review the template before approving a simulated send."
        action={
          ctx.canManage && (
            <Button
              kind="primary"
              disabled={ctx.busy}
              onClick={() =>
                ctx.act(
                  () => api("/jobs/process", {}),
                  "Simulation queue processed",
                )
              }
            >
              <Play size={15} />
              Process message queue
            </Button>
          )
        }
      >
        <div className="tabs padded">
          {["all", "overdue", "upcoming"].map((x) => (
            <button
              key={x}
              className={x === filter ? "active" : ""}
              onClick={() => {
                F(x);
                P(1);
              }}
            >
              {label(x)}
            </button>
          ))}
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Lead</th>
                <th>Next action</th>
                <th>Due · PKT</th>
                <th>Consent</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((t: Row) => (
                <tr key={t.id}>
                  <td>
                    <button
                      className="lead-cell"
                      onClick={() => ctx.open(t.lead_id)}
                    >
                      <span>
                        <strong>{t.lead_name}</strong>
                        <small>{t.interest}</small>
                      </span>
                    </button>
                  </td>
                  <td>
                    {label(t.kind)}{" "}
                    {t.overdue && <Badge tone="amber">Overdue</Badge>}
                  </td>
                  <td>{date(t.due_at, true)}</td>
                  <td>
                    <Badge tone={t.consent === "granted" ? "green" : "gray"}>
                      {label(t.consent)}
                    </Badge>
                  </td>
                  <td>
                    {ctx.canEdit && (
                      <div className="row">
                        <Button onClick={() => S(t)}>
                          <Send size={14} />
                          Review send
                        </Button>
                        <Button
                          onClick={() =>
                            ctx.act(
                              () =>
                                api("/tasks/" + t.id + "/action", {
                                  action: "snooze",
                                  minutes: 60,
                                }),
                              "Snoozed for 60 simulated minutes",
                            )
                          }
                          disabled={ctx.busy}
                        >
                          Snooze
                        </Button>
                        <Button
                          aria-label="Complete follow-up"
                          onClick={() =>
                            ctx.act(
                              () =>
                                api("/tasks/" + t.id + "/action", {
                                  action: "complete",
                                }),
                              "Task marked complete",
                            )
                          }
                          disabled={ctx.busy}
                        >
                          <Check size={14} />
                        </Button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!filtered.length && (
          <Empty
            title="You're all caught up"
            text="There are no pending tasks in this view."
          />
        )}
        <div className="pagination">
          <span>{num(filtered.length)} tasks</span>
          <div>
            <Button disabled={page === 1} onClick={() => P(page - 1)}>
              Previous
            </Button>
            <span>{page}</span>
            <Button
              disabled={page * 15 >= filtered.length}
              onClick={() => P(page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      </Panel>
      <Panel
        title="Persistent message queue"
        caption="Every job has a correlation ID, lease, retry count, and last error."
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Job</th>
                <th>Status</th>
                <th>Retries</th>
                <th>Next attempt · PKT</th>
                <th>Last error</th>
              </tr>
            </thead>
            <tbody>
              {jobs
                .slice(-20)
                .reverse()
                .map((j) => (
                  <tr key={j.id}>
                    <td>
                      <code>{j.id.slice(0, 8)}</code>
                    </td>
                    <td>
                      <Badge
                        tone={j.status === "completed" ? "green" : "amber"}
                      >
                        {label(j.status)}
                      </Badge>
                    </td>
                    <td>{j.retry_count}</td>
                    <td>{date(j.due_at, true)}</td>
                    <td>{j.last_error || "—"}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        {!jobs.length && (
          <Empty
            title="No queued messages"
            text="Approve a task template above to create a durable simulated job."
          />
        )}
      </Panel>
      {selected && (
        <Modal title="Review simulated follow-up" close={() => S(null)}>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              const body = new FormData(e.currentTarget).get("body");
              if (
                await ctx.act(
                  () =>
                    api("/tasks/" + selected.id + "/action", {
                      action: "send",
                      body,
                    }),
                  "Approved; process queue to deliver",
                )
              )
                S(null);
            }}
          >
            <p className="modal-intro">
              For {selected.lead_name}. Consent is checked again at delivery.
              Unknown consent, opt-outs, and closed leads suppress the message.
            </p>
            <Field label="Template preview">
              <textarea
                name="body"
                rows={5}
                required
                defaultValue="Simulated: Assalam-o-Alaikum! Thank you for your inquiry. May we help you choose the right option and arrange a consultation?"
              />
            </Field>
            <div className="modal-actions">
              <Button type="submit" kind="primary" disabled={ctx.busy}>
                <ShieldCheck size={16} />
                Approve simulated send
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
function Recovery({ ctx }: any) {
  const [rows, R] = useState<Row[]>([]),
    [filter, F] = useState("recommended"),
    [selected, S] = useState<Row | null>(null),
    [override, O] = useState<Row | null>(null);
  useEffect(() => {
    api("/recommendations?agent=Recovery")
      .then(R)
      .catch((e: any) => ctx.notify(e.message, "error"));
  }, [ctx.revision]);
  const filtered = rows.filter((r) => !filter || r.status === filter);
  return (
    <div className="page-stack">
      <div className="intake-banner recovery-banner">
        <div>
          <Badge tone="amber">THE LEAD RECOVERY LEDGER</Badge>
          <h2>Missed doesn't have to mean lost.</h2>
          <p>
            A visible deadline, an accountable owner, and a manager-approved
            next step. Recovery never rewrites the original SLA miss.
          </p>
        </div>
        {ctx.canManage && (
          <Button
            kind="primary"
            disabled={ctx.busy}
            onClick={() =>
              ctx.act(
                () => api("/recovery/scan", {}),
                "Recovery scan completed",
              )
            }
          >
            <LifeBuoy size={16} />
            Scan missed deadlines
          </Button>
        )}
      </div>
      <Panel
        title="Recovery recommendations"
        caption="Explicit approvals and overrides remain in the audit trail."
        action={
          <select
            aria-label="Recovery status"
            value={filter}
            onChange={(e) => F(e.target.value)}
          >
            <option value="recommended">Needs review</option>
            <option value="approved">Approved</option>
            <option value="dismissed">Dismissed</option>
            <option value="">All recommendations</option>
          </select>
        }
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Opportunity</th>
                <th>Deadline · PKT</th>
                <th>Reason</th>
                <th>State</th>
                <th>Next action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id}>
                  <td>
                    <button
                      className="text-btn"
                      onClick={() => ctx.open(r.lead_id)}
                    >
                      Open lead <ArrowUpRight size={14} />
                    </button>
                    <small className="block muted">
                      {r.lead_id.slice(0, 8)}
                    </small>
                  </td>
                  <td>{date(r.inputs.deadline, true)}</td>
                  <td>
                    {r.explanation.reason}
                    <small className="block muted">
                      {r.explanation.minutes_overdue} min overdue at detection
                    </small>
                  </td>
                  <td>
                    <Badge
                      tone={r.status === "recommended" ? "amber" : "green"}
                    >
                      {label(r.status)}
                    </Badge>
                  </td>
                  <td>
                    {ctx.canManage && r.status === "recommended" && (
                      <div className="row">
                        <Button
                          onClick={async () => {
                            try {
                              const d = await api("/leads/" + r.lead_id);
                              O(d.lead);
                            } catch (e: any) {
                              ctx.notify(e.message, "error");
                            }
                          }}
                        >
                          Reassign
                        </Button>
                        <Button onClick={() => S(r)}>Review</Button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!filtered.length && (
          <Empty
            title="No recommendations in this view"
            text="Run a recovery scan or advance the clock in Demo Lab to detect pending missed deadlines."
          />
        )}
      </Panel>
      {selected && (
        <Modal title="Review recovery recommendation" close={() => S(null)}>
          <TraceEvidence row={selected} />
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              const d = Object.fromEntries(new FormData(e.currentTarget));
              if (
                await ctx.act(
                  () => api("/recommendations/" + selected.id + "/decision", d),
                  "Recovery decision recorded",
                )
              )
                S(null);
            }}
          >
            <Field label="Decision">
              <select name="action">
                <option value="approve">Approve manager review</option>
                <option value="dismiss">Dismiss with reason</option>
              </select>
            </Field>
            <Field label="Reason" name="reason" minLength={3} required />
            <div className="modal-actions">
              <Button type="submit" kind="primary" disabled={ctx.busy}>
                Save decision
              </Button>
            </div>
          </form>
        </Modal>
      )}
      {override && (
        <OverrideModal ctx={ctx} lead={override} close={() => O(null)} />
      )}
    </div>
  );
}
function Analytics({ ctx }: any) {
  const m = ctx.metrics;
  const [lift, L] = useState(5),
    [margin, M] = useState(4000),
    [fee, F] = useState(5999);
  return (
    <div className="page-stack">
      <div className="kpis">
        <KPI
          title="Cohort conversion"
          value={m.conversion + "%"}
          detail={`${m.won} wins / ${num(m.total)} inquiries`}
          icon={Target}
        />
        <KPI
          title="First-response SLA"
          value={m.sla_met + "%"}
          detail={`${num(m.sla_denominator)} staff-replied or expired-SLA inquiries`}
          icon={Timer}
          tone="green"
        />
        <KPI
          title="Mean staff response"
          value={m.mean_response + " min"}
          detail={`${num(m.responded)} replies · simulated`}
          icon={MessageSquare}
          tone="purple"
        />
        <KPI
          title="Opt-outs"
          value={num(m.opt_outs)}
          detail="Outreach suppressed after refusal"
          icon={ShieldCheck}
          tone="amber"
        />
      </div>
      <div className="chart-row">
        <Panel
          title="The journey to a verified win"
          caption="Distinct leads with recorded progression in selected captured cohort"
        >
          <div className="funnel">
            {m.funnel.map((f: Row, i: number) => (
              <div key={f.stage}>
                <span>{label(f.stage)}</span>
                <div>
                  <i
                    style={{
                      width: `${Math.max(2, (f.count / Math.max(m.total, 1)) * 100)}%`,
                      background: [
                        "#3c51d4",
                        "#6575e2",
                        "#8b95eb",
                        "#5ebcae",
                        "#28a185",
                      ][i],
                    }}
                  />
                </div>
                <strong>{num(f.count)}</strong>
                <small>
                  {Math.round((f.count / Math.max(m.total, 1)) * 100)}%
                </small>
              </div>
            ))}
          </div>
          <p className="chart-footnote">{m.denominator_note}</p>
        </Panel>
        <Panel
          title="Source to outcome"
          caption="Synthetic wins compared with captured source cohorts"
        >
          <div className="chart">
            <ResponsiveContainer width="100%" height={270}>
              <BarChart
                data={m.sources}
                margin={{ left: -20, right: 16, top: 15 }}
              >
                <CartesianGrid strokeDasharray="3 5" vertical={false} />
                <XAxis
                  dataKey="source"
                  tick={{ fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 11 }} />
                <Bar
                  dataKey="leads"
                  name="Captured"
                  fill="#9ca7ed"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="won"
                  name="Verified wins"
                  fill="#2ba78e"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
      <Panel
        title="Team performance & workload"
        caption="Synthetic outcomes do not assess real employees."
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Adviser</th>
                <th>Today / capacity</th>
                <th>Open in cohort</th>
                <th>Wins</th>
                <th>Won / captured</th>
                <th>Synthetic won value</th>
              </tr>
            </thead>
            <tbody>
              {m.team.map((r: Row) => (
                <tr key={r.id}>
                  <td>
                    <div className="row">
                      <span className="avatar colored">{initials(r.name)}</span>
                      <b>{r.name}</b>
                    </div>
                  </td>
                  <td>
                    {r.load} / {r.capacity}
                  </td>
                  <td>{r.open}</td>
                  <td>{r.won}</td>
                  <td>{r.conversion}%</td>
                  <td>{money(r.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
      <Panel
        title="What could better follow-through be worth?"
        caption="Hypothetical planning calculator · not observed ROI or a causal claim"
      >
        <div className="roi">
          <div className="roi-inputs">
            <Field label={`Assumed additional conversion: ${lift}%`}>
              <input
                type="range"
                min={0}
                max={20}
                value={lift}
                onChange={(e) => L(+e.target.value)}
              />
            </Field>
            <div className="form-grid">
              <Field
                label="Contribution per sale (PKR)"
                type="number"
                min={0}
                value={margin}
                onChange={(e: any) => M(Math.max(0, +e.target.value))}
              />
              <Field
                label="Assumed software fee (PKR)"
                type="number"
                min={0}
                value={fee}
                onChange={(e: any) => F(Math.max(0, +e.target.value))}
              />
            </div>
            <p>
              {num(m.total)} inquiries × {lift}% assumed additional wins ×{" "}
              {money(margin)} contribution − {money(fee)} fee. Excludes labor,
              setup, and message charges.
            </p>
          </div>
          <div className="roi-result">
            <Badge tone="blue">HYPOTHETICAL ESTIMATE</Badge>
            <strong>{money(m.total * (lift / 100) * margin - fee)}</strong>
            <p>Potential cohort contribution after assumed fee</p>
            <small>
              Validate with matched or randomized real pilot cohorts before
              claiming a benefit.
            </small>
          </div>
        </div>
      </Panel>
    </div>
  );
}
function Traces({ ctx }: any) {
  const [rows, R] = useState<Row[]>([]),
    [agent, A] = useState(""),
    [selected, S] = useState<Row | null>(null);
  useEffect(() => {
    api("/recommendations?agent=" + agent)
      .then(R)
      .catch((e: any) => ctx.notify(e.message, "error"));
  }, [agent, ctx.revision]);
  return (
    <div className="page-stack">
      <div className="agent-grid">
        {[
          "Capture",
          "Qualification",
          "Allocation",
          "Follow-up",
          "Recovery",
          "Analytics",
        ].map((a, i) => (
          <button
            className={"agent-card " + (a === agent ? "selected" : "")}
            key={a}
            onClick={() => A(a === agent ? "" : a)}
          >
            <span className="agent-number">0{i + 1}</span>
            <Workflow size={20} />
            <b>{a}</b>
            <small>
              {
                [
                  "Validate & deduplicate",
                  "Score with evidence",
                  "Optimize & explain",
                  "Schedule & suppress",
                  "Detect & escalate",
                  "Reconcile outcomes",
                ][i]
              }
            </small>
          </button>
        ))}
      </div>
      <Panel
        title="Agent decision journal"
        caption="Versioned inputs, selected actions, factors, and rejected alternatives."
        action={
          <select
            value={agent}
            aria-label="Filter by agent"
            onChange={(e) => A(e.target.value)}
          >
            <option value="">All six agents</option>
            {[
              "Capture",
              "Qualification",
              "Allocation",
              "Follow-up",
              "Recovery",
              "Analytics",
            ].map((a) => (
              <option key={a}>{a}</option>
            ))}
          </select>
        }
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Agent</th>
                <th>Selected action</th>
                <th>Policy</th>
                <th>Status</th>
                <th>Time · PKT</th>
                <th>
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div className="row">
                      <span className="agent-mini">
                        <Workflow size={15} />
                      </span>
                      <b>{r.agent}</b>
                    </div>
                  </td>
                  <td>{r.action}</td>
                  <td>
                    <code>{r.policy_version}</code>
                  </td>
                  <td>
                    <Badge tone="blue">{label(r.status)}</Badge>
                  </td>
                  <td>{date(r.created_at, true)}</td>
                  <td>
                    <Button onClick={() => S(r)}>
                      Inspect <ArrowUpRight size={14} />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!rows.length && (
          <Empty
            title="No decisions in this view"
            text="Create an inquiry or run a Demo Lab scenario to generate a trace."
          />
        )}
      </Panel>
      {selected && (
        <Modal
          title={`${selected.agent} · Decision evidence`}
          close={() => S(null)}
          wide
        >
          <TraceEvidence row={selected} />
          <div className="modal-actions">
            <Button
              onClick={() => {
                ctx.open(selected.lead_id);
                S(null);
              }}
            >
              Open related lead
              <ArrowRight size={14} />
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
const scenarios = [
  [
    "inquiry",
    "A new inquiry arrives",
    "Capture, score, assign, and schedule a next step.",
    "01",
    Inbox,
  ],
  [
    "high_value",
    "A high-value opportunity",
    "See urgency and budget evidence affect priority.",
    "02",
    Flame,
  ],
  [
    "sla",
    "The missed admission",
    "Advance four hours and expose a missed deadline.",
    "03",
    Timer,
  ],
  [
    "capacity",
    "Capacity under pressure",
    "Respect daily limits and surface unassigned work.",
    "04",
    Scale,
  ],
  [
    "appointment",
    "From reply to appointment",
    "Send, receive a reply, qualify, and book.",
    "05",
    Calendar,
  ],
  [
    "override",
    "The manager has context",
    "Override an allocation with a recorded reason.",
    "06",
    GitBranch,
  ],
  [
    "conversion",
    "A verified conversion",
    "Close a simulated deal and reconcile analytics.",
    "07",
    Target,
  ],
  [
    "burst",
    "20 inquiries, one fair plan",
    "Compare optimized matching with a greedy baseline.",
    "08",
    Users,
  ],
  [
    "opt_out",
    "Consent comes first",
    "Observe an opted-out message being suppressed.",
    "09",
    ShieldCheck,
  ],
  [
    "retry",
    "A connector times out",
    "Watch a durable job retry after a two-minute backoff.",
    "10",
    RefreshCw,
  ],
] as const;
function DemoLab({ ctx }: any) {
  const [result, R] = useState<Row | null>(null),
    [running, S] = useState(""),
    [reset, X] = useState(false),
    [minutes, M] = useState(31);
  async function run(key: string) {
    S(key);
    const r = await ctx.act(
      () => api(`/demo/scenarios/${key}/run`, {}),
      "Scenario executed; persisted state updated",
    );
    if (r) R(r);
    S("");
  }
  return (
    <div className="page-stack">
      <section className="lab-hero">
        <div>
          <Badge tone="glass">
            <FlaskConical size={13} /> THE INTERACTIVE PLAYGROUND
          </Badge>
          <h2>
            A whole sales day.
            <br />
            In a few clicks.
          </h2>
          <p>
            Meet your next lead. Let the agents cooperate. Inspect every
            decision.
          </p>
        </div>
        <div className="lab-clock">
          <span>YOUR VIRTUAL CLOCK · PKT</span>
          <strong>{date(ctx.metrics.clock, true)}</strong>
          {ctx.canManage && (
            <>
              <div className="row">
                <select
                  value={minutes}
                  aria-label="Advance time by"
                  onChange={(e) => M(+e.target.value)}
                >
                  <option value={2}>2 minutes</option>
                  <option value={31}>31 minutes</option>
                  <option value={60}>1 hour</option>
                  <option value={240}>4 hours</option>
                  <option value={1440}>1 day</option>
                </select>
                <Button
                  kind="white"
                  disabled={ctx.busy}
                  onClick={() =>
                    ctx.act(
                      () => api("/demo/clock/advance", { minutes }),
                      "Virtual clock advanced; recovery and jobs processed",
                    )
                  }
                >
                  <Clock3 size={15} />
                  Advance
                </Button>
              </div>
              <small>
                Advancing time detects SLA misses and processes approved jobs.
              </small>
            </>
          )}
        </div>
      </section>
      {!ctx.canManage && (
        <div className="info-strip">
          Only managers and owners can execute scenarios. Inspect their outcomes
          in the other workspaces.
        </div>
      )}
      <div className="scenario-grid">
        {scenarios.map(([key, title, desc, number, Icon]) => (
          <button
            key={key}
            className={"scenario-card " + (running === key ? "running" : "")}
            disabled={ctx.busy || !ctx.canManage}
            onClick={() => run(key)}
          >
            <div className="between">
              <span className="scenario-icon">
                <Icon size={22} />
              </span>
              <span className="scenario-number">SCENARIO {number}</span>
            </div>
            <h3>{title}</h3>
            <p>{desc}</p>
            <span className="scenario-run">
              {running === key ? "Executing scenario…" : "Run scenario"}
              <ArrowRight size={15} />
            </span>
          </button>
        ))}
      </div>
      {result && (
        <Panel
          title={"Scenario result · " + label(result.scenario)}
          caption="Before and after are persisted simulation states, not proven business improvements."
          action={<Badge tone="green">Executed & audited</Badge>}
        >
          <div className="result-table">
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Before</th>
                  <th>After</th>
                </tr>
              </thead>
              <tbody>
                {Object.keys(result.before).map((k) => (
                  <tr key={k}>
                    <td>{label(k)}</td>
                    <td>
                      {k === "revenue"
                        ? money(result.before[k])
                        : num(result.before[k])}
                    </td>
                    <td>
                      {k === "revenue"
                        ? money(result.after[k])
                        : num(result.after[k])}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {result.comparison && (
            <div className="panel-padding">
              <div className="comparison-grid">
                <div>
                  <small>GREEDY UTILITY</small>
                  <strong>{result.comparison.baseline_utility}</strong>
                </div>
                <div>
                  <small>OPTIMIZED UTILITY</small>
                  <strong>{result.comparison.optimized_utility}</strong>
                </div>
                <div>
                  <small>UNASSIGNED</small>
                  <strong>{result.comparison.unassigned}</strong>
                </div>
              </div>
              <p>{result.comparison.explanation}</p>
              <p className="small">
                Identical batch and initial workload. Utility measures policy
                fit, not conversion lift.
              </p>
            </div>
          )}
          <div className="panel-padding row wrap">
            {result.lead_ids.slice(0, 6).map((id: string, i: number) => (
              <Button key={id} onClick={() => ctx.open(id)}>
                Inspect lead {i + 1}
                <ArrowUpRight size={14} />
              </Button>
            ))}
          </div>
        </Panel>
      )}
      <div className="insight-note">
        <RefreshCw size={22} />
        <div>
          <b>Make the next presentation a fresh start.</b>
          <p>
            Reset only your business to the reproducible LP-1 fixture. The other
            tenant is preserved.
          </p>
        </div>
        {ctx.user.role === "owner" && (
          <Button kind="danger" onClick={() => X(true)}>
            Reset demo
          </Button>
        )}
      </div>
      {reset && (
        <Modal title="Reset synthetic demo data?" close={() => X(false)}>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              const confirmation = new FormData(e.currentTarget).get(
                "confirmation",
              );
              if (
                await ctx.act(
                  () => api("/demo/reset", { confirmation }),
                  "Tenant demo reset to LP-1 seed",
                )
              ) {
                X(false);
                R(null);
              }
            }}
          >
            <p>
              This removes your tenant's demo changes, messages, jobs, and
              scenarios. Accounts and sessions remain available.
            </p>
            <Field
              label="Type RESET SYNTHETIC DATA"
              name="confirmation"
              required
              pattern="RESET SYNTHETIC DATA"
              autoComplete="off"
            />
            <div className="modal-actions">
              <Button onClick={() => X(false)}>Cancel</Button>
              <Button type="submit" kind="danger" disabled={ctx.busy}>
                Reset this business
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
function Admin({ ctx }: any) {
  const [tab, T] = useState("Team"),
    [settings, S] = useState<Row | null>(null),
    [members, M] = useState<Row[]>([]),
    [audits, A] = useState<Row[]>([]),
    [edit, E] = useState<Row | null>(null);
  useEffect(() => {
    api("/settings")
      .then(S)
      .catch((e: any) => ctx.notify(e.message, "error"));
    if (ctx.canManage)
      api("/members")
        .then(M)
        .catch((e: any) => ctx.notify(e.message, "error"));
    if (ctx.user.role !== "operator")
      api("/audit")
        .then(A)
        .catch((e: any) => ctx.notify(e.message, "error"));
  }, [ctx.revision]);
  return (
    <div className="page-stack">
      <div className="tabs page-tabs">
        {["Team", "Workspace settings", "Audit trail", "About the simulation"]
          .filter((x) => x !== "Audit trail" || ctx.user.role !== "operator")
          .map((x) => (
            <button
              key={x}
              className={x === tab ? "active" : ""}
              onClick={() => T(x)}
            >
              {x}
            </button>
          ))}
      </div>
      {tab === "Team" && (
        <>
          <Panel
            title="Your sales team"
            caption="Adjust capacity, availability, hours, and specializations."
          >
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Adviser</th>
                    <th>Specializations</th>
                    <th>Today / capacity</th>
                    <th>Availability</th>
                    <th>
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {ctx.team.map((r: Row) => (
                    <tr key={r.id}>
                      <td>
                        <b>{r.name}</b>
                      </td>
                      <td>{r.skills.join(", ")}</td>
                      <td>
                        {r.load} / {r.capacity}
                      </td>
                      <td>
                        <Badge tone={r.active ? "green" : "gray"}>
                          {r.active ? "Available" : "Unavailable"}
                        </Badge>
                      </td>
                      <td>
                        {ctx.canManage && (
                          <Button onClick={() => E(r)}>Configure</Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
          {ctx.canManage && (
            <Panel
              title="Workspace memberships"
              caption="Sign out and choose another account to test role boundaries."
            >
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Member</th>
                      <th>Demo email</th>
                      <th>Role</th>
                      <th>Access</th>
                    </tr>
                  </thead>
                  <tbody>
                    {members.map((m) => (
                      <tr key={m.id}>
                        <td>{m.name}</td>
                        <td>
                          <code>{m.email}</code>
                        </td>
                        <td>
                          {ctx.user.role === "owner" && m.role !== "owner" ? (
                            <select
                              aria-label={"Role for " + m.name}
                              value={m.role}
                              onChange={(e) =>
                                ctx.act(
                                  () =>
                                    api(
                                      "/members/" + m.id,
                                      { role: e.target.value },
                                      "PATCH",
                                    ),
                                  "Membership updated",
                                )
                              }
                            >
                              <option value="manager">Manager</option>
                              <option value="operator">Operator</option>
                              <option value="viewer">Viewer</option>
                            </select>
                          ) : (
                            <Badge tone="blue">{label(m.role)}</Badge>
                          )}
                        </td>
                        <td>
                          {m.role === "operator"
                            ? "Own assigned leads"
                            : m.role === "viewer"
                              ? "Read and export"
                              : m.role === "owner"
                                ? "All controls"
                                : "Team and workflow controls"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>
          )}
        </>
      )}
      {tab === "Workspace settings" && settings && (
        <Panel
          title="Operational policies"
          caption="Changes apply to new tasks; existing deadlines are preserved."
        >
          <form
            className="settings-form"
            onSubmit={async (e) => {
              e.preventDefault();
              const d = Object.fromEntries(new FormData(e.currentTarget));
              await ctx.act(
                () =>
                  api(
                    "/settings",
                    {
                      sla_minutes: +d.sla_minutes,
                      retention_days: +d.retention_days,
                    },
                    "PATCH",
                  ),
                "Policies saved",
              );
            }}
          >
            <div className="form-grid">
              <Field
                label="First-response SLA (minutes)"
                name="sla_minutes"
                type="number"
                min={1}
                max={1440}
                required
                defaultValue={settings.settings.sla_minutes}
                disabled={ctx.user.role !== "owner"}
              />
              <Field
                label="Retention policy (days)"
                name="retention_days"
                type="number"
                min={7}
                max={730}
                required
                defaultValue={settings.settings.retention_days}
                disabled={ctx.user.role !== "owner"}
              />
              <Field label="Timezone" value="Asia/Karachi" disabled />
              <Field label="Currency" value="PKR" disabled />
            </div>
            <p className="small">
              Retention is a documented policy. Contact redaction is an explicit
              owner action in lead details; automatic deletion is disabled to
              preserve demo evidence.
            </p>
            {ctx.user.role === "owner" && (
              <Button type="submit" kind="primary" disabled={ctx.busy}>
                Save policies
              </Button>
            )}
          </form>
        </Panel>
      )}
      {tab === "Audit trail" && (
        <Panel
          title="Immutable action trail"
          caption="No normal-user API edits audit records. Owner redaction removes contact payloads and records that action."
        >
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Reason</th>
                  <th>Target</th>
                  <th>Time · PKT</th>
                </tr>
              </thead>
              <tbody>
                {audits.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <b>{label(a.action)}</b>
                    </td>
                    <td>
                      {a.reason || "—"}
                      <small className="block muted">
                        {JSON.stringify(a.after)}
                      </small>
                    </td>
                    <td>
                      <code>{a.target_id.slice(0, 12)}</code>
                    </td>
                    <td>{date(a.created_at, true)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
      {tab === "About the simulation" && (
        <Panel
          title="An honest demonstration"
          caption="What this can prove, and what needs a real pilot."
        >
          <div className="about-copy">
            <h3>Real workflows, synthetic evidence.</h3>
            <p>
              Contacts, businesses, conversations, appointments and deals are
              fictional. Mutations persist in local SQLite. Six deterministic
              agents coordinate through events and recommendations. No
              commercial AI model or external communication account is
              connected.
            </p>
            <h3>How assignment works</h3>
            <p>
              Capacity-constrained matching maximizes specialization, urgency,
              expected response and workload utility. A fairness gap of 0.25 is
              enforced when feasible, with logged relaxation. This is
              cooperative optimization, not proof of a strategic equilibrium. It
              changes accountability and cherry-picking incentives without
              changing pay or imposing penalties.
            </p>
            <h3>What remains unproven</h3>
            <p>
              Conversion lift, real-world scoring accuracy, commercial
              reliability, legal compliance and customer ROI require controlled,
              consented pilots. The planning calculator uses explicit
              hypothetical assumptions.
            </p>
            <h3>Your data is isolated</h3>
            <p>
              Roles and membership resolve on the server. Queries are
              tenant-scoped. HTTP-only sessions, CSRF checks, idempotency keys,
              role checks and audit records protect local workflows.
            </p>
            <Badge tone="blue">
              LP-1 · Seed 20261108 · PKR 0 mandatory local spending
            </Badge>
          </div>
        </Panel>
      )}
      {edit && <RepModal ctx={ctx} rep={edit} close={() => E(null)} />}
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
