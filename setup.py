from setuptools import setup, find_packages

setup(
    name="cv-job-matcher",
    version="0.1.0",
    description="A RAG-based CV to Job Description matching system",
    author="Your Name",
    email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "langchain",
        "transformers",
        "torch",
    ],
    python_requires=">=3.10",
)
