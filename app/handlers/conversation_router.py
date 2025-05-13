from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from ..rag import document_handler, text_handler, question_handler

class Modes(StatesGroup):
    start_state = State()
    waiting_for_document = State()
    waiting_for_question = State()

conversation_router = Router()

@conversation_router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    await state.set_state(Modes.waiting_for_document)
    await message.answer("Лабораторная работа №6. Диалоговая система с поддержкой естественного языка.To view help, call the /help command")


@conversation_router.message(Command("help"))
async def help_step1_command(message: Message, state: FSMContext):
    await state.set_state(Modes.waiting_for_document)
    await message.answer("This is a dialog system that answers cooking questions based on sent documents. You are currently in document sending mode. Both documents and text messages will be treated as context. To switch to question mode, call the /change_mode command.")

@conversation_router.message(Command("change_mode"))
async def change_mode_command(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == Modes.waiting_for_document.state:
        await state.set_state(Modes.waiting_for_question)
        await message.answer("Document loading mode is disabled. Now you can ask questions.")
    else:
        await state.set_state(Modes.waiting_for_document)
        await message.answer("Document upload mode is enabled. Please submit your document.")

@conversation_router.message()
async def main_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == Modes.waiting_for_document.state:
        if message.document:
            await document_handler(message, state)
        elif message.text:
            await text_handler(message, state)
        else: 
            await message.answer("Send a document or text message.")
    elif current_state == Modes.waiting_for_question.state:
        if message.text:
            await question_handler(message, state)
        else:
            await message.answer("Send a question.")
    else:
        await state.set_state(Modes.waiting_for_document)
        message.answer("Sorry, your state is not defined, I am transferring you to the state of waiting for context.") 