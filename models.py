import sqlalchemy
from sqlalchemy import Column, Integer, Text, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
import datetime
import enum

Base = declarative_base()


class Video(Base):
    __tablename__ = 'videos'

    aid = Column(Integer, primary_key=True, unique=True, index=True)
    cid = Column(Integer)
    title = Column(VARCHAR(128))
    desc = Column(Text)
    picurl = Column(Text)

    ctime = Column(sqlalchemy.TIMESTAMP)
    duration = Column(Integer)  # 长度
    upName = Column(VARCHAR(128))
    upFaceUrl = Column(Text)
    upMid = Column(Integer)
    videos = Column(Integer)
    # stats
    coin = Column(Integer)
    danmaku = Column(Integer)
    favorite = Column(Integer)
    his_rank = Column(Integer)
    like = Column(Integer)
    now_rank = Column(Integer)
    reply = Column(Integer)
    share = Column(Integer)
    views = Column(Integer)
    lastUpdated = Column(
        sqlalchemy.TIMESTAMP, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    @staticmethod
    def fromVO(vo):
        stat = vo['stat']
        return Video(
            aid=vo['aid'], cid=vo.get('cid', None), title=vo['title'], desc=vo['desc'], picurl=vo['pic'],
            ctime=datetime.datetime.fromtimestamp(vo['ctime']),
            duration=vo['duration'], upName=vo['owner']['name'],
            upFaceUrl=vo['owner']['face'], upMid=vo['owner']['mid'],
            videos=vo['videos'],
            coin=stat['coin'], danmaku=stat['danmaku'], favorite=stat['favorite'],
            his_rank=stat['his_rank'], like=stat['like'], now_rank=stat['now_rank'],
            reply=stat['reply'], share=stat['share'], views=stat['view']
        )


class Likelihood(enum.IntEnum):
    'https://cloud.google.com/vision/docs/reference/rest/v1/images/annotate#Likelihood'
    UNKNOWN = 0
    VERY_UNLIKELY = 1
    UNLIKELY = 2
    POSSIBLE = 3
    LIKELY = 4
    VERY_LIKELY = 5

    @staticmethod
    def fromName(name):
        return getattr(Likelihood, name)


class SafeAnnotation(Base):
    'https://cloud.google.com/vision/docs/reference/rest/v1/images/annotate#SafeSearchAnnotation'

    __tablename__ = 'safe_anno'

    aid = Column(Integer, sqlalchemy.ForeignKey('videos.aid'),
                 primary_key=True, unique=True, index=True)
    adult = Column(Integer)
    spoof = Column(Integer)
    medical = Column(Integer)
    violence = Column(Integer)
    racy = Column(Integer)

    @staticmethod
    def fromVO(vo):
        return SafeAnnotation(**{
            name: int(Likelihood.fromName(vo[name]))
            for name in ('adult', 'medical', 'racy', 'spoof', 'violence')
        })


class Label(Base):
    'https://cloud.google.com/vision/docs/reference/rest/v1/images/annotate#EntityAnnotation'

    __tablename__ = 'labels'

    id = Column(Integer, primary_key=True)
    aid = Column(Integer, sqlalchemy.ForeignKey('videos.aid'), index=True)

    description = Column(VARCHAR(128))
    mid = Column(VARCHAR(128))
    score = Column(sqlalchemy.Float)
    topicality = Column(sqlalchemy.Float)

    @staticmethod
    def fromVO(vo):
        return Label(**{
            key: vo[key]
            for key in ('description', 'mid', 'score', 'topicality')
        })
        # return Label(**vo)


def getSession(dbpath) -> sqlalchemy.orm.Session:
    engine = sqlalchemy.create_engine(dbpath)
    Base.metadata.create_all(engine)
    sessionMaker = sqlalchemy.orm.sessionmaker(bind=engine)
    return sessionMaker()
