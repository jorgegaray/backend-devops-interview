from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja import Router

from blog.models import Comment, Post, Tag, User
from blog.schemas import (
    CommentCreateIn,
    CommentCreateOut,
    PostCreateIn,
    PostCreateOut,
    PostDetailOut,
    PostListOut,
    UserDetailOut,
)

router = Router()


def _serialize_author(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
    }

def _get_page_size(page_size: int = 10) -> int:
    return min(max(page_size, 1), settings.MAX_PAGE_SIZE)

def _get_page_number(page: int = 1) -> int:
    return max(page, settings.MIN_PAGE)


def _serialize_tag(tag: Tag) -> dict:
    return {"id": tag.id, "name": tag.name, "slug": tag.slug}


def _serialize_post_list(post: Post) -> dict:
    return {
        "id": post.id,
        "title": post.title,
        "author": _serialize_author(post.author),
        "tags": [_serialize_tag(t) for t in post.tags.all()],
        "view_count": post.view_count,
        "created_at": post.created_at,
    }


@router.get("/posts", response=list[PostListOut])
def list_posts(request, page: int = 1, page_size: int = 10):
    posts = Post.objects.filter(is_published=True).select_related("author").prefetch_related("tags").order_by("-created_at")
    paginator = Paginator(posts, _get_page_size(page_size))
    page_obj = paginator.get_page(_get_page_number(page))
    return [_serialize_post_list(p) for p in page_obj]


@router.get("/posts/search", response=list[PostListOut])
def search_posts(request, q: str):
    posts = Post.objects.filter(
        Q(title__icontains=q) | Q(body__icontains=q),
        is_published=True,
    ).order_by("-created_at")
    return [_serialize_post_list(p) for p in posts]


@router.get("/posts/by-tag/{slug}", response=list[PostListOut])
def posts_by_tag(request, slug: str):
    tag = get_object_or_404(Tag, slug=slug)
    posts = tag.posts.filter(is_published=True).order_by("-created_at")
    return [_serialize_post_list(p) for p in posts]


@router.get("/posts/{post_id}", response=PostDetailOut)
def get_post(request, post_id: int):
    updated = Post.objects.filter(id=post_id).update(view_count=F("view_count") + 1)

    if updated == 0:
        raise Http404("Post not found")


    post = get_object_or_404(Post.objects.select_related("author").prefetch_related("tags"), id=post_id)

    comments = post.comments.select_related("author").order_by("created_at")
    paginator = Paginator(comments, _get_page_size())
    page_comments = paginator.get_page(_get_page_number())
    comments = [
        {
            "id": c.id,
            "author": _serialize_author(c.author),
            "body": c.body,
            "created_at": c.created_at,
        }
        for c in page_comments
    ]
    return {
        "id": post.id,
        "title": post.title,
        "body": post.body,
        "author": _serialize_author(post.author),
        "tags": [_serialize_tag(t) for t in post.tags.all()],
        "comments": comments,
        "view_count": post.view_count,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }


@router.post("/posts", response=PostCreateOut)
def create_post(request, payload: PostCreateIn):
    author = get_object_or_404(User, id=payload.author_id)
    post = Post.objects.create(
        author=author,
        title=payload.title,
        body=payload.body,
    )

    tags = Tag.objects.filter(slug__in=payload.tag_slugs)
    post.tags.set(tags)
    return {"id": post.id, "title": post.title}


@router.post("/posts/{post_id}/comments", response=CommentCreateOut)
def create_comment(request, post_id: int, payload: CommentCreateIn):
    post = get_object_or_404(Post, id=post_id)
    author = get_object_or_404(User, id=payload.author_id)
    comment = Comment.objects.create(post=post, author=author, body=payload.body)
    return {"id": comment.id}


@router.get("/users/find", response=UserDetailOut)
def find_user_by_email(request, email: str):
    user = get_object_or_404(User, email=email)
    return _user_detail(user)


@router.get("/users/{user_id}", response=UserDetailOut)
def get_user(request, user_id: int):
    user = get_object_or_404(User, id=user_id)
    return _user_detail(user)


def _user_detail(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "bio": user.bio,
        "post_count": user.posts.count(),
        "comment_count": user.comments.count(),
    }
