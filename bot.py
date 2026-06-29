import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)
import database

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

database.initialize_db()

(
    WAITING_CATEGORY_NAME,
    WAITING_EXPENSE_AMOUNT,
    WAITING_EXPENSE_DESC,
    WAITING_EXPENSE_DATE,
    WAITING_EXPENSE_CATEGORY,
    WAITING_EXPENSE_RECURRING
) = range(6)


def parse_date_input(date_text):
    return datetime.strptime(date_text, '%d-%m-%Y').strftime('%Y-%m-%d')


def format_date_for_display(db_date):
    return datetime.strptime(db_date, '%Y-%m-%d').strftime('%d-%m-%Y')


# MAIN MENU / UI 

def get_main_menu_keyboard():
    """Return the main menu keyboard markup."""
    keyboard = [
        [InlineKeyboardButton("💸 Adicionar Gasto", callback_data='menu_add_expense')],
        [InlineKeyboardButton("📁 Adicionar Categoria", callback_data='menu_add_category')],
        [InlineKeyboardButton("📊 Saldo do Mês", callback_data='menu_monthly_total'),
         InlineKeyboardButton("📈 Saldo por Categoria", callback_data='menu_category_total')],
        [InlineKeyboardButton("🔄 Gastos Recorrentes", callback_data='menu_view_recurring'),
         InlineKeyboardButton("📑 Ver Categorias", callback_data='menu_view_categories')],
        [InlineKeyboardButton("🗑️ Apagar Gasto", callback_data='menu_delete_expense')],
        [InlineKeyboardButton("🧹 Zerar Banco", callback_data='menu_reset_database')]

    ]
    return InlineKeyboardMarkup(keyboard)


# BOT ENTRYPOINTS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostre ou atualize o menu principal para o usuário."""
    text = "💰 **Gabe's Piggy Bank**\n\nEscolha uma opção no menu abaixo:"
    reply_markup = get_main_menu_keyboard()
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return ConversationHandler.END


# CATEGORY HANDLERS

async def start_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📁 Digite o nome da nova categoria (ex: Alimentação, Lazer):")
    return WAITING_CATEGORY_NAME


async def save_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    category_name = update.message.text.strip()
    edit_category_id = context.user_data.pop('edit_category_id', None)

    if edit_category_id is not None:
        updated = database.update_category(user_id, edit_category_id, category_name)
        if updated:
            await update.message.reply_text(f"✅ Categoria atualizada para '{category_name}' com sucesso!")
        else:
            await update.message.reply_text("❌ Não foi possível atualizar a categoria. Tente novamente.")
    else:
        database.add_category(user_id, category_name)
        await update.message.reply_text(f"✅ Categoria '{category_name}' criada com sucesso!")

    await update.message.reply_text("Menu Principal:", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END

async def edit_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split('_')[1])
    await query.edit_message_text("📁 Digite o novo nome para a categoria:")
    context.user_data['edit_category_id'] = category_id
    return WAITING_CATEGORY_NAME


# EXPENSE HANDLERS

