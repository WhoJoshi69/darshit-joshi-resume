import os

from flask import Flask, jsonify, render_template, request, send_file

import resume_builder

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/api/resume')
def get_resume():
    return jsonify(resume_builder.load())


@app.post('/api/resume')
def save_resume():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'ok': False, 'error': 'Invalid resume data.'}), 400
    resume_builder.save(data)
    result = resume_builder.build()
    return jsonify(result), (200 if result['ok'] else 422)


@app.get('/api/status')
def status():
    return jsonify({
        'pdf': os.path.exists(resume_builder.PDF_FILE),
        'last_build': resume_builder.last_build(),
    })


@app.get('/resume.pdf')
def pdf():
    if not os.path.exists(resume_builder.PDF_FILE):
        return jsonify({'error': 'PDF not built yet.'}), 404
    name = resume_builder.load()['header']['name'].strip().replace(' ', '_') or 'Resume'
    response = send_file(
        resume_builder.PDF_FILE,
        mimetype='application/pdf',
        as_attachment=request.args.get('download') == '1',
        download_name=f'{name}_Resume.pdf',
        max_age=0,
    )
    response.headers['Cache-Control'] = 'no-store'
    return response


if __name__ == '__main__':
    app.run(debug=True, port=5000)
