"""
Tests for structural signature predicates used during discovery.

These tests validate low-level XML structure checks that operate
directly on XML elements. No filesystem access or classification
logic is involved.

They must work both with and without XML namespaces.
"""

from lxml import etree

from dita_package_processor.discovery.signatures import (
    has_topicrefs,
    has_maprefs,
)


# ---------------------------------------------------------------------------
# topicref tests
# ---------------------------------------------------------------------------


def test_has_topicrefs_true() -> None:
    """
    ``has_topicrefs`` should return True when at least one ``<topicref>``
    element exists in the XML subtree.
    """
    root = etree.XML(
        """
        <map>
            <topicref href="topics/a.dita"/>
        </map>
        """
    )

    assert has_topicrefs(root) is True


def test_has_topicrefs_false() -> None:
    """
    ``has_topicrefs`` should return False when no ``<topicref>``
    elements are present.
    """
    root = etree.XML("<map></map>")

    assert has_topicrefs(root) is False


def test_has_topicrefs_with_namespace() -> None:
    """
    ``has_topicrefs`` must work when the document uses a default namespace.
    """
    root = etree.XML(
        """
        <map xmlns="http://dita.oasis-open.org/architecture/2005/">
            <topicref href="topics/a.dita"/>
        </map>
        """
    )

    assert has_topicrefs(root) is True


# ---------------------------------------------------------------------------
# mapref tests
# ---------------------------------------------------------------------------


def test_has_maprefs_true() -> None:
    """
    ``has_maprefs`` should return True when at least one ``<mapref>``
    element exists in the XML subtree.
    """
    root = etree.XML(
        """
        <map>
            <mapref href="Other.ditamap"/>
        </map>
        """
    )

    assert has_maprefs(root) is True


def test_has_maprefs_false() -> None:
    """
    ``has_maprefs`` should return False when no ``<mapref>``
    elements are present.
    """
    root = etree.XML("<map></map>")

    assert has_maprefs(root) is False


def test_has_maprefs_with_namespace() -> None:
    """
    ``has_maprefs`` must work when the document uses a default namespace.
    """
    root = etree.XML(
        """
        <map xmlns="http://dita.oasis-open.org/architecture/2005/">
            <mapref href="Other.ditamap"/>
        </map>
        """
    )

    assert has_maprefs(root) is True