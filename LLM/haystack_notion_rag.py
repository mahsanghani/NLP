# -*- coding: utf-8 -*-
"""Haystack_Notion_RAG.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1vfiYyJQgey5zR1TSjG-_NL6yZspI1eCO

# Build a Custom Retrieval-Augmented Pipeline on Your Private Notion Pages
_by Tuana Celik ([Twitter](https://twitter.com/tuanacelik), [LinkedIn](https://www.linkedin.com/in/tuanacelik/))_

In this Colab, we will:
- Creating a custom Haystack component called `NotionExporter`
- Building an indexing pipeline to write our Notion pages into an `InMemoryDocumentStore` with embeddings
- Build a custom RAG pipeline to do question answering on our Notion pages
"""

!pip install haystack-ai cohere-haystack transformers sentence_transformers
!pip install notion-exporter
!pip install python-frontmatter
!pip install nest-asyncio

import nest_asyncio

nest_asyncio.apply()

"""## Build a custom NotionExporter component

Documentation on [Custom Components](https://docs.haystack.deepset.ai/v2.0/docs/custom-components)
"""

from typing import List
from notion_exporter import NotionExporter as _NotionExporter
import frontmatter
from haystack import component
from haystack.dataclasses import Document

@component
class NotionExporter():

    def __init__(self, api_token: str,):
        self.notion_exporter = _NotionExporter(
            notion_token=api_token,
        )

    @component.output_types(documents=List[Document])
    def run(self, page_ids: List[str]):
        extracted_pages = self.notion_exporter.export_pages(page_ids)

        documents = []
        for page_id, page in extracted_pages.items():
            metadata, markdown_text = frontmatter.parse(page)
            document = Document(content=markdown_text)
            documents.append(document)

        return {"documents": documents}

import getpass
import os

notion_api_key = getpass.getpass("Enter Notion API key:")
cohere_api_key = getpass.getpass("Cohere API key:")

"""### Test our custom NotionExporter component

- You can follow the steps outlined in the Notion [documentation](https://developers.notion.com/docs/create-a-notion-integration#create-your-integration-in-notion) to create a new Notion integration, connect it to your pages, and obtain your API token.
- Page IDs in Notion are the tailing numbers at the end of the page URL, separated by a '-' at 8-4-4-4-12 digits
"""

exporter = NotionExporter(api_token=notion_api_key)

exporter.run(page_ids=["6f98e9a6-a880-40e9-b191-1c4f41efec87"])

"""## Build an Indexing Pipeline to Write Notion Pages to a Document Store

- Documentation on [`SentenceTransformersDocumentEmbedder`](https://docs.haystack.deepset.ai/v2.0/docs/sentencetransformersdocumentembedder)
- Documentation on [`DocumentSplitter`](https://docs.haystack.deepset.ai/v2.0/docs/documentsplitter)
- Documentation on [`DocumentWriter`](https://docs.haystack.deepset.ai/v2.0/docs/documentwriter)
"""

from haystack.components.preprocessors import DocumentSplitter
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.writers import DocumentWriter
from haystack.document_stores import InMemoryDocumentStore


document_store = InMemoryDocumentStore()
exporter = NotionExporter(api_token=notion_api_key)
splitter = DocumentSplitter()
document_embedder = SentenceTransformersDocumentEmbedder()
writer = DocumentWriter(document_store=document_store)

from haystack import Pipeline

indexing_pipeline = Pipeline()
indexing_pipeline.add_component(instance=exporter, name="exporter")
indexing_pipeline.add_component(instance=splitter, name="splitter")
indexing_pipeline.add_component(instance=document_embedder, name="document_embedder")
indexing_pipeline.add_component(instance=writer, name="writer")

indexing_pipeline.connect("exporter.documents", "splitter.documents")
indexing_pipeline.connect("splitter.documents", "document_embedder.documents")
indexing_pipeline.connect("document_embedder.documents", "writer.documents")

indexing_pipeline.run(data={"exporter":{"page_ids": ["6f98e9a6-a880-40e9-b191-1c4f41efec87"]}})

"""## Build a RAG Pipeline with Cohere

- Documentation on [`SentenceTransformersTextEmbedder`](https://docs.haystack.deepset.ai/v2.0/docs/sentencetransformerstextembedder)
- Documentation on [`PromptBuilder`](https://docs.haystack.deepset.ai/v2.0/docs/promptbuilder)
- Documentation on [`CohereGenerator`](https://docs.haystack.deepset.ai/v2.0/docs/coheregenerator)
"""

import torch

from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.retrievers import InMemoryEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from cohere_haystack.generator import CohereGenerator

prompt = """ Answer the query, based on the
content in the documents.

Documents:
{% for doc in documents %}
  {{doc.content}}
{% endfor %}

Query: {{query}}
"""
text_embedder = SentenceTransformersTextEmbedder()
retriever = InMemoryEmbeddingRetriever(document_store=document_store)
prompt_builder = PromptBuilder(template=prompt)
generator = CohereGenerator(api_key=cohere_api_key)

rag_pipeline = Pipeline()

rag_pipeline.add_component(instance=text_embedder, name="text_embedder")
rag_pipeline.add_component(instance=retriever, name="retriever")
rag_pipeline.add_component(instance=prompt_builder, name="prompt_builder")
rag_pipeline.add_component(instance=generator, name="generator")

rag_pipeline.connect("text_embedder", "retriever")
rag_pipeline.connect("retriever.documents", "prompt_builder.documents")
rag_pipeline.connect("prompt_builder", "generator")

question = "What are the steps for creating a custom component?"
result = rag_pipeline.run(data={"text_embedder":{"text": question},
                       "prompt_builder":{"query": question}})

print(result['generator']['replies'][0])