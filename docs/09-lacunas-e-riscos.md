# 09 — Lacunas e riscos

[← Glossário](08-glossario.md) · [Índice](README.md)

---

Divergências, acoplamentos frágeis e armadilhas reais encontradas no repositório. **Este
documento registra; não corrige.** Cada item traz o que é, por que importa e uma sugestão
de correção — a decisão de aplicar é de quem mantém o projeto.

Nenhum destes é bug de execução: hoje tudo roda. São riscos de manutenção — o tipo de
problema que só aparece quando alguém edita a coisa errada seis meses depois.

**Prioridade sugerida:** 1, 4, 15 (armadilhas silenciosas, quebram sem avisar) → 5, 14, 16
(falsa sensação de cobertura ou de segurança) → 2, 3 (portabilidade) → 6, 11, 13 (higiene)
→ 8, 9, 10, 12 (informativos). O item 7 está resolvido e fica no documento como registro.

### Resolvido nesta rodada

| Antes | Agora |
|---|---|
| **#7 — `export/` era espelho manual** | Passou a ser gerado por [`tools/sync-export.mjs`](../tools/sync-export.mjs), e a sincronia é verificada no CI. |
| **O protótipo não tinha cobertura automatizada** | [`tools/check-prototype.mjs`](../tools/check-prototype.mjs) roda quatro verificações a cada push que toque `prototype/` ou `tools/`. |
| **`schema_version` era só documentação** | Subiu de 1 para 2 ao ganhar o bloco de rastreabilidade. O campo saiu de "boa prática documentada" para "usado de verdade". |
| **Guardrails do console eram HTML estático** | Agora renderizam a lista real e refletem os toggles da tela de Configuração. |

---

## 1. Fonte da verdade duplicada entre Python e HTML

**O que é.** As mesmas constantes existem em dois lugares, escritas à mão em cada um.

| Dado | No Python | No mockup |
|---|---|---|
| Mapa de remediação | `REMEDIATION_MAP` em [`remediation.py`](../src/squad_agentica/aiops/remediation.py) | `remediacaoLista` em [`EasyRun.dc.html`](../prototype/EasyRun.dc.html) |
| Política de modelos | [`governance.py`](../src/squad_agentica/aiops/governance.py) | `finopsCards` |
| Papéis do grafo | docstrings de [`roles.py`](../src/squad_agentica/aiops/roles.py) | `mapaLangGraph` |
| Severidades e algoritmos | [`severity.py`](../src/squad_agentica/aiops/severity.py) | textos dos cenários |
| Natureza da remediação | `RemediationKind` em `remediation.py` | `naturezaDef()` |
| Registro de integrações | `INTEGRATIONS` em [`integrations.py`](../src/squad_agentica/aiops/integrations.py) | `integracoesLista` |
| Política de egresso | [`observability.py`](../src/squad_agentica/aiops/observability.py) | `politicaCodigo` e o guardrail G-05 |

**Por que importa.** Nada liga as duas cópias. Acrescentar uma entrada ao
`REMEDIATION_MAP` não muda o mockup, e `test_remediation_map_keys` continua verde — porque
ele só olha o Python. A apresentação passa a mostrar informação desatualizada sem que
nenhum sinal seja emitido. E a superfície **cresceu** nesta rodada: são cinco pares
duplicados agora, não dois.

Já há divergência de redação: o Python diz `"Escalonamento Horizontal (Out)"`; o HTML diz
`"Escalonamento horizontal · natureza INFRA"`. Inofensivo hoje, sintomático do padrão.

**Sugestão.** Enquanto o mockup for descartável, o custo de sincronizar não se paga —
basta documentar (feito aqui) e conferir na revisão. Quando o frontend real chegar, esses
dados devem vir da API. Se o mockup sobreviver, exportar um `data.json` a partir do Python
e fazer o HTML lê-lo resolve na raiz.

---

## 2. `serve.py` depende de estar num checkout do repositório

