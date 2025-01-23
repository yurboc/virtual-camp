import os
import json
import logging
import logging.handlers
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.formatting import Text, TextLink, as_key_value, as_list
from const.text import msg
from storage.db_schema import TgUser
from storage.db_api import Database
from utils.config import tables

logger = logging.getLogger(__name__)


class MessageSender:
    def __init__(self, token, admin_id, session_maker):
        self.admin_id = admin_id
        self.AsyncSessionLocal = session_maker
        self.bot = Bot(
            token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

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

    # Notify users about new Abonement Visit
    async def notify_abonement_visit(self) -> bool:
        logger.info("Prepare notification Abonement Visit...")
        res = False
        # Get data from DB
        async with self.AsyncSessionLocal() as session:
            db = Database(session=session)
            abonent_users_list: list[TgUser] = []
            if db and self.abonement_id and self.visit_id and self.user_id:
                # Get actor (visitor/editor/deleter)
                actor_user_id = self.user_id
                actor_user = await db.user_by_id(actor_user_id)
                if actor_user:
                    logger.info("Action performed by user %s", actor_user.id)
                else:
                    logger.warning("Action performed by bad user %s", actor_user_id)
                    return False
                # Get Abonement
                abonement_id = self.abonement_id
                abonement = await db.abonement_by_id(abonement_id)
                if abonement and not abonement.hidden:
                    logger.info("Abonement %s found", abonement.id)
                    # Get Abonement owner
                    owner = await db.user_by_id(abonement.owner_id)
                    if owner:
                        abonent_users_list.append(owner)
                        logger.info("Abonement owner %s found", owner.id)
                    else:
                        logger.warning("Abonement owner %s bad", abonement.owner_id)
                        return False
                    # Get Abonement users
                    abonement_users = await db.abonement_users(abonement_id)
                    for abonement_user in abonement_users:
                        if not abonement_user or not abonement_user.user_id:
                            continue
                        user = await db.user_by_id(abonement_user.user_id)
                        if not user:
                            continue
                        logger.info("Abonement user %s found", user.id)
                        abonent_users_list.append(user)
                else:
                    logger.warning("Abonement %s bad", abonement_id)
                    return False
                # Get Abonement Visit
                visit_id = self.visit_id
                visit = await db.abonement_visit_get(visit_id)
                if visit:
                    logger.info("Abonement Visit %s found", visit.id)
                    visit_user_id = visit.user_id
                    visit_user = await db.user_by_id(visit_user_id)
                    if visit_user:
                        logger.info("Abonement Visit user %s found", visit_user.id)
                    else:
                        logger.warning("Abonement Visit user %s bad", visit_user_id)
                        return False
                else:
                    logger.warning("Abonement Visit %s bad", visit_id)
                # Get Abonement Visit User
                visit_user_id = self.visit_user_id
                visit_user = await db.user_by_id(visit_user_id)
                if visit_user:
                    logger.info("Abonement Visit user %s", visit_user.id)
                else:
                    logger.warning("Abonement Visit bad user %s", visit_user_id)
                    return False
            else:
                logger.warning("Wrong db connection or wrong data")
                return False

            # Got Abonement users
            if not abonent_users_list:
                logger.info("No users found for Abonement")
                return False
            else:
                logger.info(f"Found {len(abonent_users_list)} user(s) for Abonement")

            # Check notification settings
            setting_name = "notify_abonement_%s" % abonement.id
            logger.info("Read settings: %s", setting_name)
            notify_users_list: list[TgUser] = []
            for user in abonent_users_list:
                if not user or not user.id or user.id == actor_user.id:
                    continue
                notifications = await db.settings_value(user.id, setting_name)
                if notifications in ["all"]:
                    notify_users_list.append(user)

            # Notifiations
            logger.info("Notify %s, type: %s", len(notify_users_list), self.msg_type)
            for user in notify_users_list:
                if not user or not user.tg_id:
                    continue
                # Create notification for each user
                try:
                    logger.info("Notify user %s (%s)", user.id, user.tg_id)
                    msg_text = ""
                    visit_user_name = None
                    tokens = []
                    left_visits = await db.abonement_visits_left(abonement)
                    actor_link = TextLink(
                        actor_user.name, url=f"tg://user?id={actor_user.tg_id}"
                    )
                    if self.msg_type == "visit_new":
                        msg_text = msg["ab_notify_visit_new"]
                    elif self.msg_type == "visit_edit":
                        msg_text = msg["ab_notify_visit_edit"]
                        visit_user_name = visit_user.name
                    elif self.msg_type == "visit_delete":
                        msg_text = msg["ab_notify_visit_delete"]
                        visit_user_name = visit_user.name
                    else:
                        msg_text = msg["unknown"]
                    # Create message by lines
                    tokens.append(Text(msg_text))
                    tokens.append(as_key_value(msg["name"], abonement.name))
                    if left_visits is not None:
                        tokens.append(as_key_value(msg["ab_left_visits"], left_visits))
                    if self.ts_new and self.ts:
                        tokens.append(Text(self.ts, " >> ", self.ts_new))
                    elif self.ts:
                        tokens.append(as_key_value(msg["ab_notify_date"], self.ts))
                    if visit_user_name:
                        tokens.append(
                            as_key_value(msg["ab_notify_visitor"], visit_user_name)
                        )
                        tokens.append(as_key_value(msg["ab_notify_actor"], actor_link))
                    else:
                        tokens.append(
                            as_key_value(msg["ab_notify_visitor"], actor_link)
                        )
                    # Store Notification to DB
                    logger.info("Store Notification for user %s", user.id)
                    await db.notification_add(
                        user, msg_text + " %s %s" % (abonement.name, user.name)
                    )
                    # Send Notification to Telegram
                    logger.info("Send notification to user %s", user.tg_id)
                    res = await self.sendText(user.tg_id, as_list(*tokens).as_html())
                except Exception:
                    logger.warning("Error sending to %s", user.tg_id, exc_info=True)

        # Close Bot session
        await self.bot.session.close()

        # Notification stored and sent
        logger.info("Done notification for Abonement Visit!")
        return res

    # Table Generator results
    def prepare_table_generator_result(self, msg: dict) -> None:
        logger.info("Prepare table generator result...")
        self.msg_text = "Получен результат генерации таблицы\n\n"
        if msg.get("task_id"):
            self.task_id = int(msg["task_id"])
            self.msg_text += f"ID: {msg['task_id']}\n"
        if msg.get("table"):
            table_name = msg["table"]
            for table in tables:
                if table["generator_name"] == table_name:
                    table_name = table["title"]
                    break
            self.msg_text += f"Таблица: {table_name}\n"
        if msg.get("result"):
            res = "Успешно" if msg["result"] == "done" else "Ошибка"
            self.msg_text += f"Результат: {res}\n"
        self.pending = "text"
        logger.info("Done table generator result!")

    # Pictures Generator results
    def prepare_pictures_generator_result(self, msg: dict) -> None:
        logger.info("Prepare pictures generator result...")
        self.msg_text = "Получен результат генерации обложки"
        if msg.get("task_id"):
            self.task_id = int(msg["task_id"])
            self.msg_text += f" (ID: {msg['task_id']})"
        if msg.get("image"):
            self.file_path = msg["image"]
            self.pending = msg.get("output_type", "")
            if not self.pending:
                self.pending = "picture"
        else:
            self.pending = ""
            logger.warning("Error: image not found in task result")
        logger.info("Done pictures generator result!")

    # Convert RabbitMQ message
    def convert_rabbitmq_message(self, body):
        logger.info("Convert RabbitMQ incoming message...")
        # Decode message
        try:
            msg = json.loads(body.decode())
        except Exception:
            logger.warning("Error decoding", exc_info=True)
            return
        # Prepare notification
        self.task_id = -1
        self.msg_text = ""
        self.file_path = ""
        self.pending = ""
        logger.info("Incoming job type: %s", msg.get("job_type"))
        if msg.get("job_type") == "table_generator":
            self.prepare_table_generator_result(msg)
        elif msg.get("job_type") == "pictures_generator":
            self.prepare_pictures_generator_result(msg)
        elif msg.get("job_type") == "abonement_visit":
            self.pending = "abonement_visit"
            self.msg_type = msg.get("msg_type")
            self.abonement_id = int(msg.get("abonement_id"))
            self.visit_id = int(msg.get("visit_id"))
            self.visit_user_id = int(msg.get("visit_user_id"))
            self.user_id = int(msg.get("user_id"))
            self.ts = msg.get("ts")
            self.ts_new = msg.get("ts_new")
        else:
            logger.warning("Unknown job type: %s", msg.get("job_type"))
            return
        logger.info("Done RabbitMQ message converting!")

    # Store notification to DB and send to Telegram
    async def create_notification(self) -> bool:
        logger.info("Checking notification data...")
        # Notify about abonement visit
        if self.pending == "abonement_visit":
            return await self.notify_abonement_visit()

        # Notify about task result
        if not self.pending or not self.task_id:
            logger.warning("Error creating notification: no pending or no task_id")
            return False

        # Prepare notification data
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
