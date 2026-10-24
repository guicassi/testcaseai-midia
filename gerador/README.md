# Gerador de Reels testcaseAI — 7 estilos

Vídeos 1080x1920, 30 fps, com trilha e efeitos sonoros sintetizados (sem direitos autorais).
Requisitos: Python 3 com `playwright`, `numpy`, `scipy` e `ffmpeg` (Chromium em /opt/pw-browsers).

## Como renderizar

| Estilo | Arquivo HTML | Script |
|---|---|---|
| 1. `classico` (fundo escuro/violeta com brilho) | `classico.html` | `python3 render_classico.py classico.html roteiro.json saida.mp4` |
| 2–7. `editorial`, `terminal`, `chat`, `quadro`, `trailer`, `pop` | `estudio.html` | `python3 render_estudio.py estudio.html roteiro.json saida.mp4` |

Prévia rápida (quadros JPG antes de renderizar, ~20 s):
`python3 previa.py <html> roteiro.json prefixo 1.5 4 8 12` → gera `prefixo_0.jpg`, `prefixo_1.jpg`…
SEMPRE olhe os quadros antes do render final: corrija texto cortado ou sobreposto encurtando o roteiro.

Renderizar leva ~2–3 min por vídeo. Duração ideal: 14–22 s. Primeira cena = gancho forte.

## Rodízio

`rodizio.json` guarda a ordem dos estilos e o último usado. Para cada Reel novo: pegue o próximo da lista
(circular), produza, e atualize `ultimo` no arquivo (commit junto com o vídeo). Nunca repita o mesmo estilo
nos dois Reels da mesma semana.

## Campos por estilo

### 1. classico — `{"theme": "dark" | "violet", "scenes": [...]}`
- `hook` {lines:[1–2 linhas], accent, sub}
- `card` {variant:"bad"|"good", eyebrow, tag, text, highlight:[trechos do texto]}
- `chips` {eyebrow, items:[2–3 perguntas], punch}
- `checks` {eyebrow, tag, items:[2–3 itens; aceita <b>]}
- `code` {eyebrow, filename, lines:[["Cenário:","..."],["Dado","..."],["Quando","..."],["Então","..."]]}
- `number` {eyebrow, value, suffix, label, sub} — só número real (preço de plano, contagem de exemplo)
- `quote` {lines:[...], accent:[linhas em destaque], sign}
- `quiz` {eyebrow, question, options:[3 opções curtas], answer: índice 0–2, explain} — contagem 3-2-1
- `pov` {label:"POV", lines:[2–3 linhas], emoji}
- `flow` {eyebrow, steps:[{tag, text}], bad: índice da etapa que quebra, punch}
- `shot` {eyebrow, title, image:"caminho/print.png", zoom:{x,y,w,h} (frações 0–1), click:{x,y}, highlight:{x,y,w,h}, caption} — tour com print real
- `cta` {lines:[2 linhas], accent, sub, button:"testcaseai.com.br →"}

### 2. editorial — `{"style":"editorial"}` (creme, tipografia gigante, cortes secos, bateria)
- `manchete` {kicker, lines:[2–3 linhas curtas], color:"#FFD23F"|"#E8452C", sub}
- `versus` {aLabel, a, bLabel, b, color}
- `lista` {kicker, title, items:[3 itens curtos], lastColor}
- `carimbo` {title, stamp:"Reprovado"|"Aprovado", color, sub}
- `fim` {lines:[2 linhas], url, sub}

### 3. terminal — `{"style":"terminal"}` (fósforo verde, chiptune)
- `log` {title, lines:[{t, k:"cmd"|"ok"|"fail"|"warn"|"info", p: pausa opcional}], hold}
  - comandos fictícios em português (nunca nomes de ferramentas reais); linhas ≤ 34 caracteres
- `barra` {label, result, detail, fail:false}
- `fim` {lines:[2–3 linhas curtas], url, sub}

### 4. chat — `{"style":"chat"}` (conversa do squad, lo-fi)
- `chat` {title, members:{"PO":"#F79009","Dev":"#7A5AF8","QA":"#12B76A"}, me:"QA", messages:[{from, text, pause?} | {sys:true, text}], hold}
  - 6–9 mensagens curtas; emojis ok
- `fim` {lines:[2 linhas], sub, url}

### 5. quadro — `{"style":"quadro"}` (quadro branco desenhado, violão)
- `rabisco` {lines:[2 linhas], sub}
- `passos` {title, steps:[3 passos curtos ≤ 26 caracteres]}
- `risca` {bad, good, badLabel?, goodLabel?, sub}
- `checklist` {title, items:[3–4 itens curtos]}
- `fim` {lines:[2 linhas], url}

### 6. trailer — `{"style":"trailer"}` (cinema, drone e impactos)
- `card` {lines:[1–3 linhas curtas], dur: 2.2–3.0, hit: true para impacto}
- `flash` {words:[3 palavras curtas em maiúsculas]}
- `titulo` {title (≤ 8 caracteres), sub}
- `fim` {lines:[2 linhas], sub, url}

### 7. pop — `{"style":"pop"}` (cores chapadas, formas quicando, marimba)
- `grito` {lines:[2–3 linhas], bg, fg, seed}
- `sticker` {num, kicker, text (≤ 50 caracteres), bg, dot, seed}
- `fim` {lines:[2 linhas], sub, url, bg, seed}
- cores: #FF5CA8 rosa, #C6F432 lima, #3D5AFE azul, #FFB800 amarelo, #00C2A8 verde-água, #111111 preto

Veja `exemplos/` para um roteiro completo de cada estilo.
