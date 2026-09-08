# Fact Knowledge Layer: Dataset Analysis & Findings

**Document Purpose**: Detailed analysis of the source datasets provided for the Fact Knowledge Layer assignment, focusing on the Delhivery dataset and its multi-document reconciliation challenges, with notes on the India Macroeconomy dataset.

---

## 1. Overview of Datasets

### Dataset 1: Delhivery Corporate & Financial Disclosures
Location: `delhivery/`

1. **`01-delhivery-prospectus-2022-excerpt.pdf`**
   - **Document Type**: Initial Public Offering (IPO) Prospectus (SEBI statutory filing)
   - **Publication Date**: May 14, 2022
   - **Page Count in Excerpt**: 100 pages (Original pages: 1, 4, 26–37, 94–120, 216–245, 250–278)
   - **Key Content Areas**: Corporate history, IPO offer details, business overview, capitalization, historical financials for FY19–FY21, 9-month figures ending Dec 31, 2021, and Spoton acquisition integration data.

2. **`02-delhivery-annual-report-fy24-excerpt.pdf`**
   - **Document Type**: Statutory Annual Report (Audited FY 2023–24)
   - **Publication Date**: August 2024
   - **Page Count in Excerpt**: 100 pages (Original pages: 2–64, 105–141)
   - **Key Content Areas**: Corporate overview ("Delhivery in Numbers"), Management Discussion & Analysis (MDA), Chairperson's letter, operational scale statistics, full audited consolidated financial statements, and segment revenue disclosures.

3. **`03-delhivery-q4-fy24-earnings-presentation.pdf`**
   - **Document Type**: Investor / Earnings Presentation (Q4 & Full Year FY24)
   - **Publication Date**: May 17, 2024
   - **Page Count in Excerpt**: 27 pages (Complete filing)
   - **Key Content Areas**: High-level investor slides, quarter-on-quarter (QoQ) and year-on-year (YoY) operational and financial performance, service line splits, EBITDA bridges, and network asset counts.

---

### Dataset 2: India Macroeconomy Reports
Location: `india-macroeconomy/`

1. **`01-india-economic-survey-2024-25-excerpt.pdf`** (89 pages) - Ministry of Finance, Government of India. Focuses on GDP growth estimates, inflation trends (CPI/WPI), fiscal deficit, and external sector metrics.
2. **`02-rbi-annual-report-2024-25-excerpt.pdf`** (100 pages) - Reserve Bank of India. Focuses on monetary policy, bank credit growth, foreign exchange reserves, and inflation projections.
3. **`03-imf-india-2025-article-iv-excerpt.pdf`** (95 pages) - International Monetary Fund. Multilateral perspective with staff projections, structural reform analysis, and macro-financial risk assessments.

*Architectural note: The Fact Knowledge Layer is designed to be domain-agnostic; its document parser, schema, normalization engine, embedding matcher, and LLM reasoning pipeline seamlessly ingest both corporate filings and macroeconomic reports without code modifications.*

---

## 2. Key Recurring Metrics in the Delhivery Dataset

Across the three Delhivery documents, the following key operational and financial metrics recur:

