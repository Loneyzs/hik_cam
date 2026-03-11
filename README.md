# 海康工业相机 OpenCV Python 高性能接口

基于海康MVS SDK的图像采集接口。

## 项目结构

```
hik_cam/
├── hik_camera.py          # 核心相机类
├── MvImport/              # 海康SDK Python模块
├── lib/                   # SDK动态库文件
├── tests/                 # 测试程序
│   ├── test_live_view.py  # 实时监看测试
│   └── test_fps.py        # FPS性能测试
└── README.md              # 本文档
```

## 快速开始

### 基本用法

```python
from hik_camera import HikCamera

# 创建相机对象（BGR模式）
camera = HikCamera(color_mode="bgr")

# 初始化并打开相机
camera.init()
camera.open(0)

# 读取图像
ret, frame = camera.read()  # 返回副本，安全但稍慢
# 或
ret, frame = camera.read_latest()  # 返回引用，性能最优

# 获取FPS
fps = camera.get_fps()

# 释放资源
camera.release()
```

### 灰度模式（更高性能）

```python
# 创建灰度模式相机
camera = HikCamera(color_mode="gray")
camera.init()
camera.open(0)

ret, gray_frame = camera.read_latest()
```

## 测试程序

### 1. 实时监看测试

**功能**:
- 实时显示相机画面
- 显示当前FPS
- 按 's' 保存图像
- 按 '空格' 暂停/继续
- 按 'q' 退出

### 2. FPS性能测试

**功能**:
- 无显示窗口，纯性能测试
- 记录实时FPS和每帧耗时
- 支持BGR和灰度两种模式测试
- 自动统计平均/最大/最小FPS
- 输出详细性能报告

## API 文档

### HikCamera 类

#### 初始化参数
- `color_mode`: 输出格式，'bgr' 或 'gray'（默认'bgr'）

#### 主要方法

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `init()` | 初始化SDK并枚举设备 | bool |
| `open(index=0)` | 打开指定索引的相机 | bool |
| `read()` | 读取一帧图像（返回副本） | (bool, ndarray) |
| `read_latest()` | 读取最新帧（零拷贝，性能最优） | (bool, ndarray) |
| `get_fps()` | 获取当前FPS | float |
| `get_frame_count()` | 获取已采集的帧数 | int |
| `get_device_info(index)` | 获取设备信息 | dict |
| `isOpened()` | 检查相机是否已打开 | bool |
| `release()` | 释放相机资源 | None |

#### 性能建议

1. **高帧率场景**: 使用 `read_latest()` 而非 `read()`
2. **灰度处理**: 如果不需要颜色信息，使用 `color_mode="gray"`
3. **避免阻塞**: 主循环中不要进行耗时操作，采集线程会自动更新最新帧
4. **内存管理**: `read_latest()` 返回的是内部缓冲区引用，不要修改

## 依赖环境

- **硬件**: RK3588或其他ARM64平台
- **Python**: 3.x
- **依赖库**:
  - OpenCV (cv2)
  - NumPy
- **SDK**: 海康MVS SDK（已打包在项目中）

## 库文件说明

项目已包含必要的SDK文件，无需额外安装：
- `lib/`: 包含所有必要的.so动态库
- `MvImport/`: 包含Python SDK模块

如需在其他系统使用，确保设置正确的 `LD_LIBRARY_PATH`:
```bash
export LD_LIBRARY_PATH=/path/to/hik_cam/lib:$LD_LIBRARY_PATH
```

## 性能优化说明

### 多线程架构
- 守护线程持续采集图像到内部缓冲区
- 主程序通过 `read_latest()` 获取最新帧，无需等待
- 线程安全的锁机制保证数据一致性

### 内存优化
- 使用 `np.ctypeslib.as_array()` 实现零拷贝转换
- `read_latest()` 返回内部缓冲区引用，避免额外拷贝
- `read()` 返回副本，适合需要保存帧的场景

### 格式选择
- **BGR模式**: 3通道，适合彩色图像处理
- **灰度模式**: 单通道，数据量减少2/3，性能提升明显

## 注意事项

1. 使用 `read_latest()` 时，返回的帧是内部缓冲区的引用，不要修改
2. 如需保存或修改帧，使用 `read()` 或手动 `copy()`
3. 程序退出前务必调用 `release()` 释放资源
4. GigE相机需要正确配置网络参数以达到最佳性能