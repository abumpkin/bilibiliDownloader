import urllib.request
from urllib.request import Request
import http.cookiejar
from http.cookiejar import Cookie
import html.parser
from bs4 import BeautifulSoup as Soup
import time
import sys,os
import gzip
import re
import json
import subprocess
from threading import Thread, Lock

welcomeText = '''\
======= b站直播视频下载程序 =======
  2022年1月10日 987413197@qq.com

  下载途中输入q并回车可退出下载
'''

#更新m3u8队列的时间间隔,秒
intervalTime = 2.0
connTimeout = 5.0
retryTimes = 3
global SAVE_PATH, SAVE_NAME
SAVE_PATH = os.path.abspath(".")
SAVE_NAME = ""

#结构：(prefix, raw)
m3u8Queue = []
m3u8UrlStack = []
m3u8Lock = Lock()
m3u8LastDownload = "#"
m3u8HeadURI = ""
m3u8ThreadExit = False
streamBaseUrl = ""
qnSet = set()

baseHeaders = {
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
        ' like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66',
    }
cookieJar = http.cookiejar.CookieJar()
cookieHandler = urllib.request.HTTPCookieProcessor(cookieJar)
Downloader = urllib.request.build_opener(cookieHandler)

def add_cookie(domain:str, name:str, value:str):
    global cookieJar
    cookie_t = Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=domain,
        domain_specified=False,
        domain_initial_dot=False,
        path="/",
        path_specified=True,
        secure=False,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={"HttpOnly": None},
        rfc2109=False,
    )
    cookieJar.set_cookie(cookie_t)

def pop_m3u8_queue()->str:
    try:
        popItem = m3u8Queue.pop(0)
        return popItem[1]
    except Exception:
        return ""

def push_m3u8_url_stk(url:str):
    m3u8UrlStack.insert(0, url)

def pop_m3u8_url_stk()->str:
    try:
        return m3u8UrlStack.pop(0)
    except Exception:
        return ""

def top_m3u8_url_stk()->str:
    try:
        return m3u8UrlStack[0]
    except Exception:
        return ""

def progressBar(progress:float)->str:
    num = 25
    progress *= 100
    fix = int(progress*num/10) % 10
    strReturn = '<'
    outputCharCount=int(progress*num/100)
    i = outputCharCount
    while (i := i - 1) + 1:
        strReturn += '='
    strReturn += str(fix)
    for i in range(num - 1 - outputCharCount):
        strReturn += ' '
    strReturn += '> '
    strReturn += "%.2f%%" % progress
    return strReturn
    #<========================>

def getHtml(url: str) -> str:
    global ERR, connTimeout
    htmlheader = baseHeaders.copy()
    htmlheader.update({ 
        'Cache-Control': 'no-cache',
        # 'Connection': 'keep-alive', # 服务器检测到断开会403forbidden
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'accept-encoding': 'gzip'})
    
    try:
        reqInfo = Request(url, headers=htmlheader)
        htmlResponse = Downloader.open(reqInfo, timeout = connTimeout)
        if(htmlResponse.headers["content-encoding"] == "gzip"):
            return gzip.decompress(htmlResponse.read()).decode("utf-8")
        else:
            return htmlResponse.read().decode("utf-8")
    except Exception as err:
        ERR = str(err)
        return None

def get_api_json(room:str):
    global qnChoice
    text = getHtml("https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo?\
room_id={0}&protocol=0,1&format=0,1,2&codec=0,1&qn={1}&platform=web&ptype=8 "\
        .format(room, qnChoice))
    return text

