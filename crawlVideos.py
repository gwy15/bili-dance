import time
import os
import json
from multiprocessing.dummy import Pool
import threading
import queue
import pickle
import json
import functools

import requests
import progressbar


from models import getSession, Video


class BiliError(RuntimeError):
    pass


class WriterThread(threading.Thread):
    def __init__(self, queue, num):
        super().__init__()
        self.q = queue
        self.pbar = progressbar.ProgressBar(max_value=num)
        self.session = getSession('sqlite:///data.db')
        self.count = 0

    def run(self):
        self.pbar.start()
        while True:
            page, data = self.q.get()
            if data is None:
                break
            for vo in data:
                try:
                    v = Video.fromVO(vo)
                except Exception as ex:
                    print(ex)
                    print(vo)
                    raise
                self.session.merge(v)
            self.session.commit()
            self.count += 1
            self.pbar.update(self.count)
            with open('task.json', 'r') as f:
                data = json.load(f)
            data.remove(page)
            with open('task.json', 'w') as f:
                json.dump(data, f)
        self.pbar.finish()


class Spider:
    @staticmethod
    def getPage(page, ps=50, rid=20):
        referer = {
            20: 'otaku',
            154: 'three_d'
        }
        url = 'https://api.bilibili.com/x/web-interface/newlist?'
        url += f'callback=&rid={rid}&type=0&pn={page}&ps={ps}&jsonp=jsonp&_={int(time.time() * 1000)}'
        headers = {
            'Host': 'api.bilibili.com',
            'Referer': f'https://www.bilibili.com/v/dance/{referer[rid]}/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        }
        for i in range(5):
            try:
                resp = requests.get(url, headers=headers)
            except requests.ConnectionError:
                if i == 4:
                    raise
                print('\nConnection Error\n')
                time.sleep(5)
                continue

            if resp.status_code == 403:
                print('Request too frequent!')
                if i == 4:
                    raise RuntimeError('Request too frequent!')
                time.sleep(5)
                continue

            try:
                res = resp.json()
            except json.JSONDecodeError:
                if i == 4:
                    raise
                print('Json decode error')
                print(resp.text)
                time.sleep(5)
                continue

            break

        if res['code']:
            raise BiliError(res['message'])
        return res['data']

    def run(self, rid=20):
        if not os.path.exists('task.json'):
            total = self.getPage(1, rid=rid)['page']['count']
            pages = list(range(total // 50 + 2))
            with open('task.json', 'w') as f:
                json.dump(pages, f)
        else:
            with open('task.json') as f:
                pages = json.load(f)

        self.queue = queue.Queue()

        WriterThread(self.queue, len(pages)).start()

        func = functools.partial(self.runPage, rid=rid)

        with Pool(8) as pool:
            pool.map(func, pages)
        self.queue.put((None, None))

    def runPage(self, page, ps=50, rid=20):
        data = self.getPage(page, ps=ps, rid=rid)['archives']
        self.queue.put((page, data))
        time.sleep(1)


def main():
    Spider().run(rid=154)  # 三次元
    # Spider().run(rid=20) # 宅舞


if __name__ == "__main__":
    main()
