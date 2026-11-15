"""
Cenario de integracao (celulas 8.1 a 8.10 do notebook).

Roda no terminal e deve produzir os mesmos resultados do notebook:
    python tests/cenario.py
"""

from app.model.enums import CategoriaMaterial, CondicaoMaterial, DiaSemana, TipoPontoColeta
from app.model.usuario import Catador, Cooperativa, EmpresaCompradora, IndustriaTransformadora, UsuarioComum
from app.model.material import TipoMaterial
from app.model.comercial import CotacaoPreco, Transacao, Certificado
from app.model.coleta import HorarioFuncionamento, PontoColeta
from app.model.servicos_ia import ResultadoIdentificacao, VisaoComputacionalIA, PrecificacaoIA


# ---------------------------------------------------------------------------
# 8.1 - Preparacao dos objetos de teste
# ---------------------------------------------------------------------------

tipo_pet_teste = TipoMaterial(
    "PET",
    "Plástico PET reciclável",
    CategoriaMaterial.PLASTICO
)

usuario_comum_teste = UsuarioComum(
    "Ana",
    "ana@email.com",
    "hash123",
    "62999999999",
    "Rua A"
)

catador_teste = Catador(
    "Carlos",
    "carlos@email.com",
    "hash456",
    "62988888888",
    "Rua B",
    "12345678900"
)

cooperativa_teste = Cooperativa(
    "Cooperativa Verde",
    "cooperativa@email.com",
    "hash789",
    "62977777777",
    "Rua C",
    "12345678000199"
)

empresa_teste = EmpresaCompradora(
    "Empresa Recicladora",
    "empresa@email.com",
    "hash321",
    "62966666666",
    "Rua D",
    "98765432000188"
)

industria_teste = IndustriaTransformadora(
    "Indústria Circular",
    "industria@email.com",
    "hash654",
    "62955555555",
    "Rua E",
    "11223344000155"
)

visao_teste = VisaoComputacionalIA(
    tipo_pet_teste,
    0.82,
    CondicaoMaterial.SUJO,
    0.90
)

precificacao_teste = PrecificacaoIA(2.75)

print("Objetos de teste criados com sucesso.")


# ---------------------------------------------------------------------------
# 8.2 - Identificacao e avaliacao por IA
# ---------------------------------------------------------------------------

resultado_identificacao = usuario_comum_teste.identificarResiduo(
    "foto_garrafa_pet.jpg",
    visao_teste
)

print(resultado_identificacao.tipoMaterial.nome)
print(resultado_identificacao.confianca)

material_teste = catador_teste.registrarMaterial(
    tipo_pet_teste,
    10.0,
    CondicaoMaterial.LIMPO,
    "Garrafa PET separada para reciclagem."
)

print(material_teste.tipoMaterial.nome)
print(material_teste.pesoKg)
print(material_teste.condicaoDeclarada)
print(material_teste.responsavelAtual.nome)
print(material_teste.status)

avaliacao_teste = visao_teste.avaliarMaterial(
    material_teste,
    "foto_garrafa_pet.jpg"
)

print(avaliacao_teste.condicaoDetectada)
print(avaliacao_teste.confianca)

print("Condição declarada:", material_teste.condicaoDeclarada)
print(
    "Quantidade de avaliações:",
    len(material_teste.obterAvaliacoes())
)

avaliacoes_material = material_teste.obterAvaliacoes()

print(avaliacoes_material[0] is avaliacao_teste)


# ---------------------------------------------------------------------------
# 8.3 - Material, rastreabilidade e formacao de lote
# ---------------------------------------------------------------------------

historico_inicial = material_teste.obterHistorico()

print("Quantidade de eventos:", len(historico_inicial))

for evento in historico_inicial:
    print(evento.tipo, "-", evento.descricao)

material_teste.disponibilizar()

print(material_teste.status)

lote_teste = catador_teste.criarLote(material_teste)

print(lote_teste.criador.nome)
print(lote_teste.calcularPesoTotal())
print(material_teste.status)
print(material_teste.loteAtual is lote_teste)

for evento in material_teste.obterHistorico():
    print(evento.tipo, "-", evento.descricao)

tipo_vidro_teste = TipoMaterial(
    "Vidro",
    "Embalagem de vidro reciclável",
    CategoriaMaterial.VIDRO
)

material_vidro_teste = catador_teste.registrarMaterial(
    tipo_vidro_teste,
    5.0,
    CondicaoMaterial.LIMPO
)

material_vidro_teste.disponibilizar()

