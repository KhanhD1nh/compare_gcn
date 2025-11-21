from pathlib import Path
import time
from datetime import datetime

from config import Config
from pdf_utils import find_all_gcn_pdfs
from processor import process_batch_pdfs
from excel_exporter import export_to_excel


def main():
    """Main function"""  
    start_total = time.time()
    
    # Step 1: Find all GCN files (recursively)
    print(f"\n[1/4] Searching for GCN files in {Config.INPUT_DIR}...")
    gcn_files = find_all_gcn_pdfs(Config.INPUT_DIR)
    
    if not gcn_files:
        print("No GCN files found. Exiting program.")
        return
    
    # Step 2: Ask user how many files to process
    print(f"\nFound {len(gcn_files)} GCN files.")
    try:
        user_input = input(f"Enter the number of files to process (1-{len(gcn_files)}, Enter = all): ").strip()
        if user_input:
            batch_size = int(user_input)
            batch_size = min(max(1, batch_size), len(gcn_files))
        else:
            batch_size = len(gcn_files)
    except:
        batch_size = len(gcn_files)
    
    selected_files = gcn_files[:batch_size]
    print(f"-> Will process {len(selected_files)} files")
    
    # Step 3: Process batch
    print(f"\n[2/4] Processing {len(selected_files)} files with {Config.MAX_WORKERS} workers...")
    results = process_batch_pdfs(
        pdf_files=selected_files,
        max_workers=Config.MAX_WORKERS
    )
    
    # Step 4: Statistics
    print("\n[3/4] Statistics:")
    success = sum(1 for r in results if r["status"] == "success")
    skip = sum(1 for r in results if r["status"] == "skip")
    error = sum(1 for r in results if r["status"] == "error")
    
    # Classify reasons for skip
    skip_bad_filename = sum(1 for r in results if r["status"] == "skip" and "Sai tên file" in str(r.get("error", "")))
    skip_no_page2 = sum(1 for r in results if r["status"] == "skip" and "No page 2" in str(r.get("error", "")))
    
    correct = sum(1 for r in results if r["comparison"] == "Đúng")
    incorrect = sum(1 for r in results if r["comparison"] == "Cần hiệu đính")
    
    print(f"  Success: {success}")
    print(f"  Skip: {skip}")
    if skip_bad_filename > 0:
        print(f"    - Bad filename: {skip_bad_filename}")
    if skip_no_page2 > 0:
        print(f"    - No page 2: {skip_no_page2}")
    print(f"  Error: {error}")
    print(f"\n  Comparison:")
    print(f"    - Correct: {correct}")
    print(f"    - Need correction: {incorrect}")
    if success > 0:
        accuracy = (correct / success) * 100
        print(f"    - Accuracy: {accuracy:.2f}%")
    
    # Step 5: Export Excel
    print("\n[4/4] Exporting results to Excel...")
    timestamp = datetime.now().strftime("%Y%m%d")
    excel_file = Path(f"gcn_comparison_{timestamp}.xlsx")
    export_to_excel(results, excel_file)
    
    # Summary
    total_time = time.time() - start_total
    print("\n" + "=" * 80)
    print(f"COMPLETE - Total time: {total_time:.2f} seconds")
    if len(results) > 0:
        print(f"Average: {total_time / len(results):.2f} seconds/file")
    print(f"Excel file: {excel_file.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()

