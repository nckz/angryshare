#!/usr/bin/env python

import os
from flask import Flask, request, redirect, url_for, send_from_directory, abort
from werkzeug import secure_filename

UPLOAD_FOLDER = './tmp/'
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return True # allow any file type
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def template(body, path):
    page = """
<!doctype html>
<title>Angry Share</title>
<xmp theme="united" style="display:none;">

# Upload New File
<form action="" method=post enctype=multipart/form-data>
<input type=file name=file> <input type=submit value=Upload>
</form>
"""
    page += "\n----\n"
    page += "## " + path + "\n------\n<p>"
    page += body
    page += """</p></xmp>
<script src="http://strapdownjs.com/v/0.2/strapdown.js"></script>
</html>"""
    return page

def listandlinkdir(rel_path, phys_path):
    # the links need to be relative to the parent path only
    html = "".join(["["+l+"]("+os.path.join(os.path.basename(rel_path),l)+")<br>" for l in os.listdir(phys_path)])
    return html

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route("/<path:path>", methods=['GET', 'POST'])
def index(path):

    # Convert requested path to the path relative to the downloads directory.
    # This way the client sees the root as http://<host>/ but the actual
    # uploads directory can be something else.
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
    #print('path', path)
    #print('upload_path', upload_path)
    #print('url_for_index', os.path.join(url_for('index'),path))

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_path, filename))
            return redirect(os.path.join(url_for('index'),path))

    # if GET
    if os.path.isdir(upload_path):
        display_path = os.path.join('/',path)
        return template(listandlinkdir(path, upload_path), display_path)

    if os.path.isfile(upload_path):
        dirname = os.path.dirname(upload_path)
        basename = os.path.basename(upload_path)
        return send_from_directory(dirname, basename)

    # Server Error (the client shouldn't get here)
    abort(500)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
