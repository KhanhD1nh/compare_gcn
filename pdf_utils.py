"""PDF processing utilities"""

from pathlib import Path
from PIL import Image
import fitz
import base64
from io import BytesIO
from typing import List, Optional

from config import Config


def find_all_gcn_pdfs(root_dir: Path) -> List[Path]:
    """
    Find all PDF files containing 'GCN' in the name (recursively)
    
    Args:
        root_dir: Root directory to search
        
    Returns:
        List of PDF file paths
    """
    gcn_files = sorted(root_dir.rglob('*GCN*.pdf'))
    print(f"Found {len(gcn_files)} GCN files in {root_dir}")
    return gcn_files


def extract_page2_to_base64(pdf_path: Path) -> Optional[str]:
    """
    Extract page 2 of PDF to base64 (without saving file)
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Base64 string of image, or None if error
    """
    try:
        with fitz.open(pdf_path) as doc:
            if doc.page_count < 2:
                return None
            
            # Get page 2 (index 1)
            page = doc.load_page(1)
            pix = page.get_pixmap(dpi=Config.RENDER_DPI)
            img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
            gray_img = img.convert('L')
            
            # If image is horizontal, cut in half and keep right half
            if gray_img.width > gray_img.height:
                mid_x = gray_img.width // 2
                gray_img = gray_img.crop((mid_x, 0, gray_img.width, gray_img.height))
            
            # Convert to base64
            buffer = BytesIO()
            gray_img.save(buffer, format='PNG')
            img_bytes = buffer.getvalue()
            img_b64 = base64.b64encode(img_bytes).decode('utf8')
            
            return img_b64
            
    except Exception as e:
        print(f"✗ Error processing {pdf_path.name}: {e}")
        return None

