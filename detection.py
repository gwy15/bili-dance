from pprint import pprint
import datetime
import base64
import typing

import requests
import sqlalchemy
from sqlalchemy.sql.expression import func
from progressbar import progressbar

import models
import config

with open('API_KEY', 'r') as f:
    API_KEY = f.read()
URL = 'https://vision.googleapis.com/v1/images:annotate?key={}'.format(API_KEY)


class CloudVisionManager:
    'https://cloud.google.com/vision/docs/request'

    def __init__(self):
        self.session = requests.session()
        self.s = models.getSession(config.DB_PATH)

    def getResults(self, records: typing.List[models.Video]):
        params = {
            "requests": [
                {
                    "features": [{
                        'type': 'LABEL_DETECTION'
                    }, {
                        "type": "SAFE_SEARCH_DETECTION"
                    }],
                    "image": {"source": {
                        "imageUri": record.picurl
                    }}
                } for record in records
            ]
        }
        res = self.session.post(URL, json=params).json()
        if res.get('error', None):
            pprint(params)
            pprint(res['error'])
            raise RuntimeError(res['error']['message'])

        return [item for item in res['responses']]

    def getResultByDownloading(self, record: models.Video):
        im = requests.get(record.picurl).content
        imbase64 = base64.encodebytes(im)
        params = {
            "requests": [{
                "features": [{
                    'type': 'LABEL_DETECTION'
                }, {
                    "type": "SAFE_SEARCH_DETECTION"
                }],
                "image": {
                    "content": imbase64.decode()
                }
            }]
        }
        res = self.session.post(URL, json=params).json()
        if res.get('error', None):
            pprint(res['error'])
            raise RuntimeError(res['error']['message'])
        res = res['responses']
        assert len(res) == 1
        return res[0]

    def getBatch(self, records: typing.List[models.Video]):
        annos = self.getResults(records)
        for record, anno in zip(records, annos):
            if anno.get('error', None):
                if anno['error']['code'] not in (4, 14):
                    print(f'\naid: {record.aid}, url: {record.picurl}')
                    print('\ncode: ' + str(anno['error']['code']) + ', ' + anno['error']['message'] + '\n\n')
                    raise RuntimeError(anno['error']['message'])
                else:  # download
                    # print('using download method.')
                    anno = self.getResultByDownloading(record)

            safeAnno = models.SafeAnnotation.fromVO(
                anno['safeSearchAnnotation'])
            safeAnno.aid = record.aid
            self.s.merge(safeAnno)

            labels = [models.Label.fromVO(vo)
                      for vo in anno.get('labelAnnotations', [])]
            for label in labels:
                label.aid = record.aid
                self.s.merge(label)
        self.s.commit()

    def run(self, batch_size=16, batch_num=20):
        print('已完成:', self.s.query(models.SafeAnnotation).count(), end=', ')
        print('总数量:', self.s.query(models.Video).count())
        query: sqlalchemy.orm.Query
        query = self.s.query(models.Video)\
            .filter(~ sqlalchemy.exists().where(models.Video.aid == models.SafeAnnotation.aid))\
            .filter(models.Video.picurl.notlike(r'%gif'))\
            .order_by(models.Video.views.desc())
            # .order_by(func.random())
        # print(', 剩余任务:', query.count())

        records = query.limit(batch_size * batch_num).all()
        # print('最低播放:', records[-1].views)
        for i in progressbar(range(batch_num)):
            batch = records[i*batch_size: (i+1)*batch_size]
            self.getBatch(batch)


if __name__ == "__main__":
    CloudVisionManager().run(batch_size=16, batch_num=20)
