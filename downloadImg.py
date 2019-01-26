import re
import threading
import queue

import requests
from sqlalchemy.sql.expression import func
import progressbar

from models import getSession, Video, VDownload

REGEXP = re.compile('\w+\.\w+$')


class Producer(threading.Thread):
    def __init__(self, q_in, q_out, num=8):
        super().__init__()
        self.q_in = q_in
        self.q_out = q_out
        self.num = num
        self.count = 0
        self.pbar = None

    def run(self):
        self.session = getSession('sqlite:///data.db')
        q = self.session.query(VDownload).filter(VDownload.status == False)
        self.total = q.count()
        if self.total == 0:
            print('全部下载完成')
        else:
            self.pbar = progressbar.ProgressBar(max_value=self.total)
            self.pbar.start()

        for vd in q.limit(self.num).all():
            self.q_out.put((vd.aid, vd.picurl))

        while True:
            item = self.q_in.get()
            self.session.query(VDownload).filter(
                VDownload.aid == item[0]
            ).update({'status': True})
            self.session.commit()

            self.count += 1
            self.pbar.update(self.count)

            vd = self.session.query(VDownload).order_by(
                func.random()).limit(1).first()
            if vd is None:
                print('下载完成')
                for i in range(self.num):
                    self.q_out.put(None)
                break
            else:
                self.q_out.put((vd.aid, vd.picurl))
        self.pbar.finish()


class Consumer(threading.Thread):
    def __init__(self, q_in, q_out):
        super().__init__()
        self.q_in = q_in
        self.q_out = q_out

    def run(self):
        session = requests.session()
        while True:
            item = self.q_in.get()
            if item is None:
                break
            url = item[1]
            url = url.replace('http://', 'https://')
            fn = REGEXP.findall(url)
            assert len(fn) == 1
            fn = fn[0]
            im = session.get(url).content
            with open('download/' + fn, 'wb') as f:
                f.write(im)
            self.q_out.put(item)


def main():
    q1 = queue.Queue()
    q2 = queue.Queue()
    Producer(q1, q2).start()
    for i in range(8):
        Consumer(q2, q1).start()


if __name__ == "__main__":
    main()
