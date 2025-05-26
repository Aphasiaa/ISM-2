from QRCodeGenerator import *
import io
import sys
from PIL import Image

# 全部测试用例列表
TESTS = []

def register(fn):
    TESTS.append(fn)
    return fn

@register
def test_allowed_file_various_extensions():
    cases = [
        ("test.png", True),
        ("test.jpg", True),
        ("test.jpeg", True),
        ("test.gif", True),
        ("test.bmp", False),
        ("noext", False),
    ]
    for filename, expected in cases:
        assert allowed_file(filename) is expected, f"{filename} 期望 {expected}"

@register
def test_is_image_with_valid_image():
    # 生成一个 10×10 白色 PNG
    img = Image.new("RGB", (10, 10), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()
    assert is_image(data) is True, "合法图片应返回 True"

@register
def test_is_image_with_invalid_image():
    fake = b"not an image"
    assert is_image(fake) is False, "非图片数据应返回 False"
    
@register
def test_valid_image_with_invalid_extension():
    """
    模拟一个文件名扩展名不被允许（如 .txt），但文件内容确实是合法图片的场景。
    - is_image 应该返回 True（文件内容为图片）
    - allowed_file 应该返回 False（.bmp 不在 ALLOWED_EXTENSIONS 列表中）
    """
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建相对于脚本的路径
    file_path = os.path.join(script_dir, 'test.txt')
    
    # 读取一个合法的 PNG 图像字节
    with open(file_path,'rb') as file:
        # 校验文件内容：应当识别为图片
        assert is_image(file.read()) is True, "文件内容是图片，应当被 is_image 识别"

    # 校验扩展名：.bmp 不在 ALLOWED_EXTENSIONS 中，应当被拒绝
    assert allowed_file("test.txt") is False, "bmp 扩展名不被允许，应当拒绝"

@register
def test_invalid_content_with_valid_extension():
    """
    模拟文件扩展名合法（.png），但文件内容并非图片的场景：
    - allowed_file 应当返回 True
    - is_image 应当返回 False
    """
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建相对于脚本的路径
    file_path = os.path.join(script_dir, 'test.png')
    
    # 读取一个非法的 txt 文本字节
    with open(file_path,'rb') as file:
        # 校验文件内容：应当识别为图片
        assert is_image(file.read()) is False, "非图片内容应被 is_image 拒绝"

    # 校验扩展名：.bmp 不在 ALLOWED_EXTENSIONS 中，应当被拒绝
    assert allowed_file("test.png") is True,  "扩展名 .png 应被允许"

def main():
    total = len(TESTS)
    passed = 0
    print(f"运行 {total} 个测试用例...\n")
    for fn in TESTS:
        name = fn.__name__
        try:
            fn()
            print(f"[PASS] {name}")
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {name}: {e}")
        except Exception as e:
            print(f"[ERROR] {name}: 未预期异常 {e!r}")
    print(f"\n测试完成：{passed}/{total} 通过，{total-passed} 失败。")
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()