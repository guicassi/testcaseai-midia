# Série "Bugs que custaram caro"

Reels narrados (45–60 s) sobre incidentes reais e públicos de software, sempre terminando com o cartão do testcaseAI. Publicados às **terças de manhã** (Reel do dia). É um formato em teste, com exceções aprovadas pelo usuário: duração acima de 22 s e citação dos nomes das empresas envolvidas nos incidentes.

| Ep. | História | Data | Pasta | Vídeo final |
|---|---|---|---|---|
| 1 | Knight Capital, 2012 (deploy esquecido em 1 de 8 servidores) | 12/11/2026 (QUI, antecipado) | `ep1-knight/` | `reels/2026-11-17-bugs-que-custaram-caro-ep1-knight.mp4` |
| 2 | O dia da tela azul, 19/07/2024 (atualização com 21 entradas x 20) | 17/11/2026 | `ep2-tela-azul/` | `reels/2026-11-24-bugs-que-custaram-caro-ep2-tela-azul.mp4` |
| 3 | O dia em que o WhatsApp sumiu, 04/10/2021 (comando de manutenção + bug na auditoria) | 24/11/2026 | `ep3-whatsapp/` | `reels/2026-12-01-bugs-que-custaram-caro-ep3-whatsapp.mp4` |

(Os nomes dos arquivos dos Ep. 1–3 mantêm as datas originais; o que vale é a data no título do design no Canva.)

## Fluxo semanal (semi-automático, porque a voz é gerada pelo usuário)

1. **Domingo – rotina de produção:** escolhe a próxima história (veja `pauta.md`), confere os fatos na web, escreve `roteiros/epN-<tema>.md` (narração + plano de cenas) e manda a narração no resumo para o usuário. Também cria um Reel RESERVA para a terça, em "1 - Para aprovar".
2. **Usuário:** gera a narração no ElevenLabs (modelo multilíngue, voz séria, MP3), mantendo as linhas em branco entre parágrafos, e manda o MP3 no chat de produção.
3. **Chat de produção – montagem** (passo a passo abaixo). O episódio vai para "2 - Aprovados" com a data da terça. A reserva fica em "1 - Para aprovar" e não é publicada. Se o episódio não ficar pronto, o usuário aprova a reserva.

## Montagem de um episódio

1. Salve o MP3 em `serie/audio/epN-narracao.mp3`. Detecte as pausas:
   `ffmpeg -i serie/audio/epN-narracao.mp3 -af silencedetect=noise=-35dB:d=0.18 -f null - 2>&1 | grep -oE "silence_(start|end): [0-9.]+" | paste - -`
   Cada intervalo entre pausas é uma frase. Mapeie frase por frase com o roteiro.
2. Copie o episódio mais parecido (`ep2-tela-azul/index.html` é o mais completo: cenas, legendas, mapa de pontos e cartão final) para `serie/epN-<tema>/index.html`. Edite:
   - `S` (início e fim de cada cena, cortando no meio das pausas);
   - `SUBS` (legenda de cada frase com o tempo);
   - os cues de animação (cada elemento entra no instante em que a palavra é dita);
   - o subtítulo do cabeçalho (`EP. N · ...`).
   O `#root` precisa de `position:absolute; inset:0` (sem isso os fundos das camadas somem).
3. Prévia: `python3 serie/quadros.py serie/epN-<tema>/index.html /tmp/q <tempos...>`. Olhe os quadros mais cheios e corrija cortes e sobreposições.
4. Render: `python3 serie/render.py serie/epN-<tema>/index.html /tmp/epN`. Para refazer só uma cena, passe os índices no fim (ex.: `... /tmp/epN 7`).
5. Áudio: `ffmpeg -i /tmp/epN/video_mudo.mp4 -i serie/audio/epN-narracao.mp3 -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -af apad -t <duração> reels/AAAA-MM-DD-bugs-que-custaram-caro-epN-<tema>.mp4`. Confira 3 quadros com ffmpeg.
6. Commit e push. No Canva: upload-asset-from-url com a URL raw, copy-design de DAHYSlYnC8M (página 1), apague todos os elementos e faça insert_fill do vídeo (0, 0, 1080, 1920). Título: `AAAA-MM-DD TER | IG+FB | REEL | Bugs que custaram caro – Ep. N: <Tema> (série)`. Adicione o comentário "LEGENDA INSTAGRAM E FACEBOOK:" (gancho, resumo em 2–3 frases, "Ep. N da série Bugs que custaram caro. Toda terça tem episódio novo.", chamada para salvar ou comentar, 5–6 hashtags incluindo #BugsQueCustaramCaro). Mova para "2 - Aprovados".

## Regras de conteúdo da série

- Só incidentes reais, públicos e bem documentados. Confira datas, números e causa em fontes primárias (postmortem da empresa, órgão oficial) ou em imprensa séria. Nada de número inventado.
- Narrar o que a fonte diz. Quando o detalhe técnico não foi publicado (ex.: o comando exato), marcar na tela como "ilustrativo".
- Nunca culpar pessoas: a mensagem é sempre "faltou processo / faltou teste".
- Ícones de apps e empresas: genéricos (letra + cor), nunca logotipos oficiais.
- Fechamento: "Pra sua squad [...]: conheça o testcaseAI. Do requisito ao release, sem lacunas de qualidade." + cartão com 3 funcionalidades (sem nomes de ferramentas) + testcaseai.com.br.
