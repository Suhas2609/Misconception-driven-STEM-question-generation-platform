FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app/src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data (punkt tokenizer for PDF text processing)
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# Download spaCy language model for advanced NLP analysis
RUN python -m spacy download en_core_web_sm

# Download TextBlob corpora for sentiment/subjectivity analysis
RUN python -m textblob.download_corpora

COPY ./src ./src

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
