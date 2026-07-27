# 01 — Visão geral

[← Índice](README.md) · [Próximo: Ambiente e ferramentas →](02-ambiente-e-ferramentas.md)

---

## O problema

Quando um sistema em produção quebra — a API de checkout fica lenta, um servidor satura,
o DNS para de responder — alguém precisa: perceber que quebrou, descobrir o porquê,
decidir o que fazer, executar a correção e depois escrever o que aprendeu.

Esse ciclo tem um nome e uma métrica: **MTTR** (*Mean Time To Repair*, tempo médio de
reparo). No material do protótipo, o número de referência para uma operação humana é
**38 minutos** por incidente. Trinta e oito minutos com o checkout lento é receita
perdida, cliente irritado e engenheiro acordado às 3h da manhã.

O agravante é que a maior parte desse tempo não é trabalho intelectual difícil — é
trabalho repetitivo: abrir o painel de métricas, correlacionar com o último deploy,
lembrar que "isso já aconteceu mês passado", achar o runbook, rodar o comando.

## A proposta: AIOps agêntica

**AIOps** = aplicar inteligência artificial às operações de TI.
**Agêntica** = em vez de um único modelo respondendo perguntas, um time de *agentes* —
programas que combinam um modelo de linguagem (LLM) com ferramentas reais e autonomia
para agir — dividindo o trabalho entre si.

O EasyRun propõe uma **squad de 8 agentes** que cobre o ciclo inteiro:

| Agente | Ícone | Papel | Analogia humana |
|---|---|---|---|
| **Maestro** | 🎼 | Orquestrador | O líder do plantão, que distribui as tarefas |
| **Sentinela** | 🛰️ | Detecção & triggers | Quem fica de olho nos painéis e dá o alarme |
| **Elo** | 🔗 | Rastreabilidade corporativa | Quem preenche o chamado, abre o card e a GMUD |
| **Contexto** | 🧠 | Contexto & memória | Quem lembra "isso já aconteceu no INC-1893" |
| **Diagnosta** | 🔬 | Causa raiz & natureza | O engenheiro que investiga e diz o que o caso exige |
| **Artífice** | 🛠️ | Código · Devin · PR | Quem escreve a correção e abre o pull request |
| **Executor** | ⚡ | Ações de infra | Quem digita os comandos |
| **Auditor** | 🛡️ | Guardrails & avaliação | Quem revisa, aprova e escreve o pós-mortem |

