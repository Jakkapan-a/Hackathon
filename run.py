from src.load_test_doc import load_test_phase_csvs

if __name__ == "__main__":
    # Load File doc info
    data = load_test_phase_csvs()
    print(f"Loaded {len(data['doc_info'])} document info records.")
    for doc_info in data['doc_info']:
        print(f"{doc_info['doc_id']}, {doc_info['doc_location_url']}, {doc_info['type_id']}, {doc_info['nacc_id']}")
        # Get file info in doc_location_url
        fileName = {doc_info['doc_location_url']}
        # File path .\test phase 1\test phase 1 input\Test_pdf\pdf\[filename.pdf]
        

