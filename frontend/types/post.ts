export type Post = {
  id: string | number;
  title: string;
  user?: string;
  label?: string;
  labelColor?: string;
  text?: string;
  date?: string;
  url?: string;
  model?: string;
};


export type PaginationMeta = {
  page: number;
  per_page: number;
  total_pages: number;
  total_items: number;
};

export type PaginatedResponse = {
  posts: Post[];
  meta: PaginationMeta;
};