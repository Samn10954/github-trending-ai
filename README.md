# GitHub Trending AI 每日精选

> 每日 AI、具身智能热门开源项目精选

## 快速部署到 GitHub Pages

### 方式一：手动部署（推荐）

1. **创建 GitHub 仓库**
   - 打开 https://github.com/new
   - 仓库名：`github-trending-ai`
   - 设为 **Public**
   - 不要勾选 README

2. **推送代码**
   ```bash
   cd ~/.openclaw/workspace/github-trending-ai
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/github-trending-ai.git
   git push -u origin main
   ```

3. **开启 GitHub Pages**
   - 进入仓库 → Settings → Pages
   - Source 选择 **Deploy from a branch**
   - Branch 选择 **gh-pages** / **(root)**
   - Save

4. **获取访问链接**
   - 等待 1-2 分钟，页面会生成类似 `https://YOUR_USERNAME.github.io/github-trending-ai/` 的链接

### 方式二：自动部署（推荐）

推送代码后，GitHub Actions 会自动部署：
- 打开仓库 → Actions
- 查看部署状态
- 成功后点击 "GitHub Pages" 链接

## 本地运行

```bash
cd github-trending-ai
python3 collector.py    # 采集数据
python3 server.py       # 启动本地服务 http://localhost:8080
```

## 自动采集

已配置每日 8:00 自动运行采集脚本（需手动触发或配置 Cron）