async def start_add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not database.list_categories(user_id):
        await query.edit_message_text(
            "⚠️ Você precisa cadastrar ao menos uma categoria antes de adicionar um gasto!",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END

    await query.edit_message_text("💸 Digite o valor do gasto (Use pontos ou vírgulas, ex: 45.50):")
    return WAITING_EXPENSE_AMOUNT


async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace(',', '.').strip()
    try:
        amount = float(text)
        context.user_data['expense_amount'] = amount
        await update.message.reply_text("📝 Digite uma breve descrição para o gasto:")
        return WAITING_EXPENSE_DESC
    except ValueError:
        await update.message.reply_text("❌ Valor inválido. Por favor, envie apenas números com ponto ou vírgula (ex: 150.75):")
        return WAITING_EXPENSE_AMOUNT


async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['expense_desc'] = update.message.text.strip()

    keyboard = [
        [InlineKeyboardButton("📅 Hoje", callback_data='date_today')],
        [InlineKeyboardButton("⌨️ Outra data (Digitar)", callback_data='date_type')]
    ]
    await update.message.reply_text("📅 Quando ocorreu esse gasto?", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_EXPENSE_DATE


async def receive_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'date_today':
        context.user_data['expense_date'] = datetime.now().strftime('%Y-%m-%d')
        return await show_category_selection(query, context, via_callback=True)
    else:
        await query.edit_message_text("Digite a data no formato DD-MM-AAAA (ex: 14-06-2026):")
        return WAITING_EXPENSE_DATE


async def receive_date_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_text = update.message.text.strip()
    try:
        context.user_data['expense_date'] = parse_date_input(date_text)
        return await show_category_selection(update, context, via_callback=False)
    except ValueError:
        await update.message.reply_text("❌ Formato incorreto. Envie a data exatamente como DD-MM-AAAA:")
        return WAITING_EXPENSE_DATE


async def show_category_selection(target, context, via_callback=True):
    """Generate the buttons list with the user's categories."""
    user_id = target.from_user.id if via_callback else target.message.from_user.id
    categories = database.list_categories(user_id)

    keyboard = [[InlineKeyboardButton(cat[1], callback_data=f"gcat_{cat[0]}")] for cat in categories]
    markup = InlineKeyboardMarkup(keyboard)

    text = "📁 Selecione a categoria para este gasto:"
    if via_callback:
        await target.edit_message_text(text, reply_markup=markup)
    else:
        await target.message.reply_text(text, reply_markup=markup)
    return WAITING_EXPENSE_CATEGORY


async def receive_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    category_id = int(query.data.split('_')[1])
    context.user_data['expense_category_id'] = category_id

    keyboard = [
        [InlineKeyboardButton("Sim", callback_data='rec_1'),
         InlineKeyboardButton("Não", callback_data='rec_0')]
    ]
    await query.edit_message_text("🔄 É um gasto fixo/recorrente mensal?", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_EXPENSE_RECURRING


async def receive_recurring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    recurring = int(query.data.split('_')[1])
    user_id = query.from_user.id

    database.add_expense(
        user_id=user_id,
        amount=context.user_data['expense_amount'],
        description=context.user_data['expense_desc'],
        date=context.user_data['expense_date'],
        category_id=context.user_data['expense_category_id'],
        recurring=recurring
    )

    await query.edit_message_text("✅ Gasto registrado com sucesso!")
    await query.message.reply_text("Menu Principal:", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


# MENU CALLBACK HANDLER

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    choice = query.data
    
    back_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data='back_menu')]])

    if choice == 'menu_monthly_total':
        total = database.get_monthly_total(user_id)
        expenses = database.list_monthly_expenses(user_id)
        if not expenses:
            text = (
                f"📊 **Total gasto no mês atual:**\n\n➡️ R$ {total:.2f}\n\n"
                "Nenhum gasto registrado neste mês."
            )
        else:
            text = (
                f"📊 **Total gasto no mês atual:**\n\n➡️ R$ {total:.2f}\n\n"
                "🧾 **Gastos do mês:**\n"
            )
            for amount, desc, date, category in expenses:
                formatted_date = format_date_for_display(date) if '-' in date else date
                description = desc if desc else 'Sem descrição'
                category_text = category if category else 'Sem categoria'
                text += f"• {formatted_date} — {description} ({category_text}) — R$ {amount:.2f}\n"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=back_markup)
        
    elif choice == 'menu_category_total':
        totals = database.get_total_by_category(user_id)
        if not totals:
            text = "📈 Não foram encontrados gastos neste mês."
        else:
            text = "📈 **Resumo de Gastos por Categoria (Mês Atual):**\n\n"
            for category, total in totals:
                text += f"• *{category}*: R$ {total:.2f}\n"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=back_markup)
        
    elif choice == 'menu_reset_database':
        keyboard = [
            [InlineKeyboardButton("Sim", callback_data='reset_yes')],
            [InlineKeyboardButton("Não", callback_data='back_menu')]
        ]
        await query.edit_message_text(
            "⚠️ Tem certeza que deseja zerar o banco de dados? Essa ação não pode ser desfeita.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif choice == 'reset_yes':
        database.reset_database()
        await query.edit_message_text("✅ Banco de dados zerado com sucesso!", reply_markup=back_markup)

    elif choice == 'menu_view_recurring':
        recurring = database.list_recurring_expenses(user_id)
        if not recurring:
            await query.edit_message_text("🔄 Você não possui gastos recorrentes cadastrados.", parse_mode='Markdown', reply_markup=back_markup)
        else:
            text = "🔄 **Seus Gastos Recorrentes:**\n\n"
            keyboard = []
            for expense_id, amount, desc, date, category in recurring:
                formatted_date = format_date_for_display(date) if '-' in date else date
                text += f"• *{desc}* ({category}) — R$ {amount:.2f} [Todo dia {formatted_date}]\n"
                keyboard.append([InlineKeyboardButton(f"🗑️ Apagar {formatted_date} - {desc}", callback_data=f"delrec_{expense_id}")])
            keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data='back_menu')])
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif choice == 'menu_view_categories':
        categories = database.list_categories(user_id)
        if not categories:
            await query.edit_message_text("📑 Nenhuma categoria criada ainda.", parse_mode='Markdown', reply_markup=back_markup)
            return

        text = "📑 **Categorias Disponíveis:**\n\nSelecione uma categoria para editar:"
        keyboard = []
        for category_id, name in categories:
            keyboard.append([InlineKeyboardButton(name, callback_data=f'editcat_{category_id}')])
        keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data='back_menu')])
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif choice.startswith('editcat_'):
        await edit_category(update, context)

    elif choice == 'menu_delete_expense':
        expenses = database.list_recent_expenses(user_id, limit=5)
        if not expenses:
            await query.edit_message_text("❌ Não há nenhum gasto computado para apagar.", reply_markup=back_markup)
        else:
            keyboard = []
            for expense_id, amount, desc, date in expenses:
                formatted_date = format_date_for_display(date) if '-' in date else date
                keyboard.append([InlineKeyboardButton(f"🗑️ {formatted_date} - {desc} (R$ {amount:.2f})", callback_data=f"del_{expense_id}")])
            keyboard.append([InlineKeyboardButton("🔙 Cancelar", callback_data='back_menu')])
            await query.edit_message_text("❌ Selecione um dos últimos 5 gastos para apagar definitivamente:", reply_markup=InlineKeyboardMarkup(keyboard))
            
    elif choice.startswith('del_'):
        expense_id = int(choice.split('_')[1])
        if database.delete_expense(user_id, expense_id):
            await query.edit_message_text("✅ Gasto excluído com sucesso do banco de dados!", reply_markup=back_markup)
        else:
            await query.edit_message_text("❌ Ocorreu um erro ao tentar apagar o gasto.", reply_markup=back_markup)
            
    elif choice.startswith('delrec_'):
        expense_id = int(choice.split('_')[1])
        if database.delete_expense(user_id, expense_id):
            await query.edit_message_text("✅ Gasto recorrente excluído com sucesso!", reply_markup=back_markup)
        else:
            await query.edit_message_text("❌ Ocorreu um erro ao tentar apagar o gasto recorrente.", reply_markup=back_markup)

    elif choice == 'back_menu':
        await start(update, context)


