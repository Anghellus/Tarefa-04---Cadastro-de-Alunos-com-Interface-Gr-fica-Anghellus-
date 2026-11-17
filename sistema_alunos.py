import csv
import re
import sqlite3
from contextlib import closing
from pathlib import Path

import FreeSimpleGUI as sg


CAMINHO_BANCO = Path(__file__).with_name("alunos.db")
EMAIL_VALIDO = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def criar_conexao(caminho=CAMINHO_BANCO):
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_tabela(caminho=CAMINHO_BANCO):
    with closing(criar_conexao(caminho)) as conexao, conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS alunos (
                matricula TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                curso TEXT NOT NULL,
                email TEXT NOT NULL,
                data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def validar_campos(matricula, nome, curso, email):
    campos = {
        "Matrícula": matricula,
        "Nome": nome,
        "Curso": curso,
        "Email": email,
    }
    vazios = [rotulo for rotulo, valor in campos.items() if not valor.strip()]
    if vazios:
        raise ValueError(f"Preencha os campos obrigatórios: {', '.join(vazios)}.")
    if any(caractere.isalpha() for caractere in matricula):
        raise ValueError("A matrícula não pode conter letras.")
    if any(caractere.isupper() for caractere in email):
        raise ValueError("O email deve conter apenas letras minúsculas.")
    if not EMAIL_VALIDO.fullmatch(email.strip()):
        raise ValueError("Digite um endereço de email válido.")


def inserir_aluno(matricula, nome, curso, email, caminho=CAMINHO_BANCO):
    validar_campos(matricula, nome, curso, email)
    try:
        with closing(criar_conexao(caminho)) as conexao, conexao:
            conexao.execute(
                "INSERT INTO alunos (matricula, nome, curso, email) VALUES (?, ?, ?, ?)",
                (matricula.strip(), nome.strip(), curso.strip(), email.strip()),
            )
    except sqlite3.IntegrityError as erro:
        if "UNIQUE constraint failed" in str(erro):
            raise ValueError("Já existe um aluno cadastrado com essa matrícula.") from erro
        raise


def buscar_aluno(matricula, caminho=CAMINHO_BANCO):
    with closing(criar_conexao(caminho)) as conexao:
        aluno = conexao.execute(
            "SELECT matricula, nome, curso, email, data_cadastro "
            "FROM alunos WHERE matricula = ?",
            (matricula.strip(),),
        ).fetchone()
    return tuple(aluno) if aluno else None


def atualizar_aluno(matricula, nome, curso, email, caminho=CAMINHO_BANCO):
    validar_campos(matricula, nome, curso, email)
    with closing(criar_conexao(caminho)) as conexao, conexao:
        cursor = conexao.execute(
            "UPDATE alunos SET nome = ?, curso = ?, email = ? WHERE matricula = ?",
            (nome.strip(), curso.strip(), email.strip(), matricula.strip()),
        )
        if cursor.rowcount == 0:
            raise ValueError("Aluno não encontrado.")


def excluir_aluno(matricula, caminho=CAMINHO_BANCO):
    with closing(criar_conexao(caminho)) as conexao, conexao:
        cursor = conexao.execute(
            "DELETE FROM alunos WHERE matricula = ?", (matricula.strip(),)
        )
        if cursor.rowcount == 0:
            raise ValueError("Aluno não encontrado.")


def listar_todos(caminho=CAMINHO_BANCO):
    with closing(criar_conexao(caminho)) as conexao:
        alunos = conexao.execute(
            "SELECT matricula, nome, curso, email, data_cadastro "
            "FROM alunos ORDER BY nome COLLATE NOCASE"
        ).fetchall()
    return [tuple(aluno) for aluno in alunos]


def buscar_por_termo(termo, caminho=CAMINHO_BANCO):
    termo = termo.strip()
    if not termo:
        raise ValueError("Digite um nome ou uma matrícula para buscar.")
    padrao = f"%{termo}%"
    with closing(criar_conexao(caminho)) as conexao:
        alunos = conexao.execute(
            "SELECT matricula, nome, curso, email, data_cadastro FROM alunos "
            "WHERE matricula LIKE ? OR nome LIKE ? ORDER BY nome COLLATE NOCASE",
            (padrao, padrao),
        ).fetchall()
    return [tuple(aluno) for aluno in alunos]


def exportar_csv(caminho_csv, caminho=CAMINHO_BANCO):
    alunos = listar_todos(caminho)
    with open(caminho_csv, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(
            ["Matrícula", "Nome", "Curso", "Email", "Data de cadastro"]
        )
        escritor.writerows(alunos)


def atualizar_tabela(janela, alunos):
    janela["-TABELA-"].update(values=[aluno[:4] for aluno in alunos])


def confirmar_exclusao(nome, matricula):
    layout = [
        [sg.Text(f"Confirma a exclusão de {nome} (matrícula {matricula})?")],
        [sg.Button("Sim"), sg.Button("Não")],
    ]
    janela = sg.Window("Confirmar exclusão", layout, modal=True)
    try:
        evento, _ = janela.read()
        return evento == "Sim"
    finally:
        janela.close()


def main():
    criar_tabela()
    sg.theme("SystemDefault")
    colunas = ["Matrícula", "Nome", "Curso", "Email"]

    layout = [
        [sg.Text("Sistema de Cadastro de Alunos", font=("Arial", 16, "bold"))],
        [
            sg.Text("Matrícula", size=(18, 1)),
            sg.Input(key="-MATRICULA-", size=(35, 1), enable_events=True),
        ],
        [sg.Text("Nome", size=(18, 1)), sg.Input(key="-NOME-", size=(55, 1))],
        [sg.Text("Curso", size=(18, 1)), sg.Input(key="-CURSO-", size=(55, 1))],
        [sg.Text("Email", size=(18, 1)), sg.Input(key="-EMAIL-", size=(55, 1))],
        [
            sg.Button("Cadastrar"),
            sg.Button("Editar"),
            sg.Button("Excluir"),
            sg.Button("Limpar"),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Text("Buscar por nome ou matrícula:"),
            sg.Input(key="-BUSCA-", size=(35, 1)),
            sg.Button("Buscar"),
            sg.Button("Listar todos"),
            sg.Button("Exportar CSV"),
        ],
        [
            sg.Table(
                values=[],
                headings=colunas,
                key="-TABELA-",
                auto_size_columns=True,
                display_row_numbers=False,
                justification="left",
                num_rows=12,
                expand_x=True,
                expand_y=True,
                enable_events=True,
                select_mode=sg.TABLE_SELECT_MODE_BROWSE,
            )
        ],
        [sg.Text("Selecione um aluno na tabela para carregar seus dados.")],
        [sg.Button("Sair")],
    ]

    janela = sg.Window(
        "Sistema de Cadastro de Alunos",
        layout,
        resizable=True,
        finalize=True,
    )
    alunos_exibidos = listar_todos()
    atualizar_tabela(janela, alunos_exibidos)

    while True:
        evento, valores = janela.read()
        if evento in (sg.WIN_CLOSED, "Sair"):
            break

        try:
            matricula = valores["-MATRICULA-"].strip()
            nome = valores["-NOME-"].strip()
            curso = valores["-CURSO-"].strip()
            email = valores["-EMAIL-"].strip()

            if evento == "Cadastrar":
                inserir_aluno(matricula, nome, curso, email)
                alunos_exibidos = listar_todos()
                atualizar_tabela(janela, alunos_exibidos)
                sg.popup_ok("Aluno cadastrado com sucesso!")

            elif evento == "Buscar":
                alunos_exibidos = buscar_por_termo(valores["-BUSCA-"])
                atualizar_tabela(janela, alunos_exibidos)
                if not alunos_exibidos:
                    sg.popup_ok("Nenhum aluno encontrado.")

            elif evento == "Listar todos":
                alunos_exibidos = listar_todos()
                atualizar_tabela(janela, alunos_exibidos)
                janela["-BUSCA-"].update("")

            elif evento == "-MATRICULA-":
                if any(caractere.isalpha() for caractere in matricula):
                    janela["-MATRICULA-"].update(
                        "".join(
                            caractere
                            for caractere in matricula
                            if not caractere.isalpha()
                        )
                    )

            elif evento == "Editar":
                atualizar_aluno(matricula, nome, curso, email)
                alunos_exibidos = listar_todos()
                atualizar_tabela(janela, alunos_exibidos)
                sg.popup_ok("Dados do aluno alterados com sucesso!")

            elif evento == "Excluir":
                aluno = buscar_aluno(matricula)
                if aluno is None:
                    raise ValueError("Aluno não encontrado.")
                if confirmar_exclusao(aluno[1], matricula):
                    excluir_aluno(matricula)
                    alunos_exibidos = listar_todos()
                    atualizar_tabela(janela, alunos_exibidos)
                    sg.popup_ok("Aluno excluído com sucesso.")

            elif evento == "-TABELA-":
                selecionados = valores["-TABELA-"]
                if selecionados:
                    aluno = alunos_exibidos[selecionados[0]]
                    janela["-MATRICULA-"].update(aluno[0])
                    janela["-NOME-"].update(aluno[1])
                    janela["-CURSO-"].update(aluno[2])
                    janela["-EMAIL-"].update(aluno[3])

            elif evento == "Exportar CSV":
                caminho_csv = sg.popup_get_file(
                    "Salvar lista de alunos",
                    save_as=True,
                    default_extension=".csv",
                    default_path="alunos.csv",
                    file_types=(("Arquivos CSV", "*.csv"),),
                )
                if caminho_csv:
                    exportar_csv(caminho_csv)
                    sg.popup_ok("Lista exportada com sucesso.")

            elif evento == "Limpar":
                for chave in ("-MATRICULA-", "-NOME-", "-CURSO-", "-EMAIL-"):
                    janela[chave].update("")

        except ValueError as erro:
            sg.popup_error(str(erro), title="Dados inválidos")
        except (sqlite3.Error, OSError) as erro:
            sg.popup_error(f"Não foi possível concluir a operação: {erro}")

    janela.close()


if __name__ == "__main__":
    main()
