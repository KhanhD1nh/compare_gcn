from pathlib import Path
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from pdf_utils import extract_page2_to_base64
from llm_client import extract_gcn_with_llm
from gcn_validator import (
    validate_filename_format,
    extract_gcn_from_filename,
    normalize_gcn_number,
    compare_gcn
)


def process_single_pdf(pdf_path: Path, index: int) -> Dict:
    """
    Process a single PDF file: extract page 2, call LLM, compare
    
    Args:
        pdf_path: Path to PDF file
        index: Index
        
    Returns:
        Dict containing processing result
    """
    start = time.time()
    result = {
        "index": index,
        "pdf_file": pdf_path.name,
        "pdf_path": str(pdf_path),
        "filename_gcn": "",
        "predicted_gcn": "",
        "comparison": "",
        "status": "pending",
        "error": None,
        "time": 0
    }
    
    try:
        # Step 0: Validate filename format
        is_valid, error_msg = validate_filename_format(pdf_path.name)
        if not is_valid:
            result["status"] = "skip"
            result["error"] = f"Sai tên file: {error_msg}"
            result["comparison"] = "N/A"
            return result
        
        # Step 1: Extract GCN number from filename
        filename_gcn = extract_gcn_from_filename(pdf_path.name)
        result["filename_gcn"] = filename_gcn
        
        # Step 2: Extract page 2 to base64
        img_b64 = extract_page2_to_base64(pdf_path)
        if not img_b64:
            result["status"] = "skip"
            result["error"] = "No page 2"
            result["comparison"] = "N/A"
            return result
        
        # Step 3: Call LLM to extract GCN number
        predicted_gcn_raw, llm_error = extract_gcn_with_llm(img_b64)
        
        # Normalize predicted GCN
        if predicted_gcn_raw != "ERROR":
            predicted_gcn = normalize_gcn_number(predicted_gcn_raw)
        else:
            predicted_gcn = predicted_gcn_raw
        
        result["predicted_gcn"] = predicted_gcn
        
        # Step 4: Compare
        if predicted_gcn != "ERROR" and filename_gcn != "UNKNOWN":
            comparison = compare_gcn(filename_gcn, predicted_gcn)
            result["comparison"] = comparison
            result["status"] = "success"
        else:
            result["comparison"] = "N/A"
            result["status"] = "error"
            # Detailed error reason
            if predicted_gcn == "ERROR" and filename_gcn == "UNKNOWN":
                result["error"] = f"Both LLM and filename failed. LLM: {llm_error}"
            elif predicted_gcn == "ERROR":
                result["error"] = f"LLM extraction failed: {llm_error}. Filename GCN: {filename_gcn}"
            elif filename_gcn == "UNKNOWN":
                result["error"] = f"Cannot parse GCN from filename. LLM predicted: {predicted_gcn}"
            else:
                result["error"] = "Cannot extract GCN number"
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["comparison"] = "N/A"
    
    finally:
        result["time"] = time.time() - start
    
    return result


def process_batch_pdfs(
    pdf_files: List[Path],
    max_workers: int = 1
) -> List[Dict]:
    """
    Process batch of PDF files with multi-threading
    
    Args:
        pdf_files: List of PDF files to process
        max_workers: Number of parallel workers
        
    Returns:
        List of processing results
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_pdf, pdf, idx + 1): (pdf, idx + 1)
            for idx, pdf in enumerate(pdf_files)
        }
        
        for future in as_completed(futures):
            pdf_path, idx = futures[future]
            try:
                result = future.result()
                results.append(result)
                
                if result["status"] == "success":
                    status_icon = "✓" if result["comparison"] == "Đúng" else "⚠"
                    msg = f"{result['filename_gcn']} vs {result['predicted_gcn']} -> {result['comparison']}"
                elif result["status"] == "skip":
                    status_icon = "⚠"
                    msg = result.get('error', 'Skip')
                else:
                    status_icon = "✗"
                    msg = result.get('error', 'Error')
                
                print(f"{status_icon} [{result['time']:.2f}s] #{idx} {result['pdf_file']}: {msg}")
                
            except Exception as e:
                print(f"✗ {pdf_path.name}: Unexpected error - {e}")
    
    # Sort by index
    results.sort(key=lambda x: x["index"])
    return results

