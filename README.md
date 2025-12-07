**目标**
- 将收藏链接统一归集到表格，自动识别平台并采集文本/视频内容；对视频进行本地转写；用国内模型生成Markdown总结；写入飞书文档并按类别归档。

**项目结构**
- `src/main.py` 入口，读取 `data/collection.csv` 并执行采集、总结与写入
- `src/platforms/detector.py` 平台识别
- `src/collectors/*` 采集模块（知乎/抖音/B站/通用网页）
- `src/transcribe/transcriber.py` 本地语音转写（faster-whisper）
- `src/llm/*` DeepSeek 与阿里百炼总结
- `src/feishu/client.py` 飞书API，创建文件夹、文档并写入Markdown代码块
- `data/collection.csv` 示例数据
- `.env.example` 环境变量模板

**准备**
- 安装依赖：`pip install -r requirements.txt`
- 新建 `.env`：
  - `DEEPSEEK_API_KEY` 填入 DeepSeek 密钥
  - `ALI_DASHSCOPE_API_KEY` 填入阿里百炼密钥
  - `FEISHU_APP_ID`、`FEISHU_APP_SECRET` 填入飞书应用凭证
  - `FEISHU_ROOT_FOLDER_TOKEN` 可留空表示根目录
  - 可选：`DEFAULT_SUMMARIZER=bailian` 指定默认总结模型为阿里百炼

**使用**
- 编辑 `data/collection.csv`，包含列：`source,url`
- 运行：`python src/main.py` 或 `python src/main.py data/collection.csv`

**说明**
- 视频链接通过 `yt-dlp` 抽取音频并用 `faster-whisper` 本地转写，避免依赖国外API。
- 写入飞书时以“Markdown代码块”的形式保留结构与可读性；可扩展为块级渲染。
- 首次写入会在云空间创建文件夹“知识收藏”。
