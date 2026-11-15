from datetime import time

from werkzeug.security import generate_password_hash

from app.model.enums import CategoriaMaterial, DiaSemana, TipoPontoColeta
from app.model.usuario import (
    Catador,
    Cooperativa,
    EmpresaCompradora,
    IndustriaTransformadora,
    UsuarioComum,
)
from app.model.material import TipoMaterial
from app.model.coleta import HorarioFuncionamento, PontoColeta

SENHA_DEMO = "123456"


class Repositorio:
    """Singleton com a persistência em memória da Recicl.AI (padrão da aula 29-32)."""

    __instancia = None

    def __new__(cls):
        if cls.__instancia is None:
            cls.__instancia = super().__new__(cls)
            cls.__instancia.__inicializar()
        return cls.__instancia

    def __inicializar(self):
        self.usuarios = []
        self.tipos = []
        self.materiais = []
        self.lotes = []
        self.transacoes = []
        self.pontos = []
        self.certificados = []

        self.__seed()

    def __seed(self):
        senha_hash = generate_password_hash(SENHA_DEMO)

        ana = UsuarioComum(
            "Ana",
            "ana@email.com",
            senha_hash,
            "62999999999",
            "Rua A, Goiânia"
        )

        carlos = Catador(
            "Carlos",
            "carlos@email.com",
            senha_hash,
            "62988888888",
            "Rua B, Goiânia",
            "12345678900"
        )

        cooperativa_verde = Cooperativa(
            "Cooperativa Verde",
            "cooperativa@email.com",
            senha_hash,
            "62977777777",
            "Rua C, Goiânia",
            "12345678000199"
        )

        empresa_recicladora = EmpresaCompradora(
            "Empresa Recicladora",
            "empresa@email.com",
            senha_hash,
            "62966666666",
            "Rua D, Goiânia",
            "98765432000188"
        )

        industria_circular = IndustriaTransformadora(
            "Indústria Circular",
            "industria@email.com",
            senha_hash,
            "62955555555",
            "Rua E, Goiânia",
            "11223344000155"
        )

        self.usuarios.extend([
            ana,
            carlos,
            cooperativa_verde,
            empresa_recicladora,
            industria_circular,
        ])

        tipo_pet = TipoMaterial("PET", "Plástico PET reciclável", CategoriaMaterial.PLASTICO)
        tipo_vidro = TipoMaterial("Vidro", "Embalagem de vidro reciclável", CategoriaMaterial.VIDRO)
        tipo_papel = TipoMaterial("Papel", "Papel e papelão recicláveis", CategoriaMaterial.PAPEL)
        tipo_metal = TipoMaterial("Metal", "Latas e sucata metálica", CategoriaMaterial.METAL)

        self.tipos.extend([tipo_pet, tipo_vidro, tipo_papel, tipo_metal])

        horario_comercial = HorarioFuncionamento(DiaSemana.SEGUNDA, time(8, 0), time(18, 0))
        horario_sabado = HorarioFuncionamento(DiaSemana.SABADO, time(8, 0), time(12, 0))

        self.pontos.extend([
            PontoColeta(
                "Ecoponto Setor Bueno",
                "Av. T-63, Setor Bueno, Goiânia",
                -16.7079,
                -49.2733,
                TipoPontoColeta.ECOPONTO,
                tiposAceitos=[tipo_pet, tipo_vidro, tipo_papel, tipo_metal],
                horarios=[horario_comercial],
            ),
            PontoColeta(
                "Cooperativa Verde - Unidade Central",
                "Rua C, Goiânia",
                -16.6799,
                -49.2550,
                TipoPontoColeta.COOPERATIVA,
                tiposAceitos=[tipo_pet, tipo_papel, tipo_metal],
                horarios=[horario_comercial, horario_sabado],
            ),
            PontoColeta(
                "PEV Setor Marista",
                "Av. República do Líbano, Setor Marista, Goiânia",
                -16.7074,
                -49.2642,
                TipoPontoColeta.PONTO_ENTREGA_VOLUNTARIA,
                tiposAceitos=[tipo_vidro, tipo_metal],
                horarios=[horario_comercial],
            ),
            PontoColeta(
                "Ecoponto Campinas",
                "Av. Anhanguera, Campinas, Goiânia",
                -16.6775,
                -49.2843,
                TipoPontoColeta.ECOPONTO,
                tiposAceitos=[tipo_pet, tipo_vidro],
                horarios=[horario_sabado],
            ),
        ])

    def resetar(self):
        """Recria o repositório do zero (usado pelo endpoint de demo /admin/reset)."""
        type(self).__instancia = None
        return Repositorio()
