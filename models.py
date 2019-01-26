import sqlalchemy
from sqlalchemy import Column, Integer, Text, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class VDownload(Base):
    __tablename__ = 'download'

    aid = Column(Integer, primary_key=True, unique=True, index=True)
    picurl = Column(Text)
    status = Column(sqlalchemy.Boolean)


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


def getSession(dbpath):
    engine = sqlalchemy.create_engine(dbpath)
    Base.metadata.create_all(engine)
    sessionMaker = sqlalchemy.orm.sessionmaker(bind=engine)
    return sessionMaker()
