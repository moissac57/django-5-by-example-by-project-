from django.core.paginator import EmptyPage, Paginator
from django.shortcuts import get_object_or_404, render
from django.core.mail import send_mail
from django.views.generic import ListView
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.contrib.postgres.search import SearchVector
from django.contrib.postgres.search import (
    SearchVector, SearchQuery, SearchRank)
from django.contrib.postgres.search import TrigramSimilarity

from .forms import EmailPostForm, CommentForm, SearchForms
from .models import Post
from taggit.models import Tag

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
    # List of similar comment
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(
        tags__in = post_tags_ids
    ).exclude(id=post.id)
    similar_posts = similar_posts.annotate(
        same_tags = Count('tags')
    ).order_by('-same_tags', '-publish')[:4]
    return render(
        request,
        'blog/post/detail.html',
        {'post':post,
         'comments':comments,
         'form':form,
         'similar_posts':similar_posts
         }
    )

def post_list(request, tag_slug=None):
    post_list=Post.published.all()
    tag=None
    if tag_slug:
        tag=get_object_or_404(Tag, slug=tag_slug)
        post_list=post_list.filter(tags__in=[tag])
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
        {'posts':posts,
         'tag':tag,
         'page_obj':posts}
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
    
def post_search(request):
    form = SearchForms()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForms(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A'
            )+ SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            results = (
                Post.published.annotate(
                    similarity = TrigramSimilarity('title', query)
                )
                .filter(similarity__gt=0.1)
                .order_by('-similarity')
            )

    return render(
        request,
        'blog/post/search.html',
        {
            'form': form,
            'query': query,
            'results': results
        }
    )
