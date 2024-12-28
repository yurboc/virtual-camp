import json
import logging
import logging.handlers
from aiogram import Bot
from storage.db_api import Database

logger = logging.getLogger(__name__)


class AsyncMessageSender:
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
        except:
            logger.warning("Error decoding", exc_info=True)
            return

        # Prepare text
        self.msg_text = "Получен результат генерации:\n\n"
        if self.msg.get("task_id"):
            self.task_id = int(self.msg["task_id"])
            self.msg_text += f"ID задания: {self.msg['task_id']}\n"
        if self.msg.get("uuid"):
            self.msg_text += f"UUID: {self.msg['uuid']}\n"
        if self.msg.get("table"):
            self.msg_text += f"Таблица: {self.msg['table']}\n"
        if self.msg.get("job"):
            self.msg_text += f"Задание: {self.msg['job']}\n"
        if self.msg.get("result"):
            self.msg_text += f"Результат: {self.msg['result']}\n"
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
            except:
                logger.warning(
                    f"Error sending Telegram message to {chat_id}", exc_info=True
                )
            await self.bot.session.close()

        # Notification stored and sent
        logger.info("Done notification!")
