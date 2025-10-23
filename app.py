from flask import Flask, render_template, request, jsonify, send_file
import os
import subprocess
import glob

app = Flask(__name__)

RESUME_DIR = '/home/darshit/Documents/personal/darshit_joshi_resume'
RESUME_SECTIONS = ['summary', 'skills', 'experience', 'projects', 'education']

@app.route('/')
def index():
    return render_template('index.html', sections=RESUME_SECTIONS)

@app.route('/get_file/<section>')
def get_file(section):
    file_path = os.path.join(RESUME_DIR, 'resume', f'{section}.tex')
    try:
        with open(file_path, 'r') as f:
            return jsonify({'content': f.read()})
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/save_file/<section>', methods=['POST'])
def save_file(section):
    content = request.json.get('content', '')
    file_path = os.path.join(RESUME_DIR, 'resume', f'{section}.tex')
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        # Clean old files
        for ext in ['*.aux', '*.log', '*.out']:
            for f in glob.glob(os.path.join(RESUME_DIR, ext)):
                os.remove(f)
        
        # Generate PDF
        result = subprocess.run(['xelatex', 'resume.tex'], 
                              cwd=RESUME_DIR, 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': 'PDF generated successfully'})
        else:
            return jsonify({'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_pdf')
def download_pdf():
    pdf_path = os.path.join(RESUME_DIR, 'resume.pdf')
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return jsonify({'error': 'PDF not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)