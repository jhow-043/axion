import { useState } from "react";

interface PaginationState {
  page: number;
  pageSize: number;
}

interface PaginationActions {
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  reset: () => void;
}

export function usePagination(initialPageSize = 20): PaginationState & PaginationActions {
  const [page, setPageState] = useState(1);
  const [pageSize, setPageSizeState] = useState(initialPageSize);

  function setPage(p: number) {
    setPageState(p);
  }

  function setPageSize(size: number) {
    setPageSizeState(size);
    setPageState(1);
  }

  function reset() {
    setPageState(1);
    setPageSizeState(initialPageSize);
  }

  return { page, pageSize, setPage, setPageSize, reset };
}
