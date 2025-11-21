import streamlit as st
from pathlib import Path
from datetime import datetime
import pandas as pd
import time

from pdf_utils import find_all_gcn_pdfs
from processor import process_batch_pdfs
from excel_exporter import export_to_excel
from config import Config


def main():
    st.set_page_config(
        page_title="GCN Comparison Tool",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("🔍 GCN Comparison Tool")
    st.markdown("Công cụ so sánh số Giấy Chứng Nhận (GCN) từ file PDF với dự đoán từ AI")
    
    # Main area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Input folder path with search button
        st.subheader("📁 Đường dẫn thư mục chứa file GCN")
        
        # Use form to enable Enter key submission
        with st.form(key="search_form", clear_on_submit=False):
            col_path, col_btn = st.columns([4, 1])
            
            with col_path:
                folder_path = st.text_input(
                    "Nhập đường dẫn đầy đủ:",
                    value=str(Config.INPUT_DIR),
                    placeholder="Ví dụ: C:\\Users\\YourName\\Documents\\GCN_Files",
                    help="Đường dẫn đến thư mục chứa các file PDF GCN",
                    label_visibility="collapsed"
                )
            
            with col_btn:
                search_button = st.form_submit_button("🔎 Tìm kiếm", type="primary", use_container_width=True)
        
        # Configuration section
        st.subheader("⚙️ Cấu hình")
        
        # LLM URL configuration
        llm_url = st.text_input(
            "🌐 URL của LLM API:",
            value=Config.LM_URL,
            placeholder="http://192.168.1.69:1234/v1/chat/completions",
            help="Địa chỉ URL của LLM API endpoint"
        )
        
        # Number of workers configuration
        col_config1, col_config2 = st.columns(2)
        with col_config1:
            max_workers = st.number_input(
                "⚡ Số luồng xử lý song song:",
                min_value=1,
                max_value=20,
                value=Config.MAX_WORKERS,
                step=1,
                help="Số lượng file được xử lý đồng thời"
            )
        with col_config2:
            api_timeout = st.number_input(
                "⏱️ Timeout (giây):",
                min_value=10,
                max_value=300,
                value=Config.API_TIMEOUT,
                step=10,
                help="Thời gian chờ tối đa cho mỗi request API"
            )
        
        # Find GCN files when search button is clicked or Enter is pressed
        if search_button:
            input_dir = Path(folder_path)
            
            # Check if folder exists
            if not input_dir.exists():
                st.error(f"❌ Thư mục không tồn tại: {folder_path}")
                st.info("💡 Vui lòng kiểm tra lại đường dẫn thư mục")
            else:
                with st.spinner("Đang tìm kiếm file GCN..."):
                    gcn_files = find_all_gcn_pdfs(input_dir)
                    st.session_state.gcn_files = gcn_files
                    st.session_state.input_dir = input_dir  # Save input_dir to session
                    st.session_state.folder_scanned = True
        
        # Display found files
        if hasattr(st.session_state, 'folder_scanned') and st.session_state.folder_scanned:
            gcn_files = st.session_state.gcn_files
            input_dir = st.session_state.input_dir  # Retrieve input_dir from session
            
            if not gcn_files:
                st.warning("⚠️ Không tìm thấy file GCN nào trong thư mục")
                return
            
            st.success(f"✅ Đã tìm thấy **{len(gcn_files)}** file GCN")
            
            # Select number of files to process
            col_batch1, col_batch2 = st.columns([3, 1])
            
            with col_batch2:
                st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
                process_all = st.checkbox("Xử lý tất cả", value=False, help="Xử lý tất cả file tìm thấy")
            
            with col_batch1:
                batch_size = st.number_input(
                    "Số lượng file muốn xử lý:",
                    min_value=1,
                    max_value=len(gcn_files),
                    value=min(10, len(gcn_files)),
                    help="Chọn số lượng file muốn xử lý (từ đầu danh sách)",
                    disabled=process_all
                )
            
            # Determine actual batch size
            actual_batch_size = len(gcn_files) if process_all else batch_size
            
            # Display how many files will be processed
            if process_all:
                st.info(f"📊 Sẽ xử lý **tất cả {len(gcn_files)}** file")
            else:
                st.info(f"📊 Sẽ xử lý **{actual_batch_size}** file đầu tiên")
            
            # Show file structure
            with st.expander("📁 Xem cấu trúc thư mục", expanded=True):
                st.markdown(f"**📂 Cấu trúc thư mục ({len(gcn_files)} file):**")
                
                # Build directory tree for all files
                dir_structure = {}
                for file_path in gcn_files:
                    try:
                        rel_path = file_path.relative_to(input_dir)
                        parts = rel_path.parts
                        
                        # Build nested dict structure
                        current = dir_structure
                        for part in parts[:-1]:  # All directories
                            if part not in current:
                                current[part] = {}
                            current = current[part]
                        
                        # Add file to the last directory
                        if '__files__' not in current:
                            current['__files__'] = []
                        current['__files__'].append(parts[-1])
                    except:
                        pass
                
                # Display tree - collect lines first, then display with st.code
                tree_lines = []
                
                def display_tree(tree, prefix=""):
                    items = [(k, v) for k, v in tree.items() if k != '__files__']
                    files = tree.get('__files__', [])
                    
                    total_items = len(items) + len(files)
                    current_item = 0
                    
                    # Display directories first
                    for dirname, subtree in items:
                        current_item += 1
                        is_last = current_item == total_items
                        
                        connector = "└── " if is_last else "├── "
                        tree_lines.append(f"{prefix}{connector}📁 {dirname}/")
                        
                        # Prepare prefix for children
                        child_prefix = prefix + ("    " if is_last else "│   ")
                        display_tree(subtree, child_prefix)
                    
                    # Display files
                    for filename in files:
                        current_item += 1
                        is_last = current_item == total_items
                        
                        connector = "└── " if is_last else "├── "
                        tree_lines.append(f"{prefix}{connector}📄 {filename}")
                
                if dir_structure:
                    tree_lines.append(f"📁 {input_dir.name}/")
                    display_tree(dir_structure, "    ")
                    
                    # Display all lines using st.code with custom container for fixed height
                    st.markdown("""
                    <style>
                    .tree-container {
                        max-height: 400px;
                        overflow-y: auto;
                        border: 1px solid #e0e0e0;
                        border-radius: 5px;
                        padding: 10px;
                        font-family: monospace;
                        white-space: pre;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    tree_content = "\n".join(tree_lines)
                    st.markdown(f'<div class="tree-container">{tree_content}</div>', unsafe_allow_html=True)
                else:
                    st.text("Tất cả file nằm trong thư mục gốc")
            
            # Process button
            if st.button("🚀 Bắt đầu xử lý", type="primary"):
                selected_files = gcn_files[:actual_batch_size]
                
                # Progress bar and status
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Live log container
                st.subheader("📝 Log xử lý realtime")
                st.caption("⏱️ Thời gian hiển thị là thời gian xử lý của TỪNG FILE riêng lẻ | [W1], [W2]... là Worker ID đang xử lý")
                log_container = st.container()
                
                # Process files
                start_time = time.time()
                status_text.text(f"Đang xử lý {len(selected_files)} file với {max_workers} luồng...")
                
                # Import needed for processing
                from concurrent.futures import ThreadPoolExecutor, as_completed
                from processor import process_single_pdf
                
                results = []
                completed = 0
                worker_assignments = {}  # Track which worker is processing which file
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks and assign worker IDs
                    futures = {}
                    for idx, pdf in enumerate(selected_files):
                        worker_id = (idx % max_workers) + 1  # Assign worker ID (1 to max_workers)
                        future = executor.submit(process_single_pdf, pdf, idx + 1, llm_url, api_timeout)
                        futures[future] = (pdf, idx + 1, worker_id)
                    
                    for future in as_completed(futures):
                        pdf_path, idx, worker_id = futures[future]
                        try:
                            result = future.result()
                            results.append(result)
                            completed += 1
                            
                            # Update progress
                            progress = int((completed / len(selected_files)) * 100)
                            progress_bar.progress(progress)
                            status_text.text(f"Đã xử lý: {completed}/{len(selected_files)} file")
                            
                            # Display live log with worker ID
                            with log_container:
                                status_icon = ""
                                if result["status"] == "success":
                                    if result["comparison"] == "Đúng":
                                        status_icon = "✅"
                                        msg = f"{result['filename_gcn']} = {result['predicted_gcn']}"
                                    else:
                                        status_icon = "⚠️"
                                        msg = f"{result['filename_gcn']} ≠ {result['predicted_gcn']}"
                                elif result["status"] == "skip":
                                    status_icon = "⏭️"
                                    msg = result.get('error', 'Skip')
                                else:
                                    status_icon = "❌"
                                    msg = result.get('error', 'Error')
                                
                                st.text(f"{status_icon} [W{worker_id}] [{result['time']:.2f}s] #{result['index']} {result['pdf_file']}: {msg}")
                        
                        except Exception as e:
                            st.error(f"❌ Lỗi không mong đợi với {pdf_path.name}: {e}")
                            completed += 1
                            progress = int((completed / len(selected_files)) * 100)
                            progress_bar.progress(progress)
                
                # Sort results by index
                results.sort(key=lambda x: x["index"])
                
                progress_bar.progress(100)
                processing_time = time.time() - start_time
                status_text.success(f"✅ Hoàn tất xử lý {len(selected_files)} file trong {processing_time:.2f}s")
                
                # Save results to session
                st.session_state.results = results
                
                # Results container
                results_container = st.container()
                
                with results_container:
                    
                    # Display statistics
                    st.subheader("📈 Thống kê")
                    
                    success = sum(1 for r in results if r["status"] == "success")
                    skip = sum(1 for r in results if r["status"] == "skip")
                    error = sum(1 for r in results if r["status"] == "error")
                    correct = sum(1 for r in results if r["comparison"] == "Đúng")
                    incorrect = sum(1 for r in results if r["comparison"] == "Cần hiệu đính")
                    
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    
                    with col_stat1:
                        st.metric("✅ Thành công", success)
                        st.metric("⏭️ Bỏ qua", skip)
                        st.metric("❌ Lỗi", error)
                    
                    with col_stat2:
                        st.metric("✓ Đúng", correct)
                        st.metric("⚠ Cần hiệu đính", incorrect)
                        if success > 0:
                            accuracy = (correct / success) * 100
                            st.metric("🎯 Độ chính xác", f"{accuracy:.2f}%")
                    
                    with col_stat3:
                        st.metric("⏱️ Tổng thời gian", f"{processing_time:.2f}s")
                        if len(results) > 0:
                            avg_time = processing_time / len(results)
                            st.metric("⚡ Trung bình", f"{avg_time:.2f}s/file")
                    
                    # Display processing log
                    st.subheader("📝 Log xử lý chi tiết")
                    with st.expander("Xem log xử lý từng file", expanded=False):
                        for r in results:
                            status_icon = ""
                            if r["status"] == "success":
                                if r["comparison"] == "Đúng":
                                    status_icon = "✅"
                                else:
                                    status_icon = "⚠️"
                            elif r["status"] == "skip":
                                status_icon = "⏭️"
                            else:
                                status_icon = "❌"
                            
                            # Build log message
                            log_msg = f"{status_icon} **#{r['index']}** `{r['pdf_file']}`"
                            
                            if r["status"] == "success":
                                log_msg += f"\n   - GCN từ tên file: `{r.get('filename_gcn', 'N/A')}`"
                                log_msg += f"\n   - Dự đoán AI: `{r['predicted_gcn']}`"
                                log_msg += f"\n   - Kết quả: **{r['comparison']}**"
                            elif r["status"] == "skip":
                                log_msg += f"\n   - Lý do: {r.get('error', 'N/A')}"
                            elif r["status"] == "error":
                                log_msg += f"\n   - Lỗi: {r.get('error', 'N/A')}"
                            
                            log_msg += f"\n   - Thời gian: {r['time']:.2f}s\n"
                            st.markdown(log_msg)
                    
                    # Display results table
                    st.subheader("📋 Bảng kết quả chi tiết")
                    
                    # Create dataframe
                    df_data = []
                    for r in results:
                        df_data.append({
                            "STT": r["index"],
                            "Tên file": r["pdf_file"],
                            "GCN từ tên file": r.get("filename_gcn", ""),
                            "Dự đoán": r["predicted_gcn"],
                            "Kết quả": r["comparison"],
                            "Trạng thái": r["status"],
                            "Thời gian (s)": f"{r['time']:.2f}"
                        })
                    
                    df = pd.DataFrame(df_data)
                    
                    # Color code only the result column
                    def highlight_result(val):
                        if val == "Đúng":
                            return 'background-color: #C6EFCE; color: #006100; font-weight: bold'
                        elif val == "Cần hiệu đính":
                            return 'background-color: #FFEB9C; color: #9C5700; font-weight: bold'
                        else:
                            return ''
                    
                    st.dataframe(
                        df.style.map(highlight_result, subset=['Kết quả']),
                        width='stretch',
                        height=400
                    )
                    
                    # Export to Excel
                    st.subheader("💾 Xuất kết quả")
                    
                    # Excel filename input
                    timestamp = datetime.now().strftime("%Y%m%d")
                    excel_filename = st.text_input(
                        "Tên file Excel:",
                        value=f"gcn_comparison_{timestamp}.xlsx",
                        help="Tên file Excel để lưu kết quả"
                    )
                    
                    if st.button("📊 Xuất ra Excel"):
                        excel_path = Path(excel_filename)
                        export_to_excel(results, excel_path)
                        st.success(f"✅ Đã xuất kết quả ra file: **{excel_path.resolve()}**")
                        
                        # Option to download
                        if excel_path.exists():
                            with open(excel_path, "rb") as f:
                                st.download_button(
                                    label="⬇️ Tải xuống file Excel",
                                    data=f,
                                    file_name=excel_filename,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
    
    with col2:
        st.header("ℹ️ Thông tin")
        
        st.info("""
        **Cách sử dụng:**
        
        1. Nhập đường dẫn thư mục chứa file GCN
        
        2. Nhấn nút "Tìm kiếm file GCN"
        
        3. Chọn số lượng file muốn xử lý
        
        4. Nhấn "Bắt đầu xử lý"
        
        5. Xem kết quả và xuất ra Excel
        """)
        
        st.markdown("---")
        
        st.markdown("""
        **Giải thích kết quả:**
        
        - ✅ **Đúng**: Số GCN từ tên file khớp với dự đoán
        - ⚠️ **Cần hiệu đính**: Không khớp, cần kiểm tra lại
        - ⏭️ **Bỏ qua**: File không đúng định dạng hoặc không có trang 2
        - ❌ **Lỗi**: Có lỗi trong quá trình xử lý
        """)
        
        st.markdown("---")
        
        st.markdown("""
        **Cấu hình mặc định:**
        
        - 🤖 Model: `{}`
        - 🖼️ DPI: `{}`
        - 🌡️ Temperature: `{}`
        """.format(Config.MODEL, Config.RENDER_DPI, Config.TEMPERATURE))


if __name__ == "__main__":
    main()

