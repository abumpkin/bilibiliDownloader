#  2020/12/26 创建项目
#  2020/12/30 增加-o选项,修复几个小bug
#  2020/12/31 小改
#  2021/6/19 20:00左右程序失效，已修复

import urllib.request
from urllib.request import Request
import html.parser
from bs4 import BeautifulSoup as Soup
import time
import sys,os
import gzip
import re
import json
import subprocess
import http.cookiejar


cookie = http.cookiejar.CookieJar()
cookieHandler = urllib.request.HTTPCookieProcessor(cookie)
Downloader = urllib.request.build_opener(cookieHandler)

def progressBar(progress:float)->str:
    num = 25
    progress *= 100
    fix = int(progress*num/10) % 10
    strReturn = '<'
    outputCharCount=int(progress*num/100)
    for i in range(outputCharCount):
        strReturn += '='
    strReturn += str(fix)
    for i in range(num - 1 - outputCharCount):
        strReturn += ' '
    strReturn += '> '
    strReturn += "%.2f%%" % progress
    return strReturn
    #<========================>

def download(path,filename:str,HttpResponse,/):
    dataLen = HttpResponse.headers['Content-Length']
    with open(os.path.join(path,filename),"wb+") as f:
        size = 0
        previousSize = 0
        refreshInSec = 0.2
        start_time = time.time()
        totalTime = start_time
        while chunk := HttpResponse.read(512):
            f.write(chunk)
            size += 512
            if time.time() - start_time > refreshInSec:
                start_time = time.time()
                outputStr = "\r"+ progressBar(size/int(dataLen))
                outputStr += " 已下载：" + "%.2f" % (size/1024/1024) +' MB'
                outputStr += " 下载速度：" + "%.3f" % ((size-previousSize)/1024/1024/refreshInSec) +' MB/s  '
                sys.stdout.write(outputStr)
                previousSize = size
        totalTime = time.time() - totalTime
        sys.stdout.write("\r" + ' ' * 80)
        sys.stdout.write("\r文件大小：" + "%.3f" % (size/1024/1024) + ' MB'
        " 平均下载速度：" + "%.3f" % (int(dataLen)/totalTime/1024/1024) + ' MB/s')
        f.flush()
        f.close()

def epid2json(ep_id:str)->str:
    apiUrl = 'https://api.bilibili.com/pgc/player/web/playurl?'
    urlArgs = [
        "fnval=80",
        "otype=json",
        "ep_id=" + ep_id
    ]
    apiUrl = apiUrl + "&".join(urlArgs)
    response = Downloader.open(Request(apiUrl,headers=headers))
    if response.headers['content-encoding'] == 'gzip':
        jsond = gzip.decompress(response.read()).decode("utf-8")
    else:
        jsond = response.read().decode("utf-8")
    return jsond

def excuteCommand(com):
    ex = subprocess.Popen(com, stdout=subprocess.PIPE, shell=True)
    out, err = ex.communicate()
    status = ex.wait()
    print(out.decode())
    return out.decode()

def helper()->str:
    return '''说明：
    用法：命令 [选项] <url>
    选项：
    -h/--help  显示此帮助。
    -d  -d1等同-d为最高画质下载,-d2为中等画质，-d3为最低画质。
    -s/--sess <SESSDATA数据>  大会员视频下载支持
    -o <目录>  指定视频保存目录'''

