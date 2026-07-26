#!/usr/bin/env node
/**
 * Regenera prototype/export/EasyRun-src.dc.html a partir da fonte canônica.
 *
 * O espelho difere do canônico em exatamente duas coisas, e ambas são estruturais:
 *   1. o <script src> aponta para "../support.js" (o arquivo está um nível abaixo);
 *   2. há um <template id="__bundler_thumbnail"> com o SVG de miniatura.
 *
 * Manter as duas cópias sincronizadas à mão sempre divergiu no primeiro esquecimento.
 * Este script faz a cópia; `node tools/check-prototype.mjs` verifica se está em dia.
 *
 * Uso:  node tools/sync-export.mjs
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), '..');
const CANONICO = join(RAIZ, 'prototype', 'EasyRun.dc.html');
const ESPELHO = join(RAIZ, 'prototype', 'export', 'EasyRun-src.dc.html');

const TAG_CANONICA = '<script src="./support.js"></script>';
const TAG_ESPELHO = '<script src="../support.js"></script>';

const canonico = readFileSync(CANONICO, 'utf8');
if (!canonico.includes(TAG_CANONICA)) {
  console.error(`não encontrei ${TAG_CANONICA} na fonte canônica — o cabeçalho mudou?`);
  process.exit(1);
}

// preserva o final de linha da fonte (os arquivos do protótipo são CRLF)
const EOL = canonico.includes('\r\n') ? '\r\n' : '\n';

// preserva o <template> de thumbnail que só existe no espelho
let thumbnail = '';
try {
  const atual = readFileSync(ESPELHO, 'utf8');
  const m = atual.match(/<template id="__bundler_thumbnail"[\s\S]*?<\/template>\r?\n/);
  // normaliza para o final de linha da fonte — o bloco vem do espelho anterior,
  // que pode ter sido escrito com outra convenção
  if (m) thumbnail = m[0].replace(/\r?\n$/, '').replace(/\r?\n/g, EOL);
} catch {
  console.warn('espelho ainda não existe; será criado sem o <template> de thumbnail');
}

const novo = canonico.replace(TAG_CANONICA, TAG_ESPELHO + (thumbnail ? EOL + thumbnail : ''));

writeFileSync(ESPELHO, novo, 'utf8');
console.log(
  `espelho regenerado: ${novo.split('\n').length - 1} linhas` +
  (thumbnail ? ' (thumbnail preservado)' : '')
);
