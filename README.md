# Sistema de Cadastro de Alunos

Aplicação gráfica para cadastrar, consultar, editar e excluir alunos. Os dados
são armazenados permanentemente em `alunos.db`, criado ao executar o programa.

## Requisitos

- Python 3.9 ou superior
- Dependência listada em `requirements.txt`

Instale as dependências e execute:

```powershell
python -m pip install -r requirements.txt
python sistema_alunos.py
```

O SQLite já faz parte da biblioteca padrão do Python, portanto não precisa ser
instalado separadamente.

## Campos e validações

- Matrícula, nome, curso e email são obrigatórios.
- O email precisa ter um formato válido.
- O email deve ser escrito apenas com letras minúsculas.
- A matrícula é a chave primária e não pode se repetir.
- A exclusão pede confirmação.
- A busca localiza alunos pelo nome ou pela matrícula.
- A lista pode ser exportada para CSV pelo botão da interface.

## Banco de dados

O script `banco.sql` cria a tabela usada pela aplicação:

| Campo | Tipo | Regras |
| --- | --- | --- |
| `matricula` | `TEXT` | Chave primária |
| `nome` | `TEXT` | Obrigatório |
| `curso` | `TEXT` | Obrigatório |
| `email` | `TEXT` | Obrigatório |
| `data_cadastro` | `TIMESTAMP` | Obrigatório; preenchido automaticamente |

```sql
CREATE TABLE IF NOT EXISTS alunos (
    matricula TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    curso TEXT NOT NULL,
    email TEXT NOT NULL,
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

