(function () {
  const vscode = acquireVsCodeApi();
  const promptEl = document.getElementById('prompt');
  const logEl = document.getElementById('log');
  const sendBtn = document.getElementById('send');

  function append(text) {
    logEl.textContent += text;
  }

  window.addEventListener('message', (event) => {
    const msg = event.data;
    if (msg.type === 'reset') {
      logEl.textContent = '';
    } else if (msg.type === 'chunk' && typeof msg.delta === 'string') {
      append(msg.delta);
    } else if (msg.type === 'error') {
      append('\n[error] ' + msg.message + '\n');
    }
  });

  sendBtn.addEventListener('click', () => {
    const text = promptEl.value || '';
    vscode.postMessage({ command: 'send', text });
  });
})();
