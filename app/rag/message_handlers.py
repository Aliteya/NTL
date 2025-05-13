import io
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from docx import Document

from ..logging import logger 
from .llm_pipeline import get_answer

async def document_handler(message: Message, state: FSMContext):
    logger.info(f"Received document message from user {message.from_user.id}")

    data = await state.get_data()
    documents = data.get("documents", [])
    logger.info(f"Current documents in state: {len(documents)}")

    filename = message.document.file_name.lower()
    logger.info(f"Processing file: {filename}")

    if not filename.endswith(".docx"):
        logger.warning(f"Unsupported file format received: {filename}")
        await message.answer("Only DOCX format is supported. Please send a file with the .docx extension.")
        return

    try:
        file_id = message.document.file_id
        file = await message.bot.get_file(file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        file_buffer = io.BytesIO(file_bytes.read())
        file_buffer.seek(0)
        logger.info(f"Downloaded file {filename} ({len(file_bytes.getvalue())} bytes)")
    except Exception as e:
        logger.error(f"Failed to download file {filename}: {e}")
        await message.answer("Failed to download the file. Please try again.")
        return

    try:
        doc = Document(file_buffer)
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        logger.info(f"Extracted text length from {filename}: {len(text)} characters")
    except Exception as e:
        logger.error(f"Error processing DOCX file {filename}: {e}")
        await message.answer("Failed to process the DOCX file. Please ensure it is a valid document.")
        return

    if not text:
        logger.warning(f"DOCX file {filename} is empty or contains no text")
        await message.answer("DOCX file is empty or does not contain text.")
        return

    documents.append({
        "text": text,
        "metadata": {
            "file_name": filename
        }
    })
    logger.info(f"Appended document from {filename}. Total documents now: {len(documents)}")

    await state.update_data(documents=documents)
    await message.answer("Text from DOCX has been successfully extracted and saved to the context.")


async def text_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    documents = data.get("documents", [])

    documents.append({
        "text": message.text,
        "metadata": {
            "source": "user_text"
        }
    })

    await state.update_data(documents=documents)
    await message.answer("Your text has been added to the context.")


async def question_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    result = await get_answer(data.get("documents", []), message)
    answer_text = result.get('result', 'No answer found.')
    sources = result.get('source_documents', [])
    sources_text = "\n".join([f"- {doc.metadata.get('file_name', 'unknown')}" for doc in sources])

    response_message = f"{answer_text}\n\nSources:\n{sources_text}"

    await message.answer(response_message)