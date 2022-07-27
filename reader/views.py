from msilib.schema import ControlEvent
from django.http import HttpResponse, HttpResponseRedirect
from .forms import UploadFileForm
from .models import *
from django.views import generic
from django.shortcuts import get_object_or_404, redirect, render
import json
from django.contrib.auth import authenticate,login,logout


def upload_file(request):
    if  request.method == 'POST':
        handle_uploaded_file(request.FILES['file'])
        return render(request, 'upload_file.html', {'notice':"succeed"})
        

    return render(request, 'upload_file.html')




class BookListView(generic.ListView):
    template_name = 'book_list.html'
    context_object_name = 'book_list'

    def get_queryset(self):
        """Return the last five published questions."""
        return Book.objects.all()

class BookAdminView(generic.ListView):
    template_name = 'book_admin.html'
    context_object_name = 'book_list'

    def get_queryset(self):
        """Return the last five published questions."""
        return Book.objects.all()

class ChapterListView(generic.ListView):
    template_name = 'chapter_list.html'
    context_object_name = 'chapter_list'

    def get_queryset(self):
        return Chapter.objects.filter(book_id=self.kwargs['pk'])


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
    book =  get_object_or_404(Book,id = pk)
    print(pk)
    return redirect('reader:book_reader',book_pk=pk,chapter_pk=book.first_chapter)


def book_reader(request,book_pk,chapter_pk):
    if  request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponse('required login')  
        
        if 'words' in request.POST:
            UserBookRecord(user_id =request.user.id, book_id =book_pk, chapter_id = chapter_pk, words_read = int(request.POST['words'])).save()
            return HttpResponse('success')  
        if 'kwd' in request.POST:
            return keyword_search(request,book_pk,chapter_pk,str(request.POST['kwd']))


    chapter_list = Chapter.objects.filter(book_id = book_pk)
    chapter = get_object_or_404(Chapter,pk = chapter_pk)
    con = get_object_or_404(Content,pk = chapter.content_id)
    content_lines = con.content.split('\n')
    if len(content_lines) == 1:
        content_lines = content_lines[0].split(' ',1)
    # print(request.META['HTTP_REFERER'])
    if request.user.is_authenticated and 'HTTP_REFERER' in request.META and 'book_list' in request.META['HTTP_REFERER'] :
        last = UserBookRecord.objects.filter(user_id = request.user.id , book_id = book_pk).order_by('-read_time')
        user_setting = get_object_or_404(UserSetting,user_id = request.user.id)
        if len(last) > 0:
            last = last[0]
            print(last.words_read)
            return render(request, 'book_reader.html', 
                {'chapter_list': chapter_list,'chapter_title':content_lines[0],'content_lines':content_lines[1:],
                'last_words':last.words_read,'user_setting':user_setting})

    if request.user.is_authenticated:
        user_setting = get_object_or_404(UserSetting,user_id = request.user.id)
        return render(request, 'book_reader.html', {'chapter_list': chapter_list,'chapter_title':content_lines[0],'content_lines':content_lines[1:],'user_setting':user_setting})
    else:
        return render(request, 'book_reader.html', {'chapter_list': chapter_list,'chapter_title':content_lines[0],'content_lines':content_lines[1:]})

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

def update_setting(request):
    if request.user.is_authenticated and request.method == 'POST':
        print(request.POST.keys())
        print(request.POST['font_size'])
        print(request.POST['read_bg'])
        
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