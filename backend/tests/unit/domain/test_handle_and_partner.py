from datetime import UTC, datetime

import pytest

from vinichannels.domain.channels.value_objects import Handle
from vinichannels.domain.partners.entities import Partner
from vinichannels.domain.shared.errors import InvalidStateError, ValidationError
from vinichannels.domain.shared.ids import PartnerId


@pytest.mark.parametrize("raw", ["@Brand.VN", "brand.vn", "  @brand.vn  "])
def test_handle_is_normalized(raw: str) -> None:
    handle = Handle(raw)
    assert handle.value == "brand.vn"
    assert handle.display == "@brand.vn"


@pytest.mark.parametrize("raw", ["", "@", "a", "brand vn", "brand.", "x" * 30, "bran$d"])
def test_handle_rejects_invalid(raw: str) -> None:
    with pytest.raises(ValidationError):
        Handle(raw)


def test_partner_requires_name() -> None:
    with pytest.raises(ValidationError):
        Partner(id=PartnerId("p1"), name="   ")


def test_partner_tags_are_normalized_and_unique() -> None:
    partner = Partner(id=PartnerId("p1"), name="Brand A")
    partner.add_tag(" Thời Trang ")
    partner.add_tag("thời trang")
    assert partner.tags == frozenset({"thời trang"})
    partner.remove_tag("THỜI TRANG")
    assert partner.tags == frozenset()


def test_partner_archive_and_restore() -> None:
    partner = Partner(id=PartnerId("p1"), name="Brand A")
    partner.archive(datetime(2026, 10, 19, tzinfo=UTC))
    assert partner.is_archived
    with pytest.raises(InvalidStateError):
        partner.archive(datetime(2026, 10, 20, tzinfo=UTC))
    partner.restore()
    assert not partner.is_archived
    with pytest.raises(InvalidStateError):
        partner.restore()
