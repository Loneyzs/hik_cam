# 海康工业相机 OpenCV Python 高性能接口

基于海康MVS SDK开发的高性能Python接口，专为电赛控制组优化，支持高帧率图像采集。

## 项目结构

```
hik_cam/
├── hik_camera.py          # 核心相机类（回调模式）
├── MvImport/              # 海康SDK Python模块
├── lib/                   # SDK动态库文件
├── tests/                 # 测试程序
│   ├── test_live_view.py  # 实时监看测试
│   └── test_fps.py        # FPS性能测试
├── verify_callback.py     # 快速验证脚本
├── README.md              # 本文档
└── OPTIMIZATION.md        # 优化说明文档
```

## 快速开始

### 基本用法

```python
from hik_camera import HikCamera

# 创建相机对象
camera = HikCamera()

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

## 测试程序

### 1. 快速验证

运行5秒快速测试，验证回调模式是否正常工作。

### 2. 实时监看测试

**功能**:
- 实时显示相机画面
- 显示当前FPS
- 按 's' 保存图像
- 按 '空格' 暂停/继续
- 按 'q' 退出

### 3. FPS性能测试

**功能**:
- 无显示窗口，纯性能测试
- 记录实时FPS
- 自动统计平均/最大/最小FPS
- 输出详细性能报告

## API 文档

### HikCamera 类

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
2. **避免阻塞**: 主循环中不要进行耗时操作
3. **内存管理**: `read_latest()` 返回的是内部缓冲区引用，不要修改

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

### 回调模式架构
- SDK内部C线程直接回调，无需Python轮询
- 避免Python GIL锁竞争
- 事件驱动，延迟更低

### 内存优化
- 预分配转换缓冲区，避免每帧重复创建
- 使用`np.frombuffer`直接从缓冲区构建numpy数组
- `read_latest()` 返回内部缓冲区引用，避免额外拷贝
- `read()` 返回副本，适合需要保存帧的场景

### 缓存优化
- 设置`MV_CC_SetImageNodeNum(10)`增加SDK内部缓存节点
- 防止高帧率场景丢帧

## 性能指标

基于RK3588平台测试：

- **BGR模式**: 180-190 FPS（稳定）
- **首秒峰值**: 可达250 FPS（SDK缓存预热）
- **CPU占用**: 低（无Python线程轮询）

## 注意事项

1. 使用 `read_latest()` 时，返回的帧是内部缓冲区的引用，不要修改
2. 如需保存或修改帧，使用 `read()` 或手动 `copy()`
3. 程序退出前务必调用 `release()` 释放资源
4. GigE相机需要正确配置网络参数以达到最佳性能
