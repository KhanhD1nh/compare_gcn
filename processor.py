from pathlib import Path
import time
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from pdf_utils import extract_page2_to_base64
from llm_client import extract_gcn_with_llm
from gcn_validator import (
    validate_filename_format,
    extract_gcn_from_filename,
    normalize_gcn_number,
    compare_gcn
)
from processed_cache import ProcessedCache


def process_single_pdf(
    pdf_path: Path, 
    index: int, 
    llm_url: str = None, 
    api_timeout: int = None,
    cache: Optional[ProcessedCache] = None,
    skip_processed: bool = True
) -> Dict:
    """
    Process a single PDF file: extract page 2, call LLM, compare
    
    Args:
        pdf_path: Path to PDF file
        index: Index
        llm_url: LLM API URL (optional)
        api_timeout: API timeout in seconds (optional)
        cache: ProcessedCache instance (optional)
        skip_processed: Skip already processed files (default: True)
        
    Returns:
        Dict containing processing result
    """
    start = time.time()
    
    # Check cache if enabled
    if cache and skip_processed and cache.is_processed(pdf_path):
        cached_result = cache.get_processed_result(pdf_path)
        result = {
            "index": index,
            "pdf_file": pdf_path.name,
            "pdf_path": str(pdf_path),
            "filename_gcn": cached_result.get("filename_gcn", ""),
            "predicted_gcn": cached_result.get("predicted_gcn", ""),
            "comparison": cached_result.get("comparison", ""),
            "status": "cached",
            "error": cached_result.get("error"),
            "time": 0,
            "from_cache": True,
            "processed_at": cached_result.get("processed_at", "")
        }
        return result
    
    result = {
        "index": index,
        "pdf_file": pdf_path.name,
        "pdf_path": str(pdf_path),
        "filename_gcn": "",
        "predicted_gcn": "",
        "comparison": "",
        "status": "pending",
        "error": None,
        "time": 0,
        "from_cache": False
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
        predicted_gcn_raw, llm_error = extract_gcn_with_llm(img_b64, llm_url, api_timeout)
        
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
        
        # Save to cache if processing was successful or skipped
        if cache and result["status"] in ["success", "skip", "error"]:
            cache.add_processed(pdf_path, result)
    
    return result


def process_batch_pdfs(
    pdf_files: List[Path],
    max_workers: int = 1,
    llm_url: str = None,
    api_timeout: int = None,
    cache: Optional[ProcessedCache] = None,
    skip_processed: bool = True
) -> List[Dict]:
    """
    Process batch of PDF files with multi-threading
    
    Args:
        pdf_files: List of PDF files to process
        max_workers: Number of parallel workers
        llm_url: LLM API URL (optional)
        api_timeout: API timeout in seconds (optional)
        cache: ProcessedCache instance (optional)
        skip_processed: Skip already processed files (default: True)
        
    Returns:
        List of processing results
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_pdf, pdf, idx + 1, llm_url, api_timeout, cache, skip_processed): (pdf, idx + 1)
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

