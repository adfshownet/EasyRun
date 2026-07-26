# tools/

Ferramentas de verificação do protótipo. Node puro, **sem dependências** — não há
`package.json` e nada precisa ser instalado.

## `check-prototype.mjs`

```bash
node tools/check-prototype.mjs
```

Carrega a classe `Component` de [`prototype/EasyRun.dc.html`](../prototype/EasyRun.dc.html)
fora do navegador, com stubs mínimos de `React` e `DCLogic`, e roda quatro verificações:

| # | Verificação | O que pega |
|---|---|---|
| 1 | **Dados** | Passo apontando para agente ou status inexistente · `planoOk`/`planoUpdate` para um id que não está no plano · `rastreioSet` com chave fora da cadeia · gate sem campo obrigatório ou com tipo inválido · gate de PR sem `branch`/`checks`, de GMUD sem `janela`/`rollback` · id de gate duplicado · cenário sem natureza, sem `fim`, ou com elo de rastreio faltando |
| 2 | **Motor** | Roda os 8 cenários **nos dois caminhos** (aprovar e rejeitar) com `setState` e `setTimeout` falsos. Pega simulação que não termina, que para no meio, que fica com `rodando=true`, e — o caso que já apareceu de verdade — **passo do plano que fica em `hitl` ou `pendente`** porque só era resolvido no caminho de aprovação |
| 3 | **Template** | Toda `{{ variavel }}` usada existe no que `renderVals()` devolve, e toda `{{ alias.prop }}` existe nos itens da lista — avaliado no estado inicial, em cada gate e no fim de cada cenário · `navItens` bate com o número de telas · `hint-placeholder-count` bate com o tamanho real das listas estáticas |
| 4 | **Espelho** | `export/EasyRun-src.dc.html` está sincronizado com a fonte canônica |

Sai com código 1 se algo falhar. Roda no CI a cada mudança em `prototype/` ou `tools/`
(ver [`.github/workflows/prototype.yml`](../.github/workflows/prototype.yml)).

## `sync-export.mjs`

```bash
node tools/sync-export.mjs
```

Regenera [`prototype/export/EasyRun-src.dc.html`](../prototype/export/EasyRun-src.dc.html)
a partir da fonte canônica. O espelho difere em exatamente duas coisas, ambas estruturais:
o `<script src>` aponta para `../support.js` e há um `<template>` com o SVG de miniatura —
que o script preserva.

**Rode isto sempre que editar `prototype/EasyRun.dc.html`.** A verificação 4 acima existe
justamente para lembrar quando você esquecer.

## Por que Node e não pytest

O protótipo é JavaScript rodando num runtime (`dc`) que não está neste repositório.
Carregá-lo em Python exigiria reimplementar o interpretador; em Node, um `eval` com dois
stubs de dez linhas dá acesso à classe real — que é o que se quer verificar.

Os testes do pacote Python continuam em [`tests/`](../tests/), com `pytest`.