# 返回格式
# [{
#   "format": "..."
#   "codec": [{
#     "name": "avc|hevc"
#     "accept_qn": [...]
#     "sources": [...]
#   }, ...]
# }, ...]
def getStream(text:str, isJson:bool = False) :
    global ERR, qnSet
    qnSet.clear()
    jsonData:str = text
    try:
        if(isJson == False):
            doc = Soup(text, features="html.parser")
            jsonData = doc.find(text=re.compile(\
                r"(?m)(window\.__NEPTUNE_IS_MY_WAIFU__(?=\s*=\s*{))"))
            jsonData = jsonData[jsonData.find('{'):]

        jsonObj = json.loads(jsonData)
        try:
            stream = jsonObj["roomInitRes"]["data"]["playurl_info"]["playurl"]["stream"]
        except:
            stream = jsonObj["data"]["playurl_info"]["playurl"]["stream"]
        streamFormats = [stream[i]["format"] for i in range(0, len(stream))]
        streamFormats = [p for i in streamFormats for p in i]
        streamFormats = [{"format": i["format_name"], "codec": i["codec"]} \
            for i in streamFormats]
        for i in streamFormats:
            for p in i["codec"]:
                qnSet.update(p["accept_qn"])
            i["codec"] = [{"name": p["codec_name"], \
                "accept_qn": p["accept_qn"], \
                "sources": [ \
                    o["host"] + p["base_url"] + o["extra"] for o in p["url_info"] \
                ]} for p in i["codec"] if p["base_url"] != ""]
    except Exception as err:
        ERR = str(err)
        return None
    return streamFormats

def get_host_url(url:str)->str:
    repress = re.compile(r"(?i)(https://.*(?=/))")
    ret = repress.match(url)
    if(ret != None):
        return ret.group(0)
    return url

def url_remove_param(url:str)->str:
    repress = re.compile(r"(.*(?=\?))")
    ret = repress.match(url)
    if(ret != None):
        return ret.group(0)
    return url

def url_get_param(url:str)->str:
    repress = re.compile(r"((?<=\?).*)")
    ret = repress.search(url)
    if(ret != None):
        return '?' + ret.group(0)
    return ""

def url_set_qn(url:str, qn:int)->str:
    repress = re.compile(r"(.*qn=)\d*(&.*|)")
    ret = repress.match(url)
    if(ret != None):
        # print(ret.groups())
        return ret.group(1) + str(qn) + ret.group(2)
    return url + "&qn=" + str(qn)

def get_room_id(url:str)->str:
    repress = re.compile(r"(?i)((?<=/)\d+(?=/|))")
    ret = repress.search(url)
    if(ret != None):
        return ret.group(0)
    return ""

def m3u8_get_head(text:str):
    repress = re.compile(r"(?i)(?m)((?<=#EXT-X-MAP:URI=\").*(?=\"))")
    ret = repress.search(text)
    if(ret != None):
        return ret.group(1)
    return ""

def update_m3u8_queue()->bool:
    global streamBaseUrl, m3u8UrlStack
    global qnChoice
    global m3u8LastDownload
    global m3u8HeadURI
    if(len(m3u8UrlStack) == 0):
        return False
    m3u8Text = getHtml(top_m3u8_url_stk())
    if(m3u8Text == None):
        if(len(m3u8UrlStack) > 0):
            pop_m3u8_url_stk()
            return update_m3u8_queue()
        return False
    repress = re.compile(r"(?m)(^(?=\b|/)(?![\#.*$]).*$)")
    li = repress.findall(m3u8Text)
    di = [(url_remove_param(i), i) for i in li]
    # print(li)
    #检查链接嵌套
    if(len(li) > 0 and li[0].find("https") != -1):
        push_m3u8_url_stk(li[0])
        update_m3u8_queue()
    else:
        streamBaseUrl = get_host_url(top_m3u8_url_stk())
        lastItem = "#"
        m3u8Lock.acquire()
        if m3u8_get_head(m3u8Text) != m3u8HeadURI:
            m3u8HeadURI = m3u8_get_head(m3u8Text)
            m3u8Queue.extend([(m3u8HeadURI, m3u8HeadURI)])
        if(len(m3u8Queue) > 0):
            lastItem = m3u8Queue[len(m3u8Queue) - 1][0]
        else:
            lastItem = m3u8LastDownload
        try:
            index = -1
            for i, v in enumerate(di):
                if(v[0] == lastItem):
                    index = i
                    break
            if(index == -1):
                raise Exception(-1)
            m3u8Queue.extend(di[index + 1:])
        except Exception:
            m3u8Queue.extend(di)
        m3u8Lock.release()
    return True

