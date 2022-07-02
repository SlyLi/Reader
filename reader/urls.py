from django.urls import path

from . import views

app_name = 'reader'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    # path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    # path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    path('upload_file', views.upload_file, name='upload_file'),
    path('book_list', views.BookListView.as_view(), name='book_list'),
    path('chapter_list/<int:pk>', views.ChapterListView.as_view(), name='chapter_list'),
    path('chapter_detail/<int:pk>', views.ChapterDetailView.as_view(), name='chapter_detail'),
    path('book_temp/<int:pk>', views.book, name='book'),
    path('book/<int:book_pk>/<int:chapter_pk>', views.book_reader, name='book_reader'),
    path('login', views.login, name='login'),

]