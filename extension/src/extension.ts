import * as vscode from 'vscode';
import { ChatPanelProvider } from './chat/ChatPanelProvider';

export function activate(context: vscode.ExtensionContext): void {
  const chat = new ChatPanelProvider(context);

  context.subscriptions.push(
    vscode.commands.registerCommand('assistant.openChat', () => {
      chat.show();
    }),
    vscode.commands.registerCommand('assistant.explainSelection', async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        void vscode.window.showWarningMessage('No active editor.');
        return;
      }
      const selection = editor.selection;
      const text = editor.document.getText(selection.isEmpty ? undefined : selection);
      if (!text.trim()) {
        void vscode.window.showWarningMessage('Select code to explain.');
        return;
      }
      chat.show();
      await vscode.window.showInformationMessage(
        'Explain workflow: chat panel streaming will be wired to /explain in next iteration.',
      );
    }),
    chat,
  );
}

export function deactivate(): void {}
