# manga drawer 使用说明

`manga drawer` 是一个按故事板逐格生成漫画，并自动拼成漫画页的 ComfyUI 工作流。

## 已安装内容

ComfyUI 用户工作流：

```text
outputs/ComfyUI/user/default/workflows/manga drawer.json
```

自定义节点：

```text
outputs/ComfyUI/custom_nodes/ComfyUI-MangaDrawer/
```

示例故事板：

```text
outputs/manga_drawer/storyboard.json
```

示例角色参考图：

```text
outputs/manga_drawer/character_sheet.png
`

示例分镜草稿：

`	ext
outputs/manga_drawer/roughs/p01.png
outputs/manga_drawer/roughs/p02.png
outputs/manga_drawer/roughs/p03.png
outputs/manga_drawer/roughs/p04.png
`

2x2 排版预览：

`	ext
outputs/manga_drawer/layout_preview.png
```

## 启动和打开

1. 双击 `outputs/start_comfyui.bat`。
2. 浏览器打开 `http://127.0.0.1:8188`。
3. 点击左侧 Workflows / 工作流。
4. 打开 `manga drawer`。

## 怎么运行

1. 在 `Manga Storyboard Loader` 节点中选择 `storyboard.json`。
2. 点击一次 `Queue/Run`。
3. 工作流会按故事板中的 panel 顺序逐格生成。
4. 每一个 panel 使用相同的角色参考图，并自动使用各自的提示词和 seed。
5. 最后一格完成后，`Manga Page Composer` 自动拼成漫画页。

因为是列表顺序执行，所以 8 GB 显存不会同时加载多张图片。它不会加速单张生成，但不需要手动一张一张点击。

## 输出位置

单格图片：

```text
outputs/ComfyUI/output/manga drawer/panels/
```

漫画页：

```text
outputs/ComfyUI/output/manga drawer/pages/page_001.png
```

## storyboard.json 格式

```json
{
  "project": "demo_manga",
  "style": "black-and-white manga, clean inking, screentone shading",
  "character": "young detective, short black hair, long beige coat",
  "negative_prompt": "text, watermark, logo, bad hands",
  "character_sheet": "character_sheet.png",
  "base_seed": 100000,
  "defaults": {
    "width": 768,
    "height": 768,
    "resolution": 768
  },
  "panels": [
    {
      "id": "p01",
      "prompt": "wide shot, rainy city street at night",
      "dialogue": ["这个城市，从来没有真正安静过。"]
    },
    {
      "id": "p02",
      "prompt": "close-up of the detective noticing a red light",
      "dialogue": ["等等……那是什么？"],
      "seed": 120001
    }
  ]
}
```

## 提高漫画一致性

- `style` 和 `character` 会固定加在每个 panel 的提示词前面。
- `character_sheet` 是对应角色的参考图，建议保持固定。
- `frame` 可以为每个 panel 指定一张草图或构图参考。
- 不填写 `frame` 时，节点会生成一个带边框和三分线的占位面板。
- 建议每个 panel 使用不同的 `seed`，但保持相同的 `style`、`character`、采样器和步数。
- 如果要做长期连载，下一步可以给固定角色训练一个小型 LoRA。

## 对白与分镜

- `dialogue` 是数组，可以放多条对白。
- 默认会在面板左上或右上绘制白底黑框对话框。
- 如果不想让节点自动加对白，把 `Manga Page Composer` 的 `add_bubbles` 改为 false。
- 漫画字号和气泡位置还可以用 Photoshop、Krita、Clip Studio Paint 等后期调整。

## 页面布局

`Manga Page Composer` 的默认布局是 2x2：

```text
rows = 2
cols = 2
```

如果需要其他布局：

- 四格：2 x 2
- 六格：2 x 3 或 3 x 2
- 纵向条漫：1 x 6
- 横向页：3 x 1

每页超过 `rows * cols` 个 panel 时，会自动生成下一页。

## 性能建议

- 当前 GPU：RTX 4060 Laptop 8 GB
- 推荐草稿：512 x 512 或 768 x 768，12–18 steps
- 推荐定稿：1024 x 1024，25–30 steps
- 保持 `batch_size = 1` 或不对 panel 做并行批次
- 漫画页拼接发生在最后一步，不增加采样阶段显存
- 首次运行模型加载时间较长，后续 panel 会继续使用同一进程


## 重要故障修复

如果出现：

```text
aimdo memory compile error
RuntimeError
```

请在启动 ComfyUI 时使用：

```text
--disable-dynamic-vram --lowvram
```

`start_comfyui.bat` 已经更新为这两个参数。不要只使用 `--lowvram`，因为新版 ComfyUI 在动态 VRAM 开启时可能忽略它。

## 当前示例故事板注意

`storyboard.json` 引用了：

```text
roughs/p01.png ... roughs/p12.png
```

目前实际存在的是 `p01.png` 到 `p04.png`。p05 到 p12 的缺失文件会自动生成占位格，不会导致 JSON 报错；但如果希望控制构图，应补充对应草图，或者删除这些 panel 中的 `frame` 字段。

## 生成时间建议

Qwen Image 2.1 20B 模型在 RTX 4060 Laptop 8 GB 上很慢。首次加载还会包含模型加载时间。

- 第一次测试：只保留 1 个 panel，使用 1–4 steps
- 漫画草稿：768 x 768，8–15 steps
- 最终输出：再使用 20–25 steps
- 不要第一次直接跑 12 格 x 25 steps

## 三个四格分部

原来的 12 格已拆成三个独立故事板：

```text
outputs/manga_drawer/storyboards/storyboard_part1.json
outputs/manga_drawer/storyboards/storyboard_part2.json
outputs/manga_drawer/storyboards/storyboard_part3.json
```

对应三个 ComfyUI 工作流：

```text
manga drawer part1
manga drawer part2
manga drawer part3
```

每个工作流只生成四格并自动拼成一张页面：

```text
outputs/ComfyUI/output/manga drawer part1/pages/page_001.png
outputs/ComfyUI/output/manga drawer part2/pages/page_001.png
outputs/ComfyUI/output/manga drawer part3/pages/page_001.png
```

三部之间通过 `continuity` 字段保持连续：

- Part 1：下班回家、进门、洗澡
- Part 2：浴室出来后遇见男伴、客厅到沙发
- Part 3：继续、高潮、事后收尾

每个 panel 的花括号可以单独复制和修改。`continuity` 会固定加到每个 panel 的提示词之前。

> The README above also documents local ComfyUI paths from the original machine. Treat `outputs/...` paths as installation-relative guidance.
