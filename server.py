#!/usr/bin/env python3
"""
简单的 HTTP 服务器，用于展示 GitHub Trending AI 页面
运行: python3 server.py
访问: http://localhost:8080
"""

import http.server
import socketserver
import os

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🚀 服务已启动: http://localhost:{PORT}")
        print(f"📁 当前目录: {DIRECTORY}")
        print("按 Ctrl+C 停止服务")
        httpd.serve_forever()
