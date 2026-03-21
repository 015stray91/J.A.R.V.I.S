"""
Image and boot animation creator for Jarvis X
Creates simple design assets and Android bootanimation.zip packages
"""

from pathlib import Path
from typing import Dict
from zipfile import ZipFile, ZIP_STORED
from PIL import Image, ImageDraw, ImageFont, ImageSequence


class ImageCreatorManager:
    """Creates local design images and boot animations"""

    def create_design_image(self, text: str, output_path: str, width: int = 1920, height: int = 1080) -> Dict[str, object]:
        if not output_path:
            return {
                "success": False,
                "message": "No output path provided"
            }

        output = Path(output_path).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)

        try:
            image = Image.new("RGB", (width, height), color=(16, 20, 28))
            draw = ImageDraw.Draw(image)

            for y in range(height):
                ratio = y / max(height - 1, 1)
                r = int(16 + 40 * ratio)
                g = int(20 + 24 * ratio)
                b = int(28 + 70 * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            try:
                font = ImageFont.truetype("arial.ttf", 64)
            except Exception:
                font = ImageFont.load_default()

            title = text.strip() if text else "Jarvis Image"
            bbox = draw.textbbox((0, 0), title, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]

            x = (width - tw) // 2
            y = (height - th) // 2

            draw.text((x + 3, y + 3), title, fill=(0, 0, 0), font=font)
            draw.text((x, y), title, fill=(245, 247, 255), font=font)

            image.save(output)
            return {
                "success": True,
                "path": str(output),
                "message": "Design image created"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to create image: {e}"
            }

    def create_boot_animation(self, source_gif: str, output_zip: str, width: int = 1080, height: int = 2400, fps: int = 30) -> Dict[str, object]:
        src = Path(source_gif).expanduser()
        out = Path(output_zip).expanduser()

        if not src.exists() or not src.is_file():
            return {
                "success": False,
                "message": f"Source animation not found: {src}"
            }

        out.parent.mkdir(parents=True, exist_ok=True)

        work_dir = out.parent / (out.stem + "_frames")
        part0 = work_dir / "part0"
        part0.mkdir(parents=True, exist_ok=True)

        try:
            im = Image.open(src)
            frame_count = 0
            for idx, frame in enumerate(ImageSequence.Iterator(im)):
                frame_rgb = frame.convert("RGB").resize((width, height), Image.LANCZOS)
                frame_path = part0 / f"{idx:05d}.png"
                frame_rgb.save(frame_path, format="PNG")
                frame_count += 1

            desc = f"{width} {height} {fps}\np 1 0 part0\n"
            (work_dir / "desc.txt").write_text(desc, encoding="utf-8")

            with ZipFile(out, "w", compression=ZIP_STORED) as zf:
                zf.write(work_dir / "desc.txt", arcname="desc.txt")
                for frame_path in sorted(part0.glob("*.png")):
                    zf.write(frame_path, arcname=f"part0/{frame_path.name}")

            return {
                "success": True,
                "path": str(out),
                "frames": frame_count,
                "message": "bootanimation.zip created"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to create boot animation: {e}"
            }

