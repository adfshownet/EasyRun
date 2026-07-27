# Documentação do EasyRun

Documentação completa do projeto: o que cada arquivo é, por que existe, o vocabulário
técnico envolvido e o processo end-to-end — tanto o do desenvolvedor quanto o do
incidente que o produto simula.

**Premissa desta documentação:** ela não pressupõe conhecimento prévio de Python,
ambientes virtuais, AWS ou AIOps. Todo termo técnico é explicado na primeira vez que
aparece e tem verbete no [glossário](08-glossario.md).

---

## Aviso importante antes de qualquer coisa

O EasyRun hoje é um **protótipo**, e é fundamental não confundir as camadas:

| Camada | Estado real |
|---|---|
| `prototype/` (o dashboard bonito) | **Mockup** — HTML/JS estático, dados fixos no código, sem backend |
| `src/squad_agentica/aiops/` | **Contrato/stub** — tipos, portas e constantes; todo papel levanta `NotImplementedError` |
| `src/squad_agentica/serve.py` | **Implementado** — servidor HTTP local, é o único código que faz algo |
| ServiceNow, Datadog, IUClick, Devin, LangGraph, AWS | **Planejado** — não existe uma linha desse código no repositório |

Detalhe completo em [01 — Visão geral](01-visao-geral.md#quadro-de-maturidade).

---

## Índice

| # | Documento | O que responde |
|---|---|---|
| 01 | [Visão geral](01-visao-geral.md) | O que é o EasyRun, que problema resolve, o que já existe e o que é promessa |
| 02 | [Ambiente e ferramentas](02-ambiente-e-ferramentas.md) | Para que serve o `.venv`, o `pyproject.toml`, o `pip install -e`, o `.gitignore` |
| 03 | [Arquitetura do código](03-arquitetura-do-codigo.md) | Cada módulo Python, linha a linha, com o conceito da linguagem explicado antes |
| 04 | [Frontend / protótipo](04-frontend-prototype.md) | Como o dashboard funciona: o runtime `dc`, as 9 telas, o motor de simulação |
| 05 | [Processo end-to-end](05-processo-end-to-end.md) | As duas jornadas: ciclo do desenvolvedor e ciclo do incidente AIOps |
| 06 | [Arquitetura-alvo](06-arquitetura-alvo.md) | LangGraph, a stack Lang*, os 13 pilares, AWS — o que ainda vai ser construído |
| 07 | [CI/CD e Git](07-ci-cd-e-git.md) | GitHub Actions campo a campo, modelo de branches, integração com o VS Code |
| 08 | [Glossário](08-glossario.md) | ~100 verbetes de A a Z, de "agente" a "zip-slip" |
| 09 | [Lacunas e riscos](09-lacunas-e-riscos.md) | Divergências e armadilhas reais encontradas no repositório |
| 10 | [Ecossistema da empresa](10-ecossistema-da-empresa.md) | ServiceNow, Datadog, IUClick, Devin, GitHub: o que a squad lê, escreve e onde para |
| 11 | [MLOps e LLMOps](11-mlops-llmops.md) | Observabilidade da própria esteira, avaliação e rollout seguro de agentes |
| 12 | [Segurança](12-seguranca.md) | A auditoria feita antes de levar o projeto para a empresa, o que ela achou e como verificar tudo de novo |

---

## Trilhas de leitura

### "Preciso apresentar o EasyRun para alguém" (≈ 35 min)

1. [01 — Visão geral](01-visao-geral.md) — o pitch e o quadro de maturidade honesto
2. [10 — Ecossistema da empresa](10-ecossistema-da-empresa.md) — **onde o EasyRun se encaixa no que já existe**; é o que faz a plateia reconhecer o próprio dia a dia
3. [05 — Processo end-to-end](05-processo-end-to-end.md#b-ciclo-do-incidente-aiops) — a jornada B, o fluxo do incidente
4. [11 — MLOps e LLMOps](11-mlops-llmops.md#o-que-isso-muda-na-conversa-com-o-comitê) — as três perguntas que decidem a aprovação
5. [04 — Frontend](04-frontend-prototype.md#anatomia-da-ui-as-9-telas) — para navegar o dashboard ao vivo com segurança

Rode o mockup enquanto apresenta: `squad-agentica-serve` (ver [02](02-ambiente-e-ferramentas.md)).
Sugestão de roteiro: comece pelo cenário **ANM-2047** (mostra o fluxo básico com um gate),
depois vá para o **INC-3312** (código → Devin → PR → GMUD, com dois gates) e feche com o
**INC-3377** (a squad sabendo desistir). Com a prop `velocidade` em `2x`, os três cabem em
poucos minutos.

### "Vou mexer no código" (≈ 50 min)

1. [02 — Ambiente e ferramentas](02-ambiente-e-ferramentas.md) — montar o ambiente e entender por quê
2. [03 — Arquitetura do código](03-arquitetura-do-codigo.md) — o pacote Python inteiro
3. [06 — Arquitetura-alvo](06-arquitetura-alvo.md#o-caminho-daqui-até-lá) — a ordem sugerida de implementação
4. [07 — CI/CD e Git](07-ci-cd-e-git.md) — o que roda quando você dá push
5. [09 — Lacunas e riscos](09-lacunas-e-riscos.md) — **leia antes de editar**, tem armadilha silenciosa aqui

### "Quero entender como isso conversa com o ServiceNow / Datadog / IUClick / Devin"

[10 — Ecossistema da empresa](10-ecossistema-da-empresa.md), do começo ao fim. Se a dúvida
for de segurança ("vão mandar nosso código para fora?"), vá direto para
[a política de código](10-ecossistema-da-empresa.md#a-política-de-código).

### "Só quero rodar isso na minha máquina" (≈ 5 min)

Vá direto para [02 — Ambiente e ferramentas → Receita completa](02-ambiente-e-ferramentas.md#receita-completa-do-zero-ao-mockup-rodando).

### "Posso confiar neste repositório?" (≈ 10 min)

[12 — Segurança](12-seguranca.md) — a auditoria completa (código, histórico, binários,
dependências, CI), os pontos corrigidos e um checklist para refazer a verificação por
conta própria, sem confiar no documento.

### "Não entendi um termo"

[08 — Glossário](08-glossario.md).

---

## Como esta documentação se mantém honesta

Todos os números, nomes e valores citados aqui foram lidos diretamente do código-fonte
deste repositório, não de memória ou de especificação externa. Quando um dado vem do
mockup (e portanto é fictício, inventado para a demonstração), isso está dito
explicitamente — por exemplo, as métricas de MTTR da aba Avaliação.

Se você alterar código, atualize o documento correspondente no mesmo commit.
