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