# RAG Data Loss Analyzer (Full Stack)

A Streamlit full-stack app that now includes:

- `Sign Up` and `Sign In` authentication using Supabase Auth
- CSV upload and missing-data analysis with pandas
- RAG-style business impact summary generation
- MongoDB persistence for saved analysis history per user

## Run Locally

```bash
cd data_loss_analyzer
pip install -r requirements.txt
streamlit run app.py

