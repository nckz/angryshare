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
import time
import socket
from flask import Flask, request, redirect, url_for, send_from_directory, abort
from flask import render_template
from werkzeug import secure_filename

HOSTNAME = socket.gethostname()
UPLOAD_FOLDER = './tmp/'
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/favicon.ico')
def faviconico():
    return send_from_directory('static', 'favicon.ico')

@app.route('/favicon.png')
def faviconpng():
    return send_from_directory('static', 'favicon.png')

def AllowedFile(filename):
    return True # allow any file type
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def ListAndLinkDir(rel_path, phys_path):
    # the links need to be relative to the parent path only
    ls = [] # directory listing
    links = [] # urls for each file
    style = [] # how should directory links be styled
    upload_date = [] # date the file was created on the server (string)
    ids = [] # valid and unique html id tags
    for l in os.listdir(phys_path):

        # full server-side file-system path
        file_path = os.path.join(phys_path,l)

        # creation date
        upload_date.append(time.ctime(os.path.getctime(file_path)))

        # keep the filename
        ls.append(l)

        # id tags
        ids.append(l.replace('.','-'))

        # make directories stand out
        if os.path.isdir(file_path):
            style.append(True)
        else:
            style.append(False)

        # assemble markdown links
        url = os.path.join(os.path.basename(rel_path),l)
        links.append(url)

    print(ids)

    return zip(ls, links, style, upload_date, ids)

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
        print('files POSTed:', file)
        if file and AllowedFile(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_path, filename))

            # if its a post from js, then the js will handle this refresh
            return redirect(os.path.join(url_for('index'),path))

    # if GET
    if os.path.isdir(upload_path):
        display_path = os.path.join('/',path)
        path_nav = LinkDisplayPath(display_path) # path navigation
        dirlinks = ListAndLinkDir(path, upload_path) # file links
        return render_template('directory_index.html', pathlist=path_nav, dirlinks=dirlinks, hostname=HOSTNAME)

    if os.path.isfile(upload_path):
        dirname = os.path.dirname(upload_path)
        basename = os.path.basename(upload_path)
        return send_from_directory(dirname, basename)

    # Server Error (the client shouldn't get here)
    abort(500)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(host='tron.local', port=5000, debug=True)
