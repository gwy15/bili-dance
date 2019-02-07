import sys

import progressbar

import models

from_session = models.getSession('FROM_DB_PATH')
to_session = models.getSession('TO_DB_PATH')

TABLE = models.Label # Video, SafeAnnotation
BATCH_SIZE = 1000
count = from_session.query(TABLE).count()
print('total count:', count)

for index in progressbar.progressbar(range(int(sys.argv[1]), count // BATCH_SIZE + 2)):
    query = from_session.query(TABLE)\
        .order_by(TABLE.aid)\
        .offset(index * BATCH_SIZE)\
        .limit(BATCH_SIZE)
    try:
        videos = query.all()
    except Exception:
        print('current index: {}'.format(index))
        raise

    for video in videos:
        to_session.merge(video)
    to_session.commit()
