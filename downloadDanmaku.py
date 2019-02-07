import requests
import io
import os
import xml.etree.cElementTree as ET

from progressbar import progressbar
from sqlalchemy.sql.expression import func

import models
import config

class DanmakuDownloader:
    def __init__(self):
        self.cidSession = requests.session()
        self.danmakuSession = requests.session()

    def getCids(self, video: models.Video):
        res = self.cidSession.get(
            f'https://www.bilibili.com/widget/getPageList?aid={video.aid}').json()
        return [item['cid'] for item in res]

    def getDanmaku(self, cid):
        res = self.cidSession.get(f'https://comment.bilibili.com/{cid}.xml')
        with io.StringIO(res.content.decode('utf8')) as f:
            tree = ET.ElementTree(file=f)
        for d in tree.iterfind('d'):
            yield d.text

    def getAllDanmakuForVideo(self, video: models.Video):
        with io.StringIO() as f:
            for cid in self.getCids(video):
                for d in self.getDanmaku(cid):
                    print(d, file=f)
            with open(f'danmaku/{video.aid}.txt', 'w', encoding='utf8') as fp:
                fp.write(f.getvalue())



def main():
    downloader = DanmakuDownloader()
    s = models.getSession(config.DB_PATH)
    videos = s.query(models.Video).order_by(func.random()).all()
    for video in progressbar(videos):
        if os.path.exists(f'danmaku/{video.aid}.txt'):
            continue
        downloader.getAllDanmakuForVideo(video)


if __name__ == "__main__":
    main()


class Item(object):
    pass
