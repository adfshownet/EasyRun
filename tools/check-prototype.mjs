#!/usr/bin/env node
/**
 * Verificações do protótipo estático (prototype/EasyRun.dc.html).
 *
 * O mockup não tem framework de teste — ele roda no navegador com o runtime `dc`,
 * que não está neste repositório. Este script carrega a classe `Component` fora do
 * navegador, com stubs mínimos de React e DCLogic, e verifica quatro coisas:
 *
 *   1. DADOS     — os cenários são internamente consistentes
 *   2. MOTOR     — cada cenário roda até o fim nos dois caminhos (aprovar e rejeitar)
 *   3. TEMPLATE  — toda variável {{ }} usada existe nos dados que renderVals() devolve
 *   4. ESPELHO   — export/ está sincronizado com a fonte canônica
 *
 * Uso:  node tools/check-prototype.mjs
 * Sai com código 1 se qualquer verificação falhar.
 */

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), '..');
const CANONICO = join(RAIZ, 'prototype', 'EasyRun.dc.html');
const ESPELHO = join(RAIZ, 'prototype', 'export', 'EasyRun-src.dc.html');

const erros = [];
const falha = (msg) => erros.push(msg);

// ---------------------------------------------------------------------------
// Carga: separa o HTML em template + lógica e instancia o Component
// ---------------------------------------------------------------------------

/** Os arquivos do protótipo são CRLF; normalizar aqui deixa as regexes simples. */
const lf = (s) => s.replace(/\r\n/g, '\n');

const html = lf(readFileSync(CANONICO, 'utf8'));

const mScript = html.match(/<script type="text\/x-dc" data-dc-script[^>]*>\n([\s\S]*?)\n<\/script>/);
if (!mScript) {
  console.error('não encontrei o <script data-dc-script> em prototype/EasyRun.dc.html');
  process.exit(1);
}
const logica = mScript[1];
const template = html.slice(0, html.indexOf('<script type="text/x-dc"'));

globalThis.DCLogic = class {
  constructor(props) {
    this.props = props || {};
  }
};
globalThis.React = { createRef: () => ({ current: null }) };
(0, eval)(logica + '\nglobalThis.Component = Component;');

/** Instância crua, só para ler os dados estáticos (agentesDef, cenarios…). */
function novoComponente(cenarioId) {
  const c = new globalThis.Component({ velocidade: 1, autoAprovar: false });
  c.state = c.estadoInicial(cenarioId);
  c.logRef = { current: null };
  c.chatRef = { current: null };
  return c;
}

const base = novoComponente();
const AGENTES = new Set(base.agentesDef().map((a) => a.id));
const RASTREIO = new Set(base.rastreioDef().map((r) => r.k));
const NATUREZAS = new Set(Object.keys(base.naturezaDef()));
const STATUS = new Set(Object.keys({
  ocioso: 1, vigiando: 1, detectando: 1, orquestrando: 1, buscando: 1, analisando: 1,
  executando: 1, monitorando: 1, aguardando: 1, 'concluído': 1, consultando: 1,
  registrando: 1, clonando: 1, delegando: 1, escalando: 1,
}));
const TIPOS_GATE = new Set(['acao', 'pr', 'gmud']);

// ---------------------------------------------------------------------------
// 1. DADOS — consistência interna dos cenários
// ---------------------------------------------------------------------------

