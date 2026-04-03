package com.ganizanisitara.moniker.resolver.moniker;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for MonikerParser.
 */
class MonikerParserTest {

    @Test
    void testParseSimplePath() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices.equity/AAPL");

        assertEquals("prices.equity/AAPL", m.getPath().toString());
        assertNull(m.getNamespace());
        assertFalse(m.hasSegmentId());
    }

    @Test
    void testParseWithNamespace() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prod@prices/AAPL");

        assertEquals("prices/AAPL", m.getPath().toString());
        assertEquals("prod", m.getNamespace());
    }

    @Test
    void testParseWithRevision() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/AAPL/v2");

        assertEquals("prices/AAPL", m.getPath().toString());
        assertEquals(2, m.getRevision());
    }

    @Test
    void testParseWithScheme() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("moniker://holdings/fund_alpha");

        assertEquals("holdings/fund_alpha", m.getPath().toString());
    }

    @Test
    void testParseWithQueryParams() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("holdings/fund_alpha?format=json");

        assertEquals("holdings/fund_alpha", m.getPath().toString());
        assertTrue(m.getParams().has("format"));
        assertEquals("json", m.getParams().get("format"));
    }

    @Test
    void testParseWithNamespaceAndRevision() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prod@prices/AAPL/v3");

        assertEquals("prod", m.getNamespace());
        assertEquals(3, m.getRevision());
        assertEquals("prices/AAPL", m.getPath().toString());
    }

    // --- @id identity parameter tests (OM-17) ---

    @Test
    void testParseSegmentIdMidPath() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("holdings/positions@ACC001/summary");

        assertTrue(m.hasSegmentId());
        assertEquals(1, m.getSegmentIdIndex());
        assertEquals("ACC001", m.getSegmentIdValue());
        assertEquals("holdings/positions/summary", m.canonicalPath());
    }

    @Test
    void testParseSegmentIdFirstSegment() throws MonikerParseException {
        // Segment 0 @id requires namespace prefix to avoid ambiguity
        Moniker m = MonikerParser.parseMoniker("prod@portfolios@FUND_ALPHA/holdings");

        assertEquals("prod", m.getNamespace());
        assertTrue(m.hasSegmentId());
        assertEquals(0, m.getSegmentIdIndex());
        assertEquals("FUND_ALPHA", m.getSegmentIdValue());
        assertEquals("portfolios/holdings", m.canonicalPath());
    }

    @Test
    void testParseSegmentIdWithRevision() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("holdings/positions@ACC001/summary/v3");

        assertTrue(m.hasSegmentId());
        assertEquals("ACC001", m.getSegmentIdValue());
        assertEquals(3, m.getRevision());
        assertEquals("holdings/positions/summary", m.canonicalPath());
    }

    @Test
    void testParseSegmentIdWithNamespace() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prod@holdings/positions@ACC001/summary");

        assertEquals("prod", m.getNamespace());
        assertTrue(m.hasSegmentId());
        assertEquals("ACC001", m.getSegmentIdValue());
        assertEquals("holdings/positions/summary", m.canonicalPath());
    }

    @Test
    void testParseNoSegmentId() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/AAPL");

        assertFalse(m.hasSegmentId());
        assertNull(m.getSegmentIdValue());
    }

    @Test
    void testParseSegmentIdFullPath() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("holdings/positions@ACC001/summary");

        assertEquals("holdings/positions@ACC001/summary", m.fullPath());
    }

    @Test
    void testParseSegmentIdStringRoundtrip() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("holdings/positions@ACC001/summary");

        String s = m.toString();
        assertTrue(s.contains("positions@ACC001"));
    }

    @Test
    void testParseSegmentIdSpecialChars() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("holdings/positions@ACC-001.test_val/summary");

        assertTrue(m.hasSegmentId());
        assertEquals("ACC-001.test_val", m.getSegmentIdValue());
    }

    // --- @id error cases ---

    @Test
    void testRejectAtEndOfPath() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("prices/AAPL@20260101");
        });
    }

    @Test
    void testRejectMultipleAtId() {
        // Use namespace prefix so the first @ isn't consumed as namespace
        MonikerParseException ex = assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("ns@holdings@ACC001/positions@XYZ/summary");
        });
        assertTrue(ex.getMessage().contains("At most one @id"));
    }

    @Test
    void testRejectEmptyAtId() {
        MonikerParseException ex = assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("holdings/positions@/summary");
        });
        assertTrue(ex.getMessage().contains("Empty @id value"));
    }

    @Test
    void testRejectInvalidAtIdChars() {
        MonikerParseException ex = assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("holdings/positions@ACC 001/summary");
        });
        assertTrue(ex.getMessage().contains("Invalid segment identity value"));
    }

    // --- @version rejection tests (OM-19: @version syntax removed) ---

    @Test
    void testRejectAtVersionLatest() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("prices/AAPL@latest");
        });
    }

    @Test
    void testRejectAtVersionDate() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("prices/AAPL@20260101");
        });
    }

    @Test
    void testRejectAtVersionLookback() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("prices/AAPL@3M");
        });
    }

    @Test
    void testRejectAtVersionAll() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("risk.cvar/portfolio-123@all");
        });
    }

    @Test
    void testRejectAtVersionFrequency() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("prices/AAPL@daily");
        });
    }

    @Test
    void testRejectBareAtEnd() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("prices/AAPL@");
        });
    }

    // --- date@VALUE tests (OM-20) ---

    @Test
    void testParseDateParamAbsolute() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/AAPL/date@20260101");
        assertEquals("20260101", m.getDateParam());
        assertEquals("prices/equity/AAPL", m.canonicalPath());
    }

    @Test
    void testParseDateParamLatest() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/AAPL/date@latest");
        assertEquals("latest", m.getDateParam());
    }

    @Test
    void testParseDateParamPrevious() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/AAPL/date@previous");
        assertEquals("previous", m.getDateParam());
    }

    @Test
    void testParseDateParamRelative() throws MonikerParseException {
        for (String val : new String[]{"3M", "1Y", "2W", "5D"}) {
            Moniker m = MonikerParser.parseMoniker("prices/equity/AAPL/date@" + val);
            assertEquals(val, m.getDateParam());
        }
    }

    @Test
    void testParseDateParamNotInCanonicalPath() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/AAPL/date@20260101");
        assertFalse(m.canonicalPath().contains("date@"));
        assertEquals(3, m.getPath().length()); // date@ is not a positional segment
    }

    @Test
    void testParseDateParamWithSegmentId() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("holdings/positions@ACC001/summary/date@20260101");
        assertEquals("ACC001", m.getSegmentIdValue());
        assertEquals("20260101", m.getDateParam());
    }

    @Test
    void testParseDateParamWithRevision() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/AAPL/date@20260101/v2");
        assertEquals("20260101", m.getDateParam());
        assertEquals(2, m.getRevision());
    }

    @Test
    void testParseDateParamWithQueryParams() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/AAPL/date@latest?format=json");
        assertEquals("latest", m.getDateParam());
        assertEquals("json", m.getParams().get("format"));
    }

    @Test
    void testParseDateParamInStringOutput() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/AAPL/date@20260101");
        assertTrue(m.toString().contains("date@20260101"));
    }

    @Test
    void testParseDateParamCaseInsensitive() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/AAPL/date@Latest");
        assertEquals("Latest", m.getDateParam());
    }

    @Test
    void testParseDateParamEmpty() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("prices/AAPL/date@");
        });
    }

    @Test
    void testParseDateParamInvalid() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("prices/AAPL/date@notadate");
        });
    }

    @Test
    void testParseDateParamZeroPrefix() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("prices/AAPL/date@0M");
        });
    }

    @Test
    void testParseDateParamWithScheme() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("moniker://prices/equity/AAPL/date@20260101");
        assertEquals("20260101", m.getDateParam());
    }

    @Test
    void testParseNoDateParamByDefault() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/AAPL");
        assertNull(m.getDateParam());
    }

    @Test
    void testParseDateParamWithNamespace() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prod@prices/equity/AAPL/date@20260101");
        assertEquals("prod", m.getNamespace());
        assertEquals("20260101", m.getDateParam());
    }

    // --- filter@CODE tests (OM-21) ---

    private MonikerParser.ShortlinkStore mockStore() {
        return code -> {
            if ("abc123".equals(code)) {
                return new MonikerParser.ShortlinkEntry(
                    java.util.Arrays.asList("developed", "EUR"),
                    java.util.Map.of("region", "EMEA")
                );
            }
            return null;
        };
    }

    @Test
    void testParseFilterExpands() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/filter@abc123", mockStore());
        assertEquals("filter@abc123", m.getFilterShortlink());
        assertEquals("prices/equity/developed/EUR", m.canonicalPath());
        assertEquals("EMEA", m.getParams().get("region"));
    }

    @Test
    void testParseFilterSplicesInPlace() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/filter@abc123/summary", mockStore());
        assertEquals("prices/equity/developed/EUR/summary", m.canonicalPath());
    }

    @Test
    void testParseFilterWithSegmentId() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("holdings/positions@ACC001/filter@abc123/summary", mockStore());
        assertEquals("ACC001", m.getSegmentIdValue());
        assertNotNull(m.getFilterShortlink());
    }

    @Test
    void testParseFilterWithDateParam() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/filter@abc123/date@20260101", mockStore());
        assertEquals("20260101", m.getDateParam());
    }

    @Test
    void testParseFilterEmptyCode() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("prices/equity/filter@");
        });
    }

    @Test
    void testParseFilterNoStore() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("prices/equity/filter@abc123");
        });
    }

    @Test
    void testParseFilterUnknownCode() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("prices/equity/filter@UNKNOWN", mockStore());
        });
    }

    @Test
    void testParseFilterCanonicalPathClean() throws MonikerParseException {
        Moniker m = MonikerParser.parseMoniker("prices/equity/filter@abc123", mockStore());
        assertFalse(m.canonicalPath().contains("filter@"));
    }

    // --- Validation tests ---

    @Test
    void testValidateSegment() {
        assertTrue(MonikerParser.validateSegment("valid_segment"));
        assertTrue(MonikerParser.validateSegment("segment123"));
        assertTrue(MonikerParser.validateSegment("seg.ment"));
        assertTrue(MonikerParser.validateSegment("seg-ment"));

        assertFalse(MonikerParser.validateSegment(""));
        assertFalse(MonikerParser.validateSegment("_invalid"));
        assertFalse(MonikerParser.validateSegment("-invalid"));
    }

    @Test
    void testValidateNamespace() {
        assertTrue(MonikerParser.validateNamespace("valid"));
        assertTrue(MonikerParser.validateNamespace("valid_namespace"));
        assertTrue(MonikerParser.validateNamespace("valid-namespace"));

        assertFalse(MonikerParser.validateNamespace(""));
        assertFalse(MonikerParser.validateNamespace("123invalid"));
        assertFalse(MonikerParser.validateNamespace("_invalid"));
        assertFalse(MonikerParser.validateNamespace("invalid.namespace"));
    }

    @Test
    void testInvalidMoniker() {
        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("");
        });

        assertThrows(MonikerParseException.class, () -> {
            MonikerParser.parseMoniker("invalid://scheme");
        });
    }
}
