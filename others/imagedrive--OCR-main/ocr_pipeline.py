import torch
from doctr.models import ocr_predictor
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import numpy as np
import logging
import time
from typing import Union, List 

# --- 1. 全局初始化 (只在启动时运行一次) ---
# 智能检测硬件
try:
    if torch.backends.mps.is_available():
        DEVICE = torch.device("mps")
    elif torch.cuda.is_available():
        DEVICE = torch.device("cuda")
    else:
        DEVICE = torch.device("cpu")
except Exception:
    DEVICE = torch.device("cpu")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # 💡 确保日志配置
logging.info(f"OCR Pipeline: Activating device: {DEVICE}") 

# 加载 doctr 模型
try:
    MODEL = ocr_predictor(
        "db_mobilenet_v3_large", "crnn_mobilenet_v3_large", pretrained=True
    ).to(DEVICE) 
    logging.info("OCR Pipeline: doctr model loaded successfully to GPU.")
except Exception as e:
    logging.error(f"Failed to load doctr model: {e}")
    MODEL = None

# --- 2. 图像预处理 ---
def _process_image_file(image_path: str):
    """从路径打开并预处理单个图像。"""
    try:
        image = Image.open(image_path).convert("RGB")
        image = np.array(image)
        return image
    except Exception as e:
        logging.error(f"Failed to process image {image_path}: {e}")
        return None

# --- 3. 结果后处理 (doctr 的过滤器) ---
def _process_page_result(page, ocr_threshold=0.3) -> Union[str, None]:
    """清理单个页面的 doctr OCR 结果。"""
    if page is None:
        return None
        
    try:
        text = " ".join(
            word.value
            for block in page.blocks
            for line in block.lines
            for word in line.words
            if word.confidence > ocr_threshold 
        )
    except Exception:
        text = "" 

    if not text or (not any(char.isalpha() for char in text) or len(text) < 3) \
       or all(len(word) == 1 for word in text.split() if word.isalpha()):
        return None
        
    return text.strip()

# --- 4. 对外暴露的接口函数 ---
def extract_text_from_image_path(image_path: str) -> Union[str, None]:
    """
    【给 Flask 负责人调用】处理单张图片（例如用户上传时）。
    """
    if MODEL is None:
        logging.error("OCR model is not loaded.")
        return None
        
    start_time = time.time()
    
    image_np = _process_image_file(image_path)
    if image_np is None:
        return None
    
    results = MODEL([image_np]) 
    
    text_result = _process_page_result(results.pages[0], ocr_threshold=0.3)
    
    end_time = time.time()
    logging.info(f"Processed single image {image_path} in {end_time - start_time:.2f}s")
    
    return text_result

def process_image_batch(image_paths: List[str], batch_size=32) -> List[Union[str, None]]:
    """
    【给你自己调用】并行处理一大批图片。
    """
    if MODEL is None:
        logging.error("OCR model is not loaded.")
        return [None] * len(image_paths)

    all_texts = []
    total_images = len(image_paths)
    # 💡 修复：更准确的总批次数计算
    total_batches = (total_images + batch_size - 1) // batch_size 

    logging.info(f"Starting batch processing: {total_images} images in {total_batches} batches.")

    for i in range(0, total_images, batch_size):
        batch_paths = image_paths[i : i + batch_size]
        current_batch_num = (i // batch_size) + 1
        
        # 💡 新增：阶段 1 日志
        logging.info(f"  Batch {current_batch_num}/{total_batches}: Pre-processing {len(batch_paths)} images (I/O)...")
        
        # 1. 并行预处理
        with ThreadPoolExecutor() as executor:
            images_np = list(executor.map(_process_image_file, batch_paths))
        
        valid_images = [img for img in images_np if img is not None]
        if not valid_images:
            all_texts.extend([None] * len(batch_paths))
            logging.warning(f"  Batch {current_batch_num}/{total_batches}: All images failed to load. Skipping.")
            continue

        # 2. 模型批量推理 (GPU 上的核心优势)
        # 💡 新增：阶段 2 日志
        logging.info(f"  Batch {current_batch_num}/{total_batches}: Running model on {len(valid_images)} images (GPU/MPS)...")
        batch_start_time = time.time()
        results = MODEL(valid_images)
        batch_end_time = time.time()
        # 💡 新增：阶段 3 日志 (带计时)
        logging.info(f"  Batch {current_batch_num}/{total_batches}: Model inference complete in {batch_end_time - batch_start_time:.2f}s.")

        # 3. 并行后处理
        # 💡 新增：阶段 4 日志
        logging.info(f"  Batch {current_batch_num}/{total_batches}: Post-processing results (CPU)...")
        with ThreadPoolExecutor() as executor:
            texts = list(executor.map(lambda page: _process_page_result(page, ocr_threshold=0.3), results.pages))
        
        text_iter = iter(texts)
        batch_results = []
        for img in images_np:
            if img is None:
                batch_results.append(None)
            else:
                batch_results.append(next(text_iter, None))
        
        all_texts.extend(batch_results)
        
    logging.info("Batch processing complete.")
    return all_texts