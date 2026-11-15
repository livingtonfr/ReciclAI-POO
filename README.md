# Recicl.AI — Projeto de Programação Orientada a Objetos

Universidade Federal de Goiás (UFG) — Instituto de Informática
Disciplina: Programação Orientada a Objetos (POO) — Cursos BIA / BCC

Alunas e alunos: Gabryelle da Silva Parente, Laura Cecilia Cruz Pereira,
Livington Francisco de Sousa Silva, Maria Julia Dias Teixeira, Maryana Miguel Gomes.

Recicl.AI é um ecossistema web que conecta quem descarta resíduos recicláveis
(usuário comum e catador) a cooperativas, empresas compradoras e indústrias,
com identificação e avaliação de material por IA (simulada), formação de
lotes, negociação comercial e emissão de certificado.

## Arquitetura

MVC + DAO, seguindo o padrão apresentado em sala (aulas 29-32): Flask puro,
templates Jinja, HTML/CSS sem frameworks, e persistência em memória através
de um `Repositorio` Singleton (sem banco de dados — os dados voltam ao
estado inicial a cada reinício do servidor, ou pelo botão "Resetar demo").

```
app/
├── model/        # Regras de negócio (classes do UML, migradas do notebook)
├── dao/          # Repositorio (Singleton) + seed de dados de demonstração
├── controller/   # Rotas Flask, uma por área (auth, materiais, lotes, ...)
├── view/         # Templates Jinja (um arquivo .html por tela)
└── static/       # CSS e imagens
tests/
└── cenario.py    # Cenário de integração (reproduz as células 8.1-8.10 do notebook)
```

O notebook original (`ReciclAI_POO_Implementação.ipynb`) contém o
desenvolvimento e a validação do `model/` célula a célula; o `tests/cenario.py`
reproduz esse mesmo roteiro para rodar fora do notebook.

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (no Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python mainFlask.py
```

Acesse `http://127.0.0.1:5000`.

> O servidor roda com `debug=True` (páginas de erro detalhadas e o botão
> "Resetar demo", que só funciona em modo debug) mas com
> `use_reloader=False` — se fosse `True`, o Flask reiniciaria o processo a
> cada arquivo salvo e isso zeraria o `Repositorio` em memória no meio de
> uma demonstração. Se for editar código com o servidor rodando, reinicie-o
> manualmente depois de salvar.

Para rodar o cenário de integração do model (sem subir o servidor):

```bash
python -m tests.cenario
```

## Dados de demonstração (seed)

Todos os usuários de demonstração usam a senha **`123456`**:

| Perfil | Nome | E-mail |
|---|---|---|
| Usuário Comum | Ana | ana@email.com |
| Catador | Carlos | carlos@email.com |
| Cooperativa | Cooperativa Verde | cooperativa@email.com |
| Empresa Compradora | Empresa Recicladora | empresa@email.com |
| Indústria | Indústria Circular | industria@email.com |

Tipos de material cadastrados: PET, Vidro, Papel, Metal.
4 pontos de coleta em Goiânia (Ecoponto Setor Bueno, Cooperativa Verde,
PEV Setor Marista, Ecoponto Campinas).

Para voltar tudo a esse estado inicial a qualquer momento, use o link
**"Resetar demo"** no rodapé de qualquer página (ou `POST /admin/reset`,
que exige login e só funciona com `app.debug` ligado).

## Roteiro de demonstração (≈ 8 min)

1. **Ana (comum)** — login, consulta pontos de coleta que aceitam PET,
   identifica um resíduo por foto (simulada) em "Analisar exemplo".
2. **Carlos (catador)** — login, registra 10 kg de PET declarado LIMPO,
   pede a avaliação da IA (retorna SUJO, sem sobrescrever a condição
   declarada), cria um lote, registra pesagem, disponibiliza e cota o preço.
3. **Empresa e Cooperativa** — logam e propõem compra do lote de Carlos
   no Mercado.
4. **Carlos** — na tela de transações, conclui a proposta da Empresa; a da
   Cooperativa é cancelada automaticamente; emite o certificado (página
   imprimível).
5. **Empresa** — cria um novo lote com o material recebido e o disponibiliza;
   a **Indústria** propõe (em "Mercado") e a Empresa conclui. O material
   fica `DESTINADO` e o histórico de rastreio mostra todos os eventos
   (registro → lote → transferência → lote → transferência → destinação).
6. **Indústria** — em "Materiais recebidos" (mesma tela `/materiais`, sem
   botões de ação), abre o material comprado e mostra esse histórico
   completo — esse é o clímax da demo: provar que o rastreio sobrevive a
   duas vendas.
7. **Erro proposital** — tentar colocar um material de tipo diferente
   (ex.: Vidro) num lote de PET já existente, para mostrar a mensagem de
   erro do model na tela.

## Rotas principais

| Perfil | Rotas |
|---|---|
| Público | `GET /`, `GET/POST /login`, `GET /cadastro`, `GET/POST /cadastro/<perfil>` |
| Todos (logado) | `GET /dashboard`, `GET/POST /perfil`, `GET /pontos`, `GET /logout` |
| Comum | `GET/POST /ia/identificar` |
| Catador, Cooperativa, Empresa, Indústria | `GET /materiais`, `GET /materiais/<id>` (a Indústria só vê o que comprou, sem botões de ação) |
| Catador, Cooperativa, Empresa | `POST /materiais/<id>/disponibilizar`, `/avaliar`, `/cotar`; `GET /lotes`, `POST /lotes/novo`, `GET /lotes/<id>`, `POST /lotes/<id>/adicionar`, `/remover`, `/pesagem`, `/disponibilizar`, `/cancelar`, `/cotar` |
| Catador (apenas) | `GET/POST /materiais/novo` (só o Catador registra material no UML) |
| Comprador (Cooperativa, Empresa, Indústria) | `GET /mercado`, `POST /lotes/<id>/propor`, `GET /minhas-propostas` |
| Vendedor (Catador, Cooperativa, Empresa) | `GET /transacoes`, `POST /transacoes/<id>/concluir`, `/cancelar`, `/certificado` |
| Vendedor ou comprador da transação (logado) | `GET /certificados/<id>` |
| Demo (logado, só com `app.debug` ligado) | `POST /admin/reset` |
| API (JSON) | `GET /api/pontos` (público, aceita `?tipo=<id>`); `GET /api/materiais/<id>/historico` (logado — dono atual, ou vendedor/comprador de uma transação `CONCLUIDA` daquele material) |

**Nota para a arguição:** `GET /logout` é tecnicamente uma ação com efeito
colateral (destrói a sessão) numa rota `GET`, o que não é estritamente
RESTful — aceitável para o escopo da disciplina, mas vale citar se
perguntarem. `POST /admin/reset` já segue o padrão correto.

## Estado do projeto

Fases 0 a 9 do plano concluídas (ambiente, model, DAO/seed, autenticação,
materiais/IA, lotes, mercado/transações/certificado, pontos de coleta,
acabamento), incluindo o opcional de endpoints JSON. O mapa Leaflet segue
como opcional, não implementado.