function checarDados() {
  const linhas = [];
  const idsDeGate = [];
  let totalPassos = 0;

  for (const cen of base.cenarios()) {
    for (const campo of ['titulo', 'idIncidente', 'severidade', 'algoritmo', 'icone',
      'origem', 'textoProblema', 'textoConcluido']) {
      if (!cen[campo]) falha(`${cen.id}: campo "${campo}" ausente`);
    }
    for (const chave of ['causa', 'plano', 'statusAtivo', 'statusAguardando', 'statusConcluido']) {
      if (!cen.chat?.[chave]) falha(`${cen.id}: chat.${chave} ausente`);
    }

    let plano = [];
    let natureza = null;
    const rastreioVisto = new Set();
    const gates = [];

    cen.passos.forEach((p, i) => {
      totalPassos++;
      const onde = `${cen.id}[${i}]`;

      if (!AGENTES.has(p.ag)) falha(`${onde}: agente desconhecido "${p.ag}"`);
      if (!p.txt && !p.dinamico) falha(`${onde}: sem txt nem dinamico`);
      if (p.dinamico && (!p.dinamico.aprovado || !p.dinamico.rejeitado)) {
        falha(`${onde}: dinamico incompleto (precisa de aprovado e rejeitado)`);
      }

      if (p.fx) {
        for (const [ag, st] of Object.entries(p.fx.agStatus || {})) {
          if (!AGENTES.has(ag)) falha(`${onde}: fx.agStatus para agente desconhecido "${ag}"`);
          if (!STATUS.has(st)) falha(`${onde}: status desconhecido "${st}"`);
        }
        if (p.fx.planoCriar) plano = p.fx.planoCriar.map((x) => x.id);
        if (p.fx.planoOk && !plano.includes(p.fx.planoOk)) {
          falha(`${onde}: planoOk ${p.fx.planoOk} não existe no plano`);
        }
        if (p.fx.planoUpdate && !plano.includes(p.fx.planoUpdate.id)) {
          falha(`${onde}: planoUpdate ${p.fx.planoUpdate.id} não existe no plano`);
        }
        for (const k of Object.keys(p.fx.rastreioSet || {})) {
          if (!RASTREIO.has(k)) falha(`${onde}: rastreioSet com chave desconhecida "${k}"`);
          rastreioVisto.add(k);
        }
        if (p.fx.naturezaSet) {
          if (!NATUREZAS.has(p.fx.naturezaSet)) falha(`${onde}: natureza desconhecida "${p.fx.naturezaSet}"`);
          natureza = p.fx.naturezaSet;
        }
      }

      if (p.gate) {
        gates.push(p.gate);
        idsDeGate.push(p.gate.id);
        for (const campo of ['id', 'tipo', 'titulo', 'descricao', 'risco', 'guardrail',
          'detalhe', 'mensagemAprovado', 'mensagemRejeitado', 'mensagemAutoAprovado']) {
          if (!p.gate[campo]) falha(`${onde}: gate sem o campo "${campo}"`);
        }
        if (!TIPOS_GATE.has(p.gate.tipo)) falha(`${onde}: gate.tipo inválido "${p.gate.tipo}"`);
        if (p.gate.tipo === 'pr') {
          for (const campo of ['repositorio', 'branch', 'arquivos', 'checks']) {
            if (!p.gate[campo]) falha(`${onde}: gate de PR sem o campo "${campo}"`);
          }
        }
        if (p.gate.tipo === 'gmud') {
          for (const campo of ['gmud', 'ci', 'janela', 'rollback']) {
            if (!p.gate[campo]) falha(`${onde}: gate de GMUD sem o campo "${campo}"`);
          }
        }
      }
    });

    const comFim = cen.passos.filter((p) => p.fim);
    if (comFim.length !== 1) falha(`${cen.id}: deve ter exatamente um passo com fim:true (tem ${comFim.length})`);
    if (!cen.passos[cen.passos.length - 1].fim) falha(`${cen.id}: o último passo precisa ter fim:true`);
    if (!natureza) falha(`${cen.id}: nenhum passo define a natureza da remediação`);
    for (const k of ['anm', 'inc', 'ci', 'bug', 'trace']) {
      if (!rastreioVisto.has(k)) falha(`${cen.id}: a cadeia de rastreio nunca preenche "${k}"`);
    }

    linhas.push(
      `  ${cen.id.padEnd(9)} ${String(cen.passos.length).padStart(2)} passos · ` +
      `${gates.length} gate(s) [${gates.map((g) => g.tipo).join(',') || '—'}] · ` +
      `natureza ${String(natureza).padEnd(7)} · rastreio ${rastreioVisto.size}/${RASTREIO.size}`
    );
  }

  const duplicados = idsDeGate.filter((x, i) => idsDeGate.indexOf(x) !== i);
  if (duplicados.length) falha(`ids de gate duplicados: ${[...new Set(duplicados)].join(', ')}`);

  linhas.forEach((l) => console.log(l));
  console.log(`  ${base.cenarios().length} cenários · ${totalPassos} passos · ${AGENTES.size} agentes`);
}

// ---------------------------------------------------------------------------
// 2. MOTOR — roda cada cenário até o fim, nos dois caminhos
// ---------------------------------------------------------------------------

function simular(cenarioId, decisao) {
  const c = novoComponente(cenarioId);

  c.setState = function (patch, cb) {
    const p = typeof patch === 'function' ? patch(this.state) : patch;
    this.state = { ...this.state, ...p };
    if (cb) cb();
  };

  const fila = [];
  const setTimeoutReal = globalThis.setTimeout;
  const clearTimeoutReal = globalThis.clearTimeout;
  globalThis.setTimeout = (fn) => fila.push(fn);
  globalThis.clearTimeout = () => {};

  const gates = [];
  try {
    c.iniciarPausar();
    let guarda = 0;
    while (guarda++ < 1000) {
      if (fila.length) {
        fila.shift()();
        continue;
      }
      if (c.state.aguardandoHitl) {
        const pendente = c.state.hitl.find((h) => h.status === 'pendente');
        if (!pendente) throw new Error('aguardandoHitl sem gate pendente na fila');
        gates.push(`${pendente.id}:${pendente.tipo}`);
        c.decidir(pendente.id, decisao, false);
        continue;
      }
      break;
    }
    if (guarda >= 1000) throw new Error('o laço da simulação não terminou');
  } finally {
    globalThis.setTimeout = setTimeoutReal;
    globalThis.clearTimeout = clearTimeoutReal;
  }

  return {
    componente: c,
    gates,
    concluido: c.state.concluido,
    rodando: c.state.rodando,
    i: c.state.i,
    total: c.cenarioAtiva().passos.length,
    eventos: c.state.eventos.length,
    natureza: c.state.natureza,
    rastreio: Object.keys(c.state.rastreio).length,
    plano: c.state.plano.map((p) => p.st),
  };
}

