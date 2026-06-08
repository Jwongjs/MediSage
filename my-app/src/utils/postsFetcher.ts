import { SingleArticle } from 'types/types';

export async function getAllPosts(): Promise<SingleArticle[]> {
  const res = await fetch('/posts/posts.json');
  if (!res.ok) {
    throw new Error('Failed to load posts');
  }

  const data = await res.json();
  return data;
}

export async function getSinglePost(slug: string): Promise<SingleArticle | null> {
  const posts = await getAllPosts();
  const post = posts.find((p) => p.slug === slug);
  return post ?? null;
}
