#!/bin/bash
# 一键部署脚本

cd "$(dirname "$0")"

echo "🚀 开始部署到 GitHub Pages..."

# 检查是否已初始化 git
if [ ! -d .git ]; then
    echo "📁 初始化 Git 仓库..."
    git init
    git add .
    git commit -m "Update GitHub Trending AI data"
    git branch -M main
fi

echo ""
echo "========================================"
echo "请在 GitHub 创建空仓库后，运行以下命令："
echo ""
echo "  git remote add origin https://github.com/YOUR_USERNAME/github-trending-ai.git"
echo "  git push -u origin main"
echo ""
echo "然后在 GitHub 仓库设置中开启 Pages："
echo "  Settings → Pages → Source: Deploy from a branch → main"
echo "========================================"
echo ""
echo "推送后，GitHub Actions 会自动部署"
