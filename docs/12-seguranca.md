# 12 — Segurança

[← MLOps e LLMOps](11-mlops-llmops.md) · [Índice](README.md)

---

Este documento existe porque o EasyRun vai ser levado para dentro de uma rede corporativa.
Ele responde três perguntas, nesta ordem: **o que foi auditado e como**, **o que a auditoria
encontrou**, e **como qualquer pessoa da empresa pode verificar tudo de novo por conta
própria**, sem confiar neste texto.

A auditoria foi feita em **26/07/2026**, sobre a branch `feature/python-package`
(base `3e8c71a`), cobrindo também o histórico completo de todas as branches locais e
remotas. Como o resto desta documentação, os achados vêm de leitura direta do repositório,
não de memória.

---

## Escopo e método

O que foi varrido, e com quê:

| Alvo | Método |
| --- | --- |
| Os 62 arquivos versionados | Leitura de estrutura + grep por padrões de risco (`eval`, `exec`, `subprocess`, `child_process`, `os.system`, `pickle`, decodificação base64, URLs hardcoded) |
| Histórico completo de **todas** as branches | `git log --all -S` por padrões de segredo (chaves AWS `AKIA…`, tokens GitHub `ghp_…`, chaves privadas PEM, `password=`, `api_key`) e `git rev-list --all --objects` por binários |
| Binários versionados | Verificação de magic bytes (`file`) em 100% dos arquivos rastreados |
| O bundle `EasyRun - Standalone.html` (381 KB) | Descompressão dos 19 assets embutidos e comparação byte a byte do único JS contra o `support.js` versionado (sha256 idênticos) |
| Manifests de dependência | `pyproject.toml` deste branch; `package-lock.json` da branch remota `copilot/upload-de-arquivo` (82 pacotes: registry, integrity, install scripts) |
| Workflows do CI | Permissões, secrets, actions de terceiros, gatilhos perigosos (`pull_request_target`), downloads externos |
| Rede em runtime | Grep por `fetch`, `XMLHttpRequest`, `WebSocket`, `sendBeacon`, `serviceWorker`, cookies e storage em todo o `prototype/` |

---

## Resultado: o que está limpo

**Nenhum código malicioso foi encontrado.** As evidências, item a item:

| Vetor | Evidência |
| --- | --- |
| Supply chain Python | [`pyproject.toml`](../pyproject.toml) declara **zero dependências de runtime** — todo `import` do pacote é stdlib. Único extra: `pytest` (dev). |
| Supply chain Node | Não há `package.json` nas branches principais; [`tools/`](../tools/) usa só `node:fs`/`node:path`/`node:url`. Na branch não mergeada `copilot/upload-de-arquivo`, os 82 pacotes do lockfile apontam para `registry.npmjs.org`, todos com `integrity`, nenhum com install script. |
| Segredos | Zero em código, em configs e no **histórico inteiro de todas as branches**. Nenhum `.env`, `.pem` ou chave já foi commitado. |
| Binários | Só dois: um PNG de documentação e um WebP de thumbnail, ambos com magic bytes legítimos. Zero `.exe`/`.dll`/`.whl`/`.zip` em qualquer ponto do histórico (o único "`.zip`" que já existiu tinha 11 bytes de texto `Placeholder`). |
| Payload escondido no bundle | O JS embutido no `Standalone.html` é **byte a byte idêntico** ao [`support.js`](../prototype/support.js) versionado; a lista de recursos externos do bundle está vazia. |
| Execução de comando | Nenhum `subprocess`, `os.system`, `child_process` ou `Invoke-Expression` em lugar algum. Nenhum script `.ps1`/`.sh`/`.bat` no repositório. |
| CI | Só actions oficiais (`actions/*`), `permissions: contents: read` explícito, **nenhum secret**, nenhum `pull_request_target`, nenhum download externo. |
| Rede em runtime | A lógica do mockup não faz **nenhuma** chamada de rede (é simulação com `setTimeout`). O runtime `dc` carrega React/Babel do `unpkg.com` **com SRI sha384 e versões fixas**. Sem service worker, sem cookies, sem storage, sem telemetria. |
| Servidor local | [`serve.py`](../src/squad_agentica/serve.py) faz bind em `localhost` — não expõe nada na rede — e usa o handler da stdlib, que já sanitiza path traversal. |

---

## Pontos de atenção encontrados — e o que foi feito

Nenhum era malicioso; todos eram lacunas de robustez ou de hardening. Estado após esta rodada:

