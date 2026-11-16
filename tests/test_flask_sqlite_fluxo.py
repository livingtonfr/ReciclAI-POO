"""Fluxo completo da apresentação, pela interface Flask, com SQLite real.

Cada "reinício" abre um cliente novo (sem cookies) e limpa o cache de
preparação do banco, como faria um novo processo.
"""

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import app
from app.database import contexto


class BaseFluxo(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp())
        self.caminho = self.pasta / "teste.sqlite3"
        self.config_anterior = {
            k: app.config.get(k)
            for k in ("DATABASE_PATH", "TESTING", "PERMITIR_RESET_DEMO")
        }
        app.config.update(
            DATABASE_PATH=self.caminho,
            TESTING=True,
            PERMITIR_RESET_DEMO=False,
        )
        contexto._preparados.clear()

    def tearDown(self):
        app.config.update(self.config_anterior)
        contexto._preparados.clear()
        shutil.rmtree(self.pasta, ignore_errors=True)

    def reiniciar(self):
        contexto._preparados.clear()

    def cliente(self, email=None, senha="123456"):
        cliente = app.test_client()

        if email:
            resposta = cliente.post(
                "/login", data={"email": email, "senha": senha}
            )
            self.assertEqual(resposta.status_code, 302)
            self.assertTrue(resposta.headers["Location"].endswith("/dashboard"))

        return cliente

    def sql(self, consulta, parametros=()):
        conexao = sqlite3.connect(self.caminho)
        conexao.row_factory = sqlite3.Row
        try:
            return conexao.execute(consulta, parametros).fetchall()
        finally:
            conexao.close()

    def tipo_id(self, nome="PET"):
        return self.sql(
            "SELECT id FROM tipos_material WHERE nome = ?", (nome,)
        )[0]["id"]

    def criar_lote_disponivel(self, carlos, peso=10, pesagem="9,5"):
        carlos.post("/materiais/novo", data={
            "tipo_id": self.tipo_id(), "pesoKg": str(peso),
            "condicaoDeclarada": "LIMPO", "observacoes": "",
        })
        material_id = self.sql(
            "SELECT id FROM materiais ORDER BY rowid DESC LIMIT 1"
        )[0]["id"]
        carlos.post(f"/materiais/{material_id}/disponibilizar")
        carlos.post("/lotes/novo", data={"material_id": material_id})
        lote_id = self.sql(
            "SELECT id FROM lotes ORDER BY rowid DESC LIMIT 1"
        )[0]["id"]
        if pesagem:
            carlos.post(f"/lotes/{lote_id}/pesagem", data={"peso": pesagem})
        carlos.post(f"/lotes/{lote_id}/disponibilizar")
        return material_id, lote_id


