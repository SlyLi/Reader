from audioop import reverse
from msilib.schema import ControlEvent
from django.http import HttpResponse, HttpResponseRedirect
from requests import request
from .forms import UploadFileForm
from .models import *
from django.views import generic
from django.shortcuts import get_object_or_404, redirect, render
import json
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required

def handle_uploaded_file(request):
    f = request.FILES['file']
    if str(f)[-4:]!='.txt':
        return
    file = ''
    
    for chunk in f.chunks():
        if 'conding' not in locals().keys():
            conding = chardet.detect(chunk)["encoding"] 
        file += chunk.decode(conding,'ignore')

    book = Book(title = str(f)[:-4])
    if request.user.is_authenticated:
        book.uploader = request.user.id
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


@login_required(login_url='reader:index')
def upload_file(request):
    if  request.method == 'POST':
        handle_uploaded_file(request)
        return render(request, 'upload_file.html', {'notice':"succeed"})
        

    return render(request, 'upload_file.html')



class BookListView(generic.ListView):
    template_name = 'book_list.html'
    context_object_name = 'book_list'

    def get_queryset(self):
        """Return the last five published questions."""
        if self.request.user.is_authenticated:
            return Book.objects.filter(uploader = 0) | Book.objects.filter(uploader = self.request.user.id)
        else:
            return Book.objects.filter(uploader = 0)

@login_required(login_url='reader:index')
def BookAdminView(request):
    if request.user.is_superuser == 1:
        books = Book.objects.all()
    else:
        books = Book.objects.filter(uploader = request.user.id)
    return render(request, 'book_admin.html', {'book_list': books})


class ChapterListView(generic.ListView):
    template_name = 'chapter_list.html'
    context_object_name = 'chapter_list'

    def get_queryset(self):
        _book =  get_object_or_404(Book,id = self.kwargs['pk'])
        if _book.uploader == 0:
            return Chapter.objects.filter(book_id=self.kwargs['pk'])
        if self.request.user.is_authenticated and self.request.user.id == _book.uploader :
            return Chapter.objects.filter(book_id=self.kwargs['pk'])
        return Chapter.objects.none()

        
        

class BookmarkListView(generic.ListView):
    template_name = 'bookmark_list.html'
    context_object_name = 'bookmark_list'

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.id == self.kwargs['user_id']:
            return UserBookMark.objects.filter(book_id=self.kwargs['book_id'],user_id =self.kwargs['user_id']).order_by('-add_time')
        else:
            return UserBookMark.objects.none()

class ChapterDetailView(generic.DetailView):
    template_name = 'chapter_detail.html'
    model: Content

    def get_queryset(self):
        return Content.objects.filter(pk=self.kwargs['pk'])

class IndexView(generic.TemplateView):
    template_name = 'index.html'


def book(request,pk):
    if request.user.is_authenticated:
        last = UserBookRecord.objects.filter(user_id = request.user.id , book_id = pk).order_by('-read_time')
        if len(last) > 0:
            last = last[0]
            return redirect('reader:book_reader',pk,last.chapter_id)
    _book =  get_object_or_404(Book,id = pk)
    if _book.uploader == 0 or _book.uploader==request.user.id:
        return redirect('reader:book_reader',book_pk=pk,chapter_pk=_book.first_chapter)
    return redirect('reader:index')

@login_required(login_url='reader:index')
def book_reader_offset(request,book_pk,chapter_pk,offset):
    _book = get_object_or_404(Book,id = book_pk)
    if _book.uploader == 0 or _book.uploader == request.user.id:
        chapter_list = Chapter.objects.filter(book_id = book_pk)
        chapter_list = Chapter.objects.filter(book_id = book_pk)
        chapter = get_object_or_404(Chapter,pk = chapter_pk)
        con = get_object_or_404(Content,pk = chapter.content_id)
        content_lines = con.content.split('\n')
        if len(content_lines) == 1:
            content_lines = content_lines[0].split(' ',1)
        user_setting = get_object_or_404(UserSetting,user_id = request.user.id)


        return render(request, 'book_reader.html', 
                    {'chapter_list': chapter_list,'chapter_title':content_lines[0],'content_lines':content_lines[1:],
                'last_words':offset,'user_setting':user_setting})

    return redirect('reader:index')


def progress(book_id,chapter_id):
    chapter_list = Chapter.objects.filter(book_id = book_id)
    all = 0.0
    read = 0.0
    for ch in chapter_list:
        all+=ch.words
    
    for ch in chapter_list:
        if chapter_id == ch.id:
            break
        read+=ch.words
    return read/all *100 
    
