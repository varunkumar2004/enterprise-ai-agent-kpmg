import * as vscode from 'vscode';
import { streamChatCompletion } from '../api/client';

export class ChatPanelProvider implements vscode.Disposable {
  private panel: vscode.WebviewPanel | undefined;

  constructor(private readonly context: vscode.ExtensionContext) {}

  show(): void {
    if (this.panel) {
      this.panel.reveal(vscode.ViewColumn.Beside);
      return;
    }

    this.panel = vscode.window.createWebviewPanel(
      'assistantChat',
      'Coding Assistant',
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, 'media')],
      },
    );

    this.panel.webview.html = this.renderHtml(this.panel.webview);
    this.panel.webview.onDidReceiveMessage((msg) => void this.handleMessage(msg));
    this.panel.onDidDispose(() => {
      this.panel = undefined;
    });
  }

  private handleMessage(msg: { command?: string; text?: string }): void {
    if (!this.panel) {
      return;
    }
    if (msg.command === 'send' && typeof msg.text === 'string') {
      void this.runPrompt(msg.text);
    }
  }

  private async runPrompt(userText: string): Promise<void> {
    if (!this.panel) {
      return;
    }

    this.panel.webview.postMessage({ type: 'reset' });

    const messages = [
      {
        role: 'system' as const,
        content:
          'You are an enterprise coding assistant operating inside a regulated environment. Prefer concise, accurate answers.',
      },
      { role: 'user' as const, content: userText },
    ];

    try {
      await streamChatCompletion(
        this.context,
        { messages, stream: true, feature: 'chat' },
        (delta) => {
          this.panel?.webview.postMessage({ type: 'chunk', delta });
        },
      );
      this.panel.webview.postMessage({ type: 'done' });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      this.panel.webview.postMessage({ type: 'error', message });
    }
  }

  private renderHtml(webview: vscode.Webview): string {
    const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this.context.extensionUri, 'media', 'chat.js'));
    const nonce = getNonce();
    const csp = [
      `default-src 'none';`,
      `style-src 'unsafe-inline';`,
      `script-src 'nonce-${nonce}';`,
      `connect-src ${webview.cspSource};`,
    ].join(' ');

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="${csp}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Assistant</title>
  <style>
    body { font-family: var(--vscode-font-family); color: var(--vscode-foreground); padding: 12px; }
    #log { white-space: pre-wrap; border: 1px solid var(--vscode-editorWidget-border); padding: 8px; min-height: 240px; }
    textarea { width: 100%; height: 90px; font-family: inherit; }
    button { margin-top: 8px; }
  </style>
</head>
<body>
  <h3>Enterprise Coding Assistant</h3>
  <textarea id="prompt" placeholder="Ask a question..."></textarea>
  <div><button id="send">Send</button></div>
  <div id="log"></div>
  <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
  }

  dispose(): void {
    this.panel?.dispose();
  }
}

function getNonce(): string {
  let text = '';
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}
