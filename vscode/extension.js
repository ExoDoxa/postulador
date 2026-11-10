'use strict';
const vscode = require('vscode');
const http = require('http');
const { spawn } = require('child_process');

const URL_PANEL = 'http://127.0.0.1:8770/';
const INTENTOS = 40;
let pestana = null;

const responde = () => new Promise((resolver) => {
  const peticion = http.get(URL_PANEL, (respuesta) => { respuesta.resume(); resolver(true); });
  peticion.setTimeout(800, () => { peticion.destroy(); resolver(false); });
  peticion.on('error', () => resolver(false));
});

async function asegurarPanel(carpeta) {
  if (await responde()) return true;
  spawn('python', ['-m', 'postulador', 'panel'], { cwd: carpeta, detached: true, stdio: 'ignore', windowsHide: true }).on('error', () => {}).unref();
  for (let intento = 0; intento < INTENTOS; intento += 1) {
    if (await responde()) return true;
    await new Promise((resolver) => { setTimeout(resolver, 250); });
  }
  return false;
}

const pagina = () => `<!doctype html>
<html><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; frame-src ${URL_PANEL.slice(0, -1)}; style-src 'unsafe-inline'">
<style>html, body, iframe { margin: 0; padding: 0; width: 100%; height: 100%; border: 0; overflow: hidden }</style>
</head><body><iframe src="${URL_PANEL}" title="Postulador"></iframe></body></html>`;

async function abrir() {
  const carpeta = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  if (!carpeta) return;
  if (pestana) { pestana.reveal(); return; }
  if (!(await asegurarPanel(carpeta))) {
    vscode.window.showErrorMessage('Postulador: no pude iniciar el panel. Ejecuta python -m postulador panel.');
    return;
  }
  pestana = vscode.window.createWebviewPanel('postulador', 'Postulador', { viewColumn: vscode.ViewColumn.Beside, preserveFocus: true }, { enableScripts: true, retainContextWhenHidden: true });
  pestana.webview.html = pagina();
  pestana.onDidDispose(() => { pestana = null; });
}

function activate(contexto) {
  contexto.subscriptions.push(vscode.commands.registerCommand('postulador.abrir', abrir));
  abrir();
}

module.exports = { activate, deactivate() {} };