| Achado | Correção aplicada |
| --- | --- |
| [`validate_zip.py`](../validate_zip.py) aprovava caminhos maliciosos de Windows (`C:\…`, `..\..\`, UNC `\\server\…`) porque validava só com `PurePosixPath`; não rejeitava symlinks; não tinha limite nenhum contra zip bomb (o `testzip()` descomprime tudo) | `is_safe_member` agora valida nas duas semânticas (POSIX e Windows) e rejeita `\`, `:`, UNC e nome vazio; membros symlink são rejeitados pelo `external_attr`; limites de 1.000 membros, 100 MiB descomprimidos e razão de compressão 100:1 são checados **antes** de qualquer descompressão |
| `is_safe_member` era código de segurança sem um único teste (registrado em [09 — Cobertura](09-lacunas-e-riscos.md#cobertura-de-testes-o-que-não-é-verificado)) | [`tests/test_validate_zip.py`](../tests/test_validate_zip.py): 21 casos, incluindo traversal POSIX/Windows/UNC, symlink, zip bomb sintético e arquivo corrompido |
| Workflows pinavam actions por tag (`@v4`), que é móvel — quem controla a tag controla o código que roda no runner | As três actions dos workflows existentes (e as duas novas) estão pinadas por **SHA de commit**, com a versão em comentário; o Dependabot mantém os pins atualizados via PR |
| [`.gitignore`](../.gitignore) não cobria `*.pem`, `*.key`, `.env.*` nem `*.log` — um vazamento de credencial por descuido passaria | Padrões adicionados |
| Nenhuma varredura contínua de segredos ou análise estática | Novo workflow [`security.yml`](../.github/workflows/security.yml) — ver abaixo |

---

## Risco aceito (documentado de propósito)

[`tools/check-prototype.mjs:52`](../tools/check-prototype.mjs) faz `eval` da lógica do
protótipo dentro do runner do CI. Isso significa que um PR que altere
`prototype/EasyRun.dc.html` executa código arbitrário no runner do workflow
[`prototype.yml`](../.github/workflows/prototype.yml).

**Por que é aceito:** é exatamente o mesmo nível de confiança de rodar `pytest` sobre o
código de um PR — todo CI que testa código executa código. O blast radius está contido:
o job tem `permissions: contents: read`, não existe nenhum secret no repositório, e o
runner é efêmero. Se um dia o workflow ganhar secrets ou permissões de escrita, este
item precisa ser reavaliado.

---

## Pendências que exigem decisão humana

Duas coisas **não** foram corrigidas porque a decisão não é técnica:

1. **A branch remota `copilot/upload-de-arquivo`** (não mergeada) contém um servidor
   Express de upload com `/upload` e `/files` **sem autenticação, sem rate limit e sem
   validação de tipo**. As dependências do lockfile estão limpas (verificado), mas os
   endpoints não estão prontos para rede alguma. Recomendação: **apagar a branch** se a
   feature foi abandonada; se for entrar, auditar e corrigir antes do merge.
2. **O workflow `validate-zip.yml` continua inerte** — a pasta `uploads/` não existe
   (contexto em [09 — item 5](09-lacunas-e-riscos.md#5-o-workflow-validate-zipyml-não-valida-nada)).
   O script agora está endurecido e testado, mas a decisão "remover ou reativar" segue aberta.

---

## Garantia contínua

O que passa a rodar sozinho a partir desta rodada:

- **[`security.yml`](../.github/workflows/security.yml)** — em cada push/PR para
  `main`/`develop` e toda segunda-feira:
  - **gitleaks** varre o histórico completo atrás de segredos;
  - **CodeQL** (Python + JavaScript/TypeScript) publica análise estática na aba
    **Security → Code scanning** do GitHub. O repositório é público, então é gratuito.
- **[`dependabot.yml`](../.github/dependabot.yml)** — PRs semanais para atualizar os pins
  de SHA das actions e dependências pip.

Observação honesta: o CodeQL vai apontar o `eval`/`new Function` do runtime `dc`
([`support.js`](../prototype/support.js)) — são os achados esperados, já analisados na
auditoria (o caminho de `x-import`, o mais sensível, não é usado por nenhum HTML deste
repositório).

---

## Checklist de verificação independente (para a empresa)

Para validar sem confiar neste documento — na ordem, do mais barato ao mais completo:

1. **Fixe o que vai auditar.** Baixe por SHA de commit, não por branch:
   `git clone https://github.com/adfshownet/EasyRun && git checkout <SHA auditado>`.
   Branch é ponteiro móvel; SHA é imutável.
2. **Confira as dependências em 30 segundos.** [`pyproject.toml`](../pyproject.toml) é a
   lista completa — zero dependências de runtime. Qualquer coisa a mais que um
   `pip install` puxar é sinal de alerta.
3. **Rode um scanner de segredos no histórico:**
   `gitleaks git .` (ou `gitleaks detect --log-opts="--all"` em versões antigas) — deve
   retornar zero achados.
4. **Leia os workflows** — são 4 arquivos curtos em [`.github/workflows/`](../.github/workflows/).
   Confira: `permissions: contents: read`, nenhum secret, actions pinadas por SHA.
5. **Confira o CI no GitHub:** aba **Actions** verde, aba **Security → Code scanning**
   recebendo resultados do CodeQL, aba **Security → Secret scanning** sem alertas.
6. **Rode em sandbox primeiro** se a política exigir: o único servidor do projeto
   (`squad-agentica-serve`) faz bind em `localhost` e serve arquivos estáticos — dá para
   confirmar com `netstat` que nada escuta em interface externa.
7. **Proteja o destino:** branch protection em `main` e `develop` (PR review + status
   checks obrigatórios) e 2FA na conta GitHub — a auditoria vale para o código de hoje;
   a proteção de branch é o que mantém isso verdadeiro amanhã.

---

[← MLOps e LLMOps](11-mlops-llmops.md) · [Índice](README.md)