**O que é.**

```python
PROTOTYPE_DIR = Path(__file__).resolve().parents[2] / "prototype"
```

Sobe três níveis a partir de `src/squad_agentica/serve.py` para achar a raiz do repositório
e, dali, a pasta `prototype/`.

**Por que importa.** Isso assume um layout específico de disco. Funciona com
`pip install -e` (o código fica no checkout). **Quebra** com `pip install` comum: o arquivo
vai para `site-packages/squad_agentica/serve.py`, e `parents[2]` aponta para dentro do
ambiente virtual, onde não existe `prototype/`. O servidor sobe e devolve 404 em tudo.

O `prototype/` também não está declarado como *package data* no `pyproject.toml`, então
nem seria empacotado.

**Sugestão.** Se o mockup nunca for distribuído, documentar a limitação basta. Se for,
mover `prototype/` para dentro do pacote, declará-lo como package data e localizá-lo via
`importlib.resources`. Uma melhoria barata no meio-termo: falhar com mensagem clara se
`PROTOTYPE_DIR` não existir, em vez de servir 404 silenciosamente.

---

## 3. O F5 do VS Code só funciona no Windows

**O que é.** [`.vscode/tasks.json`](../.vscode/tasks.json):

```json
"command": "${workspaceFolder}/.venv/Scripts/python.exe"
```

`Scripts/` e `.exe` são específicos do Windows — no Linux e no macOS o caminho é
`.venv/bin/python`.

**Por que importa.** Quem clonar o projeto no Linux ou Mac aperta F5 e recebe "command not
found", sem indicação do motivo. Como `tasks.json` é versionado (exceção explícita no
`.gitignore`), ele é infraestrutura compartilhada — e essa infraestrutura só serve a
metade do time.

**Sugestão.** Usar a substituição de variável do VS Code para o interpretador selecionado:

```json
"command": "${command:python.interpreterPath}"
```

Ou declarar `windows` / `linux` / `osx` como variantes dentro da própria task.

---

## 4. O `problemMatcher` está acoplado ao texto do `print()`

**O que é.** O `tasks.json` só considera o servidor pronto quando aparece uma linha
começando com `Serving`:

```json
"beginsPattern": "^Serving",
"endsPattern": "^Serving"
```

E o [`serve.py`](../src/squad_agentica/serve.py) emite exatamente:

```python
print(f"Serving {PROTOTYPE_DIR} at {url} (Ctrl+C to stop)")
```

**Por que importa.** É um contrato invisível entre dois arquivos que não se referenciam.
Traduzir a mensagem para português, trocar por `logging`, ou simplesmente reescrever para
`"Servidor em {url}"` faz o F5 **travar esperando eternamente** — o servidor sobe, mas o
VS Code nunca abre o Chrome. E o sintoma não aponta para a causa: nada indica que o problema
está numa string de log.

**Sugestão.** Um comentário no `serve.py` acima do `print`, avisando que o texto é contrato
com o `tasks.json`. É a correção de menor custo e maior efeito desta lista. Alternativa
mais robusta: tornar o `beginsPattern` mais frouxo (ex.: casar a URL `http://localhost`).

---

## 5. O workflow `validate-zip.yml` não valida nada

**O que é.** [`.github/workflows/validate-zip.yml`](../.github/workflows/validate-zip.yml)
dispara em `uploads/**` e roda [`validate_zip.py`](../validate_zip.py). A pasta `uploads/`
foi removida no commit `1fe0348`, junto com o protótipo Express.

**Por que importa.** Duplamente inerte: o filtro de `paths` nunca casa, e se casasse o
script imprimiria *"uploads/ not found; nothing to validate."* e retornaria 0. Na aba
Actions do GitHub, o repositório aparenta ter dois workflows de verificação — na prática
tem um.

Relacionado: o `.gitignore` ainda carrega `node_modules/`, `uploads/*` e `!uploads/.gitkeep`
da mesma fase morta.

