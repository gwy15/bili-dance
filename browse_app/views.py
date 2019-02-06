from collections import namedtuple
import functools

import flask
import requests
from sqlalchemy import func

from browse_app import app
import models

Video = namedtuple('Video', ('url', 'title', 'aid'))
NUM_PER_PAGE = 24


def convertResult(func):
    @functools.wraps(func)
    def newfunc(*args, **kws):
        videos = func(*args, **kws)
        videos = [
            Video(
                url='|'.join(item.picurl.split('/')[1:]),
                title=item.title, aid=item.aid)
            for item in videos
        ]
        return videos
    return newfunc


@convertResult
def getVideosByAnnotation(keyname, page, session):
    order_key = getattr(models.SafeAnnotation, keyname)
    videos = session.query(models.Video)\
        .join(models.SafeAnnotation, models.SafeAnnotation.aid == models.Video.aid)\
        .order_by(order_key.desc(), models.Video.ctime.desc())\
        .offset((page-1)*NUM_PER_PAGE)\
        .limit(NUM_PER_PAGE).all()
    return videos


@convertResult
def getVideosByTag(tagname, page, session):
    videos = session.query(models.Video)\
        .join(models.Label,
              (models.Label.description == tagname) &
              (models.Label.score > 0.8) &
              (models.Label.aid == models.Video.aid))\
        .order_by(models.Video.ctime.desc())\
        .offset((page-1)*NUM_PER_PAGE)\
        .limit(NUM_PER_PAGE).all()
    return videos


def getTags(session):
    label = models.Label
    tags = session.query(label.description)\
        .group_by(label.description)\
        .order_by(func.count(label.description).desc())\
        .limit(10).all()
    return [item[0] for item in tags]


def getPageOptions(page):
    _startIndex = max(1, page-3)
    return list(range(_startIndex, _startIndex+6))


@app.route('/')
def index():
    return flask.redirect(flask.url_for('safe', key='adult'))


@app.route('/safe/<string:key>')
def safe(key):
    page = max(1, flask.request.args.get('page', 1, type=int))

    keys = ('adult', 'racy', 'spoof', 'medical', 'violence')

    sess = models.getSession(app.config['DB_PATH'])
    videos = getVideosByAnnotation(key, page, sess)
    sess.close()

    return flask.render_template('browse.html',
                                 prefix='safe',
                                 key=key, keys=keys,
                                 videos=videos,
                                 page=page, pageoptions=getPageOptions(page))


@app.route('/tag/<string:tagname>')
def tag(tagname):
    page = max(1, flask.request.args.get('page', 1, type=int))

    sess = models.getSession(app.config['DB_PATH'])
    keys = getTags(sess)
    videos = getVideosByTag(tagname, page, sess)
    sess.close()

    return flask.render_template('browse.html',
                                 prefix='tag',
                                 key=tagname, keys=keys,
                                 videos=videos,
                                 page=page, pageoptions=getPageOptions(page))


@app.route('/pic/<string:picurl>')
def getPic(picurl):
    if not picurl.split('|')[1].endswith('hdslb.com'):
        return flask.Response(status=403)
    picurl = 'https:/' + picurl.replace('|', '/')
    img = requests.get(picurl).content
    return flask.Response(img, mimetype="image/"+picurl.split('.')[-1])
