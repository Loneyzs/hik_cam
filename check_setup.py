#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目结构验证脚本
检查所有必要的文件和依赖是否正确
"""

import os
import sys

def check_file(path, description):
    """检查文件是否存在"""
    if os.path.exists(path):
        print(f"✓ {description}: {path}")
        return True
    else:
        print(f"✗ {description}: {path} (未找到)")
        return False

def check_dir(path, description):
    """检查目录是否存在"""
    if os.path.isdir(path):
        file_count = len(os.listdir(path))
        print(f"✓ {description}: {path} ({file_count} 个文件)")
        return True
    else:
        print(f"✗ {description}: {path} (未找到)")
        return False

def main():
    print("="*60)
    print("海康相机项目结构验证")
    print("="*60)

    base_dir = os.path.dirname(__file__)
    all_ok = True

    print("\n[核心文件]")
    all_ok &= check_file(os.path.join(base_dir, "hik_camera.py"), "核心模块")
    all_ok &= check_file(os.path.join(base_dir, "README.md"), "说明文档")

    print("\n[SDK文件]")
    all_ok &= check_dir(os.path.join(base_dir, "MvImport"), "Python SDK模块")
    all_ok &= check_dir(os.path.join(base_dir, "lib"), "动态库文件")

    print("\n[测试文件]")
    all_ok &= check_file(os.path.join(base_dir, "tests", "test_live_view.py"), "实时监看测试")
    all_ok &= check_file(os.path.join(base_dir, "tests", "test_fps.py"), "FPS性能测试")

    print("\n[依赖检查]")
    try:
        import numpy
        print(f"✓ NumPy: {numpy.__version__}")
    except ImportError:
        print("✗ NumPy: 未安装")
        all_ok = False

    try:
        import cv2
        print(f"✓ OpenCV: {cv2.__version__}")
    except ImportError:
        print("✗ OpenCV: 未安装")
        all_ok = False

    print("\n[SDK模块检查]")
    sys.path.insert(0, os.path.join(base_dir, "MvImport"))
    try:
        from MvCameraControl_class import MvCamera
        print("✓ MvCameraControl_class 导入成功")
    except ImportError as e:
        print(f"✗ MvCameraControl_class 导入失败: {e}")
        all_ok = False

    print("\n" + "="*60)
    if all_ok:
        print("✓ 所有检查通过，项目结构正确")
        print("\n可以运行测试:")
        print("  cd tests && python3 test_live_view.py")
        print("  cd tests && python3 test_fps.py")
    else:
        print("✗ 存在问题，请检查上述错误")
    print("="*60)

if __name__ == "__main__":
    main()
