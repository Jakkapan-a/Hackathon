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

# ================ Input CSV File Names ================
INPUT_CSV_DOC_INFO = os.getenv("INPUT_CSV_DOC_INFO", "Test_doc_info.csv")
INPUT_CSV_NACC_DETAIL = os.getenv("INPUT_CSV_NACC_DETAIL", "Test_nacc_detail.csv")
INPUT_CSV_SUBMITTER = os.getenv("INPUT_CSV_SUBMITTER", "Test_submitter.csv")

# ================ Output File Prefix ================
OUTPUT_PREFIX = os.getenv("OUTPUT_PREFIX", "Train")  # Prefix for output CSV files (e.g., "Train", "Final")

# Construct full PDF path
PDF_DIR = os.path.join(INPUT_BASE_DIR, PDF_FOLDER)

# ================ Phase Skip Configuration ================
# Set to "true" to skip each phase (for debugging/testing)
SKIP_PHASE_1 = os.getenv("SKIP_PHASE_1", "false").lower() == "true"  # PDF to Image
SKIP_PHASE_2 = os.getenv("SKIP_PHASE_2", "false").lower() == "true"  # OCR Processing
SKIP_PHASE_3 = os.getenv("SKIP_PHASE_3", "false").lower() == "true"  # LLM Parsing (Text → JSON)
SKIP_PHASE_4 = os.getenv("SKIP_PHASE_4", "false").lower() == "true"  # JSON to CSV/Database
SKIP_PHASE_5 = os.getenv("SKIP_PHASE_5", "false").lower() == "true"  # Summary Generation

