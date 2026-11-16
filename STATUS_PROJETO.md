# Estado do projeto Recicl.AI

## Objetivo
Concluir a aplicação acadêmica de POO, aproveitando a implementação
existente e aprimorando organização, persistência e testes.

## Base
Projeto recebido no arquivo reciclai.zip.
Histórico Git original preservado.

## Verificações da Fase 1
- [x] ZIP original preservado.
- [x] Ambiente Python configurado.
- [x] Dependências instaladas.
- [x] Cenário tests.cenario executado e conferido.
- [x] Aplicação aberta no navegador.
- [x] Login e fluxo básico de materiais e lotes verificados.
- [x] Confirmado que os dados desaparecem após reiniciar.
- [x] Projeto enviado para repositório privado no GitHub.

## Limitações atuais
- Armazenamento em memória, sem banco de dados.
- Identificação, avaliação e precificação simuladas.
- Certificado apresentado em página imprimível.
- Testes existentes baseados principalmente em mensagens no terminal.

## Próximas etapas
- Reorganizar pastas e responsabilidades.
- Corrigir validações e regras do domínio.
- Separar controllers, serviços e DAOs.
- Implementar persistência com SQLite.
- Completar desativação de contas e controles de acesso.
- Integrar os padrões escolhidos.
- Revisar interface, automatizar testes e atualizar documentação.

## Ajustes de funcionalidades planejados
- Adicionar acesso ao mapa em todas as telas.
- Mostrar cooperativas, empresas e indústrias no mapa.
- Distinguir estabelecimentos de locais que recebem materiais do público.
- Permitir cadastro de materiais por cooperativas e empresas compradoras.
- Não duplicar materiais adquiridos dentro da plataforma.
- Manter a indústria sem cadastro de materiais e sem criação ou venda de lotes.
- Retirar Pontos de coleta do painel da indústria.
- Mostrar programação da coleta seletiva ao usuário comum.
- Identificar explicitamente os dados simulados.

## Pontos a confirmar com o professor
- Data e formato da entrega final.
- Funcionalidades mínimas exigidas.
- Exigência de banco de dados e de integração dos padrões.

## Fase 2 — Organização

- [x] Criada branch específica para a reorganização.
- [x] Preparadas pastas services, patterns e database.
- [x] Centralizadas configurações em app/config.py.
- [x] Atualizados os arquivos de inicialização.
- [x] Documentada a estrutura em docs/ARQUITETURA.md.
- [x] Cenário de classes executado após as alterações.
- [x] Navegação básica conferida após as alterações.
- [x] Alterações registradas e enviadas ao GitHub.

## Fase 3 — Regras do domínio

### Bloco 3A — Validações numéricas
- [x] Centralizadas as validações numéricas.
- [x] Pesos e valores exigem números finitos e positivos.
- [x] Confianças exigem valores numéricos entre 0 e 1.
- [x] Horizonte de cotação exige inteiro positivo.
- [x] Testes automáticos do bloco executados.
- [x] Cenário anterior e cadastro de material conferidos.
- [x] Definidos limites operacionais de peso para a versão acadêmica: até 50.000 kg por material e por lote.
- [x] Validada a soma dos materiais antes da inclusão no lote.
- [x] Validada a pesagem do lote, preservando o valor anterior quando uma tentativa é recusada.
- [x] Executados 14 testes de validação numérica.
- [x] Reexecutado o cenário completo de rastreabilidade.

Os limites são regras do sistema e não representam a capacidade
legal de transporte de um veículo específico.

### Fase 3B — Permissões de criação de lotes

- [x] A classe LoteMaterial permite criação somente por catadores,
cooperativas e empresas compradoras.
- [x] Indústrias e usuários comuns não podem criar lotes,
inclusive por chamada direta ao construtor.
- [x] O criador precisa ser o responsável atual pelo material.
- [x] Tentativas recusadas preservam o material.
- [x] Executados 18 testes automatizados com sucesso.
- [x] Cenário completo de rastreabilidade continua funcionando.

### Fase 3C — Vínculos entre materiais e lotes

- [x] Ajustada a ordem de inclusão e remoção de materiais.
- [x] Verificada a preservação das listas quando os métodos
      de agrupamento ou remoção recusam a operação.
- [x] Testado o impedimento de vínculo simultâneo a dois lotes.
- [x] Testado o impedimento de remoção do único material.
- [x] Executados 23 testes automatizados com sucesso.
- [x] Cenário completo de rastreabilidade preservado.

### Fase 3C — Estados de lotes e transações

