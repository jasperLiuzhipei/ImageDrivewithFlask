from PIL import Image
import numpy as np
from .model import load_clip_model

class EmbeddingProcessor:
    """
    一个封装了 CLIP 嵌入功能的处理器。
    
    这是交付给 Flask 团队的核心接口。
    """
    
    def __init__(self, model_name='clip-ViT-B-32'):
        """
        初始化处理器并加载模型。
        这应该在 Flask 服务器启动时被调用一次。
        """
        self.model, self.device = load_clip_model(model_name)
        # 获取嵌入向量的维度 (e.g., 512)
        try:
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
        except Exception:
            # 兼容老版本或其他模型接口
            self.embedding_dim = None

    def embed_image(self, image_path):
        """
        为单张图片生成嵌入向量（“在线”处理）。
        
        参数:
        image_path (str): 图像文件的路径
        
        返回:
        np.array: 图像的嵌入向量
        """
        try:
            pil_image = Image.open(image_path).convert("RGB")
            embedding = self.model.encode(pil_image, convert_to_numpy=True)
            return embedding
        except Exception as e:
            print(f"处理图像失败 {image_path}: {e}")
            return None

    def embed_text(self, text_query):
        """
        为文本查询生成嵌入向量。
        
        参数:
        text_query (str): 用户的搜索词，例如 "a dog on the beach"
        
        返回:
        np.array: 文本的嵌入向量
        """
        try:
            embedding = self.model.encode(text_query, convert_to_numpy=True)
            return embedding
        except Exception as e:
            print(f"处理文本失败 '{text_query}': {e}")
            return None
            
    def embed_batch(self, image_paths, batch_size=32):
        """
        批量处理图像列表（“离线”处理）。
        
        参数:
        image_paths (list): 图像文件路径的列表
        batch_size (int): 一次处理多少张图片
        
        返回:
        np.array: 包含所有嵌入的 NumPy 数组，形状为 (num_images, embedding_dim)
        """
        print(f"开始批量嵌入 {len(image_paths)} 张图片 (批大小: {batch_size})...")
        try:
            # 批量打开所有图片并确保为 RGB
            pil_images = [Image.open(path).convert("RGB") for path in image_paths]
            
            all_embeddings = self.model.encode(
                pil_images, 
                batch_size=batch_size, 
                convert_to_numpy=True,
                show_progress_bar=True
            )
            return all_embeddings
        except Exception as e:
            print(f"批量处理失败: {e}")
            return None