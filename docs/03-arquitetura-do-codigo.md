# 03 — Arquitetura do código

[← Ambiente e ferramentas](02-ambiente-e-ferramentas.md) · [Índice](README.md) · [Próximo: Frontend / protótipo →](04-frontend-prototype.md)

---

Este documento percorre todo o código Python do repositório. Cada seção apresenta primeiro
o **conceito da linguagem** envolvido e só depois o código que o usa.

## Mapa dos arquivos

```
EasyRun/
├── src/
│   └── squad_agentica/           # o pacote Python
│       ├── __init__.py           # 1 linha: a versão
│       ├── serve.py              # servidor HTTP local          [IMPLEMENTADO]
│       └── aiops/                # o contrato da arquitetura AIOps
│           ├── __init__.py       # vazio (0 bytes)
│           ├── severity.py       # severidade, algoritmo, origem, natureza [CONTRATO]
│           ├── remediation.py    # RemediationKind + mapa anomalia → ação  [CONTRATO]
│           ├── state.py          # o AgentState (schema v2)                [CONTRATO]
│           ├── roles.py          # papéis de raciocínio + nós adaptadores  [STUB]
│           ├── integrations.py   # portas: ServiceNow, Datadog, IUClick,   [CONTRATO]
│           │                     #         Devin, GitHub
│           ├── observability.py  # trace, prompts versionados, egresso     [CONTRATO]
│           ├── evaluation.py     # golden set, judge, shadow/canário       [CONTRATO]
│           ├── governance.py     # constantes de FinOps/modelos            [CONTRATO]
│           ├── checkpoint.py     # persistência de estado                  [STUB]
│           └── graph.py          # o grafo LangGraph                       [STUB]
├── tests/
│   ├── test_package.py           # 1 teste
│   └── test_aiops.py             # 16 funções → 24 testes
└── validate_zip.py               # script solto, fora do pacote
```

---

## Conceitos básicos: módulo, pacote e `__init__.py`

Antes de qualquer coisa, três termos que se repetem:

- **Módulo** — um arquivo `.py`. `serve.py` é o módulo `squad_agentica.serve`.
- **Pacote** — uma pasta que contém módulos e é tratada como unidade importável.
  `squad_agentica` é um pacote; `squad_agentica.aiops` é um subpacote.
- **`__init__.py`** — o arquivo que marca uma pasta como pacote e roda automaticamente
  quando o pacote é importado pela primeira vez.

### `src/squad_agentica/__init__.py`

Uma linha:

```python
__version__ = "0.1.0"
```

Isso torna possível `from squad_agentica import __version__` — e é exatamente o que o
teste `test_version` verifica. Colocar a versão aqui é convenção estabelecida em Python:
qualquer código que precise saber a versão do pacote em tempo de execução (para logar, para
mandar num header HTTP, para checar compatibilidade) sabe onde procurar.

⚠️ A versão aparece em **dois lugares** — aqui e no `version = "0.1.0"` do
[`pyproject.toml`](../pyproject.toml). Elas não se sincronizam sozinhas; o teste
`test_version` existe justamente para pegar a divergência.

### `src/squad_agentica/aiops/__init__.py` — vazio, e por quê

Este arquivo tem **0 bytes**. Ele existe só para marcar a pasta como pacote.

A alternativa seria usá-lo para *re-exportar* os nomes importantes:

```python
# o que NÃO está lá:
from .severity import Severity, DetectionAlgorithm
from .state import AgentState
```

Se estivesse, seria possível escrever `from squad_agentica.aiops import AgentState`. Como
não está, é obrigatório importar do submódulo exato:
`from squad_agentica.aiops.state import AgentState`. É o que os testes fazem — repare nas
cinco linhas de import de [`tests/test_aiops.py`](../tests/test_aiops.py), cada uma
apontando um módulo diferente.

