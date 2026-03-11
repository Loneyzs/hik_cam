# -*- coding: utf-8 -*-

import sys
import os
import numpy as np
import threading
import time
from ctypes import *

# 设置库文件路径
lib_path = os.path.join(os.path.dirname(__file__), "lib")
if os.path.exists(lib_path):
    os.environ["LD_LIBRARY_PATH"] = lib_path + ":" + os.environ.get("LD_LIBRARY_PATH", "")

# 添加SDK模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "MvImport"))
from MvCameraControl_class import *


class HikCamera:
    """
    海康工业相机高性能封装类
    - 多线程架构，守护线程循环抓图
    - 零拷贝优化，减少内存操作
    - 支持BGR和灰度两种输出格式
    """

    def __init__(self, color_mode="bgr"):
        """
        初始化相机
        Args:
            color_mode: 'bgr' 或 'gray'，指定输出图像格式
        """
        self.cam = None
        self.device_list = None
        self.is_opened = False
        self.color_mode = color_mode.lower()

        # 多线程相关
        self._capture_thread = None
        self._running = False
        self._lock = threading.Lock()
        self._latest_frame = None
        self._frame_count = 0

        # 性能统计
        self.fps = 0.0
        self._last_time = 0

    def init(self):
        """初始化SDK并枚举设备"""
        try:
            ret = MvCamera.MV_CC_Initialize()
            if ret != 0:
                print(f"初始化SDK失败! 错误码: 0x{ret:x}")
                return False

            self.device_list = MV_CC_DEVICE_INFO_LIST()
            tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE

            ret = MvCamera.MV_CC_EnumDevices(tlayerType, self.device_list)
            if ret != 0:
                print(f"枚举设备失败! 错误码: 0x{ret:x}")
                return False

            if self.device_list.nDeviceNum == 0:
                print("未找到设备!")
                return False

            print(f"找到 {self.device_list.nDeviceNum} 个设备")
            return True

        except Exception as e:
            print(f"初始化异常: {e}")
            return False

    def open(self, index=0):
        """打开指定索引的相机并启动采集线程"""
        if self.device_list is None:
            print("请先调用init()初始化")
            return False

        if index >= self.device_list.nDeviceNum:
            print(f"设备索引 {index} 超出范围")
            return False

        try:
            self.cam = MvCamera()
            stDeviceList = cast(
                self.device_list.pDeviceInfo[index], POINTER(MV_CC_DEVICE_INFO)
            ).contents

            ret = self.cam.MV_CC_CreateHandle(stDeviceList)
            if ret != 0:
                print(f"创建句柄失败! 错误码: 0x{ret:x}")
                return False

            ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
            if ret != 0:
                print(f"打开设备失败! 错误码: 0x{ret:x}")
                return False

            # GigE相机优化
            if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
                nPacketSize = self.cam.MV_CC_GetOptimalPacketSize()
                if int(nPacketSize) > 0:
                    self.cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)

            # 设置触发模式为off
            ret = self.cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
            if ret != 0:
                print(f"设置触发模式失败! 错误码: 0x{ret:x}")
                return False

            # 设置Bayer转换质量
            self.cam.MV_CC_SetBayerCvtQuality(1)

            # 开始取流
            ret = self.cam.MV_CC_StartGrabbing()
            if ret != 0:
                print(f"开始取流失败! 错误码: 0x{ret:x}")
                return False

            self.is_opened = True

            # 启动采集线程
            self._running = True
            self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._capture_thread.start()

            print("相机打开成功，采集线程已启动")
            return True

        except Exception as e:
            print(f"打开相机异常: {e}")
            return False

    def _capture_loop(self):
        """采集线程主循环"""
        stOutFrame = MV_FRAME_OUT()
        memset(byref(stOutFrame), 0, sizeof(stOutFrame))

        # 根据颜色模式设置目标像素格式
        if self.color_mode == "gray":
            dst_pixel_type = PixelType_Gvsp_Mono8
            channels = 1
        else:
            dst_pixel_type = PixelType_Gvsp_BGR8_Packed
            channels = 3

        while self._running:
            try:
                # 获取一帧图像
                ret = self.cam.MV_CC_GetImageBuffer(stOutFrame, 100)
                if ret != 0 or stOutFrame.pBufAddr is None:
                    continue

                # 准备转换参数
                width = stOutFrame.stFrameInfo.nWidth
                height = stOutFrame.stFrameInfo.nHeight
                buffer_size = width * height * channels

                stConvertParam = MV_CC_PIXEL_CONVERT_PARAM_EX()
                memset(byref(stConvertParam), 0, sizeof(stConvertParam))

                stConvertParam.nWidth = width
                stConvertParam.nHeight = height
                stConvertParam.pSrcData = stOutFrame.pBufAddr
                stConvertParam.nSrcDataLen = stOutFrame.stFrameInfo.nFrameLen
                stConvertParam.enSrcPixelType = stOutFrame.stFrameInfo.enPixelType
                stConvertParam.enDstPixelType = dst_pixel_type
                stConvertParam.pDstBuffer = (c_ubyte * buffer_size)()
                stConvertParam.nDstBufferSize = buffer_size

                # 转换像素格式
                ret = self.cam.MV_CC_ConvertPixelTypeEx(stConvertParam)
                if ret != 0:
                    self.cam.MV_CC_FreeImageBuffer(stOutFrame)
                    continue

                # 零拷贝转换为numpy数组
                frame = np.ctypeslib.as_array(
                    stConvertParam.pDstBuffer, shape=(height, width, channels) if channels > 1 else (height, width)
                ).copy()

                # 释放图像缓冲区
                self.cam.MV_CC_FreeImageBuffer(stOutFrame)

                # 更新最新帧
                with self._lock:
                    self._latest_frame = frame
                    self._frame_count += 1

                    # 计算FPS
                    current_time = time.time()
                    if self._last_time > 0:
                        elapsed = current_time - self._last_time
                        if elapsed > 0:
                            self.fps = 1.0 / elapsed
                    self._last_time = current_time

            except Exception as e:
                print(f"采集线程异常: {e}")
                if stOutFrame.pBufAddr is not None:
                    try:
                        self.cam.MV_CC_FreeImageBuffer(stOutFrame)
                    except:
                        pass

    def read(self):
        """
        读取最新的一帧图像
        返回: (ret, frame)
            ret: bool, 是否成功读取
            frame: numpy.ndarray, BGR或灰度格式的图像
        """
        if not self.is_opened:
            return False, None

        with self._lock:
            if self._latest_frame is None:
                return False, None
            # 返回副本，避免外部修改
            return True, self._latest_frame.copy()

    def read_latest(self):
        """
        读取最新帧（不复制，性能最优）
        注意：返回的是内部缓冲区的引用，外部不应修改
        返回: (ret, frame)
        """
        if not self.is_opened:
            return False, None

        with self._lock:
            if self._latest_frame is None:
                return False, None
            return True, self._latest_frame

    def get_fps(self):
        """获取当前FPS"""
        return self.fps

    def get_frame_count(self):
        """获取已采集的帧数"""
        with self._lock:
            return self._frame_count

    def isOpened(self):
        """检查相机是否已打开"""
        return self.is_opened

    def release(self):
        """释放相机资源"""
        # 停止采集线程
        if self._running:
            self._running = False
            if self._capture_thread is not None:
                self._capture_thread.join(timeout=2.0)

        if self.cam is not None:
            try:
                if self.is_opened:
                    self.cam.MV_CC_StopGrabbing()
                    self.cam.MV_CC_CloseDevice()
                    self.is_opened = False

                self.cam.MV_CC_DestroyHandle()
                self.cam = None
                print("相机已释放")

            except Exception as e:
                print(f"释放相机异常: {e}")

    def __del__(self):
        """析构函数"""
        self.release()
        try:
            MvCamera.MV_CC_Finalize()
        except:
            pass

    def get_device_info(self, index=0):
        """
        获取设备信息
        返回: dict 包含设备信息
        """
        if self.device_list is None or index >= self.device_list.nDeviceNum:
            return None

        mvcc_dev_info = cast(
            self.device_list.pDeviceInfo[index], POINTER(MV_CC_DEVICE_INFO)
        ).contents

        info = {}

        if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
            info["type"] = "GigE"
            info["model"] = self._decode_char(mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName)
            nip1 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24
            nip2 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16
            nip3 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8
            nip4 = mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff
            info["ip"] = f"{nip1}.{nip2}.{nip3}.{nip4}"

        elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
            info["type"] = "USB3.0"
            info["model"] = self._decode_char(mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName)
            info["serial"] = self._decode_char(mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber)

        return info

    @staticmethod
    def _decode_char(ctypes_char_array):
        """解码ctypes字符数组"""
        byte_str = memoryview(ctypes_char_array).tobytes()
        null_index = byte_str.find(b"\x00")
        if null_index != -1:
            byte_str = byte_str[:null_index]

        for encoding in ["gbk", "utf-8", "latin-1"]:
            try:
                return byte_str.decode(encoding)
            except UnicodeDecodeError:
                continue

        return byte_str.decode("latin-1", errors="replace")
