# RAG Data Loss Analyzer

A Streamlit app that:

- uploads a CSV
- detects missing data with pandas
- ranks the riskiest fields for sales reporting
- uses a lightweight RAG layer to turn findings into a business summary

## Website URL
https://data-loss-analyzer.streamlit.app

## Run Locally

```bash
streamlit run app.py
```

## Notes

- The app ships with a sample sales dataset if no file is uploaded.
- The summary is based on local retrieval over a small sales-impact knowledge base.
