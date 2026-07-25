# 02 — Ambiente e ferramentas

[← Visão geral](01-visao-geral.md) · [Índice](README.md) · [Próximo: Arquitetura do código →](03-arquitetura-do-codigo.md)

---

Este documento explica cada peça de infraestrutura local do projeto no formato
**o que é → por que existe aqui → o que quebra sem ela**.

## Receita completa (do zero ao mockup rodando)

```bash
git clone https://github.com/adfshownet/EasyRun.git
cd EasyRun
python -m venv .venv                 # cria o ambiente virtual
.venv\Scripts\activate               # Windows (PowerShell/cmd)
# source .venv/Scripts/activate      # Git Bash no Windows
# source .venv/bin/activate          # Linux / macOS
pip install -e ".[dev]"              # instala o projeto + pytest
pytest                               # 25 testes devem passar
squad-agentica-serve                 # abre http://localhost:8080 no navegador
```

O resto deste documento explica o que cada uma dessas linhas realmente faz.

---

## `.venv/` — o ambiente virtual

### O que é

Uma pasta que contém uma **instalação isolada e privada do Python** para este projeto.
Estrutura no Windows:

```
.venv/
├── Scripts/            # (no Linux/Mac chama-se bin/)
│   ├── python.exe      # o interpretador deste ambiente
│   ├── pip.exe
│   ├── pytest.exe
│   ├── squad-agentica-serve.exe   # ← criado pelo pyproject.toml deste projeto
│   └── activate        # script que "liga" o ambiente no terminal
├── Lib/
│   └── site-packages/  # onde TODAS as bibliotecas instaladas vão parar
├── Include/
└── pyvenv.cfg          # o arquivo de configuração do ambiente
```

O `pyvenv.cfg` deste projeto contém:

```ini
home = C:\Program Files\Python312
include-system-site-packages = false
version = 3.12.6
executable = C:\Program Files\Python312\python.exe
command = C:\Program Files\Python312\python.exe -m venv C:\Users\adfsh\workspace\EasyRun\.venv
```

A linha decisiva é `include-system-site-packages = false`: significa **"não enxergue as
bibliotecas instaladas no Python do sistema"**. É o que garante o isolamento. Se fosse
`true`, o ambiente veria as bibliotecas globais e o isolamento seria parcial.

### Por que ela é necessária

Sem ambiente virtual, `pip install` instala **no Python do sistema inteiro**, e todos os
seus projetos compartilham a mesma pasta de bibliotecas. Isso gera três problemas
concretos:

**1. Conflito de versões.** O projeto A precisa de `pytest 7`, o projeto B de `pytest 9`.
Só cabe uma versão instalada. Instalar o B quebra o A silenciosamente — o teste do A
passa a falhar sem que ninguém tenha tocado no A.

**2. Ambiente não reprodutível.** Se as dependências estão espalhadas no Python do
sistema, ninguém sabe de quais o projeto realmente depende. O colega clona, roda, e
funciona *na máquina dele* porque ele instalou aquela biblioteca há seis meses por outro
motivo. Na máquina limpa do CI, quebra.

**3. Poluição irreversível.** Depois de um ano você tem 200 pacotes instalados
globalmente e não faz ideia de quais pode remover. Com `.venv`, desinstalar tudo é
`rm -rf .venv` — e reconstruir é um comando.

Aqui o isolamento tem uma consequência prática visível: o executável
`squad-agentica-serve.exe` **só existe dentro de `.venv/Scripts/`**. Ele não é um programa
do sistema — é criado pela instalação deste projeto neste ambiente.

### Por que ela está no `.gitignore`

Três motivos:

- **É gigante.** Centenas de MB de arquivos binários — inflaria o repositório sem valor.
- **É específica da máquina.** O `pyvenv.cfg` acima tem caminhos absolutos
  (`C:\Users\adfsh\...`) e executáveis compilados para Windows. Não funcionaria no
  Linux do CI.
- **É 100% reconstruível.** Tudo que ela contém pode ser regerado a partir do
  [`pyproject.toml`](../pyproject.toml) com dois comandos. Versionar um artefato
  derivado é redundância que só dá trabalho quando desatualiza.

A regra que faz isso está em [`.gitignore`](../.gitignore):

```gitignore
.venv/
venv/
```

### `activate` vs. chamar o Python direto

Há duas formas de usar o ambiente:

**Ativar** (`.venv\Scripts\activate`) — modifica a variável `PATH` do seu terminal para
que `python`, `pip` e `pytest` passem a apontar para os de dentro do `.venv`. Enquanto
ativo, o prompt normalmente mostra `(.venv)`. Vale só naquela sessão de terminal;
`deactivate` desfaz.

