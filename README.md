# Squad Agentica em Python

Projeto Python (estrutura `src/` + testes com `pytest`). O pacote `squad_agentica`
tem um subpacote `aiops/` com os tipos/stubs (TypedDict `AgentState`, papéis
Planner/Explainer/Validator/Coach, mapa de remediação, governança de modelos) que
espelham a especificação de arquitetura AIOps — ainda sem lógica real de
LLM/LangGraph, só o contrato estrutural.

## Estrutura

```text
.
├── src/squad_agentica/
│   ├── serve.py            # servidor HTTP local para o prototype/
│   └── aiops/               # tipos/stubs espelhando a especificação AIOps
├── tests/                    # testes (pytest)
├── prototype/                 # mockup estático de UI (HTML/JS), não integrado ao backend
├── pyproject.toml
└── .gitignore
```

### `prototype/`

Contém um dashboard estático chamado "EasyRun — Squad Agêntica AIOps" (HTML/JS,
sem lógica Python), simulando 4 cenários de incidente com 6 agentes. Não é usado
pelo pacote `squad_agentica` — é só o mockup visual. Pontos a saber:

- `EasyRun.dc.html` é a fonte canônica. Carrega `support.js` (runtime gerado, com
  o comentário "GENERATED from dc-runtime/src/*.ts — do not edit"). O projeto-fonte
  `dc-runtime/` não faz parte deste repositório.
- `export/EasyRun-src.dc.html` é uma cópia espelhada de `EasyRun.dc.html` (só
  difere no path do `<script src>` e num `<template>` de thumbnail) — toda edição
  na fonte canônica deve ser replicada aqui.
- **`EasyRun - Standalone.html` está desatualizado** (bundle de 381KB, autocontido,
  não depende de `support.js`). Ele não reflete os 4 cenários nem os painéis novos
  (FinOps, mapa de remediação, telemetria) adicionados depois — a ferramenta de
  build que o gera (`dc-runtime/`) não está disponível neste repositório para
  regerá-lo. Use `squad-agentica-serve` (abaixo) para rodar a versão atual.
- `thumbnail.webp` é uma imagem de preview solta, sem referências no código.

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate          # Git Bash: source .venv/Scripts/activate
pip install -e ".[dev]"
```

## Testes

```bash
pytest
```

## Rodando o mockup localmente

Depois de instalar (o comando `squad-agentica-serve` é registrado como script do pacote):

```bash
squad-agentica-serve            # sobe http://localhost:8080 e abre o navegador
squad-agentica-serve --no-browser --port 8081   # sem abrir navegador, porta custom
```

No VS Code: pressione `F5` (task "Serve prototype" sobe o servidor e o Chrome
já abre em `http://localhost:8080/EasyRun.dc.html` com o debugger conectado).
