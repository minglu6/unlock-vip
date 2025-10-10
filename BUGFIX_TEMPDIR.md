# Bug修复: Windows临时目录路径问题

## 问题描述

在Windows系统上运行登录测试时，出现以下错误：

```
FileNotFoundError: [WinError 3] 系统找不到指定的路径。: '/tmp\\pw_user_data_5klnfcfz'
```

## 根本原因

在 `app/services/auth_service.py` 第86行，代码硬编码使用了Linux的临时目录路径：

```python
self.user_data_dir = tempfile.mkdtemp(prefix="pw_user_data_", dir="/tmp")
```

这在Windows上不起作用，因为：
- Windows的临时目录是：`C:\Users\<username>\AppData\Local\Temp`
- Linux的临时目录是：`/tmp`
- macOS的临时目录是：`/var/folders/...`

## 修复方案

移除硬编码的 `/tmp` 路径，让Python使用系统默认的临时目录：

### Before（修复前）
```python
self.user_data_dir = tempfile.mkdtemp(prefix="pw_user_data_", dir="/tmp")
```

### After（修复后）
```python
# 使用系统默认临时目录，跨平台兼容（Windows/Linux/Mac）
self.user_data_dir = tempfile.mkdtemp(prefix="pw_user_data_")
```

## 验证结果

运行测试脚本 `test_temp_dir_fix.py`：

```
Platform info:
  OS: win32
  Temp dir: C:\Users\luming2\AppData\Local\Temp

1. Test old way (with /tmp):
   [EXPECTED] Failed as expected

2. Test new way (system default):
   [PASS] Created successfully: C:\Users\luming2\AppData\Local\Temp\pw_user_data_se1k0vfb
   [PASS] Directory exists
   [PASS] Cleaned up successfully
```

## 影响范围

- ✅ Windows: 现在可以正常工作
- ✅ Linux: 不受影响（tempfile会自动使用/tmp）
- ✅ macOS: 不受影响（tempfile会自动使用系统临时目录）

## 相关文件

- 修复文件: [auth_service.py:87](d:\Projects\Personal\unlock-vip\app\services\auth_service.py#L87)
- 测试文件: [test_temp_dir_fix.py](d:\Projects\Personal\unlock-vip\test_temp_dir_fix.py)

## 最佳实践

在Python中创建临时目录/文件时，应该：

✅ **推荐**: 让Python自动选择临时目录
```python
import tempfile
temp_dir = tempfile.mkdtemp(prefix="myapp_")  # 跨平台
temp_file = tempfile.NamedTemporaryFile()     # 跨平台
```

❌ **不推荐**: 硬编码路径
```python
temp_dir = tempfile.mkdtemp(dir="/tmp")        # 仅Linux/Mac
temp_dir = tempfile.mkdtemp(dir="C:\\Temp")    # 仅Windows
```

## 总结

这是一个典型的跨平台兼容性问题。通过使用Python的标准库（tempfile）的默认行为，可以轻松实现跨平台兼容。

---

**修复日期**: 2025-10-10
**修复者**: Claude Code
