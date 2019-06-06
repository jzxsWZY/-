import sys
from collections import deque
import requests
import urllib
from urllib import request
import re
from bs4 import BeautifulSoup
import lxml
import sqlite3
import jieba

url='https://www.zut.edu.cn/index/xwdt.htm'
#要抓去的链接入口

unvisited=deque()#待爬取链接的集合，使用广度优先搜索
visited=set()   #己访问的链接集合
unvisited.append(url)

conn=sqlite3.connect('viewsdu.db')
c=conn.cursor()
c.execute('drop table doc')#在create table之前先drop table，所以再次运行代码的时候要把旧table删了重建
c.execute('create table doc(id int primary key ,link text)')
c.execute('drop table word')
c.execute('create table word(term varchar(25) primary key ,list text)')
conn.commit()
conn.close()
print('************开始爬虫****************')
cnt=0
print('开始.....')
while unvisited:
    url=unvisited.popleft()
    visited.add(url)
    cnt+=1
    print('开始抓取第',cnt,'个链接：',url)
    try:#爬取网页内容
        response=requests.get(url)
        content=response.content.decode('utf-8')
    except:
        continue

    soup=BeautifulSoup(content,'lxml')
    all_a=soup.find_all('a',{'class':'c67214'})#本页面所有的新闻链接
    for a in all_a:
        #print(a.attrs['href'])
        x=a.attrs['href']
        if re.match(r'http.+',x):
            if not re.match(r'https\:\/\/www\.zut\.edu\.cn\/.+',x):
                continue
        if re.match(r'\/info\/.+',x):
            x='https://www.zut.edu.cn'+x  #'/info/1046/20314.htm'
        elif re.match(r'info/.+',x):
            x='https://www.zut.edu.cn/'+x #'info/1046/20314.htm'
        elif re.match(r'\.\.\/info/.+',x):
            x='https://www.zut.edu.cn'+x[2:] #'../info/1046/20314.htm'
        elif re.match(r'\.\.\/\.\.\/info/.+',x):
            x='https://www.zut.edu.cn'+x[5:]  #'../../info/1046/20314.htm'
        if(x not in visited) and(x not in unvisited):
            unvisited.append(x)
    a=soup.find('a',{'class':'Next'})
    if a!=None:
        x=a.attrs['href']
        if re.match(r'xwdt\/.+',x):
            x='https://www.zut.edu.cn/index/'+x
        else:
            x='https://www.zut.edu.cn/index/xwdt/'+x
        if(x not in visited) and(x not in unvisited):
            unvisited.append(x)

    soup=BeautifulSoup(content,'lxml')
    title=soup.title
    article=soup.find('div',class_='c67215_content',id='vsb_newscontent')
    author=soup.find('span',class_="timestyle67215")
    if title ==None and article==None and author==None:
        print('无内容的页面')
        continue
    elif article==None and author==None:
        print('只有标题')
        title=title.text
        title=''.join(title.split())
        article=''
        author=''
    elif article==None:
        print('有标题有作者,缺失内容')
        title=title.text
        title=''.join(title.split())
        article=''
        author=author.get_text("",strip=True)
        author=''.join(author.split())
    elif author ==None:
        print('有标题有内容，缺失作者')
        title=title.text
        title=''.join(title.split())
        article=article.get_text("",strip=True)
        article=''.join(article.split())
        author=''
    else:
        title=title.text
        title=''.join(title.split())
        article=article.get_text("",strip=True)
        article=''.join(article.split())
        author=author.get_text("",strip=True)
        author=''.join(author.split())
    print('网页标题：',title)
    seggen=jieba.cut_for_search(title)
    seglist=list(seggen)
    seggen=jieba.cut_for_search(article)
    seglist+=list(seggen)
    seggen=jieba.cut_for_search(author)
    seglist+=list(seggen)

    #数据存储
    conn=sqlite3.connect('viewsdu.db')
    c=conn.cursor()
    c.execute('insert into doc values(?,?)',(cnt,url))
    #对每个分出的词语建立倒排表
    for word in seglist:
        #print(word)
        #检验看着这个词语士在否已存在于数据库
        c.execute('select list from word where term=?',(word,))
        result=c.fetchall()
        #如果不存在
        if len(result)==0:
            docliststr=str(cnt)
            c.execute('insert into word values(?,?)',(word,docliststr))
        else:#如果己存在
            docliststr=result[0][0]
            docliststr+=' '+str(cnt)
            c.execute('update word set list=? where term=?',(docliststr,word))
    conn.commit()
    conn.close()







