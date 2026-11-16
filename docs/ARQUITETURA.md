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