# coding=utf-8
from gensim import corpora, models, similarities
import sys    
import re
import sqlite3
import jieba.posseg as pseg
import cPickle
from langconv import *
#用来对取数据库里的评论并对评论进行预处理：去除除中文及中文标点外的字符，将繁体字转换成简体字，利用结巴分词进行分词以及词性标注，去除停词，最后将每一条评论输出到file_jieba文件中，评论间用换行符标注



#define comment_record class

comment_list=[]      #read comment_body from database
comment_list_chinese=[]           #leave chinese only
comments_words=[]                  #use jieba segment the comment
comment_words=[]
comment_stopwd_rm=[]              #remove stopwords

#creat database and tables,define insert_sql

#db='/home/andyliu/thesis/android_market.sqlite'
db='/home/andyliu/thesis/google_play_2.0.sqlite'    
#select_comment_sql="select comment_title from comments;"
select_comment_sql="select comment_body from comments;"
connection=sqlite3.connect(db)
cursor=connection.cursor()

#change the unicode

reload(sys)                         # 2
sys.setdefaultencoding('utf-8') 


#read data from database
cursor.execute(select_comment_sql)
comment_list=cursor.fetchall()
connection.commit()
#i=0

#leave chinese only
for temp in comment_list:
	#if i<200:
	comment_list_chinese.append(re.sub(ur'[^\u4E00-\u9FA5，。？！]+','',temp[0].strip()))
	#else :
	#	break
	#i=i+1


#change fanti to jianti 
i=0
file_jianti=open("/home/andyliu/thesis/file_jianti.txt",'w')
for temp in comment_list_chinese:
 	# 转换繁体到简体
 	comment_list_chinese[i] = Converter('zh-hans').convert(comment_list_chinese[i])
	file_jianti.write(comment_list_chinese[i])
	file_jianti.write('\n')
	#print comment_list_chinese[i]
	i=i+1
#file_jianti=open("/home/andyliu/thesis/file_jianti.txt",'w')

#remove comment with words less than 10
for temp in comment_list_chinese:
	if len(temp)<10:
		del comment_list_chinese[comment_list_chinese.index(temp)]

#print comment_list_chinese[:20]


#split comment into words with jieba
file_jieba=open('/home/andyliu/thesis/file_jieba.txt','w')
for comment in comment_list_chinese:
	comment_words=[]
	words=pseg.cut(comment)
	for word in words:
		comment_words.append({word.word:word.flag})
		#file_jieba.write(word.word+" :"+word.flag)
	#file_jieba.write('\n')
	comments_words.append(comment_words)

#write comment to file
file_comment=open("/home/andyliu/thesis/file_comment.txt",'w')
for comment in comments_words:
	for word in comment:
		for key in word.keys():
			file_comment.write(key+":"+word[key]+"  ")
	file_comment.write('\n')
file_comment.close()


#define funtion to remove stopwords
def StopwordsRm(words):  
    result=''  
    i=0 
    stopwords = [line.strip('\n') for line in open("/home/andyliu/thesis/stop_words.txt")]  
    for stopword in stopwords:
    	stopwords[i]=unicode(stopword,'utf-8').strip()
    	i=i+1
    cleanTokens=[]
    for w in words :
    	for key  in w.keys():
    		if key not in stopwords:
    			cleanTokens.append(w)
    		else:
    			continue
    #cleanTokens= [w for w in words if key for key in w.keys() not in stopwords] 
    return cleanTokens  
#remove stop words and write the result to file 
for words in comments_words:
	comment_stopwd_rm.append(StopwordsRm(words))
file_rm=open("/home/andyliu/thesis/file_rm.txt",'w')
for comment in comment_stopwd_rm:
	for word in comment:
		for key in word.keys():
			file_rm.write(key+":"+word[key]+"  ")
	file_rm.write('\n')
file_rm.close()

#refactor the result into comment_pair list [[],[]]
comment_pair=[]
for comment in comment_stopwd_rm:
	temp1=[]
	temp2=[]
	for word in comment:

		for key in word.keys():
			#if word[key]=='n' or word[key]=='v':
			if key=='，'or key=='。'or key=='？'or key =='！':
				continue
			else:
				if word[key]=='n' or word[key]=='nl' or  word[key]=='ng' or  word[key]=='nz':
					temp1.append(word)
				if word[key]=='a' or  word[key]=='ad' or  word[key]=='an' or  word[key]=='ag'or word[key]=='al':
					temp2.append(word)
	if temp1==[]:
		continue
	else:
		comment_pair.append([temp1,temp2])

#exact non list from comment_pair to comment_non
comment_non=[]
for comment in comment_pair:
	print(comment[0])
	print (comment[1])
	temp=[]
	for word in comment[0]:
		for key in word.keys():
			file_jieba.write(key+" :"+word[key])
			temp.append(key)

	file_jieba.write('      ')
	for word in comment[1]:
		for key in word.keys():
			file_jieba.write(key+" :"+word[key])
	comment_non.append(temp)
	file_jieba.write('\n')
file_jieba.close()

#remove the word whose feq is 1
all_tokens = sum(comment_non, [])
token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
texts = [[word for word in text if word not in token_once] for text in comment_non]
corpus_text_file=open("/home/andyliu/thesis/corpus_text_file.txt",'w')
for comment in texts:
    for words in comment:
        corpus_text_file.write(words)
    corpus_text_file.write('\n')
corpus_text_file.close()

dic = corpora.Dictionary(texts)

#print dic
#print dic.token2id

#for word,index in dic.token2id.iteritems():
#    print word +" 编号为:"+ str(index)
corpus = [dic.doc2bow(text) for text in texts]
corpus_file=open("/home/andyliu/thesis/corpus_file.txt",'w')
cPickle.dump(corpus,corpus_file)
corpus_file.close()


tfidf = models.TfidfModel(corpus)
corpus_tfidf = tfidf[corpus]
#for doc in corpus_tfidf:
#    print doc


lsi = models.LsiModel(corpus_tfidf, id2word=dic, num_topics=10)
lsiout=lsi.print_topics(10)
topic_file=open("/home/andyliu/thesis/topic_file.txt",'w')
cPickle.dump(lsiout,topic_file)
topic_file.close()
for topic in lsiout:
    print topic