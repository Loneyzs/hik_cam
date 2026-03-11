# 海康相机回调模式优化完成

## 优化内容

### 核心改动

1. **移除轮询线程** - 完全删除了`_capture_loop`方法和相关的线程管理代码
2. **实现回调机制** - 使用`MV_CC_RegisterImageCallBackEx2`注册回调函数
3. **预分配缓冲区** - 在`_create_callback`中预分配转换缓冲区，避免每帧重复创建
4. **增加缓存节点** - 设置`MV_CC_SetImageNodeNum(10)`防止高帧率丢帧
5. **优化内存拷贝** - 使用`np.frombuffer`直接从预分配缓冲区构建numpy数组

### 性能优势

- **无GIL竞争** - SDK内部C线程直接回调，不受Python GIL限制
- **事件驱动** - 无轮询延迟，图像到达立即处理
- **内存优化** - 预分配缓冲区，减少内存分配开销
- **自动释放** - SDK自动管理内存，无需手动释放

### 代码变化

**之前（轮询模式）**：
- Python线程循环调用`MV_CC_GetImageBuffer`
- 每帧创建新的转换缓冲区
- 需要手动调用`MV_CC_FreeImageBuffer`
- 受Python GIL限制

**现在（回调模式）**：
- SDK内部线程自动回调
- 预分配转换缓冲区复用
- SDK自动释放内存（bAutoFree=True）
- 无GIL竞争

## 测试方法

### 1. 快速验证

```bash
cd /home/loneyzs/code/hik_cam
python3 verify_callback.py
```

这将运行5秒测试，验证：
- 回调是否正常工作
- 图像是否正确采集
- FPS是否达到预期

### 2. 性能测试

```bash
cd /home/loneyzs/code/hik_cam/tests
python3 test_fps.py
```

选择BGR或灰度模式，运行10秒性能测试，输出详细统计。

### 3. 实时监看

```bash
cd /home/loneyzs/code/hik_cam/tests
python3 test_live_view.py
```

实时显示相机画面和FPS。

## 预期性能

根据SDK官方示例和优化方案：

- **BGR模式**: 230-248 FPS（之前120 FPS）
- **灰度模式**: 240-250 FPS（单通道，数据量更小）
- **CPU占用**: 降低（无Python线程轮询）

## 文件清单

### 修改的文件
- `/home/loneyzs/code/hik_cam/hik_camera.py` - 核心类，完全重构为回调模式

### 新增的文件
- `/home/loneyzs/code/hik_cam/verify_callback.py` - 快速验证脚本

### 未修改的文件
- `/home/loneyzs/code/hik_cam/tests/test_fps.py` - 性能测试（接口兼容）
- `/home/loneyzs/code/hik_cam/tests/test_live_view.py` - 实时监看（接口兼容）

## 关键技术点

### 1. 回调函数签名

```python
CALLBACK_TYPE = get_callback_functype()(None, POINTER(MV_FRAME_OUT), c_void_p, c_bool)
```

- 返回值：None
- 参数1：POINTER(MV_FRAME_OUT) - 图像帧信息
- 参数2：c_void_p - 用户自定义数据
- 参数3：c_bool - 是否自动释放

### 2. 预分配缓冲区

```python
max_buffer_size = 4096 * 3072 * channels
self._convert_buffer = (c_ubyte * max_buffer_size)()
```

按最大分辨率预分配，避免每帧创建。

### 3. 闭包捕获

```python
cam_ref = self
convert_param = self._convert_param
convert_buffer = self._convert_buffer

def image_callback(pstFrame, pUser, bAutoFree):
    # 使用闭包捕获的变量
    ret = cam_ref.cam.MV_CC_ConvertPixelTypeEx(convert_param)
```

确保回调函数能访问类成员。

## 注意事项

1. **回调函数必须快速返回** - 不要在回调中执行耗时操作
2. **线程安全** - 使用锁保护共享数据（`_latest_frame`）
3. **内存管理** - bAutoFree=True时SDK自动释放，无需手动调用FreeImageBuffer
4. **缓冲区大小** - 预分配缓冲区按4096x3072最大分辨率，如需更大请调整

## 下一步

如果性能仍不满足要求，可以考虑：

1. **跳过像素转换** - 直接使用Bayer原始数据（需要修改后续处理）
2. **降低分辨率** - 减少数据量
3. **调整曝光时间** - 减少曝光时间可提高帧率
4. **使用硬件加速** - 如果RK3588有硬件解码器，可以利用

## 参考

- SDK示例：`/opt/MVS/Samples/aarch64/Python/General/Grab_Callback/Grab_Callback.py`
- 优化计划：`/home/loneyzs/.claude/plans/rippling-wibbling-spark.md`
