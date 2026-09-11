// Страница списка — контракт бэкенда (Б7): items + total + окно.
export type Page<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type PageQuery = {
  limit: number;
  offset: number;
};
