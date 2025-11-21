from pathlib import Path
from typing import List, Dict
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment


def export_to_excel(results: List[Dict], output_path: Path):
    """
    Export results to Excel file
    
    Args:
        results: List of processing results
        output_path: Path to Excel output file
    """
    # Create new workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "GCN Comparison Results"
    
    # Header
    headers = ["Số thứ tự", "Tên tệp GCN", "Dự đoán", "Kết quả"]
    ws.append(headers)
    
    # Format header
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Add data
    for result in results:
        row = [
            result["index"],
            result["pdf_file"],
            result["predicted_gcn"],
            result["comparison"]
        ]
        ws.append(row)
    
    # Format result column
    for row_idx in range(2, len(results) + 2):
        cell = ws.cell(row=row_idx, column=4)
        if cell.value == "Đúng":
            cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            cell.font = Font(color="006100", bold=True)
        elif cell.value == "Cần hiệu đính":
            cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            cell.font = Font(color="9C6500", bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Center index column
    for row_idx in range(2, len(results) + 2):
        ws.cell(row=row_idx, column=1).alignment = Alignment(horizontal="center", vertical="center")
    
    # Automatically adjust column width
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save file
    wb.save(output_path)
    print(f"\nSaved results to {output_path}")

