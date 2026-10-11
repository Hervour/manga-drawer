import json
from pathlib import Path

ROOT = Path.cwd()
IN_DIR = ROOT / "outputs" / "workflows"
FILES = [
    "qwen_image_2_1_t2i_official.json",
    "qwen_image_2_1_image_edit_official.json",
]
OLD_UNET = "qwen_image_2.1_int8_convrot.safetensors"
NEW_UNET = "qwen-image-2.1-UC-Q4_K_M.gguf"
GGUF_URL = "https://huggingface.co/abenzerps/Qwen-Image-2.1-Uncensored-GGUF/resolve/main/qwen-image-2.1-UC-Q4_K_M.gguf"


def replace_values(obj):
    if isinstance(obj, dict):
        return {k: replace_values(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [replace_values(v) for v in obj]
    if isinstance(obj, str):
        return NEW_UNET if obj == OLD_UNET else obj
    return obj


def patch_subgraphs(defs):
    count = 0
    for sg in (defs or {}).get("subgraphs", []):
        for node in sg.get("nodes", []):
            if node.get("type") == "UNETLoader":
                node["type"] = "UnetLoaderGGUF"
                node.setdefault("properties", {})["Node name for S&R"] = "UnetLoaderGGUF"
                node["properties"]["models"] = [{
                    "name": NEW_UNET,
                    "url": GGUF_URL,
                    "directory": "diffusion_models",
                }]
                if isinstance(node.get("widgets_values"), list):
                    node["widgets_values"] = [NEW_UNET]
                if isinstance(node.get("widgets_values_named"), dict):
                    node["widgets_values_named"] = {"unet_name": NEW_UNET}
                count += 1
        count += patch_subgraphs(sg)
    return count


for name in FILES:
    src = IN_DIR / name
    data = json.loads(src.read_text(encoding="utf-8"))
    data = replace_values(data)
    patched = patch_subgraphs(data.get("definitions", {}))
    if patched == 0:
        raise RuntimeError(f"No UNETLoader found in {name}")
    if isinstance(data.get("extra"), dict):
        pass
    out = src.with_name(src.stem.replace("_official", "") + "_GGUF_LOCAL.json")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{out.name}: patched {patched} UNETLoader node(s)")