class TestInicializacao(BaseFluxo):
    def test_banco_criado_sem_duplicar_usuarios_e_tipos_ao_reiniciar(self):
        self.assertFalse(self.caminho.exists())
        self.cliente("carlos@email.com")
        self.reiniciar()
        self.cliente("carlos@email.com")
        self.reiniciar()
        self.cliente("empresa@email.com")

        self.assertEqual(self.sql("SELECT COUNT(*) c FROM usuarios")[0]["c"], 5)
        self.assertEqual(
            self.sql("SELECT COUNT(*) c FROM tipos_material")[0]["c"], 4
        )

    def test_semear_nao_reaplica_senha_de_conta_existente(self):
        from werkzeug.security import generate_password_hash
        self.cliente("ana@email.com")
        novo_hash = generate_password_hash("outra-senha")
        conexao = sqlite3.connect(self.caminho)
        conexao.execute(
            "UPDATE usuarios SET senha_hash = ? WHERE email = 'ana@email.com'",
            (novo_hash,),
        )
        conexao.commit()
        conexao.close()
        self.reiniciar()

        resposta = app.test_client().post(
            "/login", data={"email": "ana@email.com", "senha": "123456"}
        )
        self.assertEqual(resposta.status_code, 200)  # recusado

        resposta = app.test_client().post(
            "/login",
            data={"email": "ana@email.com", "senha": "outra-senha"},
        )
        self.assertEqual(resposta.status_code, 302)

    def test_cadastro_novo_permanece_apos_reiniciar(self):
        cliente = app.test_client()
        resposta = cliente.post("/cadastro/catador", data={
            "nome": "Maria", "email": "Maria@Email.com", "senha": "abcdef",
            "telefone": "62900000000", "endereco": "Rua X",
            "documento": "99988877766",
        })
        self.assertEqual(resposta.status_code, 302)
        self.reiniciar()
        self.cliente("maria@email.com", "abcdef")

    def test_cadastro_duplicado_e_recusado(self):
        resposta = app.test_client().post("/cadastro/comum", data={
            "nome": "Outra Ana", "email": "ana@email.com", "senha": "abcdef",
            "telefone": "1", "endereco": "x",
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            self.sql("SELECT COUNT(*) c FROM usuarios WHERE email='ana@email.com'")[0]["c"], 1
        )

    def test_sessao_continua_valida_apos_reiniciar(self):
        carlos = self.cliente("carlos@email.com")
        self.reiniciar()
        self.assertEqual(carlos.get("/materiais").status_code, 200)

    def test_reset_desabilitado_nao_apaga_nada(self):
        carlos = self.cliente("carlos@email.com")
        self.criar_lote_disponivel(carlos)
        resposta = carlos.post("/admin/reset")
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.sql("SELECT COUNT(*) c FROM lotes")[0]["c"], 1)
        pagina = carlos.get("/dashboard").get_data(as_text=True)
        self.assertNotIn("Resetar demo", pagina)

    def test_reset_habilitado_apaga_e_recarrega(self):
        app.config["PERMITIR_RESET_DEMO"] = True
        carlos = self.cliente("carlos@email.com")
        self.criar_lote_disponivel(carlos)
        resposta = carlos.post("/admin/reset")
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.sql("SELECT COUNT(*) c FROM lotes")[0]["c"], 0)
        self.assertEqual(self.sql("SELECT COUNT(*) c FROM materiais")[0]["c"], 0)
        self.assertEqual(self.sql("SELECT COUNT(*) c FROM usuarios")[0]["c"], 5)
        self.assertEqual(self.sql("SELECT COUNT(*) c FROM tipos_material")[0]["c"], 4)


