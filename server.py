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
#   * checkout dropzone.js and dragula.js

import os
import jinja2
from flask import Flask, request, redirect, url_for, send_from_directory, abort
from flask import render_template
from werkzeug import secure_filename

jinja_env = jinja2.Environment()
jinja_env.globals.update(zip=zip)

UPLOAD_FOLDER = './tmp/'
STATIC_FOLDER = 'static'
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico')

@app.route('/dropzone.js')
def dropzone():
    path = os.path.join(STATIC_FOLDER,'dropzone.js')
    return send_from_directory(app.root_path, path)

def AllowedFile(filename):
    return True # allow any file type
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def ListAndLinkDir(rel_path, phys_path):
    # the links need to be relative to the parent path only
    ls = [] # directory listing
    links = [] # urls for each file
    style = [] # how should directory links be styled
    for l in os.listdir(phys_path):
        # keep the filename
        ls.append(l)

        # make directories stand out
        if os.path.isdir(os.path.join(phys_path,l)):
            style.append(True)
        else:
            style.append(False)

        # assemble markdown links
        url = os.path.join(os.path.basename(rel_path),l)
        links.append(url)

    return zip(ls, links, style)

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
    paths = ['/']
    urls  = ['/']
    for p,d in zip(pieces,dirorder):
        if p == '': # skip first and last /
            continue
        if p != pieces[-1]: # don't put a trailing /
            p += '/'
        paths.append(p)
        urls.append(d)

    return zip(paths, urls)
    
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route("/<path:path>", methods=['GET', 'POST'])
def index(path):

    # Convert requested path to the path relative to the downloads directory.
    # This way the client sees the root as http://<host>/ but the actual
    # uploads directory can be something else.
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], path)

    if request.method == 'POST':
        file = request.files['file']
        if file and AllowedFile(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_path, filename))
            return redirect(os.path.join(url_for('index'),path))

    # if GET
    if os.path.isdir(upload_path):
        display_path = os.path.join('/',path)
        path_nav = LinkDisplayPath(display_path)
        dirlinks = ListAndLinkDir(path, upload_path)
        return render_template('directory_index.html', pathlist=path_nav, dirlinks=dirlinks)

    if os.path.isfile(upload_path):
        dirname = os.path.dirname(upload_path)
        basename = os.path.basename(upload_path)
        return send_from_directory(dirname, basename)

    # Server Error (the client shouldn't get here)
    abort(500)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(host='tron.local', port=5000, debug=True)