def book_reader(request,book_pk,chapter_pk):
    if  request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponse('required login')  
        
        if 'words' in request.POST:
            UserBookRecord(user_id =request.user.id, book_id =book_pk, chapter_id = chapter_pk, words_read = int(request.POST['words'])).save()
            return HttpResponse('success')  
        if 'kwd' in request.POST:
            return keyword_search(request,book_pk,chapter_pk,str(request.POST['kwd']))

    _book = get_object_or_404(Book,id = book_pk)
    if _book.uploader != 0 and _book.uploader != request.user.id:
        return redirect('reader:index')

    chapter_list = Chapter.objects.filter(book_id = book_pk)
    chapter = get_object_or_404(Chapter,pk = chapter_pk)
    con = get_object_or_404(Content,pk = chapter.content_id)
    content_lines = con.content.split('\n')
    if len(content_lines) == 1:
        content_lines = content_lines[0].split(' ',1)
    # print(request.META['HTTP_REFERER'])
    if request.user.is_authenticated and 'HTTP_REFERER' in request.META and ('book_list' in request.META['HTTP_REFERER'] or 'bookmark_href' in request.META['HTTP_REFERER'])  :
        print(request.META['HTTP_REFERER'])
        last = UserBookRecord.objects.filter(user_id = request.user.id , book_id = book_pk).order_by('-read_time')
        user_setting = get_object_or_404(UserSetting,user_id = request.user.id)
        if len(last) > 0:
            last = last[0]
            return render(request, 'book_reader.html', 
                {'chapter_title':content_lines[0],'chapter_list':chapter_list, 'content_lines':content_lines[1:],
                'last_words':last.words_read,'user_setting':user_setting,'progess':progress(book_pk,chapter_pk)})

    if request.user.is_authenticated:
        user_setting = get_object_or_404(UserSetting,user_id = request.user.id)
        return render(request, 'book_reader.html', {'chapter_title':content_lines[0],'chapter_list':chapter_list,'content_lines':content_lines[1:],
            'user_setting':user_setting,'progess':progress(book_pk,chapter_pk)})
    else:
        return render(request, 'book_reader.html', {'chapter_title':content_lines[0],'chapter_list':chapter_list,'content_lines':content_lines[1:],'progess':progress(book_pk,chapter_pk)})

def login_auth(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        print(user)
        if user is not None:
            login(request, user)
            return HttpResponse('success')  
        else:
            return HttpResponse('请输出正确的用户名或密码')  

    return HttpResponse('fk off')  


def logout_view(request):
    logout(request)
    return redirect('reader:book_list')
    # Redirect to a success page.

def book_del(request,pk):
    _book = get_object_or_404(Book,id = pk)
    if request.user.is_superuser or request.user.id == _book.uploader:
        chapter_list = Chapter.objects.filter(book_id = pk)
        for i in chapter_list:
            Content.objects.filter(id=i.content_id).delete()
        chapter_list.delete()
        UserBookRecord.objects.filter(book_id = pk).delete()
        Book.objects.filter(id = pk).delete()
    return redirect('reader:book_admin')


class search_item:
    def __init__(self,book,chapter,cont,off):
        self.book_pk = book
        self.chapter_pk = chapter
        self.content = cont
        self.offset = off

def keyword_search(request,book_pk,chapter_pk,kwd):
    chapter_list = Chapter.objects.filter(book_id = book_pk)
    search_list = []
    for chapter in chapter_list:
        con = get_object_or_404(Content,pk = chapter.content_id)
        content_lines = con.content.split('\n')
        cnt = 0
        content_cnt = [0,]
        for i in content_lines:
            cnt += len(i)
            content_cnt.append(cnt)

        for i in range(len(content_lines)):
            if content_lines[i].find(kwd) != -1:
                search_list.append(search_item(book_pk,chapter.id,content_lines[i],content_cnt[i]))
    return render(request, 'search.html', {'list': search_list})

@login_required(login_url='reader:index')
def update_setting(request):
    if request.method == 'POST':
       
        settings = UserSetting.objects.filter(user_id = request.user.id)
        if len(settings) == 0:
            setting = UserSetting(user_id = request.user.id,font_size = request.POST['font_size'],read_bg = request.POST['read_bg'])
            setting.save()
        else:
            settings[0].font_size = request.POST['font_size']
            settings[0].read_bg = request.POST['read_bg']
            settings[0].save()
        return HttpResponse('ok')  
    return HttpResponse('not login')  

@login_required(login_url='reader:index')
def bookmark_save(request):
    if not request.user.is_authenticated:
        return HttpResponse('not login')  
    
    if request.method == 'POST':
        user_bookmark = UserBookMark(user_id = request.user.id,book_id = request.POST['book_id'],chapter_id = request.POST['chapter_id'],
            words_read = request.POST['words_read'],content =request.POST['content'] )
        user_bookmark.save()
        return HttpResponse('ok')  

    
def ret_null(request):
    return HttpResponse('')