try:
    lote_teste.adicionarMaterial(material_vidro_teste)
    print("ERRO: material incompatível foi aceito.")
except ValueError as erro:
    print("OK:", erro)


# ---------------------------------------------------------------------------
# 8.4 - Precificacao e regra {xor}
# ---------------------------------------------------------------------------

cotacao_material_teste = catador_teste.solicitarPrecificacaoMaterial(
    material_teste,
    15,
    precificacao_teste
)

print(cotacao_material_teste.valorPorKg)
print(cotacao_material_teste.horizonteDias)
print(cotacao_material_teste.material is material_teste)
print(cotacao_material_teste.lote)

cotacao_lote_teste = catador_teste.solicitarPrecificacaoLote(
    lote_teste,
    30,
    precificacao_teste
)

print(cotacao_lote_teste.valorPorKg)
print(cotacao_lote_teste.horizonteDias)
print(cotacao_lote_teste.material)
print(cotacao_lote_teste.lote is lote_teste)

try:
    cotacao_invalida = CotacaoPreco(
        2.75,
        15,
        material=material_teste,
        lote=lote_teste
    )
    print("ERRO: cotação com duas fontes foi aceita.")
except ValueError as erro:
    print("OK:", erro)

try:
    cotacao_sem_fonte = CotacaoPreco(2.75, 15)
    print("ERRO: cotação sem fonte foi aceita.")
except ValueError as erro:
    print("OK:", erro)


# ---------------------------------------------------------------------------
# 8.5 - Fluxo comercial e transacao
# ---------------------------------------------------------------------------

lote_teste.disponibilizar()

print(lote_teste.status)

transacao_teste = Transacao(
    lote_teste,
    catador_teste,
    empresa_teste,
    32.00
)

print(transacao_teste.status)
print(transacao_teste.valorTotal)

print(material_teste.responsavelAtual.nome)
print(lote_teste.status)

transacao_teste.concluir()

print(transacao_teste.status)
print(transacao_teste.pesoNegociado)
print(lote_teste.status)

print(material_teste.responsavelAtual.nome)
print(material_teste.status)
print(material_teste.loteAtual)

for evento in material_teste.obterHistorico():
    print(evento.tipo, "-", evento.descricao)

novo_lote_teste = empresa_teste.criarLote(material_teste)

print(novo_lote_teste.criador.nome)
print(novo_lote_teste.calcularPesoTotal())
print(material_teste.status)
print(material_teste.loteAtual is novo_lote_teste)


# ---------------------------------------------------------------------------
# 8.6 - Industria e destinacao final
# ---------------------------------------------------------------------------

cotacao_industria_teste = industria_teste.solicitarPrecificacaoLote(
    novo_lote_teste,
    30,
    precificacao_teste
)

print(cotacao_industria_teste.valorPorKg)
print(cotacao_industria_teste.horizonteDias)
print(cotacao_industria_teste.lote is novo_lote_teste)

novo_lote_teste.disponibilizar()

print(novo_lote_teste.status)

transacao_industria_teste = Transacao(
    novo_lote_teste,
    empresa_teste,
    industria_teste,
    35.00
)

print(transacao_industria_teste.status)
print(material_teste.responsavelAtual.nome)

transacao_industria_teste.concluir()

print(transacao_industria_teste.status)
print(transacao_industria_teste.pesoNegociado)
print(novo_lote_teste.status)

print(material_teste.responsavelAtual.nome)
print(material_teste.status)
print(material_teste.loteAtual)

for evento in material_teste.obterHistorico():
    print(evento.tipo, "-", evento.descricao)

print(
    "IndustriaTransformadora possui criarLote:",
    hasattr(industria_teste, "criarLote")
)


# ---------------------------------------------------------------------------
# 8.7 - Certificacao da transacao
# ---------------------------------------------------------------------------

material_certificado_teste = catador_teste.registrarMaterial(
    tipo_pet_teste,
    3.0,
    CondicaoMaterial.LIMPO
)

material_certificado_teste.disponibilizar()

lote_certificado_teste = catador_teste.criarLote(material_certificado_teste)

lote_certificado_teste.disponibilizar()

transacao_pendente_teste = Transacao(
    lote_certificado_teste,
    catador_teste,
    empresa_teste,
    12.00
)

certificado_invalido_teste = Certificado("CERT-INVALIDO-001")

try:
    transacao_pendente_teste.associarCertificado(certificado_invalido_teste)
    print("ERRO: certificado associado a transação pendente.")
except ValueError as erro:
    print("OK:", erro)


