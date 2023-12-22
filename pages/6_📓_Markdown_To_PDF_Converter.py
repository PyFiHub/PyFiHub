'''
Make sure you have wkhtmltopdf installed on your system, as it is required by pdfkit for HTML to PDF conversion. 
You can download it from the official website: https://wkhtmltopdf.org/downloads.html

'''

import streamlit as st
import markdown2
import pdfkit
import os
from extras import logo_sidebar_lit

def markdown_to_pdf(md_text, pdf_file):
    # Convert Markdown to HTML
    html = markdown2.markdown(md_text)

    # Write HTML to file
    html_file = "temp.html"
    with open(html_file, "w", encoding="utf-8") as file:
        file.write(html)

    # Convert HTML to PDF
    options = {
        'page-size': 'A4',
        'margin-top': '10mm',
        'margin-right': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
    }
    pdfkit.from_file(html_file, pdf_file, options=options)

if __name__ == "__main__":

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    logo_path = os.path.join(parent_dir, 'extras', 'logo.png')
    asset_thumbs_path = os.path.join(parent_dir, 'extras', 'assets_thumbs')
    st.set_page_config(page_title='📓 Markdown to PDF Converter', page_icon='🌐', layout='centered',initial_sidebar_state='expanded')
    st.markdown(logo_sidebar_lit(logo_path, height=159), unsafe_allow_html=True)

    hide_menu_style = """
            <style>
                #MainMenu {visibility: hidden;}
                button[title="View fullscreen"]{visibility: hidden;}
                .css-15zrgzn {display: none}
                section[data-testid="stSidebar"] .css-ng1t4o {{width: 14rem;}}
                footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

    st.title("Markdown to PDF Converter")

    # Upload Markdown file
    md_file = st.file_uploader("Upload Markdown file", type=["md"])
    
    if md_file is not None:
        # Read Markdown file content
        md_text = md_file.read()

        # Convert Markdown to PDF
        pdf_file_path = "output.pdf"
        markdown_to_pdf(md_text, pdf_file_path)

        # Display download link
        st.success("Conversion successful! Download your PDF file:")
        with open(pdf_file_path, "rb") as f:
            st.download_button(
                label="Download PDF",
                data=f.read(),
                key="download_pdf",
                file_name=pdf_file_path,
            )

        # Clean up temporary files
        os.remove("temp.html")
        os.remove("output.pdf")
