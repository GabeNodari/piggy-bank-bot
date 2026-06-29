# Piggy Bank Bot 💰
A Telegram finance bot that helps track expenses, manage categories, and view monthly balances.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)

## Features

- Main menu with inline keyboard options.
- Add custom expense categories.
- Edit existing categories from the category view.
- Add expenses with amount, description, date, category, and recurring flag.
- View the current month's total spending.
- View category totals for the current month.
- View recurring expenses.
- Delete recent expenses.
- Reset the database.

## Requirements

- Any platform with Python support.
- Python 3.8+ recommended.
- `python-telegram-bot` and dependencies from `requirements.txt`.
- A Telegram bot created through BotFather.
- `.env` file containing the `TELEGRAM_TOKEN` variable.

## Project Structure

- `bot.py`: main bot logic and conversation flows.
- `database.py`: SQLite database creation and data access.
- `financas.db`: SQLite database file generated automatically.
- `requirements.txt`: Python dependencies.

## Database Schema

### Table `categories`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id` INTEGER NOT NULL
- `name` TEXT NOT NULL

### Table `expenses`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id` INTEGER NOT NULL
- `amount` REAL NOT NULL
- `description` TEXT
- `date` TEXT NOT NULL
- `category_id` INTEGER
- `recurring` INTEGER NOT NULL CHECK (recurring IN (0, 1))
- `category_id` references `categories(id)`

## User Flow and Microcopy

1. Start the bot with `/start`.
2. The bot shows the main menu:
   - `💰 **Gabe's Piggy Bank**\n\nEscolha uma opção no menu abaixo:`
3. Adding a category:
   - `📁 Digite o nome da nova categoria (ex: Alimentação, Lazer):`
   - Success message: `✅ Categoria 'Name' criada com sucesso!`
4. Editing a category:
   - `📁 Digite o novo nome para a categoria:`
   - Success message: `✅ Categoria atualizada para 'Name' com sucesso!`
5. Adding an expense:
   - `💸 Digite o valor do gasto (Use pontos ou vírgulas, ex: 45.50):`
   - Invalid value message: `❌ Valor inválido. Por favor, envie apenas números com ponto ou vírgula (ex: 150.75):`
   - `📝 Digite uma breve descrição para o gasto:`
   - `📅 Quando ocorreu esse gasto?`
   - Buttons: `📅 Hoje` and `⌨️ Outra data (Digitar)`
   - `📁 Selecione a categoria para este gasto:`
   - `🔄 É um gasto fixo/recorrente mensal?`
   - Final confirmation: `✅ Gasto registrado com sucesso!`
6. Viewing categories:
   - `📑 **Categorias Disponíveis:**\n\nSelecione uma categoria para editar:`
   - Category buttons and `🔙 Voltar ao Menu`
7. Common flow messages:
   - `Menu Principal:` returns to the main menu with buttons.
   - `❌ Processo cancelado.` for cancellation.

## How to Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Telegram token:

```env
TELEGRAM_TOKEN=your_token_here
```

3. Run the bot:

```bash
python bot.py
```

4. Open Telegram and send `/start` to the bot.
