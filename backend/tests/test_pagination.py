from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.pagination import PagedResponse, PaginationParams


class TestPaginationOffset:
    def test_first_page_offset_is_zero(self) -> None:
        params = PaginationParams(page=1, page_size=20)
        assert params.offset == 0

    def test_second_page_offset(self) -> None:
        params = PaginationParams(page=2, page_size=20)
        assert params.offset == 20

    def test_offset_with_custom_page_size(self) -> None:
        params = PaginationParams(page=3, page_size=10)
        assert params.offset == 20

    def test_large_page_offset(self) -> None:
        params = PaginationParams(page=10, page_size=100)
        assert params.offset == 900


class TestPaginationValidation:
    def test_page_zero_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PaginationParams(page=0, page_size=20)

    def test_negative_page_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PaginationParams(page=-1, page_size=20)

    def test_page_size_above_100_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PaginationParams(page=1, page_size=101)

    def test_page_size_zero_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PaginationParams(page=1, page_size=0)

    def test_page_size_100_is_valid(self) -> None:
        params = PaginationParams(page=1, page_size=100)
        assert params.page_size == 100

    def test_defaults_are_page_1_size_20(self) -> None:
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20


class TestPagedResponse:
    def test_paged_response_structure(self) -> None:
        response = PagedResponse[str](total=50, page=2, page_size=10, items=["a", "b"])
        assert response.total == 50
        assert response.page == 2
        assert response.page_size == 10
        assert response.items == ["a", "b"]