**Chamar pelo caminho completo** (`.venv\Scripts\python.exe -m pytest`) — não mexe em
nada, funciona sempre. É a forma que ferramentas automatizadas usam, justamente por não
depender do estado do terminal. É exatamente o que o
[`.vscode/tasks.json`](../.vscode/tasks.json) faz:

```json
"command": "${workspaceFolder}/.venv/Scripts/python.exe",
"args": ["-m", "squad_agentica.serve", "--no-browser"]
```

⚠️ Esse caminho fixo é Windows-only — ver
[09 — Lacunas](09-lacunas-e-riscos.md#3-o-f5-do-vs-code-só-funciona-no-windows).

### Windows vs. Linux/Mac

| | Windows | Linux / macOS |
|---|---|---|
| Pasta dos executáveis | `.venv\Scripts\` | `.venv/bin/` |
| Ativar | `.venv\Scripts\activate` | `source .venv/bin/activate` |
| Interpretador | `python.exe` | `python` |

No **Git Bash** dentro do Windows a sintaxe é híbrida: `source .venv/Scripts/activate` —
o `source` do shell Unix, mas a pasta `Scripts/` do Windows. É por isso que o
[README](../README.md) traz as duas variantes.

---

## `pyproject.toml` — a identidade do projeto

### O que é

O arquivo-padrão moderno que descreve um projeto Python: nome, versão, dependências, como
construir e quais comandos de terminal ele oferece. Substituiu o antigo `setup.py`
(código executável, imprevisível) por configuração declarativa em formato TOML.

O nosso, [`pyproject.toml`](../pyproject.toml), tem 22 linhas. Vamos por partes.

### `[build-system]`

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

Responde: *"para transformar esta pasta num pacote instalável, qual ferramenta usar?"*

- `requires` — o que o `pip` precisa instalar **antes** de começar a construir. Aqui,
  `setuptools` versão 68 ou superior.
- `build-backend` — a função exata que o `pip` chama para fazer a construção.

Isso é o padrão **PEP 517**. Antes dele, `pip` assumia que todo projeto usava setuptools e
executava `setup.py` — o que amarrava o ecossistema inteiro a uma ferramenta. Hoje você
declara qual quer (setuptools, hatchling, poetry, flit…) e o `pip` obedece.

### `[project]`

```toml
[project]
name = "squad-agentica"
version = "0.1.0"
description = "Squad Agentica em Python"
readme = "README.md"
requires-python = ">=3.10"
```

| Campo | Significado |
|---|---|
| `name` | Nome de **distribuição** — o que você digitaria em `pip install`. Com hífen. |
| `version` | Versão atual. Também exposta em código como `squad_agentica.__version__` e travada pelo teste `test_version`. |
| `description` | Resumo de uma linha, exibido em listagens de pacote. |
| `readme` | Qual arquivo vira a "descrição longa" do pacote. |
| `requires-python` | Versão mínima do interpretador. `>=3.10` porque o código usa sintaxe como `list[str]` e `dict[str, X]` sem importar do módulo `typing`. |

⚠️ `name = "squad-agentica"` mas o pacote importável é `squad_agentica` (underscore) —
ver [01 — Como o nome se organiza](01-visao-geral.md#como-o-nome-se-organiza).

### `[project.optional-dependencies]`

```toml
[project.optional-dependencies]
dev = ["pytest>=8"]
```

Define um **extra** chamado `dev`. Extras são grupos de dependências que só são instaladas
se você pedir explicitamente, com a sintaxe de colchetes: `pip install ".[dev]"`.

Por que `pytest` é opcional e não obrigatório? Porque quem só quer **usar** o projeto não
precisa rodar os testes dele. Deixar `pytest` como dependência normal forçaria todo
usuário a baixar um framework de testes que nunca vai usar. Quem **desenvolve** pede o
extra.

Note também que este projeto **não tem nenhuma dependência obrigatória** — não existe a
chave `dependencies` no `[project]`. `squad_agentica` roda usando apenas a biblioteca
padrão do Python. Isso é deliberado: `graph.py` explicitamente *não* importa `langgraph`
(ver [03](03-arquitetura-do-codigo.md#graphpy)).

### `[project.scripts]`

```toml
[project.scripts]
squad-agentica-serve = "squad_agentica.serve:main"
```

Isto é um **console script** (ou *entry point*), e é o mecanismo que transforma uma função
Python num comando de terminal.

Lê-se: *"crie um comando chamado `squad-agentica-serve` que, quando executado, importa o
módulo `squad_agentica.serve` e chama a função `main()` dele."* A sintaxe é
`módulo:função`.

Na prática, durante o `pip install`, o setuptools gera um pequeno executável em
`.venv/Scripts/squad-agentica-serve.exe` cujo conteúdo é essencialmente:

```python
from squad_agentica.serve import main
sys.exit(main())
```

É por isso que, depois de instalar, você digita `squad-agentica-serve` e funciona — sem
precisar lembrar o caminho do arquivo `.py`. Sem esse bloco, o único jeito de rodar seria
`python -m squad_agentica.serve` ou `python src/squad_agentica/serve.py`.

### `[tool.setuptools.packages.find]`

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

Diz ao setuptools: *"procure os pacotes Python dentro da pasta `src/`, não na raiz."*
Sem isso, o setuptools varreria a raiz e poderia empacotar `tests/` ou não achar nada.

A razão de o código morar em `src/` está em
[03 — Por que src-layout](03-arquitetura-do-codigo.md#por-que-src-layout).

Qualquer seção começando com `[tool.X]` é, por convenção, configuração da ferramenta `X`.
Poderia haver `[tool.pytest.ini_options]`, `[tool.ruff]`, `[tool.mypy]` — este projeto só
tem a do setuptools (ver
[09 — Lacunas #8](09-lacunas-e-riscos.md#8-pytest-sem-instalação-falha-com-importerror)).

---

## `pip install -e ".[dev]"` — dissecando o comando

Três partes, cada uma com um efeito distinto:

### O `.`

"Instale o projeto que está no diretório atual." O `pip` procura o `pyproject.toml`, lê a
seção `[build-system]`, chama o setuptools e instala o resultado.

### O `[dev]`

"…e também as dependências do extra `dev`." Sem isso, `pytest` não seria instalado e o
comando `pytest` não existiria no ambiente. As aspas em `".[dev]"` são necessárias porque
alguns shells (zsh, PowerShell) interpretam colchetes como caracteres especiais.

### O `-e` — *editable install*

Esta é a parte que mais confunde, e a mais importante no dia a dia.

**Instalação normal** (`pip install .`): o `pip` **copia** os arquivos `.py` para dentro de
`.venv/Lib/site-packages/squad_agentica/`. A partir daí, `import squad_agentica` lê a
cópia. Se você editar `src/squad_agentica/serve.py`, **nada muda** — a cópia continua a
antiga. Você teria que reinstalar a cada alteração.

**Instalação editável** (`pip install -e .`): o `pip` não copia nada. Ele grava em
`site-packages` um arquivo-ponteiro dizendo *"o pacote `squad_agentica` está em
`C:\Users\adfsh\workspace\EasyRun\src`"*. A partir daí, `import squad_agentica` lê
**direto do seu código-fonte**. Você edita e a próxima execução já usa a versão nova.

Regra prática: **desenvolvendo, sempre `-e`**; instalando para usar, sem `-e`.

Um efeito colateral do `-e` importa aqui: o `serve.py` calcula o caminho da pasta
`prototype/` subindo diretórios a partir do próprio arquivo. Isso só funciona porque o
código está no checkout do repositório — ou seja, **porque a instalação é editável**. Ver
[09 — Lacunas #2](09-lacunas-e-riscos.md#2-servepy-depende-de-estar-num-checkout-do-repositório).

---

## `src/squad_agentica.egg-info/` — metadados gerados

### O que é

Uma pasta criada automaticamente pelo setuptools durante o `pip install`. Contém a ficha
de identidade do pacote, extraída do `pyproject.toml` e traduzida para um formato que as
ferramentas de empacotamento consomem.

| Arquivo | Conteúdo | Origem |
|---|---|---|
| `PKG-INFO` | Nome, versão, Python mínimo, extras e o README inteiro embutido | `[project]` |
| `entry_points.txt` | `[console_scripts]` → `squad-agentica-serve = squad_agentica.serve:main` | `[project.scripts]` |
| `requires.txt` | `[dev]` → `pytest>=8` | `[project.optional-dependencies]` |
| `top_level.txt` | `squad_agentica` — o nome importável de nível superior | descoberto em `src/` |
| `SOURCES.txt` | A lista de todos os arquivos incluídos no pacote | varredura |
| `dependency_links.txt` | Vazio (mecanismo legado, obsoleto) | — |

O nome "egg" é herança histórica: *egg* era o formato de distribuição do Python antes do
formato *wheel* atual. O sufixo ficou.

### Por que está no `.gitignore`

Pelo mesmo princípio do `.venv`: é **artefato derivado**. Todo o conteúdo dela é gerado a
partir do `pyproject.toml`. Versionar significaria manter duas fontes da mesma informação
e, inevitavelmente, vê-las divergir. A regra é:

```gitignore
*.egg-info/
```

Se você apagar a pasta, ela reaparece no próximo `pip install`.

---

## `__pycache__/` e `.pytest_cache/` — caches

### `__pycache__/`

Python compila cada `.py` para **bytecode** (uma forma intermediária, mais rápida de
carregar) e guarda o resultado em `__pycache__/nome.cpython-312.pyc`. Na próxima execução,
se o `.py` não mudou, ele pula a compilação.

É puramente uma otimização de tempo de carga. Apagar não quebra nada — só torna a
próxima execução alguns milissegundos mais lenta. O `312` no nome é a versão do
interpretador: caches de versões diferentes convivem sem conflito.

### `.pytest_cache/`

O `pytest` guarda aqui o resultado da última execução. O que isso habilita:

- `pytest --last-failed` — roda só os testes que falharam da última vez;
- `pytest --failed-first` — roda os que falharam primeiro, para feedback mais rápido.

O arquivo `.pytest_cache/v/cache/nodeids` contém a lista dos identificadores dos testes
coletados — hoje, 10 entradas.

Ambas as pastas são ignoradas:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
```

O padrão `*.py[cod]` usa uma classe de caracteres: pega `.pyc`, `.pyo` e `.pyd` de uma vez.

---

## `.gitignore` — bloco a bloco

O [`.gitignore`](../.gitignore) lista padrões de arquivos que o Git deve fingir que não
existem: não aparecem no `git status`, não entram em commits acidentais.

```gitignore
# Python
__pycache__/          # bytecode compilado
*.py[cod]             # .pyc, .pyo, .pyd soltos
*.egg-info/           # metadados de build
.eggs/                # cache de dependências de build (legado)
build/                # saída intermediária de empacotamento
dist/                 # os .whl e .tar.gz finais
.venv/                # o ambiente virtual
venv/                 # idem, nome alternativo
.pytest_cache/        # cache do pytest
.mypy_cache/          # cache do type-checker mypy
.ruff_cache/          # cache do linter ruff
```

Note que `.mypy_cache/` e `.ruff_cache/` estão listados **preventivamente** — nenhuma
dessas ferramentas está configurada no projeto hoje. É comum e inofensivo.

```gitignore
# Node
node_modules/         # dependências JavaScript
uploads/*             # arquivos enviados por usuários
!uploads/.gitkeep     # ...exceto este marcador
```

⚠️ **Essas três linhas são herança morta.** O repositório teve um protótipo Express
(Node.js) com upload de arquivos, removido no commit `1fe0348`. Não há mais `package.json`
nem pasta `uploads/`. Ver
[09 — Lacunas #5](09-lacunas-e-riscos.md#5-o-workflow-validate-zipyml-não-valida-nada).

```gitignore
# Environment
.env                  # variáveis de ambiente com segredos
```

Convenção universal: `.env` guarda chaves de API, senhas e afins. **Nunca** deve ir para
o Git. Este projeto ainda não usa nenhuma, mas a proteção já está no lugar.

```gitignore
# OS
.DS_Store             # metadados de pasta do macOS
Thumbs.db             # cache de miniaturas do Windows
```

Lixo que o sistema operacional cria sozinho dentro das pastas.

```gitignore
# Editor
.vscode/*
!.vscode/launch.json
!.vscode/tasks.json
```

Aqui há um padrão que vale entender: **ignorar tudo e depois abrir exceções**.

- `.vscode/*` — ignore todo o conteúdo da pasta.
- `!arquivo` — o `!` **nega** a regra anterior: "exceto este".

Por quê? A pasta `.vscode/` mistura duas naturezas de arquivo. Coisas como
`settings.json` costumam conter preferências pessoais (tema, tamanho de fonte, caminhos
locais) que não devem ser impostas ao time. Já `launch.json` e `tasks.json` **são
infraestrutura compartilhada** — é o que faz o F5 funcionar igual para todo mundo. Então
o projeto ignora a pasta inteira e versiona só esses dois deliberadamente.

Uma pegadinha do Git vale registrar: se você ignorar um diretório inteiro
(`.vscode/` com barra, em vez de `.vscode/*` com asterisco), o Git nem entra nele, e as
negações com `!` **não funcionam**. Por isso a regra aqui usa `/*`.

---

## O que roda onde: mapa rápido

| Comando | Onde precisa estar | O que exige |
|---|---|---|
| `python -m venv .venv` | raiz do repo | Python 3.10+ instalado no sistema |
| `pip install -e ".[dev]"` | raiz do repo, `.venv` ativo | conexão de rede (baixa o pytest) |
| `pytest` | raiz do repo, `.venv` ativo | o `pip install -e` já ter sido feito |
| `squad-agentica-serve` | qualquer lugar, `.venv` ativo | instalação editável + pasta `prototype/` |
| `python -m squad_agentica.serve` | qualquer lugar, `.venv` ativo | o mesmo, sem depender do console script |
| `python validate_zip.py` | raiz do repo | nada (só biblioteca padrão) |

---

[← Visão geral](01-visao-geral.md) · [Índice](README.md) · [Próximo: Arquitetura do código →](03-arquitetura-do-codigo.md)
