#!/bin/bash

# 杀死占用 5000 端口的进程
echo "检查并杀死占用 5000 端口的进程..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

# 等待进程完全终止
sleep 2

# 暂停并提示用户确认
read -p "按 Ctrl+C 退出或按 Enter 键继续启动项目..."

# 启动 Flask 应用作为后台进程
echo "启动 Flask 应用..."
nohup flask run --host=0.0.0.0 &

# 捕获 SIGINT 信号（Ctrl+C）
trap cleanup SIGINT

cleanup() {
    echo "正在关闭 Flask 应用..."

    # 杀死 Flask 进程
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true

    echo "Flask 应用已关闭"
    exit 0
}

# 等待所有后台进程
wait

echo "项目已启动！"
