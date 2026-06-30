import React from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  Archive,
  BrainCircuit,
  Cpu,
  FileText,
  Gauge,
  Lock,
  MessageSquareText,
  Play,
  Quote,
  Server,
  ShieldCheck,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import "./styles.css";

const ABSTENTION = "I do not know based on the provided documents.";

function App() {
  const [indexName, setIndexName] = React.useState("default");
  const [useSamples, setUseSamples] = React.useState(true);
  const [files, setFiles] = React.useState([]);
  const [topK, setTopK] = React.useState(3);
  const [question, setQuestion] = React.useState("");
  const [status, setStatus] = React.useState(null);
  const [system, setSystem] = React.useState(null);
  const [indexInfo, setIndexInfo] = React.useState(null);
  const [result, setResult] = React.useState(null);
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    refreshHealth();
    refreshDocuments();
  }, []);

  const documents = indexInfo?.documents || [];
  const documentsReady = useSamples || files.length > 0 || documents.length > 0;
  const modelReady = Boolean(system?.model_loaded);
  const indexReady = Boolean(system?.index_ready || indexInfo?.index_ready || indexInfo?.chunks);

  async function refreshHealth() {
    try {
      const data = await request("/health");
      setSystem(data);
    } catch {
      setStatus({ tone: "warn", text: "Backend status is unavailable." });
    }
  }

  async function refreshDocuments() {
    try {
      const data = await request("/documents");
      if (data.documents?.length) {
        setIndexInfo((current) => ({ ...(current || {}), documents: data.documents, index_ready: true }));
      }
    } catch {
      // The empty document state is already represented in the UI.
    }
  }

  async function buildIndex() {
    setBusy(true);
    setStatus({ tone: "gold", text: "Building a local evidence index..." });
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("use_samples", useSamples ? "true" : "false");
      for (const file of files) {
        formData.append("files", file);
      }
      const data = await request("/upload", { method: "POST", body: formData });
      setIndexInfo(data);
      setStatus({ tone: "ok", text: data.message });
      await refreshHealth();
    } catch (error) {
      setStatus({ tone: "warn", text: error.message });
    } finally {
      setBusy(false);
    }
  }

  async function loadIndex() {
    setBusy(true);
    setStatus({ tone: "gold", text: "Loading cached local index..." });
    try {
      const docs = await request("/documents");
      const health = await request("/health");
      setSystem(health);
      setIndexInfo({ documents: docs.documents || [], index_ready: health.index_ready, chunks: 0 });
      setStatus({
        tone: health.index_ready ? "ok" : "warn",
        text: health.index_ready ? "Loaded cached local index." : "No cached index found. Upload documents first.",
      });
    } catch (error) {
      setStatus({ tone: "warn", text: error.message });
    } finally {
      setBusy(false);
    }
  }

  async function askQuestion() {
    if (!question.trim()) {
      setStatus({ tone: "warn", text: "Ask a question about your documents first." });
      return;
    }
    setBusy(true);
    setStatus({ tone: "gold", text: "Retrieving evidence and preparing an answer..." });
    try {
      const data = await request("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: topK }),
      });
      setResult(data);
      setStatus({ tone: "ok", text: "Answer grounded in retrieved evidence." });
    } catch (error) {
      setResult(null);
      setStatus({ tone: "warn", text: error.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen overflow-hidden bg-adtc-black text-adtc-cream">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <section className="relative mx-auto flex min-h-screen w-full max-w-[1680px] flex-col px-5 py-6 sm:px-8 lg:px-10">
        <TopBar system={system} />

        <section className="grid flex-1 gap-8 py-8 2xl:grid-cols-[minmax(520px,0.88fr)_minmax(860px,1.12fr)] 2xl:items-center">
          <div className="max-w-[760px] space-y-8">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-adtc-line bg-adtc-card/80 px-4 py-2 text-sm text-adtc-muted shadow-amber">
                <Sparkles className="h-4 w-4 text-adtc-gold" />
                ADTC 2026 offline intelligence
              </div>
              <div className="space-y-5">
                <h1 className="max-w-4xl text-5xl font-black leading-[0.95] tracking-tight text-adtc-cream sm:text-6xl xl:text-7xl">
                  Private AI for your business documents.
                </h1>
                <p className="max-w-2xl text-lg leading-8 text-adtc-muted sm:text-xl">
                  Upload policies, invoices, agreements, and price lists. Ask questions. Get answers with evidence.
                  Everything runs offline.
                </p>
              </div>
              <StatusPills system={system} modelReady={modelReady} />
            </div>

            <PerformanceStrip topK={topK} indexInfo={indexInfo} modelReady={modelReady} />
          </div>

          <Workspace
            indexName={indexName}
            setIndexName={setIndexName}
            useSamples={useSamples}
            setUseSamples={setUseSamples}
            files={files}
            setFiles={setFiles}
            topK={topK}
            setTopK={setTopK}
            question={question}
            setQuestion={setQuestion}
            buildIndex={buildIndex}
            loadIndex={loadIndex}
            askQuestion={askQuestion}
            busy={busy}
            status={status}
            documentsReady={documentsReady}
            indexReady={indexReady}
            modelReady={modelReady}
            result={result}
            documents={documents}
          />
        </section>
      </section>
    </main>
  );
}

function TopBar({ system }) {
  return (
    <header className="relative z-10 flex items-center justify-between border-b border-adtc-line/70 pb-5">
      <div className="flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-2xl border border-adtc-gold/40 bg-adtc-card shadow-amber">
          <BrainCircuit className="h-6 w-6 text-adtc-gold" />
        </div>
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-adtc-gold">Offline SME AI</p>
          <p className="text-sm text-adtc-muted">Local RAG assistant</p>
        </div>
      </div>
      <div className="hidden items-center gap-2 rounded-full border border-adtc-line bg-adtc-card px-4 py-2 text-sm text-adtc-muted sm:flex">
        <Server className="h-4 w-4 text-adtc-green" />
        {system?.service || "backend status"}
      </div>
    </header>
  );
}

function StatusPills({ system, modelReady }) {
  const pills = [
    { icon: Lock, label: "Offline first", tone: "gold" },
    { icon: ShieldCheck, label: "No cloud APIs", tone: "green" },
    { icon: Cpu, label: modelReady ? "GGUF model found" : "Model missing", tone: modelReady ? "green" : "warn" },
    { icon: Archive, label: `${system?.documents_count || 0} indexed docs`, tone: "gold" },
  ];
  return (
    <div className="flex flex-wrap gap-3">
      {pills.map((pill) => (
        <div key={pill.label} className={`status-pill ${pill.tone}`}>
          <pill.icon className="h-4 w-4" />
          {pill.label}
        </div>
      ))}
    </div>
  );
}

function PerformanceStrip({ topK, indexInfo, modelReady }) {
  return (
    <div className="grid gap-3 rounded-3xl border border-adtc-line bg-adtc-card/80 p-4 shadow-premium sm:grid-cols-3">
      <Metric icon={Gauge} label="Context" value="2048 tokens" />
      <Metric icon={Quote} label="Retrieval" value={`Top ${topK} chunks`} />
      <Metric icon={Cpu} label="Model" value={modelReady ? "Local GGUF" : "Waiting"} />
      {indexInfo ? <p className="text-sm text-adtc-muted sm:col-span-3">{indexInfo.chunks} chunks indexed locally.</p> : null}
    </div>
  );
}

function Metric({ icon: Icon, label, value }) {
  return (
    <div className="rounded-2xl border border-adtc-line bg-adtc-ink/70 p-4">
      <Icon className="mb-3 h-5 w-5 text-adtc-gold" />
      <p className="text-xs uppercase tracking-[0.22em] text-adtc-muted">{label}</p>
      <p className="mt-1 text-lg font-bold text-adtc-cream">{value}</p>
    </div>
  );
}

function Workspace(props) {
  return (
    <div className="workspace-shell">
      <aside className="document-rail">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-black">Documents</h2>
          <FileText className="h-5 w-5 text-adtc-gold" />
        </div>

        <label className="field">
          <span>Index name</span>
          <input value={props.indexName} onChange={(event) => props.setIndexName(event.target.value)} />
        </label>

        <label className="sample-toggle">
          <input
            type="checkbox"
            checked={props.useSamples}
            onChange={(event) => props.setUseSamples(event.target.checked)}
          />
          <span>Use sample SME documents</span>
        </label>

        <label className="upload-zone">
          <UploadCloud className="h-7 w-7 text-adtc-gold" />
          <span className="font-bold">Upload PDF or TXT</span>
          <span className="text-sm text-adtc-muted">Policies, invoices, agreements, price lists</span>
          <input
            type="file"
            multiple
            accept=".pdf,.txt"
            onChange={(event) => props.setFiles(Array.from(event.target.files || []))}
          />
        </label>

        <DocumentList files={props.files} useSamples={props.useSamples} documents={props.documents} />

        <div className="grid grid-cols-2 gap-3">
          <button className="action-button" disabled={props.busy} onClick={props.buildIndex}>
            <Play className="h-4 w-4" />
            Build
          </button>
          <button className="quiet-button" disabled={props.busy} onClick={props.loadIndex}>
            Load
          </button>
        </div>

        <label className="field">
          <span>Evidence depth: {props.topK}</span>
          <input
            type="range"
            min="1"
            max="6"
            value={props.topK}
            onChange={(event) => props.setTopK(Number(event.target.value))}
          />
        </label>
      </aside>

      <section className="chat-panel">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(220px,300px)] lg:items-start">
          <div className="min-w-0">
            <p className="text-sm uppercase tracking-[0.22em] text-adtc-gold">Workspace</p>
            <h2 className="mt-2 text-3xl font-black leading-tight">Ask with proof.</h2>
          </div>
          <StatusBadge status={props.status} />
        </div>

        <EmptyStates
          documentsReady={props.documentsReady}
          indexReady={props.indexReady}
          modelReady={props.modelReady}
          status={props.status}
        />

        <div className="question-box">
          <MessageSquareText className="h-5 w-5 shrink-0 text-adtc-gold" />
          <input
            value={props.question}
            onChange={(event) => props.setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") props.askQuestion();
            }}
            placeholder="Ask about payment terms, return policies, prices, or obligations"
          />
          <button className="action-button" disabled={props.busy} onClick={props.askQuestion}>
            Ask
          </button>
        </div>

        <AnswerCard result={props.result} />
      </section>
    </div>
  );
}