# FALLBACK / UTILITY HANDLERS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow interrupting a flow by typing /cancel."""
    await update.message.reply_text("❌ Processo cancelado.")
    await start(update, context)
    return ConversationHandler.END


if __name__ == '__main__':
    if not TOKEN:
        print("FALHA: Defina a variável TELEGRAM_TOKEN no arquivo .env!")
        exit(1)
        
    app = ApplicationBuilder().token(TOKEN).build()

    conv_category = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_add_category, pattern='^menu_add_category$'),
            CallbackQueryHandler(edit_category, pattern='^editcat_')
        ],
        states={
            WAITING_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_category)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    conv_expense = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_expense, pattern='^menu_add_expense$')],
        states={
            WAITING_EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)],
            WAITING_EXPENSE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            WAITING_EXPENSE_DATE: [
                CallbackQueryHandler(receive_date_callback, pattern='^date_'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date_text)
            ],
            WAITING_EXPENSE_CATEGORY: [CallbackQueryHandler(receive_category, pattern='^gcat_')],
            WAITING_EXPENSE_RECURRING: [CallbackQueryHandler(receive_recurring, pattern='^rec_')]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_category)
    app.add_handler(conv_expense)
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    print("🚀 O Bot Financeiro está online e operando!")
    app.run_polling()