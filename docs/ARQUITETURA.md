# Organização da Recicl.AI

## Inicialização

mainFlask.py inicia o servidor.

app/__init__.py cria a aplicação Flask, carrega as configurações
e importa os controllers para registrar as rotas.

app/config.py centraliza as configurações da aplicação.

## Pastas existentes

- app/model: entidades, enumerações e regras do domínio.
- app/controller: rotas e tratamento das requisições.
- app/dao: acesso aos dados; atualmente utiliza repositório em memória.
- app/view: páginas HTML com templates Jinja.
- app/static: arquivos CSS, imagens e JavaScript.
- tests: cenários e testes.
- docs: documentação técnica.

## Pastas preparadas para as próximas fases

- app/services: coordenação de operações que envolvem domínio e armazenamento.
- app/patterns: implementações dos padrões de projeto escolhidos.
- app/database: código de inicialização e estrutura do banco.

Essas três pastas ainda não representam funcionalidades implementadas.

## Armazenamento local futuro

O banco SQLite ficará na pasta instance, ignorada pelo Git.

O código de criação das tabelas ficará em app/database e será versionado.

## Limites desta etapa

A Fase 2 organiza a estrutura e centraliza configurações.

O armazenamento permanece em memória.
As regras de negócio e funcionalidades existentes foram preservadas.
A separação efetiva entre controllers, serviços e DAOs será feita
nas próximas fases.

## Organização após a fase 4

### Controladores — app/controller

Recebem requisições, leem os campos dos formulários, convertem
valores de entrada e produzem respostas HTML ou JSON.

Chamam os serviços para executar as operações da aplicação.
As referências ao Repositorio ficam nas funções que montam
as dependências.

### Serviços — app/services

Coordenam as operações e verificam permissões de acesso.

Incluem materiais, lotes, transações, usuários, pontos de coleta,
identificação de resíduos, rastreabilidade e demonstração.

Não dependem de request, session, render_template ou abort.

### Acesso aos dados — app/dao

Os DAOs centralizam consultas e inclusões nas listas do
repositório em memória.

O Repositorio mantém os dados e a inicialização da demonstração.

### Modelo — app/model

As classes preservam as regras do domínio, como limites de peso,
estados dos materiais e lotes, transferência de responsabilidade
e condições para conclusão e certificação das transações.

### Persistência atual

Os dados ainda ficam em memória e não são preservados após
reiniciar o processo.

As alterações nos objetos são observadas pelo repositório porque
ele mantém referências aos mesmos objetos.

A fase 5 implementará a persistência SQLite, incluindo gravação
das alterações, reconstrução dos relacionamentos e transações
de banco de dados.

### Certificados

A página permite imprimir ou salvar em PDF pela janela de
impressão do navegador. Não há geração de arquivo PDF no servidor.