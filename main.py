import sys
import json
import pymupdf as fitz  # PyMuPDF
import re

def extract_question_blocks(pdf_path):
    doc = fitz.open(pdf_path)
    all_blocks = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        # Split text into blocks starting with "Q<number>"
        blocks = re.split(r'(?=Q\d+\s*-\s*\d+\s*\(.*?\))', text)
        # The first split may be empty or text before the first Q, so skip if empty
        for block in blocks:
            block = block.strip()
            if block and re.match(r'^Q\d+\s*-\s*\d+\s*\(.*?\)', block):
                all_blocks.append({
                    "page": page_num + 1,
                    "block": block
                })
    doc.close()
    print(f"Extracted {len(all_blocks)} question blocks from PDF.")
    return all_blocks

def find_relevant_blocks(search_term, question_blocks):
    relevant = []
    search_term = search_term.lower()
    for block in question_blocks:
        if search_term in block['block'].lower():
            relevant.append(block)
    print(f"Found {len(relevant)} relevant blocks for search term: {search_term}")
    return relevant

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <search_term>")
        sys.exit(1)
    search_term = sys.argv[1]
    pdf_path = "./assets/sample.pdf"  # Adjust if needed
    print(f"Search term: {search_term}")
    print(f"PDF path: {pdf_path}")

    question_blocks = extract_question_blocks(pdf_path)
    if not question_blocks:
        print("No question blocks found in PDF. Exiting.")
        sys.exit(1)

    relevant = find_relevant_blocks(search_term, question_blocks)
    results = []
    for block in relevant:
        results.append({
            "page": block['page'],
            "question_block": block['block']
        })

    print("Final results:", json.dumps(results, indent=2))
