#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速验证脚本 - 测试回调模式是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import time
from hik_camera import HikCamera


def main():
    print("="*60)
    print("海康相机回调模式验证")
    print("="*60)

    # 创建相机对象
    camera = HikCamera(color_mode="bgr")

    # 初始化
    print("\n[1/4] 初始化SDK...")
    if not camera.init():
        print("❌ 初始化失败")
        return

    print("✓ 初始化成功")

    # 显示设备信息
    device_count = camera.device_list.nDeviceNum
    print(f"\n[2/4] 找到 {device_count} 个设备")
    for i in range(device_count):
        info = camera.get_device_info(i)
        if info:
            print(f"  设备 [{i}]: {info}")

    # 打开相机
    print("\n[3/4] 打开相机...")
    if not camera.open(0):
        print("❌ 打开相机失败")
        return

    print("✓ 相机已打开，回调已注册")

    # 测试采集
    print("\n[4/4] 测试图像采集（5秒）...")
    print("-" * 60)

    start_time = time.time()
    last_count = 0

    try:
        for i in range(5):
            time.sleep(1)

            ret, frame = camera.read_latest()
            current_count = camera.get_frame_count()
            fps = camera.get_fps()

            if ret:
                print(f"第 {i+1} 秒: "
                      f"FPS={fps:.1f} | "
                      f"总帧数={current_count} | "
                      f"新增帧数={current_count - last_count} | "
                      f"图像尺寸={frame.shape}")
                last_count = current_count
            else:
                print(f"第 {i+1} 秒: ❌ 未获取到图像")

    except KeyboardInterrupt:
        print("\n用户中断")

    finally:
        # 释放资源
        print("\n" + "-" * 60)
        camera.release()

        # 总结
        total_frames = camera.get_frame_count()
        elapsed = time.time() - start_time
        avg_fps = total_frames / elapsed if elapsed > 0 else 0

        print("\n" + "="*60)
        print("测试结果")
        print("="*60)
        print(f"总采集帧数: {total_frames}")
        print(f"测试时长: {elapsed:.2f}秒")
        print(f"平均FPS: {avg_fps:.2f}")

        if avg_fps > 200:
            print("✓ 性能优秀！FPS > 200")
        elif avg_fps > 150:
            print("✓ 性能良好，FPS > 150")
        elif avg_fps > 100:
            print("⚠ 性能一般，FPS > 100")
        else:
            print("❌ 性能不足，FPS < 100")

        print("="*60)


if __name__ == "__main__":
    main()