Trade-off: imports mais verbosos, porém mais explícitos sobre a origem de cada nome.
Ver [09 — Lacunas #10](09-lacunas-e-riscos.md#10-aiops__init__py-vazio-torna-os-imports-verbosos).

---

## Por que src-layout

O código-fonte mora em `src/squad_agentica/`, não em `squad_agentica/` na raiz do
repositório. Isso é o **src-layout**, e a razão é sutil mas importante.

Python, ao resolver um `import`, procura primeiro no diretório de onde você rodou o
comando. Nas duas disposições possíveis:

**Sem `src/`** — o pacote fica na raiz, ao lado dos testes. Ao rodar `pytest` na raiz,
`import squad_agentica` encontra a **pasta local** e nem chega a olhar a instalação. Isso
mascara erros graves: você pode esquecer de declarar um módulo no empacotamento, os testes
passam felizes, e o pacote quebra na máquina de quem instalou de verdade.

**Com `src/`** — a raiz não contém nenhuma pasta chamada `squad_agentica`. O único jeito
de o `import` funcionar é achando o pacote **instalado no ambiente**. Ou seja: os testes
rodam contra exatamente o que o usuário final receberia.

Consequência prática: **sem `pip install -e ".[dev]"` os testes nem coletam** — falham com
`ModuleNotFoundError`. Isso é uma feature, não um bug (ver
[09 — Lacunas #8](09-lacunas-e-riscos.md#8-pytest-sem-instalação-falha-com-importerror)).

---

## `serve.py` — o servidor local

📄 [`src/squad_agentica/serve.py`](../src/squad_agentica/serve.py) · 38 linhas ·
**IMPLEMENTADO** — é o único código do repositório que executa trabalho real.

### O problema que ele resolve

Você poderia abrir `prototype/EasyRun.dc.html` com dois cliques no explorador de arquivos.
O navegador usaria o protocolo `file://` — e o mockup **não funcionaria**. Por segurança,
navegadores bloqueiam parte do carregamento de recursos entre arquivos locais. Como o
`EasyRun.dc.html` carrega o `support.js` e este busca bibliotecas externas, é preciso
servir por HTTP de verdade. Daí o servidor.

### Linha a linha

```python
"""Serve the static EasyRun prototype locally for manual inspection."""

import argparse
import http.server
import socketserver
import webbrowser
from pathlib import Path
```

Todos da **biblioteca padrão** — nada instalado via `pip`. `argparse` lê argumentos de
linha de comando; `http.server` e `socketserver` fazem o servidor; `webbrowser` abre o
navegador; `pathlib.Path` manipula caminhos de arquivo de forma portátil entre sistemas
operacionais.

```python
PROTOTYPE_DIR = Path(__file__).resolve().parents[2] / "prototype"
```

A linha mais densa do arquivo. Decompondo:

| Trecho | O que faz | Resultado |
|---|---|---|
| `__file__` | variável mágica: caminho deste arquivo | `src/squad_agentica/serve.py` (possivelmente relativo) |
| `.resolve()` | converte em caminho absoluto e resolve links simbólicos | `C:\...\EasyRun\src\squad_agentica\serve.py` |
| `.parents[0]` | um nível acima | `.../src/squad_agentica` |
| `.parents[1]` | dois níveis | `.../src` |
| `.parents[2]` | três níveis | `.../EasyRun` ← a raiz do repositório |
| `/ "prototype"` | o operador `/` do `pathlib` concatena caminhos | `.../EasyRun/prototype` |

O `/` sobrecarregado é um recurso do `pathlib`: em vez de `os.path.join(a, b)` ou de
concatenar strings com a barra errada para o SO, você escreve `Path(a) / b` e a biblioteca
usa `\` no Windows e `/` no Linux automaticamente.

⚠️ O `parents[2]` assume que existem exatamente dois níveis entre o arquivo e a raiz do
repo. Isso só é verdade num checkout do código. Ver
[09 — Lacunas #2](09-lacunas-e-riscos.md#2-servepy-depende-de-estar-num-checkout-do-repositório).

```python
class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()
```

**Conceito: herança.** `class Filha(Mãe)` cria uma classe que herda todo o comportamento
da mãe e pode substituir partes. Aqui, `SimpleHTTPRequestHandler` é uma classe pronta do
Python que já sabe servir arquivos de uma pasta. Só um detalhe é alterado.

**Conceito: `super()`.** Chama a implementação original da classe mãe. A ordem importa: o
`send_header` acontece **antes** do `super().end_headers()`, porque `end_headers()` é o
que fecha o bloco de cabeçalhos HTTP — depois dele não dá mais para adicionar nada.

**O que é `Cache-Control: no-store`.** Um cabeçalho HTTP que instrui o navegador a
**nunca** guardar cópia da resposta. Sem ele, você editaria o `EasyRun.dc.html`, apertaria
F5 e continuaria vendo a versão antiga — o navegador serviria do próprio cache. Num
arquivo de 96 KB em edição ativa, isso custa horas de confusão. `must-revalidate` reforça:
mesmo que houvesse cópia, confirme com o servidor antes de usar.

```python
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--no-browser", action="store_true", help="Don't auto-open the browser")
    args = parser.parse_args()
```

**Conceito: `argparse`.** Transforma `sys.argv` (a lista crua de argumentos) num objeto
com atributos, e ainda gera o `--help` de graça.

| Argumento | Tipo | Padrão | Efeito |
|---|---|---|---|
| `--port N` | inteiro | `8080` | porta TCP onde o servidor escuta |
| `--no-browser` | flag | `False` | `action="store_true"` = presente vira `True`; não pede valor |

`description=__doc__` reaproveita a docstring do módulo (a primeira string do arquivo)
como texto de ajuda. Rodar `squad-agentica-serve --help` mostra
*"Serve the static EasyRun prototype locally for manual inspection."*

```python
    handler = lambda *a, **kw: NoCacheHandler(*a, directory=str(PROTOTYPE_DIR), **kw)
    url = f"http://localhost:{args.port}/EasyRun.dc.html"
```

**Conceito: `lambda`.** Uma função anônima de uma linha.
**Conceito: `*args` / `**kwargs`.** Capturam "qualquer quantidade de argumentos
posicionais" e "qualquer quantidade de argumentos nomeados", repassando-os adiante.

Por que essa ginástica? Porque o `TCPServer` recebe a **classe** do handler e a instancia
sozinho, passando argumentos que ele controla. Não há como dizer a ele "e passe também
`directory=...`". A solução é entregar um invólucro que já traz o `directory` embutido e
repassa o resto — um *currying* manual.

`f"..."` é uma **f-string**: interpolação de variáveis direto na string, com `{}`.

```python
    with socketserver.TCPServer(("localhost", args.port), handler) as httpd:
        print(f"Serving {PROTOTYPE_DIR} at {url} (Ctrl+C to stop)")
        if not args.no_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
```

**Conceito: `with`** (*context manager*). Garante que o recurso seja fechado ao sair do
bloco — inclusive se houver erro. Aqui, garante que a porta TCP seja liberada.

**`("localhost", args.port)`** — o endereço de escuta. `localhost` (127.0.0.1) significa
**só esta máquina**: outro computador na mesma rede não consegue acessar. É a escolha
segura para uma ferramenta de desenvolvimento. Para expor na rede seria `"0.0.0.0"`.

**`serve_forever()`** bloqueia: fica em laço infinito atendendo requisições. O programa
só sai quando você interrompe.

**`except KeyboardInterrupt: pass`** — quando você aperta `Ctrl+C`, o Python levanta a
exceção `KeyboardInterrupt`. Sem esse tratamento, o terminal seria poluído com um
*traceback* de erro. Com ele, o `pass` (que significa "não faça nada") deixa o programa
encerrar em silêncio, como se fosse uma saída normal — porque é.

⚠️ A linha do `print` é **contrato com o VS Code**: o `problemMatcher` do
[`tasks.json`](../.vscode/tasks.json) espera exatamente a palavra `Serving` no começo da
linha para considerar o servidor pronto. Ver
[09 — Lacunas #4](09-lacunas-e-riscos.md#4-o-problemmatcher-está-acoplado-ao-texto-do-print).

```python
if __name__ == "__main__":
    main()
```

**Conceito: o guard `__main__`.** A variável `__name__` vale `"__main__"` quando o arquivo
é o ponto de entrada da execução, e vale o nome do módulo quando ele foi *importado* por
outro. O `if` garante que `main()` só roda no primeiro caso — permitindo importar
`serve.py` (num teste, por exemplo) sem que um servidor suba do nada.

Este bloco é o que faz `python -m squad_agentica.serve` funcionar. Já o comando
`squad-agentica-serve` não passa por ele: o console script chama `main()` diretamente
(ver [02](02-ambiente-e-ferramentas.md#projectscripts)).

---

## O subpacote `aiops/`

Dez módulos que descrevem a arquitetura AIOps em código, sem implementá-la. Os docstrings
citam uma "spec section 3/4/5" — um documento de especificação externo que **não está no
repositório** (ver
[09 — Lacunas #9](09-lacunas-e-riscos.md#9-a-especificação-citada-nos-docstrings-não-está-no-repositório)).

O subpacote continua **sem nenhuma dependência obrigatória**: as integrações são declaradas
com `typing.Protocol`, não com SDKs de fornecedor.

### `severity.py`

📄 [`src/squad_agentica/aiops/severity.py`](../src/squad_agentica/aiops/severity.py) · **CONTRATO**

**Conceito: `Enum`.** Um tipo com um conjunto fixo e nomeado de valores possíveis.
Resolve o problema de "strings mágicas": em vez de espalhar `"critico"` pelo código —
onde um `"critcio"` com erro de digitação só apareceria em produção — você escreve
`Severity.CRITICO`, e o erro vira falha imediata de atributo inexistente.

**Conceito: `class X(str, Enum)`.** Herança múltipla que faz cada membro **ser**, ao mesmo
tempo, uma string e um membro do enum. Na prática:

```python
Severity.CRITICO == "critico"        # True
json.dumps({"sev": Severity.CRITICO}) # funciona: serializa como "critico"
```

Sem o `str`, seria preciso escrever `Severity.CRITICO.value` em toda serialização. É um
detalhe pequeno que evita centenas de conversões manuais numa API real.

```python
class Severity(str, Enum):
    CRITICO = "critico"
    ALERTA = "alerta"
    PREDITIVO = "preditivo"
```

| Valor | Significado | Cenário do mockup |
|---|---|---|
| `CRITICO` | Impacto acontecendo agora, cliente afetado | ANM-2047 (latência), ANM-2118 (DNS) |
| `ALERTA` | Degradação relevante, ainda sem impacto pleno | ANM-2091 (CPU spike) |
| `PREDITIVO` | Nada quebrou — vai quebrar se ninguém agir | PRD-2144 (disco vai encher em ~2h) |

O `PREDITIVO` é o mais interessante conceitualmente: representa a mudança de operação
reativa para preventiva. Não há incidente ainda; há uma projeção.

```python
class DetectionAlgorithm(str, Enum):
    BASIC = "basic"
    AGILE = "agile"
    ROBUST = "robust"
```

Os três algoritmos de detecção de anomalia (a docstring credita a metodologia da Datadog).
A pergunta que cada um responde é *"esse valor estranho é anormal mesmo?"* — e a resposta
depende do que se assume sobre a série histórica:

| Algoritmo | Assume | Quando usar | Cenário |
|---|---|---|---|
| `BASIC` | Nada — não há histórico suficiente | Métrica nova, sem baseline. Usa janelas de quantil móvel. | ANM-2118: endpoint lançado há poucos dias |
| `AGILE` | Que há **sazonalidade** (SARIMA) | Métricas com padrão de hora/dia/semana. Adapta-se rápido a mudanças de patamar legítimas. | ANM-2091: campanha de marketing dobra o tráfego — é novo normal, não anomalia |
| `ROBUST` | Que a série é **estável** | Métricas previsíveis. Ignora ruído de curto prazo, detecta deriva sistêmica. | ANM-2047 e PRD-2144 |

Escolher errado tem custo real: usar `ROBUST` numa métrica sazonal dispara alarme falso
toda segunda-feira de manhã; usar `AGILE` numa métrica estável faz o algoritmo "aceitar"
uma degradação gradual como novo normal e nunca alarmar.

O módulo traz mais dois enums, acrescentados para refletir o ecossistema da empresa:

```python
class AnomalyOrigin(str, Enum):   # de onde veio o estímulo
    DATADOG = "datadog"
    SERVICENOW = "servicenow"
    AGENDADO = "agendado"
    HUMANO = "humano"

class IncidentNature(str, Enum):  # falha técnica ou de resultado de negócio
    SISTEMICO = "sistemico"
    NEGOCIO = "negocio"
```

`IncidentNature.NEGOCIO` é o caso que a telemetria sozinha não enxerga: notas fiscais sem
conciliação, pedidos não faturados — **com todas as métricas de infraestrutura verdes**. A
única entrada capaz de trazer isso é o volume de chamados no ServiceNow. É o cenário
INC-3350 do protótipo.

### `state.py`

📄 [`src/squad_agentica/aiops/state.py`](../src/squad_agentica/aiops/state.py) · **CONTRATO**

**Conceito: `TypedDict`.** Um dicionário comum com um contrato de chaves declarado. É
importante entender o que ele **não** faz: em tempo de execução, um `TypedDict` é apenas
`dict`. Nada é validado, nada é verificado, nenhuma chave errada levanta erro. A
verificação acontece **antes** de rodar, feita por ferramentas de análise estática
(mypy, pyright) e pelo autocompletar do editor.

Por que usar isso em vez de uma classe? Porque frameworks de orquestração como o LangGraph
trabalham com o estado como dicionário — serializando, mesclando e persistindo entre nós
do grafo. O `TypedDict` dá segurança de tipos sem abrir mão de ser um dicionário de verdade.

**Conceito: `Optional[X]`.** Equivale a `X | None`: "ou é um `X`, ou é `None`". Comunica
que a ausência de valor é um estado **esperado**, não um erro.

O `AgentState` está organizado em blocos. Os campos de identidade, diagnóstico, plano e
HITL, e quem preenche cada um:

| Campo | Tipo | Significado | Preenchido por |
|---|---|---|---|
| `incident_id` | `str` | Identificador do incidente (`"ANM-2047"`) | Sentinela, na detecção |
| `anomaly_type` | `str` | Categoria (`"latency_spike"`, `"code_defect"`) — chave de busca no `REMEDIATION_MAP` | Sentinela |
| `severity` | `Severity` | Crítico / Alerta / Preditivo | Sentinela |
| `detection_algorithm` | `DetectionAlgorithm` | Qual motor classificou | Sentinela |
| `origin` | `AnomalyOrigin` | Datadog, ServiceNow, agendado ou humano | Sentinela |
| `incident_nature` | `IncidentNature` | Sistêmico ou de negócio | Sentinela |
| `schema_version` | `int` | Versão deste próprio contrato — **hoje 2** | Constante do código |
| `root_cause` | `Optional[str]` | A causa identificada. `None` até o diagnóstico. | Diagnosta / Explainer |
| `confidence` | `Optional[float]` | Confiança no diagnóstico (0–1). No mockup: 0.89 a 0.96. | Diagnosta |
| `remediation_kind` | `Optional[RemediationKind]` | **Roteia toda a esteira** | Diagnosta |
| `remediation_plan` | `list[str]` | Os passos propostos | Maestro / Planner |
| `remediation_action` | `Optional[str]` | A ação efetivamente escolhida | Planner |
| `hitl_required` | `bool` | Se este plano precisa de aprovação humana | Auditor (guardrails) |
| `hitl_approved` | `Optional[bool]` | **Três estados**: `None` = ainda não decidido, `True` = aprovado, `False` = rejeitado | Humano |
| `checkpoint_id` | `Optional[str]` | Ponteiro para o último estado salvo | `CheckpointStore` |
| `history` | `list[str]` | Trilha de auditoria do que aconteceu | Todos os nós |

Repare no `hitl_approved`: é `Optional[bool]` justamente porque um booleano puro não daria
conta. `False` significaria tanto "rejeitado" quanto "ainda não perguntamos" — e são
situações opostas. O `None` separa as duas.

#### O bloco de rastreabilidade corporativa

Acrescentado na versão 2 do schema. É o "fio único" que liga todos os registros que o
processo da empresa exige — cada campo preenchido pelo Elo conforme a esteira avança:

| Campo | Plataforma | Quando é preenchido |
|---|---|---|
| `servicenow_incident_id` | ServiceNow | Ao correlacionar ou abrir o incidente |
| `cmdb_ci` | ServiceNow CMDB | Na consulta ao item de configuração |
| `iuclick_task_id` | IUClick | Logo após identificar o CI |
| `repository` | GitHub org | Só no ramo `CODIGO` |
| `devin_session_id` | Devin | Só no ramo `CODIGO` |
| `pull_request_url` | GitHub org | Só no ramo `CODIGO` |
| `servicenow_change_id` | ServiceNow | Nos ramos `CODIGO` e `CONFIG` (a GMUD) |
| `escalated_to` | ServiceNow | Quando a squad desiste com segurança |
| `trace_id` | Datadog · Langfuse · LangSmith | Na detecção |

Os campos que ficam `None` **também informam**: um incidente sem `repository` e sem
`pull_request_url` é, por construção, um caso que se resolveu em runtime.

**Por que existe `schema_version` — e por que ele acabou de subir para 2.** Durante um
*rolling deployment* (atualização gradual, em que as instâncias antigas e novas do serviço
convivem por alguns minutos), um incidente pode ter seu estado criado pela versão antiga do
código e ser lido pela nova — ou vice-versa. Se o formato mudou, isso quebra de formas
difíceis de diagnosticar. Acrescentar o bloco de rastreabilidade é exatamente esse tipo de
mudança, e por isso a constante `SCHEMA_VERSION` foi de 1 para 2. O campo saiu do papel de
"boa prática documentada" para "usado de verdade" — que é o melhor destino possível para um
item de hardening.

O teste `test_agent_state_shape` constrói um estado completo, e
`test_traceability_fields_present` garante que nenhum elo da cadeia desapareça
silenciosamente numa refatoração.

### `roles.py`

📄 [`src/squad_agentica/aiops/roles.py`](../src/squad_agentica/aiops/roles.py) · **STUB**

**Conceito: *callable class*.** Uma classe que define `__call__` pode ser chamada como se
fosse função: `planner = Planner(); planner(state)` executa `Planner.__call__(state)`.

Por que não usar funções simples? Porque uma classe pode guardar configuração no
`__init__` — qual modelo usar, qual temperatura, qual cliente de API — e ainda assim ser
invocada com a assinatura uniforme que um grafo espera. Num LangGraph, todo nó é
"algo chamável que recebe o estado e devolve o estado". A classe dá as duas coisas.

**Conceito: *stub*.** Uma implementação vazia que declara a interface sem o comportamento.
`raise NotImplementedError` é a forma idiomática em Python de dizer "existe, mas ainda
não". Falha alto e imediatamente se alguém chamar por engano — muito melhor do que
retornar `None` e propagar o problema para longe da causa.

O módulo tem **duas famílias de nó**, e a distinção é importante:

**Papéis de raciocínio** — os quatro da especificação; cada um chama um modelo:

| Papel | Responsabilidade (docstring) | Agente EasyRun correspondente |
|---|---|---|
| `Planner` | Define o plano estruturado de diagnóstico e remediação | Maestro 🎼 |
| `Explainer` | Analisa a causa raiz via ferramentas MCP | Diagnosta 🔬 |
| `Validator` | *Quiz/Validator*: julga a eficácia da remediação **após** a execução | Auditor 🛡️ |
| `Coach` | Sintetiza o aprendizado e decide encerrar ou escalar | Maestro + Auditor |

**Nós adaptadores** — chamam as plataformas corporativas pelas portas de
[`integrations.py`](../src/squad_agentica/aiops/integrations.py); não raciocinam:

| Nó | O que faz | Agente EasyRun |
|---|---|---|
| `TraceabilityNode` | Lê a CMDB, abre o bug, abre a GMUD, move o kanban, encerra ou reatribui | Elo 🔗 |
| `CodeRemediationNode` | Clona o repositório, delega ao Devin, abre o pull request | Artífice 🛠️ |

**Por que a distinção importa.** Na tela, Elo e Artífice são agentes — é assim que a squad
se apresenta e é o que o público reconhece. No grafo, são nós que usam ferramentas. Os dois
modelos estão certos no seu próprio nível, e o docstring do módulo registra isso para que
ninguém "conserte" um em nome do outro.

Há ainda duas funções soltas:

- **`classify_remediation(state)`** — decide o ramo (`INFRA`, `CODIGO`, `CONFIG`,
  `EXTERNO`). É a decisão de maior alavancagem do fluxo: rotear infraestrutura para o
  caminho de código gasta uma sessão do Devin à toa; rotear código para o caminho de
  infraestrutura "resolve" o sintoma e o bug volta no próximo deploy.
- **`escalate(state)`** — desistir com segurança: devolve o incidente ao time dono com o
  contexto. Um agente que insiste é mais perigoso do que um que escala.

Duas notas de engenharia embutidas nos docstrings merecem destaque:

**Sobre o `Validator`** — roda a temperatura **0.1** (`governance.TEMPERATURE_VALIDATOR`)
"para manter a avaliação consistente e analiticamente justa". Faz sentido: quem julga
precisa dar a mesma nota para o mesmo caso, sempre.

**Sobre `request_human_approval`** — o gate HITL, implementado via `interrupt()` do
LangGraph. A docstring traz um aviso explícito:

> após um `interrupt()` para intervenção humana, o nó **DEVE** retornar o `AgentState`
> completo — caso contrário os nós seguintes falham por perda de contexto.

É o tipo de armadilha que só se descobre em produção às 3h da manhã, então está registrada
no código. Detalhes em [06 — Arquitetura-alvo](06-arquitetura-alvo.md#o-gate-hitl-e-o-interrupt).

### `remediation.py`

📄 [`src/squad_agentica/aiops/remediation.py`](../src/squad_agentica/aiops/remediation.py) · **CONTRATO**

**Conceito: `@dataclass`.** Um decorador que gera automaticamente o código repetitivo de
uma classe que só carrega dados: o `__init__`, o `__repr__` (representação legível ao
imprimir) e o `__eq__` (comparação por valor, não por identidade).

**Conceito: `frozen=True`.** Torna as instâncias **imutáveis**: depois de criadas, tentar
alterar um campo levanta `FrozenInstanceError`. Dois benefícios: ninguém modifica uma
entrada da tabela por acidente em tempo de execução, e o objeto vira *hashable* (pode ser
chave de dicionário ou entrar em `set`).

```python
@dataclass(frozen=True)
class RemediationAction:
    trigger: str      # a condição observada
    action: str       # o que fazer
    platform: str     # onde a ação acontece — nem sempre AWS
    kind: RemediationKind
```

O campo se chama `platform`, e não `aws_service`, de propósito: o desfecho pode ser um pull
request no GitHub ou uma GMUD no ServiceNow.

**O enum que roteia tudo:**

```python
class RemediationKind(str, Enum):
    INFRA   = "infra"    # ação em runtime — o Executor age direto
    CODIGO  = "codigo"   # o software precisa mudar — vira pull request
    CONFIG  = "config"   # parâmetro ou dado — desfecho sob GMUD
    EXTERNO = "externo"  # fora do escopo — escalonamento
```

E a tabela:

| Chave (`anomaly_type`) | `trigger` | `action` | `platform` | `kind` |
|---|---|---|---|---|
| `cpu_spike` | CPU Spike > 90% | Escalonamento Horizontal (Out) | ASG (Auto Scaling) | `INFRA` |
| `lambda_error_rate` | Lambda Error > 5% | Rollback ou Update de Config | AWS Lambda | `INFRA` |
| `dns_timeout` | DNS Timeout | Failover de Rota | Route 53 | `INFRA` |
| `disk_exhaustion_forecast` | Projeção de disco em 100% < 4h | Expansão preventiva de volume | EC2 (EBS) | `INFRA` |
| `code_defect` | Erro recorrente rastreado a um commit | Correção via agente + Pull Request | Devin · GitHub org | `CODIGO` |
| `config_drift` | Parâmetro divergente do baseline | Correção sob mudança formal | ServiceNow (GMUD) · SSM | `CONFIG` |
| `third_party_outage` | Degradação em serviço de terceiro | Escalonamento ao time/fornecedor | ServiceNow (reatribuição) | `EXTERNO` |

Esta é a ponte entre o que a Sentinela detecta e o que a squad faz. O fluxo pretendido é:
`state["anomaly_type"]` → busca no `REMEDIATION_MAP` → ação recomendada **e o ramo da
esteira**.

O teste `test_remediation_kinds_are_coherent` verifica que os quatro valores do enum
aparecem no mapa — ou seja, que nenhum caminho da esteira ficou sem exemplo.

*Escalonamento horizontal* significa acrescentar mais máquinas (em oposição ao vertical,
que é trocar por uma máquina maior). O horizontal é preferido em nuvem por ser reversível
e não exigir reinício.

⚠️ Este mapa está duplicado, palavra por palavra, dentro do HTML do mockup (variável
`remediacaoLista`). Ver
[09 — Lacunas #1](09-lacunas-e-riscos.md#1-fonte-da-verdade-duplicada-entre-python-e-html).

### `governance.py`

📄 [`src/squad_agentica/aiops/governance.py`](../src/squad_agentica/aiops/governance.py) · **CONTRATO**

Constantes de **FinOps** (disciplina de gestão financeira de nuvem — no caso de IA, custo
de inferência) e governança de modelos. Nenhum import; só valores de referência.

```python
GOLD_MODEL = "qwen2.5-coder:32b"
MINIMUM_VIABLE_MODEL = "qwen2.5:7b"

TEMPERATURE_VALIDATOR = 0.1
TEMPERATURE_COACH = 0.4
TEMPERATURE_EXPLAINER = 0.4

LOCAL_VRAM_GB_32B = 24
LOCAL_VRAM_GB_7B = 8
```

**`GOLD_MODEL` e `MINIMUM_VIABLE_MODEL`.** O "32b" e o "7b" indicam o número de
*parâmetros* do modelo — 32 bilhões e 7 bilhões. Mais parâmetros ≈ mais capacidade,
mais memória, mais custo, mais lentidão.

Segundo o painel FinOps do protótipo, o critério de escolha aqui é *tool calling*: a
capacidade do modelo de emitir JSON estruturado corretamente para chamar uma ferramenta.
Isso é decisivo numa arquitetura agêntica — se o modelo produz JSON malformado ao pedir
"escale o ASG de 6 para 14", o agente inteiro para. O 32b é apontado como o mais confiável
nisso; o 7b como o **piso**: abaixo disso, a geração estruturada começa a falhar com
frequência inaceitável.

**Temperatura.** Um parâmetro entre 0 e ~2 que controla a aleatoriedade da geração. Perto
de 0, o modelo sempre escolhe a continuação mais provável — respostas determinísticas e
repetíveis. Mais alto, ele amostra entre alternativas — respostas mais variadas e
criativas, e menos previsíveis.

A política do projeto é coerente com o papel de cada agente:

| Papel | Temperatura | Racional |
|---|---|---|
| `Validator` | **0.1** | Está **julgando**. O mesmo caso precisa receber a mesma nota sempre. Variação aqui seria injustiça. |
| `Coach` | **0.4** | Está **sintetizando aprendizado** para humanos lerem. Alguma variação melhora o texto. |
| `Explainer` | **0.4** | Está **explicando** a causa raiz. Idem. |

O teste `test_governance_constants` não checa os valores exatos das temperaturas — ele
checa a **relação**: `TEMPERATURE_VALIDATOR < TEMPERATURE_COACH`. Isso trava o princípio
de design ("quem julga é mais determinístico do que quem explica") sem engessar os
números. É um teste bem pensado.

**VRAM.** Memória da placa de vídeo (GPU). Para rodar um modelo localmente, ele precisa
caber na VRAM. Os números — 24 GB para o 32b, 8 GB para o 7b — são a fronteira de decisão
entre rodar local (hardware caro, custo fixo previsível, latência controlada) e usar nuvem
(sem hardware, custo por token, maior capacidade). 24 GB corresponde a uma GPU de ponta;
8 GB, a uma placa comum.

### `integrations.py`

📄 [`src/squad_agentica/aiops/integrations.py`](../src/squad_agentica/aiops/integrations.py) · **CONTRATO**

**Conceito: `Protocol`.** Uma interface *estrutural*: qualquer classe que tenha os métodos
certos satisfaz o protocolo, sem precisar herdar de nada. É o equivalente Python das
"portas" da arquitetura hexagonal — o domínio declara o que precisa, e quem implementa fica
na borda.

Por que isso importa aqui: o módulo declara cinco integrações **sem importar um único SDK
de fornecedor**. O pacote continua com zero dependências obrigatórias, e trocar de
ferramenta é trocar de adaptador, não reescrever o domínio.

| Porta | Plataforma | Métodos |
|---|---|---|
| `ITSMClient` | ServiceNow | `get_configuration_item`, `open_incident`, `open_change_request`, `close_incident`, `reassign_incident` |
| `KanbanClient` | IUClick | `create_bug`, `move_card` |
| `ObservabilityClient` | Datadog | `query_metric`, `search_logs`, `get_error_tracking_issue` |
| `CodeAgentClient` | Devin | `start_session`, `fetch_result` |
| `SourceControlClient` | GitHub org | `clone`, `open_pull_request`, `get_checks` |

Mais três *value objects* — `ConfigurationItem`, `ChangeRequest` e `PullRequest` — e a
tupla `INTEGRATIONS`, que é a fonte de verdade da tela de Integrações do protótipo.

Duas decisões de contrato valem destaque:

**`ConfigurationItem.repository` é `Optional[str]`.** É o campo que torna a correção de
código possível — sem saber qual repositório sustenta o serviço, o Artífice não tem o que
clonar. E é justamente o campo com maior chance de estar vazio numa CMDB real. Marcá-lo
como opcional força quem implementar a tratar o caso, em vez de descobrir em produção.

**`Integration.automatic` é `False` para o GitHub.** Há um teste garantindo isso:

```python
github = next(i for i in INTEGRATIONS if i.platform == "GitHub (org)")
assert github.automatic is False, "merge sempre exige aprovação humana"
```

### `observability.py`

📄 [`src/squad_agentica/aiops/observability.py`](../src/squad_agentica/aiops/observability.py) · **CONTRATO**

O contrato de observabilidade **da própria esteira** — não dos sistemas monitorados. O
docstring do módulo abre justamente separando as duas, porque confundi-las é o erro mais
comum nesse tipo de projeto. Detalhe em [11 — MLOps e LLMOps](11-mlops-llmops.md).

O que ele define:

- **`TraceContext`** — o `trace_id` correlacionando Datadog APM, Langfuse, LangSmith e o
  incidente do ServiceNow.
- **`PromptRef(name, version, stage)`** e o enum `Stage` — prompt como artefato versionado,
  promovido por ambiente, nunca literal no código.
- **`AgentRunMetrics`** — tokens, latência e chamadas de ferramenta por execução de nó,
  com a propriedade `total_tokens`.
- **Duas constantes de política de egresso**, e são as mais importantes do arquivo:

```python
REDACTION_REQUIRED_BEFORE_EGRESS = True
REPOSITORY_ALLOWLIST_REQUIRED = True
```

Elas existem porque delegar uma correção ao Devin significa que **código-fonte da empresa
atravessa uma fronteira organizacional**. Essa é a primeira objeção que segurança levanta,
e a resposta precisa estar no contrato, não escondida num adaptador. O teste
`test_egress_policy_is_locked_on` garante que ninguém as desligue por conveniência.

### `evaluation.py`

📄 [`src/squad_agentica/aiops/evaluation.py`](../src/squad_agentica/aiops/evaluation.py) · **CONTRATO**

Como uma versão nova de agente chega a produção sem quebrar nada. Um pipeline agêntico não
pode ser promovido como um serviço sem estado: não há saída única esperada — duas
explicações diferentes de causa raiz podem estar ambas corretas.

- **`EvalCase`** — um incidente encerrado do ServiceNow replayado como caso de teste. O
  conjunto cresce sozinho: o que a squad resolve hoje é o teste de regressão de amanhã.
- **`EvalResult`** — a nota atribuída pelo modelo juiz.
- **`RolloutMode`** — `SHADOW` (roda e registra o que faria, **sem agir**), `CANARY` (fatia
  delimitada), `FULL`. O shadow mode é o que torna autonomia aceitável numa organização
  avessa a risco.
- **`passes_regression_gate()`** — o portão, ainda stub.

Os limiares, e por que são diferentes entre si:

| Constante | Valor | Racional |
|---|---|---|
| `GOLDEN_SET_MIN_SIZE` | 40 | Abaixo disso, diferença de score é ruído |
| `MIN_ROOT_CAUSE_SCORE` | 0.80 | Explicação imprecisa custa tempo de leitura |
| `MIN_REMEDIATION_KIND_ACCURACY` | **0.90** | Errar a natureza manda o incidente pelo caminho errado inteiro |
| `MAX_REGRESSION_TOLERANCE` | 0.02 | Margem para ruído estatístico, não para piora real |

O teste `test_regression_gate_thresholds` trava a **relação** entre os dois do meio — mesmo
padrão usado nas temperaturas: preserva o princípio de design sem engessar o número.

### `checkpoint.py`

📄 [`src/squad_agentica/aiops/checkpoint.py`](../src/squad_agentica/aiops/checkpoint.py) · **STUB**

```python
@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    incident_id: str
    state: AgentState

class CheckpointStore:
    def save(self, checkpoint: Checkpoint) -> None: ...   # NotImplementedError
    def load(self, checkpoint_id: str) -> Checkpoint: ... # NotImplementedError
```

**Conceito: checkpoint.** Uma fotografia do estado num instante, gravada de forma durável,
para permitir retomar dali.

Por que isso é crítico **neste** domínio especificamente? Porque as ações dos agentes têm
efeitos colaterais irreversíveis no mundo real. Considere a sequência do cenário ANM-2047:

1. Congelar deploys ✅ feito
2. Rollback v2.14.3 → v2.14.2 ✅ feito
3. Escalar pool RDS 50 → 120 ⬅️ **o processo morre aqui**
4. Validar métricas

Sem checkpoint, ao reiniciar o processo começaria do zero — e faria o rollback **de novo**,
sobre uma aplicação que já está na v2.14.2. Na melhor hipótese é ruído; na pior, reverte
para uma versão anterior à correta e agrava o incidente.

A docstring registra exatamente isso: *"em caso de falha, a remediação retoma exatamente
do último checkpoint salvo em vez de reexecutar ações corretivas já aplicadas."*

O destino planejado é PostgreSQL — banco relacional, transacional, durável. Ver
[06 — Arquitetura-alvo](06-arquitetura-alvo.md).

### `graph.py`

📄 [`src/squad_agentica/aiops/graph.py`](../src/squad_agentica/aiops/graph.py) · **STUB**

Uma função stub e um docstring longo, que é onde mora o conteúdo. O fluxo pretendido, com
o roteamento condicional que a natureza da remediação introduz:

```text
TraceabilityNode           # abre INC/Bug, resolve o CI e o repositório
  -> Planner
  -> Explainer             # causa raiz
  -> classify_remediation  # decide o ramo
       |
       +-- INFRA    -> [interrupt() se hitl_required] -> Executor
       +-- CONFIG   -> TraceabilityNode(GMUD) -> interrupt() -> Executor
       +-- CODIGO   -> CodeRemediationNode     # clona, delega, abre PR
       |               -> TraceabilityNode(GMUD)
       |               -> interrupt()          # aprovação do PR
       |               -> interrupt()          # aprovação da GMUD
       |               -> Executor             # merge e deploy
       +-- EXTERNO  -> escalate
  -> Validator             # eficácia pós-execução
  -> TraceabilityNode      # move o kanban, encerra o incidente
  -> Coach
```

Duas notas do docstring merecem destaque:

**O ramo `CODIGO` interrompe duas vezes.** Aprovar código e aprovar uma janela de mudança
em produção são autoridades diferentes, exercidas por pessoas possivelmente diferentes.
Fundir as duas numa aprovação só é o tipo de simplificação que não sobrevive ao primeiro
comitê de mudança. No protótipo isso é literal: o cenário INC-3312 **para duas vezes**.

**`TraceabilityNode` aparece três vezes de propósito.** Registro corporativo não é etapa
final: o bug é aberto no começo, a GMUD no meio, o encerramento no fim. Agrupar tudo no
final deixaria o incidente invisível para todo mundo fora da ferramenta justamente enquanto
está sendo trabalhado — que é quando o board mais importa.

E o ponto que já estava lá: **"deliberadamente não importa langgraph"**.

É uma decisão de arquitetura consciente. Importar a biblioteca significaria adicioná-la às
dependências obrigatórias do `pyproject.toml`, e com ela toda a sua árvore transitiva —
por um módulo que não faz nada. O resultado seria um `pip install` lento e frágil para
quem só quer rodar o servidor do mockup. Enquanto o grafo não existe de verdade, o
projeto permanece **sem nenhuma dependência obrigatória**.

O fluxo pretendido está detalhado em
[06 — Arquitetura-alvo](06-arquitetura-alvo.md#o-grafo-langgraph-pretendido).

---

## `validate_zip.py`

📄 [`validate_zip.py`](../validate_zip.py) · script na raiz, **fora** do pacote

Não é importável como `squad_agentica.validate_zip`. É um script standalone, herança da
fase em que o repositório hospedava um protótipo de upload de arquivos em Express/Node.

### `is_safe_member` — a defesa contra zip-slip

```python
def is_safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    if path.is_absolute():
        return False
    return all(part not in ("", ".", "..") for part in path.parts)
```

**Conceito: zip-slip** (ou *path traversal* em arquivos compactados). Um arquivo ZIP
guarda o caminho de cada item internamente. Nada impede que esse caminho seja malicioso:

```
../../../../Windows/System32/drivers/etc/hosts
/etc/cron.d/backdoor
```

Se o programa que extrai simplesmente concatenar esse nome com a pasta de destino, os
`..` fazem o arquivo escapar dela e sobrescrever qualquer coisa no sistema. É uma
vulnerabilidade clássica e ainda comum.

A função bloqueia os dois vetores:

- `path.is_absolute()` → recusa `/etc/passwd` e `C:\Windows\...`
- `part not in ("", ".", "..")` → recusa qualquer componente que suba um nível

**`PurePosixPath`** é usado de propósito: a especificação do formato ZIP manda usar `/`
como separador, independentemente do sistema. Usar `Path` (que no Windows viraria
`WindowsPath`) faria a análise se comportar de forma diferente entre plataformas — e uma
verificação de segurança que muda conforme o SO é uma verificação quebrada.

**`all(... for ...)`** é uma *generator expression*: `all` retorna `True` só se todos os
elementos satisfizerem a condição, e para na primeira falha.

### `validate_zip` e `main`

`validate_zip()` acumula erros numa lista em vez de levantar exceção no primeiro — assim
um arquivo com três problemas reporta os três de uma vez. Verifica: corrupção
(`archive.testzip()`, que testa o CRC de cada item), arquivo vazio, caminhos inseguros, e
captura `BadZipFile` para o caso de o arquivo nem ser um ZIP.

`main()` varre `uploads/**/*.zip` (o `rglob` é recursivo), imprime `[OK]` ou `[FAIL]` por
arquivo e devolve **exit code** `0` (sucesso) ou `1` (falha) — o contrato universal que o
CI lê para decidir se o job passou. O `sys.exit(main())` propaga esse número para o
sistema operacional.

⚠️ A pasta `uploads/` não existe mais no repositório. Hoje `main()` imprime
*"uploads/ not found; nothing to validate."* e retorna 0 — ou seja, o workflow de CI que
o chama sempre passa sem testar nada. Ver
[09 — Lacunas #5](09-lacunas-e-riscos.md#5-o-workflow-validate-zipyml-não-valida-nada).

---

## Testes

📁 [`tests/`](../tests/) — pasta plana, sem `__init__.py` e sem `conftest.py`.

**Conceito: pytest.** O framework de testes mais usado em Python. Funciona por convenção:
ele varre a pasta procurando arquivos `test_*.py`, dentro deles funções `test_*`, executa
cada uma e reporta as que levantaram exceção. Sem classes obrigatórias, sem registro
manual.

**Conceito: `assert` puro.** Diferente de frameworks que exigem `self.assertEqual(a, b)`, o
pytest reescreve o bytecode dos `assert` para produzir mensagens de erro detalhadas.
Você escreve `assert x == 3` e, se falhar, vê o valor real de `x`.

### `tests/test_package.py`

```python
from squad_agentica import __version__

def test_version():
    assert __version__ == "0.1.0"
```

Teste de fumaça (*smoke test*): garante que o pacote **é importável**. Se o
`pip install -e` não foi feito, ou o src-layout está mal configurado, ou o
`packages.find` aponta para o lugar errado — este teste falha primeiro e explica por quê.
Também trava a versão contra divergência com o `pyproject.toml`.

### `tests/test_aiops.py`

| Teste | O que trava |
|---|---|
| `test_agent_state_shape` | Constrói um `AgentState` completo e verifica identidade, origem e natureza do incidente. Documenta o formato de forma executável. |
| `test_schema_version_is_two` | O schema está na v2 — o bump que acompanhou o bloco de rastreabilidade. |
| `test_traceability_fields_present` | Os nove campos da cadeia de rastreabilidade existem. Impede que um elo suma numa refatoração. |
| `test_remediation_map_keys` | O conjunto exato de sete chaves e duas `platform` específicas. Impede remoção ou renomeação silenciosa. |
| `test_remediation_kinds_are_coherent` | Defeito de código vai para `CODIGO`, terceiro degradado para `EXTERNO` — e **todos os quatro ramos têm exemplo no mapa**. |
| `test_severity_and_algorithm_members` | Os valores dos dois enums originais. |
| `test_origin_and_nature_members` | Os valores de `AnomalyOrigin` e `IncidentNature`. |
| `test_remediation_kind_members` | Os quatro valores de `RemediationKind`. |
| `test_governance_constants` | Os nomes dos modelos e a **relação** `TEMPERATURE_VALIDATOR < TEMPERATURE_COACH`. |
| `test_egress_policy_is_locked_on` | As duas constantes de política de egresso continuam `True`. É o teste que impede alguém de desligar a redação de segredos por conveniência. |
| `test_integrations_registry` | As seis plataformas do registro — e que o GitHub tem `automatic is False`, porque merge sempre exige humano. |
| `test_agent_run_metrics_total_tokens` | A propriedade calculada de `AgentRunMetrics`. |
| `test_rollout_modes_are_ordered_by_authority` | Os três modos de rollout: shadow, canary, full. |
| `test_regression_gate_thresholds` | A **relação** `MIN_REMEDIATION_KIND_ACCURACY > MIN_ROOT_CAUSE_SCORE` — errar o roteamento custa mais do que uma explicação imprecisa. |
| `test_role_stubs_are_not_implemented` | Parametrizado sobre os quatro papéis **e os dois nós adaptadores** — seis testes. |
| `test_function_stubs_are_not_implemented` | Parametrizado sobre `request_human_approval`, `classify_remediation` e `escalate`. |
| `test_regression_gate_stub` | O portão de regressão ainda é stub. |

São **16 funções que rendem 24 testes** (duas são parametrizadas), mais o `test_version` de
`test_package.py` — 25 no total.

**Conceito: `@pytest.mark.parametrize`.** Um decorador que roda a mesma função de teste
várias vezes, com valores diferentes:

```python
@pytest.mark.parametrize(
    "role_cls",
    [Planner, Explainer, Validator, Coach, TraceabilityNode, CodeRemediationNode],
)
def test_role_stubs_are_not_implemented(role_cls):
    with pytest.raises(NotImplementedError):
        role_cls()(state={})
```

Isso conta como **6 testes**, não 1 — cada um com seu próprio resultado no relatório. É o
que faz 16 funções virarem 24 testes coletados.

**Conceito: `with pytest.raises(X)`.** Inverte a lógica do teste: o bloco *deve* levantar
a exceção `X`. Se não levantar, o teste falha. É como se afirma que um comportamento
negativo está garantido.

Note a chamada dupla `role_cls()(state={})`: o primeiro par de parênteses **instancia** a
classe, o segundo a **chama** (via `__call__`).

Testar que um stub continua stub parece estranho à primeira vista, mas é intencional:
enquanto o teste existir, ninguém implementa o papel pela metade sem também atualizar a
suíte — a implementação vem acompanhada da remoção deliberada deste teste.

### O que não é testado

`serve.py`, `Checkpoint`/`CheckpointStore`, `validate_zip.py` e **todo o `prototype/`** —
o mockup não tem nenhum teste automatizado na suíte do repositório. Ver
[09 — Lacunas](09-lacunas-e-riscos.md).

---

[← Ambiente e ferramentas](02-ambiente-e-ferramentas.md) · [Índice](README.md) · [Próximo: Frontend / protótipo →](04-frontend-prototype.md)