def showStreamInfo(stream:str):
    for k, i in enumerate(stream):
        print('格式:\n[{0}] {1}'.format(k, i["format"]))
        print('  编码:')
        for ik, ii in enumerate(i["codec"]):
            print('    [{0}] {1} 可用画质{2}'.format(ik, ii["name"], ii["accept_qn"]))


def flv_download_thread(url:str, path:str = ".", filename:str = ""):
    global live_room_url, ERR, connTimeout
    size = 0
    previousSize = 0
    chunkSize = 512
    refreshInSec = 0.2
    start_time = time.time()
    if filename == "":
        filename = get_room_id(live_room_url) + ".flv"
    header = baseHeaders.copy()
    header.update({ 
        'Cache-Control': 'no-cache',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'accept-encoding': 'identity'})
    reqInfo = Request(url, headers=header)
    try:
        dataResponse = Downloader.open(reqInfo, timeout = connTimeout)
    except Exception as err:
        ERR = str(err)
        print("下载完成")
        return False
    with open(os.path.join(path,filename),"ab+") as f:
        while chunk := dataResponse.read(chunkSize):
            f.write(chunk)
            size += chunkSize
            if time.time() - start_time > refreshInSec:
                start_time = time.time()
                outputStr = "\r"
                outputStr += " 已下载：" + "%.2f" % (size/1024/1024) +' MB'
                outputStr += " 下载速度：" + "%.3f" % ((size-previousSize)/1024/1024/refreshInSec) +' MB/s  '
                sys.stdout.write(outputStr)
                previousSize = size
            f.flush()
    print("下载完成")
    return True

def data_download(url:str, format:str, filename:str = "", path:str = ".")->int:
    global connTimeout, retryTimes
    header = baseHeaders.copy()
    header.update({ 
        'Cache-Control': 'no-cache',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        # 'Connection': 'keep-alive',
        'accept-encoding': 'identity'})
    if filename == "":
        filename = get_room_id(live_room_url) + "." + format
    # if not os.path.exists(path):
    #     os.makedirs(path)
    reqInfo = Request(url, headers=header)
    times = 0
    stat = False
    while times <= retryTimes and not stat:
        try:
            dataResponse = Downloader.open(reqInfo, timeout = connTimeout)
            with open(os.path.join(path,filename),"ab+") as f:
                buf = dataResponse.read()
                size = f.write(buf)
                f.flush()
        except Exception as err:
            ERR = str(err)
            size = 0
            times += 1
        stat = True
    return size

def m3u8_update_thread():
    global retryTimes, m3u8ThreadExit
    times = 0
    while times <= retryTimes:
        if not update_m3u8_queue():
            times += 1
        time.sleep(intervalTime)
    m3u8ThreadExit = True
    print("m3u8更新线程退出")

def m3u8_download_thread(format:str, path:str = ".", filename:str = ""):
    global streamBaseUrl, m3u8LastDownload
    global m3u8HeadURI, m3u8ThreadExit
    m3u8HeadURI = ""
    totalSize = 0
    start_time = time.time()
    while True:
        m3u8Lock.acquire()
        cur_url = pop_m3u8_queue()
        if cur_url != "":
            m3u8LastDownload = url_remove_param(cur_url)
        m3u8Lock.release()
        if cur_url != "":
            if format == "fmp4":
                url = streamBaseUrl + '/' + cur_url + url_get_param(top_m3u8_url_stk())
                size_ret = data_download(url, "m4s", filename, path)
                # with open(os.path.join(".", roomid, roomid + ".m3u8"), "a+") as f:
                #     f.writelines([cur_url + "\n"])
                #     f.flush()
            else:
                url = streamBaseUrl +  cur_url
                size_ret = data_download(url, format, filename, path)
            totalSize += size_ret
        else:
            if m3u8ThreadExit:
                print("下载完成")
                return None
            time.sleep(intervalTime)
        d_time = time.time() - start_time
        outputStr = "\r"
        outputStr += " 已下载：" + "%.2f" % (totalSize/1024/1024) +' MB'
        outputStr += " 下载速度：" + "%.3f" % ((totalSize)/1024/1024/d_time) +' MB/s  '
        outputStr += "[{0}]  ".format(m3u8LastDownload)
        sys.stdout.write(outputStr)

