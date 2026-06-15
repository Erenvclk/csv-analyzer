# 📊 CSV Analyzer

A Streamlit web app that lets you ask plain-language questions about any CSV dataset and get instant, accurate answers.

No formulas. No pivot tables. Just upload your data and ask.

## What it does

Upload a CSV file → type a question → get a clear answer based on your data.

**Example questions:**
- "Which product had the highest sales last quarter?"
- "What is the average order value by region?"
- "Are there any customers who placed more than 5 orders?"
- "Which month had the lowest revenue?"

## Tech stack

- **Python 3.11+**
- **Streamlit** — web UI
- **OpenAI API** — GPT-4o-mini for data analysis
- **Pandas** — CSV parsing and preview

## Setup

```bash
git clone https://github.com/Erenvclk/csv-analyzer
cd csv-analyzer
pip install -r requirements.txt
python -m streamlit run app.py
```
 
> **Note:** If `streamlit run app.py` doesn't work, use `python -m streamlit run app.py` instead. This is common on Windows.

## Limits

- Max file size: **200 KB**
- Max question length: **500 characters**
- Supported format: **CSV only**

## Use cases

- Sales teams reviewing monthly performance data
- Operations managers analyzing logistics reports
- Small business owners exploring customer data
- Consultants doing quick data audits for clients

---
Built by Vah
t Eren ÇELİK· [Upwork Profile](https://www.upwork.com/freelancers/~0105366d87793056d2)