- [x] Conferidos responsável, estado e vínculo de todos os
materiais antes da conclusão de uma transação.
- [x] Validado o peso negociado antes das alterações.
- [x] Testado o cancelamento de lote com proposta pendente.
- [x] Testado o cancelamento de propostas concorrentes.
- [x] Testadas tentativas de repetir uma conclusão ou cancelar
um lote já negociado.
- [x] Testada a recusa de conclusão diante de materiais
inconsistentes, sem transferência parcial.
- [x] Executados 27 testes automatizados com sucesso.
- [x] Cenário completo de rastreabilidade preservado.

### Fase 3D — Horários dos pontos e conferência final

- [x] Cada ponto de coleta possui seus próprios objetos de horário.
- [x] Alterações nas listas externas não apagam os horários internos.
- [x] Testada a rejeição de elementos que não são horários.
- [x] Testada a regra de abertura anterior ao fechamento.
- [x] Executada a suíte automatizada sem falhas.
- [x] Reexecutado o cenário completo de rastreabilidade.
- [x] Conferidas as páginas de pontos de coleta e o fluxo
de cadastro de material e criação de lote.

### Fase 4A — Consultas de materiais

- [x] Criado MaterialDAO para consultas em memória.
- [x] Criado MaterialService para coordenar consultas e permissões.
- [x] Listagem e busca de materiais utilizam o serviço.
- [x] Preservadas as respostas 403 e 404.
- [x] Testes anteriores e cenário executados sem falhas.
- [x] Conferidos listagem, detalhes e bloqueio de acesso
a material de outro responsável.

Cadastro, disponibilização, avaliação e cotação ainda serão
migrados nas próximas etapas.

### Fase 4B — Cadastro e disponibilização de materiais

- [x] Cadastro coordenado pelo MaterialService.
- [x] Inclusão no armazenamento centralizada no MaterialDAO.
- [x] Disponibilização coordenada pelo serviço.
- [x] Preservadas as permissões e validações do modelo.
- [x] Adicionados cinco testes do serviço e do DAO.
- [x] Suíte, cenário e verificações no navegador aprovados.

### Fase 4C — Consulta dos tipos de material

- [x] Criado TipoMaterialDAO.
- [x] Listagem e busca dos tipos passam pelo MaterialService.
- [x] Removido o acesso direto à lista de tipos no controlador de materiais.
- [x] Adicionados três testes de consulta dos tipos.
- [x] Suíte automatizada e cadastro pelo navegador verificados.

Avaliação e cotação ainda serão migradas para o serviço.

### Fase 4C — Avaliação e cotação de materiais

- [x] Avaliação e cotação coordenadas pelo MaterialService.
- [x] Permissões verificadas antes de acionar os serviços de IA.
- [x] Serviços simulados recebidos pelo construtor.
- [x] Controlador de materiais sem acesso direto às listas
do repositório.
- [x] Adicionados quatro testes de avaliação, cotação e acesso.
- [x] Suíte, cenário e verificações no navegador aprovados.

### Fase 4D — Consultas de lotes

- [x] Criados LoteDAO e LoteService.
- [x] Listagem e busca de lotes passam pelo serviço.
- [x] Consulta de materiais disponíveis utiliza MaterialDAO.
- [x] Preservadas as permissões de gerenciamento do criador.
- [x] Adicionados quatro testes de consultas e permissões.
- [x] Suíte e verificações no navegador aprovadas.

Criação e alterações dos lotes ainda serão migradas.

### Fase 4E — Criação e composição dos lotes

- [x] Criação coordenada pelo LoteService.
- [x] Armazenamento centralizado no LoteDAO.
- [x] Inclusão e remoção de materiais passam pelo serviço.
- [x] Preservadas as permissões e as regras de LoteMaterial.
- [x] Adicionados cinco testes das operações.
- [x] Suíte e verificações no navegador aprovadas.

### Fase 4F — Pesagem, estados e cotação dos lotes

- [x] Pesagem coordenada pelo LoteService.
- [x] Disponibilização e cancelamento passam pelo serviço.
- [x] Precificação recebida pelo construtor do serviço.
- [x] Cotação coordenada pelo LoteService.
- [x] Controlador de lotes sem acesso direto ao repositório nas rotas.
- [x] Adicionados cinco testes das operações e permissões.
- [x] Suíte, cenário e verificações no navegador aprovados.

### Fase 4G.1 — Consultas do Mercado e das transações

- [x] Criados TransacaoDAO e TransacaoService.
- [x] Mercado utiliza consulta de lotes disponíveis pelo DAO.
- [x] Preservados filtro de lotes próprios e cálculo sugerido.
- [x] Listas de propostas e vendas passam pelo serviço.
- [x] Busca de transação verifica o vendedor no serviço.
- [x] Adicionados cinco testes de consultas e permissões.
- [x] Suíte e verificações no navegador aprovadas.