def get_no_exists_filename(path:str, filename:str)->str:
    count = 0
    newFilename = filename
    repr = re.compile(r"(.*)(\..*$)")
    ret = repr.search(filename)
    while True:
        if os.path.exists(os.path.join(path, newFilename)):
            if(ret == None):
                newFilename = filename + "_" + str(count := count + 1)
            else:
                newFilename = ret.group(1) + " ({0})".format(count := count + 1) + ret.group(2)
        else:
            break
    return newFilename

def get_int(s:str)->int:
    repress = re.compile(r"(\d*)")
    ret = repress.search("0" + s)
    if(ret != None):
        return int(ret.group(1))
    return 0

if __name__ == "__main__":
    global qnChoice, live_room_url
    live_room_url = "https://live.bilibili.com/22528847"
    add_cookie("bilibili.com", "SESSDATA", "d822017f%2C1648905421%2C8a4c3%2Aa1")
    print(welcomeText)
    live_room_url = input("输入直播链接:")
    roomid = get_room_id(live_room_url)
    html = getHtml(live_room_url)
    stream = getStream(html)
    if stream == None:
        print("链接无效")
        exit()

    print("可用画质:", sorted(qnSet, reverse=True))
    while True:
        qnChoice = get_int(input("输入画质:"))
        if qnChoice in qnSet:
            break
    apiJson = get_api_json(get_room_id(live_room_url))
    stream = getStream(apiJson, True)
    showStreamInfo(stream)
    
    while True:
        formatChoice = get_int(input("输入格式编号:"))
        if formatChoice >= 0 and formatChoice < len(stream):
            break
    while True:
        codecChoice = get_int(input("输入编码编号:"))
        if codecChoice >=0 and codecChoice < len(stream[formatChoice]["codec"]):
            break

    fileFormat = stream[formatChoice]["format"]
    if fileFormat == "fmp4":
        fileFormat = "m4s"
    SAVE_NAME = input("输入保存文件名:")
    path = input("输入保存目录:")
    if path != "":
        SAVE_PATH = path
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
    SAVE_PATH = os.path.abspath(SAVE_PATH)
    if SAVE_NAME != "":
        SAVE_NAME += "." + fileFormat
    else:
        SAVE_NAME = roomid + "." + fileFormat
    SAVE_NAME = get_no_exists_filename(SAVE_PATH, SAVE_NAME)

    print("文件保存目录:" + os.path.join(SAVE_PATH, SAVE_NAME))

    if(stream[formatChoice]["format"] == "flv"):
        downloadThread = Thread(target=flv_download_thread, \
            args=((stream[formatChoice]["codec"][codecChoice]["sources"][0]), \
                (SAVE_PATH), (SAVE_NAME)), \
            name="downloader")
        downloadThread.setDaemon(True)
        downloadThread.start()
    else:
        m3u8ThreadExit = False
        m3u8UrlStack.extend(stream[formatChoice]["codec"][codecChoice]["sources"])
        updatingThread = Thread(target = m3u8_update_thread, daemon=True)
        downloadThread = Thread(target=m3u8_download_thread, daemon=True, \
            args=((stream[formatChoice]["format"]), (SAVE_PATH), (SAVE_NAME)))
        updatingThread.start()
        downloadThread.start()

    while True:
        if input() == "q":
            exit()

