# -*- coding: utf-8 -*-
"""rag-evaluation-llama2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1OHr5YoFkZ_DnLmpeTEMcmNLk5m3wI7y4

## LLM RAG Evaluation with MLflow using llama2-as-judge Example Notebook

In this notebook, we will demonstrate how to evaluate various a RAG system with MLflow. We will use llama2-70b as the judge model, via a Databricks serving endpoint.

<a href="https://raw.githubusercontent.com/mlflow/mlflow/master/docs/source/llms/llm-evaluate/notebooks/rag-evaluation-llama2.ipynb" class="notebook-download-btn"><i class="fas fa-download"></i>Download this Notebook</a>

### Notebook compatibility

With rapidly changing libraries such as `langchain`, examples can become outdated rather quickly and will no longer work. For the purposes of demonstration, here are the critical dependencies that are recommended to use to effectively run this notebook:

| Package             | Version     |
|:--------------------|:------------|
| langchain           | **0.1.16**  |
| lanchain-community  | **0.0.33**  |
| langchain-openai    | **0.0.8**   |
| openai              | **1.12.0**  |
| mlflow              | **2.12.1**  |

If you attempt to execute this notebook with different versions, it may function correctly, but it is recommended to use the precise versions above to ensure that your code executes properly.

#### Installing Requirements

Before proceeding with this tutorial, ensure that your versions of the installed packages meet the requirements listed above.

```bash
    pip install langchain==0.1.16 langchain-community==0.0.33 langchain-openai==0.0.8 openai==1.12.0
```

### Configuration

We need to set our OpenAI API key.

In order to set your private key safely, please be sure to either export your key through a command-line terminal for your current instance, or, for a permanent addition to all user-based sessions, configure your favored environment management configuration file (i.e., .bashrc, .zshrc) to have the following entry:

`OPENAI_API_KEY=<your openai API key>`

In order to run this notebook, using a Databricks hosted Llama2 model, you will need to set your host and personal access token. Please ensure that these are set either using the Databricks SDK ***or*** setting the environment variables:

`DATABRICKS_HOST=<your Databricks workspace URI>`

`DATABRICKS_TOKEN=<your personal access token>`
"""

import pandas as pd
from langchain.chains import RetrievalQA
from langchain.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_openai import OpenAI, OpenAIEmbeddings

import mlflow
from mlflow.deployments import set_deployments_target
from mlflow.metrics.genai import EvaluationExample, faithfulness, relevance

"""Set the deployment target to "databricks" for use with Databricks served models."""

set_deployments_target("databricks")

"""## Create a RAG system

Use Langchain and Chroma to create a RAG system that answers questions based on the MLflow documentation.
"""

loader = WebBaseLoader("https://mlflow.org/docs/latest/index.html")

documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings()
docsearch = Chroma.from_documents(texts, embeddings)

qa = RetrievalQA.from_chain_type(
    llm=OpenAI(temperature=0),
    chain_type="stuff",
    retriever=docsearch.as_retriever(),
    return_source_documents=True,
)

"""## Evaluate the RAG system using `mlflow.evaluate()`

Create a simple function that runs each input through the RAG chain
"""

def model(input_df):
    answer = []
    for index, row in input_df.iterrows():
        answer.append(qa(row["questions"]))

    return answer

"""Create an eval dataset"""

eval_df = pd.DataFrame(
    {
        "questions": [
            "What is MLflow?",
            "How to run mlflow.evaluate()?",
            "How to log_table()?",
            "How to load_table()?",
        ],
    }
)

"""Create a faithfulness metric using `databricks-llama2-70b-chat` as the judge"""

# Create a good and bad example for faithfulness in the context of this problem
faithfulness_examples = [
    EvaluationExample(
        input="How do I disable MLflow autologging?",
        output="mlflow.autolog(disable=True) will disable autologging for all functions. In Databricks, autologging is enabled by default. ",
        score=2,
        justification="The output provides a working solution, using the mlflow.autolog() function that is provided in the context.",
        grading_context={
            "context": "mlflow.autolog(log_input_examples: bool = False, log_model_signatures: bool = True, log_models: bool = True, log_datasets: bool = True, disable: bool = False, exclusive: bool = False, disable_for_unsupported_versions: bool = False, silent: bool = False, extra_tags: Optional[Dict[str, str]] = None) → None[source] Enables (or disables) and configures autologging for all supported integrations. The parameters are passed to any autologging integrations that support them. See the tracking docs for a list of supported autologging integrations. Note that framework-specific configurations set at any point will take precedence over any configurations set by this function."
        },
    ),
    EvaluationExample(
        input="How do I disable MLflow autologging?",
        output="mlflow.autolog(disable=True) will disable autologging for all functions.",
        score=5,
        justification="The output provides a solution that is using the mlflow.autolog() function that is provided in the context.",
        grading_context={
            "context": "mlflow.autolog(log_input_examples: bool = False, log_model_signatures: bool = True, log_models: bool = True, log_datasets: bool = True, disable: bool = False, exclusive: bool = False, disable_for_unsupported_versions: bool = False, silent: bool = False, extra_tags: Optional[Dict[str, str]] = None) → None[source] Enables (or disables) and configures autologging for all supported integrations. The parameters are passed to any autologging integrations that support them. See the tracking docs for a list of supported autologging integrations. Note that framework-specific configurations set at any point will take precedence over any configurations set by this function."
        },
    ),
]

faithfulness_metric = faithfulness(
    model="endpoints:/databricks-llama-2-70b-chat", examples=faithfulness_examples
)
print(faithfulness_metric)

"""Create a relevance metric using `databricks-llama2-70b-chat` as the judge"""

relevance_metric = relevance(model="endpoints:/databricks-llama-2-70b-chat")
print(relevance_metric)

results = mlflow.evaluate(
    model,
    eval_df,
    model_type="question-answering",
    evaluators="default",
    predictions="result",
    extra_metrics=[faithfulness_metric, relevance_metric, mlflow.metrics.latency()],
    evaluator_config={
        "col_mapping": {
            "inputs": "questions",
            "context": "source_documents",
        }
    },
)
print(results.metrics)

results.tables["eval_results_table"]