# ---------------------------------------------------------------------------
# 8.8 - Ponto de coleta e horario de funcionamento
# ---------------------------------------------------------------------------

tipo_pet_ponto = TipoMaterial(
    "PET",
    "Plástico PET reciclável",
    CategoriaMaterial.PLASTICO
)

tipo_vidro_ponto = TipoMaterial(
    "Vidro",
    "Embalagem de vidro reciclável",
    CategoriaMaterial.VIDRO
)

horario_teste = HorarioFuncionamento(
    DiaSemana.SEGUNDA,
    "08:00",
    "17:00"
)

ponto_teste = PontoColeta(
    "Ecoponto Central",
    "Avenida Central, 100",
    -16.6869,
    -49.2648,
    TipoPontoColeta.ECOPONTO,
    tiposAceitos=[tipo_pet_ponto],
    horarios=[horario_teste]
)

print("Ponto:", ponto_teste.nome)
print("Endereço:", ponto_teste.endereco)
print("Latitude:", ponto_teste.latitude)
print("Longitude:", ponto_teste.longitude)

print("Aceita PET:", ponto_teste.aceitaMaterial(tipo_pet_ponto))
print("Aceita vidro:", ponto_teste.aceitaMaterial(tipo_vidro_ponto))
print("Quantidade de horários:", len(ponto_teste.horarios))


# ---------------------------------------------------------------------------
# 8.9 - Validacoes e regras de excecao
# ---------------------------------------------------------------------------

print("=== TESTES DE EXCEÇÃO ===")

try:
    from app.model.material import Material
    material_invalido = Material(
        tipo_pet_teste,
        0,
        CondicaoMaterial.LIMPO,
        catador_teste
    )
    print("ERRO 1: material com peso zero foi aceito.")
except ValueError as erro:
    print("OK 1:", erro)

try:
    resultado_invalido = ResultadoIdentificacao(tipo_pet_teste, 1.5)
    print("ERRO 2: confiança acima de 1 foi aceita.")
except ValueError as erro:
    print("OK 2:", erro)

try:
    from app.model.material import AvaliacaoQualidade
    avaliacao_invalida = AvaliacaoQualidade(
        CondicaoMaterial.LIMPO,
        -0.1,
        "Teste inválido"
    )
    print("ERRO 3: confiança negativa foi aceita.")
except ValueError as erro:
    print("OK 3:", erro)

material_estado_teste = catador_teste.registrarMaterial(
    tipo_pet_teste,
    2.0,
    CondicaoMaterial.LIMPO
)

material_estado_teste.disponibilizar()

try:
    material_estado_teste.disponibilizar()
    print("ERRO 4: material foi disponibilizado duas vezes.")
except ValueError as erro:
    print("OK 4:", erro)

material_lote_a = catador_teste.registrarMaterial(
    tipo_pet_teste,
    4.0,
    CondicaoMaterial.LIMPO
)

material_lote_a.disponibilizar()

lote_bloqueado_teste = catador_teste.criarLote(material_lote_a)

lote_bloqueado_teste.disponibilizar()

material_lote_b = catador_teste.registrarMaterial(
    tipo_pet_teste,
    2.0,
    CondicaoMaterial.LIMPO
)

material_lote_b.disponibilizar()

try:
    lote_bloqueado_teste.adicionarMaterial(material_lote_b)
    print("ERRO 5: lote disponível foi alterado.")
except ValueError as erro:
    print("OK 5:", erro)


# ---------------------------------------------------------------------------
# 8.10 - Conferencia final da integracao
# ---------------------------------------------------------------------------

print("=== CONFERÊNCIA FINAL ===")

print("Material:", material_teste.tipoMaterial.nome)
print("Responsável final:", material_teste.responsavelAtual.nome)
print("Status final do material:", material_teste.status)
print("Avaliações registradas:", len(material_teste.obterAvaliacoes()))
print("Eventos de rastreio:", len(material_teste.obterHistorico()))
print("1ª transação:", transacao_teste.status)
print("2ª transação:", transacao_industria_teste.status)
print(
    "Destino final:",
    isinstance(material_teste.responsavelAtual, IndustriaTransformadora)
)
print("Ponto aceita PET:", ponto_teste.aceitaMaterial(tipo_pet_ponto))
print(
    "Cotação XOR material:",
    cotacao_material_teste.material is not None
    and cotacao_material_teste.lote is None
)
print(
    "Cotação XOR lote:",
    cotacao_lote_teste.material is None
    and cotacao_lote_teste.lote is not None
)