Definidos em [`agentesDef()`](../prototype/EasyRun.dc.html) — a tabela completa, com
plataformas, modelo e *skills* de cada um, está em
[04 — Frontend](04-frontend-prototype.md#os-8-agentes).

Três ideias sustentam a proposta e merecem destaque:

**1. Nem toda anomalia se resolve com infraestrutura.** Pode exigir mudança de código,
ajuste de configuração, ou estar fora do alcance da squad. Depois do diagnóstico, o
Diagnosta classifica a **natureza da remediação** — `INFRA`, `CODIGO`, `CONFIG` ou
`EXTERNO` — e é isso que decide o caminho da esteira, quem executa e qual é o artefato
final. Ver [10 — Natureza da remediação](10-ecossistema-da-empresa.md#a-natureza-da-remediação).

**2. Nem tudo pode ser automático.** Reverter um deploy em produção é irreversível o
suficiente para exigir um humano. A squad para, pede aprovação e só então age — é o
**HITL** (*Human-In-The-Loop*, humano no circuito). Quem decide o que exige aprovação são
os **guardrails**: regras explícitas que limitam a autonomia dos agentes. A regra que
resume a fronteira: **a squad abre a GMUD sozinha, mas nunca a aprova; gera o pull request,
mas nunca faz o merge.**

**3. Cada incidente resolvido deixa um aprendizado.** O Auditor grava o episódio na
memória de longo prazo, então o próximo incidente parecido já começa com a resposta
pronta — e o caso entra no conjunto de avaliação que julga as próximas versões dos agentes.

O fluxo completo, passo a passo, está em
[05 — Processo end-to-end](05-processo-end-to-end.md#b-ciclo-do-incidente-aiops).

### O ecossistema da empresa

O EasyRun se encaixa entre as plataformas que a empresa já usa, e é isso que o torna
apresentável internamente — quem assiste reconhece as próprias ferramentas na tela:

| Plataforma | Papel |
|---|---|
| **ServiceNow** | Registro: incidentes, CMDB (itens de configuração) e gestão de mudança (GMUD) |
| **Datadog** | Observabilidade: métricas, logs, traces e error tracking |
| **IUClick** | Kanban: o card de Bug que nasce e se move sozinho |
| **Devin** | Agente de código, quando a causa raiz está no software |
| **GitHub (org)** | Versionamento: onde o pull request nasce e é revisado |
| **AWS** | Onde o EasyRun roda — e onde parte, não toda, das ações acontece |

Detalhe de cada uma em [10 — Ecossistema da empresa](10-ecossistema-da-empresa.md).

## O que existe hoje

O repositório tem três coisas, e elas são bem diferentes entre si:

### 1. Um dashboard de demonstração (`prototype/`)

Um painel web de tela cheia, tema escuro, com 9 telas: console de orquestração, chat com
a squad, fila de aprovação HITL, avaliação/métricas, configuração, integrações, LLMOps,
FinOps e arquitetura. Ele simula **9 cenários** de incidente do começo ao fim, com log ao
vivo, plano de ação que avança passo a passo, cadeia de rastreabilidade que se preenche
elo a elo, e gates de aprovação que realmente pausam a simulação — o cenário de correção
de código para **duas vezes**, uma para o pull request e outra para a GMUD.

**É um mockup.** Não existe backend. Os 8 agentes, os 9 cenários, as métricas, o texto de
cada evento — está tudo escrito literalmente dentro do arquivo HTML. O "chat com a squad"
responde por correspondência de palavra-chave, não por LLM. Nenhuma chamada de rede sai
dali além do carregamento do React.

Isso não é um defeito: é exatamente o que um protótipo de alta fidelidade deve ser —
um instrumento para validar a experiência antes de gastar meses construindo o backend.
Só não pode ser apresentado como sistema funcionando.

Detalhes em [04 — Frontend / protótipo](04-frontend-prototype.md).

### 2. Um pacote Python com o contrato estrutural (`src/squad_agentica/aiops/`)

Dez módulos que definem os **tipos e as constantes** da arquitetura AIOps: o formato do
estado compartilhado (`AgentState`, agora com o bloco de rastreabilidade corporativa), as
classificações de severidade, origem e natureza da remediação, os papéis do grafo, o mapa
de remediação, as constantes de governança de modelos, as **portas das integrações**
(ServiceNow, Datadog, IUClick, Devin, GitHub), o contrato de observabilidade da esteira e
o de avaliação.

**É um stub** (esqueleto): toda classe de papel existe, tem docstring explicando o que
deveria fazer, e o corpo do método é `raise NotImplementedError` — "isto ainda não foi
implementado". Há testes que *garantem* que continue assim, travando o contrato.

Por que fazer isso? Porque congela as decisões de design (quais campos o estado tem, quais
papéis existem, quais valores de severidade são válidos) antes de escrever a lógica, e
torna a especificação executável — se alguém renomear um campo, o teste quebra.

Detalhes em [03 — Arquitetura do código](03-arquitetura-do-codigo.md#o-subpacote-aiops).

### 3. Um servidor local (`src/squad_agentica/serve.py`)

38 linhas de Python que sobem um servidor HTTP estático apontando para `prototype/`, para
você abrir o mockup no navegador com um comando. É o **único código do repositório que
executa trabalho real**. Detalhes em
[03 — Arquitetura do código](03-arquitetura-do-codigo.md#servepy--o-servidor-local).

Há ainda um script solto, [`validate_zip.py`](../validate_zip.py), sobrevivente de uma
fase anterior do projeto — ver [09 — Lacunas](09-lacunas-e-riscos.md#5-o-workflow-validate-zipyml-não-valida-nada).

## Quadro de maturidade

A tabela mais importante desta documentação. Use-a antes de qualquer apresentação:

| Componente | O que é hoje | O que seria em produção |
|---|---|---|
| Dashboard `prototype/` | **MOCKUP** — HTML estático, dados fixos, sem rede | Frontend Angular 18 consumindo API real |
| Os 8 agentes | **MOCKUP** — nomes e textos escritos à mão no HTML | Agentes LangGraph com LLM e ferramentas reais |
| Chat com a squad | **MOCKUP** — roteador de palavra-chave (`includes('causa')`) | Conversa com o Maestro via LLM |
| Métricas das abas Avaliação e LLMOps | **MOCKUP** — números fictícios fixos | Agregação real de Datadog, Langfuse e LangSmith |
| Integrações ServiceNow · Datadog · IUClick · Devin · GitHub | **CONTRATO** — portas tipadas (`Protocol`), sem SDK | Adaptadores reais na borda |
| `AgentState`, `Severity`, `RemediationKind`, `REMEDIATION_MAP` | **CONTRATO** — tipos e constantes válidos e testados | Os mesmos, agora efetivamente usados |
| Política de egresso (redação, allowlist) | **CONTRATO** — constantes travadas por teste | Aplicada de fato antes de cada chamada ao Devin |
| `Planner` / `Explainer` / `Validator` / `Coach` | **STUB** — `raise NotImplementedError` | Nós de raciocínio de um grafo LangGraph |
| `TraceabilityNode` (Elo) / `CodeRemediationNode` (Artífice) | **STUB** | Nós adaptadores com ferramentas |
| `classify_remediation` / `escalate` | **STUB** | Roteamento condicional do grafo |
| `CheckpointStore` | **STUB** | Persistência em PostgreSQL |
| `build_graph()` | **STUB** — nem importa `langgraph` | Grafo de estados completo |
| Avaliação (golden set, LLM-as-judge, shadow/canário) | **CONTRATO** — tipos e limiares definidos | Pipeline de promoção de versões |
| `serve.py` | **IMPLEMENTADO** ✅ | Substituído por um servidor de aplicação real |
| Testes (`pytest`) | **IMPLEMENTADO** ✅ — 25 testes, rodam no CI | Ampliados para a lógica real |
| CI de testes | **IMPLEMENTADO** ✅ | O mesmo, mais lint, cobertura e deploy |
| AWS, LangGraph, Langfuse, LangSmith | **PLANEJADO** — zero linha de código | A infraestrutura de verdade |

Legenda: **IMPLEMENTADO** = roda e faz o que promete · **CONTRATO** = tipos válidos, sem
comportamento · **STUB** = esqueleto que levanta erro se chamado · **MOCKUP** = aparência
sem substância · **PLANEJADO** = não existe.

## Como o nome se organiza

Um detalhe que confunde quem chega: **"EasyRun" é o nome do produto, mas o pacote Python
se chama `squad_agentica`.**

| Onde | Nome usado |
|---|---|
| Repositório e produto | EasyRun |
| Pacote Python / projeto no `pyproject.toml` | `squad-agentica` / `squad_agentica` |
| Comando de terminal | `squad-agentica-serve` |
| Arquivo do dashboard | `EasyRun.dc.html` |

O hífen vs. underscore não é aleatório: nomes de *distribuição* (o que você instala com
`pip`) usam hífen; nomes de *pacote* (o que você escreve depois de `import`) usam
underscore, porque hífen é operador de subtração em Python.

---

[← Índice](README.md) · [Próximo: Ambiente e ferramentas →](02-ambiente-e-ferramentas.md)
