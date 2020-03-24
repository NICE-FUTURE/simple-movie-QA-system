# -*- "coding: utf-8" -*-

'''
极简问答系统：
1. 获取问题（基于命令行）
2. 对问题抽象并提取关键词（pyhanlp模块分词和词性标注，其实我认为如果求简的话，这里可以用jieba替代）
3. 对抽象问句分类得到对应的模板（scikit-learn模块的朴素贝叶斯算法）
4. 根据模板规则到Neo4j数据库中查询回答（py2neo模块连接Neo4j数据库进行查询）
5. 对回答包装后进行回显（基于命令行）
'''

from pyhanlp import HanLP
from sklearn.naive_bayes import ComplementNB
import os
import numpy as np
from Neo4j import Neo4j


def get_abstract_sentence(sentence, vocabulary):
    '''
    句子抽象化
    电影名 nm
    演员名 nnt
    电影类型 ng
    紧跟演员名之后的演员名 nnr
    评分 x
    '''
    abstract_sentence = []
    query_dict = {}
    second = False
    for segment in HanLP.segment(sentence):
        word = str(segment.word)
        nature = str(segment.nature)
        if nature == "nm":
            query_dict["nm"] = word
            word == "nm"
        elif nature == "nnt" and not second:
            query_dict["nnt"] = word
            word == "nnt"
            second = True
        elif nature == "ng":
            query_dict["ng"] = word
            word = "ng"
        elif nature == "m":
            query_dict["x"] = word
            word = "x"
        elif nature == "nnt" and second:
            query_dict["nnr"] = word
            word = "nnr"
            second = False
        if word in vocabulary:
            abstract_sentence.append(word)
    return abstract_sentence, query_dict

def get_model_label(abstract_sentence, classifier, vocabulary):
    '''
    使用训练好的分类器，将抽象的句子分类到某一个模板
    '''

    # 将抽象的句子向量化
    vector = np.zeros((1,len(vocabulary)))
    for item in abstract_sentence:
        vector[0,vocabulary.index(item)] = 1

    # 分类
    label = classifier.predict(vector)[0]
    return label

def get_classifier(vocabulary):
    '''
    需要将抽象的句子分类到某一个模板，这里是训练分类器
    '''

    # 准备数据集
    x_train = []
    y_train = []

    root = "./Qdata/question/"
    filenames = [filename for filename in os.listdir(root) if filename[0]=="【"]
    for filename in filenames:
        label = int(filename[filename.index("【")+1:filename.index("】")])
        with open(root+filename, "r", encoding="utf-8") as f:
            sen_list = [line.strip() for line in f.readlines()]
            x_train += sen_list
            y_train += [label]*len(sen_list)

    x_train_array = np.zeros((len(x_train), len(vocabulary)))
    for row, sentence in enumerate(x_train):
        for col, voc in enumerate(vocabulary):
            if voc in sentence:
                x_train_array[row,col] = 1

    classifier = ComplementNB()
    classifier.fit(x_train_array, y_train)
    
    return classifier

def get_query_sentence(query_dict, model):
    '''
    将抽象的句子还原成自然语句（目前没有用到）
    '''
    query_sentence = model
    for key, value in query_dict.items():
        query_sentence = query_sentence.replace(key, value)
    return query_sentence

