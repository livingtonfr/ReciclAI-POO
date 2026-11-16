# Organização da Recicl.AI

## Estado atual

As fases 1 a 4 do acompanhamento atual foram concluídas.
A fase 5, dedicada à persistência SQLite, ainda não começou.

A aplicação utiliza MVC com serviços e DAOs. Os dados
permanecem em memória.

## Inicialização

mainFlask.py inicia o servidor.

app/__init__.py cria a aplicação Flask, carrega as configurações
e importa os controladores para registrar as rotas.

app/config.py centraliza as configurações da aplicação.

## Organização das pastas

| Local | Responsabilidade |
|---|---|
| app/model/ | Entidades, enumerações e regras do domínio |
| app/controller/ | Requisições HTTP e respostas HTML ou JSON |
| app/services/ | Coordenação das operações e permissões |
| app/dao/ | Acesso ao repositório em memória |
| app/view/ | Templates Jinja |
| app/static/ | CSS e imagens |
| app/database/ | Estrutura reservada para SQLite |
| app/patterns/ | Estrutura reservada para os padrões escolhidos |
| tests/ | Testes automatizados e cenário de integração |
| docs/ | Documentação técnica |

A camada de serviços está implementada.
As pastas database e patterns ainda não possuem implementações
próprias nesta etapa.

## Controladores

Recebem requisições, leem os campos dos formulários, convertem
valores de entrada e produzem respostas HTML ou JSON.

Chamam os serviços para executar as operações da aplicação.
As referências ao Repositorio ficam nas funções que montam
as dependências.

## Serviços

Coordenam as operações e verificam permissões de acesso.

Incluem materiais, lotes, transações, usuários, pontos de coleta,
identificação de resíduos, rastreabilidade e demonstração.

Não dependem de request, session, render_template ou abort.

## Acesso aos dados

Os DAOs centralizam consultas e inclusões nas listas do
repositório em memória.

O Repositorio mantém os dados e a inicialização da demonstração.

As alterações nos objetos são observadas pelo repositório
porque ele mantém referências aos mesmos objetos.

## Modelo

As classes preservam as regras do domínio, incluindo:

- Limites e validações de valores numéricos.
- Permissões de criação de lotes.
- Homogeneidade dos materiais de um lote.
- Vínculos entre materiais e lotes.
- Estados dos materiais, lotes e transações.
- Transferência de responsabilidade e rastreabilidade.
- Condições para conclusão e certificação das transações.

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
a soma dos pesos dos materiais.

## Certificados

A emissão e a consulta são coordenadas pelo TransacaoService,
com armazenamento pelo CertificadoDAO.

O certificado só pode ser associado a uma transação concluída.
A consulta pela aplicação é restrita aos participantes
da transação.

A página apresenta o certificado em HTML. Seu botão chama
window.print(), permitindo imprimir ou salvar em PDF pelo
navegador.

Certificado.gerarPDF() é uma simulação textual no terminal:
não gera arquivo PDF e não é chamado pelo botão de impressão.

## Persistência planejada — fase 5

O banco SQLite ficará na pasta instance, ignorada pelo Git.
O código de inicialização e estrutura ficará em app/database.

A implementação deverá contemplar a gravação das alterações,
a reconstrução dos relacionamentos e o uso de transações
de banco de dados.

Até essa implementação, os dados não são preservados após
reiniciar o processo.

## Verificação

A suíte automatizada utiliza unittest e possui 92 testes
após a correção da pesagem.

O módulo tests.cenario executa o roteiro de integração
do modelo. Seu resultado final inclui duas transações
concluídas, seis eventos de rastreabilidade e material
destinado à indústria.