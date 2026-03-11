#!/bin/bash

# 海康相机项目快速启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="${SCRIPT_DIR}/lib:${LD_LIBRARY_PATH}"

echo "=========================================="
echo "海康工业相机 - 快速启动"
echo "=========================================="
echo ""
echo "请选择要运行的程序:"
echo "  1) 检查项目配置"
echo "  2) 实时监看测试"
echo "  3) FPS性能测试"
echo "  q) 退出"
echo ""
read -p "请输入选项 (1-3/q): " choice

case $choice in
    1)
        echo ""
        echo "运行配置检查..."
        python3 "${SCRIPT_DIR}/check_setup.py"
        ;;
    2)
        echo ""
        echo "启动实时监看测试..."
        cd "${SCRIPT_DIR}/tests"
        python3 test_live_view.py
        ;;
    3)
        echo ""
        echo "启动FPS性能测试..."
        cd "${SCRIPT_DIR}/tests"
        python3 test_fps.py
        ;;
    q|Q)
        echo "退出"
        exit 0
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac
