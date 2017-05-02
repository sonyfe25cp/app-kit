SELECT
  share.pv               '分享次数',
  share.uv               '分享人数',
  pv.pv,
  pv.uv,
  share.uv * 100 / pv.uv '分享比例',
  pv.pv / pv.uv          'depth',
  pv.date10
FROM (
       SELECT
         count(1)            pv,
         count(DISTINCT cid) uv,
         date10
       FROM event_$month
       WHERE pk = 'activity' AND pp = 'bsalary' AND ckk LIKE 'wx-sha%'
       GROUP BY date10
     ) share JOIN (
                    SELECT
                      count(1)            pv,
                      count(DISTINCT cid) uv,
                      date10
                    FROM pv_$month
                    WHERE pk = 'activity' AND pp = 'bsalary'
                    GROUP BY date10
                  ) pv ON pv.date10 = share.date10
ORDER BY pv.date10


SELECT
  pv.uv,
  click.uv               click_uv,
  date10,
  click.uv * 100 / pv.uv click_rate
FROM (
       SELECT
         count(1)            pv,
         count(DISTINCT cid) uv,
         date10
       FROM pv_$month
       WHERE url LIKE '/activity/bsalary/hom%'
       GROUP BY date10
     ) pv JOIN (
                 SELECT
                   count(1)            pv,
                   count(DISTINCT cid) uv,
                   date10
                 FROM event_$month
                 WHERE url LIKE '/activity/bsalary/hom%' AND ckk LIKE 'hot%'
                 GROUP BY date10
               ) click ON click.date10 = pv.date10
ORDER BY date10