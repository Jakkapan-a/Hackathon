import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.load_test_doc import load_test_phase_csvs

if __name__ == "__main__":
    # Load File doc info
    data = load_test_phase_csvs()
    print(f"Loaded {len(data['doc_info'])} document info records.")
    print("=================== Phase 1 Coversion PDF to Image ===================")
    for doc_info in data['doc_info']:
        print(f"{doc_info['doc_id']}, {doc_info['doc_location_url']}, {doc_info['type_id']}, {doc_info['nacc_id']}")
        # Get file info in doc_location_url
        fileName = doc_info['doc_location_url']
        # File path .\test phase 1\test phase 1 input\Test_pdf\pdf\[filename.pdf]
        path = f".\\test phase 1\\test phase 1 input\\Test_pdf\\pdf\\{fileName}"
        print(f"File path: {path}")
        # Get Information about the file
        if os.path.exists(path):
            file_info = os.stat(path)
            print(f"File Size: {file_info.st_size} bytes")
            print(f"Last Modified: {file_info.st_mtime}")

            # Create Folder [fileName] + "_output"
            # ตัดนามสกุล .pdf ออกจาก fileName
            file_base_name = os.path.splitext(fileName)[0]
            # สร้าง output_folder ใน path เดียวกับ PDF
            pdf_dir = os.path.dirname(path)
            output_folder = os.path.join(pdf_dir, f"{file_base_name}_output")
            images_folder = os.path.join(output_folder, "images")

            # สร้าง folder
            
            # os.makedirs(images_folder, exist_ok=True)
            # print(f"Created folder: {output_folder}")
            # print(f"Created subfolder: {images_folder}")
            # # Remove * all files in images_folder
            # for img_file in os.listdir(images_folder):
            #     img_path = os.path.join(images_folder, img_file)
            #     if os.path.isfile(img_path):
            #         os.remove(img_path)
            #         print(f"Removed old image file: {img_path}")
            #
            # # Extract PDF to images
            # from src.pdf_to_image import pdf_to_images
            # try:
            #     pdf_to_images(path, images_folder)
            # except Exception as e:
            #     print(f"ERROR: Failed to convert PDF to images: {e}")
            #     print(f"Skipping this PDF and continuing to next file...")

        else:
            print(f"File does not exist: {path}")
            
    print("=================== Phase 2 OCR Processing ===================")
    # Choose OCR method: 'ollama' or 'api'
    OCR_METHOD = os.getenv("OCR_METHOD", "ollama")  # default to ollama

    if OCR_METHOD == "api":
        from src.extract_text_from_image import extract_text_from_image as ocr_function
        print("Using OpenTyphoon API for OCR")
    else:
        from src.extract_text_from_image_ollama_v2 import extract_text_from_image_ollama as ocr_function
        print("Using Ollama for OCR")

    for doc_info in data['doc_info']:
        print(f"Processing OCR for Document ID: {doc_info['doc_id']}")

        # Get all images from the corresponding output folder
        fileName = doc_info['doc_location_url']
        file_base_name = os.path.splitext(fileName)[0]
        pdf_dir = os.path.dirname(f".\\test phase 1\\test phase 1 input\\Test_pdf\\pdf\\{fileName}")
        images_folder = os.path.join(pdf_dir, f"{file_base_name}_output", "images")
        print(f"Looking for images in folder: {images_folder}")

        if os.path.exists(images_folder):
            # Get all image files and sort them
            image_files = sorted([f for f in os.listdir(images_folder)
                                if os.path.isfile(os.path.join(images_folder, f))
                                and f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            print(f"Found {len(image_files)} images for OCR processing.")

            for image_file in image_files:
                image_path = os.path.join(images_folder, image_file)

                # Call OCR function (either Ollama or API based on OCR_METHOD)
                try:
                    print("========= Time Taken for OCR =========")
                    print(f"Processing OCR for image: {image_path}")
                    timeStart = time.time()
                    txt_filename = os.path.splitext(image_file)[0] + ".txt"
                    txt_path = os.path.join(images_folder, txt_filename)
                    # continue if txt_path already exists
                    if os.path.exists(txt_path):
                        print(f"✓ OCR result already exists, skipping: {txt_path}")
                        continue

                    ocr_result = ocr_function(image_path)


                    if ocr_result:

                        # Create output .txt file with same name as image
                        # Save OCR result to .txt file
                        with open(txt_path, 'w', encoding='utf-8') as f:
                            f.write(ocr_result)

                        print(f"✓ Saved OCR result to: {txt_path}")

                        elapsed = time.time() - timeStart

                        print(f"Time: {elapsed:.2f} seconds, length: {len(ocr_result)} chars")
                        print("========= Time END =========")

                    else:
                        print(f"✗ OCR failed for: {image_file}")

                except Exception as e:
                    print(f"✗ Error processing {image_file}: {e}")

        else:
            print(f"Images folder does not exist: {images_folder}")
