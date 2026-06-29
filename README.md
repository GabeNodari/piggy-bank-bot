# Piggy Bank Bot 💰
Um bot de finanças do Telegram que ajuda a rastrear despesas, gerenciar categorias e visualizar saldos mensais.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)

## Funcionalidades

- Menu principal com opções de teclado inline.
- Adicione categorias de despesas personalizadas.
- Edite categorias existentes da visualização de categorias.
- Adicione despesas com valor, descrição, data, categoria e flag recorrente.
- Visualize o gasto total do mês atual.
- Visualize totais de categorias para o mês atual.
- Visualize despesas recorrentes.
- Exclua despesas recentes.
- Resete o database.

## Requisitos

- Qualquer plataforma com suporte a Python.
- Python 3.8+ recomendado.
- `python-telegram-bot` e dependências de `requirements.txt`.
- Um bot do Telegram criado através do BotFather.
- Arquivo `.env` contendo a variável `TELEGRAM_TOKEN`.

## Estrutura do Projeto

- `bot.py`: lógica principal do bot e fluxos de conversa.
- `database.py`: criação de database SQLite e acesso aos dados.
- `financas.db`: arquivo de database SQLite gerado automaticamente.
- `requirements.txt`: dependências Python.

## Esquema do Database

### Tabela `categories`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id` INTEGER NOT NULL
- `name` TEXT NOT NULL

### Tabela `expenses`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id` INTEGER NOT NULL
- `amount` REAL NOT NULL
- `description` TEXT
- `date` TEXT NOT NULL
- `category_id` INTEGER
- `recurring` INTEGER NOT NULL CHECK (recurring IN (0, 1))
- `category_id` references `categories(id)`

## Fluxo Principal do Usuário

1. Iniciar o bot com `/start`.
2. O bot mostra o menu principal:
   - `💰 **Gabe's Piggy Bank**\n\nEscolha uma opção no menu abaixo:`
3. Adicionar uma categoria:
   - `📁 Digite o nome da nova categoria (ex: Alimentação, Lazer):`
   - Mensagem de sucesso: `✅ Categoria 'Name' criada com sucesso!`
4. Editar uma categoria:
   - `📁 Digite o novo nome para a categoria:`
   - Mensagem de sucesso: `✅ Categoria atualizada para 'Name' com sucesso!`
5. Adicionar uma despesa:
   - `💸 Digite o valor do gasto (Use pontos ou vírgulas, ex: 45.50):`
   - Mensagem de valor inválido: `❌ Valor inválido. Por favor, envie apenas números com ponto ou vírgula (ex: 150.75):`
   - `📝 Digite uma breve descrição para o gasto:`
   - `📅 Quando ocorreu esse gasto?`
   - Botões: `📅 Hoje` e `⌨️ Outra data (Digitar)`
   - `📁 Selecione a categoria para este gasto:`
   - `🔄 É um gasto fixo/recorrente mensal?`
   - Confirmação final: `✅ Gasto registrado com sucesso!`
6. Visualizar categorias:
   - `📑 **Categorias Disponíveis:**\n\nSelecione uma categoria para editar:`
   - Botões de categorias e `🔙 Voltar ao Menu`
7. Mensagens de fluxo comuns:
   - `Menu Principal:` retorna ao menu principal com botões.
   - `❌ Processo cancelado.` para cancelamento.

## Como Executar

**Obs.:** Dependendo do seu sistema, use `python3` ou `py` ao invés de `python`, e `pip3` ou `pip` conforme necessário.

1. Crie e ative um ambiente virtual (venv).

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Crie um arquivo `.env` com seu token do Telegram:

```env
TELEGRAM_TOKEN=seu_token_aqui
```

4. Execute o bot:

```bash
python bot.py
```

5. Abra o Telegram e envie `/start` para o bot.