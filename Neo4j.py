# -*- "coding: utf-8" -*-

'''
已知问题模板和对应的关键词，通过Neo4j查询问题答案
代码中所有Neo4j的查询语句（Cypher）均来自参考的Java代码，暂未细究
'''

from py2neo import Graph

'''
模板
0:nm 评分
1:nm 上映时间
2:nm 类型
3:nm 简介
4:nm 演员列表
5:nnt 介绍
6:nnt ng 电影作品
7:nnt 电影作品
8:nnt 参演评分 大于 x
9:nnt 参演评分 小于 x
10:nnt 电影类型
11:nnt nnr 合作 电影列表
12:nnt 电影数量
13:nnt 出生日期
'''

class Neo4j(object):
    def __init__(self):
        '''
        neo4j查询语言
        '''
        self.query_models = {
            0:"match(n:Movie) where n.title='{title}' return n.rating",  # nm
            1:"match(n:Movie) where n.title='{title}' return n.releasedate",  # nm
            2:"match(n:Movie)-[r:is]->(b:Genre) where n.title='{title}' return b.name",  # nm
            3:"match(n:Movie) where n.title ='{title}' return n.introduction",  # nm
            4:"match(n:Person)-[:actedin]-(m:Movie) where m.title ='{title}' return n.name",  # nm
            5:"match(n:Person) where n.name='{name}' return n.birthplace",  # nnt
            6:"match(n:Person)-[:actedin]-(m:Movie) where n.name ='{name}' match(g:Genre)-[:is]-(m) where g.name=~'{gname}' return distinct  m.title",  # nnt, ng
            7:"match(n:Person)-[:actedin]->(m:Movie) where n.name='{name}' return m.title",  # nnt
            8:"match(n:Person)-[:actedin]-(m:Movie) where n.name ='{name}' and m.rating > {score} return m.title",  # nnt, x
            9:"match(n:Person)-[:actedin]-(m:Movie) where n.name ='{name}' and m.rating < {score} return m.title",  # nnt, x
            10:"match(n:Person)-[:actedin]-(m:Movie) where n.name ='{name}' match(p:Genre)-[:is]-(m) return distinct  p.name",  # nnt
            # 11: 单独处理
            12:"match(n)-[:actedin]-(m) where n.name ='{name}' return count(*)",  # nnt
            13:"match(n:Person) where n.name='{name}' return n.birth",  #  nnt
        }

        self.graph = Graph('http://localhost:7474', username="neo4j", password="neo4j")

    def query(self, model_label, query_dict):
        
        try:
            if model_label == 11:
                data_x = self._query(model_label=7, query_dict={"nnt":query_dict["nnt"]})
                data_y = self._query(model_label=7, query_dict={"nnt":query_dict["nnr"]})
                result = list(data_x.intersection(data_y))
                return result
            else:
                result = list(self._query(model_label, query_dict))
                return result
        except:
            return []

    def _query(self, model_label, query_dict):

        query_str = ""

        if model_label in [0, 1, 2, 3, 4]:
            query_str = self.query_models[model_label].format(title=query_dict["nm"])
        elif model_label in [5, 7, 10, 12, 13]:
            query_str = self.query_models[model_label].format(name=query_dict["nnt"])
        elif model_label == 6:
            query_str = self.query_models[model_label].format(name=query_dict["nnt"], gname=query_dict["ng"])
        elif model_label in [8, 9]:
            query_str = self.query_models[model_label].format(name=query_dict["nnt"], score=query_dict["x"])

        data = self.graph.run(query_str).data()
        result = set()
        for dic in data:
            temp = [item[1] for item in dic.items()]  # 一个元素
            result.add(temp[0])

        return result
