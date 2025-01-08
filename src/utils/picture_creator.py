import json
import os
import pika
import logging
import tempfile
from PIL import Image, ImageDraw, ImageFont
from utils.config import config

logger = logging.getLogger(__name__)


# Generate text on image
class PictureCreator:
    def __init__(self):
        pass

    # Save image with selected quality
    def save_image_with_quality(self, image: Image.Image, quality: int) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_path = temp_file.name
            image.save(temp_path, format="JPEG", quality=quality, optimize=True)
        return temp_path

    # Save image with selected maximum size
    def save_image_with_max_size(self, image: Image.Image, max_size: int) -> str:
        low, high = 10, 95  # Quality range
        best_quality = high
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_path = temp_file.name
            while low <= high:
                quality = (low + high) // 2
                image.save(temp_path, format="JPEG", quality=quality, optimize=True)
                file_size = os.path.getsize(temp_path)
                if file_size <= max_size:
                    best_quality = quality
                    low = quality + 1
                else:
                    high = quality - 1
            # Save image with optimal quality
            image.save(temp_path, format="JPEG", quality=best_quality, optimize=True)
        return temp_path

    # Generate image with text
    def generate_image(
        self, img_params: dict, lines: list[str], src_img: str, font_path: str
    ) -> str:
        # Set image parameters
        width = img_params["width"]
        height = img_params["height"]
        max_width = int(width * 2 / 3)
        line_spacing = 15

        # Prepare background
        background = Image.open(src_img).resize((width, height))
        draw = ImageDraw.Draw(background)

        # Prepare text
        lines_cnt = len(lines)
        font_size_line = [10, 10]
        font_line = [ImageFont.truetype(font_path), ImageFont.truetype(font_path)]

        # Select font size
        for id in range(min(2, lines_cnt)):
            for _ in range(120):
                font_line[id] = ImageFont.truetype(font_path, font_size_line[id])
                if draw.textlength(lines[id], font=font_line[id]) < max_width:
                    font_size_line[id] += 1
                else:
                    font_size_line[id] -= 1
                    font_line[id] = ImageFont.truetype(font_path, font_size_line[id])
                    break

        # First line: draw text
        caption_height = draw.textbbox((0, 0), lines[0], font=font_line[0])[3] + (
            (line_spacing + draw.textbbox((0, 0), lines[1], font=font_line[1])[3])
            if lines_cnt == 2
            else 0
        )
        frame_heigth = img_params["frame-bottom-y"] - img_params["frame-top-y"]
        if frame_heigth > caption_height:
            y_offset = img_params["frame-top-y"] + (frame_heigth - caption_height) // 3
        else:
            y_offset = img_params["frame-top-y"]
        x_offset_line0 = (width - draw.textlength(lines[0], font=font_line[0])) // 2
        draw.text((x_offset_line0, y_offset), lines[0], font=font_line[0], fill="white")

        # Second line: draw text
        if lines_cnt == 2:
            caption_height_line0 = draw.textbbox((0, 0), lines[0], font=font_line[0])[3]
            y_offset_line1 = y_offset + caption_height_line0 + line_spacing
            x_offset_line1 = (width - draw.textlength(lines[1], font=font_line[1])) // 2
            draw.text(
                (x_offset_line1, y_offset_line1),
                lines[1],
                font=font_line[1],
                fill="white",
            )

        # Save image to temporary file
        temp_path = self.save_image_with_quality(background, 95)
        return temp_path

    # Publish results to RabbitMQ
    def publish_result(self, msg: dict) -> None:
        logger.info("Publishing result...")
        message_json = json.dumps(msg)
        connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
        channel = connection.channel()
        channel.queue_declare(queue=config["RABBITMQ"]["QUEUES"]["RESULTS"])
        channel.basic_publish(
            exchange="",
            routing_key=config["RABBITMQ"]["QUEUES"]["RESULTS"],
            body=message_json,
        )
        connection.close()
        logger.info("Done publishing result!")

    # Handle new task from RabbitMQ
    def handle_new_task(self, msg: dict) -> None:
        logger.info("Generate picture...")
        logger.info("Source: {}".format(msg))
        try:
            # Generate picture
            generated_image_path = self.generate_image(
                img_params=msg["picture"],
                lines=msg["lines"],
                src_img=os.path.join("static", "pictures", msg["picture"]["file"]),
                font_path=os.path.join("static", "fonts", msg["picture"]["font"]),
            )
            logger.info("Saved image to {}".format(generated_image_path))
            # Publish result
            msg["uuid"] = msg.get("uuid", "no_uuid")
            msg["image"] = generated_image_path
            msg["result"] = "done"
            self.publish_result(msg)
            logger.info("Result: {}".format(msg))
            logger.info("Done image generating!")
        except Exception as e:
            logger.error(e, exc_info=True)
