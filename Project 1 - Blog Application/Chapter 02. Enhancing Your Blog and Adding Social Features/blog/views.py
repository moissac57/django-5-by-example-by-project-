from django.core.paginator import EmptyPage, Paginator
from django.shortcuts import get_object_or_404, render
from django.core.mail import send_mail
from django.views.generic import ListView
from django.views.decorators.http import require_POST

from .forms import EmailPostForm, CommentForm
from .models import Post

# Create your views here.
def post_share(request, post_id):
    # Retrive post by id
    post=get_object_or_404(
        Post,
        id=post_id,
        status=Post.Status.PUBLISHED
    )
    sent=False
    if request.method=='POST':
        # Form was submitted
        form=EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields passed validation
            cd=form.cleaned_data
            post_url=request.build_absolute_ur(
                post.get_absolute_url()
            )
            subject=(
                f"{cd['name']} ({cd['email']})"
                f"recommends you read {post.title}"
            )
            message=(
                f"Read {post.title} at {post_url}\n\n"
                f"{cd['name']}\'s comments: {cd['comments']}"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[cd['to']]
            )
            sent=True
    else:
        form=EmailPostForm()
    return render(
        request,
        'blog/post/share.html',
        {'post': post, 'form': form, 'sent':sent}
    )



class PostListView(ListView):
    """ Alternative post list view """
    queryset=Post.published.all()
    context_object_name='posts'
    paginate_by=3
    template_name='blog/post/list.html'

def post_detail(request, year, month, day, post):
    post=get_object_or_404(
        Post,
        status=Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day
    )
    # List of active comments for this post
    comments=post.comments.filter(active=True)
    # Form for users to comment
    form=CommentForm()
    return render(
        request,
        'blog/post/detail.html',
        {'post':post,
         'comments':comments,
         'form':form}
    )

def post_list(request):
    post_list=Post.published.all()
    # Pagination with 3 posts per page
    paginator=Paginator(post_list, 3)
    page_number=request.GET.get('page', 1)
    try:
        posts=paginator.page(page_number)
    except EmptyPage:
    # If page_nember is out of range, get last page of results.
        posts=paginator.page(paginator.num_pages)
    return render(
        request,
        'blog/post/list.html',
        {'posts':posts}
    )

@require_POST
def post_comment(request, post_id):
    post=get_object_or_404(
        Post,
        id=post_id,
        status=Post.Status.PUBLISHED
    )
    comment=None
    # A comment was posted
    form=CommentForm(data=request.POST)
    if form.is_valid():
        # Create a Comment object without saving
        # it to the database
        comment=form.save(commit=False)
        # Assign the post to the comment
        comment.post=post
        # Save the comment to the database
        comment.save()
        return render(
            request,
            'blog/post/comment.html',
            {
                'post':post,
                'form':form,
                'comment':comment
            }
        )