# Game Scraper

一个用于抓取 onlinegames.io 游戏 iframe 信息的爬虫工具。

## 功能特性

- 自动获取游戏列表
- 提取游戏页面中的 iframe 信息
- 将数据保存为 CSV 格式
- 自动处理会话失效和错误重试

## 使用方法

1. 安装依赖：
```python
pip install selenium requests
```

2. 运行脚本：
```python
python scraper.py
```

## 数据格式

生成的 CSV 文件包含以下字段：
- game_name: 游戏名称
- game_url: 游戏页面URL
- iframe_src: iframe 源地址
- iframe_id: iframe ID
- iframe_class: iframe 类名
- timestamp: 记录时间

## 注意事项

- 需要 Chrome 浏览器
- 自动下载对应版本的 ChromeDriver
- 支持错误重试和会话恢复