# 水印嵌入代码改进

## 改进内容
- [x] 添加错误处理机制
  - 添加文件存在性检查
  - 添加异常处理
  - 确保输出目录存在
- [ ] 参数化水印嵌入强度（待实现）

## 具体改动
1. 在`convert_image`函数中：
   - 添加了文件存在性检查
   - 添加了异常处理机制
   - 使用`os.makedirs`确保输出目录存在

2. 在`embed_watermark_to_image`函数中：
   - 添加了完整的异常处理
   - 优化了代码结构
   - 确保输出目录存在

## 测试结果
- [x] 测试文件不存在的情况
- [x] 测试输出目录不存在的情况
- [x] 测试正常水印嵌入流程

## 使用示例
```python
# 正常使用
embed_watermark_to_image("original.jpg", "watermark.jpg", "result.jpg")

# 错误处理示例
try:
    embed_watermark_to_image("not_exist.jpg", "watermark.jpg", "result.jpg")
except Exception as e:
    print(f"错误信息: {str(e)}")
```

## 错误信息示例
- 文件不存在：`找不到图像文件: ./pictures/original.jpg`
- 图像处理错误：`图像处理过程中出错: [具体错误信息]`
- 水印嵌入错误：`水印嵌入过程中出错: [具体错误信息]`

## 后续计划
- [ ] 实现水印嵌入强度参数化
- [ ] 添加水印提取功能
- [ ] 添加水印鲁棒性测试

## 相关文件
- `watermarkHide.py`: 主要代码文件
- `pictures/`: 输入图像目录
- `dataset/`: 处理后的图像目录
- `result/`: 输出结果目录 