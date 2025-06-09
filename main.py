import sys
import json
import pymupdf as fitz  # PyMuPDF
import re
import os
import shutil
from sentence_transformers import SentenceTransformer, util
import torch

def clear_screenshots():
    """Clear all files in the screenshots folder inside static."""
    screenshots_dir = os.path.join('static', 'screenshots')
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
        text_blocks.sort(key=lambda b: b[1])  # sort by y-coordinate (top to bottom)
        page_text = page.get_text()
        markers = list(re.finditer(r'Q\d+\s*-\s*\d+\s*\(.*?\)', page_text))
        marker_positions = [(m.start(), m.end(), m.group()) for m in markers]

        for i, (start, end, marker_text) in enumerate(marker_positions):
            # Find the block containing the current marker
            marker_block = None
            for block in text_blocks:
                if marker_text in block[4]:  # block[4] is the text
                    marker_block = block
                    break
            if not marker_block:
                continue

            x0, y0, x1, y1 = marker_block[0:4]
            min_x, max_x = x0, x1

            # Find the next question marker on the same page
            next_y1 = page.rect.y1  # default to end of page
            if i + 1 < len(marker_positions):
                next_marker = marker_positions[i+1]
                # Find the block containing the next marker
                for block in text_blocks:
                    if next_marker[2] in block[4]:
                        next_y1 = block[1]  # top of next question block
                        break

            # Expand the bounding box to include options and text below, but not beyond next question
            for block in text_blocks:
                if block[1] > y0 and block[3] < next_y1:
                    min_x = min(min_x, block[0])
                    max_x = max(max_x, block[2])
                    y1 = max(y1, block[3])

            # Ensure y1 does not go beyond the next question or page bottom
            y1 = min(y1, next_y1)
            max_x = min(max_x, page.rect.x1)

            # Extract the text in this region
            question_text = page.get_text("text", clip=(min_x, y0, max_x, y1))

            blocks.append({
                "pdf": os.path.basename(pdf_path),
                "page": page_num + 1,
                "marker": marker_text,
                "text": question_text,
                "rect": (min_x, y0, max_x, y1)
            })
    doc.close()
    return blocks

def screenshot_question_block(pdf_path, block_info, zoom=2):
    """Take screenshot of question block and save to static/screenshots/."""
    screenshots_dir = os.path.join('static', 'screenshots')
    os.makedirs(screenshots_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    page = doc[block_info["page"] - 1]
    x0, y0, x1, y1 = block_info["rect"]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=(x0, y0, x1, y1))
    img_name = f"Q{block_info['marker'].split()[0][1:]}_page{block_info['page']}_{os.path.splitext(os.path.basename(pdf_path))[0]}.png"
    img_path = os.path.join(screenshots_dir, img_name)
    pix.save(img_path)
    doc.close()
    # Return path relative to static for Flask url_for
    return f"screenshots/{img_name}"

def write_question_data(results, output_file="question_data.txt"):
    """Write question data to a text file (optional for web app)."""
    with open(output_file, "w", encoding="utf-8") as f:
        for result in results:
            f.write(f"PDF: {result['pdf']}\n")
            f.write(f"Page: {result['page']}\n")
            f.write(f"Marker: {result['marker']}\n")
            f.write(f"Screenshot: {result['screenshot']}\n")
            f.write(f"Text: {result['text']}\n")
            f.write(f"Rect: {result['rect']}\n")
            f.write(f"Similarity: {result.get('similarity', 'N/A')}\n")
            f.write("-" * 40 + "\n")

if __name__ == "__main__":
    # This block is optional; main logic will be in app.py for web use
    if len(sys.argv) < 2:
        print("Usage: python main.py <search_sentence>")
        sys.exit(1)
    search_sentence = sys.argv[1]
    assets_folder = "./assets"
    print(f"Search sentence: {search_sentence}")
    print(f"Assets folder: {assets_folder}")

    # Clear screenshots before new search
    clear_screenshots()

    # Load semantic search model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    results = []
    for pdf_file in os.listdir(assets_folder):
        if pdf_file.lower().endswith(".pdf"):
            pdf_path = os.path.join(assets_folder, pdf_file)
            print(f"\nProcessing: {pdf_path}")
            question_blocks = find_question_blocks(pdf_path)
            print(f"Found {len(question_blocks)} question blocks in {pdf_file}")

            if not question_blocks:
                continue

            question_texts = [block["text"] for block in question_blocks]
            # Encode question texts and search sentence
            question_embeddings = model.encode(question_texts, convert_to_tensor=True)
            query_embedding = model.encode([search_sentence], convert_to_tensor=True)

            # Use util.semantic_search for efficient top-k search
            top_k = 5  # Only keep top 5 results
            hits = util.semantic_search(query_embedding, question_embeddings, top_k=top_k)[0]

            # Threshold for semantic relevance (increase to reduce irrelevant results)
            threshold = 0.3
            for hit in hits:
                if hit['score'] > threshold:
                    block = question_blocks[hit['corpus_id']]
                    img_path = screenshot_question_block(pdf_path, block)
                    if img_path:
                        results.append({
                            "pdf": block["pdf"],
                            "page": block["page"],
                            "marker": block["marker"],
                            "text": block["text"],
                            "screenshot": img_path,
                            "rect": block["rect"],
                            "similarity": float(hit['score'])
                        })

    # Write question data to a text file
    write_question_data(results)
    print("\nFinal results:", json.dumps(results, indent=2))