**Sugestão.** Ou remover script + workflow + regras órfãs do `.gitignore` (se uploads não
voltam), ou recriar `uploads/.gitkeep` e documentar o propósito (se voltam). O estado atual
— presente mas inerte — é o pior dos três.

---

## 6. O `Standalone.html` está desatualizado e não pode ser regerado

**O que é.** `prototype/EasyRun - Standalone.html` é um bundle autocontido de 381 KB. Está
agora **duas gerações atrás**: foi gerado antes dos 4 cenários originais, e desde então o
protótipo ganhou 3 cenários novos, 2 agentes, 2 telas e a cadeia de rastreabilidade. O
gerador (`dc-runtime/`) não está neste repositório.

**Por que importa.** É o arquivo com o nome mais convidativo da pasta — "Standalone" sugere
"abra este". Quem o abrir vai apresentar uma versão antiga do produto sem saber. E não há
como corrigir sem a ferramenta de build.

**Sugestão.** Renomear para algo como `EasyRun-Standalone.OBSOLETO.html`, ou remover.
O README já avisa em texto, mas o nome do arquivo comunica mais alto que o README.

---

## 7. O `export/` é espelho manual

**O que é.** [`prototype/export/EasyRun-src.dc.html`](../prototype/export/EasyRun-src.dc.html)
é cópia byte a byte de [`EasyRun.dc.html`](../prototype/EasyRun.dc.html), exceto pelo
caminho do `<script src>` e por um `<template>` de thumbnail. A sincronização é manual.

**Por que importa.** Duas cópias de 96 KB mantidas à mão divergem no primeiro esquecimento
— e a divergência é silenciosa: nenhum teste, lint ou CI compara os arquivos.

**Resolvido.** O espelho agora é gerado por
[`tools/sync-export.mjs`](../tools/sync-export.mjs), e a quarta verificação de
[`tools/check-prototype.mjs`](../tools/check-prototype.mjs) falha se os dois divergirem —
com a mensagem dizendo exatamente qual comando rodar. O CI executa isso a cada push que
toque `prototype/`.

**Risco residual:** regenerar continua sendo um passo manual depois de editar a fonte. A
diferença é que agora esquecer **falha visivelmente** em vez de passar despercebido. Segue
valendo a alternativa mais radical: eliminar o `export/` se ele não tiver consumidor
identificado.

---

## 8. `pytest` sem instalação falha com ImportError

**O que é.** Não há `[tool.pytest.ini_options]` no `pyproject.toml`, nem `conftest.py`, nem
`tests/__init__.py`. O `import squad_agentica` dos testes depende inteiramente do
`pip install -e ".[dev]"` ter sido feito.

**Por que importa.** Rodar `pytest` num clone recém-feito produz `ModuleNotFoundError`, que
pode ser lido como "o projeto está quebrado" em vez de "faltou instalar".

