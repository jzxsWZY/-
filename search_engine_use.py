import re
import requests
from collections import deque
from bs4 import BeautifulSoup
import lxml
import sqlite3
import jieba
import math
conn=sqlite3.connect("viewsdu.db")
c=conn.cursor()
c.execute('select count(*) from doc')
N=1+c.fetchall()[0][0]#文档总数
target=input("请输入搜索词 ：")
seggen=jieba.cut_for_search(target)#将搜索内容分词
score={} #字典，用于储存"文档号: 文档得分"
for word in seggen:
    print("得到查询词 :",word)
    tf={}
    c.execute('select list from word where term=?',(word,))
    result=c.fetchall()
    if len(result)>0:
        doclist=result[0][0]
        doclist=doclist.split(' ')
        doclist=[int(x) for x in doclist]
        df=len(set(doclist))
        idf=math.log(N/df)
        print('idf: ',idf)
        for num in doclist: #计算词频TF，即某文档出现的次数
            if num in tf:
                tf[num]=tf[num]+1
            else:
                tf[num]=1
        for num in tf:
            if num in score:
                #如果该num文档已经有分数了，则累加
                score[num]=score[num]+tf[num]*idf
            else:
                score[num]=tf[num]*idf

sortedlist=sorted(score.items(),key=lambda d:d[1],reverse=True)
#对 score 字典按字典的值排序

cnt=0
for num,docscore in sortedlist:
    cnt=cnt+1
    c.execute('select  link from doc where id=?',(num,))
    #按照ID获取文档的连接（网址）
    url=c.fetchall()[0][0]
    print(url,'得分',docscore) #输出网址和对应得分
    try:
        response=requests.get(url)
        content=response.content.decode('utf8')
    except:
        print('oops...读取网页错误')
        continue
    #解析网页输出标题
    soup=BeautifulSoup(content,'lxml')
    title=soup.title
    if title==None:
        print('No title.')
    else:
        title=title.text
        print(title)
    if cnt>20:
        break

if cnt==0:
    print('无搜索结果')