| Metric Name / Predicate | Description | Common Units Observed | Reporting Periods |
| :--- | :--- | :--- | :--- |
| `revenue_from_services` | Total operating revenue from core service lines | INR Crore (`₹ Cr`), INR Million (`₹ Mn`) | FY19, FY20, FY21, FY22, FY23, FY24, Q4 FY24 |
| `express_parcel_shipments` | Total parcel shipment volume | Million (`Mn`), Absolute count | FY19, FY20, FY21, FY22, FY23, FY24, Q4 FY24, Inception-to-date |
| `ptl_freight_tonnage` | Part-truckload cargo volume delivered | Thousand tonnes (`K tonnes`, `'000 Tons`), Million tonnes (`Mn Tons`) | FY19, FY20, FY21, FY22, FY23, FY24, Inception-to-date |
| `ebitda` | Earnings Before Interest, Tax, Depreciation & Amortization | INR Crore (`₹ Cr`), INR Million (`₹ Mn`) | FY20, FY21, FY22, FY23, FY24, Q4 FY24 |
| `adjusted_ebitda` | EBITDA adjusted for share-based payments and corporate overheads | INR Crore (`₹ Cr`), INR Million (`₹ Mn`) | FY21, FY22, FY23, FY24, Q4 FY24 |
| `ebitda_margin` | EBITDA as a percentage of revenue | Percentage (`%`) | FY23, FY24, Q4 FY24 |
| `net_working_capital_days` | Working capital efficiency cycle | Days | FY20, FY21, FY22, FY23, FY24 |
| `pin_code_reach` | Postal codes serviced by delivery network | Count | As of FY19, FY20, FY21, Dec 31 2021, FY23, FY24 |
| `active_customers` | Transacting customers with invoice raised in period | Count | FY19, FY20, FY21, Q4 FY23, Q4 FY24 |
| `gateways` | Large logistics hubs / sortation nodes | Count | FY19, FY20, FY21, FY23, FY24 |
| `fleet_size_daily_avg` | Average daily operating vehicles in line-haul & last-mile | Count | Q4 FY22, Q4 FY23, Q3 FY24, Q4 FY24 |
| `tractor_trailers_46ft` | Large form-factor 46-foot prime movers | Count | FY24 |

---

## 3. Discovered Candidate Facts from Source Documents

The table below catalogs 15 verified candidate facts directly extracted from the PDF pages:

| # | Subject | Predicate | Raw Value & Unit | Normalized Value & Unit | Period | Source Document | Page | Exact Supporting Evidence Snippet |
| :- | :--- | :--- | :--- | :--- | :--- | :--- | :- | :--- |
| 1 | Delhivery | `revenue_from_services` | ₹81,415 Mn | 81,415 INR Million | FY24 | Annual Report FY24 | 4 | "₹81,415Mn Revenue from services" |
| 2 | Delhivery | `revenue_from_services` | ₹8,142 Cr | 81,420 INR Million | FY24 | Earnings Presentation | 6 | "₹8,142 Cr FY24 revenue from services YoY: 12.7%" |
| 3 | Delhivery | `revenue_from_services` | ₹81,415.38 Mn | 81,415.38 INR Million | FY24 | Annual Report FY24 | 85 | "Revenue from services* 81,415.38 [All amounts in Indian Rupees in million]" |
| 4 | Delhivery | `express_parcel_shipments`| 740 Mn | 740 Million | FY24 | Annual Report FY24 | 4 | "740Mn Express parcels shipped" |
| 5 | Delhivery | `express_parcel_shipments`| 740 Mn | 740 Million | FY24 | Earnings Presentation | 6 | "740 Mn Express parcel shipments in FY24 YoY: 11.5%" |
| 6 | Delhivery | `ptl_freight_tonnage` | 1,429K tonnes | 1,429,000 Tonnes | FY24 | Annual Report FY24 | 4 | "1,429K tonnes PTL freight delivered" |
| 7 | Delhivery | `ptl_freight_tonnage` | 1.4 Mn Tons | 1,400,000 Tonnes | FY24 | Earnings Presentation | 6 | "1.4 Mn Tons PTL freight tonnage in FY24 YoY: 29.8%" |
| 8 | Delhivery | `ptl_freight_tonnage` | 1,429 ('000 Tons) | 1,429,000 Tonnes | FY24 | Earnings Presentation | 9 | "1,429 ('000 Tons) PTL freight tonnage FY24" |
| 9 | Delhivery | `ebitda` | ₹1,266 Mn | 1,266 INR Million | FY24 | Annual Report FY24 | 4 | "₹1,266Mn EBITDA ... 1.6% EBITDA margin" |
| 10 | Delhivery | `ebitda` | ₹127 Cr | 1,270 INR Million | FY24 | Earnings Presentation | 6 | "₹127Cr / 1.6% EBITDA / EBITDA margin" |
| 11 | Delhivery | `adjusted_ebitda` | ₹758 Mn | 758 INR Million | FY24 | Annual Report FY24 | 4 | "₹758Mn Adjusted EBITDA" |
| 12 | Delhivery | `adjusted_ebitda` | ₹76 Cr | 760 INR Million | FY24 | Earnings Presentation | 6 | "₹76Cr / 0.9% Adj. EBITDA / Adj. EBITDA margin" |
| 13 | Delhivery | `net_working_capital_days`| 31 days | 31 Days | FY24 | Annual Report FY24 | 4 | "We significantly reduced our net working capital days to 31 days as of March 2024 from 38 days a year ago" |
| 14 | Delhivery | `pin_code_reach` | 18,793 | 18,793 | As of March 31, 2024 | Annual Report FY24 | 2 | "18,793 Pin codes covered (1) As of March 31, 2024" |
| 15 | Delhivery | `pin_code_reach` | 18,793 | 18,793 | Q4 FY24 | Earnings Presentation | 8 | "Pin-code reach Q4 FY24: 18,793" |
| 16 | Delhivery | `revenue_from_services` | ₹2,076 Cr | 20,760 INR Million | Q4 FY24 | Earnings Presentation | 7 | "₹2,076 Cr Q4 FY24 revenue from services" |
| 17 | Delhivery | `fleet_size_daily_avg` | 15,065 | 15,065 | Q4 FY24 | Annual Report FY24 | 2 | "15,065 Daily average fleet size (3) For the period Q4 FY24" |
| 18 | Delhivery | `tractor_trailers_46ft` | 753 | 753 | End of FY24 | Annual Report FY24 | 8 | "taking the total count to 753 by the end of the year" |
| 19 | Delhivery | `revenue_from_services` | ₹27,748.25 Mn | 27,748.25 INR Million| FY20 | Prospectus 2022 | 45 | "Revenue from Services FY20: 27,748.25 (₹ in million)" |
| 20 | Delhivery | `revenue_from_services` | ₹27,748 Mn | 27,748 INR Million | FY20 | Annual Report FY24 | 6 | "Revenue from services* (₹ million) 27,748 FY20" |

