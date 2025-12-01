import glob
import json
from ocr_pipeline import process_image_batch
import ocr_pipeline  # 💡 新增：导入整个 ocr_pipeline 以便访问 DEVICE
import time
import os
import logging

# --- 设置 ---
DATASET_PATH = "./image/**/*.jpg"  # 💡 重要：我假设您的图片在子文件夹中
OUTPUT_FILE = "ocr_metadata.json"
# 为 M4 GPU 设置一个合理的批处理大小
BATCH_SIZE = 64 

# (确保日志能正常输出)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("============================================")
    logging.info("Starting main OCR pipeline...")
    logging.info("============================================")
    
    # 1. 查找所有图片
    logging.info(f"Step 1: Searching for images in {DATASET_PATH}...")
    image_paths = glob.glob(DATASET_PATH, recursive=True) 
    if not image_paths:
        logging.error(f"Error: No images found at {DATASET_PATH}. Check path?")
        return
        
    total_images = len(image_paths)
    logging.info(f"Step 1: Complete. Found {total_images} images to process.")

    
    # 2. 运行批量 OCR
    # 💡 新增：打印将使用的硬件
    logging.info(f"Step 2: Starting OCR batch processing (Batch Size: {BATCH_SIZE})...")
    logging.info(f"       Using hardware device: {ocr_pipeline.DEVICE}")
    
    start_time = time.time()
    ocr_texts = process_image_batch(image_paths, batch_size=BATCH_SIZE)
    end_time = time.time()
    
    # 💡 修改：更清晰的完成日志
    logging.info(f"Step 2: Complete. OCR processing finished in {end_time - start_time:.2f} seconds.")

    
    # 3. 保存结果
    logging.info(f"Step 3: Saving results to {OUTPUT_FILE}...") # 💡 新增
    metadata = {}
    valid_text_count = 0
    for path, text in zip(image_paths, ocr_texts):
        filename = os.path.basename(path) 
        metadata[filename] = text
        if text:
            valid_text_count += 1
            
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
        
    # 💡 修改：更清晰的总结
    logging.info(f"Step 3: Complete. Successfully saved metadata.")
    logging.info("============================================")
    logging.info("Final Summary:")
    logging.info(f"  Total images processed: {total_images}")
    logging.info(f"  Images with text found: {valid_text_count}")
    logging.info(f"  Output file: {OUTPUT_FILE}")
    logging.info("============================================")


if __name__ == "__main__":
    main()