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

config = conf.getconfig()

def gettypepage(url):
    ts = config['newstype']
    for i in ts:
        v = 0
        while True:
            rurl = url.format(type= i, pagenum= v)
            r = requests.get(rurl)
            content = r.content
            if content:
                rsstr = content.decode(encoding = "utf-8")[5:-1]
                rs = json.loads(rsstr)
                typeinfofilter(rs)

            v += 1
            #if len(rs['data']) > 0:
            print(v, i)
            if v > 500:
                break
    
def typeinfofilter(rs):
    ctt = []
    if rs and len(rs['data']) > 0:
        for i in rs['data']:
            filter = (i['rowkey'], i['date'], i['hotnews'], i['isvideo'], i['lbimg'][0]['src'], '$$'.join([i['src'] for i in i['miniimg']]), i['source'], i['topic'].replace("'","\\\'"), i['url'], i['urlfrom'], i['type'], i['urlpv'], i['clkrate'], str(i['ctrtime']))
            ctt.append(filter)
    basesql = 'insert into articles (row_key, date, hot_news, is_video, lb_img, thumbnail_pics, source, topic, url, url_from, category, url_pv, click_rate, ctr_time) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    db.executemany(basesql, ctt)

def getpagecontent():
    idx = 0
    sql = 'select distinct row_key, url from articles'
    cursor = db.select(sql)
    rs = cursor.fetchall()
    for i in rs:
        u = i[1]
        if u:
            content = utils.gethtml(u)
            contentfilter(u, i[0], content)
            idx += 1
            print(idx, u)

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
    

    # save data
    basesql = 'insert into article_contents (row_key, date, topic, content, source, url) values (%s, %s, %s, %s, %s, %s)'
    db.execute(basesql, (rk, t, title, json.dumps(ctt), s, u))

def main():
    # get list data
    #gettypepage(config['url'])

    # get content data
    getpagecontent()

    # finally
    db.closeconn()

if __name__ == '__main__':
    main()
    