function checarMotor() {
  const finais = [];
  for (const cen of base.cenarios()) {
    for (const decisao of [true, false]) {
      const rot = decisao ? 'aprovar ' : 'rejeitar';
      let r;
      try {
        r = simular(cen.id, decisao);
      } catch (e) {
        falha(`${cen.id} (${rot}): ${e.message}`);
        continue;
      }
      if (!r.concluido) falha(`${cen.id} (${rot}): a simulação não chegou ao fim`);
      if (r.rodando) falha(`${cen.id} (${rot}): terminou com rodando=true`);
      if (r.i !== r.total) falha(`${cen.id} (${rot}): parou no passo ${r.i} de ${r.total}`);
      if (!r.natureza) falha(`${cen.id} (${rot}): natureza não foi definida`);
      for (const st of ['hitl', 'pendente']) {
        if (r.plano.includes(st)) {
          falha(`${cen.id} (${rot}): o plano terminou com passo em "${st}" — todo passo precisa ` +
            `chegar a ok ou rejeitado nos dois caminhos`);
        }
      }
      console.log(
        `  ${cen.id.padEnd(9)} ${rot} → ${String(r.eventos).padStart(2)} eventos · ` +
        `gates [${r.gates.join(' ') || '—'}] · rastreio ${r.rastreio}/${RASTREIO.size} · ` +
        `plano [${r.plano.join(',')}]`
      );
      finais.push({ cen: cen.id, decisao, r });
    }
  }
  return finais;
}

// ---------------------------------------------------------------------------
// 3. TEMPLATE — toda variável {{ }} usada existe nos dados
// ---------------------------------------------------------------------------

function lerTemplate() {
  // alias de sc-for → expressão da lista de origem
  const listas = new Map();
  for (const m of template.matchAll(/list="\{\{\s*([\w.]+)\s*\}\}"\s+as="(\w+)"/g)) {
    listas.set(m[2], m[1]);
  }
  // hint-placeholder-count declarado em cada sc-for
  const hints = new Map();
  for (const m of template.matchAll(/as="(\w+)"\s+hint-placeholder-count="(\d+)"/g)) {
    hints.set(m[1], Number(m[2]));
  }
  // toda interpolação usada
  const usadas = new Set();
  for (const m of template.matchAll(/\{\{\s*([A-Za-z_][\w.]*)\s*\}\}/g)) usadas.add(m[1]);

  const topo = new Set();
  const props = new Map(); // alias → Set de propriedades
  for (const u of usadas) {
    const [raiz, prop] = u.split('.');
    if (listas.has(raiz)) {
      if (!props.has(raiz)) props.set(raiz, new Set());
      if (prop) props.get(raiz).add(prop);
    } else if (raiz !== 'true' && raiz !== 'false') {
      topo.add(u.includes('.') ? raiz : u);
    }
  }
  return { listas, hints, topo, props };
}

/** Resolve a expressão de origem de um sc-for para os arrays que ele percorre. */
function resolverListas(expr, vals, listas) {
  if (!expr.includes('.')) {
    const v = vals[expr];
    return Array.isArray(v) ? [v] : [];
  }
  const [aliasPai, prop] = expr.split('.');
  const exprPai = listas.get(aliasPai);
  if (!exprPai) return [];
  const arrays = [];
  for (const arr of resolverListas(exprPai, vals, listas)) {
    for (const item of arr) {
      if (Array.isArray(item?.[prop])) arrays.push(item[prop]);
      else return []; // pai não expõe essa propriedade como lista — reportado em outro check
    }
  }
  return arrays;
}

