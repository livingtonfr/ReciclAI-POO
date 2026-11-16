# Organização da Recicl.AI

## Estado atual

As fases 1 a 5 do acompanhamento atual foram concluídas para o fluxo
principal. O histórico está em STATUS_PROJETO.md.

A aplicação utiliza MVC com serviços e DAOs. Usuários, tipos de material,
materiais, lotes, propostas, vendas, certificados e eventos de
rastreabilidade são gravados em SQLite e permanecem após reiniciar o
servidor. Pontos de coleta, identificação, avaliação e precificação
continuam em memória ou simulados.

## Inicialização

mainFlask.py prepara o banco, informa seu caminho no terminal e inicia
o servidor.

app/__init__.py cria a aplicação Flask, carrega as configurações,
registra a integração com o banco e importa os controladores para
registrar as rotas.

app/config.py centraliza as configurações: caminho do banco
(DATABASE_PATH, ou a variável RECICLAI_DB), permissão de reset da
demonstração (RECICLAI_PERMITIR_RESET) e SECRET_KEY.

## Organização das pastas

| Local | Responsabilidade |
|---|---|
| app/model/ | Entidades, enumerações e regras do domínio |
| app/controller/ | Requisições HTTP e respostas HTML ou JSON |
| app/services/ | Coordenação das operações e permissões |
| app/dao/ | DAOs em memória e em SQLite, e o repositório em memória |
| app/database/ | Esquemas SQL, conexão, integração com o Flask e carga inicial |
| app/view/ | Templates Jinja |
| app/static/ | CSS e imagens |
| app/patterns/ | Estrutura reservada para os padrões escolhidos |
| tests/ | Testes automatizados e cenário de integração |
| docs/ | Documentação técnica |

A pasta app/patterns ainda não possui implementação própria.

Ordem de leitura sugerida: model, services, dao, database e controller.
Ela acompanha o caminho do dado, das regras até as rotas, e explica as
decisões melhor do que a ordem alfabética dos arquivos.

## Controladores

Recebem requisições, leem os campos dos formulários, convertem
valores de entrada e produzem respostas HTML ou JSON.

Chamam os serviços para executar as operações da aplicação.
As funções que montam as dependências obtêm a conexão SQLite da
requisição e criam os DAOs e serviços com ela. O Repositorio é
referenciado apenas para pontos de coleta e simulações de IA.

O usuário da sessão é carregado do banco uma vez por requisição e
guardado em flask.g.

## Serviços

Coordenam as operações e verificam permissões de acesso.

Incluem materiais, lotes, transações, usuários, pontos de coleta,
identificação de resíduos, rastreabilidade e demonstração.

Não dependem de request, session, render_template ou abort.

Comparam usuários pelo UUID (atributo id), e não pela identidade do
objeto, porque o SQLite devolve uma instância nova a cada consulta.

## Acesso aos dados

Cada contrato de acesso (usuários, tipos, materiais, lotes, transações
e certificados) tem duas implementações com a mesma interface:

- DAOs em memória, que consultam as listas do Repositorio. São usados
  pelos testes escritos antes da persistência.
- DAOs SQLite (arquivos terminados em _sqlite_dao.py), sem ORM, usados
  pela aplicação Flask.

Os serviços funcionam com as duas implementações. Foi essa decisão que
permitiu manter os testes anteriores sem alteração ao introduzir o
banco.

O Repositorio mantém os pontos de coleta, as simulações de IA e as
listas usadas pelos DAOs em memória.

## Banco de dados SQLite

O banco fica em instance/reciclai.sqlite3, pasta ignorada pelo Git.
Os esquemas SQL ficam em app/database, divididos por assunto (usuários,
materiais, lotes, vínculos, transações, certificados e eventos).

| Arquivo | Responsabilidade |
|---|---|
| conexao.py | Abre conexões e executa os esquemas |
| inicializacao.py | Cria as tabelas |
| contexto.py | Integra o banco ao ciclo de requisição do Flask |
| seed.py | Carga inicial de demonstração, limpeza e reset |

### Conexão e transação por requisição

Cada requisição usa uma conexão, guardada em flask.g. Ao final, se a
resposta tiver status menor que 400, a transação recebe commit. Nos
demais casos, ou diante de exceção, recebe rollback. A conexão é sempre
fechada.

Operações compostas dos DAOs usam SAVEPOINT. Por isso, uma falha de
negócio capturada por um controlador não deixa gravação parcial, mesmo
quando a resposta final ainda é uma página normal.

### Inicialização do banco

preparar_banco cria as tabelas e a carga inicial uma vez por processo e
por caminho de banco, com uma trava para evitar concorrência. Ela é
chamada por mainFlask.py e não no import do pacote app, porque os testes
importam app e usam bancos temporários próprios.

As tabelas usam IF NOT EXISTS e não há migração. Um banco de versão
anterior deve ser apagado antes de iniciar.

### Carga inicial e reset

A carga inicial é repetível: não duplica usuários nem tipos, não apaga
dados e não reaplica a senha de uma conta existente.

