from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.views.decorators.http import require_POST
from smtplib import SMTPException
from .models import Post, Comment
from .forms import EmailPostForm, CommentForm

def post_list(request):
    post_list = Post.published.all()
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    return render(request,
                 'blog/post/list.html',
                 {'posts': posts, 'page': posts})  # added 'page': posts


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)

    comments = post.comments.filter(active=True)

    form = CommentForm()

    return render(request, 'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'form': form})


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False

    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                post_url = request.build_absolute_uri(post.get_absolute_url())
                subject = f"{cd['name']} recommends reading {post.title}"
                message = (
                    f"Read '{post.title}' at the link {post_url}\n\n"
                    f"Comment from {cd['name']}: {cd['comments']}"
                )
                # Sending email
                result = send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[cd['to']],
                    fail_silently=False,
                )
                if result:
                    sent = True
                else:
                    print("Email was not sent")
            except SMTPException as e:
                print(f"SMTP error: {e}")
            except Exception as e:
                print(f"General error: {e}")
    else:
        form = EmailPostForm()

    return render(request,
                 'blog/post/share.html',
                 {'post': post, 'form': form, 'sent': sent})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    return render(request, 'blog/post/comment.html', 
                 {'post': post, 'form': form, 'comment': comment, 'errors': form.errors})