class TestFluxoComercial(BaseFluxo):
    def test_fluxo_da_apresentacao_com_reinicios(self):
        carlos = self.cliente("carlos@email.com")
        material_id, lote_id = self.criar_lote_disponivel(carlos)

        lote = self.sql("SELECT * FROM lotes WHERE id = ?", (lote_id,))[0]
        self.assertEqual(lote["status"], "DISPONIVEL")
        self.assertEqual(lote["peso_registrado"], 9.5)

        # Reinício 1: material, lote, composição e pesagem permanecem.
        self.reiniciar()
        carlos = self.cliente("carlos@email.com")
        pagina = carlos.get(f"/lotes/{lote_id}").get_data(as_text=True)
        self.assertIn("DISPONIVEL", pagina)
        self.assertIn("9.5", pagina)
        pagina = carlos.get(f"/materiais/{material_id}").get_data(as_text=True)
        self.assertIn("EM_LOTE", pagina)

        # Empresa vê o mercado e propõe R$ 30,00.
        empresa = self.cliente("empresa@email.com")
        pagina = empresa.get("/mercado").get_data(as_text=True)
        self.assertIn("Carlos", pagina)
        empresa.post(f"/lotes/{lote_id}/propor", data={"valorTotal": "30,00"})

        # Proposta duplicada da mesma empresa é recusada (sem duplicar).
        empresa.post(f"/lotes/{lote_id}/propor", data={"valorTotal": "31"})
        self.assertEqual(
            self.sql("SELECT COUNT(*) c FROM transacoes")[0]["c"], 1
        )

        # Reinício 2: a proposta permanece.
        self.reiniciar()
        empresa = self.cliente("empresa@email.com")
        pagina = empresa.get("/minhas-propostas").get_data(as_text=True)
        self.assertIn("30.00", pagina)
        self.assertIn("PENDENTE", pagina)

        carlos = self.cliente("carlos@email.com")
        pagina = carlos.get("/transacoes").get_data(as_text=True)
        self.assertIn("Empresa Recicladora", pagina)
        transacao_id = self.sql("SELECT id FROM transacoes")[0]["id"]

        # Conclusão.
        resposta = carlos.post(f"/transacoes/{transacao_id}/concluir")
        self.assertEqual(resposta.status_code, 302)

        transacao = self.sql("SELECT * FROM transacoes")[0]
        self.assertEqual(transacao["status"], "CONCLUIDA")
        self.assertEqual(transacao["peso_negociado"], 9.5)
        self.assertEqual(
            self.sql("SELECT status FROM lotes WHERE id=?", (lote_id,))[0]["status"],
            "NEGOCIADO",
        )
        material = self.sql("SELECT * FROM materiais WHERE id=?", (material_id,))[0]
        empresa_id = self.sql(
            "SELECT id FROM usuarios WHERE email='empresa@email.com'"
        )[0]["id"]
        self.assertEqual(material["responsavel_atual_id"], empresa_id)
        self.assertEqual(material["status"], "DISPONIVEL")
        self.assertEqual(
            self.sql("SELECT COUNT(*) c FROM vinculos_lotes_atuais")[0]["c"], 0
        )

        # Certificado.
        resposta = carlos.post(f"/transacoes/{transacao_id}/certificado")
        self.assertEqual(resposta.status_code, 302)
        certificado = self.sql("SELECT * FROM certificados")[0]
        self.assertEqual(certificado["transacao_id"], transacao_id)
        self.assertTrue(certificado["codigo"].startswith("CERT-"))

        # Segunda emissão é recusada sem duplicar.
        carlos.post(f"/transacoes/{transacao_id}/certificado")
        self.assertEqual(
            self.sql("SELECT COUNT(*) c FROM certificados")[0]["c"], 1
        )

        # Reinício 3: tudo continua correto.
        self.reiniciar()
        carlos = self.cliente("carlos@email.com")
        empresa = self.cliente("empresa@email.com")
        url_cert = f"/certificados/{certificado['id']}"

        pagina = carlos.get(url_cert).get_data(as_text=True)
        self.assertIn(certificado["codigo"], pagina)
        self.assertIn("9.5 kg", pagina)
        self.assertIn("/transacoes", pagina)  # link de volta do vendedor

        pagina = empresa.get(url_cert).get_data(as_text=True)
        self.assertIn(certificado["codigo"], pagina)
        self.assertIn("/minhas-propostas", pagina)  # link de volta do comprador

        # Quem não participou não consulta o certificado.
        cooperativa = self.cliente("cooperativa@email.com")
        self.assertEqual(cooperativa.get(url_cert).status_code, 403)

        # Lista de vendas / propostas e material recebido com histórico.
        pagina = carlos.get("/transacoes").get_data(as_text=True)
        self.assertIn("CONCLUIDA", pagina)
        self.assertIn("Ver certificado", pagina)
        pagina = empresa.get("/minhas-propostas").get_data(as_text=True)
        self.assertIn("CONCLUIDA", pagina)

        pagina = empresa.get(f"/materiais/{material_id}").get_data(as_text=True)
        self.assertIn("TRANSFERENCIA", pagina)
        historico = empresa.get(f"/api/materiais/{material_id}/historico").get_json()
        self.assertEqual(
            [e["tipo"] for e in historico],
            ["REGISTRO", "AGRUPAMENTO_LOTE", "TRANSFERENCIA"],
        )
        # O vendedor histórico também consulta o histórico pela API.
        historico = carlos.get(f"/api/materiais/{material_id}/historico").get_json()
        self.assertEqual(len(historico), 3)
        self.assertEqual(
            cooperativa.get(f"/api/materiais/{material_id}/historico").status_code,
            403,
        )

        # O lote antigo continua consultável.
        pagina = carlos.get(f"/lotes/{lote_id}").get_data(as_text=True)
        self.assertIn("NEGOCIADO", pagina)

    def test_propostas_concorrentes_sao_canceladas_na_conclusao(self):
        carlos = self.cliente("carlos@email.com")
        material_id, lote_id = self.criar_lote_disponivel(carlos)

        empresa = self.cliente("empresa@email.com")
        cooperativa = self.cliente("cooperativa@email.com")
        industria = self.cliente("industria@email.com")
        empresa.post(f"/lotes/{lote_id}/propor", data={"valorTotal": "30"})
        cooperativa.post(f"/lotes/{lote_id}/propor", data={"valorTotal": "28"})
        industria.post(f"/lotes/{lote_id}/propor", data={"valorTotal": "35"})

        ids = {
            r["email"]: r["id"]
            for r in self.sql(
                "SELECT t.id, u.email FROM transacoes t "
                "JOIN usuarios u ON u.id = t.comprador_id"
            )
        }
        self.reiniciar()
        carlos = self.cliente("carlos@email.com")
        # Concluir a da indústria: material deve ficar DESTINADO.
        carlos.post(f"/transacoes/{ids['industria@email.com']}/concluir")

        status = {
            r["email"]: r["status"]
            for r in self.sql(
                "SELECT t.status, u.email FROM transacoes t "
                "JOIN usuarios u ON u.id = t.comprador_id"
            )
        }
        self.assertEqual(status["industria@email.com"], "CONCLUIDA")
        self.assertEqual(status["empresa@email.com"], "CANCELADA")
        self.assertEqual(status["cooperativa@email.com"], "CANCELADA")

        material = self.sql("SELECT * FROM materiais WHERE id=?", (material_id,))[0]
        self.assertEqual(material["status"], "DESTINADO")
        eventos = [
            r["tipo"]
            for r in self.sql(
                "SELECT tipo FROM eventos_rastreio WHERE material_id=? ORDER BY ordem",
                (material_id,),
            )
        ]
        self.assertEqual(
            eventos,
            ["REGISTRO", "AGRUPAMENTO_LOTE", "TRANSFERENCIA", "DESTINACAO"],
        )

        # Segunda conclusão (concorrente cancelada) é recusada.
        carlos.post(f"/transacoes/{ids['empresa@email.com']}/concluir")
        self.assertEqual(
            self.sql("SELECT COUNT(*) c FROM transacoes WHERE status='CONCLUIDA'")[0]["c"],
            1,
        )

        # A indústria vê o material recebido após reiniciar.
        self.reiniciar()
        industria = self.cliente("industria@email.com")
        pagina = industria.get("/materiais").get_data(as_text=True)
        self.assertIn("DESTINADO", pagina)

    def test_cancelar_lote_cancela_propostas_pendentes(self):
        carlos = self.cliente("carlos@email.com")
        material_id, lote_id = self.criar_lote_disponivel(carlos)
        empresa = self.cliente("empresa@email.com")
        empresa.post(f"/lotes/{lote_id}/propor", data={"valorTotal": "30"})

        carlos.post(f"/lotes/{lote_id}/cancelar")
        self.assertEqual(
            self.sql("SELECT status FROM lotes")[0]["status"], "CANCELADO"
        )
        self.assertEqual(
            self.sql("SELECT status FROM transacoes")[0]["status"], "CANCELADA"
        )
        self.assertEqual(
            self.sql("SELECT status FROM materiais")[0]["status"], "DISPONIVEL"
        )
        self.reiniciar()
        carlos = self.cliente("carlos@email.com")
        self.assertEqual(carlos.get(f"/lotes/{lote_id}").status_code, 200)
        empresa = self.cliente("empresa@email.com")
        self.assertIn("CANCELADA", empresa.get("/minhas-propostas").get_data(as_text=True))
        # O lote cancelado não aparece mais no mercado.
        self.assertNotIn("Carlos", empresa.get("/mercado").get_data(as_text=True))

    def test_vendedor_cancela_proposta_pendente(self):
        carlos = self.cliente("carlos@email.com")
        _, lote_id = self.criar_lote_disponivel(carlos)
        empresa = self.cliente("empresa@email.com")
        empresa.post(f"/lotes/{lote_id}/propor", data={"valorTotal": "30"})
        transacao_id = self.sql("SELECT id FROM transacoes")[0]["id"]
        carlos.post(f"/transacoes/{transacao_id}/cancelar")
        self.assertEqual(
            self.sql("SELECT status FROM transacoes")[0]["status"], "CANCELADA"
        )
        # Lote continua DISPONIVEL e aceita nova proposta.
        empresa.post(f"/lotes/{lote_id}/propor", data={"valorTotal": "32"})
        self.assertEqual(self.sql("SELECT COUNT(*) c FROM transacoes")[0]["c"], 2)

    def test_outro_usuario_nao_conclui_transacao_alheia(self):
        carlos = self.cliente("carlos@email.com")
        _, lote_id = self.criar_lote_disponivel(carlos)
        empresa = self.cliente("empresa@email.com")
        empresa.post(f"/lotes/{lote_id}/propor", data={"valorTotal": "30"})
        transacao_id = self.sql("SELECT id FROM transacoes")[0]["id"]

        cooperativa = self.cliente("cooperativa@email.com")
        self.assertEqual(
            cooperativa.post(f"/transacoes/{transacao_id}/concluir").status_code, 403
        )
        self.assertEqual(
            empresa.post(f"/transacoes/{transacao_id}/concluir").status_code, 403
        )
        self.assertEqual(self.sql("SELECT status FROM transacoes")[0]["status"], "PENDENTE")

    def test_proprio_lote_nao_pode_ser_proposto_pelo_criador(self):
        coop = self.cliente("cooperativa@email.com")
        # A cooperativa cria seu lote a partir de material recebido por compra.
        carlos = self.cliente("carlos@email.com")
        material_id, lote_id = self.criar_lote_disponivel(carlos)
        coop.post(f"/lotes/{lote_id}/propor", data={"valorTotal": "20"})
        transacao_id = self.sql("SELECT id FROM transacoes")[0]["id"]
        carlos.post(f"/transacoes/{transacao_id}/concluir")

        # A cooperativa agora é responsável pelo material e revende em lote.
        self.reiniciar()
        coop = self.cliente("cooperativa@email.com")
        coop.post("/lotes/novo", data={"material_id": material_id})
        novo_lote = self.sql("SELECT id FROM lotes ORDER BY rowid DESC LIMIT 1")[0]["id"]
        self.assertNotEqual(novo_lote, lote_id)
        coop.post(f"/lotes/{novo_lote}/disponibilizar")
        # Não vê o próprio lote no mercado nem consegue propor a si mesma.
        pagina = coop.get("/mercado").get_data(as_text=True)
        self.assertNotIn(novo_lote, pagina)
        coop.post(f"/lotes/{novo_lote}/propor", data={"valorTotal": "50"})
        self.assertEqual(self.sql("SELECT COUNT(*) c FROM transacoes")[0]["c"], 1)

        # O lote antigo (NEGOCIADO) continua consultável pelo vendedor
        # histórico, mesmo com o material agora em outro lote.
        carlos = self.cliente("carlos@email.com")
        resposta = carlos.get(f"/lotes/{lote_id}")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("NEGOCIADO", resposta.get_data(as_text=True))
        # E consultar o lote antigo não roubou o vínculo atual.
        vinculo = self.sql("SELECT lote_id FROM vinculos_lotes_atuais")[0]["lote_id"]
        self.assertEqual(vinculo, novo_lote)
        # A cooperativa vê o material EM_LOTE (reconstruído via lote ativo).
        pagina = coop.get(f"/materiais/{material_id}").get_data(as_text=True)
        self.assertIn("EM_LOTE", pagina)

    def test_falha_de_negocio_nao_deixa_gravacao_parcial(self):
        carlos = self.cliente("carlos@email.com")
        material_id, lote_id = self.criar_lote_disponivel(carlos)
        antes = {
            tabela: self.sql(f"SELECT COUNT(*) c FROM {tabela}")[0]["c"]
            for tabela in ("materiais", "lotes", "transacoes",
                           "eventos_rastreio", "lotes_materiais")
        }
        # Pesagem inválida, proposta inválida, adicionar material inexistente.
        carlos.post(f"/lotes/{lote_id}/pesagem", data={"peso": "-3"})
        carlos.post(f"/lotes/{lote_id}/adicionar", data={"material_id": "x"})
        empresa = self.cliente("empresa@email.com")
        empresa.post(f"/lotes/{lote_id}/propor", data={"valorTotal": "0"})
        empresa.post(f"/lotes/{lote_id}/propor", data={"valorTotal": "abc"})
        depois = {
            tabela: self.sql(f"SELECT COUNT(*) c FROM {tabela}")[0]["c"]
            for tabela in antes
        }
        self.assertEqual(antes, depois)
        self.assertEqual(
            self.sql("SELECT peso_registrado FROM lotes")[0]["peso_registrado"], 9.5
        )

    def test_lote_com_varios_materiais_e_remocao(self):
        carlos = self.cliente("carlos@email.com")
        ids = []
        for peso in ("4", "6"):
            carlos.post("/materiais/novo", data={
                "tipo_id": self.tipo_id(), "pesoKg": peso,
                "condicaoDeclarada": "LIMPO", "observacoes": "",
            })
            mid = self.sql("SELECT id FROM materiais ORDER BY rowid DESC LIMIT 1")[0]["id"]
            carlos.post(f"/materiais/{mid}/disponibilizar")
            ids.append(mid)
        carlos.post("/lotes/novo", data={"material_id": ids[0]})
        lote_id = self.sql("SELECT id FROM lotes")[0]["id"]
        carlos.post(f"/lotes/{lote_id}/adicionar", data={"material_id": ids[1]})
        self.assertEqual(
            self.sql("SELECT COUNT(*) c FROM vinculos_lotes_atuais")[0]["c"], 2
        )
        carlos.post(f"/lotes/{lote_id}/remover", data={"material_id": ids[1]})
        self.assertEqual(
            self.sql("SELECT COUNT(*) c FROM vinculos_lotes_atuais")[0]["c"], 1
        )
        self.reiniciar()
        carlos = self.cliente("carlos@email.com")
        self.assertIn("4.0 kg", carlos.get(f"/lotes/{lote_id}").get_data(as_text=True))

    def test_avaliar_material_em_lote_persiste_avaliacao(self):
        carlos = self.cliente("carlos@email.com")
        material_id, _ = self.criar_lote_disponivel(carlos)
        carlos.post(f"/materiais/{material_id}/avaliar", data={"foto": "f.jpg"})
        self.assertEqual(
            self.sql("SELECT COUNT(*) c FROM avaliacoes_qualidade")[0]["c"], 1
        )
        self.assertEqual(
            self.sql("SELECT status FROM materiais")[0]["status"], "EM_LOTE"
        )


if __name__ == "__main__":
    unittest.main()
