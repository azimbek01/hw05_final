from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page,
                  'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.group_posts.order_by('-pub_date')
    paginator = Paginator(posts_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'page': page,
                  'paginator': paginator, 'group': group})


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            form_new = form.save(commit=False)
            form_new.author_id = request.user.pk
            form_new.save()
            return redirect('index')
    else:
        form = PostForm()
    return render(request, 'posts/new.html', {'form': form})


def profile(request, username):
    username = get_object_or_404(User, username=username)

    post_list = username.author_posts.order_by('-pub_date')
    count = post_list.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    author = get_object_or_404(User, username=username)

    return render(
        request, 'posts/profile.html', {
            'username': username, 'count': count, 'page': page,
            'paginator': paginator, 'author': author
            }
        )


def post_view(request, username, post_id):
    username = get_object_or_404(User, username=username)
    count = username.author_posts.count()
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    items = post.comments.all()

    return render(
        request, 'posts/post.html', {
            'username': username,
            'count': count,
            'post': post,
            'form': form,
            'items': items
            }
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user == post.author:
        if request.method == 'POST':
            form = PostForm(request.POST, files=request.FILES or None,
                            instance=post)
            if form.is_valid():
                form.save()
                return redirect('post', username=username, post_id=post_id)
        else:
            form = PostForm(instance=post)
        return render(request, 'posts/new.html', {'form': form, 'post': post})
    return redirect('post', username=username, post_id=post_id)


def page_not_found(request, exception):
    return render(request, 'misc/404.html', {'path': request.path},
                  status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    if request.method == 'POST':
        form_comment = CommentForm(request.POST)
        if form_comment.is_valid:
            form = form_comment.save(commit=False)
            form.author_id = request.user.pk
            form.post_id = post_id
            form.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    follow = Follow.objects.filter(user=request.user)
    authors = (i.author for i in follow)
    posts_list = Post.objects.filter(
        author__in=authors).order_by('-pub_date')
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'posts/follow.html', {'page': page, 'paginator': paginator}
        )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author).exists()
    if follow:
        return redirect('profile', username=username)
    else:
        if request.user != author:
            Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author).exists()
    if follow:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username=username)
