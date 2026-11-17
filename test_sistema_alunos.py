import csv
import tempfile
import unittest
from pathlib import Path

import sistema_alunos as sistema


class TestBancoAlunos(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.banco = Path(self.diretorio.name) / "teste.db"
        sistema.criar_tabela(self.banco)

    def tearDown(self):
        self.diretorio.cleanup()

    def test_crud_persiste_dados_e_impede_matricula_repetida(self):
        sistema.inserir_aluno("2024001", "Ana Silva", "Computação", "ana@example.com", self.banco)
        self.assertEqual(sistema.buscar_aluno("2024001", self.banco)[1:4],
                         ("Ana Silva", "Computação", "ana@example.com"))

        with self.assertRaisesRegex(ValueError, "Já existe"):
            sistema.inserir_aluno("2024001", "Outra Ana", "Outro curso", "outra@example.com", self.banco)

        sistema.atualizar_aluno("2024001", "Ana Souza", "Sistemas", "ana.souza@example.com", self.banco)
        self.assertEqual(sistema.listar_todos(self.banco)[0][1:4],
                         ("Ana Souza", "Sistemas", "ana.souza@example.com"))
        self.assertEqual(len(sistema.buscar_por_termo("souza", self.banco)), 1)

        sistema.excluir_aluno("2024001", self.banco)
        self.assertEqual(sistema.listar_todos(self.banco), [])

    def test_valida_email_e_exporta_csv(self):
        with self.assertRaisesRegex(ValueError, "email válido"):
            sistema.inserir_aluno("2024002", "Bruno", "Computação", "email-inválido", self.banco)
        with self.assertRaisesRegex(ValueError, "letras minúsculas"):
            sistema.inserir_aluno("2024002", "Bruno", "Computação", "Bruno@example.com", self.banco)

        sistema.inserir_aluno("2024002", "Bruno", "Computação", "bruno@example.com", self.banco)
        arquivo_csv = Path(self.diretorio.name) / "alunos.csv"
        sistema.exportar_csv(arquivo_csv, self.banco)

        with arquivo_csv.open(newline="", encoding="utf-8-sig") as arquivo:
            linhas = list(csv.reader(arquivo))
        self.assertEqual(linhas[1][:4], ["2024002", "Bruno", "Computação", "bruno@example.com"])

    def test_matricula_nao_aceita_letras(self):
        with self.assertRaisesRegex(ValueError, "matrícula não pode conter letras"):
            sistema.inserir_aluno(
                "2024ABC",
                "Carla",
                "Computação",
                "carla@example.com",
                self.banco,
            )


if __name__ == "__main__":
    unittest.main()
