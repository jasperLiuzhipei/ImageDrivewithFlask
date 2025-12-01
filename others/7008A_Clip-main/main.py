import os
import numpy as np
from clip_pipeline.processor import EmbeddingProcessor

# --- 创建一个假的测试图片 (或者你放一张真实的图片) ---
try:
    from PIL import Image
    TEST_IMAGE = 'test_image.jpg'
    if not os.path.exists(TEST_IMAGE):
        img = Image.new('RGB', (100, 100), color = 'blue')
        img.save(TEST_IMAGE)
except ImportError:
    print("请安装 Pillow (python3 -m pip install Pillow) 来创建测试图片。")
    exit()
# ---------------------------------------------------

def test_pipeline():
    print("--- 测试 EmbeddingProcessor ---")
    
    # 1. 初始化
    # 这会加载模型，第一次运行时较慢
    processor = EmbeddingProcessor()
    
    print(f"\n模型嵌入维度: {processor.embedding_dim}")

    # 2. 测试图像嵌入
    print(f"\n测试图像: {TEST_IMAGE}")
    image_vec = processor.embed_image(TEST_IMAGE)
    if image_vec is not None:
        print(f"✅ 图像嵌入成功。 形状: {image_vec.shape}")
        print(f"   (前5维): {image_vec[:5]}")
    else:
        print("❌ 图像嵌入失败。")

    # 3. 测试文本嵌入
    test_text = "a blue square"
    print(f"\n测试文本: '{test_text}'")
    text_vec = processor.embed_text(test_text)
    if text_vec is not None:
        print(f"✅ 文本嵌入成功。 形状: {text_vec.shape}")
        print(f"   (前5维): {text_vec[:5]}")
    else:
        print("❌ 文本嵌入失败。")
        
    # (可选) 清理测试图片
    # os.remove(TEST_IMAGE)

if __name__ == "__main__":
    test_pipeline()