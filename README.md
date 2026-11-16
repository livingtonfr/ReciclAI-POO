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

A aplicação utiliza MVC com uma camada de serviços e DAOs:
Flask para as rotas, templates Jinja para as páginas e classes
Python para as entidades e regras do domínio.

Os controladores recebem as requisições e chamam os serviços.
Os serviços coordenam operações e permissões, utilizando os
DAOs para acessar os dados e o modelo para executar as regras
do domínio.

O armazenamento permanece em memória, por meio do Repositorio
Singleton. Os dados retornam ao estado inicial ao reiniciar
o servidor ou executar o reset da demonstração.

| Local | Responsabilidade |
|---|---|
| app/model/ | Entidades, enumerações e regras do domínio |
| app/controller/ | Rotas Flask e respostas HTML ou JSON |
| app/services/ | Coordenação das operações e permissões |
| app/dao/ | DAOs, repositório em memória e dados de demonstração |
| app/view/ | Templates Jinja |
| app/static/ | CSS e imagens |
| app/config.py | Configurações da aplicação |
| app/database/ | Estrutura reservada para a futura persistência SQLite |
| app/patterns/ | Estrutura reservada para a integração dos padrões escolhidos |
| tests/ | Testes automatizados e cenário de integração |
| docs/ | Documentação técnica |
| mainFlask.py | Inicialização do servidor |

As pastas app/database e app/patterns ainda não possuem
implementações próprias nesta etapa. A camada app/services
já está implementada e integrada aos controladores.

O cenário tests/cenario.py reproduz o roteiro de validação
do modelo desenvolvido no notebook original.

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

O acompanhamento atual utiliza as fases registradas em
STATUS_PROJETO.md:

1. Fase 1 — Verificação da aplicação e configuração do ambiente: concluída.
2. Fase 2 — Organização das pastas e configurações: concluída.
3. Fase 3 — Validações e regras do domínio: concluída.
4. Fase 4 — Separação entre controladores, serviços e DAOs: concluída.
5. Fase 5 — Persistência SQLite: ainda não iniciada.

A antiga referência às fases 0 a 9 correspondia ao roteiro
inicial de construção e foi substituída pelo acompanhamento
atual.

Após a fase 4, foi corrigida a invalidação da pesagem quando
materiais são adicionados ou removidos de um lote. Operações
recusadas preservam a pesagem anterior.

O armazenamento continua em memória. Identificação, avaliação
e precificação por IA permanecem simuladas.

## Testes

Execute os comandos na raiz do projeto, utilizando o Python
do ambiente virtual:

```powershell
python -m unittest discover -s tests -v
python -m tests.cenario
```

Após a correção da pesagem, a suíte possui 92 testes.

O cenário de integração termina com duas transações concluídas,
seis eventos de rastreabilidade e material destinado à indústria.

## Certificados e PDF

O certificado é apresentado em uma página HTML imprimível.
O botão da página utiliza window.print() para abrir a janela
de impressão do navegador, onde o usuário pode imprimir ou
selecionar a opção de salvar em PDF.

Não há geração de arquivo PDF no servidor.

O método Certificado.gerarPDF() mantém uma simulação textual
no terminal. Ele não cria arquivos e não é o mecanismo
utilizado pelo botão da página.
