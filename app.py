import os
import shutil
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from main import find_question_blocks, screenshot_question_block
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For flash messages

ASSETS_FOLDER = './assets'
SCREENSHOTS_FOLDER = './static/screenshots'
ALLOWED_EXTENSIONS = {'pdf'}

model = SentenceTransformer('all-MiniLM-L6-v2')

os.makedirs(ASSETS_FOLDER, exist_ok=True)
os.makedirs(SCREENSHOTS_FOLDER, exist_ok=True)

def clear_screenshots():
    for filename in os.listdir(SCREENSHOTS_FOLDER):
        file_path = os.path.join(SCREENSHOTS_FOLDER, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    files = [f for f in os.listdir(ASSETS_FOLDER) if f.lower().endswith('.pdf')]
    results = []
    prompt = ''
    error = None

    if request.method == 'POST':
        if 'upload_pdf' in request.form:
            # Handle PDF upload
            if 'pdf_file' not in request.files:
                flash('No file part', 'error')
                return redirect(request.url)
            file = request.files['pdf_file']
            if file.filename == '':
                flash('No selected file', 'error')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(ASSETS_FOLDER, filename))
                flash(f'File {filename} uploaded successfully.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid file type. Only PDFs allowed.', 'error')
                return redirect(request.url)

        # Handle search
        prompt = request.form.get('prompt', '').strip()
        selected_files = request.form.getlist('pdf_files')
        if not prompt or not selected_files:
            error = "Please enter a prompt and select at least one PDF file."
        else:
            clear_screenshots()
            for pdf_file in selected_files:
                pdf_path = os.path.join(ASSETS_FOLDER, pdf_file)
                question_blocks = find_question_blocks(pdf_path)
                if not question_blocks:
                    continue
                question_texts = [block["text"] for block in question_blocks]
                question_embeddings = model.encode(question_texts, convert_to_tensor=True)
                prompt_embedding = model.encode([prompt], convert_to_tensor=True)
                hits = util.semantic_search(prompt_embedding, question_embeddings, top_k=5)[0]
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
                                "similarity": float(hit['score'])
                            })

    return render_template('index.html', files=files, results=results, prompt=prompt, error=error)

@app.route('/delete/<filename>')
def delete_file(filename):
    filepath = os.path.join(ASSETS_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f'File {filename} deleted successfully.', 'success')
    else:
        flash('File not found.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