**Isto é uma consequência desejada do [src-layout](03-arquitetura-do-codigo.md#por-que-src-layout)**,
não um defeito — é justamente o que garante que os testes rodem contra o pacote instalado.
Fica registrado como armadilha de primeira execução, não como bug.

**Sugestão.** Nenhuma mudança de código. O README e o
[doc 02](02-ambiente-e-ferramentas.md#receita-completa-do-zero-ao-mockup-rodando) já trazem
a ordem correta dos comandos.

---

## 9. A especificação citada nos docstrings não está no repositório

**O que é.** Seis módulos de `aiops/` citam "spec section 3", "spec section 4" ou
"spec section 5". Esse documento de arquitetura AIOps não está versionado aqui.

**Por que importa.** As referências apontam para o vazio. Um leitor que queira entender
*por que* a severidade tem exatamente três níveis, ou de onde vem a metodologia Datadog dos
algoritmos, não tem para onde ir. E a especificação é a fonte da qual todo o contrato
deriva — se ela mudar fora do repositório, o código fica silenciosamente desatualizado.

**Sugestão.** Versionar a especificação em `docs/spec/`, ou substituir as citações por links
para onde ela realmente vive. Enquanto isso, os documentos
[05](05-processo-end-to-end.md) e [06](06-arquitetura-alvo.md) reconstroem o conteúdo a
partir do código e do mockup.

---

## 10. `aiops/__init__.py` vazio torna os imports verbosos

**O que é.** O arquivo tem 0 bytes: nenhum re-export. Consumidores precisam importar de
cada submódulo:

```python
from squad_agentica.aiops.state import AgentState
from squad_agentica.aiops.severity import Severity, DetectionAlgorithm
from squad_agentica.aiops.remediation import REMEDIATION_MAP
```

**Por que importa.** Mais uma decisão de estilo do que um problema. O custo é ergonômico:
cada consumidor precisa saber a organização interna do subpacote, e mover uma classe de
módulo quebra todos os imports externos.

**Sugestão.** Se a API pública do subpacote estabilizar, re-exportar os nomes principais com
um `__all__` explícito. Enquanto tudo é stub, não há pressa.

---

## 11. Numeração dos guardrails inconsistente no mockup

**O que é.** A aba Configuração lista os guardrails na ordem `g1` = "Aprovação humana p/
rollback", `g2` = "Limite de ações de escrita". Mas os cenários citam:

- ANM-2047: *"Guardrail **G-02** interceptou o passo 2"* — para o **rollback**;
- ANM-2091: gate com `guardrail: '**G-01** · escalonamento acima do orçamento exige humano'`;
- Chat: *"rollback em produção exige aprovação humana (**G-02**)"*.

Ou seja, o rollback é o guardrail nº 1 na lista de configuração e o nº 2 nos eventos, e
"escalonamento acima do orçamento" aparece como G-01 sem existir na lista de configuração.

**Por que importa.** Só na apresentação — alguém atento pode perguntar, e não há resposta
boa. Não afeta execução.

**Sugestão.** Escolher uma numeração e propagar para os quatro lugares (`grDefs`, textos dos
gates, textos do log, resposta do chat).

---

## 12. Step Functions e LangGraph se sobrepõem

**O que é.** A arquitetura-alvo cita **AWS Step Functions** como orquestrador (papel do
Maestro, pilar 10) **e** **LangGraph** como grafo de estados dos quatro papéis. São duas
máquinas de estado para o mesmo fluxo.

**Por que importa.** Não é contradição necessária — é comum usar Step Functions no nível
macro (disparo, retentativas, integração com serviços AWS) e um grafo de agentes dentro de
uma etapa. Mas a divisão não está escrita em lugar nenhum, e cada uma traz seu próprio
mecanismo de checkpoint e de espera por humano. Implementar os dois sem decidir a fronteira
produz duplicação de estado — exatamente o tipo de coisa difícil de desfazer depois.

**Sugestão.** Registrar a decisão (quem é responsável por quê, e onde o estado autoritativo
vive) antes de escrever `build_graph()`.

---

## 13. Dois cenários de deployment de modelo não reconciliados

**O que é.** Duas telas do mesmo protótipo apontam para stacks de LLM diferentes:

| Onde | Modelos |
|---|---|
| Cards dos agentes (Console/Configuração) | **Claude Sonnet / Haiku e Titan, servidos pelo gateway MCP do IARA** |
| Aba FinOps e [`governance.py`](../src/squad_agentica/aiops/governance.py) | **Qwen 2.5-coder:32b e Qwen 2.5:7b, local via Ollama** |

**Por que importa.** São dois modelos de operação legítimos — via gateway corporativo
(IARA) e local/soberano — com implicações opostas de custo, latência e conformidade. Numa
apresentação, a pergunta "afinal, roda pelo IARA ou na minha GPU?" não tem resposta no
material atual. E há uma restrição a mais: como o acesso a LLMs é governado pelo time
IARA, a opção local via Ollama só existe se entrar no catálogo do próprio IARA — não é uma
decisão que a squad toma sozinha.

**Sugestão.** Assumir explicitamente que são dois cenários de deployment e rotulá-los como
tal na aba FinOps ("Opção A: modelos gerenciados via IARA · Opção B: Ollama local, sujeito
à governança do IARA"), ou escolher um.

---

## 14. O CI testa só Python 3.12, mas o projeto declara 3.10+

**O que é.** O [`pyproject.toml`](../pyproject.toml) diz `requires-python = ">=3.10"`. O
[workflow](../.github/workflows/tests.yml) instala **apenas** o 3.12.

**Por que importa.** A promessa de compatibilidade com 3.10 e 3.11 não é verificada por
ninguém. Basta alguém usar sintaxe introduzida no 3.11 ou 3.12 para que o CI continue verde
enquanto o usuário de 3.10 recebe `SyntaxError`.

**Sugestão.** Matriz de versões no workflow:

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
```

Custa três vezes mais minutos de CI numa suíte de 25 testes — irrelevante — e transforma a
declaração do `pyproject.toml` em promessa verificada.

---

## 15. A política de egresso é contrato, não implementação

**O que é.** As constantes `REDACTION_REQUIRED_BEFORE_EGRESS` e
`REPOSITORY_ALLOWLIST_REQUIRED` estão em
[`observability.py`](../src/squad_agentica/aiops/observability.py), travadas por teste. O
guardrail G-05 aparece como um passo visível no cenário INC-3312 do protótipo.

**Nada disso executa.** Não existe redator de segredos, não existe allowlist, não existe
chamada ao Devin. São uma declaração de intenção com força de contrato — nada mais.

**Por que importa.** É a lacuna com maior potencial de mal-entendido numa apresentação.
Alguém pode assistir ao cenário INC-3312, ver *"variáveis de ambiente e tokens removidos do
contexto antes do envio ao agente externo"* e concluir que a proteção existe. Ela não
existe: é o requisito escrito, não a implementação.

**Sugestão.** Ao apresentar o cenário de código, dizer explicitamente que aquele passo é o
requisito de segurança sendo declarado, não executado. E, na implementação, essa é a peça
que precisa vir **antes** da primeira chamada real ao Devin — não depois.

---

## 16. A esteira de código depende de um campo frágil da CMDB

**O que é.** O ramo `CODIGO` só existe porque o Elo consegue descobrir, na CMDB do
ServiceNow, **qual repositório sustenta o item de configuração afetado**. É o campo
`ConfigurationItem.repository`, declarado `Optional[str]` justamente por isso.

**Por que importa.** Em qualquer CMDB real, esse é um dos campos com maior chance de estar
vazio, desatualizado ou apontando para um repositório arquivado — porque não é usado no dia
a dia por ninguém, e portanto ninguém percebe quando apodrece. Um protótipo que sempre
encontra o repositório dá uma impressão otimista da taxa de sucesso do ramo de código.

**Sugestão.** Duas frentes, e a primeira é organizacional: tratar a qualidade desse campo
como pré-requisito do projeto, com uma medição antes de começar ("de X serviços, quantos
têm repositório mapeado?"). Na esteira, degradar com elegância — sem repositório, escalar
ao time dono **com o diagnóstico pronto**, que ainda economiza a maior parte do tempo. Já
está na lista de hardening da tela de Arquitetura, mas merece um cenário próprio no
protótipo.

---

## 17. O cenário de código é longo para uma demonstração ao vivo

**O que é.** O `inc3312` tem 23 passos e dois gates. Na velocidade padrão (1,9 s por passo)
são cerca de 45 segundos de log, mais duas paradas esperando decisão humana.

**Por que importa.** É o cenário mais importante para vender a ideia, e também o mais fácil
de perder a plateia no meio. Os quatro cenários de infraestrutura levam ~30 s.

**Sugestão.** Não encurtar — os passos são o conteúdo. Em vez disso, apresentar com a prop
`velocidade` em `2x` ou `3x`, e usar as duas paradas do HITL como pontos naturais para
falar (é exatamente onde a atenção da sala volta). A prop já existe e não exige mudança
nenhuma no código.

---

## Não é lacuna: decisões deliberadas

Para evitar que alguém "corrija" o que está certo:

| Aparência de problema | Por que é intencional |
|---|---|
| Papéis levantam `NotImplementedError` | São stubs declarados. O teste `test_role_stubs_are_not_implemented` **garante** que continuem assim até a implementação real. |
| `graph.py` não importa `langgraph` | Decisão explícita no docstring: evita dependência pesada por um módulo que ainda não faz nada. O projeto segue sem dependências obrigatórias. |
| O chat do mockup não usa LLM | É um mockup. Um roteador de palavra-chave entrega a demonstração sem custo de inferência nem latência. |
| O Executor é "Determinístico", sem modelo | É o único agente que muda o mundo real. Não-determinismo ali é risco, não recurso. |
| `serve.py` envia `Cache-Control: no-store` | Sem isso, editar o protótipo e recarregar mostraria a versão antiga. |
| Elo e Artífice são "agentes" na tela e "nós adaptadores" no grafo | Os dois modelos estão certos no seu nível: um é como a squad se apresenta a pessoas, o outro é como o código se organiza. |
| `integrations.py` não importa nenhum SDK | Mantém o pacote sem dependências obrigatórias e o domínio independente de fornecedor. É a arquitetura hexagonal, não preguiça. |
| A GMUD abre sozinha mas nunca é aprovada sozinha | Automatizar o preenchimento não é automatizar a decisão. Essa fronteira é o produto. |
| O ramo de código para **duas** vezes | Aprovar um patch e aprovar uma janela de produção são autoridades diferentes. |
| Campos de rastreio ficam `None` em vários cenários | A ausência informa: sem repositório e sem PR, o caso se resolveu em runtime. |
| Os testes checam relação, não valor (`TEMPERATURE_VALIDATOR < TEMPERATURE_COACH`) | Trava o princípio de design sem engessar os números. |

---

## Cobertura de testes: o que não é verificado

| Componente | Testado? |
|---|---|
| `severity.py`, `state.py`, `remediation.py`, `governance.py`, `roles.py` | ✅ |
| `integrations.py` (registro), `observability.py`, `evaluation.py` | ✅ |
| `squad_agentica.__version__` | ✅ |
| `serve.py` | ❌ |
| `checkpoint.Checkpoint` / `CheckpointStore` | ❌ |
| `validate_zip.py` (incluindo `is_safe_member`, que é código de segurança) | ❌ |
| Todo o `prototype/` | ✅ por [`tools/check-prototype.mjs`](../tools/check-prototype.mjs), fora do pytest |

O caso mais notável é o `validate_zip.py`: `is_safe_member` implementa uma defesa contra
zip-slip e não tem um único teste. Se alguém "simplificar" a condição e deixar passar `..`,
nada acusa. São três casos de teste que valeriam a pena caso o script continue no repositório.

Sobre o protótipo: ele agora tem cobertura automatizada em
[`tools/check-prototype.mjs`](../tools/check-prototype.mjs), versionado e rodando no CI.
São quatro verificações — consistência dos cenários, execução do motor nos dois caminhos,
conferência do template contra os dados, e sincronia do espelho. Detalhe em
[`tools/README.md`](../tools/README.md).

Vale registrar que elas já pagaram o custo: acharam **dois passos de plano que ficavam sem
resolução no caminho de rejeição** e **oito `hint-placeholder-count` desatualizados** — nada
disso quebrava a tela, e nada disso seria notado numa revisão visual.

---

[← Glossário](08-glossario.md) · [Índice](README.md)
