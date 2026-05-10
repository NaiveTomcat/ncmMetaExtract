# ncmMetaExtract

从网易云音乐封面文件中提取歌曲 ID，调用远端接口获取歌曲元数据，并把信息写入m4a文件，供Apple Music导入。

## 功能

- 支持单个封面文件处理和批处理目录处理
- 根据封面文件名提取 ID，请求网易云元数据接口
- 将标题、歌手、专辑和歌词写入 `m4a`
- 支持从 `flac`、`m4a`、`mp3` 中查找对应歌曲文件
- 自动重编码至`m4a`文件：`flac`使用`alac`编码，`mp3`使用`aac`编码
- 元数据结果会缓存到 `~/.cache/ncmMetaExtract/`，减少重复请求
- 批处理模式可选删除找不到对应歌曲文件的孤儿封面

## 环境要求

- Python 3.14+
- ffmpeg，需要在`PATH`中

## 安装

使用 `uv`：

```bash
uv sync
```

## 使用

首先保证对应的音乐有解密之后的正常音乐文件

### 单个封面

```bash
uv run src/main.py single <cover_path> <base_dir> [--dest DEST]
```

示例：

```bash
uv run src/main.py single ~/Music/网易云音乐/meta/track-1474337939.jpg ~/Music/网易云音乐 --dest ~/Music/NCM\ Export/
```

### 批处理目录

```bash
uv run src/main.py batch <cover_dir> <base_dir> [--dest DEST] [--delete-orphaned-covers]
```

示例：

```bash
uv run src/main.py batch ~/Music/网易云音乐/meta ~/Music/网易云音乐 --dest ~/Music/NCM\ Export/ --delete-orphaned-covers
```

## 参数说明

- `cover_path`：单个封面图片路径
- `cover_dir`：封面图片目录
- `base_dir`：搜索歌曲文件的根目录
- `--dest`：输出目录；不传时会直接处理原文件
- `--delete-orphaned-covers`：批处理模式下，如果找不到对应歌曲文件，则删除该封面文件

## 约定

- 只有文件名包含歌曲标题时才会被视为候选文件
- 候选文件进一步优先匹配歌手名
- 目前只会搜索 `.flac`、`.m4a`、`.mp3` 文件

## 缓存

元数据请求会按 ID 缓存为 JSON 文件，位置在：

```bash
~/.cache/ncmMetaExtract/
```

如果你想强制重新拉取数据，可以删除对应 ID 的缓存文件。


