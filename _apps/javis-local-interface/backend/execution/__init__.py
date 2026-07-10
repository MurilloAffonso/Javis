"""Executor supervisionado do Javes (R4.1 — fundação).

Este pacote contém APENAS a fundação segura: modelo/máquina de estados
(`execution_task`), gerência de worktree Git isolada (`worktree_manager`) e
política default-deny de comandos (`execution_policy`).

Nesta fase NENHUM agente é executado (Codex/Claude Code entram na R4.2 via
adapters). A flag `JAVIS_ENABLE_SUPERVISED_EXEC` permanece desligada por padrão.
"""
