# 08 — Glossário

[← CI/CD e Git](07-ci-cd-e-git.md) · [Índice](README.md) · [Próximo: Lacunas e riscos →](09-lacunas-e-riscos.md)

---

Todos os termos técnicos que aparecem no EasyRun, em ordem alfabética, com link para onde
o assunto é tratado a fundo.

## A

**A2A (Agent-to-Agent)** — Protocolo para que agentes construídos em frameworks diferentes
se descubram e conversem, via um *Agent Card* publicado em `.well-known/agent-card.json`.
Pilar 13. → [06](06-arquitetura-alvo.md#os-13-pilares-agênticos)

**Agent Card** — Documento publicado em `.well-known/agent-card.json` que descreve as
capacidades de um agente para que outros o descubram. Base do protocolo A2A.

**Agente** — Programa que combina um modelo de linguagem, um conjunto de ferramentas e
alguma autonomia para agir em direção a um objetivo. Diferente de um chatbot, ele *executa*
ações. O EasyRun propõe 6. → [04](04-frontend-prototype.md#os-8-agentes)

**AgentState** — O `TypedDict` de 13 campos que carrega todo o contexto de um incidente
entre os nós do grafo. É o contrato central da arquitetura.
→ [03](03-arquitetura-do-codigo.md#statepy)

**Allowlist de repositórios** — Lista explícita dos repositórios que podem ser enviados ao
agente de código externo. Constante `REPOSITORY_ALLOWLIST_REQUIRED`, travada por teste.
→ [10](10-ecossistema-da-empresa.md#a-política-de-código)

**AIOps** — *Artificial Intelligence for IT Operations*. Aplicar IA à operação de
infraestrutura: detectar anomalias, diagnosticar causas, remediar automaticamente.
→ [01](01-visao-geral.md)

**Ambiente virtual (venv)** — Instalação isolada e privada do Python para um projeto, na
pasta `.venv/`. Impede que as dependências de projetos diferentes colidam.
→ [02](02-ambiente-e-ferramentas.md#venv--o-ambiente-virtual)

**Ambiente on-premises** — Sistema hospedado em datacenter próprio, fora da nuvem. O
EasyRun trata incidentes nesses sistemas pela API do próprio sistema — o cenário INC-3350.

**Anomalia** — Desvio de comportamento esperado numa métrica. No EasyRun recebe um ID
(`ANM-2047`), uma severidade e um algoritmo de detecção.

**ASG (Auto Scaling Group)** — Serviço AWS que mantém automaticamente um número desejado de
instâncias EC2, adicionando ou removendo conforme a demanda. É a ação de remediação para
`cpu_spike`.

**assert** — Instrução Python que levanta erro se a condição for falsa. É como o `pytest`
expressa uma verificação de teste.

## B

**Babel** — Compilador JavaScript. O protótipo usa a versão *standalone*, que compila no
próprio navegador em tempo de execução, dispensando build.
→ [04](04-frontend-prototype.md#o-runtime-dc-supportjs)

**Barramento de eventos** — Canal onde componentes publicam fatos e outros se inscrevem
para reagir, sem se conhecerem diretamente. No EasyRun, o EventBridge.
→ [05](05-processo-end-to-end.md#2--evento-no-barramento)

**Baseline** — O padrão de comportamento normal de uma métrica, contra o qual o desvio é
medido. Métricas novas não têm baseline, o que obriga o uso do algoritmo `BASIC`.

**Bedrock** — Serviço AWS de modelos de linguagem gerenciados (Claude, Titan e outros),
sem necessidade de gerenciar infraestrutura de GPU.

**Bounded context** — Conceito de DDD: fronteira dentro da qual cada termo do domínio tem
um significado único. Os quatro propostos: Detecção, Diagnóstico, Execução, Governança.
→ [06](06-arquitetura-alvo.md#backend--python)

**Bug (card de)** — O item que o EasyRun cria no IUClick para cada incidente, e move no
kanban conforme o desfecho. → [10](10-ecossistema-da-empresa.md#iuclick)

**Bytecode** — Forma intermediária compilada de um `.py`, guardada em `__pycache__/`.
Otimização de tempo de carga. → [02](02-ambiente-e-ferramentas.md#__pycache__-e-pytest_cache--caches)

## C

**Cache-Control** — Cabeçalho HTTP que instrui o navegador sobre armazenar ou não a
resposta. O `serve.py` envia `no-store` para que edições no protótipo apareçam sem F5
forçado. → [03](03-arquitetura-do-codigo.md#servepy--o-servidor-local)

**Canário (canary)** — Modo de rollout em que a versão nova age sobre uma fatia pequena e
delimitada dos incidentes, antes de assumir todo o tráfego.
→ [11](11-mlops-llmops.md#5-shadow-mode-e-canário)

**Callable class** — Classe que define `__call__`, podendo ser invocada como função. É a
forma como os papéis do grafo são declarados.
→ [03](03-arquitetura-do-codigo.md#rolespy)

**CDN (Content Delivery Network)** — Rede de servidores que hospeda arquivos públicos. O
protótipo busca React e Babel do CDN unpkg — por isso precisa de internet.

**Checkpoint** — Fotografia durável do estado num instante, para permitir retomar dali em
caso de falha. Crítico quando as ações já executadas são irreversíveis.
→ [03](03-arquitetura-do-codigo.md#checkpointpy)

**CI/CD** — *Continuous Integration / Continuous Delivery*. Verificação automática de cada
mudança (CI) e publicação automática do que passou (CD). Este projeto tem só CI.
→ [07](07-ci-cd-e-git.md#o-que-é-cicd)

**Circuit breaker** — Padrão que interrompe as tentativas de chamar um serviço após N
falhas seguidas, evitando *retry storms* contra um sistema já saturado. Item de hardening.
→ [06](06-arquitetura-alvo.md#hardening-para-produção)

**CI (Configuration Item)** — Item de configuração: como a CMDB do ServiceNow inventaria
cada serviço, servidor ou integração. É o CI que diz qual time é dono e qual repositório
sustenta o serviço. → [10](10-ecossistema-da-empresa.md#servicenow)

**CMDB (Configuration Management Database)** — O inventário de itens de configuração do
ServiceNow. Para o EasyRun é a fonte que liga um incidente ao serviço, ao time dono e ao
repositório de código.

**CloudWatch** — Serviço AWS de métricas, logs e alarmes. É a fonte de telemetria da
Sentinela.

**Console script (entry point)** — Mecanismo do empacotamento Python que transforma uma
função num comando de terminal. Declarado em `[project.scripts]`, gera
`squad-agentica-serve`. → [02](02-ambiente-e-ferramentas.md#projectscripts)

**Confiança (confidence)** — Grau de certeza que o Diagnosta atribui ao diagnóstico. Nos
cenários varia de 89% a 95%. Campo `confidence` do `AgentState`.

## D

**Datadog** — Plataforma de observabilidade da empresa: métricas, logs, traces APM, error
tracking, monitores sintéticos e forecast. Principal fonte de gatilhos.
→ [10](10-ecossistema-da-empresa.md#datadog)

**dataclass** — Decorador Python que gera automaticamente `__init__`, `__repr__` e `__eq__`
de uma classe que só carrega dados. Com `frozen=True`, torna as instâncias imutáveis.
→ [03](03-arquitetura-do-codigo.md#remediationpy)

**DDD (Domain-Driven Design)** — Abordagem que modela o software na linguagem do negócio,
organizado em *bounded contexts*. → [06](06-arquitetura-alvo.md#backend--python)

**DeepEval** — Framework de avaliação de saídas de LLM, incluindo a técnica *LLM-as-judge*.
Citado no hardening.

**dc / dc-runtime** — O micro-framework de componentes declarativos usado pelo protótipo.
O `support.js` é gerado a partir dele; o projeto-fonte não está neste repositório.
→ [04](04-frontend-prototype.md#o-runtime-dc-supportjs)

**Determinístico** — Que produz sempre o mesmo resultado para a mesma entrada. O Executor
é deliberadamente determinístico (sem LLM) por ser o agente que muda o mundo real.

**Devin** — Agente de código usado pela empresa para desenvolvimento. No EasyRun, recebe o
diagnóstico e devolve o patch que vira pull request.
→ [10](10-ecossistema-da-empresa.md#devin-e-a-organização-do-github)

**Drift** — Deriva silenciosa da qualidade, em dois níveis: nos baselines de detecção e na
precisão do próprio agente ao longo do tempo. → [11](11-mlops-llmops.md#7-drift-em-dois-níveis)

**DynamoDB** — Banco NoSQL da AWS. No EasyRun, guarda a memória episódica (incidentes
anteriores).

## E

**EBS (Elastic Block Store)** — Volumes de disco da AWS anexados a instâncias EC2. O
cenário PRD-2144 expande um volume gp3 em 40%.

**EC2** — Serviço de máquinas virtuais da AWS.

**Editable install (`pip install -e`)** — Instalação por ponteiro em vez de cópia: o
`import` lê direto do seu código-fonte, então editar reflete imediatamente.
→ [02](02-ambiente-e-ferramentas.md#pip-install--e-dev--dissecando-o-comando)

**egg-info** — Pasta de metadados gerada pelo setuptools durante a instalação. Artefato
derivado, por isso gitignorada.
→ [02](02-ambiente-e-ferramentas.md#srcsquad_agenticaegg-info--metadados-gerados)

**Embedding** — Representação de um texto como vetor numérico, de modo que textos com
significado próximo fiquem próximos no espaço vetorial. É o que viabiliza a busca
semântica de runbooks.

**Egresso (política de)** — As regras que governam o que pode sair da fronteira da empresa
rumo a um agente externo: allowlist de repositórios e redação de segredos.
→ [11](11-mlops-llmops.md#8-redação-antes-da-saída)

**Error Tracking** — Recurso do Datadog que agrupa exceções por assinatura em vez de listar
ocorrências isoladas. É o que permite dizer "1.284 ocorrências do mesmo defeito".

**Enum** — Tipo com conjunto fixo e nomeado de valores. Elimina "strings mágicas".
`Severity` e `DetectionAlgorithm` são enums.
→ [03](03-arquitetura-do-codigo.md#severitypy)

**EventBridge** — Barramento de eventos da AWS. Publica `anomalia.detectada`.

**Exit code** — Número devolvido por um programa ao sistema operacional: 0 = sucesso,
diferente de 0 = falha. É como o CI decide se um step passou.

## F

**FastAPI** — Framework web Python assíncrono que gera documentação OpenAPI a partir das
anotações de tipo. Escolha do backend-alvo.

**Failover** — Redirecionar tráfego para um recurso reserva quando o principal falha. É a
remediação para `dns_timeout`, via Route 53.

**FinOps** — Disciplina de gestão financeira de nuvem. No contexto de IA, controlar o custo
de inferência: escolha de modelo, orçamento de tokens, local vs. nuvem.
→ [06](06-arquitetura-alvo.md#governança-finops)

**f-string** — String Python com interpolação embutida: `f"porta {porta}"`.

**frozen=True** — Parâmetro de `@dataclass` que torna as instâncias imutáveis e hasheáveis.

## G

**Golden set** — Conjunto de incidentes já encerrados, usado para avaliar versões
candidatas de agente offline. Cresce sozinho: o que a squad resolve hoje é o teste de
amanhã. → [11](11-mlops-llmops.md#3-golden-set-de-incidentes)

**GMUD** — Gestão de mudança: o registro formal que autoriza uma alteração em produção. No
EasyRun a GMUD é **aberta automaticamente** e **aprovada sempre por um humano**.
→ [10](10-ecossistema-da-empresa.md#gmud-abertura-automática-aprovação-humana)

**GitHub Actions** — Sistema de CI integrado ao GitHub, configurado por arquivos YAML em
`.github/workflows/`. → [07](07-ci-cd-e-git.md)

**gitignore** — Arquivo que lista padrões que o Git deve ignorar.
→ [02](02-ambiente-e-ferramentas.md#gitignore--bloco-a-bloco)

**Guardrail** — Política explícita e determinística que limita o que os agentes podem fazer
sozinhos. O EasyRun define quatro.
→ [05](05-processo-end-to-end.md#os-guardrails)

## H

**Hardening** — Conjunto de medidas que tornam um sistema apto a produção: versionamento
de schema, circuit breakers, auditoria imutável, sanitização.
→ [06](06-arquitetura-alvo.md#hardening-para-produção)

**Herança** — Mecanismo em que uma classe reaproveita e especializa outra.
`NoCacheHandler(SimpleHTTPRequestHandler)` é um exemplo.

**Hexagonal (ports and adapters)** — Arquitetura que isola o domínio das tecnologias
externas por trás de interfaces. → [06](06-arquitetura-alvo.md#backend--python)

**HITL (Human-In-The-Loop)** — Humano no circuito: a execução automática **para** e aguarda
decisão humana antes de prosseguir. O mecanismo central de segurança do EasyRun.
→ [05](05-processo-end-to-end.md#12--a-fila-hitl)

## I

**IUClick** — Ferramenta de Kanban da empresa. Recebe um card de Bug por incidente, movido
automaticamente conforme a esteira avança. → [10](10-ecossistema-da-empresa.md#iuclick)

**Idempotente** — Operação que, executada duas vezes, produz o mesmo resultado que uma vez.
Requisito para remediação automática segura.

**Incidente** — Ocorrência que afeta (ou vai afetar) um serviço. IDs `ANM-####` para
anomalias, `PRD-####` para previsões, `INC-####` para episódios de memória.

**Injeção de prompt** — Ataque em que texto de fonte não confiável (um log, por exemplo)
contém instruções que o modelo obedece. Motiva a sanitização de I/O no hardening.

**`interrupt()`** — Função do LangGraph que suspende a execução do grafo, persiste o estado
e devolve o controle — o mecanismo do gate HITL.
→ [06](06-arquitetura-alvo.md#o-gate-hitl-e-o-interrupt)

## L

**Lambda** — Serviço AWS de execução de código sem servidor. Ferramenta principal do
Executor.

**LangChain** — Framework de abstração de ferramentas, retrievers e integração com modelos.
Usado na esteira junto com o LangGraph.

**Langfuse** — Plataforma de observabilidade de LLM: traces de execução, gestão de prompts
versionados e custo. No EasyRun, o lado de **operação** do LLMOps.
→ [11](11-mlops-llmops.md#a-stack)

**LangSmith** — Plataforma de datasets e avaliação de LLM. No EasyRun, o lado de
**avaliação**: experimentos e comparação entre versões candidatas.

**LangGraph** — Framework que estrutura aplicações com LLM como grafos de estado, com nós,
arestas condicionais, `interrupt()` e checkpointing.
→ [06](06-arquitetura-alvo.md#o-grafo-langgraph-pretendido)

**LLM (Large Language Model)** — Modelo de linguagem de grande porte, como Claude ou Qwen.

**LLMOps** — Práticas de operação de sistemas baseados em LLM: traces, prompts versionados,
avaliação, rollout controlado, orçamento de tokens. → [11](11-mlops-llmops.md)

**LLM-as-judge** — Técnica de avaliação em que um modelo julga a qualidade da saída de
outro. Necessária quando não há resposta única esperada.

## M

**MLOps** — Disciplina de operar modelos em produção de forma reprodutível e monitorada.
No contexto agêntico se manifesta como LLMOps. → [11](11-mlops-llmops.md)

**Máquina de estados** — Modelo em que o sistema está sempre num estado definido e as
transições são explícitas. O papel do Maestro / Step Functions / LangGraph.

**MCP (Model Context Protocol)** — Protocolo aberto que padroniza o acesso de modelos a
ferramentas e fontes de dados externas. Citado no docstring do `Explainer`.

**Memória episódica** — Registro de incidentes específicos já vividos, com desfecho e
eficácia. Fica no DynamoDB.
→ [05](05-processo-end-to-end.md#67--contexto-e-memória)

**Memória semântica** — Conhecimento geral vetorizado (runbooks), consultável por
significado. Fica no OpenSearch.

**Mockup** — Protótipo de aparência, sem funcionamento real por trás. É o que a pasta
`prototype/` é. → [04](04-frontend-prototype.md)

**Módulo / Pacote** — Módulo é um arquivo `.py`; pacote é uma pasta de módulos tratada como
unidade importável. → [03](03-arquitetura-do-codigo.md#conceitos-básicos-módulo-pacote-e-__init__py)

**MTTR (Mean Time To Repair)** — Tempo médio de reparo de um incidente. A métrica-chave do
produto: 4m 32s da squad contra 38 min de referência humana.

## N

**Natureza da remediação** — A classificação que o Diagnosta atribui depois da causa raiz:
`INFRA`, `CODIGO`, `CONFIG` ou `EXTERNO`. É ela que roteia toda a esteira.
→ [10](10-ecossistema-da-empresa.md#a-natureza-da-remediação)

**Nó adaptador** — Nó do grafo que chama plataformas externas por meio de portas tipadas,
em vez de raciocinar. Elo e Artífice são adaptadores.
→ [03](03-arquitetura-do-codigo.md#rolespy)

**NotImplementedError** — Exceção que Python usa idiomaticamente para marcar código ainda
não implementado. É o que todos os papéis de `roles.py` levantam.

**no-store** — Valor de `Cache-Control` que proíbe o navegador de guardar a resposta.

## O

**Ollama** — Ferramenta para rodar modelos de linguagem localmente. Citada na política
FinOps como alternativa à nuvem.

**OpenSearch** — Motor de busca e análise da AWS, com suporte a busca vetorial. Guarda a
memória semântica.

**Optional[X]** — Anotação de tipo que significa "ou um `X`, ou `None`". Comunica que a
ausência de valor é um estado esperado.

## P

**p99 (percentil 99)** — Valor abaixo do qual estão 99% das medições. Em latência, é a
métrica que revela a experiência da minoria mal atendida, invisível na média.

**Porta (port)** — Interface que o domínio declara para o que precisa do mundo externo. Em
Python, um `typing.Protocol`. As seis portas do EasyRun estão em `integrations.py`.
→ [03](03-arquitetura-do-codigo.md#integrationspy)

**parents[N]** — Do `pathlib`: sobe N níveis na árvore de diretórios. O `serve.py` usa
`parents[2]` para chegar à raiz do repositório.

**parametrize** — Decorador do pytest que roda a mesma função de teste com valores
diferentes, contando cada um como um teste separado.
→ [03](03-arquitetura-do-codigo.md#testes)

**Path traversal** — Ver **zip-slip**.

**PEP 517** — Padrão Python que permite a cada projeto declarar qual ferramenta de build
usar, em vez de assumir setuptools. É o que o `[build-system]` faz.

**pip** — O instalador de pacotes do Python.

**PostgreSQL** — Banco relacional. Destino planejado dos checkpoints.

**problemMatcher** — Configuração do VS Code que interpreta a saída de uma task. No
EasyRun, detecta pela linha `Serving …` que o servidor já subiu.
→ [05](05-processo-end-to-end.md#a-cadeia-do-f5-no-vs-code)

**Prompt versionado** — Prompt tratado como artefato: versionado, promovido por ambiente e
referenciado por id, nunca literal no código. → [11](11-mlops-llmops.md#2-prompts-versionados)

**Pull request (PR)** — Proposta de mudança de código submetida à revisão antes do merge. É
o artefato final do ramo `CODIGO`, e nunca é mergeado sem aprovação humana.

**pyproject.toml** — Arquivo padrão que descreve um projeto Python: nome, versão,
dependências, build e comandos. → [02](02-ambiente-e-ferramentas.md#pyprojecttoml--a-identidade-do-projeto)

**pytest** — Framework de testes do Python. Descobre `test_*.py` por convenção e usa
`assert` puro. → [03](03-arquitetura-do-codigo.md#testes)

## Q

**Quiz/Validator** — Nome do papel que julga a eficácia da remediação após a execução.
Roda a temperatura 0.1. Corresponde ao agente Auditor.

**Qwen** — Família de modelos de linguagem abertos. `qwen2.5-coder:32b` é o padrão-ouro do
projeto; `qwen2.5:7b`, o piso mínimo viável.

## R

**Rastreabilidade (cadeia de)** — O "fio único" que liga anomalia, incidente, CI, card do
kanban, repositório, sessão do Devin, pull request, GMUD e trace.
→ [10](10-ecossistema-da-empresa.md#a-cadeia-de-rastreabilidade--o-fio-único)

**React** — Biblioteca JavaScript de interface, carregada pelo `support.js` do CDN unpkg
na versão 18.3.1.

**Redação (de segredos)** — Remoção de credenciais, tokens e dados pessoais do conteúdo
antes de enviá-lo a um agente externo. Obrigatória por contrato
(`REDACTION_REQUIRED_BEFORE_EGRESS`). → [11](11-mlops-llmops.md#8-redação-antes-da-saída)

**Rolling deployment** — Atualização gradual em que instâncias antigas e novas do serviço
coexistem por alguns minutos. É a razão de existir o campo `schema_version`.

**Rollback** — Reverter um sistema para a versão anterior. Ação de maior risco do cenário
ANM-2047, e por isso protegida por guardrail.

**Rollout** — Como uma versão nova de agente ganha autoridade em produção: `SHADOW` →
`CANARY` → `FULL`. → [11](11-mlops-llmops.md#5-shadow-mode-e-canário)

**Root cause (causa raiz)** — A origem real do problema, distinta dos sintomas. Campo
`root_cause` do `AgentState`; responsabilidade do Diagnosta/Explainer.

**Route 53** — Serviço de DNS da AWS. Executa o failover de rota.

**Runbook** — Procedimento documentado para lidar com uma situação operacional conhecida.
Recuperado por busca semântica no OpenSearch.

## S

**ServiceNow** — Plataforma de ITSM da empresa: incidentes, CMDB e gestão de mudança. É
sistema de registro tanto na entrada quanto na saída do EasyRun.
→ [10](10-ecossistema-da-empresa.md#servicenow)

**SARIMA** — Modelo estatístico de séries temporais com componente sazonal. Base do
algoritmo de detecção `AGILE`.

**schema_version** — Campo do `AgentState` que versiona o próprio contrato, permitindo
detectar incompatibilidade durante rolling deployments.

**Severidade** — Classificação do impacto: `CRITICO`, `ALERTA` ou `PREDITIVO`.
→ [03](03-arquitetura-do-codigo.md#severitypy)

**Shadow mode** — Modo em que a versão nova roda sobre incidentes reais registrando o que
*faria*, sem agir. É o que torna autonomia aceitável num ambiente avesso a risco.
→ [11](11-mlops-llmops.md#5-shadow-mode-e-canário)

**Signals** — Sistema de reatividade granular do Angular 18, previsto no frontend-alvo.

**Skills** — Capacidades versionadas atribuídas a cada agente (ex.: `rollback-deploy`,
`buscar-runbooks`). Pilar 8.

**SRI (Subresource Integrity)** — Atributo `integrity` que declara o hash esperado de um
script externo; o navegador recusa executar se não bater. Usado pelo `support.js`.

**src-layout** — Convenção de colocar o código em `src/` para que os testes rodem contra o
pacote instalado, e não contra a pasta local.
→ [03](03-arquitetura-do-codigo.md#por-que-src-layout)

**SSM (Systems Manager)** — Serviço AWS para gerenciar parâmetros e executar comandos em
instâncias. Usado pelo Executor.

**Step Functions** — Serviço AWS de máquinas de estado. Representa a orquestração do
Maestro.

**Stub** — Implementação vazia que declara a interface sem o comportamento. Em Python, o
idioma é `raise NotImplementedError`.

**super()** — Chamada à implementação da classe mãe.

## T

**Temperatura** — Parâmetro que controla a aleatoriedade da geração de um LLM. Perto de 0,
determinístico; mais alto, mais variado. Validator = 0.1, Coach/Explainer = 0.4.
→ [03](03-arquitetura-do-codigo.md#governancepy)

**Tipo de gate** — Qual decisão o gate HITL pede: `acao` (infraestrutura), `pr` (pull
request) ou `gmud` (janela de mudança). Cada tipo mostra campos diferentes.

**Titan Embeddings** — Modelo de embeddings da AWS, usado pelo agente Contexto para busca
semântica.

**TOML** — Formato de arquivo de configuração legível, usado pelo `pyproject.toml`.

**Tool calling** — Capacidade de um modelo emitir uma chamada de ferramenta estruturada em
JSON. É o critério que define o padrão-ouro e o piso mínimo da política FinOps.

**Trigger** — Gatilho que aciona a squad: alarme, deploy, varredura agendada ou pedido
humano. Pilar 9.

**TypedDict** — Dicionário com contrato de chaves declarado. Em tempo de execução é um
`dict` comum; a verificação é estática. Formato do `AgentState`.
→ [03](03-arquitetura-do-codigo.md#statepy)

## V

**Validação (janela de)** — Período de observação após a remediação, para confirmar que a
correção sustentou. No ANM-2047, 10 minutos.

**VRAM** — Memória da placa de vídeo. Determina se um modelo cabe localmente: 24 GB para o
32B, 8 GB para o 7B.

## W

**Wheel (.whl)** — Formato binário de distribuição de pacotes Python, sucessor do *egg*.

**Workflow** — Arquivo YAML que descreve um processo automatizado no GitHub Actions.
→ [07](07-ci-cd-e-git.md#o-que-é-um-workflow-do-github-actions)

## X

**`<x-dc>`** — Tag que delimita o template visual num arquivo `.dc.html`. A lógica fica no
`<script data-dc-script>` irmão. → [04](04-frontend-prototype.md#o-runtime-dc-supportjs)

## Y

**YAML** — Formato de configuração baseado em indentação, usado pelos workflows. Espaços
importam; tabulação é erro.

## Z

**zip-slip (path traversal)** — Vulnerabilidade em que um arquivo dentro de um ZIP declara
um caminho como `../../etc/passwd`, escapando da pasta de destino ao ser extraído. O
`validate_zip.py` implementa a defesa.
→ [03](03-arquitetura-do-codigo.md#validate_zippy)

---

[← CI/CD e Git](07-ci-cd-e-git.md) · [Índice](README.md) · [Próximo: Lacunas e riscos →](09-lacunas-e-riscos.md)
