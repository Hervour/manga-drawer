import json
import math
import re
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont, ImageOps

import folder_paths

CATEGORY = "Manga Drawer"


def _safe_name(value: str, fallback: str = "item") -> str:
    value = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "_", str(value or "")).strip("_")
    return value or fallback


def _resolve_path(base: Path, value: str) -> Path:
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def _font(size: int):
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def _tensor_to_pil(image):
    if isinstance(image, (list, tuple)):
        image = image[0]
    if image.ndim == 4:
        image = image[0]
    array = (image.detach().cpu().numpy().clip(0.0, 1.0) * 255.0).astype(np.uint8)
    return Image.fromarray(array, mode="RGB" if array.shape[-1] == 3 else "RGBA").convert("RGB")


def _pil_to_tensor(image: Image.Image):
    array = np.asarray(image.convert("RGB")).astype(np.float32) / 255.0
    return torch.from_numpy(array)[None, ...]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int):
    text = str(text).strip()
    if not text:
        return []
    lines = []
    current = ""
    for char in text:
        candidate = current + char
        if current and draw.textlength(candidate, font=font) > max_width:
            lines.append(current.rstrip())
            current = char.lstrip()
        else:
            current = candidate
    if current:
        lines.append(current.rstrip())
    return lines


def _draw_dialogues(image: Image.Image, dialogue_json: str) -> Image.Image:
    try:
        dialogues = json.loads(dialogue_json) if dialogue_json else []
    except Exception:
        dialogues = [str(dialogue_json)] if dialogue_json else []
    if isinstance(dialogues, str):
        dialogues = [dialogues]
    if not dialogues:
        return image

    image = image.convert("RGB").copy()
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = image.size
    font = _font(max(14, int(min(w, h) * 0.036)))
    padding = max(8, int(min(w, h) * 0.018))
    line_gap = max(3, padding // 3)
    max_width = int(w * 0.58)
    y = padding + 4

    for index, entry in enumerate(dialogues):
        if isinstance(entry, dict):
            text = entry.get("text", "")
            position = entry.get("position", "left")
        else:
            text = entry
            position = "left" if index % 2 == 0 else "right"
        lines = _wrap_text(draw, text, font, max_width - 2 * padding)
        if not lines:
            continue
        line_height = draw.textbbox((0, 0), "Ag", font=font)[3]
        box_w = min(max_width, max(draw.textlength(line, font=font) for line in lines) + 2 * padding)
        box_h = len(lines) * line_height + (len(lines) - 1) * line_gap + 2 * padding
        x = padding + 4 if position == "left" else w - box_w - padding - 4
        if y + box_h > h - padding:
            break
        draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=max(8, padding // 2), fill=(255, 255, 255, 238), outline=(20, 20, 20, 255), width=max(2, padding // 6))
        text_y = y + padding
        for line in lines:
            draw.text((x + padding, text_y), line, font=font, fill=(15, 15, 15, 255))
            text_y += line_height + line_gap
        y += box_h + padding

    return image


class MangaStoryboardLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "storyboard_path": ("STRING", {"default": "", "multiline": False}),
                "output_dir": ("STRING", {"default": "manga_drawer", "multiline": False}),
                "default_width": ("INT", {"default": 768, "min": 256, "max": 4096, "step": 32}),
                "default_height": ("INT", {"default": 768, "min": 256, "max": 4096, "step": 32}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "INT", "STRING", "STRING", "STRING", "INT", "INT", "STRING")
    RETURN_NAMES = ("prompt", "negative_prompt", "seed", "resolution", "frame_image", "character_image", "panel_id", "panel_index", "total_panels", "dialogue_json")
    OUTPUT_IS_LIST = (True,) * 10
    FUNCTION = "load"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, storyboard_path, output_dir, default_width, default_height):
        path = Path(storyboard_path).expanduser().resolve()
        return path.stat().st_mtime_ns if path.exists() else float("NaN")

    def load(self, storyboard_path, output_dir, default_width, default_height):
        path = Path(storyboard_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Storyboard not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        panel_count = len(data.get("panels", []))
        if panel_count == 0:
            raise ValueError("Storyboard contains no panels")

        project = _safe_name(data.get("project") or path.parent.name, "manga")
        base_dir = path.parent
        input_root = Path(folder_paths.get_input_directory()) / "manga_drawer" / project
        frames_dir = input_root / "frames"
        refs_dir = input_root / "refs"
        frames_dir.mkdir(parents=True, exist_ok=True)
        refs_dir.mkdir(parents=True, exist_ok=True)

        defaults = data.get("defaults", {})
        style = str(data.get("style", "")).strip()
        continuity = str(data.get("continuity", "")).strip()
        character = str(data.get("character", "")).strip()
        global_negative = str(data.get("negative_prompt", "")).strip()
        base_seed = int(data.get("base_seed", 100000))

        character_src = data.get("character_sheet")
        character_path = refs_dir / "character_sheet.png"
        if character_src:
            source = _resolve_path(base_dir, character_src)
            if source.exists():
                Image.open(source).convert("RGB").save(character_path, "PNG")
        if not character_path.exists():
            placeholder = Image.new("RGB", (768, 768), (235, 235, 232))
            draw = ImageDraw.Draw(placeholder)
            draw.rectangle((4, 4, 763, 763), outline=(40, 40, 40), width=8)
            draw.ellipse((270, 105, 498, 333), fill=(120, 125, 135), outline=(35, 35, 35), width=7)
            draw.rounded_rectangle((210, 350, 558, 700), radius=70, fill=(85, 105, 145), outline=(35, 35, 35), width=7)
            draw.text((26, 26), "CHARACTER REFERENCE PLACEHOLDER", font=_font(26), fill=(20, 20, 20))
            placeholder.save(character_path, "PNG")

        prompts, negatives, seeds, resolutions = [], [], [], []
        frame_files, character_files, panel_ids = [], [], []
        indices, totals, dialogues = [], [], []
        character_rel = character_path.relative_to(Path(folder_paths.get_input_directory())).as_posix()

        for index, panel in enumerate(data.get("panels", [])):
            panel_id = _safe_name(panel.get("id"), f"p{index + 1:02d}")
            width = int(panel.get("width", defaults.get("width", default_width)))
            height = int(panel.get("height", defaults.get("height", default_height)))
            width = max(256, int(math.ceil(width / 32.0) * 32))
            height = max(256, int(math.ceil(height / 32.0) * 32))

            frame_src = panel.get("frame") or panel.get("image")
            frame_path = frames_dir / f"{index + 1:03d}_{panel_id}.png"
            loaded = False
            if frame_src:
                source = _resolve_path(base_dir, frame_src)
                if source.exists():
                    Image.open(source).convert("RGB").save(frame_path, "PNG")
                    loaded = True
            if not loaded:
                frame = Image.new("RGB", (width, height), (245, 245, 242))
                draw = ImageDraw.Draw(frame, "RGBA")
                draw.rectangle((4, 4, width - 5, height - 5), outline=(25, 25, 25), width=7)
                for step in (1, 2):
                    x = int(width * step / 3)
                    y = int(height * step / 3)
                    draw.line((x, 8, x, height - 9), fill=(180, 180, 180, 80), width=2)
                    draw.line((8, y, width - 9, y), fill=(180, 180, 180, 80), width=2)
                draw.text((22, 20), panel_id, font=_font(28), fill=(70, 70, 70))
                frame.save(frame_path, "PNG")

            full_prompt = "\n".join(part for part in (style, continuity, character, str(panel.get("prompt", "")).strip()) if part)
            prompt_neg = str(panel.get("negative_prompt", global_negative)).strip()
            seed = int(panel.get("seed", base_seed + index))
            resolution = int(panel.get("resolution", defaults.get("resolution", min(width, height))))
            dialogue = panel.get("dialogue", [])
            if isinstance(dialogue, str):
                dialogue = [dialogue]

            prompts.append(full_prompt)
            negatives.append(prompt_neg)
            seeds.append(seed)
            resolutions.append(resolution)
            frame_files.append(frame_path.relative_to(Path(folder_paths.get_input_directory())).as_posix())
            character_files.append(character_rel)
            panel_ids.append(panel_id)
            indices.append(index)
            totals.append(panel_count)
            dialogues.append(json.dumps(dialogue, ensure_ascii=False))

        return (prompts, negatives, seeds, resolutions, frame_files, character_files, panel_ids, indices, totals, dialogues)


class MangaPageComposer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "panel_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "panel_id": ("STRING", {"default": "p01"}),
                "dialogue_json": ("STRING", {"default": "[]", "multiline": True}),
                "total_panels": ("INT", {"default": 1, "min": 1, "max": 9999}),
                "output_dir": ("STRING", {"default": "manga_drawer"}),
                "rows": ("INT", {"default": 2, "min": 1, "max": 6}),
                "cols": ("INT", {"default": 2, "min": 1, "max": 6}),
                "gutter": ("INT", {"default": 20, "min": 0, "max": 200}),
                "margin": ("INT", {"default": 40, "min": 0, "max": 400}),
                "page_width": ("INT", {"default": 1600, "min": 512, "max": 8192, "step": 64}),
                "add_bubbles": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("page_or_panel",)
    FUNCTION = "compose"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True

    def compose(self, image, panel_index, panel_id, dialogue_json, total_panels, output_dir, rows, cols, gutter, margin, page_width, add_bubbles):
        root = Path(output_dir).expanduser()
        if not root.is_absolute():
            root = Path(folder_paths.get_output_directory()) / root
        root = root.resolve()
        panels_dir = root / "panels"
        pages_dir = root / "pages"
        panels_dir.mkdir(parents=True, exist_ok=True)
        pages_dir.mkdir(parents=True, exist_ok=True)

        panel = _tensor_to_pil(image)
        if add_bubbles:
            panel = _draw_dialogues(panel, dialogue_json)

        if panel_index == 0:
            for old in panels_dir.glob("*.png"):
                old.unlink()

        panel_path = panels_dir / f"{panel_index + 1:03d}_{_safe_name(panel_id, f'p{panel_index + 1:02d}')}.png"
        panel.save(panel_path, "PNG")

        all_panels = sorted(panels_dir.glob("*.png"))
        if panel_index + 1 < total_panels or len(all_panels) < total_panels:
            return (image,)

        per_page = rows * cols
        page_count = math.ceil(len(all_panels) / per_page)
        saved_pages = []
        page_number = 0
        for page_start in range(0, len(all_panels), per_page):
            page_number += 1
            page_panels = all_panels[page_start:page_start + per_page]
            cell_w = (page_width - 2 * margin - (cols - 1) * gutter) // cols
            cell_h = cell_w
            page_h = 2 * margin + rows * cell_h + (rows - 1) * gutter
            page = Image.new("RGB", (page_width, page_h), (250, 250, 248))
            draw = ImageDraw.Draw(page)
            for index, panel_file in enumerate(page_panels):
                row, col = divmod(index, cols)
                x = margin + col * (cell_w + gutter)
                y = margin + row * (cell_h + gutter)
                tile = ImageOps.fit(Image.open(panel_file).convert("RGB"), (cell_w, cell_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                page.paste(tile, (x, y))
                draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline=(15, 15, 15), width=3)
            page_path = pages_dir / f"page_{page_number:03d}.png"
            page.save(page_path, "PNG")
            saved_pages.append(page_path)

        preview = Image.open(saved_pages[-1]).convert("RGB")
        output_root = Path(folder_paths.get_output_directory()).resolve()
        try:
            subfolder = saved_pages[-1].parent.relative_to(output_root).as_posix()
        except ValueError:
            subfolder = ""
        ui = {"images": [{"filename": saved_pages[-1].name, "subfolder": subfolder, "type": "output"}]}
        return {"ui": ui, "result": (_pil_to_tensor(preview),)}



class MangaImageLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_path": ("STRING", {"default": "", "multiline": False}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "load"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, image_path):
        path = Path(image_path).expanduser()
        if not path.is_absolute():
            path = Path(folder_paths.get_input_directory()) / path
        path = path.resolve()
        return path.stat().st_mtime_ns if path.exists() else float("NaN")

    def load(self, image_path):
        path = Path(image_path).expanduser()
        if not path.is_absolute():
            path = Path(folder_paths.get_input_directory()) / path
        path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(f"Manga reference image not found: {path}")
        image = Image.open(path).convert("RGB")
        return (_pil_to_tensor(image),)

NODE_CLASS_MAPPINGS = {
    "MangaStoryboardLoader": MangaStoryboardLoader,

    "MangaImageLoader": MangaImageLoader,
    "MangaPageComposer": MangaPageComposer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MangaStoryboardLoader": "Manga Storyboard Loader",

    "MangaImageLoader": "Manga Image Loader",
    "MangaPageComposer": "Manga Page Composer",
}


