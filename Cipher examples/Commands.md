
Get any chain of tweets related to one Conference day with associated Author, Hashtag, User Mention, and Client used.

```
match (x)<--(n)-[*1..]->(t:Time {name: 'Day #3 of IIW October 2018'}) return n, t, x
```