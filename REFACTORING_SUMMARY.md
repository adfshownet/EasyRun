# Refatoração de CSS Inline — EasyRun.dc.html

## Resultado final

- **Antes:** ~795 atributos `style="..."` inline; nenhum CSS externo.
- **Depois:** **22 atributos `style=` inline** — todos carregando exclusivamente valores
  dinâmicos interpolados (`{{ }}`) que não podem viver em CSS estático.
- **CSS externo:** `prototype/EasyRun.dc.css` (2331 linhas), carregado via
  `<link rel="stylesheet" href="./EasyRun.dc.css">` no `<helmet>`.

## Histórico honesto (correção de rota)

A primeira passada da refatoração (feita por scripts em lote) tentou converter os estilos
dinâmicos em classes `-dyn`, mas produziu **17 linhas com atributo `class` duplicado**
(ex.: `<div class="er-incident-badge" class="er-incident-badge-dyn">`). O parser HTML
descarta o segundo atributo, e a maioria dessas classes nem existia no CSS — resultado:
todo o estilo dinâmico (cores por agente, chip de incidente, nav ativo, severidade,
toggles) ficou morto.

A correção restaurou o padrão pretendido desde o início: **classe estática + custom
property inline** para o resíduo dinâmico. As expressões originais foram recuperadas do
commit `fb971a4` e mapeadas para as custom properties que o CSS já esperava.

## O padrão final

```html
<!-- HTML: classe carrega o estático, style carrega só o dinâmico -->
<div class="er-agent-card-dynamic" style="--ag-border: {{ ag.borda }};">
```

```css
/* CSS: consome a custom property */
.er-agent-card-dynamic { border: 1px solid var(--ag-border); }
```

Os 22 pontos restantes se dividem em:

- **17 com custom properties** (`--inc-*`, `--nv-*`, `--btn-*`, `--status-*`, `--ag-border`,
  `--bg-color`, `--bar-color`, `--nature-bg`, `--dot-color`, `--text-color`, `--avatar-bg`,
  `--agent-color`, `--track-color`, `--knob-left`, `--ref-border`/`--ref-color`) — o CSS
  define o resto da regra e consome a var. Custom properties herdam, então setar no pai
  (ex.: `.er-incident-badge`) alimenta os filhos (`.er-incident-status`, `.er-incident-id`).
- **5 com `color:` direto** (`er-severity-tag-dyn`, `er-agent-status-text-dyn`,
  `er-event-agent-dyn`, `er-plan-title-dyn`, `er-nature-label-dyn`) — cor única simples
  não justifica indireção por var.

O runtime `dc` suporta o padrão: `support.js` preserva chaves `--x` ao converter a string
de estilo em objeto React (`cssToObj`, que só camel-iza propriedades sem prefixo `--`).

## Estrutura do CSS

O arquivo tem duas regiões, resultado das passadas sucessivas:

1. **Seção organizada** (~l.1–2040): componentes nomeados (header, nav, console, chat,
   HITL, avaliação, configuração…). Contém alguns seletores paralelos que o HTML não usa
   (`.er-agent-card`, `.er-event-bar`, `.er-toggle`…) — candidatos a limpeza futura.
2. **Seção utilitária** (~l.2040+): classes granulares geradas nas últimas passadas
   (`er-flex-*`, `er-mono-*`, `er-tag-*`, e as classes que consomem custom properties).

## Espelho e verificação

- `tools/sync-export.mjs` reescreve **três** diferenças estruturais ao gerar
  `prototype/export/EasyRun-src.dc.html`: o `<script src>`, o `<link>` do CSS
  (`../EasyRun.dc.css`) e o `<template>` de thumbnail.
- `tools/check-prototype.mjs` normaliza as mesmas três diferenças ao comparar o espelho.
- Verificação: `node tools/sync-export.mjs && node tools/check-prototype.mjs` → 4 checks
  verdes (dados, motor, template, espelho).

## Nota sobre o linter

Os avisos "CSS inline styles should not be used" nos 22 pontos restantes são **falsos
positivos por design**: o valor é interpolado em runtime e não tem representação possível
em CSS estático. Não "consertar" esses avisos convertendo para classes — foi exatamente
esse atalho que quebrou o protótipo na primeira passada.
