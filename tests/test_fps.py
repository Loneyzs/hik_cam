# -*- coding: utf-8 -*-

"""
测试2: FPS性能测试（无显示）
测试相机的实际采集性能，记录FPS和每帧耗时
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time
import numpy as np
from hik_camera import HikCamera


def main():
    # 创建相机对象
    print("选择测试模式:")
    print("1. BGR彩色模式")
    print("2. 灰度模式")
    choice = input("请选择 (1/2): ").strip()

    color_mode = "gray" if choice == "2" else "bgr"
    camera = HikCamera(color_mode=color_mode)

    if not camera.init():
        print("初始化失败")
        return

    # 显示设备信息
    device_count = camera.device_list.nDeviceNum
    for i in range(device_count):
        info = camera.get_device_info(i)
        if info:
            print(f"设备 [{i}]: {info}")

    # 打开相机
    if not camera.open(0):
        print("打开相机失败")
        return

    print(f"\n开始性能测试 ({color_mode.upper()}模式)...")
    print("按 Ctrl+C 停止测试\n")

    # 等待相机稳定
    time.sleep(0.5)

    frame_times = []
    fps_samples = []
    test_duration = 10  # 测试时长（秒）
    start_time = time.time()
    last_frame_count = 0

    try:
        while True:
            frame_start = time.time()

            # 读取最新帧（零拷贝）
            ret, frame = camera.read_latest()

            frame_end = time.time()
            frame_time = (frame_end - frame_start) * 1000  # 转换为毫秒

            if ret:
                frame_times.append(frame_time)

                # 每秒统计一次
                elapsed = time.time() - start_time
                if elapsed >= 1.0:
                    current_frame_count = camera.get_frame_count()
                    actual_fps = (current_frame_count - last_frame_count) / elapsed
                    fps_samples.append(actual_fps)

                    print(f"时间: {elapsed:.1f}s | "
                          f"FPS: {actual_fps:.1f} | "
                          f"帧耗时: {frame_time:.2f}ms | "
                          f"总帧数: {current_frame_count}")

                    start_time = time.time()
                    last_frame_count = current_frame_count

                    # 达到测试时长后自动停止
                    if len(fps_samples) >= test_duration:
                        break

            # 短暂休眠，避免CPU占用过高
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n用户中断测试")

    finally:
        camera.release()

        # 统计结果
        if frame_times and fps_samples:
            print("\n" + "="*50)
            print("性能测试结果")
            print("="*50)
            print(f"测试模式: {color_mode.upper()}")
            print(f"总采集帧数: {camera.get_frame_count()}")
            print(f"\nFPS统计:")
            print(f"  平均FPS: {np.mean(fps_samples):.2f}")
            print(f"  最大FPS: {np.max(fps_samples):.2f}")
            print(f"  最小FPS: {np.min(fps_samples):.2f}")
            print(f"  标准差: {np.std(fps_samples):.2f}")
            print(f"\n帧耗时统计 (ms):")
            print(f"  平均耗时: {np.mean(frame_times):.2f}")
            print(f"  最大耗时: {np.max(frame_times):.2f}")
            print(f"  最小耗时: {np.min(frame_times):.2f}")
            print(f"  标准差: {np.std(frame_times):.2f}")
            print("="*50)


if __name__ == "__main__":
    main()