function checarTemplate(estados) {
  const { listas, hints, topo, props } = lerTemplate();

  // as telas do sc-if precisam existir como flags em renderVals
  const flags = [...template.matchAll(/value="\{\{\s*(v[A-Z]\w*)\s*\}\}"/g)].map((m) => m[1]);
  const telas = [...template.matchAll(/data-screen-label="([^"]+)"/g)].map((m) => m[1]);
  if (flags.length !== telas.length) {
    falha(`o template tem ${telas.length} telas mas ${flags.length} flags de sc-if`);
  }
  const itensNav = base.renderVals.call(estados[0].comp).navItens.length;
  if (itensNav !== telas.length) {
    falha(`navItens tem ${itensNav} entradas mas o template tem ${telas.length} telas`);
  }

  for (const { rotulo, comp } of estados) {
    const vals = comp.renderVals();

    for (const nome of topo) {
      if (!(nome in vals)) falha(`${rotulo}: {{ ${nome} }} usado no template mas ausente em renderVals()`);
    }

    for (const [alias, expr] of listas) {
      const arrays = resolverListas(expr, vals, listas);
      if (!arrays.length && !expr.includes('.') && !(expr in vals)) {
        falha(`${rotulo}: sc-for percorre "${expr}", que renderVals() não devolve`);
        continue;
      }
      for (const arr of arrays) {
        for (const prop of props.get(alias) || []) {
          const faltante = arr.find((item) => !(prop in item));
          if (faltante) {
            falha(`${rotulo}: {{ ${alias}.${prop} }} não existe em algum item de "${expr}"`);
            break;
          }
        }
      }
    }
  }

  // hint-placeholder-count das listas estáticas (as que já têm itens no estado inicial)
  const valsIniciais = estados.find((e) => e.rotulo === 'estado inicial').comp.renderVals();
  let conferidos = 0;
  for (const [alias, expr] of listas) {
    if (expr.includes('.')) continue;
    const arr = valsIniciais[expr];
    if (!Array.isArray(arr) || arr.length === 0) continue; // lista dinâmica, cresce durante a simulação
    conferidos++;
    const hint = hints.get(alias);
    if (hint !== undefined && hint !== arr.length) {
      falha(`hint-placeholder-count de "${expr}" é ${hint} mas a lista tem ${arr.length} itens`);
    }
  }
  console.log(`  ${topo.size} variáveis de topo · ${listas.size} sc-for · ${conferidos} hints conferidos · ` +
    `${estados.length} estados avaliados`);
}

// ---------------------------------------------------------------------------
// 4. ESPELHO — export/ sincronizado com a fonte canônica
// ---------------------------------------------------------------------------

function checarEspelho() {
  let espelho;
  try {
    espelho = lf(readFileSync(ESPELHO, 'utf8'));
  } catch {
    falha('prototype/export/EasyRun-src.dc.html não encontrado');
    return;
  }
  const normalizado = espelho
    .replace('<script src="../support.js"></script>', '<script src="./support.js"></script>')
    .replace(/<template id="__bundler_thumbnail"[\s\S]*?<\/template>\n/, '');

  if (normalizado === html) {
    console.log('  export/ idêntico à fonte canônica (fora as 2 diferenças conhecidas)');
  } else {
    falha('export/EasyRun-src.dc.html divergiu da fonte canônica — rode: node tools/sync-export.mjs');
  }
}

// ---------------------------------------------------------------------------
// Execução
// ---------------------------------------------------------------------------

console.log('\n1. DADOS — consistência dos cenários');
checarDados();

console.log('\n2. MOTOR — cada cenário nos dois caminhos');
const execucoes = checarMotor();

console.log('\n3. TEMPLATE — variáveis usadas × dados disponíveis');
// avalia o template contra o estado inicial, contra cada gate e contra cada fim de cenário
const estados = [{ rotulo: 'estado inicial', comp: novoComponente() }];
for (const cen of base.cenarios()) {
  const temGate = cen.passos.some((p) => p.gate);
  if (temGate) {
    // reexecuta parando no primeiro gate
    const c = novoComponente(cen.id);
    c.setState = function (patch, cb) {
      const p = typeof patch === 'function' ? patch(this.state) : patch;
      this.state = { ...this.state, ...p };
      if (cb) cb();
    };
    const fila = [];
    const st = globalThis.setTimeout;
    const ct = globalThis.clearTimeout;
    globalThis.setTimeout = (fn) => fila.push(fn);
    globalThis.clearTimeout = () => {};
    try {
      c.iniciarPausar();
      let g = 0;
      while (g++ < 1000 && fila.length && !c.state.aguardandoHitl) fila.shift()();
    } finally {
      globalThis.setTimeout = st;
      globalThis.clearTimeout = ct;
    }
    estados.push({ rotulo: `${cen.id} no gate`, comp: c });
  }
}
for (const { cen, decisao, r } of execucoes) {
  estados.push({ rotulo: `${cen} ${decisao ? 'aprovado' : 'rejeitado'}`, comp: r.componente });
}
checarTemplate(estados);

console.log('\n4. ESPELHO — export/ × fonte canônica');
checarEspelho();

console.log('');
if (erros.length) {
  console.log(`${erros.length} problema(s):\n`);
  [...new Set(erros)].forEach((e) => console.log(`  ✗ ${e}`));
  console.log('');
  process.exit(1);
}
console.log('Protótipo verificado: sem problemas.\n');
