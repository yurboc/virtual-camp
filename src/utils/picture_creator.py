import os
import logging
import tempfile
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


# Generate text on image
class PictureCreator:
    def __init__(self):
        pass

    def generate_image(self, text: str, src_img: str, font_path: str) -> str:
        # Set image parameters
        width, height = 1920, 1080
        max_width = int(width * 2 / 3)
        line_spacing = 15

        # Prepare background
        background = Image.open(src_img).resize((width, height))
        draw = ImageDraw.Draw(background)

        # Prepare text
        lines = text.split("\n")
        font_size_line1 = 10
        font_size_line2 = 10

        # First line: select font size
        for _ in range(300):
            font_line1 = ImageFont.truetype(font_path, font_size_line1)
            if draw.textlength(lines[0], font=font_line1) < max_width:
                font_size_line1 += 1
            else:
                font_size_line1 -= 1
                font_line1 = ImageFont.truetype(font_path, font_size_line1)
                break

        # Second line: select font size
        for _ in range(300):
            font_line2 = ImageFont.truetype(font_path, font_size_line2)
            if draw.textlength(lines[1], font=font_line2) < draw.textlength(
                lines[0], font=font_line1
            ):
                font_size_line2 += 1
            else:
                font_size_line2 -= 1
                font_line2 = ImageFont.truetype(font_path, font_size_line2)
                break

        # Draw text
        y_offset = 940 - (
            draw.textbbox((0, 0), lines[0], font=font_line1)[3]
            + draw.textbbox((0, 0), lines[1], font=font_line2)[3]
            + line_spacing
        )

        # First line: draw text
        x_text_line1 = (width - draw.textlength(lines[0], font=font_line1)) // 2
        draw.text((x_text_line1, y_offset), lines[0], font=font_line1, fill="white")

        # Second line: draw text
        y_text_line2 = (
            y_offset
            + draw.textbbox((0, 0), lines[0], font=font_line1)[3]
            + line_spacing
        )
        x_text_line2 = (width - draw.textlength(lines[1], font=font_line2)) // 2
        draw.text((x_text_line2, y_text_line2), lines[1], font=font_line2, fill="white")

        # Save image to temporary file
        temp_path = self.save_image_with_max_size(background, max_size=2 * 1024 * 1024)

        return temp_path

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
