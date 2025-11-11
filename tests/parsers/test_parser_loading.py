"""Tests for parser loading optimizations."""

from __future__ import annotations

from custom_components.cable_modem_monitor.parsers import (
    get_parser_by_name,
    get_parsers,
)
from custom_components.cable_modem_monitor.parsers.base_parser import ModemParser


class TestParserCaching:
    """Test parser caching functionality."""

    def test_get_parsers_caches_results(self):
        """Test that get_parsers caches results on first call."""
        ***REMOVED*** Clear cache
        import custom_components.cable_modem_monitor.parsers as parser_module

        parser_module._PARSER_CACHE = None

        ***REMOVED*** First call should populate cache
        parsers1 = get_parsers(use_cache=True)
        assert parser_module._PARSER_CACHE is not None
        assert len(parsers1) > 0  ***REMOVED*** type: ignore[unreachable]

        ***REMOVED*** Second call should return cached results
        parsers2 = get_parsers(use_cache=True)
        assert parsers2 is parsers1  ***REMOVED*** Same object reference

    def test_get_parsers_bypass_cache(self):
        """Test that get_parsers can bypass cache when requested."""
        ***REMOVED*** First call with cache
        parsers1 = get_parsers(use_cache=True)

        ***REMOVED*** Second call bypassing cache should re-discover
        parsers2 = get_parsers(use_cache=False)
        assert len(parsers2) == len(parsers1)
        ***REMOVED*** Should be different objects (re-discovered)
        assert parsers2 is not parsers1

    def test_get_parsers_returns_all_known_parsers(self):
        """Test that get_parsers finds all expected parsers."""
        parsers = get_parsers()
        parser_names = [p.name for p in parsers]

        ***REMOVED*** Check for known parsers
        assert "ARRIS SB6141" in parser_names
        assert "ARRIS SB6190" in parser_names
        assert "Motorola MB Series (Generic)" in parser_names
        assert "Motorola MB7621" in parser_names
        assert "Motorola MB8611 (HNAP)" in parser_names
        assert "Motorola MB8611 (Static)" in parser_names
        assert "Technicolor TC4400" in parser_names
        assert "Technicolor XB7" in parser_names

    def test_get_parsers_sorts_by_manufacturer_and_priority(self):
        """Test that parsers are sorted correctly."""
        parsers = get_parsers()

        ***REMOVED*** Check that parsers are grouped by manufacturer
        manufacturers = [p.manufacturer for p in parsers]
        ***REMOVED*** Should have ARRIS, Motorola, Technicolor groups
        assert "ARRIS" in manufacturers
        assert "Motorola" in manufacturers
        assert "Technicolor" in manufacturers

        ***REMOVED*** Within Motorola, check priority ordering
        motorola_parsers = [p for p in parsers if p.manufacturer == "Motorola"]
        priorities = [p.priority for p in motorola_parsers]
        ***REMOVED*** Higher priority should come first (descending order)
        assert priorities == sorted(priorities, reverse=True)


class TestGetParserByName:
    """Test get_parser_by_name functionality."""

    def test_get_parser_by_name_motorola_mb7621(self):
        """Test loading Motorola MB7621 parser by name."""
        parser_class = get_parser_by_name("Motorola MB7621")
        assert parser_class is not None
        assert issubclass(parser_class, ModemParser)
        assert parser_class.name == "Motorola MB7621"
        assert parser_class.manufacturer == "Motorola"

    def test_get_parser_by_name_mb8611_static(self):
        """Test loading MB8611 Static parser by name."""
        parser_class = get_parser_by_name("Motorola MB8611 (Static)")
        assert parser_class is not None
        assert issubclass(parser_class, ModemParser)
        assert parser_class.name == "Motorola MB8611 (Static)"
        ***REMOVED*** Verify it has the fixed url_patterns
        assert hasattr(parser_class, "url_patterns")
        assert len(parser_class.url_patterns) > 0

    def test_get_parser_by_name_mb8611_hnap(self):
        """Test loading MB8611 HNAP parser by name."""
        parser_class = get_parser_by_name("Motorola MB8611 (HNAP)")
        assert parser_class is not None
        assert issubclass(parser_class, ModemParser)
        assert parser_class.name == "Motorola MB8611 (HNAP)"

    def test_get_parser_by_name_arris_sb6190(self):
        """Test loading ARRIS SB6190 parser by name."""
        parser_class = get_parser_by_name("ARRIS SB6190")
        assert parser_class is not None
        assert issubclass(parser_class, ModemParser)
        assert parser_class.name == "ARRIS SB6190"
        assert parser_class.manufacturer == "ARRIS"

    def test_get_parser_by_name_invalid(self):
        """Test that invalid parser name returns None."""
        parser_class = get_parser_by_name("Invalid Parser Name")
        assert parser_class is None

    def test_get_parser_by_name_instantiable(self):
        """Test that returned parser class can be instantiated."""
        parser_class = get_parser_by_name("Motorola MB7621")
        assert parser_class is not None

        ***REMOVED*** Should be able to create an instance
        parser_instance = parser_class()
        assert isinstance(parser_instance, ModemParser)


class TestParserLoadingPerformance:
    """Test performance characteristics of parser loading."""

    def test_direct_load_faster_than_discovery(self):
        """Test that direct loading is faster than full discovery."""
        import time

        import custom_components.cable_modem_monitor.parsers as parser_module

        ***REMOVED*** Clear cache to ensure fair comparison
        parser_module._PARSER_CACHE = None

        ***REMOVED*** Time full discovery
        start = time.perf_counter()
        get_parsers(use_cache=False)
        discovery_time = time.perf_counter() - start

        ***REMOVED*** Time direct load
        start = time.perf_counter()
        get_parser_by_name("Motorola MB7621")
        direct_time = time.perf_counter() - start

        ***REMOVED*** Direct load should be significantly faster (at least 2x)
        ***REMOVED*** In practice, it's often 8x+ faster
        assert direct_time < discovery_time / 2

    def test_cached_load_is_instant(self):
        """Test that cached parser loading is very fast."""
        import time

        ***REMOVED*** Prime the cache
        get_parsers(use_cache=True)

        ***REMOVED*** Time cached load
        start = time.perf_counter()
        get_parsers(use_cache=True)
        cached_time = time.perf_counter() - start

        ***REMOVED*** Cached load should be extremely fast (< 1ms)
        assert cached_time < 0.001


class TestMB8611StaticParserFix:
    """Test that MB8611 Static parser has required url_patterns."""

    def test_mb8611_static_has_url_patterns(self):
        """Test that MB8611 Static parser has url_patterns attribute."""
        parser_class = get_parser_by_name("Motorola MB8611 (Static)")
        assert parser_class is not None

        ***REMOVED*** Check for url_patterns attribute
        assert hasattr(parser_class, "url_patterns")
        assert isinstance(parser_class.url_patterns, list)
        assert len(parser_class.url_patterns) > 0

    def test_mb8611_static_url_patterns_format(self):
        """Test that MB8611 Static url_patterns are correctly formatted."""
        parser_class = get_parser_by_name("Motorola MB8611 (Static)")
        assert parser_class is not None

        ***REMOVED*** Check first pattern
        pattern = parser_class.url_patterns[0]
        assert "path" in pattern
        assert "auth_method" in pattern
        assert "auth_required" in pattern

        ***REMOVED*** Check specific values
        assert pattern["path"] == "/MotoStatusConnection.html"
        assert pattern["auth_method"] == "none"
        assert pattern["auth_required"] is False