function DocumentList({ files, useSamples, documents }) {
  const docs = [
    ...(documents?.length ? documents.map((document) => document.filename) : []),
    ...(!documents?.length && useSamples
      ? ["sample_supplier_agreement.txt", "sample_returns_policy.txt", "sample_price_list.txt"]
      : []),
    ...files.map((file) => file.name),
  ];

  if (!docs.length) {
    return <div className="empty-mini">No documents uploaded yet.</div>;
  }

  return (
    <div className="space-y-2">
      {docs.map((doc) => (
        <div className="document-chip" key={doc}>
          <FileText className="h-4 w-4 text-adtc-gold" />
          <span>{doc}</span>
        </div>
      ))}
    </div>
  );
}

function EmptyStates({ documentsReady, indexReady, modelReady, status }) {
  const states = [];
  if (!documentsReady) states.push({ icon: UploadCloud, text: "No documents uploaded. Add PDF/TXT files to begin." });
  if (!indexReady) states.push({ icon: Archive, text: "Index not built. Build or load a cached index before asking." });
  if (!modelReady) states.push({ icon: AlertTriangle, text: "Model missing. Place a GGUF file at models/model.gguf." });
  if (status?.tone === "warn" && status.text.includes("evidence")) {
    states.push({ icon: Quote, text: "No evidence found for that question." });
  }

  if (!states.length) return null;

  return (
    <div className="grid gap-3 min-[900px]:grid-cols-2">
      {states.map((state) => (
        <div className="empty-state" key={state.text}>
          <state.icon className="h-5 w-5 text-adtc-gold" />
          <span>{state.text}</span>
        </div>
      ))}
    </div>
  );
}

