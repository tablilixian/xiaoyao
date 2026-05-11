# 逍遥小散仙 - 知识图谱系统

## 项目说明

本项目包含三个主要模块：
1. **知识图谱可视化系统** (`novel_visualization/`) - 展示人物关系、势力关系、世界地图、故事时间线
2. **小说阅读器** (`novel_reader_site/`) - 在线阅读小说，支持角色卡片悬浮显示
3. **小说数据** (`novel_reader/`) - 章节内容数据（28卷完整内容）

## 快速开始

### 方式一：Python 简易服务器（推荐）

1. 确保已安装 Python 3
2. 打开终端，进入项目目录
3. 运行以下命令：

```bash
# 启动服务器
python3 -m http.server 9999

# 或者使用 Python 2
python -m SimpleHTTPServer 9999
```

4. 打开浏览器访问：
   - 知识图谱：http://localhost:9999/novel_visualization/index.html
   - 小说阅读器：http://localhost:9999/novel_reader_site/index.html

### 方式二：Node.js 服务器

```bash
# 安装 http-server
npm install -g http-server

# 启动服务器
http-server -p 9999
```

### 方式三：直接打开（部分功能可能受限）

直接双击 `novel_visualization/index.html` 或 `novel_reader_site/index.html` 文件。

**注意**：由于浏览器安全限制，直接打开文件时 AJAX 请求可能失败，建议使用 HTTP 服务器。

## 功能说明

### 知识图谱系统

| 功能 | 说明 |
|------|------|
| 关系图谱 | 394个人物的关系网络，支持搜索、筛选、聚焦 |
| 势力关系 | 52个势力的同盟/敌对关系，点击显示成员 |
| 世界地图 | 325个地点的层级关系网络 |
| 故事时间线 | 按章节展示事件、角色、地点信息 |

### 小说阅读器

- 支持多卷阅读（28卷完整内容）
- 角色卡片悬浮显示（功法、兵器、法宝等）
- 章节导航
- 阅读进度保存

## 目录结构

```
xiaoyao_project/
├── novel_visualization/     # 知识图谱系统
│   ├── index.html          # 主页面
│   ├── main.js             # 关系图谱、势力关系、世界地图
│   └── timeline.js         # 故事时间线
├── novel_reader_site/       # 小说阅读器前端
│   ├── index.html          # 主页面
│   ├── reader.html         # 阅读器页面
│   └── characters_db.json  # 角色数据库（418个角色）
├── novel_reader/            # 小说内容数据
│   ├── index.json          # 全局索引（5.6MB）
│   ├── chapters/           # 章节内容
│   │   ├── volume_01/      # 第1卷
│   │   │   ├── chapter_001.json  # 楔子
│   │   │   ├── chapter_002.json  # 第一回
│   │   │   └── ...
│   │   ├── volume_02/      # 第2卷
│   │   └── ...             # 共28卷
│   └── images/             # 插图图片
├── novel_data/              # 分析数据
│   ├── volumes/            # 各卷分析JSON
│   └── index/              # 索引文件（角色、地点、势力）
└── README.md               # 本说明文件
```

## 数据文件说明

### 阅读器内容数据

阅读器显示的小说内容存储在 `novel_reader/chapters/` 目录下：

| 文件路径 | 内容 |
|----------|------|
| `novel_reader/index.json` | 全局索引（所有卷章节列表） |
| `novel_reader/chapters/volume_XX/` | 第XX卷的章节目录 |
| `novel_reader/chapters/volume_XX/chapter_XXX.json` | 第XXX章的完整内容 |

每个章节JSON文件包含：
- `volume`: 卷号
- `chapter`: 章节号
- `title`: 章节标题
- `content`: 章节正文内容
- `images`: 相关图片

### 角色数据库

`novel_reader_site/characters_db.json` 包含418个角色的详细信息：
- 基本信息（姓名、性别、势力）
- 能力数据（功法、兵器、法宝、坐骑等）
- 人物关系

## 技术栈

- **前端**：HTML5, CSS3, JavaScript
- **可视化**：D3.js (力导向图), ECharts (饼图)
- **数据**：JSON 格式

## 浏览器支持

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 注意事项

1. 首次加载可能需要几秒钟，请耐心等待
2. 建议使用 Chrome 浏览器以获得最佳体验
3. 如果图表显示异常，请刷新页面重试

---

**逍遥小散仙** - 知识图谱可视化系统 v1.0
