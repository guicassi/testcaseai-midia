# Pauta da série "Bugs que custaram caro"

Marque como `[usado]` ao produzir o roteiro. Sempre confira os fatos de novo na web antes de escrever.

- [usado] Ep. 1: Knight Capital, 2012.
- [usado] Ep. 2: a tela azul global de 19/07/2024.
- [usado] Ep. 3: o dia em que WhatsApp, Instagram e Facebook sumiram (04/10/2021).
- [ ] **GitLab, 31/01/2017 – "5 backups, nenhum funcionou".** Um sysadmin cansado apagou por engano a pasta do banco de produção (~300 GB) no servidor errado, tarde da noite. Dos 5 métodos de backup e replicação, nenhum funcionava. Restauraram um snapshot de 6 horas antes, feito por acaso para testes; perderam cerca de 6 horas de dados. A empresa transmitiu a recuperação ao vivo e publicou um postmortem detalhado. Lição: backup que nunca foi restaurado não é backup. Formato sugerido: terminal ao vivo com os 5 backups sendo testados e todos dando "FALHOU".
- [ ] **NASA Mars Climate Orbiter, 1999 – "Metros ou pés?".** Sonda de US$ 125 milhões perdida em 23/09/1999 porque um software entregava dados de impulso em libras-força enquanto outro esperava newtons. Lição: teste de integração entre equipes. Formato sugerido: trajetória da sonda no espaço, os dois números lado a lado.
- [ ] Ideias para pesquisar e confirmar antes: Ariane 5 (1996, conversão numérica), bug do ano 2000 (Y2K, o que foi evitado graças a teste), outage da AWS S3 em 2017 (comando digitado errado), Therac-25 (tratar com cuidado: houve mortes; tom sóbrio, sem sensacionalismo).
