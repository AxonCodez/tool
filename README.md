# PDF Question Search Tool

A Python tool for searching and extracting question blocks from multiple PDFs, capturing screenshots of relevant questions, and exporting question data.

## Features

- **Batch processing:** Searches all PDF files in the `assets` folder.
- **Keyword search:** Finds questions containing a specified search term.
- **Automated screenshots:** Captures and saves images of relevant question blocks.
- **Clean output:** Clears previous screenshots before each new search.
- **Question data export:** Generates a `question_data.txt` file with details for each matching question.
- **JSON output:** Displays results as JSON for easy inspection.

## Requirements

- **Python 3.8+**
- **PyMuPDF (`fitz`/`pymupdf`)**
- **Other dependencies:**  
  - `os`
  - `re`
  - `json`
  - `shutil` (for folder cleanup)

## Installation

1. **Clone the repository:**

`git clone https://github.com/AxonCodez/tool.git`
`cd pdf-question-search`


2. **Install dependencies:**

`pip install pymupdf`


3. **Prepare your PDFs:**
- Place your PDF files in the `assets` folder.

## Usage

1. **Run the tool with your search term:**

`python main.py "your_search_term"`

- Replace `"your_search_term"` with the word or phrase you want to search for.

2. **Output:**
- **Screenshots:** Saved in the `screenshots` folder.
- **Question data:** Saved in `question_data.txt`.
- **JSON results:** Printed to the console.

## Checkpoints

- **Checkpoint 1:** Current version as of your last saved checkpoint.  
- Clears screenshots before each search.
- Searches all PDFs in `assets`.
- Saves new results as screenshots.
- Exports question data to `question_data.txt`.
- Outputs results as JSON.

## Example

`python main.py "capacitor"`

- **Output:**  
  - `screenshots/Q1_page1_pdfname.png`
  - `question_data.txt` with question details
  - JSON output in the terminal

## License

Open Source and developed by Akshay (9840808272)