function StatusBadge({ status }) {
  if (!status) {
    return <div className="status-badge">Ready</div>;
  }
  return <div className={`status-badge ${status.tone}`}>{status.text}</div>;
}

function AnswerCard({ result }) {
  const answer = result?.answer || "Answers will appear here after the local model reads retrieved evidence.";
  const evidence = result?.evidence || [];
  const abstained = answer === ABSTENTION;

  return (
    <article className="answer-card">
      <div className="answer-section">
        <div className="section-label">Answer</div>
        <p className={abstained ? "text-adtc-gold" : ""}>{answer}</p>
      </div>

      <div className="evidence-section">
        <div className="section-label">Evidence</div>
        {evidence.length ? (
          <div className="grid gap-3">
            {evidence.map((item) => (
              <div className="evidence-card" key={`${item.source_document}-${item.chunk_id}`}>
                <div className="flex items-center justify-between gap-3">
                  <strong>{item.source_document}</strong>
                  <span>{item.confidence || "low"} support</span>
                </div>
                <p>{item.quote}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-mini">No evidence found yet.</div>
        )}
      </div>

      <details className="debug-chunks">
        <summary>Retrieved chunks</summary>
        {result?.retrieved_chunks?.length ? (
          <div className="mt-3 grid gap-3">
            {result.retrieved_chunks.map((chunk) => (
              <div className="chunk-card" key={`${chunk.source_document}-${chunk.chunk_id}`}>
                <div className="flex items-center justify-between gap-3">
                  <strong>{chunk.source_document}</strong>
                  <span>{Number(chunk.score || 0).toFixed(3)}</span>
                </div>
                <p>{chunk.text}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-3 empty-mini">No chunks retrieved yet.</div>
        )}
      </details>
    </article>
  );
}

async function request(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Request failed.");
  }
  return data;
}

createRoot(document.getElementById("root")).render(<App />);
