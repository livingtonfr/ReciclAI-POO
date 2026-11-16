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

O fluxo principal é gravado em SQLite, sem ORM, e os dados permanecem
após reiniciar o servidor. Cada contrato de acesso a dados tem duas
implementações com a mesma interface: uma em memória e uma em SQLite.
Os serviços funcionam com as duas, e por isso os testes escritos antes
da persistência continuam válidos. Pontos de coleta, identificação,
avaliação e precificação continuam em memória, por meio do Repositorio
Singleton, como dados fixos de demonstração e simulações.

O banco fica em `instance/reciclai.sqlite3`, pasta ignorada pelo Git.
O caminho pode ser alterado pela variável de ambiente `RECICLAI_DB`.

| Local | Responsabilidade |
|---|---|
| app/model/ | Entidades, enumerações e regras do domínio |
| app/controller/ | Rotas Flask e respostas HTML ou JSON |
| app/services/ | Coordenação das operações e permissões |
| app/dao/ | DAOs em memória e em SQLite, e o repositório em memória |
| app/view/ | Templates Jinja |
| app/static/ | CSS e imagens |
| app/config.py | Configurações da aplicação |
| app/database/ | Esquemas SQL, conexão, integração com o Flask e carga inicial |
| app/patterns/ | Estrutura reservada para a integração dos padrões escolhidos |
| tests/ | Testes automatizados e cenário de integração |
| docs/ | Documentação técnica |
| mainFlask.py | Inicialização do servidor |

A pasta app/patterns ainda não possui implementação própria.
A camada app/services está integrada aos controladores, e a pasta
app/database está integrada ao fluxo principal.

Para entender o código, a leitura por camadas ajuda mais do que a ordem
dos arquivos: model, services, dao, database e controller. O detalhamento
está em docs/ARQUITETURA.md.

O cenário tests/cenario.py reproduz o roteiro de validação
do modelo desenvolvido no notebook original.

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (no Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python mainFlask.py
```

Acesse `http://127.0.0.1:5000`. Ao iniciar, o servidor informa no
terminal o caminho do banco SQLite em uso.

Requisito: Python 3.12 ou superior, pois o código usa o parâmetro
`autocommit` do módulo `sqlite3`.

> O servidor roda com `debug=True` (páginas de erro detalhadas), mas com
> `use_reloader=False`, para não reiniciar o processo a cada arquivo
> salvo. Se for editar código com o servidor rodando, reinicie-o
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
PEV Setor Marista, Ecoponto Campinas), mantidos em memória.

Usuários e tipos são gravados no banco na primeira execução. A carga
inicial é repetível: não duplica registros, não apaga dados e não
reaplica a senha de uma conta existente.

### Como ver ou zerar os dados

O arquivo `instance/reciclai.sqlite3` pode ser aberto no VS Code com a
extensão SQLite Viewer. Para começar do zero, pare o servidor e apague
esse arquivo; ele será recriado com a carga inicial na próxima execução.

O reset pela interface (`POST /admin/reset`) apaga todos os dados do
banco. Por isso ele vem desabilitado e o botão "Resetar demo" só aparece
quando o servidor é iniciado com `RECICLAI_PERMITIR_RESET=1` e em modo
debug. As tabelas usam `IF NOT EXISTS` e não há migração: se existir um
banco de uma versão anterior, apague-o antes de iniciar.

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
| Demo (logado, `RECICLAI_PERMITIR_RESET=1` e `app.debug` ligado) | `POST /admin/reset` |
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
5. Fase 5 — Persistência SQLite: concluída para o fluxo principal.

A fase 5 foi feita em etapas: esquemas e DAOs de usuários, tipos,
materiais e lotes; reconstrução dos objetos do modelo a partir do banco;
propostas, conclusão atômica e certificados (5F); integração com o Flask
e carga de demonstração (5H); e validação final (5I).

Continuam em memória ou simulados: pontos de coleta, identificação,
avaliação e precificação por IA, e as cotações, que não são gravadas.
A persistência dessas duas últimas partes (blocos 5G.1 e 5G.2) está
pendente. O certificado é um recurso acadêmico de rastreabilidade, sem
validade jurídica.

A versão anterior, totalmente em memória, foi preservada na branch
`apresentacao-memoria-validada`.

## Certificados e PDF

O certificado é apresentado em uma página HTML imprimível.
O botão da página utiliza window.print() para abrir a janela
de impressão do navegador, onde o usuário pode imprimir ou
selecionar a opção de salvar em PDF.

Não há geração de arquivo PDF no servidor.

O método Certificado.gerarPDF() mantém uma simulação textual
no terminal. Ele não cria arquivos e não é o mecanismo
utilizado pelo botão da página.