O reset apaga todos os dados do banco. Por isso vem desabilitado e só
funciona com RECICLAI_PERMITIR_RESET=1 e em modo debug. O botão da
interface só aparece nesse caso. Para zerar sem o reset, pare o servidor
e apague o arquivo do banco.

## Modelo

As classes preservam as regras do domínio, incluindo:

- Limites e validações de valores numéricos.
- Permissões de criação de lotes.
- Homogeneidade dos materiais de um lote.
- Vínculos entre materiais e lotes.
- Estados dos materiais, lotes e transações.
- Transferência de responsabilidade e rastreabilidade.
- Condições para conclusão e certificação das transações.

### Reconstrução a partir do banco

Os métodos reconstituir e restaurar_transacoes recriam objetos já
existentes sem repetir efeitos de negócio, como mudar de estado ou
registrar eventos.

O modelo exige instâncias compartilhadas dentro de um mesmo grafo: o
vendedor de uma transação é a mesma instância do criador do lote, e o
responsável pelos materiais também. Por isso a reconstrução segue uma
ordem sem recursão:

1. O lote é montado com seus materiais e seu criador.
2. carregar_transacoes_do_lote reconstrói as transações e os
   certificados, apontando para esse mesmo lote.

Um lote sem registros comerciais é lido sem transações, o que preserva o
comportamento dos testes anteriores.

### Pesagem dos lotes

calcularPesoTotal() soma os pesos dos materiais do lote.
pesoRegistrado representa uma pesagem informada separadamente.

Após adicionar ou remover um material com sucesso,
pesoRegistrado passa a ser None, pois a composição foi alterada.

A invalidação ocorre depois da atualização do vínculo e da
lista de materiais. Operações recusadas preservam a pesagem
anterior.

Uma nova pesagem pode ser registrada conforme as regras
existentes de estado e de validação numérica.

Na conclusão da transação, o sistema utiliza a pesagem
registrada quando ela existe. Caso contrário, utiliza
a soma dos pesos dos materiais. O valor usado é gravado como
peso negociado e não muda se os materiais forem alterados depois.

## Transações e conclusão atômica

Propostas são gravadas com as regras de que o lote esteja DISPONIVEL,
o vendedor seja o criador do lote e o mesmo comprador não tenha outra
proposta pendente no mesmo lote.

A conclusão segue dois passos:

1. O serviço carrega o grafo e executa Transacao.concluir() no modelo,
   que aplica as regras e transfere a responsabilidade.
2. registrar_conclusao grava o resultado em um único SAVEPOINT: novo
   responsável e estado dos materiais, eventos de transferência e de
   destinação, remoção dos vínculos do lote, lote NEGOCIADO, transação
   CONCLUIDA com o peso negociado e propostas concorrentes CANCELADAS.

O material recebido por empresa ou cooperativa fica DISPONIVEL; o
recebido por indústria fica DESTINADO.

Se qualquer passo da gravação falhar, nenhum material, evento, vínculo,
lote ou transação permanece alterado. Isso foi testado com uma falha SQL
provocada no último passo.

Cancelar um lote com propostas pendentes também cancela essas propostas
no banco.

## Certificados

A emissão e a consulta são coordenadas pelo TransacaoService,
com armazenamento pelo CertificadoDAO (em memória) ou pelo
CertificadoSQLiteDAO.

O certificado só pode ser associado a uma transação concluída, o que é
conferido no modelo e no banco. Há um certificado por transação, com
código único.

A consulta pela aplicação é restrita aos participantes
da transação.

A página apresenta o certificado em HTML. Seu botão chama
window.print(), permitindo imprimir ou salvar em PDF pelo
navegador. É um recurso acadêmico de rastreabilidade, sem validade
jurídica.

Certificado.gerarPDF() é uma simulação textual no terminal:
não gera arquivo PDF e não é chamado pelo botão de impressão.

## Limitações conhecidas

- Pontos de coleta continuam fixos em memória; identificação, avaliação
  e precificação são simuladas, e as cotações não são gravadas.
- Requer Python 3.12 ou superior, pelo parâmetro autocommit do sqlite3.
- Não há migração de estrutura do banco.
- Um lote NEGOCIADO sem nenhuma transação gravada (dado legado) é lido
  sem transações.
- Não há controle de concorrência além do bloqueio do próprio SQLite.
- Não há proteção CSRF, a SECRET_KEY padrão é fixa, o servidor roda com
  debug ligado e GET /logout altera a sessão. São aceitáveis no escopo
  acadêmico.

## Verificação

A suíte automatizada utiliza unittest e possui 249 testes, todos
executados com sucesso: 223 escritos antes da integração com o Flask e
26 adicionados nela.

O módulo tests.cenario executa o roteiro de integração
do modelo. Seu resultado final inclui duas transações
concluídas, seis eventos de rastreabilidade e material
destinado à indústria.

Além da suíte, foram conferidos manualmente o fluxo pelo navegador e o
roteiro de duas vendas consecutivas com o servidor real, encerrado e
iniciado novamente, verificando que os dados permanecem.
