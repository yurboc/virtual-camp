import asyncio
import os
import logging
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from storage.db_schema import Base
from utils.config import config, pictures
from utils.picture_creator import PictureCreator
from utils.message_sender import MessageSender

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Setup DB
url: URL = URL.create(
    config["DB"]["TYPE"],
    username=config["DB"]["USERNAME"],
    password=config["DB"]["PASSWORD"],
    host=config["DB"]["HOST"],
    database=config["DB"]["NAME"],
)
engine = create_async_engine(url, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine)


# MAIN
async def main():
    logger.info("Starting PictureCreator")

    # Initialize DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create internal objects
    picture_creator = PictureCreator()
    messageSender = MessageSender(
        token=config["BOT"]["TOKEN"],
        admin_id=config["BOT"]["ADMIN"],
        session_maker=AsyncSessionLocal,
    )
    image = picture_creator.generate_image(
        text="Hello, World!\nОсновы физичской подготовки",
        src_img=os.path.join("static", "pictures", pictures[0]["file"]),
        font_path=os.path.join("static", "fonts", "Montserrat-SemiBold.ttf"),
    )
    logger.info("Saved image to {}".format(image))
    result = await messageSender.sendPicture(image)
    if result:
        logger.info("Image sent")
        os.remove(image)
        logger.info("Image deleted")
    else:
        logger.info("Image not sent")
    await messageSender.close()
    logger.info("Session closed")


# Entry point
if __name__ == "__main__":
    asyncio.run(main())
