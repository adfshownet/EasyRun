# 07 — CI/CD e Git

[← Arquitetura-alvo](06-arquitetura-alvo.md) · [Índice](README.md) · [Próximo: Glossário →](08-glossario.md)

---

## O que é CI/CD

**CI** (*Continuous Integration*, integração contínua) — a prática de verificar
automaticamente cada mudança enviada ao repositório: rodar testes, checar estilo, tentar
construir o pacote. O objetivo é detectar problemas em minutos, não em semanas.

**CD** (*Continuous Delivery/Deployment*, entrega/implantação contínua) — o passo seguinte:
publicar automaticamente o que passou. **Este projeto ainda não tem CD** — nada é publicado
em lugar nenhum. Só CI.

O valor concreto do CI aqui: o servidor do GitHub monta uma máquina **limpa**, sem seu
`.venv`, sem seus caches, sem aquela biblioteca que você instalou em janeiro. Se o teste
passa lá, passa na máquina de qualquer pessoa.

## O que é um workflow do GitHub Actions

**GitHub Actions** é o sistema de CI integrado ao GitHub. A hierarquia:

| Conceito | O que é |
|---|---|
| **Workflow** | Um arquivo `.yml` em `.github/workflows/` descrevendo um processo automatizado |
| **Evento** (`on`) | O que dispara o workflow: push, pull request, agenda, acionamento manual |
| **Job** | Um bloco de trabalho, executado numa máquina própria. Jobs rodam em paralelo por padrão |
| **Runner** | A máquina virtual que executa o job (`ubuntu-latest` = Ubuntu gerenciado pelo GitHub) |
| **Step** | Um passo dentro do job: ou um comando (`run`) ou uma ação reutilizável (`uses`) |
| **Action** | Um componente pronto, publicado por alguém, referenciado por `usuário/nome@versão` |

**YAML** é o formato dos arquivos: indentação define hierarquia, `-` indica itens de lista.
Espaços importam; tabulação é erro de sintaxe.

---

## `tests.yml` — o workflow de testes

📄 [`.github/workflows/tests.yml`](../.github/workflows/tests.yml)

```yaml
name: Tests
```

O nome exibido na aba **Actions** do GitHub e nos checks do pull request.

```yaml
on:
  push:
    paths:
      - 'src/**'
      - 'tests/**'
      - 'pyproject.toml'
      - '.github/workflows/tests.yml'
  pull_request:
    paths:
      - 'src/**'
      - 'tests/**'
      - 'pyproject.toml'
      - '.github/workflows/tests.yml'
```

Dois gatilhos: **push** (qualquer envio para qualquer branch) e **pull_request** (abertura
ou atualização de PR). Ambos com o mesmo **filtro de `paths`**.

O filtro diz: *só rode se algum arquivo alterado casar com estes padrões*. O `**` casa
qualquer profundidade de subdiretório.

Por que filtrar? Economia e ruído. Um commit que só altera o `README.md` ou o mockup em
`prototype/` não pode quebrar teste Python nenhum — rodar a suíte ali gastaria minutos de
CI e poluiria o histórico com checks irrelevantes.

Note que `.github/workflows/tests.yml` está na própria lista: alterar o workflow dispara o
workflow, para você validar a mudança imediatamente.

⚠️ **Consequência prática:** editar apenas `prototype/` **não dispara nada**. O mockup não
tem cobertura automatizada de espécie alguma.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      contents: read
```

`test` é o identificador do job. `runs-on: ubuntu-latest` pede um runner Linux gerenciado
pelo GitHub — descartado ao fim da execução, o que garante ambiente limpo toda vez.

`permissions: contents: read` é uma boa prática de segurança: **princípio do menor
privilégio**. Por padrão, o token que o Actions injeta no job pode ter permissão de escrita
no repositório. Este workflow só precisa **ler** o código para rodar testes, então a
permissão é restringida explicitamente. Se uma dependência comprometida tentasse abusar do
token, não conseguiria criar commits, branches ou releases.

```yaml
    steps:
      - uses: actions/checkout@v4
```

Baixa o código do repositório para dentro do runner. Sem este passo, a máquina está vazia.
O `@v4` fixa a versão maior da ação — atualizações compatíveis entram automaticamente,
mudanças que quebram não.

```yaml
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
```

Instala e configura o Python 3.12 no runner. `with:` passa parâmetros para a ação.

⚠️ O [`pyproject.toml`](../pyproject.toml) declara `requires-python = ">=3.10"`, mas o CI
testa **somente** 3.12. Se alguém usar sintaxe de 3.12 que não existe em 3.10, o CI não
percebe e o usuário de 3.10 quebra. A solução padrão é uma *matriz* de versões:

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
```

