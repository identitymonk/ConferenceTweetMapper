
Get any chain of tweets related to one Conference day with associated Author, Hashtag, User Mention, and Client used.

```
match (x)<--(n)-[*1..]->(t:Time {name: 'Day #3 of IIW October 2018'}) return n, t, x
```

Return all distinct twitters of one specific conference except the organizer

```
MATCH (Conference {name: 'Identify 2018 - NY'})<-[:PartOf]-(:Time)<-[*0..]-(t:Tweet)-[:AuthoredBy]->(u:User) WHERE u.name <> '@pingidentity' WITH Conference, u, count(DISTINCT u.name) AS Total RETURN DISTINCT u.name
```

Return all the distinct twitters of one day of one specific conference that made an original tweet (no RT, Reply, Quote) except the organizer
```
MATCH (Conference {name: 'Identify 2018 - NY'})<-[:PartOf]-(Time {name: 'Post-Conference of Identify 2018 - NY'})<-[:RelatesTo]-(t:Tweet)-[:AuthoredBy]->(u:User) WHERE u.name <> {b} WITH Time, Count(DISTINCT u.name) as Total RETURN RETURN DISTINCT u.name
```

Return TOP 3 RepliedTo Users globally except the organizer

```
MATCH (u:User)<-[:AuthoredBy]-(n:Tweet)<-[r:ReplyTo]-(m:Tweet) WHERE u.name <> '@pingidentity' WITH u, Count(DISTINCT n.name) AS Total RETURN DISTINCT u.name, Total ORDER BY Total DESC LIMIT 3
```

Return TOP 3 RepliedTo Users for a specific conference except the organizer
```
MATCH (u:User)<-[:AuthoredBy]-(n:Tweet)<-[r:ReplyTo]-(m:Tweet) WHERE u.name <> '@pingidentity' AND (n)-[*0..]->(:Conference {name: 'Identify 2018 - NY'}) WITH u, Count(DISTINCT n.name) AS Total RETURN DISTINCT u.name, Total ORDER BY Total DESC LIMIT 3
```

Return TOP 3 RepliedTo Users for a specific conference day except the organizer
```
MATCH (u:User)<-[:AuthoredBy]-(n:Tweet)<-[r:ReplyTo]-(m:Tweet) WHERE u.name <> '@pingidentity' AND (n)-[*0..]->(:Time {name: 'Day #1 of Identify 2018 - SF'})-[:PartOf]->(:Conference {name: 'Identify 2018 - SF'}) WITH u, Count(DISTINCT n.name) AS Total RETURN DISTINCT u.name, Total ORDER BY Total DESC LIMIT 3
```

Return Source of Tweet for one user
```
MATCH (u:User)<-[r:AuthoredBy]-(t:Tweet)-[x:Using]->(s:Source)
WHERE u.name = '@someone'
WITH u, collect(DISTINCT s) AS Means
UNWIND Means as Item
MATCH (u2:User)<-[r2:AuthoredBy]-(t2:Tweet)-[x2:Using]->(s2:Source)
WHERE u2.name = '@someone' AND s2.name = Item.name
WITH {user: u2.name, source: Item.name, Total: count(x2)} AS Stat
RETURN Stat
```