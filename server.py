#!/usr/bin/env python

# Author: Nick Zwart
# Date: 2016feb21

# TODO
#   * make commandline interface with options for port, uploads dir, app path...
#   * add file size and date
#   * add upload drag'n drop
#   * add new directory, move, and delete options
#   * project name: AngryShare, ShareNinja, TheGiver, ShareBot, GiveAndTake, 
#     EasyShare, RapidShare, FileHub, PowerShare, MaximumShare,
#     HyperTextTransferProtocolShare (HTTPS), Rat'sNest, FileDump, TheDump
#     Garbage, DumpHub, myGarbage, iDump

import os
from flask import Flask, request, redirect, url_for, send_from_directory, abort
from werkzeug import secure_filename

UPLOAD_FOLDER = './tmp/'
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico')

def AllowedFile(filename):
    return True # allow any file type
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def ListAndLinkDir(rel_path, phys_path):
    # the links need to be relative to the parent path only
    html = ''
    for l in os.listdir(phys_path):
        # make directories stand out
        p = l
        if os.path.isdir(os.path.join(phys_path,l)):
            p = "**"+l+"**"

        # assemble markdown links
        html += "["+p+"]("+os.path.join(os.path.basename(rel_path),l)+")<br>" 
    return html

def LinkDisplayPath(path):
    # split the path up into linked buttons
    pieces = path.split('/')

    # generate the links for those buttons
    dirorder = []
    for p in pieces:
        dirorder.append(path)
        path = os.path.dirname(path)
    dirorder.reverse()

    # link each part of the path
    root = '<a href=\"/\">/</a>'
    lpath = ''
    for p,d in zip(pieces,dirorder):
        if p == '': # skip first and last /
            continue
        if p != pieces[-1]: # don't put a trailing /
            p += '/'
        lpath += '<a href=\"'+d+'\">'+p+'</a>'

    return root+lpath
    
def Template(body, path):
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
    page += "## " + LinkDisplayPath(path) + "\n"
    page += "<p>"
    page += body
    page += """</p></xmp>
<script src="http://strapdownjs.com/v/0.2/strapdown.js"></script>
</html>"""
    return page

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
        if file and AllowedFile(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_path, filename))
            return redirect(os.path.join(url_for('index'),path))

    # if GET
    if os.path.isdir(upload_path):
        display_path = os.path.join('/',path)
        LinkDisplayPath(display_path)
        return Template(ListAndLinkDir(path, upload_path), display_path)

    if os.path.isfile(upload_path):
        dirname = os.path.dirname(upload_path)
        basename = os.path.basename(upload_path)
        return send_from_directory(dirname, basename)

    # Server Error (the client shouldn't get here)
    abort(500)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
