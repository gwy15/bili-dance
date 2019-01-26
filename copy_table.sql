CREATE TABLE download AS 
    SELECT aid, picurl, 0 as status
    from videos;
CREATE INDEX aid ON download(aid);

