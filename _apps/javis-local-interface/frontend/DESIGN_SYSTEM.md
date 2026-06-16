# JAVIS — Design System (Orion)

> Baseado no vídeo "PARE de Criar SaaS" (Alan Nicolas): a ordem é **Brandbook → Design System → resto**.
> O design system é a base que faz workflows, ofertas e páginas ficarem fáceis. Este doc é a fonte da verdade do visual do Javis.

## 1. Marca

- **Nome:** JAVIS (sub: AIOS — Agent Intelligence OS)
- **Conceito:** "Agora o controle é seu." Você comanda um sistema operacional de agentes de IA.
- **Personalidade:** tecnológico, vivo, cinematográfico, confiável. Menos "dashboard corporativo", mais "centro de comando".
- **Inspiração visual:** AIOS (violet/navy glassmorphism) + toque Matrix-terminal (verde/mono em áreas de "sistema/código") + profundidade tipo HUD de nave.

## 2. Tokens de cor (canônicos)

```
/* Base */
--bg:        #0a0a1a   /* deep navy — fundo app */
--surface:   #0d0d1a   /* painéis */
--surface2:  #131325   /* cards */
--border:    #18182e
--border2:   #22223a

/* Accent primário (AIOS) */
--violet:     #7c3aed
--violet-dim: rgba(124,58,237,0.15)
--violet-glow: rgba(124,58,237,0.45)

/* Accent secundário */
--cyan:      #00e5ff   /* dados/voz */
--emerald:   #10b981   /* online/sucesso */
--matrix:    #00ff9c   /* terminal/código/"sistema" — NOVO, usar com parcimônia */

/* Semânticos */
--progress:  #3b82f6
--warn:      #f59e0b
--danger:    #ef4444

/* Texto */
--text:      #e2e8f0
--text-mid:  #8892a4
--text-dim:  #5a6478
```

## 3. Tipografia

- **UI:** Inter / 'Segoe UI', system-ui (já usado).
- **Mono (sistema/código/métricas):** 'JetBrains Mono', 'SF Mono', Consolas.
- Escala: 28/20/16/14/13/12/11/10. Títulos de view = 20 bold. Labels = 11 uppercase letter-spacing .08em.

## 4. Elevação & profundidade

- **Glassmorphism:** `background: rgba(19,19,37,0.6); backdrop-filter: blur(12px);` em painéis flutuantes.
- **Sombra padrão:** `0 8px 24px rgba(0,0,0,0.3)`.
- **Glow de foco:** borda violet + `box-shadow: 0 0 0 1px var(--violet), 0 0 20px var(--violet-glow)`.
- **Grid de fundo sutil** (linhas violet 6% opacidade, mask radial) em áreas "canvas".

## 5. Raio & espaçamento

- Raio: cards 12-14px, botões 8px, chips 20px (pill).
- Espaçamento base 4px (4/8/12/16/20/24).

## 6. Componentes (estados obrigatórios)

| Componente | Estados |
|-----------|---------|
| Botão primário | normal / hover (glow) / active / disabled |
| Card (agente/projeto/integração) | normal / hover (borda violet + lift -2px) / selecionado / conectado |
| Status dot | online (emerald pulse) / working (violet pulse) / idle (amber) / offline (cinza) |
| Sidebar item | normal / hover / active (barra violet + fundo violet-dim) |
| Progress bar | trilha surface + fill gradient violet→progress |
| Chip/badge | default / accent / mono(sistema) |

## 7. Movimento

- Transições 0.15-0.2s ease para hover; 1.6s cubic-bezier para movimento de "boneco" na Sala.
- Pulsos (status, glow) 1-1.5s infinite.
- Respeitar `prefers-reduced-motion`.

## 8. Princípios

1. **Vivo, não estático** — algo sempre pulsa/respira (orbe, dots, log).
2. **Hierarquia por glow**, não por peso de borda dura.
3. **Mono = sistema** — métricas, IDs, logs e código sempre em mono + tom matrix/cyan.
4. **Consistência de view** — toda view: header (título + subtítulo) → conteúdo → painel lateral opcional.
5. **Nunca quebrar IDs/classes existentes** (orb-canvas, chat-log, sb-item, view, etc.) — o JS depende deles.
