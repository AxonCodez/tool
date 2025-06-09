import sys
import json
import pymupdf as fitz  # PyMuPDF
import re
import os

os.makedirs("screenshots", exist_ok=True)

def find_question_blocks(pdf_path):
    doc = fitz.open(pdf_path)
    blocks = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text_blocks = page.get_text("blocks")
        # Join all text for this page to find question markers
        page_text = page.get_text()
        # Find all question markers (e.g., "Q1 - 2024 (01 Feb Shift 1)")
        markers = re.finditer(r'Q\d+\s*-\s*\d+\s*\(.*?\)', page_text)
        for match in markers:
            marker_text = match.group()
            # Find the block containing the marker
            for block in text_blocks:
                if marker_text in block[4]:  # block[4] is the text
                    # This is the block containing the marker
                    x0, y0, x1, y1 = block[0:4]
                    # Estimate a wider area: add extra height and some width
                    extra_height = 200  # pixels (adjust as needed)
                    extra_width = 600    # pixels (adjust as needed)
                    # Make sure the box stays within the page
                    new_y1 = min(y1 + extra_height, page.rect.y1)
                    new_x1 = min(x1 + extra_width, page.rect.x1)
                    blocks.append({
                        "page": page_num + 1,
                        "marker": marker_text,
                        "rect": (x0, y0, new_x1, new_y1)
                    })
                    break  # only the first matching block per marker
    doc.close()
    return blocks

def screenshot_question_block(pdf_path, block_info, zoom=2):
    doc = fitz.open(pdf_path)
    page = doc[block_info["page"] - 1]
    x0, y0, x1, y1 = block_info["rect"]
    # Render the expanded area
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=(x0, y0, x1, y1))
    # Save the image
    img_path = f"screenshots/Q{block_info['marker'].split()[0][1:]}_page{block_info['page']}.png"
    pix.save(img_path)
    doc.close()
    return img_path

def find_relevant_blocks(search_term, question_blocks, pdf_path):
    doc = fitz.open(pdf_path)
    relevant = []
    search_term = search_term.lower()
    for block in question_blocks:
        page = doc[block["page"] - 1]
        # Extract text from the expanded area to check for the search term
        x0, y0, x1, y1 = block["rect"]
        text = page.get_text("text", clip=(x0, y0, x1, y1))
        if search_term in text.lower():
            relevant.append(block)
    doc.close()
    return relevant

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <search_term>")
        sys.exit(1)
    search_term = sys.argv[1]
    pdf_path = "./assets/sample.pdf"  # Adjust if needed
    print(f"Search term: {search_term}")
    print(f"PDF path: {pdf_path}")

    question_blocks = find_question_blocks(pdf_path)
    relevant = find_relevant_blocks(search_term, question_blocks, pdf_path)

    results = []
    for block in relevant:
        img_path = screenshot_question_block(pdf_path, block)
        if img_path:
            results.append({
                "page": block["page"],
                "marker": block["marker"],
                "screenshot": img_path,
                "rect": block["rect"]
            })

    print("Final results:", json.dumps(results, indent=2))
