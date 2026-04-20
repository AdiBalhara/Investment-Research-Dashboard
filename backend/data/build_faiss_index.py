"""
Build a sample FAISS index with financial summaries for ~10 major companies.
Run this script once to generate the index files.

Usage:
    python -m app.research.tools.build_faiss_index
    OR
    python data/build_faiss_index.py
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


# Sample financial documents for major companies
SAMPLE_DOCUMENTS = [
    # Apple
    Document(
        page_content="""Apple Inc. (AAPL) Q4 2024 Financial Summary:
        Revenue: $94.9 billion, up 6% year over year.
        iPhone revenue: $46.2 billion, up 5.5%.
        Services revenue: $25.0 billion, a new all-time record, up 12% YoY.
        Mac revenue: $7.7 billion. iPad revenue: $8.1 billion.
        Net income: $14.7 billion. EPS: $1.64.
        Operating cash flow: $26.8 billion.
        The company returned over $29 billion to shareholders through dividends and share repurchases.
        CEO Tim Cook highlighted strong performance across all product categories and geographic segments.""",
        metadata={"company": "Apple", "ticker": "AAPL", "document_type": "earnings_summary", "period": "Q4 2024"}
    ),
    Document(
        page_content="""Apple Inc. (AAPL) Strategic Overview 2024:
        Apple continues to lead in premium consumer electronics with an ecosystem of hardware, software, and services.
        Key growth drivers: Services segment (App Store, Apple Music, Apple TV+, iCloud) growing at 12% annually.
        Apple Intelligence (AI features) launched across iPhone, iPad, and Mac.
        Vision Pro headset entered the market with mixed initial reception.
        Supply chain diversification continues with increased manufacturing in India and Vietnam.
        R&D spending increased to $31.4 billion annually.
        Market cap consistently above $3 trillion, making it one of the most valuable companies globally.""",
        metadata={"company": "Apple", "ticker": "AAPL", "document_type": "strategic_overview", "period": "2024"}
    ),

    # Microsoft
    Document(
        page_content="""Microsoft Corporation (MSFT) Q2 FY2025 Financial Summary:
        Revenue: $69.6 billion, up 12% year over year.
        Intelligent Cloud segment: $25.5 billion revenue, up 19%. Azure growth at 31%.
        Productivity and Business Processes: $29.4 billion, up 14%.
        More Personal Computing: $14.7 billion, up 2%.
        Net income: $24.1 billion. EPS: $3.23.
        Microsoft Cloud revenue surpassed $40 billion for the quarter.
        AI services contributed an estimated $13 billion annualized run rate.
        Capital expenditures: $22.6 billion, primarily for cloud and AI infrastructure.""",
        metadata={"company": "Microsoft", "ticker": "MSFT", "document_type": "earnings_summary", "period": "Q2 FY2025"}
    ),
    Document(
        page_content="""Microsoft Corporation (MSFT) AI and Cloud Strategy:
        Microsoft is the largest commercial cloud provider with Azure growing over 30% annually.
        Copilot AI assistant integrated across Microsoft 365, GitHub, Dynamics 365, and Windows.
        Strategic partnership with OpenAI, with $13 billion investment.
        GitHub Copilot has over 1.8 million paid subscribers.
        LinkedIn revenue growing at 10% with AI-powered features.
        Gaming segment bolstered by Activision Blizzard acquisition ($69B deal closed 2023).
        Enterprise AI adoption accelerating with Azure AI services.""",
        metadata={"company": "Microsoft", "ticker": "MSFT", "document_type": "strategic_overview", "period": "2024"}
    ),

    # Google (Alphabet)
    Document(
        page_content="""Alphabet Inc. (GOOGL) Q4 2024 Financial Summary:
        Revenue: $96.5 billion, up 12% year over year.
        Google Search & other: $54.0 billion, up 12.5%.
        YouTube ads: $10.5 billion, up 13.8%.
        Google Cloud: $12.0 billion, up 35%. Cloud operating income: $2.2 billion.
        Other Bets revenue: $0.7 billion.
        Net income: $26.5 billion. EPS: $2.12.
        Total employees: approximately 183,000.
        Gemini AI models deployed across Search, Cloud, and consumer products.
        Waymo autonomous driving expanding to more cities.""",
        metadata={"company": "Alphabet", "ticker": "GOOGL", "document_type": "earnings_summary", "period": "Q4 2024"}
    ),

    # Amazon
    Document(
        page_content="""Amazon.com Inc. (AMZN) Q4 2024 Financial Summary:
        Revenue: $187.8 billion, up 10% year over year.
        AWS revenue: $28.8 billion, up 19%. AWS operating income: $10.6 billion.
        North America segment: $115.6 billion revenue.
        International segment: $43.4 billion revenue.
        Net income: $20.0 billion. EPS: $1.86.
        Free cash flow: $38.2 billion (trailing twelve months).
        Advertising revenue: $17.3 billion, up 27%.
        AWS AI services adoption tripled year over year.
        Amazon invested $15.7 billion in capex for cloud infrastructure.""",
        metadata={"company": "Amazon", "ticker": "AMZN", "document_type": "earnings_summary", "period": "Q4 2024"}
    ),

    # Tesla
    Document(
        page_content="""Tesla Inc. (TSLA) Q4 2024 Financial Summary:
        Revenue: $25.7 billion, up 2% year over year.
        Automotive revenue: $21.6 billion. Energy generation and storage: $3.1 billion, up 113%.
        Vehicle deliveries: 495,570 units in Q4. Full year deliveries: 1.79 million (down 1% YoY).
        Gross margin: 17.9%. Automotive gross margin: 16.3%.
        Net income: $2.3 billion. EPS: $0.71.
        Energy storage deployed: 11.0 GWh in Q4.
        FSD (Full Self-Driving) beta expanding. Robotaxi planned for 2025.
        Cybertruck production ramping. New affordable model expected in 2025.""",
        metadata={"company": "Tesla", "ticker": "TSLA", "document_type": "earnings_summary", "period": "Q4 2024"}
    ),
    Document(
        page_content="""Tesla Inc. (TSLA) Risk Analysis:
        Key risks include: intense EV competition from Chinese manufacturers (BYD, NIO) and legacy automakers.
        Margin pressure from price cuts across all models. Average selling price declined 15% over 2 years.
        Regulatory risks around FSD technology and autonomous driving claims.
        Dependence on CEO Elon Musk's leadership and public perception.
        Supply chain risks for lithium, cobalt, and rare earth materials.
        Geopolitical risks with Shanghai Gigafactory (China accounts for ~20% of revenue).
        Energy business provides diversification but is still a small portion of overall revenue.
        Valuation premium relative to traditional automakers remains a debate.""",
        metadata={"company": "Tesla", "ticker": "TSLA", "document_type": "risk_analysis", "period": "2024"}
    ),

    # NVIDIA
    Document(
        page_content="""NVIDIA Corporation (NVDA) Q3 FY2025 Financial Summary:
        Revenue: $35.1 billion, up 94% year over year.
        Data Center revenue: $30.8 billion, up 112%. This segment drives the vast majority of growth.
        Gaming revenue: $3.3 billion, up 15%.
        Gross margin: 74.6%.
        Net income: $19.3 billion. EPS: $0.78.
        H100 and H200 GPU demand remains extremely strong across hyperscalers and enterprises.
        Blackwell architecture GPUs began shipping. Demand significantly exceeds supply.
        AI training and inference workloads driving unprecedented data center buildouts globally.""",
        metadata={"company": "NVIDIA", "ticker": "NVDA", "document_type": "earnings_summary", "period": "Q3 FY2025"}
    ),

    # Meta
    Document(
        page_content="""Meta Platforms Inc. (META) Q4 2024 Financial Summary:
        Revenue: $48.4 billion, up 21% year over year.
        Family of Apps revenue: $47.3 billion. Reality Labs revenue: $1.1 billion.
        Daily Active People (DAP) across family of apps: 3.35 billion.
        Ad impressions grew 6%. Average price per ad increased 14%.
        Net income: $20.8 billion. EPS: $8.02.
        Reality Labs operating loss: $4.97 billion.
        Total capex: $14.8 billion for AI and metaverse infrastructure.
        Llama AI models released as open source, gaining significant developer adoption.
        Threads surpassed 300 million monthly active users.""",
        metadata={"company": "Meta", "ticker": "META", "document_type": "earnings_summary", "period": "Q4 2024"}
    ),

    # JPMorgan Chase
    Document(
        page_content="""JPMorgan Chase & Co. (JPM) Q4 2024 Financial Summary:
        Revenue: $42.8 billion, up 11% year over year.
        Net interest income: $23.5 billion.
        Non-interest revenue: $19.3 billion, up 29%.
        Net income: $14.0 billion. EPS: $4.81.
        Consumer & Community Banking revenue: $18.4 billion.
        Corporate & Investment Bank revenue: $17.5 billion.
        Asset & Wealth Management AUM: $4.0 trillion.
        Return on tangible common equity (ROTCE): 21%.
        Provision for credit losses: $2.6 billion.
        Total assets: $4.0 trillion. Largest US bank by assets.""",
        metadata={"company": "JPMorgan Chase", "ticker": "JPM", "document_type": "earnings_summary", "period": "Q4 2024"}
    ),

    # Johnson & Johnson
    Document(
        page_content="""Johnson & Johnson (JNJ) Q4 2024 Financial Summary:
        Revenue: $22.5 billion, up 5.3% year over year.
        Innovative Medicine segment: $14.3 billion, up 4.4%.
        MedTech segment: $8.2 billion, up 6.7%.
        Top drugs: Darzalex ($3.1B), Stelara ($2.5B), Tremfya ($1.2B).
        Net income: $3.7 billion. Adjusted EPS: $2.31.
        R&D investment: $4.0 billion for the quarter.
        Pipeline includes 30+ Phase 3 programs and pending regulatory submissions.
        Talc litigation remains a significant legal overhang.
        Consumer Health business (Kenvue) fully separated.""",
        metadata={"company": "Johnson & Johnson", "ticker": "JNJ", "document_type": "earnings_summary", "period": "Q4 2024"}
    ),
]


def _get_embeddings():
    jina_api_key = os.environ.get("JINA_API_KEY")
    if jina_api_key:
        from langchain_community.embeddings import JinaEmbeddings

        print("Using Jina embeddings to build the FAISS index...")
        return JinaEmbeddings(
            model_name="jina-embeddings-v2-base-en",
            jina_api_key=jina_api_key,
        )

    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        print("Using Gemini embeddings to build the FAISS index...")
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=gemini_api_key,
        )

    print("ERROR: JINA_API_KEY or GEMINI_API_KEY environment variable is required")
    print("Set one of them in your .env file before building the FAISS index")
    sys.exit(1)


def build_index():
    """Build and save the FAISS index from sample documents."""
    from dotenv import load_dotenv
    load_dotenv()

    print(f"Building FAISS index with {len(SAMPLE_DOCUMENTS)} documents...")

    embeddings = _get_embeddings()

    # Create FAISS index
    db = FAISS.from_documents(SAMPLE_DOCUMENTS, embeddings)

    # Save to disk
    output_dir = os.path.join(os.path.dirname(__file__), "faiss_index")
    os.makedirs(output_dir, exist_ok=True)
    db.save_local(output_dir)

    print(f"FAISS index saved to {output_dir}")
    print(f"  - {len(SAMPLE_DOCUMENTS)} documents indexed")
    print(f"  - Companies: AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, JPM, JNJ")


if __name__ == "__main__":
    build_index()
