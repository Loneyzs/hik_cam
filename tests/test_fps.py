# -*- coding: utf-8 -*-

"""
FPS性能测试（无显示）
测试相机的实际采集性能，记录FPS和每帧耗时
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time
import numpy as np
from hik_camera import HikCamera


def main():
    camera = HikCamera()

    if not camera.init():
        print("初始化失败")
        return

    device_count = camera.device_list.nDeviceNum
    for i in range(device_count):
        info = camera.get_device_info(i)
        if info:
            print(f"设备 [{i}]: {info}")

    if not camera.open(0):
        print("打开相机失败")
        return

    print(f"\n开始性能测试 (BGR模式)...")
    print("按 Ctrl+C 停止测试\n")

    # 等待相机稳定
    time.sleep(0.5)

    fps_samples = []
    test_duration = 10  # 测试时长（秒）
    start_time = time.time()
    last_frame_count = 0

    try:
        while True:
            # 每秒统计一次
            time.sleep(1.0)

            current_frame_count = camera.get_frame_count()
            elapsed = time.time() - start_time
            new_frames = current_frame_count - last_frame_count
            actual_fps = new_frames / elapsed
            fps_samples.append(actual_fps)

            ret, frame = camera.read_latest()
            shape_str = f"{frame.shape}" if ret else "N/A"

            print(f"第 {len(fps_samples):2d} 秒 | "
                  f"FPS: {actual_fps:6.1f} | "
                  f"新增帧: {new_frames:4d} | "
                  f"总帧数: {current_frame_count:6d} | "
                  f"图像: {shape_str}")

            start_time = time.time()
            last_frame_count = current_frame_count

            if len(fps_samples) >= test_duration:
                break

    except KeyboardInterrupt:
        print("\n用户中断测试")

    finally:
        camera.release()

        if fps_samples:
            # 跳过第一秒（预热）
            stable_fps = fps_samples[1:] if len(fps_samples) > 1 else fps_samples

            print("\n" + "="*50)
            print("性能测试结果")
            print("="*50)
            print(f"总采集帧数: {camera.get_frame_count()}")
            print(f"\nFPS统计 (跳过第1秒预热):")
            print(f"  平均FPS: {np.mean(stable_fps):.1f}")
            print(f"  最大FPS: {np.max(stable_fps):.1f}")
            print(f"  最小FPS: {np.min(stable_fps):.1f}")
            print(f"  标准差:  {np.std(stable_fps):.1f}")
            print("="*50)


if __name__ == "__main__":
    main()
