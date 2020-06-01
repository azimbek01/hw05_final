from django.forms import ModelForm, Textarea
from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': 'Текст',
            'group': 'Сообщество',
            'image': 'Изображение'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labeld = {
            'text': 'Введите комментарий'
        }
        widgets = {
            'text': Textarea(attrs={'cols': 80, 'rows': 5}),
        }
