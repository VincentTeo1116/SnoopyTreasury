import streamlit as st
from vision import process_document, handle_uploaded_file
from PIL import Image
import io

st.set_page_config(page_title="OCR Document Processor", layout="wide")

st.title("📄 OCR Document Processor")
st.caption("Upload invoice or bank statement for AI-powered extraction")

uploaded_file = st.file_uploader(
    "Choose a file (PDF or Image)",
    type=['pdf', 'png', 'jpg', 'jpeg']
)

if uploaded_file is not None:
    with st.spinner("Processing document..."):
        # Save the file bytes for later display
        file_bytes = uploaded_file.getvalue()
        
        # Process the document
        file_path = handle_uploaded_file(uploaded_file)
        result = process_document(file_path)
        
        if result.get("success"):
            st.success("✅ Extraction completed!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 Extracted Information")
                st.write(f"**Document Type:** {result['document_type']}")
                st.write(f"**Company:** {result['company_name']}")
                st.write(f"**Bank:** {result['bank_name']}")
                st.write(f"**Amount:** {result['currency']} {result['amount']}")
                st.write(f"**Invoice Date:** {result['invoice_date']}")
                st.write(f"**Due Date:** {result['due_date']}")
            
            with col2:
                st.subheader("📄 Document Preview")
                # Fix: Reload the image from bytes
                try:
                    if uploaded_file.type.startswith('image'):
                        # For images, reload from bytes
                        image = Image.open(io.BytesIO(file_bytes))
                        st.image(image, width=300)
                    else:
                        # For PDFs, show file info
                        st.info(f"📄 PDF File: {uploaded_file.name}")
                        st.write(f"**Size:** {len(file_bytes) / 1024:.2f} KB")
                except Exception as e:
                    st.warning(f"Preview not available: {str(e)}")
        else:
            st.error(f"Failed: {result.get('error')}")