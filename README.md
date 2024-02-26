# bilibiliDownloader

## [GPL License](LICENSE)

## 介绍

项目分两个程序：

* `bDownloader.py`: b站视频下载器,支持指定 sessdata（可获得更高清晰度），支持选择清晰度。
* `blive.py`: b站直播间视频下载，支持 flv、ts、
m4a 等流视频格式。

注意：本程序仅供学习使用，请勿用于其他用途，由使用此程序造成的一切法律后果本人概不负责。

## 运行环境

* python 3.8

## 依赖

* beautifulsoup4
* ffmpeg

## 环境

1. 确保你的电脑安装了python3.8+,不会的自己百度,比如这种[点这里](https://blog.csdn.net/wade1203/article/details/104191338/ "呵呵")
2. 安装beautifulsoup4,打开cmd或powershell，输入：

    ```powershell
    pip install beautifulsoup4
    ```

3. 安装ffmpeg[点这里下载](https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2020-12-28-12-36/ffmpeg-N-100479-gd67c6c7f6f-win64-gpl-shared-vulkan.zip)
4. 解压到D:\Program Files之类的目录
5. 添加环境变量，桌面右键此电脑->属性->高级系统设置->高级->环境变量

    ![5](https://images.gitee.com/uploads/images/2020/1229/184054_934871d2_7688616.png "5.png")

6. 输入D:\Program Files\ffmpeg-N-100479-gd67c6c7f6f-win64-gpl-shared-vulkan\bin

    ![6](https://images.gitee.com/uploads/images/2020/1229/184357_57eff67e_7688616.png "6.png")

## 使用说明

1. 视频下载如果不想输命令可以双击运行 `bilibili.bat` 脚本.
2. 对于 `bDownloader.py` 有以下选项：

    ```txt
        -h/--help  显示帮助。
        -d  -d1等同-d为最高画质下载,-d2为中等画质，-d3为最低画质。
        -s/--sess <SESSDATA数据>  大会员视频下载支持
        -o <目录>  指定视频保存目录
    ```

3. 直播视频下载如果不想输命令可以双击运行 `blive.exe`.

## 其他

### 获取sessdata

1. 登你号
2. 点击小锁

    ![1](https://images.gitee.com/uploads/images/2020/1229/180403_82121fa5_7688616.png "1.png")

3. 点cookie

    ![2](https://images.gitee.com/uploads/images/2020/1229/181137_e00d5d30_7688616.png "2.png")

4. 找bilibili.com/cookie/SESSDATA

    ![3](https://images.gitee.com/uploads/images/2020/1229/181259_a6b530a0_7688616.png "3.png")

5. 复制这行文本,然后在下载时加入-s <SESSDATA>

    ![4](https://images.gitee.com/uploads/images/2020/1229/181311_f1f0497b_7688616.png "4.png")

> 各浏览器方法不尽相同，还请自行尝试😋。

## 申明

本程序仅供学习使用，请勿用于其他用途。
