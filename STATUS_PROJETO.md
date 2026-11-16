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
- [ ] Alterações registradas e enviadas ao GitHub.