import imp
import math
from django.db import models
import re
import django.utils.timezone as timezone
from matplotlib.pyplot import cla, title
from numpy import mat
import chardet



# Create your models here.
class Book(models.Model):
    title = models.CharField(max_length=256)
    desc = models.CharField(max_length=1024)
    author = models.CharField(max_length=256)
    book_type = models.CharField(max_length=256)
    first_chapter = models.IntegerField(default=1)
    uploader = models.IntegerField(default=0)
    upload_time = models.DateTimeField(default = timezone.now)
    

class Chapter(models.Model):
    title = models.CharField(max_length=256)
    book_id = models.IntegerField()
    content_id = models.IntegerField()
    words = models.IntegerField()

class Content(models.Model):
    content = models.TextField()

class UserBookRecord(models.Model):
    user_id = models.IntegerField()
    book_id = models.IntegerField()
    chapter_id = models.IntegerField()
    read_time = models.DateTimeField(default = timezone.now)
    words_read = models.IntegerField()

def handle_uploaded_file(f):
    if str(f)[-4:]!='.txt':
        return
    file = ''
    
    for chunk in f.chunks():
        if 'conding' not in locals().keys():
            conding = chardet.detect(chunk)["encoding"] 
        file += chunk.decode(conding,'ignore')

    book = Book(title = str(f)[:-4])
    book.save()

    pat = u'第[一二三四五六七八九十零百千0123456789]+[集章节卷]'
    # pat = u'(?<=[　\s])(?:序章|序言|卷首语|扉页|楔子|正文(?!完|结)|终章|后记|尾声|番外|第?\s{0,4}[\d〇零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟]+?\s{0,4}(?:章|节(?!课)|卷|集(?![合和])|部(?![分赛游])|篇(?!张))).{0,30}$'
    pattern = re.compile(pat)
    match = pattern.findall(file)
    print(file[:200])
    print(match)
    st = file.find(match[0],0)
    
    intro = '介绍' if st > 5000 else '正文'
    content = Content(content = file[0:st])
    content.save()
    chapter = Chapter(title=intro,book_id = book.id,content_id = content.id,words = st)
    chapter.save()
    book.first_chapter = chapter.id
    book.save()
    for i in range(1,len(match)):
        en = file.find(match[i],st)       
        content = Content(content = file[st:en])
        content.save()
        tt = file[st:file.find('\n',st)] if file.find('\n',st) < st + 20 else match[i-1]
        chapter = Chapter(title=tt, book_id = book.id, content_id = content.id, words = en - st)
        chapter.save()
        st = en

        if i == len(match) -1 :
            content = Content(content = file[en:])
            content.save()
            tt = file[st:file.find('\n',st)] if file.find('\n',st) < st + 20 else match[i]
            chapter = Chapter(title=tt, book_id = book.id, content_id = content.id, words = len(file) - en)
            chapter.save()
