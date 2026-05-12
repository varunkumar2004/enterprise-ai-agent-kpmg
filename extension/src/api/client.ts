import * as vscode from 'vscode';
import { randomUUID } from 'crypto';
import { getBearerToken } from '../auth/tokenStore';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
}

export interface StreamChatOptions {
  messages: ChatMessage[];
  model?: string;
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
  feature?: string;
}

function joinUrl(base: string, path: string): string {
  return `${base.replace(/\/+$/, '')}${path.startsWith('/') ? path : `/${path}`}`;
}

function parseSseDataLines(buffer: string): { events: string[]; rest: string } {
  const events: string[] = [];
  let rest = buffer;
  let idx: number;
  while ((idx = rest.indexOf('\n\n')) >= 0) {
    const raw = rest.slice(0, idx);
    rest = rest.slice(idx + 2);
    for (const line of raw.split('\n')) {
      if (line.startsWith('data:')) {
        events.push(line.slice(5).trim());
      }
    }
  }
  return { events, rest };
}

export async function streamChatCompletion(
  context: vscode.ExtensionContext,
  options: StreamChatOptions,
  onDelta: (text: string) => void,
  token?: vscode.CancellationToken,
): Promise<void> {
  const config = vscode.workspace.getConfiguration();
  const baseUrl = String(config.get<string>('assistant.apiBaseUrl') ?? 'http://127.0.0.1:8000');
  const authEnabled = Boolean(config.get<boolean>('assistant.authEnabled'));
  const timeoutMs = Number(config.get<number>('assistant.requestTimeoutMs') ?? 120000);
  const url = joinUrl(baseUrl, '/api/v1/chat/completions');

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
    'X-Request-Id': randomUUID(),
    'X-Assistant-Feature': options.feature ?? 'chat',
  };

  if (authEnabled) {
    const bearer = await getBearerToken(context.secrets);
    if (bearer) {
      headers.Authorization = `Bearer ${bearer}`;
    }
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  token?.onCancellationRequested(() => controller.abort());

  const body = {
    model: options.model ?? config.get<string>('assistant.model'),
    messages: options.messages,
    stream: options.stream ?? true,
    temperature: options.temperature,
    max_tokens: options.max_tokens,
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!response.ok || !response.body) {
      const text = await response.text().catch(() => '');
      throw new Error(`Assistant API error ${response.status}: ${text.slice(0, 500)}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let pending = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      pending += decoder.decode(value, { stream: true });
      const parsed = parseSseDataLines(pending);
      pending = parsed.rest;
      for (const data of parsed.events) {
        if (data === '[DONE]') {
          return;
        }
        try {
          const json = JSON.parse(data) as {
            choices?: Array<{ delta?: { content?: string } }>;
          };
          const piece = json.choices?.[0]?.delta?.content;
          if (typeof piece === 'string' && piece.length > 0) {
            onDelta(piece);
          }
        } catch {
          // ignore malformed chunks — upstream should be trusted JSON lines
        }
      }
    }
  } finally {
    clearTimeout(timer);
  }
}
