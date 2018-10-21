import os
import json
import urllib.request
import gzip
import io
import conf

config = conf.getconfig()

headers = {
    'Accept': '*/*',
    'User-Agent': config['ua'],
    'accept-encoding': 'gzip, deflate, brg',
    'cookie': config['cookie'],
    'Host': config['host'],
    'Referer': config['referer'],
    'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8,zh-TW;q=0.7,ja;q=0.6,uk;q=0.5',

}

def mkdirs(path):
    path = path.strip()
    isExists = os.path.exists(path)
    if isExists:
        return False
    else:
        os.makedirs(path)
        return True

def getcwd():
    return os.getcwd()

def savejson(path, data):
    with open(path, 'w') as jsonfile:
        json.dump(data, jsonfile, ensure_ascii=False)

def getjsondata(path):
    f = open(path)
    data = json.loads(f.read())
    return data

def gethtml(urls):
    rs = ''
    try:
        response = urllib.request.Request(urls, headers = headers)
        html = urllib.request.urlopen(response, timeout=100.0)
        encoding = html.info().get('Content-Encoding')
        if html.getcode() == 200:
            if encoding == 'gzip':
                buf = io.BytesIO(html.read())
                gf = gzip.GzipFile(fileobj=buf)
                content = gf.read()

        if content:
            rs = content.decode('utf-8')
        
    except:
        print('Url error')
    return rs