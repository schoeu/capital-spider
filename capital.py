import re
import os
import json
import time
import requests
from bs4 import BeautifulSoup
import utils
import db
import conf
import json
import datetime

config = conf.getconfig()

ids = []
typeinfos = []
yesterday = str(datetime.date.today() - datetime.timedelta(days=1))

# get news list data by new type.
def gettypepage(url):
    ts = config['newstype']
    for i in ts:
        v = 0
        global typeinfos
        typeinfos = []
        while True:
            rurl = url.format(type= i, pagenum= v)
            r = requests.get(rurl)
            content = r.content
            if content:
                rsstr = content.decode(encoding = "utf-8")[5:-1]
                rs = json.loads(rsstr)
                ct = typeinfofilter(rs)
            v += 1
            if  len(ct) > 150 or v > 1000:
                contentrs = getpagecontent(ct)
                savetypeinfo(ct)
                savecontentdata(contentrs)
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), i, len(ct))
                break

# news data filter.
def typeinfofilter(rs):
    if rs and len(rs['data']) > 0:
        for i in rs['data']:
            if not i['rowkey'] in ids:
                ids.append(i['rowkey'])
                filter = (i['rowkey'], i['date'], i['hotnews'], i['lbimg'][0]['src'], '$$'.join([i['src'] for i in i['miniimg']]), i['source'], i['topic'].replace("'","\\\'"), i['url'], i['urlfrom'], i['type'], i['urlpv'])
                if filter and len(filter) == 11 and filter[1] > yesterday:
                    typeinfos.append(filter)
    return typeinfos

# save type info.
def savetypeinfo(ctt):
    basesql = 'insert into articles (row_key, date, hot_news, lb_img, thumbnail_pics, source, topic, url, url_from, category, url_pv) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    db.executemany(basesql, ctt)
    print('savetypeinfo')

# get news content.
def getpagecontent(ct):
    ctt = []
    for i in ct:
        u = i[7]
        if u:
            content = utils.gethtml(u)
            rs = contentfilter(u, i[0], content)
            if rs and len(rs) == 6:
                ctt.append(rs)
    return ctt 

# news content filter
def contentfilter(u, rk, rs):
    soup = BeautifulSoup(rs, "lxml")
    # parse main page info
    titlesrc = soup.select('.title')
    if not titlesrc:
        return
    title = titlesrc[0].get_text().replace("'","\\\'")
    source = soup.select('.article-src-time > span')[0].get_text()
    searchObj = re.search( r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+来源：(.*)', source, re.M|re.I)
    t = searchObj.group(1)
    s = searchObj.group(2)
    content = soup.select('.J-article-content')[0]
    ctt = []
    sqlarr = []
    for i in content.children:
        if i.name:
            if i.name == 'p':
                ctt.append({
                    'name': 'text',
                    'content': i.get_text()
                })
            elif i.name == 'figure':
                img = i.find('img')
                src = img.attrs['src']
                if src:
                    ctt.append({
                        'name': 'img',
                        'content': src
                    })
    return rk, t, title, json.dumps(ctt), s, u
    
# save news content to db.
def savecontentdata(data):
    # save data
    basesql = 'insert into article_contents (row_key, date, topic, content, source, url) values (%s, %s, %s, %s, %s, %s)'
    db.executemany(basesql, data)
    print('savecontentdata')

# get news ids.
def getexistingid():
    global ids
    sql = "SELECT row_key FROM article_contents where date > '{}'".format(yesterday)
    cursor = db.select(sql)
    rs = cursor.fetchall()
    ids = [i[0] for i in rs]

# main
def main():
    # update existing id
    getexistingid()

    # get list data
    gettypepage(config['url'])

    # finally
    db.closeconn()

if __name__ == '__main__':
    main()
    
