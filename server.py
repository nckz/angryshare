#!/usr/bin/env python

# Author: Nick Zwart
# Date: 2016feb21

# TODO
#   * make commandline interface with options for port, uploads dir, app path...
#   * add file size and date
#   * add new directory

import os
import time
import socket
import urllib
import random
import string
import threading
import hashlib
from flask import Flask, request, redirect, url_for, send_from_directory, abort
from flask import render_template
from werkzeug import secure_filename

HOSTNAME = socket.gethostname()
UPLOAD_FOLDER = os.path.abspath('./tmp/')
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(24)) 

# simple logging buffer
class LogBuffer():
    def __init__(self):
        self._log = []

    def append(self, msg):
        # append to the list
        m = (str(msg), threading.Timer(10.0, self._pop))
        self._log.append(m)
        m[1].start()

    def _pop(self):
        self._log.pop(0)
    
    def messages(self):
        return [ m[0] for m in self._log ]

log = LogBuffer()

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

def GetHumanReadable_bytes(size, precision=0):
    # change size in bytes (int) to a string with nice display units
    suffixes = ['B', 'K', 'M', 'G', 'T']
    suffixIndex = 0
    while int(size) > 1024:
        suffixIndex += 1
        size = size / 1024.0
    return "%.*f%s" % (precision, size, suffixes[suffixIndex])

def ListAndLinkDir(rel_path, phys_path):
    # the links need to be relative to the parent path only
    ls = [] # directory listing
    links = [] # urls for each file
    style = [] # how should directory links be styled
    upload_date = [] # date the file was created on the server (string)
    ids = [] # valid and unique html id tags
    file_size = [] # like ls -h
    for l in os.listdir(phys_path):

        # full server-side file-system path
        file_path = os.path.join(phys_path,l)

        # creation date
        upload_date.append(time.ctime(os.path.getctime(file_path)))

        # file size
        file_size.append(GetHumanReadable_bytes(os.path.getsize(file_path)))

        # keep the filename
        ls.append(l)

        # id tags
        ids.append(hashlib.md5(str(l).encode('utf8')).hexdigest())

        # make directories stand out
        if os.path.isdir(file_path):
            style.append(True)
        else:
            style.append(False)

        # assemble markdown links
        url = os.path.join(os.path.basename(rel_path),l)
        links.append(url)

    return zip(ls, links, style, upload_date, ids, file_size)

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

def df(path='/'):
    f = os.statvfs(path)
    free_space = f.f_bavail*f.f_frsize
    total_space = f.f_blocks*f.f_frsize
    used_space = (1 - free_space/total_space) * total_space
    percentage_full = (1 - free_space/total_space) * 100

    fs = GetHumanReadable_bytes(free_space)
    ts = GetHumanReadable_bytes(total_space)
    us = GetHumanReadable_bytes(used_space)
    pf = "%.*f%%" % (0, percentage_full)

    return (fs, us, ts, pf)

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route("/<path:path>", methods=['GET', 'POST'])
def index(path):

    # Convert requested path to the path relative to the downloads directory.
    # This way the client sees the root as http://<host>/ but the actual
    # uploads directory can be something else.
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], path)

    if request.method == 'POST':

        # remove a file or directory
        if 'trash' in request.form.keys():
            url = os.path.join(request.url, request.form.get('trash'))
            rel_path = urllib.parse.urlsplit(url).path
            local_path = os.path.abspath(UPLOAD_FOLDER + rel_path)

            if os.path.exists(local_path):

                if os.path.isfile(local_path):
                    try:
                        os.remove(local_path)
                    except:
                        log.append('Failed to remove the file at: '+str(url))

                if os.path.isdir(local_path):
                    try:
                        os.rmdir(local_path)
                    except:
                        log.append('Failed to remove the directory at: '
                            + str(url) +' [make sure its empty first]')

        # make a directory
        elif 'dirname' in request.form.keys():
            url = os.path.join(request.url, request.form.get('dirname'))
            rel_path = urllib.parse.urlsplit(url).path
            local_path = os.path.abspath(UPLOAD_FOLDER + rel_path)

            if os.path.exists(local_path):
                log.append('Failed to add path at: '+str(url)+' [already exists]')

            else:
                try:
                    os.mkdir(local_path)
                except:
                    log.append('Failed to add path at: '+str(url))

        # upload a file
        elif request.files['file'] and AllowedFile(file.filename):
            file = request.files['file']
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_path, filename))

            # if its a post from js, then the js will handle this refresh
            return redirect(os.path.join(url_for('index'),path))

    # GET a file
    if os.path.isfile(upload_path):
        dirname = os.path.dirname(upload_path)
        basename = os.path.basename(upload_path)
        return send_from_directory(dirname, basename)

    # GET the main page
    #if os.path.isdir(upload_path):
    display_path = os.path.join('/',path)
    path_nav = LinkDisplayPath(display_path) # path navigation
    dirlinks = ListAndLinkDir(path, upload_path) # file links
    return render_template('directory_index.html', pathlist=path_nav, dirlinks=dirlinks, hostname=HOSTNAME, df=df(), flash=log.messages())

    # Server Error (the client can't get here)
    abort(500)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(host='tron.local', port=5000, debug=True)
