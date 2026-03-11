# -*- coding: utf-8 -*-

"""
测试1: 实时监看图像
按 'q' 退出，按 's' 保存图像，按 'g' 切换灰度/彩色模式
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import cv2
from hik_camera import HikCamera


def main():
    # 创建相机对象（BGR模式）
    camera = HikCamera(color_mode="bgr")

    if not camera.init():
        print("初始化失败")
        return

    # 显示设备信息
    device_count = camera.device_list.nDeviceNum
    print(f"\n找到 {device_count} 个设备")
    for i in range(device_count):
        info = camera.get_device_info(i)
        if info:
            print(f"设备 [{i}]: {info}")

    # 打开相机
    if not camera.open(0):
        print("打开相机失败")
        return

    print("\n控制说明:")
    print("  q - 退出")
    print("  s - 保存图像")
    print("  空格 - 暂停/继续")

    paused = False
    save_count = 0

    try:
        while True:
            if not paused:
                # 读取最新帧（零拷贝）
                ret, frame = camera.read_latest()

                if ret:
                    # 显示FPS
                    fps = camera.get_fps()
                    cv2.putText(
                        frame,
                        f"FPS: {fps:.1f}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2,
                    )

                    cv2.imshow("Hik Camera - Live View", frame)

            # 处理按键
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            elif key == ord("s") and not paused:
                ret, frame = camera.read()
                if ret:
                    filename = f"capture_{save_count:04d}.jpg"
                    cv2.imwrite(filename, frame)
                    save_count += 1
                    print(f"已保存: {filename}")
            elif key == ord(" "):
                paused = not paused
                print("暂停" if paused else "继续")

    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
