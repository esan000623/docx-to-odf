import os
import subprocess
import zipfile
import tempfile
import shutil
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB limit

ALLOWED_EXTENSIONS = {'docx', 'pptx', 'xlsx', 'doc', 'ppt', 'xls'}

# LibreOffice executable path - search PATH and common install locations
def _find_libreoffice():
    # Check PATH first
    found = shutil.which('libreoffice') or shutil.which('soffice')
    if found:
        return found
    # Common install paths (Linux / Windows)
    candidates = [
        '/usr/bin/libreoffice',           # Linux (Debian/Ubuntu)
        '/usr/bin/soffice',
        '/usr/lib/libreoffice/program/soffice',
        '/opt/libreoffice/program/soffice',
        r'C:\Program Files\LibreOffice\program\soffice.exe',
        r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_odf_format(extension):
    mapping = {
        'docx': ('odt', 'writer8'),
        'doc':  ('odt', 'writer8'),
        'pptx': ('odp', 'impress8'),
        'ppt':  ('odp', 'impress8'),
        'xlsx': ('ods', 'calc8'),
        'xls':  ('ods', 'calc8'),
    }
    return mapping.get(extension.lower(), ('odt', 'writer8'))


def convert_to_odf(input_path, output_dir):
    """Convert a file to ODF using LibreOffice headless mode."""
    lo_path = _find_libreoffice()
    if not lo_path:
        return None, 'LibreOffice not found. Please install it from https://www.libreoffice.org/'

    ext = os.path.splitext(input_path)[1].lstrip('.').lower()
    odf_ext, _ = get_odf_format(ext)

    cmd = [
        lo_path,
        '--headless',
        '--convert-to', odf_ext,
        '--outdir', output_dir,
        input_path
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )
    except FileNotFoundError:
        return None, 'LibreOffice not found. Please install it from https://www.libreoffice.org/'
    except subprocess.TimeoutExpired:
        return None, 'Conversion timed out (120s)'
    except Exception as e:
        return None, str(e)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    expected_output = os.path.join(output_dir, f'{base_name}.{odf_ext}')

    if os.path.exists(expected_output):
        return expected_output, None
    else:
        stderr = result.stderr.decode('utf-8', errors='replace').strip() if result.stderr else ''
        stdout = result.stdout.decode('utf-8', errors='replace').strip() if result.stdout else ''
        error_msg = stderr or stdout or 'Conversion failed: output file not found'
        return None, error_msg


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/convert', methods=['POST'])
def convert_files():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400

        upload_dir = tempfile.mkdtemp()
        output_dir = tempfile.mkdtemp()
        results = []
        converted_files = []

        try:
            for file in files:
                if not file.filename:
                    continue

                filename = secure_filename(file.filename)
                if not filename or not allowed_file(filename):
                    results.append({
                        'original': file.filename,
                        'status': 'error',
                        'message': 'Unsupported file type'
                    })
                    continue

                input_path = os.path.join(upload_dir, filename)
                file.save(input_path)

                output_path, error = convert_to_odf(input_path, output_dir)

                if output_path:
                    ext = os.path.splitext(filename)[1].lstrip('.').lower()
                    odf_ext, _ = get_odf_format(ext)
                    results.append({
                        'original': file.filename,
                        'converted': os.path.basename(output_path),
                        'status': 'success',
                        'format': odf_ext.upper()
                    })
                    converted_files.append(output_path)
                else:
                    results.append({
                        'original': file.filename,
                        'status': 'error',
                        'message': error
                    })

            if not converted_files:
                return jsonify({'results': results, 'download_id': None})

            # Build zip in a separate stable temp file BEFORE cleaning output_dir
            final_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            final_zip.close()

            with zipfile.ZipFile(final_zip.name, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in converted_files:
                    zf.write(f, os.path.basename(f))

            return jsonify({
                'results': results,
                'download_id': os.path.basename(final_zip.name)
            })

        finally:
            # Clean up temp dirs only (zip is already in a separate stable path)
            shutil.rmtree(upload_dir, ignore_errors=True)
            shutil.rmtree(output_dir, ignore_errors=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    if not filename.endswith('.zip'):
        return jsonify({'error': 'Invalid file'}), 400

    tmp_dir = tempfile.gettempdir()
    file_path = os.path.join(tmp_dir, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found or expired'}), 404

    def remove_after_send(path):
        try:
            os.remove(path)
        except Exception:
            pass

    response = send_file(
        file_path,
        as_attachment=True,
        download_name='converted_odf_files.zip',
        mimetype='application/zip'
    )
    # Clean up the zip after it's sent
    response.call_on_close(lambda: remove_after_send(file_path))
    return response


@app.route('/api/debug')
def debug():
    import glob
    lo_path = _find_libreoffice()
    search_results = []
    for pattern in ['/usr/bin/libre*', '/usr/bin/soffice*', '/usr/lib/libreoffice*', '/opt/libre*']:
        search_results.extend(glob.glob(pattern))
    return jsonify({
        'libreoffice_found': lo_path,
        'which_libreoffice': shutil.which('libreoffice'),
        'which_soffice': shutil.which('soffice'),
        'search_results': search_results,
    })


@app.route('/api/check-libreoffice')
def check_libreoffice():
    lo_path = _find_libreoffice()
    if lo_path:
        try:
            result = subprocess.run(
                [lo_path, '--version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            stdout = result.stdout.decode('utf-8', errors='replace').strip() if result.stdout else ''
            stderr = result.stderr.decode('utf-8', errors='replace').strip() if result.stderr else ''
            version = stdout or stderr
            return jsonify({'available': True, 'path': lo_path, 'version': version})
        except Exception as e:
            return jsonify({'available': False, 'error': str(e)})
    return jsonify({'available': False, 'error': 'LibreOffice not found in PATH'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