Ver [09 #14](09-lacunas-e-riscos.md#14-o-ci-testa-só-python-312-mas-o-projeto-declara-310).

```yaml
      - name: Install package
        run: pip install -e ".[dev]"

      - name: Run tests
        run: pytest
```

Os mesmos dois comandos que você roda localmente. Note que **não há `venv` no CI** — o
runner é descartável, então instalar no Python do sistema dele é seguro e mais rápido.

O CI usa o **exit code** para decidir: `pytest` retorna 0 se tudo passou, diferente de 0 se
algo falhou. Qualquer step com exit code diferente de 0 interrompe o job e o marca em
vermelho.

### O que acontece quando falha

O check do PR fica vermelho, e a aba Actions mostra o log completo com a saída do `pytest`
— qual teste falhou, em que linha, com que valores. O fluxo é: corrigir localmente, rodar
`pytest`, e dar push de novo (o mesmo PR reexecuta automaticamente).

---

## `validate-zip.yml` — o workflow que não valida nada

📄 [`.github/workflows/validate-zip.yml`](../.github/workflows/validate-zip.yml)

```yaml
name: Validate ZIP Files

on:
  push:
    paths:
      - 'uploads/**'
      - 'validate_zip.py'
  pull_request:
    paths:
      - 'uploads/**'
      - 'validate_zip.py'

jobs:
  validate:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Validate ZIP file contents
        run: python validate_zip.py
```

Estruturalmente idêntico ao anterior, com uma diferença: não instala nada, porque
[`validate_zip.py`](../validate_zip.py) usa só a biblioteca padrão.

⚠️ **Este workflow é hoje um no-op.** A pasta `uploads/` foi removida do repositório no
commit `1fe0348`, junto com o protótipo Express. Duas consequências:

1. O filtro `paths: uploads/**` nunca casa — não existe arquivo lá.
2. Mesmo se disparasse, `main()` imprimiria *"uploads/ not found; nothing to validate."* e
   retornaria 0.

Ou seja: um workflow que sempre passa sem verificar nada. Ver
[09 #5](09-lacunas-e-riscos.md#5-o-workflow-validate-zipyml-não-valida-nada).

---

## O contexto histórico: o protótipo Express

Entender por que existe `validate_zip.py` num projeto sem uploads exige olhar o histórico.

O repositório passou por três fases:

| Fase | Commits | O que era |
|---|---|---|
| **1. Upload em Node** | `5550502` … `82ecc63` | Servidor Express + Multer, com `POST /upload`, `GET /files` e uma pasta `uploads/`. Foi quando `validate_zip.py` e seu workflow foram criados. |
| **2. Protótipo visual** | `1fe0348` "protótipo" | O Express foi **removido** (`package.json`, `server.js`, `public/`, `uploads/`) e o dashboard `.dc.html` entrou no lugar. |
| **3. Pacote Python** | `e63eab4` … `0d017ac` | Reorganização em pacote (`src/squad_agentica`), testes, CI de testes e task do VS Code. |

O que ficou para trás da fase 1: o script `validate_zip.py`, o workflow
`validate-zip.yml`, e as regras `node_modules/` e `uploads/*` no
[`.gitignore`](../.gitignore).

Não é lixo perigoso — o script é correto e a defesa contra zip-slip que ele implementa é
boa (ver [03](03-arquitetura-do-codigo.md#validate_zippy)). É apenas infraestrutura órfã,
que confunde quem chega e dá uma falsa sensação de cobertura de CI.

---

## Modelo de branches

Branches locais e remotas hoje:

| Branch | Papel |
|---|---|
| `main` | Branch padrão. O `origin/HEAD` aponta para ela. |
| `develop` | Estado antigo: os arquivos do protótipo na raiz, sem `src/`, sem testes, sem `pyproject.toml`. |
| `feature/python-package` | **A branch ativa** — a reorganização em pacote Python. |
| `feature/inicial` | Já mesclada via PR #6. |
| `copilot/upload-de-arquivo` | Fase 1, upload em Express. |
| `copilot/validate-zip-file-content` | Fase 1, o script de validação. |

O padrão é o **GitHub Flow**: cria-se uma branch a partir da `main`, trabalha-se nela, abre-se
um Pull Request, o CI roda, e o merge acontece pela interface do GitHub. O histórico
confirma: os commits `9fc98a4`, `82ecc63` e `98cc614` são merges de PR.

### ⚠️ O que ainda não está na `main`

Dois arquivos existem **apenas** em `feature/python-package`:

| Arquivo | Commit | Consequência de não estar na `main` |
|---|---|---|
| [`.github/workflows/tests.yml`](../.github/workflows/tests.yml) | `0d017ac` | **A `main` não roda testes automaticamente.** |
| [`.vscode/tasks.json`](../.vscode/tasks.json) | `2656b07` | O F5 não funciona para quem clona a `main` — o `launch.json` referencia uma task que não existe. |

Ambos entram na `main` quando esta branch for mesclada. Enquanto isso, quem clonar a
branch padrão tem uma experiência degradada.

---

## Checklist antes de abrir um PR

1. `pytest` passa localmente (25 testes).
2. `git status` não mostra `.venv/`, `__pycache__/` ou `*.egg-info/`.
3. Se mexeu em `prototype/EasyRun.dc.html`, replicou a mudança em
   `prototype/export/EasyRun-src.dc.html`.
4. Se mexeu no `print()` do [`serve.py`](../src/squad_agentica/serve.py), testou o **F5**
   no VS Code — o `problemMatcher` depende do texto exato
   ([09 #4](09-lacunas-e-riscos.md#4-o-problemmatcher-está-acoplado-ao-texto-do-print)).
5. Se alterou algo documentado em `docs/`, atualizou o documento no mesmo commit.
6. Se mexeu **só** em `prototype/` ou em `docs/`, lembre que **nenhum workflow vai rodar** —
   a verificação é sua.

---

[← Arquitetura-alvo](06-arquitetura-alvo.md) · [Índice](README.md) · [Próximo: Glossário →](08-glossario.md)
