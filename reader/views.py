from msilib.schema import ControlEvent
from django.http import HttpResponse, HttpResponseRedirect
from .forms import UploadFileForm
from .models import *
from django.views import generic
from django.shortcuts import get_object_or_404, redirect, render
import json


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
        
        UserBookRecord(user_id =request.user.id, book_id =book_pk, chapter_id = chapter_pk, words_read = int(request.POST['words'])).save()
        return HttpResponse('success')  

    chapter_list = Chapter.objects.filter(book_id = book_pk)
    chapter = get_object_or_404(Chapter,pk = chapter_pk)
    con = get_object_or_404(Content,pk = chapter.content_id)
    content_lines = con.content.split('\n')
    if len(content_lines) == 1:
        content_lines = content_lines[0].split(' ',1)
    # print(request.META['HTTP_REFERER'])
    if request.user.is_authenticated and 'HTTP_REFERER' in request.META and 'book_list' in request.META['HTTP_REFERER'] :
        last = UserBookRecord.objects.filter(user_id = request.user.id , book_id = book_pk).order_by('-read_time')
        if len(last) > 0:
            last = last[0]
            print(last.words_read)
            return render(request, 'book_reader.html', {'chapter_list': chapter_list,'chapter_title':content_lines[0],'content_lines':content_lines[1:],'last_words':last.words_read})

    
    return render(request, 'book_reader.html', {'chapter_list': chapter_list,'chapter_title':content_lines[0],'content_lines':content_lines[1:]})