---

## 4. Multi-Document Relationship Analysis & Case Studies

### Case 1: Corroboration (True Cross-Document Agreement across Different Units)
- **Fact A**: Annual Report FY24, Page 4: `Delhivery | revenue_from_services | ₹81,415Mn | FY24`
- **Fact B**: Q4 FY24 Earnings Presentation, Page 6: `Delhivery | revenue_from_services | ₹8,142 Cr | FY24`
- **Mathematical / Unit Grounding**:
  $$1\text{ Crore} = 10\text{ Million}$$
  $$₹8,142\text{ Crore} = ₹81,420\text{ Million}$$
  $$\Delta = |81,420 - 81,415| = 5\text{ Million} \implies \frac{5}{81,415} \approx 0.006\%$$
- **Classification**: **`CORROBORATED`**
- **Human-Readable Explanation**:
  *"Both documents report Delhivery's FY24 revenue from services. The Annual Report provides the precise figure of ₹81,415 million (audited note specifies ₹81,415.38 million), while the Earnings Presentation rounds this to ₹8,142 crore. When converted to a common metric base of INR million, the values differ by less than 0.01%, which is standard financial presentation rounding. The facts corroborate each other."*

- **Secondary Corroboration Example**:
  - `express_parcel_shipments` FY24: Annual Report Page 4 states `740Mn`; Earnings Presentation Page 6 states `740 Mn`. Exact match -> **`CORROBORATED`**.

---

### Case 2: Apparent Contradiction Explained by Context (Not a Real Contradiction)
- **Fact A**: Q4 FY24 Earnings Presentation, Page 7: `Delhivery | revenue_from_services | ₹2,076 Cr | Q4 FY24`
- **Fact B**: Annual Report FY24, Page 4: `Delhivery | revenue_from_services | ₹81,415 Mn | FY24`
- **Surface Appearance**: If evaluated solely on subject (`Delhivery`) and metric (`revenue_from_services`), ₹2,076 Cr (~₹20,760 Mn) is wildly different from ₹81,415 Mn (~74% lower).
- **Contextual Grounding**:
  - Fact A period: `Q4 FY24` (single 3-month quarterly period ending March 31, 2024).
  - Fact B period: `FY24` (full 12-month fiscal year ending March 31, 2024).
