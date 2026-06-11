# Headroom — Status de Instalação

Data: 2026-06-10

## Problema Encontrado

Python 3.14.4 é incompatível com headroom-ai 0.24.0.

O Headroom usa extensões Rust compiladas via PyO3 v0.22.6.
PyO3 0.22.6 suporta no máximo Python 3.13.

### Erro exato

```
error: the configured Python interpreter version (3.14) is newer than PyO3's maximum supported version (3.13)
= help: please check if an updated version of PyO3 is available. Current version: 0.22.6
= help: set PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 to suppress this check and build anyway using the stable ABI
```

## Opções

### Opção 1 — Workaround com ABI estável (recomendado para teste)

```bash
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install headroom-ai
```

Isso ignora a checagem de versão e compila com ABI estável.
Sem impacto permanente no sistema.
Requer aprovação de Murillo antes de executar.

### Opção 2 — Python 3.12 ou 3.13 ao lado

Instalar Python 3.12 ou 3.13 separado.
Criar virtual environment isolado.
Usar esse venv para headroom.
Mais limpo, mas requer instalação adicional.

### Opção 3 — Aguardar update

headroom-ai 0.24.0 é recente.
PyO3 0.23+ já suporta Python 3.14.
Aguardar nova versão do headroom que use PyO3 atualizado.

## Decisão Pendente

Aguardando aprovação de Murillo para tentar Opção 1.

## Impacto no Projeto

LeanCTX está funcionando normalmente.
Claude Code + LeanCTX é o modo padrão enquanto Headroom não está disponível.
