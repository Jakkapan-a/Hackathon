import os
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from src.load_test_doc import load_test_phase_csvs
from src.llm_parser import LLMParser
from src.json_to_csv import JSONToCSVConverter

load_dotenv()

# ================ Path Configuration ================
INPUT_BASE_DIR = os.getenv("INPUT_BASE_DIR", "./test phase 1/test phase 1 input")
PDF_FOLDER = os.getenv("PDF_FOLDER", "Test_pdf/pdf")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./test phase 1/test phase 1 output")

# Construct full PDF path
PDF_DIR = os.path.join(INPUT_BASE_DIR, PDF_FOLDER)

# ================ Phase Skip Configuration ================
# Set to "true" to skip each phase (for debugging/testing)
SKIP_PHASE_1 = os.getenv("SKIP_PHASE_1", "false").lower() == "true"  # PDF to Image
SKIP_PHASE_2 = os.getenv("SKIP_PHASE_2", "false").lower() == "true"  # OCR Processing
SKIP_PHASE_3 = os.getenv("SKIP_PHASE_3", "false").lower() == "true"  # LLM Parsing

if __name__ == "__main__":
    # Print configuration
    print("================= Configuration =================")
    print(f"INPUT_BASE_DIR: {INPUT_BASE_DIR}")
    print(f"PDF_FOLDER: {PDF_FOLDER}")
    print(f"PDF_DIR: {PDF_DIR}")
    print(f"OUTPUT_DIR: {OUTPUT_DIR}")
    print(f"SKIP_PHASE_1: {SKIP_PHASE_1}")
    print(f"SKIP_PHASE_2: {SKIP_PHASE_2}")
    print(f"SKIP_PHASE_3: {SKIP_PHASE_3}")
    print("=================================================\n")

    # Load File doc info
    data = load_test_phase_csvs(base_dir=INPUT_BASE_DIR)
    print(f"Loaded {len(data['doc_info'])} document info records.")

    # =================== Phase 1: PDF to Image ===================
    print("=================== Phase 1 Coversion PDF to Image ===================")
    if SKIP_PHASE_1:
        print("⏭️  Phase 1 SKIPPED (SKIP_PHASE_1=true)")
    else:
        for doc_info in data['doc_info']:
            print(f"{doc_info['doc_id']}, {doc_info['doc_location_url']}, {doc_info['type_id']}, {doc_info['nacc_id']}")
            # Get file info in doc_location_url
            fileName = doc_info['doc_location_url']
            # File path using configured PDF_DIR
            path = os.path.join(PDF_DIR, fileName)
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

                # สร้าง folder command

                # os.makedirs(images_folder, exist_ok=True)
                # print(f"Created folder: {output_folder}")
                # print(f"Created subfolder: {images_folder}")
                # # Remove * all files in images_folder
                # for img_file in os.listdir(images_folder):
                #     img_path = os.path.join(images_folder, img_file)
                #     if os.path.isfile(img_path):
                #         os.remove(img_path)
                #         print(f"Removed old image file: {img_path}")

                # # Extract PDF to images
                # from src.pdf_to_image import pdf_to_images
                # try:
                #     pdf_to_images(path, images_folder)
                # except Exception as e:
                #     print(f"ERROR: Failed to convert PDF to images: {e}")
                #     print(f"Skipping this PDF and continuing to next file...")

            else:
                print(f"File does not exist: {path}")

    # =================== Phase 2: OCR Processing ===================
    print("=================== Phase 2 OCR Processing ===================")
    if SKIP_PHASE_2:
        print("⏭️  Phase 2 SKIPPED (SKIP_PHASE_2=true)")
    else:
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
            images_folder = os.path.join(PDF_DIR, f"{file_base_name}_output", "images")
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

    # =================== Phase 3: LLM Parsing ===================
    print("=================== Phase 3 LLM Parsing(Text → Structured Data) ===================")
    if SKIP_PHASE_3:
        print("⏭️  Phase 3 SKIPPED (SKIP_PHASE_3=true)")
    else:
        # Initialize LLM Parser and CSV Converter
        LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")
        print(f"Using LLM Model: {LLM_MODEL}")

        parser = LLMParser(model=LLM_MODEL, temperature=0.1)

        # Create output directory (using configured OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        converter = JSONToCSVConverter(OUTPUT_DIR)

        # Process each document
        for doc_info in data['doc_info']:
            doc_id = str(doc_info['doc_id'])
            nacc_id = int(doc_info['nacc_id'])
            fileName = doc_info['doc_location_url']
            file_base_name = os.path.splitext(fileName)[0]

            print(f"\n--- Processing Document: {doc_id} (NACC: {nacc_id}) ---")

            # Get images folder path (where txt files are stored)
            images_folder = os.path.join(PDF_DIR, f"{file_base_name}_output", "images")

            # Check if JSON output already exists
            json_output_path = os.path.join(OUTPUT_DIR, f"{file_base_name}.json")
            if os.path.exists(json_output_path):
                print(f"✓ JSON output already exists, loading: {json_output_path}")
                with open(json_output_path, 'r', encoding='utf-8') as f:
                    parsed_data = json.load(f)
                converter.process_document(parsed_data)
                continue

            # Check if OCR txt files exist
            if not os.path.exists(images_folder):
                print(f"✗ Images folder not found: {images_folder}")
                continue

            txt_files = sorted([f for f in os.listdir(images_folder) if f.endswith('.txt')])
            if not txt_files:
                print(f"✗ No OCR txt files found in: {images_folder}")
                continue

            print(f"Found {len(txt_files)} OCR text files")

            # Parse document using LLM
            try:
                print(f"Calling LLM to parse document...")
                timeStart = time.time()

                parsed_data = parser.parse_document_from_files(images_folder, doc_id, nacc_id)

                elapsed = time.time() - timeStart
                print(f"✓ LLM parsing completed in {elapsed:.2f} seconds")
                print(f"  Status: {parsed_data.get('extraction_status', 'unknown')}")
                print(f"  Confidence: {parsed_data.get('confidence_score', 0):.2f}")

                # Save JSON output
                converter.save_json(parsed_data, f"{file_base_name}.json")

                # Process for CSV
                converter.process_document(parsed_data)

            except Exception as e:
                print(f"✗ Error parsing document {doc_id}: {e}")
                import traceback
                traceback.print_exc()
                continue

        # Save all CSV files
        print("\n=================== Saving CSV Output Files ===================")
        converter.save_all_csv()
        print(f"\n✓ All output files saved to: {OUTPUT_DIR}")

    print("\n=================== All Phases Completed ===================")
