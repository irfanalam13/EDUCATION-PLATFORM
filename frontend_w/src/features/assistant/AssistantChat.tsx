"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, TextArea } from "@/components/ui/Field";
import { apiClient, unwrapList } from "@/lib/api";


type Citation = {
  chunk_id: number;
  title: string;
  source_type: string;
  source_id: string;
  score: number;
  preview: string;
  page_start?: number | null;
  page_end?: number | null;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
};

type AIDocument = {
  id: number;
  title: string;
  file_url: string;
  mime_type: string;
  size: number;
  pages: number;
  status: "pending" | "processing" | "ready" | "failed";
  error: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
};

type ChatSessionSummary = {
  id: number;
  title: string;
  last_message: {
    role: "user" | "assistant" | "system";
    content: string;
    created_at: string;
  } | null;
  updated_at: string;
};

type ChatSessionDetail = {
  id: number;
  title: string;
  messages: Array<{
    id: number;
    role: "user" | "assistant" | "system";
    content: string;
    citations: Citation[];
  }>;
};

type ChatResponse = {
  session_id: number;
  answer: string;
  source: string;
  citations: Citation[];
  message: {
    id: number;
    role: "assistant";
    content: string;
    citations: Citation[];
  };
};

function humanSize(bytes: number) {
  if (!bytes) return "0 KB";
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function AssistantChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Upload a PDF or ask from your course material. I will use matching sources first.",
    },
  ]);
  const [documents, setDocuments] = useState<AIDocument[]>([]);
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  async function loadDocuments() {
    const response = await apiClient.get<AIDocument[] | { results: AIDocument[] }>("/api/ai/documents/");
    setDocuments(unwrapList(response.data));
  }

  async function loadSessions() {
    const response = await apiClient.get<ChatSessionSummary[] | { results: ChatSessionSummary[] }>("/api/ai/sessions/");
    setSessions(unwrapList(response.data));
  }

  async function loadSession(id: number) {
    const response = await apiClient.get<ChatSessionDetail>(`/api/ai/sessions/${id}/`);
    setSessionId(response.data.id);
    setMessages(
      response.data.messages
        .filter((message) => message.role === "user" || message.role === "assistant")
        .map((message) => {
          const role: Message["role"] = message.role === "user" ? "user" : "assistant";
          return {
            id: String(message.id),
            role,
            content: message.content,
            citations: message.citations,
          };
        }),
    );
  }

  useEffect(() => {
    void loadDocuments().catch(() => undefined);
    void loadSessions().catch(() => undefined);
  }, []);

  async function uploadPdf(file: File | null) {
    if (!file) return;
    setUploading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", file.name);

    try {
      const response = await apiClient.post<AIDocument>("/api/ai/documents/", formData);
      setDocuments((current) => [response.data, ...current.filter((document) => document.id !== response.data.id)]);
      if (response.data.status === "failed") {
        setError(response.data.error || "PDF processing failed.");
      }
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "PDF upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function send() {
    const question = draft.trim();
    if (!question || busy) return;

    const userMessage: Message = { id: `${Date.now()}-user`, role: "user", content: question };
    setDraft("");
    setMessages((current) => [...current, userMessage]);
    setBusy(true);
    setError("");

    try {
      const response = await apiClient.post<ChatResponse>("/api/ai/chat/", {
        message: question,
        session_id: sessionId,
      });
      setSessionId(response.data.session_id);
      setMessages((current) => [
        ...current,
        {
          id: String(response.data.message.id),
          role: "assistant",
          content: response.data.answer,
          citations: response.data.citations,
        },
      ]);
      void loadSessions().catch(() => undefined);
    } catch (chatError) {
      setError(chatError instanceof Error ? chatError.message : "AI chat request failed.");
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-assistant`,
          role: "assistant",
          content: "I could not reach the AI endpoint. Please confirm the backend is running and you are logged in.",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <Card className="p-6">
        <div className="flex flex-col gap-4 border-b border-app pb-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">AI study assistant</h1>
            <p className="mt-1 text-sm text-muted">RAG chat, PDF sources, and saved history.</p>
          </div>
          <Button variant="secondary" onClick={() => {
            setSessionId(null);
            setMessages([
              {
                id: "welcome",
                role: "assistant",
                content: "Upload a PDF or ask from your course material. I will use matching sources first.",
              },
            ]);
          }}>
            New chat
          </Button>
        </div>

        {error ? (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
            {error}
          </div>
        ) : null}

        <div className="mt-6 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`rounded-md p-4 text-sm leading-6 ${
                message.role === "assistant"
                  ? "border border-app bg-slate-50 dark:bg-slate-900"
                  : "ml-auto max-w-[85%] bg-cyan-700 text-white"
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>
              {message.citations?.length ? (
                <div className="mt-4 space-y-2 border-t border-app pt-3">
                  {message.citations.slice(0, 3).map((citation) => (
                    <div key={`${message.id}-${citation.chunk_id}`} className="rounded-md border border-app bg-card p-3 text-xs text-muted">
                      <div className="font-medium text-foreground">
                        {citation.title || citation.source_type} - {(citation.score * 100).toFixed(0)}%
                      </div>
                      <div className="mt-1 line-clamp-3">{citation.preview}</div>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>

        <div className="mt-6 space-y-3">
          <TextArea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask about a concept, revision plan, or uploaded material..."
          />
          <div className="flex justify-end">
            <Button disabled={!draft.trim() || busy} onClick={() => void send()}>
              {busy ? "Sending..." : "Send"}
            </Button>
          </div>
        </div>
      </Card>

      <div className="space-y-6">
        <Card className="p-6">
          <Field label="PDF source" hint="PDF files only">
            <input
              className="block w-full rounded-md border border-app bg-transparent px-3 py-2 text-sm"
              type="file"
              accept="application/pdf"
              disabled={uploading}
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                event.target.value = "";
                void uploadPdf(file);
              }}
            />
          </Field>
          <div className="mt-4 space-y-3">
            {documents.length ? documents.map((document) => (
              <div key={document.id} className="rounded-md border border-app p-3 text-sm">
                <div className="font-medium">{document.title}</div>
                <div className="mt-1 text-xs text-muted">
                  {document.status} - {document.chunk_count} chunks - {document.pages} pages - {humanSize(document.size)}
                </div>
                {document.error ? <div className="mt-2 text-xs text-red-600">{document.error}</div> : null}
              </div>
            )) : (
              <div className="rounded-md border border-app p-3 text-sm text-muted">No PDFs uploaded yet.</div>
            )}
            {uploading ? <div className="text-sm text-muted">Uploading and indexing...</div> : null}
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold">Chat history</h2>
          <div className="mt-4 space-y-3">
            {sessions.length ? sessions.map((session) => (
              <button
                key={session.id}
                className={`block w-full rounded-md border border-app p-3 text-left text-sm transition hover:border-cyan-600 ${
                  session.id === sessionId ? "bg-cyan-50 dark:bg-cyan-950/30" : ""
                }`}
                onClick={() => void loadSession(session.id)}
              >
                <div className="font-medium">{session.title || "AI chat"}</div>
                {session.last_message ? (
                  <div className="mt-1 line-clamp-2 text-xs text-muted">{session.last_message.content}</div>
                ) : null}
              </button>
            )) : (
              <div className="rounded-md border border-app p-3 text-sm text-muted">No saved chats yet.</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
