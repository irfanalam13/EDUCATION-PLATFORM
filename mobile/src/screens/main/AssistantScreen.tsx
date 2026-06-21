import { useEffect, useState } from "react";
import * as DocumentPicker from "expo-document-picker";
import { StyleSheet, View } from "react-native";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Field } from "@/components/Field";
import { Screen } from "@/components/Screen";
import { Text } from "@/components/Text";
import { apiRequest, apiUploadFile } from "@/services/api";
import { palette, spacing } from "@/theme";

type Citation = {
  chunk_id: number;
  title: string;
  source_type: string;
  score: number;
  preview: string;
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
  status: "pending" | "processing" | "ready" | "failed";
  error: string;
  chunk_count: number;
  pages: number;
  size: number;
};

type ChatSessionSummary = {
  id: number;
  title: string;
  last_message: {
    role: "user" | "assistant" | "system";
    content: string;
  } | null;
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
  citations: Citation[];
  message: {
    id: number;
    content: string;
  };
};

function unwrapList<T>(payload: T[] | { results?: T[] }) {
  return Array.isArray(payload) ? payload : payload.results ?? [];
}

function humanSize(bytes: number) {
  if (!bytes) return "0 KB";
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function AssistantScreen() {
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [documents, setDocuments] = useState<AIDocument[]>([]);
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "intro",
      role: "assistant",
      content: "Upload a PDF or ask from your course material. I will use matching sources first."
    }
  ]);

  async function loadDocuments() {
    const payload = await apiRequest<AIDocument[] | { results: AIDocument[] }>("/api/ai/documents/");
    setDocuments(unwrapList(payload));
  }

  async function loadSessions() {
    const payload = await apiRequest<ChatSessionSummary[] | { results: ChatSessionSummary[] }>("/api/ai/sessions/");
    setSessions(unwrapList(payload));
  }

  async function loadSession(id: number) {
    const session = await apiRequest<ChatSessionDetail>(`/api/ai/sessions/${id}/`);
    setSessionId(session.id);
    setMessages(
      session.messages
        .filter((message) => message.role === "user" || message.role === "assistant")
        .map((message) => {
          const role: Message["role"] = message.role === "user" ? "user" : "assistant";
          return {
            id: String(message.id),
            role,
            content: message.content,
            citations: message.citations
          };
        })
    );
  }

  useEffect(() => {
    void loadDocuments().catch(() => undefined);
    void loadSessions().catch(() => undefined);
  }, []);

  async function pickPdf() {
    setError("");
    const result = await DocumentPicker.getDocumentAsync({
      type: "application/pdf",
      copyToCacheDirectory: true,
      multiple: false
    });

    if (result.canceled) return;
    const asset = result.assets[0];
    if (!asset) return;

    setUploading(true);
    try {
      const document = await apiUploadFile<AIDocument>(
        "/api/ai/documents/",
        {
          uri: asset.uri,
          name: asset.name || "document.pdf",
          mimeType: asset.mimeType || "application/pdf"
        },
        { title: asset.name || "Learning document" }
      );
      setDocuments((current) => [document, ...current.filter((item) => item.id !== document.id)]);
      if (document.status === "failed") setError(document.error || "PDF processing failed.");
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "PDF upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function send() {
    const text = draft.trim();
    if (!text || busy) return;

    setDraft("");
    setBusy(true);
    setError("");
    setMessages((current) => [...current, { id: `${Date.now()}-user`, role: "user", content: text }]);

    try {
      const response = await apiRequest<ChatResponse>("/api/ai/chat/", {
        method: "POST",
        body: { message: text, session_id: sessionId }
      });
      setSessionId(response.session_id);
      setMessages((current) => [
        ...current,
        {
          id: String(response.message.id),
          role: "assistant",
          content: response.answer,
          citations: response.citations
        }
      ]);
      void loadSessions().catch(() => undefined);
    } catch (chatError) {
      setError(chatError instanceof Error ? chatError.message : "AI chat request failed.");
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-assistant`,
          role: "assistant",
          content: "I could not reach the AI endpoint. Please confirm the backend is running and you are logged in."
        }
      ]);
    } finally {
      setBusy(false);
    }
  }

  function newChat() {
    setSessionId(null);
    setMessages([
      {
        id: "intro",
        role: "assistant",
        content: "Upload a PDF or ask from your course material. I will use matching sources first."
      }
    ]);
  }

  return (
    <Screen>
      <View style={styles.headerRow}>
        <View style={styles.headerText}>
          <Text variant="title">AI Assistant</Text>
          <Text variant="muted">RAG chat, PDF sources, and saved history.</Text>
        </View>
        <Button label="New" variant="secondary" onPress={newChat} style={styles.newButton} />
      </View>

      {error ? (
        <Card style={styles.errorCard}>
          <Text style={styles.errorText}>{error}</Text>
        </Card>
      ) : null}

      <Card style={styles.uploadCard}>
        <Button label={uploading ? "Indexing PDF..." : "Upload PDF"} onPress={pickPdf} disabled={uploading} />
        {documents.map((document) => (
          <View key={document.id} style={styles.sourceItem}>
            <Text variant="label">{document.title}</Text>
            <Text variant="muted">
              {document.status} - {document.chunk_count} chunks - {document.pages} pages - {humanSize(document.size)}
            </Text>
            {document.error ? <Text style={styles.errorText}>{document.error}</Text> : null}
          </View>
        ))}
        {!documents.length ? <Text variant="muted">No PDFs uploaded yet.</Text> : null}
      </Card>

      <Card style={styles.thread}>
        {messages.map((message) => (
          <View key={message.id} style={[styles.bubble, message.role === "user" ? styles.userBubble : styles.assistantBubble]}>
            <Text style={message.role === "user" ? styles.userText : undefined}>{message.content}</Text>
            {message.citations?.slice(0, 2).map((citation) => (
              <View key={`${message.id}-${citation.chunk_id}`} style={styles.citation}>
                <Text variant="label">{citation.title || citation.source_type}</Text>
                <Text variant="muted">{citation.preview}</Text>
              </View>
            ))}
          </View>
        ))}
      </Card>

      <Card style={styles.composer}>
        <Field label="Message" value={draft} onChangeText={setDraft} multiline placeholder="Ask about a topic, note, or uploaded PDF" />
        <Button label={busy ? "Sending..." : "Send"} onPress={send} disabled={!draft.trim() || busy} />
      </Card>

      <Card style={styles.history}>
        <Text variant="subtitle">Chat history</Text>
        {sessions.map((session) => (
          <View key={session.id} style={styles.historyItem}>
            <View style={styles.historyText}>
              <Text variant="label">{session.title || "AI chat"}</Text>
              {session.last_message ? <Text variant="muted" numberOfLines={2}>{session.last_message.content}</Text> : null}
            </View>
            <Button label="Open" variant="secondary" onPress={() => void loadSession(session.id)} style={styles.openButton} />
          </View>
        ))}
        {!sessions.length ? <Text variant="muted">No saved chats yet.</Text> : null}
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  headerRow: {
    flexDirection: "row",
    gap: spacing.md,
    alignItems: "center"
  },
  headerText: {
    flex: 1
  },
  newButton: {
    minWidth: 76
  },
  errorCard: {
    backgroundColor: "#fef2f2",
    borderColor: "#fecaca"
  },
  errorText: {
    color: "#b91c1c"
  },
  uploadCard: {
    gap: spacing.md
  },
  sourceItem: {
    borderColor: palette.border,
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.sm
  },
  thread: {
    gap: spacing.sm
  },
  bubble: {
    borderRadius: 8,
    padding: spacing.md,
    gap: spacing.sm
  },
  assistantBubble: {
    backgroundColor: "#f1f5f9"
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: palette.primary,
    maxWidth: "86%"
  },
  userText: {
    color: "#ffffff"
  },
  citation: {
    backgroundColor: palette.card,
    borderColor: palette.border,
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.sm
  },
  composer: {
    gap: spacing.md
  },
  history: {
    gap: spacing.md
  },
  historyItem: {
    alignItems: "center",
    borderColor: palette.border,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.sm,
    padding: spacing.sm
  },
  historyText: {
    flex: 1
  },
  openButton: {
    minWidth: 80
  }
});
