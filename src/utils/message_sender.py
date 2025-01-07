import json
import logging
import logging.handlers
from aiogram import Bot
from storage.db_api import Database
from utils.config import tables

logger = logging.getLogger(__name__)


class MessageSender:
    def __init__(self, token, admin_id, session_maker):
        self.admin_id = admin_id
        self.AsyncSessionLocal = session_maker
        self.bot = Bot(token=token)

    # Convert RabbitMQ message
    def convert_rabbitmq_message(self, body):
        logger.info("Convert RabbitMQ incoming message...")
        self.task_id = None
        self.msg_text = None
        try:
            # Decode message
            self.msg = json.loads(body.decode())
        except Exception:
            logger.warning("Error decoding", exc_info=True)
            return

        # Prepare text
        self.msg_text = "Получен результат генерации таблицы\n\n"
        if self.msg.get("task_id"):
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
        logger.info("Done RabbitMQ message converting!")

    # Store notification to DB and send to Telegram
    async def create_notification(self):
        # Check task data
        logger.info("Checking notification data...")
        if not self.task_id or not self.msg_text:
            logger.warning("Error creating notification: task_id or text not found")
            return
        task_id = self.task_id
        text = self.msg_text

        # Process notification
        logger.info(f"Prepare notification for task={task_id}...")
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
                await self.bot.send_message(chat_id=chat_id, text=text)
            except Exception:
                logger.warning(
                    f"Error sending Telegram message to {chat_id}", exc_info=True
                )
            await self.bot.session.close()

        # Notification stored and sent
        logger.info("Done notification!")