Envio, conclusão, cancelamento e certificados serão
migrados no bloco 4G.2.

### Fase 4G.2.1 — Saída do certificado em PDF ou impressão

- [x] Botão para abrir a impressão com opção de salvar em PDF.
- [x] Orientação de escolha do destino apresentada na tela.
- [x] Estilos de impressão ocultam os controles da aplicação.
- [x] Link de retorno considera comprador ou vendedor.
- [x] PDF salvo e conferido visualmente.

A geração do PDF utiliza a impressão do navegador.
A migração das operações de transações e certificados
para serviços e DAOs ainda está pendente.

### Fase 4G.2.2 — Operações de transações e certificados

- [x] Envio de propostas coordenado pelo TransacaoService.
- [x] Verificação de proposta pendente duplicada no serviço.
- [x] Conclusão e cancelamento passam pelo serviço.
- [x] Criado CertificadoDAO.
- [x] Emissão e consulta de certificados passam pelo serviço.
- [x] Consulta restrita aos participantes da transação.
- [x] Preservados botão de PDF/impressão e link de retorno.
- [x] Adicionados cinco testes das operações.
- [x] Suíte, cenário e fluxo pelo navegador aprovados.

### Fase 4H.1 — Consultas de usuários e autenticação

- [x] Criados UsuarioDAO e UsuarioService.
- [x] Busca do usuário conectado passa pelo serviço.
- [x] Autenticação coordenada pelo UsuarioService.
- [x] Preservada a verificação de senha pelo modelo.
- [x] Preservados sessão e redirecionamentos.
- [x] Corrigido comentário sobre seleção de menu por tipo.
- [x] Adicionados cinco testes de consultas e autenticação.
- [x] Suíte e verificações no navegador aprovadas.

Cadastro e atualização de perfil serão migrados na 4H.2.

### Fase 4H.2 — Cadastro e atualização de perfil

- [x] Cadastro coordenado pelo UsuarioService.
- [x] Armazenamento centralizado no UsuarioDAO.
- [x] Criação de usuários limitada aos cinco perfis previstos.
- [x] Atualização de perfil coordenada pelo serviço.
- [x] Validação de e-mail duplicado antes das alterações.
- [x] Preservada a geração e verificação de hash de senha.
- [x] Adicionados seis testes de cadastro e perfil.
- [x] Suíte e verificações no navegador aprovadas.

### Fase 4I.1 — Consultas dos pontos de coleta

- [x] Criados PontoColetaDAO e PontoColetaService.
- [x] Listagem e filtro por material passam pelo serviço.
- [x] Consulta de tipos reutiliza TipoMaterialDAO.
- [x] Preservados template, horários e links existentes.
- [x] Preservada a exigência de login.
- [x] Adicionados cinco testes das consultas.
- [x] Suíte e verificações no navegador aprovadas.

### Fase 4I.2 — Identificação, API e demonstração

- [x] Identificação coordenada pelo IdentificacaoService.
- [x] API de pontos reutiliza PontoColetaService.
- [x] Histórico consultado pelo RastreabilidadeService.
- [x] Preservado acesso do responsável atual e dos participantes
      de transações concluídas.
- [x] Reset coordenado pelo DemoService.
- [x] Reset testado sem apagar dados reais da demonstração.
- [x] Adicionados quatro testes dos serviços complementares.
- [x] Suíte, cenário e consultas pelo navegador aprovados.

### Fase 4J — Revisão final

- [x] Conferidas as referências ao Repositorio nos controladores.
- [x] Documentada a divisão entre controladores, serviços,
      DAOs e modelo.
- [x] Documentadas as limitações do armazenamento em memória.
- [x] Suíte automatizada e cenário aprovados após as alterações.
- [x] Integrar a branch fase-4-servicos-dao à master.

## Revisão após a fase 4 — preparação para SQLite

- [x] Invalidada a pesagem após inclusão ou remoção bem-sucedida de materiais.
- [x] Preservada a pesagem quando a operação é recusada.
- [x] Acrescentados quatro testes de regressão.
- [x] Executada a suíte de 92 testes com sucesso.
- [x] Atualizadas as descrições da arquitetura e das fases no README.
- [x] Atualizada a documentação das responsabilidades das pastas.
- [x] Esclarecida a simulação de Certificado.gerarPDF().
- [x] Documentada a impressão e o salvamento em PDF pelo navegador.

A fase 5 de persistência SQLite ainda não foi iniciada.

## Fase 5A — Infraestrutura de conexão SQLite