# ================ LLM Parser Configuration ================
# LLM parsing mode: "combined" (all pages at once) or "page_by_page" (parse each page then merge)
LLM_PARSE_MODE = os.getenv("LLM_PARSE_MODE", "page_by_page")
LLM_MAX_WORKERS = int(os.getenv("LLM_MAX_WORKERS", "5"))  # Parallel workers for page-by-page mode
LLM_PARALLEL_DOCS = int(os.getenv("LLM_PARALLEL_DOCS", "1"))  # Number of documents to process in parallel

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
    print(f"SKIP_PHASE_4: {SKIP_PHASE_4}")
    print(f"SKIP_PHASE_5: {SKIP_PHASE_5}")
    print(f"LLM_PARSE_MODE: {LLM_PARSE_MODE}")
    print(f"LLM_MAX_WORKERS: {LLM_MAX_WORKERS}")
    print(f"INPUT_CSV_DOC_INFO: {INPUT_CSV_DOC_INFO}")
    print(f"INPUT_CSV_NACC_DETAIL: {INPUT_CSV_NACC_DETAIL}")
    print(f"INPUT_CSV_SUBMITTER: {INPUT_CSV_SUBMITTER}")
    print(f"OUTPUT_PREFIX: {OUTPUT_PREFIX}")
    print("=================================================\n")

    # Load File doc info
    data = load_test_phase_csvs(
        base_dir=INPUT_BASE_DIR,
        csv_doc_info=INPUT_CSV_DOC_INFO,
        csv_nacc_detail=INPUT_CSV_NACC_DETAIL,
        csv_submitter=INPUT_CSV_SUBMITTER
    )
    print(f"Loaded {len(data['doc_info'])} document info records.")

    # =================== Phase 1: PDF to Image ===================
    print("\n=================== Phase 1: PDF to Image ===================")
    if SKIP_PHASE_1:
        print("[SKIP] Phase 1 SKIPPED (SKIP_PHASE_1=true)")
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

                os.makedirs(images_folder, exist_ok=True)
                print(f"Created folder: {output_folder}")
                print(f"Created subfolder: {images_folder}")
                # Remove * all files in images_folder
                for img_file in os.listdir(images_folder):
                    img_path = os.path.join(images_folder, img_file)
                    if os.path.isfile(img_path):
                        os.remove(img_path)
                        print(f"Removed old image file: {img_path}")

                # Extract PDF to images
                from src.pdf_to_image import pdf_to_images
                try:
                    pdf_to_images(path, images_folder)
                except Exception as e:
                    print(f"ERROR: Failed to convert PDF to images: {e}")
                    print(f"Skipping this PDF and continuing to next file...")

            else:
                print(f"File does not exist: {path}")

    # =================== Phase 2: OCR Processing ===================
    print("\n=================== Phase 2: Image to Text (OCR) ===================")
    if SKIP_PHASE_2:
        print("[SKIP] Phase 2 SKIPPED (SKIP_PHASE_2=true)")
    else:
        # Choose OCR method: 'ollama' or 'api'
        OCR_METHOD = os.getenv("OCR_METHOD", "ollama")  # default to ollama

        if OCR_METHOD == "api":
            from src.extract_text_from_image import extract_text_from_image as _ocr_function
            print("Using OpenTyphoon API for OCR")
        else:
            from src.extract_text_from_image_ollama_v2 import extract_text_from_image_ollama as _ocr_function
            print("Using Ollama for OCR")

        # Wrapper with retry logic for OCR
        def ocr_function(image_path, max_retries=5):
            """OCR with retry on rate limit or transient errors"""
            for attempt in range(max_retries):
                try:
                    return _ocr_function(image_path)
                except Exception as e:
                    error_str = str(e).lower()
                    # Check for rate limit or transient errors
                    if "rate limit" in error_str or "429" in error_str or "timeout" in error_str:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                            print(f"    ⚠ OCR rate limit/error, waiting {wait_time}s before retry ({attempt + 1}/{max_retries})...")
                            time.sleep(wait_time)
                        else:
                            raise e
                    else:
                        # Non-retryable error
                        raise e
            return None

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
                            print(f"[OK] OCR result already exists, skipping: {txt_path}")
                            continue

                        ocr_result = ocr_function(image_path)
                        
                        if ocr_result:

                            # Create output .txt file with same name as image
                            # Save OCR result to .txt file
                            with open(txt_path, 'w', encoding='utf-8') as f:
                                f.write(ocr_result)

                            print(f"[OK] Saved OCR result to: {txt_path}")

                            elapsed = time.time() - timeStart

                            print(f"Time: {elapsed:.2f} seconds, length: {len(ocr_result)} chars")
                            print("========= Time END =========")

                        else:
                            print(f"[ERR] OCR failed for: {image_file}")

                    except Exception as e:
                        print(f"[ERR] Error processing {image_file}: {e}")

            else:
                print(f"Images folder does not exist: {images_folder}")

    # =================== Phase 3: LLM Parsing (Text → JSON) ===================
    print("\n=================== Phase 3: Text to JSON (LLM Parsing) ===================")
    if SKIP_PHASE_3:
        print("[SKIP] Phase 3 SKIPPED (SKIP_PHASE_3=true)")
    else:
        # Initialize LLM Parser
        LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")
        print(f"Using LLM Model: {LLM_MODEL}")
        print(f"Parallel Documents: {LLM_PARALLEL_DOCS}")

        parser = LLMParser(model=LLM_MODEL, temperature=0.1)

        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        def process_single_document(doc_info):
            """Process a single document - used for parallel processing"""
            doc_id = str(doc_info['doc_id'])
            nacc_id = int(doc_info['nacc_id'])
            fileName = doc_info['doc_location_url']
            file_base_name = os.path.splitext(fileName)[0]

            # Get images folder path (where txt files are stored)
            images_folder = os.path.join(PDF_DIR, f"{file_base_name}_output", "images")

            # Check if JSON output already exists
            json_output_path = os.path.join(OUTPUT_DIR, f"{file_base_name}.json")
            if os.path.exists(json_output_path):
                return {"status": "skipped", "doc_id": doc_id, "message": "JSON already exists"}

            # Check if OCR txt files exist
            if not os.path.exists(images_folder):
                return {"status": "error", "doc_id": doc_id, "message": f"Images folder not found: {images_folder}"}

            txt_files = sorted([f for f in os.listdir(images_folder) if f.endswith('.txt')])
            if not txt_files:
                return {"status": "error", "doc_id": doc_id, "message": "No OCR txt files found"}

            # Parse document using LLM
            try:
                timeStart = time.time()

                # Use v2 parser with configurable mode
                parsed_data = parser.parse_document_from_files_v2(
                    images_folder, doc_id, nacc_id,
                    mode=LLM_PARSE_MODE,
                    max_workers=LLM_MAX_WORKERS
                )

                elapsed = time.time() - timeStart

                # Save JSON output
                with open(json_output_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_data, f, ensure_ascii=False, indent=2)

                return {
                    "status": "success",
                    "doc_id": doc_id,
                    "nacc_id": nacc_id,
                    "elapsed": elapsed,
                    "extraction_status": parsed_data.get('extraction_status', 'unknown'),
                    "confidence": parsed_data.get('confidence_score', 0),
                    "txt_files": len(txt_files)
                }

            except Exception as e:
                import traceback
                return {"status": "error", "doc_id": doc_id, "message": str(e), "traceback": traceback.format_exc()}

        # Process documents - either sequentially or in parallel
        if LLM_PARALLEL_DOCS <= 1:
            # Sequential processing (original behavior)
            for doc_info in data['doc_info']:
                doc_id = str(doc_info['doc_id'])
                nacc_id = int(doc_info['nacc_id'])
                print(f"\n--- Processing Document: {doc_id} (NACC: {nacc_id}) ---")

                result = process_single_document(doc_info)

                if result["status"] == "skipped":
                    print(f"[OK] {result['message']}")
                elif result["status"] == "error":
                    print(f"[ERR] {result['message']}")
                    if "traceback" in result:
                        print(result["traceback"])
                else:
                    print(f"[OK] LLM parsing completed in {result['elapsed']:.2f} seconds")
                    print(f"  Status: {result['extraction_status']}")
                    print(f"  Confidence: {result['confidence']:.2f}")
        else:
            # Parallel processing
            print(f"\n--- Processing {len(data['doc_info'])} documents in parallel (max {LLM_PARALLEL_DOCS} at a time) ---")

            with ThreadPoolExecutor(max_workers=LLM_PARALLEL_DOCS) as executor:
                # Submit all tasks
                future_to_doc = {executor.submit(process_single_document, doc_info): doc_info for doc_info in data['doc_info']}

                # Process completed tasks as they finish
                for future in as_completed(future_to_doc):
                    doc_info = future_to_doc[future]
                    doc_id = str(doc_info['doc_id'])
                    nacc_id = int(doc_info['nacc_id'])

                    try:
                        result = future.result()

                        if result["status"] == "skipped":
                            print(f"[SKIP] Doc {doc_id}: {result['message']}")
                        elif result["status"] == "error":
                            print(f"[ERR] Doc {doc_id}: {result['message']}")
                        else:
                            print(f"[OK] Doc {doc_id} (NACC: {nacc_id}): {result['elapsed']:.2f}s, Status: {result['extraction_status']}, Conf: {result['confidence']:.2f}")
                    except Exception as e:
                        print(f"[ERR] Doc {doc_id}: Exception - {e}")

    # =================== Phase 4: JSON to CSV/Database ===================
    print("\n=================== Phase 4: JSON to CSV/Database ===================")
    if SKIP_PHASE_4:
        print("[SKIP] Phase 4 SKIPPED (SKIP_PHASE_4=true)")
    else:
        # Create output directory and converter
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        converter = JSONToCSVConverter(OUTPUT_DIR)

        # Load input data for summary generation
        print("\n--- Loading Input Data ---")
        converter.load_input_data(
            INPUT_BASE_DIR,
            csv_doc_info=INPUT_CSV_DOC_INFO,
            csv_nacc_detail=INPUT_CSV_NACC_DETAIL,
            csv_submitter=INPUT_CSV_SUBMITTER
        )

        # Process documents using doc_info.csv as driver
        # This ensures correct doc_id and nacc_id mapping from doc_info.csv
        # instead of relying on potentially incorrect values in JSON files
        converter.process_from_doc_info(OUTPUT_DIR)

        # Save all CSV files
        print("\n--- Saving CSV Files ---")
        converter.save_all_csv(output_prefix=OUTPUT_PREFIX)

        # Save to SQLite database
        print("\n--- Saving to SQLite Database ---")
        enum_dir = os.path.join(os.path.dirname(INPUT_BASE_DIR), "enum_type")
        if not os.path.exists(enum_dir):
            enum_dir = "./enum_type"  # Fallback to relative path

        converter.save_to_sqlite(
            db_name="nacc_data.db",
            input_dir=INPUT_BASE_DIR,
            enum_dir=enum_dir,
            training_dir="./training/train output",
            import_external=True
        )

        print(f"[OK] Phase 4 completed. Output saved to: {OUTPUT_DIR}")

    # =================== Phase 5: Summary Generation ===================
    print("\n=================== Phase 5: Summary Generation ===================")
    if SKIP_PHASE_5:
        print("[SKIP] Phase 5 SKIPPED (SKIP_PHASE_5=true)")
    else:
        # Check if database exists
        db_path = os.path.join(OUTPUT_DIR, "nacc_data.db")
        if not os.path.exists(db_path):
            print(f"[ERR] Database not found: {db_path}")
            print("  Please run Phase 4 first to create the database.")
        else:
            # Create converter for running validation query
            converter = JSONToCSVConverter(OUTPUT_DIR)

            # Run validation query and export summary
            print("\n--- Running Validation Query (SQL) ---")
            converter.run_validation_query(
                db_name="nacc_data.db",
                output_csv="validation_summary.csv"
            )

            print(f"\n[OK] Phase 5 completed. Summary saved to: {OUTPUT_DIR}/validation_summary.csv")

    # =================== All Phases Completed ===================
    print("\n" + "=" * 60)
    print("                    All Phases Completed")
    print("=" * 60)
    print(f"\nOutput Directory: {OUTPUT_DIR}")
    print("\nGenerated Files:")
    print("  Phase 3: *.json (LLM parsed data)")
    print("  Phase 4: Train_*.csv, nacc_data.db")
    print("  Phase 5: validation_summary.csv")
    print("\nTo skip specific phases, set environment variables:")
    print("  SKIP_PHASE_1=true  (PDF to Image)")
    print("  SKIP_PHASE_2=true  (OCR)")
    print("  SKIP_PHASE_3=true  (LLM Parsing)")
    print("  SKIP_PHASE_4=true  (JSON to CSV/DB)")
    print("  SKIP_PHASE_5=true  (Summary)")
