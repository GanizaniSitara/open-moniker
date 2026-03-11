/** Static vendor directory — will eventually be wired to the Moniker Service. */

export interface Vendor {
  key: string;
  name: string;
  description: string;
  category: string;
  datasetCount: number;
  website?: string;
}

export const VENDORS: Vendor[] = [
  // Major market data
  {
    key: "bloomberg",
    name: "Bloomberg",
    description:
      "Global financial data, analytics, and trading platform. Provides real-time and historical pricing, reference data, indices, and fixed income analytics.",
    category: "Market Data",
    datasetCount: 12,
    website: "https://www.bloomberg.com",
  },
  {
    key: "refinitiv",
    name: "Refinitiv (LSEG)",
    description:
      "Financial market data and infrastructure provider. Delivers pricing, reference data, time-series, and ESG data across asset classes via Eikon and Datascope.",
    category: "Market Data",
    datasetCount: 9,
    website: "https://www.lseg.com/en/data-analytics",
  },
  {
    key: "factset",
    name: "FactSet",
    description:
      "Integrated financial data and analytics platform. Covers company fundamentals, estimates, ownership, supply chain, and portfolio analytics.",
    category: "Market Data",
    datasetCount: 6,
    website: "https://www.factset.com",
  },
  {
    key: "ice",
    name: "ICE Data Services",
    description:
      "Exchange and fixed income reference data, evaluated pricing, indices, and analytics. Covers bonds, derivatives, and structured products.",
    category: "Market Data",
    datasetCount: 5,
  },

  // Economics & macro
  {
    key: "haver",
    name: "Haver Analytics",
    description:
      "Macroeconomic and financial time-series databases. Covers national accounts, labour, trade, industrial production, and central bank data across 200+ countries.",
    category: "Economics",
    datasetCount: 4,
    website: "https://www.haver.com",
  },
  {
    key: "fred",
    name: "FRED (St. Louis Fed)",
    description:
      "Free macroeconomic data from the Federal Reserve Bank of St. Louis. Over 800,000 time series covering interest rates, employment, GDP, and inflation.",
    category: "Economics",
    datasetCount: 3,
    website: "https://fred.stlouisfed.org",
  },
  {
    key: "imf",
    name: "IMF Data",
    description:
      "International Monetary Fund datasets including World Economic Outlook, Balance of Payments, International Financial Statistics, and Direction of Trade.",
    category: "Economics",
    datasetCount: 2,
  },

  // Fixed income & credit
  {
    key: "moodys",
    name: "Moody's Analytics",
    description:
      "Credit ratings, research, risk management tools, and structured finance data. Covers corporate and sovereign credit, CDS, and default studies.",
    category: "Credit & Ratings",
    datasetCount: 4,
  },
  {
    key: "sp-global",
    name: "S&P Global Market Intelligence",
    description:
      "Credit ratings, company financials, capital structure, and leveraged loan data. Includes Capital IQ, LCD, and Ratings Direct platforms.",
    category: "Credit & Ratings",
    datasetCount: 5,
  },
  {
    key: "fitch",
    name: "Fitch Ratings",
    description:
      "Credit ratings and research for corporates, sovereigns, structured finance, and financial institutions.",
    category: "Credit & Ratings",
    datasetCount: 2,
  },

  // Mortgage & structured products
  {
    key: "corelogic",
    name: "CoreLogic",
    description:
      "Property data and analytics covering home prices, mortgage performance, loan-level data, and real estate market trends across the US.",
    category: "Mortgage & Real Estate",
    datasetCount: 3,
  },
  {
    key: "black-knight",
    name: "Black Knight (ICE Mortgage)",
    description:
      "Mortgage performance data, loan-level analytics, prepayment models, and property valuation. Covers agency and non-agency MBS.",
    category: "Mortgage & Real Estate",
    datasetCount: 3,
  },
  {
    key: "intex",
    name: "Intex Solutions",
    description:
      "Structured finance cash flow models and analytics. Covers RMBS, CMBS, ABS, CLO deal structures and waterfall modelling.",
    category: "Mortgage & Real Estate",
    datasetCount: 2,
  },

  // Index & benchmark
  {
    key: "msci",
    name: "MSCI",
    description:
      "Equity and fixed income indices, ESG ratings, factor models, and risk analytics. Covers developed and emerging market benchmarks.",
    category: "Index & Benchmark",
    datasetCount: 4,
  },
  {
    key: "ftse-russell",
    name: "FTSE Russell",
    description:
      "Index provider covering equities, fixed income, and multi-asset benchmarks. Includes Russell indices and FTSE global equity series.",
    category: "Index & Benchmark",
    datasetCount: 3,
  },
  {
    key: "barclays-indices",
    name: "Bloomberg Barclays Indices",
    description:
      "Fixed income benchmark indices including US Aggregate, Global Aggregate, and corporate bond index families.",
    category: "Index & Benchmark",
    datasetCount: 3,
  },

  // Alternative & ESG
  {
    key: "preqin",
    name: "Preqin",
    description:
      "Alternative assets data covering private equity, hedge funds, real estate, infrastructure, and natural resources. Fund performance and fundraising data.",
    category: "Alternative Data",
    datasetCount: 2,
  },
  {
    key: "sustainalytics",
    name: "Sustainalytics (Morningstar)",
    description:
      "ESG risk ratings, controversy research, and corporate governance data. Covers 20,000+ companies globally.",
    category: "ESG",
    datasetCount: 2,
  },

  // Open-source market data
  {
    key: "yfinance",
    name: "Yahoo Finance",
    description:
      "Open-source market data via yfinance Python library. Covers equities, ETFs, futures, and index data with historical OHLCV and fundamentals.",
    category: "Market Data",
    datasetCount: 6,
    website: "https://finance.yahoo.com",
  },

  // Reference data
  {
    key: "cusip-global",
    name: "CUSIP Global Services",
    description:
      "Security identifiers (CUSIP, CINS, ISIN) and reference data for North American and global securities. Operated by FactSet on behalf of the ABA.",
    category: "Reference Data",
    datasetCount: 1,
  },
  {
    key: "dtcc",
    name: "DTCC",
    description:
      "Trade reporting, clearing, and settlement data. Provides derivatives reference data, LEI, and corporate actions through Global Trade Repository.",
    category: "Reference Data",
    datasetCount: 2,
  },
];
