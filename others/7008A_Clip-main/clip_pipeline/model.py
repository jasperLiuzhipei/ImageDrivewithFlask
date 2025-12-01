import torch
from sentence_transformers import SentenceTransformer

def load_clip_model(model_name='clip-ViT-B-32'):
    """
    加载并返回一个预训练的 CLIP 模型。
    
    参数:
    model_name (str): 来自 sentence-transformers 的模型名称。
    
    返回:
    (model, device)
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"正在加载 CLIP 模型 '{model_name}' (使用设备: {device})")
    
    try:
        model = SentenceTransformer(model_name, device=device)
        print("CLIP 模型加载成功。")
        return model, device
    except Exception as e:
        print(f"错误: 无法加载模型 '{model_name}'.")
        print("请确保你已安装 'sentence-transformers' 并且模型名称正确。")
        print(f"详细错误: {e}")
        raise