- **Classification**: **`CONTEXTUAL`**
- **Human-Readable Explanation**:
  *"While both facts report Delhivery's revenue from services, they correspond to different reporting time windows: Fact A represents quarterly revenue for Q4 FY24 (₹2,076 crore), whereas Fact B represents cumulative annual revenue for the entire FY24 fiscal year (₹81,415 million). This difference is contextual and does not constitute a contradiction."*

- **Secondary Contextual Example**:
  - Express parcels: Cumulative since inception (`>2.8Bn`, Doc 2 Page 2) vs FY24 Annual Volume (`740Mn`, Doc 2 Page 4). Scope: Cumulative vs Single Period.

---

### Case 3: Genuine Contradiction (Controlled Evaluation Case)
- **Background**: Public audited filings by the same listed entity do not publish contradictory figures for identical metrics in the same period without immediate regulatory restatements.
- **Controlled Benchmark Case**:
  - **Fact A (Authentic Document Fact)**: Annual Report FY24, Page 4: `Delhivery | revenue_from_services | ₹81,415 Mn | FY24`
  - **Fact B (Controlled Evaluation Test Fact)**: Independent Equity Research Note / Synthetic Audit: `Delhivery | revenue_from_services | ₹6,500 Cr (₹65,000 Mn) | FY24`
  - **Evaluation Criteria**: Same subject (`Delhivery`), same predicate (`revenue_from_services`), same time period (`FY24`), same unit scale (`INR Million`), but values differ materially by 20.2% ($\Delta = ₹16,415\text{ Mn}$).
- **Classification**: **`CONTRADICTION`**
- **Human-Readable Explanation**:
  *"Both facts claim to report Delhivery's FY24 revenue from services for the full fiscal year, but report irreconcilable values (₹81,415 million vs ₹65,000 million). This discrepancy of over 20% cannot be explained by unit conversion or standard rounding, indicating an authentic contradiction."*

---

### Case 4: Failure / Uncertainty (Unknown / Insufficient Evidence)
- **Fact A**: Annual Report FY24, Page 7 (Letter to Shareholders): `Delhivery | facilities_connected | close to 5,000 | FY24`
  - Evidence: *"drive more than 5 lakh kilometres every day connecting close to 5,000 facilities within our network"*
- **Fact B**: Annual Report FY24, Page 2 ("In Numbers"): `Delhivery | last_mile_centres | 4,445 | As of March 31, 2024`
  - Evidence: *"4,445 Last-mile delivery centres As of March 31, 2024"*
- **Comparison Challenge**: Are "facilities connected" synonymous with "last-mile delivery centres", or does "facilities" also encompass intermediate processing centers, gateways, and partner hubs?
- **Classification**: **`UNKNOWN`** (Insufficient Evidence / Category Ambiguity)
- **Human-Readable Explanation**:
  *"Fact A cites 'close to 5,000 facilities connected within our network' from a high-level shareholder letter, while Fact B specifically counts 4,445 'last-mile delivery centres'. Because the definition and scope of 'facilities' is broader and unspecified in the narrative text, the system cannot verify whether these two metrics describe the same underlying asset pool."*

---

## 5. Architectural Implications for the Fact Knowledge Layer

1. **Deterministic Pre-Filtering**:
   - Currency & Unit Normalization must run *before* mathematical comparison:
     - `Cr` $\to \times 10$ `Mn`
     - `K tonnes` $\to \times 1,000$ `tonnes`
     - `Mn tonnes` $\to \times 1,000,000$ `tonnes`
   - Numeric tolerance threshold: $1.0\%$ relative difference handles rounding discrepancies (such as ₹81,415 Mn vs ₹8,142 Cr).

2. **Period & Temporal Normalization**:
   - Explicit recognition of Quarterly (`Q1`, `Q2`, `Q3`, `Q4`) vs Full Year (`FY2024`, `FY24`, `Fiscal 2024`).
   - Mismatched periods must be routed to `CONTEXTUAL` rather than `CONTRADICTION`.

3. **Scope Sensitivity**:
   - Tracking keywords like `since inception`, `daily average`, `pro forma`, `standalone`, `consolidated`.

4. **Evidence Grounding**:
   - Storing strict bounding metadata (`document_name`, `page_number`, `exact_snippet`) directly in SQLite with foreign keys ensuring zero detached facts.
