# ncmMetaExtract

从网易云音乐封面文件中提取歌曲 ID，调用远端接口获取歌曲元数据，并把信息写入m4a文件，供Apple Music导入。

## 建议使用方法

1. 网易云音乐先下载，使用`ncm_c`之类工具解密
2. 将已下载单曲新建至一个歌单
3. Web端登陆，查看上面新建的歌单，获取歌单的JSON
4. 使用`track-list`功能进行转换

## 功能

- 支持单个封面文件处理、批处理目录处理和播放列表JSON处理
- 根据封面文件名或播放列表JSON提取歌曲信息
- 请求网易云官方API获取歌词和专辑封面
- 将标题、歌手、专辑、歌词和封面写入 `m4a`
- 支持从 `flac`、`m4a`、`mp3` 中查找对应歌曲文件
- 自动重编码至`m4a`文件：`flac`使用`alac`编码，`mp3`使用`aac`编码
- 元数据结果会缓存到 `~/.cache/ncmMetaExtract/`，减少重复请求
- 封面和歌词自动从网易云API获取和缓存
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

### 从歌单 JSON 处理

使用网易云官方 API 获取的歌单 JSON 文件处理：

```bash
uv run src/main.py track-list <track_list_path> <base_dir> [--dest DEST]
```

示例：

```bash
uv run src/main.py track-list ~/track_list.json ~/Music/网易云音乐 --dest ~/Music/NCM\ Export/
```

**说明**：
- `track_list_path`：从网易云官方 API 获取的歌单 JSON 文件
- 程序会自动从 JSON 中提取每首歌曲的信息
- 自动从网易云 API 获取歌词信息
- 自动下载专辑封面（如果歌曲文件中没有）
- 自动转换为 m4a 格式并填充元数据

## 参数说明

- `cover_path`：单个封面图片路径
- `cover_dir`：封面图片目录
- `track_list_path`：网易云官方 API 返回的播放列表 JSON 文件路径
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


