# 视频归类脚本使用说明

## 功能描述

该脚本用于根据 `prompts_per_dimension` 目录中的文本文件，将视频文件归类到相应的子集中。

## 脚本位置

`classify_videos.py`

## 使用方法

```bash
python classify_videos.py <视频目录> <输出目录>
```

### 参数说明

- `<视频目录>`: 包含待归类视频的目录
- `<输出目录>`: 分类后视频的存放目录

## 工作原理

1. 遍历 `prompts_per_dimension` 目录中的所有 `.txt` 文件
2. 对于每个文件，提取子集名称（文件名不含 `.txt`）
3. 读取文件中的每一行，提取 case 名称
4. 在视频目录中寻找匹配 `{case名}-0x.mp4` 格式的视频文件（x 为整数）
5. 将匹配的视频文件复制到 `output_dir/子集名称/` 目录中

## 示例

```bash
python classify_videos.py ./videos ./output
```

这将从 `./videos` 目录中寻找视频文件，并将它们归类到 `./output` 目录下的相应子集中。