def main(argv:list,headers):
    parameterList = ["-h","--help","-d","-d1","-d2","-d3","-s","--sess","-o"]
    absPath = os.path.split( os.path.realpath( sys.argv[0] ) )[0]
    outputPath = ""
    if "-h" in argv or "--help" in argv:
        print(helper())
        sys.exit()
    lastArg:str = argv.pop()
    if lastArg.find("http") != -1:
        url = lastArg
    else:
        print('非法url')
        print(helper())
        sys.exit()
    if "-s" in argv or "--sess" in argv:
        if "-s" in argv:
            index = argv.index("-s") + 1
        if "--sess" in argv:
            index = argv.index("--sess") + 1
        if index!=len(argv):
            if argv[index] not in parameterList:
                #headers['Cookie'] = "SESSDATA=" + argv[index]
                C = http.cookiejar.Cookie( 0, "SESSDATA", argv[index],
                 None, False,
                 ".bilibili.com", True, True,
                 "/", False,
                 False,
                 None,
                 True,
                 None,
                 None,
                 None,
                 rfc2109=False,
                 )
                cookie.set_cookie(C)
                argv.pop(index)
        argv.pop(index - 1)
    if "-o" in argv:
        index = argv.index("-o") + 1
        if index!=len(argv):
            if argv[index] not in parameterList:
                if os.path.exists(argv[index]):
                    outputPath = argv[index]
                argv.pop(index)
        argv.pop(index - 1)
    if outputPath=="":
        outputPath = absPath
    R = Request(url,headers=headers)
    print("正在请求网络连接...")
    try:
        htmlResponse = Downloader.open(R)
    except Exception as info:
        print("连接发生错误",info)
        input()

    if htmlResponse.headers['content-encoding'] == 'gzip':
        html = gzip.decompress(htmlResponse.read()).decode("utf-8")
    else:
        html = htmlResponse.read().decode("utf-8")
    print("正在解析网页...")
    doc = Soup(html,features="html.parser")
    fileName = doc.select("head > title")[0].text + '.mp4'
    for rchar in ('/','\\',':','*','?','"','<','>','|'):
        fileName = fileName.replace(rchar,"-")
    if os.path.exists(os.path.join(outputPath,fileName)):
        while True:
            choice = input(os.path.join(outputPath,fileName) + "\n文件已存在，是否替换？[y/n]")
            if choice.lower() == "y":
                os.remove(os.path.join(outputPath,fileName))
                break
            if choice.lower() == "n":
                sys.exit()
    jsonData = doc.find(text=re.compile('window.__playinfo__'))
    # ep
    if jsonData == None:
        check = url[url.rfind('/') + 1:]
        if check.find("ep")!=-1:
            epid = check[check.find("ep") + 2:]
            if epid.find("?")!=-1:
                epid = epid[:epid.find("?")]
        else:
            jsonData = doc.find(text=re.compile('window.__INITIAL_STATE__'))
            if jsonData == None:
                print("解析失败!")
                input("按回车结束")
                sys.exit()
            jsonData:str = jsonData[jsonData.find("{"):jsonData.rfind("};")+1]
            try:
                eplist = json.loads(jsonData)["epList"]
            except:
                print("解析失败!")
                input("按回车结束")
                sys.exit()
            epid = str(eplist[0]['id'])
            fileName = eplist[0]['titleFormat'] + fileName
        print("epid:",epid)
        jsonData:str = epid2json(epid)
        try:
            objs = json.loads(jsonData)['result']['dash']
        except:
            print("解析失败!",json.loads(jsonData)["message"])
            input("按回车结束")
            sys.exit()
    # 普通视频
    else:
        jsonData:str = jsonData[jsonData.find("{"):]
        try:
            objs = json.loads(jsonData)['data']['dash']
        except:
            try:
                objs = json.loads(jsonData)['data']['durl']
                objs[0]['url']
            except:
                print("解析失败!",json.loads(jsonData)["message"])
                input("按回车结束")
                sys.exit()
    try:
        videos = objs['video']
    except:
        videos = None

    try:
        audios = objs['audio']
    except:
        audios = None

    vurl = None
    aurl = None
    audio = None
    video = None
    payload={}
    d_headers = {
    'range': ' bytes=0-',
    'referer': ' https://www.bilibili.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
    ' like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66',
    }
    if videos==None and objs!=None:
        vurl = objs[0]['url']
        fileName = "预览-" + fileName
        print("解析成功，开始下载视频...")
    else:
        if '-d' not in argv and '-d1' not in argv and '-d2' not in argv and '-d3' not in argv:
            print("解析成功，请选择视频清晰度：")
            for index,video in enumerate(videos):
                sys.stdout.write('['+str(index)+']'+'分辨率：'+str(video["width"])+'x'+str(video["height"]))
                sys.stdout.write(" 视频编码：")
                sys.stdout.write(video["codecs"] if ("codecs" in video) else "未知")
                for taudio in audios:
                    if taudio["id"] == 30200 + video["id"]:
                        audio = taudio
                if audio == None:
                    audio = audios[0]
                sys.stdout.write(" 音频编码："+("未知" if ("codecs" not in audio) else audio["codecs"])+"\r\n")
            audio = None
            sys.stdout.write("请输入方括号里的数字或输入q取消下载：")
            while True:
                choice = input()
                if(choice == "q"):
                    sys.exit()
                try:
                    int(choice)
                except:
                    sys.stdout.write("输入不正确，请重新输入：")
                    continue
                if len(videos) > int(choice) and int(choice) >= 0:
                    video = videos[int(choice)]
                    for taudio in audios:
                        if taudio["id"] == 30200 + video["id"]:
                            audio = taudio
                    if audio == None:
                        audio = audios[0]
                    break
                sys.stdout.write("输入不正确，请重新输入：")

        else:
            if '-d2' in argv:
                index = len(videos)//2
                video = videos[index]
                for taudio in audios:
                    if taudio["id"] == 30200 + video["id"]:
                        audio = taudio
                if audio == None:
                    audio = audios[0]
            elif '-d3' in argv:
                index = len(videos) - 1
                video = videos[index]
                for taudio in audios:
                    if taudio["id"] == 30200 + video["id"]:
                        audio = taudio
                if audio == None:
                    audio = audios[0]

    if audio == None and video == None and vurl == None:
        video = videos[0]
        audio = audios[0]
    if vurl == None:
        vurl = video["baseUrl"]
        aurl = audio["baseUrl"]
    try:
        print("视频分辨率："+str(video["width"])+'x'+str(video["height"]))
    except:
        pass

    R = Request(vurl,headers = d_headers)
    response = Downloader.open(R)
    if aurl != None:
        download(absPath,"video.mp4",response)
        response.close()
        print("\n视频下载完成！\n输出:",os.path.join(absPath , 'video.mp4'))
        print("开始下载音频...")
        R = Request(aurl,headers = d_headers)

        loop = True
        while loop:
            try:
                response = Downloader.open(R)
                loop = False
            except:
                pass

        download(absPath,"audio.mp4",response)
        response.close()
        print("\n音频下载完成！\n输出：",os.path.join(absPath , 'audio.mp4'))
        print("开始合并视音频...")
        time.sleep(0.4)

        command:str = 'ffmpeg.exe -i "'+ os.path.join(absPath , 'audio.mp4') + '" -i "' + \
            os.path.join(absPath , 'video.mp4') + '" -acodec copy -vcodec copy "' + os.path.join(outputPath,fileName) +'"'
        # os.popen(command)
        excuteCommand(command)
        print("合并完成！")
    else:
        download(outputPath, fileName, response)
        response.close()
    print("下载保存目录：",outputPath)
    print("下载输出文件名：",fileName)

if __name__ == '__main__':
    headers = {
        'Accept': '*/*',
        'Cache-Control': 'no-cache',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'accept-encoding': 'gzip',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
        ' like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66',
    }
    main(sys.argv,headers)