- [x] Confirmado o funcionamento do SQLite no ambiente Python.
- [x] Configurado o caminho instance/reciclai.sqlite3.
- [x] Implementado gerenciamento de conexões e transações.
- [x] Ativada a verificação de chaves estrangeiras.
- [x] Testadas persistência, reversão e fechamento das conexões.
- [x] Executados os 97 testes com sucesso.

A fase 5 está em andamento. Este bloco prepara a infraestrutura.
As tabelas do domínio e a migração dos DAOs ainda estão pendentes.
A aplicação continua utilizando o repositório em memória.

## Fase 5B.1 — Tabela de tipos de material

- [x] Criada a tabela tipos_material.
- [x] Representados UUID como texto e booleano como 0 ou 1.
- [x] Restringidas as categorias aos valores do enum atual.
- [x] Implementada inicialização sem apagar registros existentes.
- [x] Testada a preservação dos dados após reinicialização.
- [x] Executados os 100 testes com sucesso.

A tabela ainda não está conectada ao TipoMaterialDAO.
A interface continua utilizando o repositório em memória.

## Fase 5B.2 — DAO SQLite de tipos de material

- [x] Implementada reconstrução de TipoMaterial com UUID original.
- [x] Preservados categoria e estado ativo na reconstrução.
- [x] Criado TipoMaterialSQLiteDAO com inclusão, listagem e busca.
- [x] Utilizadas consultas parametrizadas.
- [x] Mantido o controle da transação fora do DAO.
- [x] Testadas persistência e reversão diante de duplicidade.
- [x] Executados os 104 testes com sucesso.
- [x] Reexecutado o cenário de integração.

O DAO SQLite ainda não está conectado aos controladores.
A aplicação continua utilizando o repositório em memória.
A integração deverá preservar a identidade dos objetos relacionados.

## Fase 5C.1 — Estrutura de usuários

- [x] Criada a tabela usuarios para os cinco perfis existentes.
- [x] Preparados campos de hash de senha, data e localização.
- [x] Definidas restrições de documentos conforme o perfil.
- [x] Definidos os valores permitidos de situação de validação.
- [x] Testada a rejeição de e-mail duplicado com variação de caixa ASCII.
- [x] Adaptada a inicialização para executar os dois arquivos SQL.
- [x] Testada a preservação dos registros após reinicialização.
- [x] Executados os 108 testes com sucesso.

O DAO SQLite de usuários e sua integração ainda estão pendentes.
A autenticação da aplicação continua utilizando dados em memória.

## Fase 5C.2 — Reconstrução e DAO SQLite de usuários

- [x] Implementada reconstrução dos cinco perfis.
- [x] Preservados UUID, data, localização e documentos.
- [x] Preservada a situação de validação dos perfis empresariais.
- [x] Disponibilizado o hash existente para persistência.
- [x] Criado UsuarioSQLiteDAO com inclusão e consultas.
- [x] Testados cadastro e autenticação após reabrir o banco.
- [x] Testadas duplicidades e reversão da transação.
- [x] Executados os 113 testes com sucesso.
- [x] Reexecutado o cenário de integração.

O DAO SQLite ainda não está conectado aos controladores.
A atualização persistente de perfil e o tratamento de identidade
dos objetos serão implementados antes da integração.

## Fase 5C.3 — Atualização persistente de perfil

- [x] Adaptado o serviço para reconhecer usuários pelo UUID.
- [x] Encaminhada a atualização de perfil aos DAOs.
- [x] Preservado o funcionamento do repositório em memória.
- [x] Implementada atualização de perfil no SQLite.
- [x] Preservados hash, UUID, data, documento e situação de validação.
- [x] Testada a autenticação com o novo e-mail após reabrir o banco.
- [x] Testada a recusa de e-mail duplicado sem alteração dos dados.
- [x] Testada a reversão diante de erro posterior na transação.
- [x] Executados os 118 testes e o cenário de integração.

Os controladores ainda utilizam o repositório em memória.
A integração com SQLite e a identidade dos demais objetos
relacionados continuam pendentes.

## Fase 5D.1 — Estrutura de materiais e rastreabilidade

- [x] Criadas as tabelas materiais, eventos_rastreio e avaliacoes_qualidade.
- [x] Definidos vínculos com tipos de material e usuários.
- [x] Definidas posições para preservar a ordem de eventos e avaliações.
- [x] Preservada a separação entre condição declarada e detectada.
- [x] Testados limites numéricos e referências inexistentes.
- [x] Testada a preservação dos registros após reinicialização.
- [x] Testada a reversão conjunta de material e evento.
- [x] Executados os 123 testes com sucesso.

A reconstrução dos objetos e o DAO SQLite de materiais ainda
estão pendentes. O vínculo com lotes será implementado no bloco 5E.
A interface continua utilizando o repositório em memória.