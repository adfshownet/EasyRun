# 04 — Frontend / protótipo

[← Arquitetura do código](03-arquitetura-do-codigo.md) · [Índice](README.md) · [Próximo: Processo end-to-end →](05-processo-end-to-end.md)

---

> **MOCKUP.** Tudo descrito aqui é aparência e simulação. Não existe backend, não existe
> LLM, não existe AWS. Os dados são literais escritos dentro do HTML. Ver
> [01 — Quadro de maturidade](01-visao-geral.md#quadro-de-maturidade).

## Os arquivos da pasta

```
prototype/
├── EasyRun.dc.html            96 KB · 1163 linhas · ← A FONTE CANÔNICA
├── support.js                 66 KB · 1768 linhas · runtime gerado, não editar
├── export/
│   └── EasyRun-src.dc.html    97 KB · 1169 linhas · espelho manual
├── EasyRun - Standalone.html 381 KB ·  210 linhas · ⚠️ DESATUALIZADO
└── thumbnail.webp              9 KB · imagem órfã, sem referências
```

### Qual usar

**[`EasyRun.dc.html`](../prototype/EasyRun.dc.html)** — sempre esta. É a fonte canônica,
a que o `squad-agentica-serve` abre e a única que reflete o estado atual do protótipo.

**[`export/EasyRun-src.dc.html`](../prototype/export/EasyRun-src.dc.html)** — cópia
espelhada. A diferença é de exatamente duas linhas:

```diff
- <script src="./support.js"></script>
+ <script src="../support.js"></script>
+ <template id="__bundler_thumbnail" data-bg-color="#0B0F14">…</template>
```

Ou seja: o caminho do script (porque está um nível abaixo) e um `<template>` com um SVG de
miniatura. Todo o resto é byte a byte idêntico. ⚠️ Não há automação: qualquer edição na
fonte canônica precisa ser replicada aqui à mão. Ver
[09 — Lacunas #7](09-lacunas-e-riscos.md#7-o-export-é-espelho-manual).

**`EasyRun - Standalone.html`** — ⚠️ **não use.** É um bundle autocontido: 381 KB com os
recursos embutidos em base64, um indicador de "Unpacking…" e um script que desempacota
tudo antes de iniciar. A vantagem seria abrir sem servidor nenhum. O problema é que ele
**não reflete o estado atual**: foi gerado antes dos 4 cenários e dos painéis de FinOps,
mapa de remediação e telemetria. E não pode ser regerado, porque a ferramenta que o produz
(`dc-runtime/`) não está neste repositório.

**`thumbnail.webp`** — imagem de preview de 9 KB. Nenhum arquivo do repositório a
referencia.

---

## O runtime `dc` (`support.js`)

📄 [`prototype/support.js`](../prototype/support.js) — a primeira linha é um aviso:

```js
// GENERATED from dc-runtime/src/*.ts — do not edit. Rebuild with `cd dc-runtime && bun run build`.
```

Traduzindo: este arquivo é **código gerado** a partir de um projeto TypeScript chamado
`dc-runtime`, que **não faz parte deste repositório**. Editar `support.js` diretamente
significa perder a alteração no próximo build — e como o gerador não está disponível, não
há próximo build possível. Trate-o como uma caixa-preta somente-leitura.

### O que ele faz

`dc` é um pequeno framework de componentes declarativos. Ele permite escrever uma tela
inteira num único arquivo HTML, com o visual num template e a lógica numa classe
JavaScript, sem passo de compilação nem instalação de dependências.

**1. Carrega as bibliotecas da internet.** Três scripts, buscados do CDN unpkg:

| Biblioteca | Versão | Para quê |
|---|---|---|
| React | 18.3.1 | A biblioteca de interface — gerencia estado e re-renderização |
| ReactDOM | 18.3.1 | Coloca os componentes React na página |
| Babel standalone | 7.29.0 | Compila JavaScript moderno **no navegador**, em tempo de execução |

**CDN** (*Content Delivery Network*) é uma rede de servidores que hospeda arquivos
públicos. Usar CDN significa que o repositório não precisa versionar o React inteiro — mas
também que **o mockup exige internet para funcionar**.

Os carregamentos usam **SRI** (*Subresource Integrity*): um atributo `integrity` com o
hash criptográfico esperado do arquivo. O navegador baixa, calcula o hash e só executa se
bater. Se o CDN for comprometido e devolver um script adulterado, o navegador recusa.

**2. Interpreta o formato `.dc.html`.** O documento tem duas partes:

```html
<x-dc>
  ...o template visual, com {{ interpolações }}...
</x-dc>
<script type="text/x-dc" data-dc-script data-props="{...}">
  class Component extends DCLogic { ... }
</script>
```

- `<x-dc>` — o template. HTML normal, mais tags e sintaxes próprias.
- `<script data-dc-script>` — a lógica. **Obrigatoriamente** uma
  `class Component extends DCLogic` (o runtime valida e reclama se não for).
- `DCLogic` — a classe base, equivalente a `React.Component`.

**3. Estende o HTML com tags e atributos próprios:**

| Sintaxe | Função | Exemplo |
|---|---|---|
| `{{ expressão }}` | Interpola um valor vindo do `renderVals()` | `{{ relogio }}` |
| `<sc-for list="{{ x }}" as="item">` | Repete o bloco para cada item da lista | a lista de agentes |
| `<sc-if value="{{ cond }}">` | Renderiza o bloco só se a condição for verdadeira | as 7 telas |
| `<helmet>` | Conteúdo que vai para o `<head>` da página | fontes, `<title>`, CSS global |
| `style-hover="..."` | CSS aplicado no hover, sem folha de estilo | botões |
| `style-focus="..."` | CSS aplicado no foco | campos de texto |
| `data-screen-label="..."` | Rótulo da tela para ferramentas de design | `"Console de orquestração"` |

O `style-hover` existe porque todo o estilo do protótipo é *inline* (no atributo `style` de
cada elemento) e CSS inline não suporta pseudo-classes como `:hover`. O runtime resolve
isso gerando as regras nos bastidores.

**4. `data-props` — as propriedades editáveis.** Um JSON no atributo do `<script>` que
declara parâmetros ajustáveis por fora do código:

```json
{
  "velocidade":  { "editor": "range",   "default": 1,     "min": 0.5, "max": 3, "step": 0.5, "unit": "x", "tsType": "number",  "section": "Simulação" },
  "autoAprovar": { "editor": "boolean", "default": false,                                                 "tsType": "boolean", "section": "Simulação" }
}
```

| Prop | Efeito no protótipo |
|---|---|
| `velocidade` | Divisor do intervalo entre passos: `1900 / velocidade` milissegundos. Em `3x`, cada passo leva ~633 ms. |
| `autoAprovar` | Se `true`, o gate HITL se auto-aprova após um intervalo, em vez de esperar clique humano. Útil para demonstrar o fluxo sem interrupção. |

Elas são lidas em `this.props.velocidade` e `this.props.autoAprovar`.

O runtime também traz um modo de design que se comunica com uma janela-mãe via
`postMessage` (`__dc_design_mode`) e um sistema de recursos (`window.__resources`) — ambos
irrelevantes para rodar o protótipo localmente.

---

## Identidade visual

Definida no `<helmet>` do [`EasyRun.dc.html`](../prototype/EasyRun.dc.html):

**Tipografia** — duas famílias do Google Fonts:
- **Space Grotesk** (400–700) — geométrica, para a interface em geral;
- **IBM Plex Mono** (400–600) — monoespaçada, para dados técnicos: relógio, IDs de
  incidente, blocos de comando. Reforça a sensação de "terminal de operações".

**Paleta** — tema escuro, pensado para NOC/sala de operações:

| Papel | Cor |
|---|---|
| Fundo da página | `#0B0F14` |
| Painéis | `#10151C` / `#131A22` |
| Bordas | `#1E2833` |
| Texto (primário → terciário) | `#E8EEF4` · `#C7D2DC` · `#93A1B0` · `#5C6B7A` |
| Verde — sucesso, executor | `#3DDC84` |
| Ciano — vigilância, sentinela | `#4DD8E6` |
| Âmbar — atenção, aguardando humano | `#FFC24B` |
| Vermelho — crítico | `#FF6B6B` |
| Azul — informação, contexto | `#5BA8FF` |
| Roxo — maestro | `#B48CFF` |
| Rosa — auditor | `#FF8FAB` |

**Animações** — três `@keyframes`: `er-pulse` (pulsação de status ativo), `er-entrar`
(entrada suave de novos eventos no log), `er-girar` (rotação, para indicadores de trabalho
em curso).

O uso da cor é sistemático: cada agente tem cor fixa, e o estado dele muda entre "estático"
e "pulsando". Um olhar rápido no console basta para saber quem está trabalhando.

---

## Anatomia da UI: as 9 telas

Estrutura geral: **header** de 60 px no topo, **sidebar** de 184 px à esquerda, e uma área
principal onde apenas uma das 7 telas fica visível por vez (via `<sc-if>`).

**Header** — logo "E" em gradiente verde→ciano, o nome EasyRun, o *chip de incidente*
(muda de cor e pulsa conforme o estado: verde "Sistemas nominais" → vermelho pulsante
durante o incidente → âmbar "Aguardando humano" → verde na conclusão), os botões
▶/⏸ e ↺ Reiniciar, e um relógio.

O relógio começa em `50531` segundos = **14:02:11** e avança de 12 a 42 segundos por passo
(`12 + Math.floor(Math.random() * 30)`) — o aleatório dá textura de tempo real.

| # | Tela | Nav | O que mostra |
|---|---|---|---|
| 1 | **Console de orquestração** | 🎼 Console | A tela principal. Três colunas: seletor de cenário + cards dos 8 agentes · log de eventos ao vivo · plano de ação + memória + **natureza da remediação** + **rastreabilidade** + guardrails |
| 2 | **Chat com a squad** | 💬 Chat da squad | Conversa com o "Maestro" |
| 3 | **Fila de aprovação HITL** | ✋ Aprovações HITL | Cards de aprovação pendente, com layout específico por **tipo de gate** (ação, PR, GMUD), e histórico de decisões. O item do menu ganha um **badge** com a contagem de pendentes |
| 4 | **Avaliação e métricas** | 📊 Avaliação | 6 tiles de métrica, distribuição por natureza da remediação, gráfico por dia da semana, scores por agente, tabela de anomalias recentes |
| 5 | **Configuração** | ⚙️ Configuração | Agentes e skills, guardrails, triggers, mapa de remediação, telemetria e **política de código** |
| 6 | **Integrações** | 🔌 Integrações | Uma linha por plataforma do ecossistema, com o que a squad lê, o que escreve e o modo (automático ou HITL) |
| 7 | **LLMOps** | 🔭 LLMOps | A stack Lang* e os nove conceitos de observabilidade da própria esteira |
| 8 | **FinOps** | 💰 FinOps | 6 cards de política de governança de modelos |
| 9 | **Arquitetura** | 🏗️ Arquitetura | Os 13 pilares, stack-alvo, **arquitetura de integração**, hardening, mapa EasyRun↔LangGraph |

Uma observação sobre a tela 5: os toggles de guardrail **realmente alternam** o estado
(`this.setState`) e agora se refletem no painel de guardrails do console, mas não alteram o
comportamento da simulação — os gates estão fixos nos dados de cada cenário. É controle
visual, não funcional.

---

## Os 8 agentes

Definidos em `agentesDef()`, uma lista estática. A ordem da lista é a ordem em que eles
aparecem no fluxo:

| Agente | Papel | Cor | Plataformas | Modelo | Skills |
|---|---|---|---|---|---|
| 🎼 **Maestro** | Orquestrador | `#B48CFF` | Step Functions, LangGraph | Bedrock · Claude Sonnet | `decompor-tarefas`, `rotear-por-natureza`, `consolidar-resultado` |
| 🛰️ **Sentinela** | Detecção & triggers | `#4DD8E6` | Datadog, ServiceNow, EventBridge | Regras + Bedrock Haiku | `detectar-anomalia`, `classificar-severidade`, `monitorar-recuperacao` |
| 🔗 **Elo** | Rastreabilidade corporativa | `#7FD4A8` | ServiceNow, IUClick | Determinístico + Haiku | `consultar-cmdb`, `abrir-bug`, `iniciar-gmud`, `mover-kanban`, `escalar-time` |
| 🧠 **Contexto** | Contexto & memória | `#5BA8FF` | OpenSearch, DynamoDB | Bedrock · Titan Embeddings | `buscar-runbooks`, `recuperar-incidentes`, `gravar-aprendizado` |
| 🔬 **Diagnosta** | Causa raiz & natureza | `#FFC24B` | Bedrock, Datadog | Bedrock · Claude Sonnet | `correlacionar-sinais`, `hipoteses-causa-raiz`, `classificar-natureza` |
| 🛠️ **Artífice** | Código · Devin · PR | `#E8A87C` | Devin, GitHub org | Devin + Bedrock Sonnet | `clonar-repositorio`, `analisar-codigo`, `delegar-devin`, `abrir-pr` |
| ⚡ **Executor** | Ações de infra | `#3DDC84` | Lambda, SSM | **Determinístico** | `rollback-deploy`, `escalar-recursos`, `executar-runbook` |
| 🛡️ **Auditor** | Guardrails & avaliação | `#FF8FAB` | S3, Langfuse, Datadog | Bedrock · Claude Haiku | `validar-guardrails`, `avaliar-execucao`, `pos-mortem` |

Três escolhas de design valem ser notadas, porque revelam pensamento arquitetural real:

**O Executor não usa modelo — é "Determinístico".** É um dos dois agentes que **mudam o
mundo**: reverte deploys, escala instâncias. Deixar um LLM decidir os parâmetros dessa
chamada introduz não-determinismo exatamente onde ele é menos tolerável. O raciocínio fica
com o Diagnosta; o Executor apenas executa o que foi decidido.

**Elo e Artífice são adaptadores, não raciocinadores.** Na tela são agentes — é assim que a
squad se apresenta e é o que o público reconhece. No grafo LangGraph, são nós que usam
ferramentas; os papéis de raciocínio continuam sendo os quatro da especificação. Ver
[03 — roles.py](03-arquitetura-do-codigo.md#rolespy).

**Modelos diferentes por agente.** Sonnet (mais capaz, mais caro) para raciocínio —
Maestro e Diagnosta. Haiku (mais rápido, mais barato) para classificação e verificação —
Sentinela e Auditor. Titan Embeddings, que não gera texto, para busca semântica —
Contexto. É otimização de custo por tarefa, coerente com a aba FinOps.

### Estados do agente

Cada card mostra o status atual, mapeado em `statusInfo()` para uma cor e uma animação:

| Status | Cor | Animação |
|---|---|---|
| `ocioso` | cinza `#5C6B7A` | nenhuma |
| `vigiando` | ciano | pulso lento (2 s) |
| `detectando` | âmbar | pulso rápido (1,2 s) |
| `orquestrando` | roxo | pulso rápido |
| `buscando` | azul | pulso rápido |
| `analisando` | âmbar | pulso rápido |
| `executando` | verde | pulso rápido |
| `monitorando` | rosa | pulso lento |
| `aguardando` | âmbar | pulso médio (1,6 s) |
| `concluído` | verde | nenhuma |
| `consultando` · `registrando` | verde-menta (Elo) | pulso rápido |
| `clonando` · `delegando` | laranja (Artífice) | pulso rápido |
| `escalando` | âmbar | pulso rápido |

O estado inicial já traz a Sentinela em `vigiando` e todos os outros em `ocioso` — a
metáfora é a de um plantão: alguém sempre de olho, o resto em espera.

---

## Os 7 cenários

| ID | Título | Severidade · Algoritmo | Origem | Natureza | Gates HITL | Passos |
|---|---|---|---|---|---|---|
| `anm2047` | 🐢 Latência checkout-api | Crítico · Robust | Datadog | `INFRA` | APR-01 (ação) | 17 |
| `anm2091` | 📈 CPU Spike — catalog-svc | Alerta · Agile | Datadog | `INFRA` | APR-02 (ação) | 17 |
| `anm2118` | 🌐 DNS Timeout — endpoint novo | Crítico · Basic | Datadog | `INFRA` | — autônomo | 16 |
| `prd2144` | 🔮 Previsão de exaustão de disco | Preditivo · Robust | Agendado | `INFRA` | — autônomo | 16 |
| `inc3312` | 🧬 **Erro no cálculo de frete** | Crítico · Robust | Datadog + ServiceNow | **`CODIGO`** | **APR-03 (PR) + APR-04 (GMUD)** | 23 |
| `inc3350` | 💼 **Faturamento não conciliado** | Crítico · Agile | **ServiceNow** | **`CONFIG`** | APR-05 (GMUD) | 18 |
| `inc3377` | ⛔ **Gateway de pagamento degradado** | Alerta · Agile | Datadog | **`EXTERNO`** | APR-06 (ação) | 16 |

123 passos no total. A seleção do cenário só é permitida com a simulação parada
(`escolherCenario` retorna imediatamente se `this.state.rodando`).

O conjunto cobre os três níveis de severidade, os três algoritmos de detecção, as quatro
naturezas de remediação, os três tipos de gate e as três origens de estímulo. Os três
últimos são os que aproximam o protótipo da realidade da empresa:

**`inc3312` é o carro-chefe.** Único cenário que percorre a cadeia de rastreabilidade
inteira (9 de 9 elos) e o único com **dois gates**: o pull request gerado pelo Devin e a
GMUD. Se o PR for rejeitado, o gate da GMUD nem aparece — não faz sentido pedir janela de
mudança para um patch recusado.

**`inc3350` sai da AWS.** Origem é o ServiceNow (volume de chamados, não métrica), o
sistema é um ERP on-premises e a ação final é uma mudança de configuração sob GMUD. Existe
para mostrar que a squad trata o que não está na nuvem.

**`inc3377` demonstra desistir.** A squad identifica o limite da própria autonomia e
escala ao fornecedor. Rejeitar é o caminho interessante aqui — mas aprovar também funciona,
porque o simulador nunca força a mão do operador.

Análise completa em
[05 — Processo end-to-end](05-processo-end-to-end.md#comparando-os-7-cenários).

---

## O motor de simulação

Tudo dentro de `class Component extends DCLogic`, a partir da linha 561 do
[`EasyRun.dc.html`](../prototype/EasyRun.dc.html).

### O estado

`estadoInicial()` devolve o objeto que o React gerencia:

| Campo | Tipo | Papel |
|---|---|---|
| `view` | string | Qual das 7 telas está visível |
| `rodando` | bool | Simulação em andamento |
| `concluido` | bool | Cenário chegou ao fim |
| `i` | int | Índice do próximo passo — o "cursor" da simulação |
| `relogio` | int | Segundos desde a meia-noite (começa em 50531 = 14:02:11) |
| `eventos` | array | O log acumulado |
| `agStatus` | objeto | Status de cada um dos 6 agentes |
| `plano` | array | Os passos do plano de remediação e seus estados |
| `memorias` | array | Runbooks/episódios recuperados |
| `hitl` | array | Gates, pendentes e decididos |
| `rejeitado` | bool | Se o humano rejeitou — muda o texto dos passos seguintes |
| `aguardandoHitl` | bool | Simulação pausada esperando decisão |
| `natureza` | string \| null | `infra` · `codigo` · `config` · `externo` — definida pelo Diagnosta |
| `rastreio` | objeto | A cadeia de rastreabilidade, preenchida elo a elo |
| `escalado` | bool | Se o incidente foi devolvido ao time dono |
| `cenarioAtivo` | string | ID do cenário selecionado |
| `chat`, `chatInput`, `digitando` | — | Estado do chat |
| `guardrails` | objeto | Toggles `g1`–`g5` (g4 começa desligado) |

### O laço: `agendar()` → `tique()`

```js
duracao() { return 1900 / (this.props.velocidade ?? 1); }

agendar() {
  clearTimeout(this.timer);
  this.timer = setTimeout(() => this.tique(), this.duracao());
}
```

O `??` é o operador *nullish coalescing*: usa `1` se `velocidade` for `null`/`undefined`.
Em velocidade `1x`, cada passo leva 1,9 segundo.

O `tique()` faz cinco coisas:

1. Pega o passo em `passos[this.state.i]`.
2. Decide o texto: normalmente `p.txt`, mas se o passo tiver `dinamico`, escolhe entre
   `dinamico.aprovado` e `dinamico.rejeitado` conforme `this.state.rejeitado`.
3. Monta o evento (hora formatada, nome e cor do agente, pilar, serviço AWS, texto) e o
   acrescenta ao log.
4. Aplica os efeitos colaterais do passo (o objeto `fx`).
5. No *callback* pós-`setState`: se o passo tinha `gate`, **para** (a menos que
   `autoAprovar` esteja ligado); senão, agenda o próximo.

### O schema de um passo

Cada elemento de `cenario.passos`:

```js
{
  ag: 'diagnosta',                    // qual agente
  pilar: '🎯 Planning',               // qual dos 13 pilares
  aws: 'Bedrock',                     // plataforma mostrada no log
  txt: 'Causa provável: ...',         // texto fixo
  dinamico: { aprovado: '…', rejeitado: '…' },  // OU texto que depende da decisão
  fx: { ... },                        // efeitos colaterais no estado
  gate: { ... },                      // se presente, PAUSA a simulação
  pularSeRejeitado: true,             // passo que só existe no caminho de aprovação
  fim: true                           // se presente, encerra o cenário
}
```

**`pularSeRejeitado`** é o mecanismo que mantém o caminho de rejeição coerente: se o
operador recusou o pull request, não faz sentido pedir a GMUD nem fazer o merge. O `tique()`
avança o índice e segue adiante sem escrever nada no log — o passo simplesmente não
aconteceu.

### `fx` — os efeitos colaterais

| Chave | Efeito |
|---|---|
| `agStatus` | Mescla novos status nos agentes: `{...s.agStatus, ...p.fx.agStatus}` |
| `planoCriar` | **Substitui** o plano inteiro pela lista dada — é como o plano nasce |
| `planoUpdate` | Atualiza um passo, com valores distintos para `stAprovado` e `stRejeitado` |
| `planoOk` | Marca o passo de id N como `'ok'` |
| `memoriaAdd` | Acrescenta uma ou mais memórias (aceita objeto único ou array) |
| `rastreioSet` | Preenche um ou mais elos da cadeia de rastreabilidade |
| `naturezaSet` | Define a natureza da remediação — o que roteia o resto da esteira |
| `escalar` | Marca o incidente como devolvido ao time dono |

Estados de um passo do plano, com o ícone correspondente:

| Estado | Ícone | Cor | Legenda |
|---|---|---|---|
| `ok` | ✅ | verde | concluído |
| `hitl` | ✋ | âmbar | aguardando aprovação |
| `pendente` | ⏳ | cinza | pendente |
| `rejeitado` | 🚫 | vermelho | rejeitado — mitigação alternativa |

### `gate` — a pausa para o humano

Quando um passo tem `gate`, o `tique()` define `aguardandoHitl: true` e acrescenta o gate à
fila `hitl` com status `'pendente'`. Como o callback não chama `agendar()`, **o laço
morre** — a simulação fica congelada até alguém decidir.

O objeto do gate:

```js
gate: {
  id: 'APR-01',
  tipo: 'acao',                       // 'acao' | 'pr' | 'gmud'
  titulo: 'Rollback de deploy em produção',
  descricao: '...',
  risco: 'médio',
  guardrail: 'G-02 · rollback exige humano',
  aws: 'Lambda · CodeDeploy',
  detalhe: '$ easyrun executar rollback \\\n    --servico checkout-api ...',
  mensagemAprovado: '...',
  mensagemRejeitado: '...',
  mensagemAutoAprovado: '...',
}
```

**Os três tipos de gate** têm campos próprios, renderizados por `sc-if` no template:

| `tipo` | Campos extras | Onde aparece |
|---|---|---|
| `acao` | — | APR-01, APR-02, APR-06 |
| `pr` | `repositorio`, `branch`, `arquivos`, `checks` | APR-03 |
| `gmud` | `gmud`, `ci`, `janela`, `rollback` | APR-04, APR-05 |

A separação existe porque as três decisões pedem informações diferentes: para aprovar um
patch você quer ver o diff e os checks de CI; para aprovar uma GMUD você quer ver a janela
e o plano de rollback.

O `detalhe` é o bloco monoespaçado que aparece no card: o comando que seria executado,
mais a justificativa do Diagnosta e a memória que sustenta a decisão. É a informação que o
humano precisa para decidir com um clique em vez de abrir cinco abas — uma boa escolha de
produto.

`decidir(id, aprovado, automatico)` retoma o fluxo: marca o gate como aprovado/rejeitado,
grava `rejeitado: !aprovado`, adiciona ao log um evento atribuído a **"Operador humano"**
ou **"Auto-aprovação"**, avança o relógio em 8 segundos e chama `agendar()`.

O efeito de `rejeitado` se propaga: os passos com `dinamico` passam a usar o texto
alternativo, e o `planoUpdate` aplica `stRejeitado`. No ANM-2047, rejeitar o rollback faz
o Executor "reciclar as instâncias do pool sem reverter o deploy" e o passo 2 do plano
fica 🚫. É um segundo caminho completo, não uma mensagem de erro.

### Auto-aprovação

Se a prop `autoAprovar` estiver ligada, o callback agenda
`decidir(gate.id, true, true)` após um intervalo — a simulação nunca para. O log registra a
`mensagemAutoAprovado`, deixando claro que a decisão foi da máquina.

---

## O chat não é um LLM

`responderChat(texto)` é um roteador de palavra-chave. Ele passa o texto para minúsculas e
testa `includes` numa ordem fixa:

| Palavra-chave | Resposta |
|---|---|
| `causa` | Explicação da causa raiz do cenário ativo |
| `status` ou `situa` | Varia conforme o estado: concluído / aguardando HITL / ativo / nenhum incidente |
| `plano` | Os passos do plano do cenário |
| `memó`, `memo`, `hist` | Explica as duas camadas de memória (DynamoDB + OpenSearch) |
| `natureza`, `roteam` | A natureza classificada, ou as quatro possíveis se ainda não houver |
| `rastre`, `correla` | Lê o estado real e lista os elos já preenchidos da cadeia |
| `pr`, `pull`, `devin`, `código` | O caminho do Artífice, com repo/sessão/PR reais se já existirem |
| `gmud`, `mudan` | A GMUD do incidente, e a fronteira "abre sozinha, aprova nunca" |
| `bug`, `iuclick`, `kanban`, `card` | O card do IUClick e como ele se move |
| `servicenow`, `cmdb`, `incidente` | O papel do ServiceNow e por que a CMDB é decisiva |
| `datadog`, `observab`, `telemetr` | A observabilidade dos sistemas, e o ponteiro para LLMOps |
| `escal` | Por que desistir com segurança é um resultado |
| `agente`, `squad`, `quem` | Apresenta os 8 agentes |
| `guardrail`, `segur`, `aprova` | Lista os guardrails ativos, incluindo G-05, G-06 e G-07 |
| `mttr`, `tempo`, `métri` | Os números da aba Avaliação |
| `cenário`, `cenario` | Descreve os 7 cenários |
| *(nenhuma)* | Menu de fallback |

A ordem importa: a primeira correspondência vence. E há um cuidado de coerência — várias
rotas **leem o estado real** antes de responder: perguntar "qual a causa?" antes de iniciar
a simulação responde *"Ainda não há anomalia em análise"*, e perguntar pela rastreabilidade
no meio de um incidente lista os elos que já foram preenchidos, não um texto genérico.

O delay de digitação é `setTimeout(..., 900)` em `enviarChat()` — 900 ms fixos, com um
indicador "digitando" no intervalo. Puro teatro, e eficaz.

---

## Os dados são todos literais

Não há nenhum arquivo JSON, nenhuma API, nenhuma chamada `fetch`. Tudo — os 6 agentes, os
4 cenários com seus ~54 passos, as métricas, os 13 pilares, os guardrails, os triggers, as
fontes de telemetria, os cards de FinOps — está escrito como literal JavaScript dentro do
`EasyRun.dc.html`.

Os conjuntos estáticos montados em `renderVals()`:

| Variável | Conteúdo |
|---|---|
| `metricas` | MTTR médio 6m 12s (−71%) · Resolução autônoma 84% · Acerto da natureza 96% · PR aceito na 1ª revisão 78% · Tempo até GMUD 48s · Custo LLM/incidente US$ 0,84 |
| `naturezaResumo` | 48 incidentes: INFRA 31 (65%) · CÓDIGO 9 (19%) · CONFIG 5 (10%) · EXTERNO 3 (6%) |
| `barrasDados` | 7 dias: seg 6/2 · ter 4/1 · qua 8/2 · qui 5/3 · sex 9/1 · sáb 3/0 · dom 2/1 (autônomo/humano). Altura da barra = `valor/10 × 130 px` |
| `scores` | maestro 94 · sentinela 97 · elo 98 · contexto 89 · diagnosta 91 · artifice 86 · executor 99 · auditor 95 |
| `historicoAnm` | 4 anomalias anteriores (ANM-2043 a 2046) com resolução, MTTR e score |
| `grDefs` | **5** guardrails (ver [05](05-processo-end-to-end.md#os-guardrails)) |
| `triggersLista` | 5 gatilhos: monitor do Datadog · incidente do ServiceNow · deploy · varredura de 15 min · pedido humano |
| `remediacaoLista` | Espelho do `REMEDIATION_MAP` do Python ⚠️ — agora com as 7 entradas e a natureza |
| `telemetriaLista` | Datadog APM · Datadog Logs/Error Tracking · ServiceNow · CloudWatch · sistemas on-premises |
| `politicaCodigo` | 5 regras de proteção do repositório ao delegar ao Devin |
| `integracoesLista` | 6 plataformas com o que a squad lê, escreve e o modo |
| `llmopsCards` | Os 9 conceitos de LLMOps |
| `llmopsStack` | LangGraph · LangChain · Langfuse · LangSmith · Datadog LLM Obs. |
| `finopsCards` | Espelho do `governance.py` ⚠️ — mais o custo por natureza |
| `hardeningItens` | 6 itens de robustez para produção |
| `mapaLangGraph` | O mapeamento dos 4 papéis **+ os 2 nós adaptadores** |
| `pilares` | Os 13 pilares agênticos |

**⚠️ Todos esses números são fictícios**, inventados para a demonstração. Nenhum vem de
medição real. Ao apresentar, diga isso.

E as duas linhas marcadas com ⚠️ são cópias manuais de constantes que também existem no
Python — a mesma informação em dois lugares que não se sincronizam. Ver
[09 — Lacunas #1](09-lacunas-e-riscos.md#1-fonte-da-verdade-duplicada-entre-python-e-html).

---

## Como editar o protótipo

1. Suba o servidor: `squad-agentica-serve --no-browser` (ou F5 no VS Code).
2. Edite [`prototype/EasyRun.dc.html`](../prototype/EasyRun.dc.html).
3. Recarregue o navegador — o `Cache-Control: no-store` do
   [`serve.py`](../src/squad_agentica/serve.py) garante que você veja a versão nova.
4. **Replique a mudança** em
   [`prototype/export/EasyRun-src.dc.html`](../prototype/export/EasyRun-src.dc.html),
   preservando o `<script src="../support.js">` e o `<template>` do thumbnail.
5. Não toque no `support.js`.

Não há testes automatizados cobrindo o protótipo: a verificação é visual.

---

[← Arquitetura do código](03-arquitetura-do-codigo.md) · [Índice](README.md) · [Próximo: Processo end-to-end →](05-processo-end-to-end.md)
