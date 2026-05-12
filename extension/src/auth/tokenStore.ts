import * as vscode from 'vscode';

const SECRET_KEY = 'assistant.bearerToken';

/**
 * Tokens never belong in settings.json — persist via VS Code SecretStorage (OS-backed).
 */
export async function getBearerToken(secrets: vscode.SecretStorage): Promise<string | undefined> {
  return secrets.get(SECRET_KEY);
}

export async function setBearerToken(secrets: vscode.SecretStorage, token: string | undefined): Promise<void> {
  if (!token) {
    await secrets.delete(SECRET_KEY);
    return;
  }
  await secrets.store(SECRET_KEY, token);
}