def get_answer_template(model_label, query_dict):
    '''
    根据模板返回用于包装回答的语句
    '''
    templates = {
            0:"{nm}的评分是:",
            1:"{nm}的上映时间是:",
            2:"{nm}的类型是:",
            3:"{nm}的简介是:\n",
            4:"{nm}的参演演员有:\n",
            5:"{nnt}的介绍是:\n",
            6:"{nnt}参演的{ng}类型的电影作品有:\n",
            7:"{nnt}的电影作品有:\n",
            8:"{nnt}参演的评分大于{x}的电影有:\n",
            9:"{nnt}参演的评分小于{x}的电影有:\n",
            10:"{nnt}参演过的电影类型有:\n",
            11:"{nnt}和{nnr}合作过的电影有:\n",
            12:"{nnt}参演过的电影数量为:",
            13:"{nnt}的出生日期是:",
    } 
    if model_label in [0, 1, 2, 3, 4]:
        return templates[model_label].format(nm=query_dict["nm"])
    elif model_label in [5, 7, 10, 12, 13]:
        return templates[model_label].format(nnt=query_dict["nnt"])
    elif model_label in [8, 9]:
        return templates[model_label].format(nnt=query_dict["nnt"], x=query_dict["x"])
    elif model_label == 6:
        return templates[model_label].format(nnt=query_dict["nnt"], ng=query_dict["ng"])
    elif model_label == 11:
        return templates[model_label].format(nnt=query_dict["nnt"], nnr=query_dict["nnr"])

def main():
    '''
    批量运行，修改sentences列表即可（可以看到中间结果）
    '''
    with open("./Qdata/question/vocabulary.txt", "r", encoding="utf-8") as f:
        vocabulary = [line.strip().split(":")[1] for line in f.readlines()]

    with open("./Qdata/question/question_classification.txt", "r", encoding="utf-8") as f:
        models = [line.strip().split(":")[1] for line in f.readlines()]

    classifier = get_classifier(vocabulary)
    print("分类器训练完成...")

    sentences = [
        "卧虎藏龙的评分是多少？",
        "成龙有哪些动作类型的电影？",
        "成龙和李连杰合作的电影列表",
        "成龙参演的评分大于6.77的电影列表"]

    for sentence in sentences:
        abstract_sentence, query_dict = get_abstract_sentence(sentence, vocabulary)
        model_label = get_model_label(abstract_sentence, classifier, vocabulary)
        query_sentence = get_query_sentence(query_dict, models[model_label])
        neo4j = Neo4j()
        query_result = neo4j.query(model_label, query_dict)
        print("原句:{}\n抽象:{}\n关键词:{}\n模板序号:{}\n模板内容:{}\n".format(
            sentence, abstract_sentence, query_dict, model_label, models[model_label]))
        if len(query_result) > 0:
            answer = get_answer_template(model_label, query_dict) + ", ".join(list(map(str, query_result)))+"\n\n"
        else:
            answer = "对不起，没有找到你要的答案 :( \n\n"
        print(answer)

def run():
    '''
    交互式运行（默认方式）
    '''
    with open("./Qdata/question/vocabulary.txt", "r", encoding="utf-8") as f:
        vocabulary = [line.strip().split(":")[1] for line in f.readlines()]

    with open("./Qdata/question/question_classification.txt", "r", encoding="utf-8") as f:
        models = [line.strip().split(":")[1] for line in f.readlines()]

    classifier = get_classifier(vocabulary)
    # print("分类器训练完成...")

    sentence = input("请输入你电影方面的问题(exit退出)：\n")
    while(sentence != "exit"):
        abstract_sentence, query_dict = get_abstract_sentence(sentence, vocabulary)
        model_label = get_model_label(abstract_sentence, classifier, vocabulary)
        query_sentence = get_query_sentence(query_dict, models[model_label])
        neo4j = Neo4j()
        query_result = neo4j.query(model_label, query_dict)
        # print("原句:{}\n抽象:{}\n关键词:{}\n模板序号:{}\n模板内容:{}\n".format(
        #     sentence, abstract_sentence, query_dict, model_label, models[model_label]))
        if len(query_result) > 0:
            answer = get_answer_template(model_label, query_dict) + ", ".join(list(map(str, query_result)))+"\n\n"
        else:
            answer = "对不起，没有找到你要的答案 :( \n\n"
        print(answer)

        sentence = input("请输入你电影方面的问题(exit退出)：\n")

if __name__ == "__main__":
    # main()
    run()
