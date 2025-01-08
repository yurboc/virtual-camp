import os
import json
import logging
import logging.handlers
from aiogram import Bot
from aiogram.types import FSInputFile
from storage.db_api import Database
from utils.config import tables

logger = logging.getLogger(__name__)


class MessageSender:
    def __init__(self, token, admin_id, session_maker):
        self.admin_id = admin_id
        self.AsyncSessionLocal = session_maker
        self.bot = Bot(token=token)

    # Send text message
    async def sendText(self, chat_id: int, text: str) -> bool:
        res = await self.bot.send_message(chat_id, text)
        return res is not None

    # Send picture
    async def sendPicture(self, chat_id: int, text: str, path: str) -> bool:
        file = FSInputFile(path)
        res = await self.bot.send_photo(chat_id, photo=file, caption=text)
        return res is not None

    # Send document
    async def sendDocument(self, chat_id: int, text: str, path: str) -> bool:
        file = FSInputFile(path)
        res = await self.bot.send_document(chat_id, document=file, caption=text)
        return res is not None

    # Table Generator results
    def prepare_table_generator_result(self, msg: dict) -> None:
        logger.info("Prepare table generator result...")
        self.msg_text = "Получен результат генерации таблицы\n\n"
        if msg.get("task_id"):
            self.task_id = int(self.msg["task_id"])
            self.msg_text += f"ID: {self.msg['task_id']}\n"
        if self.msg.get("table"):
            table_name = self.msg["table"]
            for table in tables:
                if table["generator_name"] == table_name:
                    table_name = table["title"]
                    break
            self.msg_text += f"Таблица: {table_name}\n"
        if self.msg.get("result"):
            res = "Успешно" if self.msg["result"] == "done" else "Ошибка"
            self.msg_text += f"Результат: {res}\n"
        self.pending = "text"
        logger.info("Done table generator result!")

    # Pictures Generator results
    def prepare_pictures_generator_result(self, msg: dict) -> None:
        logger.info("Prepare pictures generator result...")
        self.msg_text = "Получен результат генерации обложки"
        if msg.get("task_id"):
            self.task_id = int(self.msg["task_id"])
            self.msg_text += f" (ID: {self.msg['task_id']})"
        if self.msg.get("image"):
            self.file_path = msg["image"]
            self.pending = self.msg.get("output_type", "picture")
        else:
            self.pending = ""
            logger.warning("Error: image not found in task result")
        logger.info("Done pictures generator result!")

    # Convert RabbitMQ message
    def convert_rabbitmq_message(self, body):
        logger.info("Convert RabbitMQ incoming message...")
        # Decode message
        try:
            self.msg = json.loads(body.decode())
        except Exception:
            logger.warning("Error decoding", exc_info=True)
            return
        # Prepare notification
        self.task_id = -1
        self.msg_text = ""
        self.file_path = ""
        self.pending = ""
        logger.info("Incoming message: %s", self.msg)
        if self.msg.get("job_type") == "table_generator":
            self.prepare_table_generator_result(self.msg)
        elif self.msg.get("job_type") == "pictures_generator":
            self.prepare_pictures_generator_result(self.msg)
        else:
            logger.warning("Unknown job type: %s", self.msg.get("job_type"))
            return
        logger.info("Done RabbitMQ message converting!")

    # Store notification to DB and send to Telegram
    async def create_notification(self) -> bool:
        # Check task data
        logger.info("Checking notification data...")
        if not self.pending or not self.task_id:
            logger.warning("Error creating notification: no pending or no task_id")
            return False

        task_id = self.task_id
        if self.pending == "text":
            text = self.msg_text
        elif self.pending == "picture":
            text = self.msg_text
            file_path = self.file_path
        elif self.pending == "document":
            text = self.msg_text
            file_path = self.file_path
        else:
            logger.warning("Unknown pending type: %s", self.pending)
            return False

        # Process notification
        logger.info(f"Prepare notification for task={task_id}...")
        res = False
        async with self.AsyncSessionLocal() as session:
            db = Database(session=session)
            logger.info(f"Get creator for task={task_id} from DB")

            # Find task creator in DB
            task_creator = await db.task_user(task_id)
            chat_id = self.admin_id

            # Store notification to DB
            if task_creator and task_creator.tg_id:
                chat_id = task_creator.tg_id
                logger.info(
                    f"Store message for user {task_creator.id} in chat {chat_id}"
                )
                await db.notification_add(task_creator, text)
            else:
                logger.warning(f"Task creator for task={task_id} not found")

            # Send Telegram message
            try:
                logger.info(f"Sending message to chat {chat_id}...")
                if self.pending == "text":
                    res = await self.sendText(chat_id, text)
                elif self.pending == "picture":
                    res = await self.sendPicture(chat_id, text, file_path)
                    os.remove(file_path)
                    logger.info("Picture %s deleted", file_path)
                elif self.pending == "document":
                    res = await self.sendDocument(chat_id, text, file_path)
                    os.remove(file_path)
                    logger.info("Document %s deleted", file_path)
                else:
                    logger.warning("Unknown pending type: %s", self.pending)
            except Exception:
                logger.warning(f"Error sending to {chat_id}", exc_info=True)
            await self.bot.session.close()

        # Notification stored and sent
        logger.info("Done notification!")
        return res
