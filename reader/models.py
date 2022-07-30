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

class UserSetting(models.Model):
    user_id = models.IntegerField()
    font_size = models.IntegerField(default=16)
    read_bg = models.CharField(max_length=256,default='#fff')

class UserBookMark(models.Model):
    user_id = models.IntegerField()
    book_id = models.IntegerField()
    chapter_id = models.IntegerField()
    words_read = models.IntegerField()
    content = models.TextField()
    add_time = models.DateTimeField(default = timezone.now)

