import sys
import json
import pymupdf as fitz  # PyMuPDF
import re
import os
import shutil

def clear_screenshots():
    """Clear all files in the screenshots folder."""
    screenshots_dir = "screenshots"
    if os.path.exists(screenshots_dir):
        for filename in os.listdir(screenshots_dir):
            file_path = os.path.join(screenshots_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        os.makedirs(screenshots_dir)

def find_question_blocks(pdf_path):
    doc = fitz.open(pdf_path)
    blocks = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text_blocks = page.get_text("blocks")
        text_blocks.sort(key=lambda b: b[1])
        page_text = page.get_text()
        markers = re.finditer(r'Q\d+\s*-\s*\d+\s*\(.*?\)', page_text)
        marker_positions = [(m.start(), m.end(), m.group()) for m in markers]
        for start, end, marker_text in marker_positions:
            marker_block = None
            for block in text_blocks:
                if marker_text in block[4]:
                    marker_block = block
                    break
            if not marker_block:
                continue
            x0, y0, x1, y1 = marker_block[0:4]
            min_x, max_x = x0, x1
            for block in text_blocks:
                if block[1] > y0:
                    if block[1] - y1 < 200:
                        min_x = min(min_x, block[0])
                        max_x = max(max_x, block[2])
                        y1 = max(y1, block[3])
                    else:
                        break
            y1 = min(y1, page.rect.y1)
            max_x = min(max_x, page.rect.x1)
            blocks.append({
                "pdf": os.path.basename(pdf_path),
                "page": page_num + 1,
                "marker": marker_text,
                "rect": (min_x, y0, max_x, y1)
            })
    doc.close()
    return blocks

def screenshot_question_block(pdf_path, block_info, zoom=2):
    doc = fitz.open(pdf_path)
    page = doc[block_info["page"] - 1]
    x0, y0, x1, y1 = block_info["rect"]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=(x0, y0, x1, y1))
    img_name = f"Q{block_info['marker'].split()[0][1:]}_page{block_info['page']}_{os.path.splitext(os.path.basename(pdf_path))[0]}.png"
    img_path = os.path.join("screenshots", img_name)
    pix.save(img_path)
    doc.close()
    return img_path

def find_relevant_blocks(search_term, question_blocks, pdf_path):
    doc = fitz.open(pdf_path)
    relevant = []
    search_term = search_term.lower()
    for block in question_blocks:
        page = doc[block["page"] - 1]
        x0, y0, x1, y1 = block["rect"]
        text = page.get_text("text", clip=(x0, y0, x1, y1))
        if search_term in text.lower():
            relevant.append(block)
    doc.close()
    return relevant

def write_question_data(results, output_file="question_data.txt"):
    """Write question data to a text file."""
    with open(output_file, "w", encoding="utf-8") as f:
        for result in results:
            f.write(f"PDF: {result['pdf']}\n")
            f.write(f"Page: {result['page']}\n")
            f.write(f"Marker: {result['marker']}\n")
            f.write(f"Screenshot: {result['screenshot']}\n")
            f.write(f"Rect: {result['rect']}\n")
            f.write("-" * 40 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <search_term>")
        sys.exit(1)
    search_term = sys.argv[1]
    assets_folder = "./assets"
    print(f"Search term: {search_term}")
    print(f"Assets folder: {assets_folder}")

    # Clear screenshots before new search
    clear_screenshots()

    results = []
    for pdf_file in os.listdir(assets_folder):
        if pdf_file.lower().endswith(".pdf"):
            pdf_path = os.path.join(assets_folder, pdf_file)
            print(f"Processing: {pdf_path}")
            question_blocks = find_question_blocks(pdf_path)
            relevant = find_relevant_blocks(search_term, question_blocks, pdf_path)
            for block in relevant:
                img_path = screenshot_question_block(pdf_path, block)
                if img_path:
                    results.append({
                        "pdf": block["pdf"],
                        "page": block["page"],
                        "marker": block["marker"],
                        "screenshot": img_path,
                        "rect": block["rect"]
                    })

    # Write question data to a text file
    write_question_data(results)

    print("Final results:", json.dumps(results, indent=2))
