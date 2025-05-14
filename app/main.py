from .core import settings
from .logging import logger
from .handlers import conversation_router

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="change_mode", description="Переключить режим"),
        BotCommand(command="delete_document", description="Удалить документ"),
        BotCommand(command="print_documents", description="Показать список документов"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    logger.info("Bot commands were set successfully.")

async def main() -> None:
    logger.info("Starting bot")
    bot = Bot(token=settings.get_bot_token())
    dp = Dispatcher()
    dp.include_router(conversation_router)

    await set_bot_commands(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

asyncio.run(main())
