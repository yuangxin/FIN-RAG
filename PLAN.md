# Financial Agentic RAG 简化实施计划

## Context

当前项目（FinSight）是一个功能完整但过于庞大的金融文档问答系统，包含React前端、FastAPI后端、Pathway向量存储、多LLM路由等。用户需要将其简化为适合放入简历的精简版本，**保留RAG核心流程不变**，只替换外部依赖组件。

### 技术选型确认

| 组件 | 当前 | 替换为 |
|------|------|--------|
| 前端 | React + Vite | Streamlit（单文件） |
| 向量数据库 | Pathway（独立服务端口7000） | ChromaDB（嵌入式本地） |
| Embedding | OpenAI ada-002（收费API） | bge-m3（开源免费本地） |
| PDF解析 | OpenParse + GPT-4o-mini（收费） | MinerU（免费开源） |
| LLM | 多模型路由（OpenAI/Anthropic/Mistral） | Qwen 3.5（通义千问） |
| 工作流 | LangGraph核心6节点 | **保持不变** |

---

## 新项目结构

```
financial_rag/
├── app.py                    # Streamlit 前端（聊天+上传）
├── config.py                 # 配置文件（简化版）
├── requirements.txt          # 依赖列表（精简版）
├── .env.example              # 环境变量模板
├── data/                     # 用户上传的PDF文件
├── chroma_db/                # ChromaDB持久化存储（自动生成）
│
├── core/
│   ├── __init__.py
│   ├── llm.py               # Qwen LLM封装（替代 llm/custom_llm.py）
│   ├── embeddings.py         # bge-m3 embedding封装（新增）
│   ├── vector_store.py       # ChromaDB向量存储（替代 retriever.py）
│   ├── document_parser.py    # MinerU文档解析（替代 vector_store.py中的OpenParse）
│   ├── state.py              # LangGraph状态定义（简化自 state.py）
│   └── prompts.py            # Prompt模板（精简自 prompt.py）
│
├── nodes/                    # LangGraph节点（保持核心逻辑）
│   ├── __init__.py
│   ├── query_rewriter.py     # 查询改写（来自 query_refiner.py）
│   ├── document_retriever.py # 文档检索（修改retriever调用方式，保留定量/定性检索策略）
│   ├── document_grader.py    # 文档评分（保持不变）
│   ├── document_reranker.py  # 文档重排（保持不变）
│   ├── answer_generator.py   # 答案生成（来自 answer_generator.py）
│   ├── hallucination_checker.py  # 幻觉检测（保持不变）
│   ├── web_searcher.py       # Web搜索降级（保持不变）
│   ├── metadata.py           # 元数据提取（来自 metadata_extractor.py）
│   ├── quant_qual.py         # 定量/定性分类（来自 quant_qual.py）
│   └── format_metadata.py    # 元数据格式化（来自 format_metadata.py，改用ChromaDB过滤）
│
├── data/
│   └── company_list.txt      # 已知公司名列表（用于元数据匹配）
│
├── tests/                    # 关键检测文件
│   ├── __init__.py
│   ├── test_01_env.py        # 检测1: 环境和依赖是否正确安装
│   ├── test_02_llm.py        # 检测2: Qwen LLM是否可用
│   ├── test_03_embedding.py  # 检测3: bge-m3 embedding是否正常
│   ├── test_04_chromadb.py   # 检测4: ChromaDB存储和检索
│   ├── test_05_parser.py     # 检测5: MinerU PDF解析
│   ├── test_06_metadata.py   # 检测6: 元数据提取和过滤格式转换
│   ├── test_07_workflow.py    # 检测7: LangGraph工作流编译
│   └── test_08_e2e.py        # 检测8: 端到端完整RAG流程
│
├── edges/                    # LangGraph边/路由逻辑
│   ├── __init__.py
│   ├── assess_metadata.py    # 元数据过滤评估
│   ├── assess_documents.py   # 文档充分性评估
│   ├── assess_hallucination.py  # 幻觉检测结果路由
│   └── assess_answer.py      # 答案质量评估
│
└── workflows/
    ├── __init__.py
    └── rag_e2e.py            # LangGraph RAG工作流（核心，保持不变）
```

---

## 实施步骤

### Step 1: 创建新项目骨架

创建 `financial_rag/` 目录及上述所有文件/文件夹结构。

**关键文件**: 新建所有目录和 `__init__.py`

### Step 2: 配置文件 `config.py`

从原 `pathway_server/config.py` 精简，只保留核心配置：

```python
# 需要保留的配置项：
NUM_DOCS_TO_RETRIEVE = 5
NUM_PREV_MESSAGES = 5
DOCS_RELEVANCE_THRESHOLD = 1
MAX_DOC_GRADING_RETRIES = 2
MAX_METADATA_FILTERING_RETRIES = 2
MAX_HALLUCINATION_RETRIES = 1
MAX_ANSWER_GENERATION_RETRIES = 1
METADATA_FILTER_INIT = ["company_name", "year"]
MAX_RETRIES = 3

WORKFLOW_SETTINGS = {
    "metadata_filtering": True,
    "assess_metadata_filters": True,
    "reranking": False,
    "grade_documents": True,
    "assess_graded_documents": True,
    "rewrite_with_hyde": False,
    "check_hallucination": True,
    "hallucination_checker": "llm",
    "grade_answer": True,
    "grade_web_answer": True,
    "calculator": False,
    "vision": False,
    "follow_up_questions": False,
    "semantic_cache": False,
    "check_safety": False,
    "query_expansion": False,
}

GLOBAL_SET_OF_FINANCE_TERMS = {...}  # 保留原有的金融术语集合
```

**删除的配置**: Pathway服务器地址、多服务器端口、缓存服务器、多LLM重试、日志服务器地址等

### Step 3: LLM封装 `core/llm.py`

替换原来的 `llm/custom_llm.py`（多模型路由），改为只用Qwen：

```python
from langchain_community.chat_models import ChatTongyi  # 或 ChatOpenAI 兼容接口
import os

class LLM:
    """简化的单模型LLM封装"""
    def __init__(self):
        self.llm = ChatTongyi(
            model="qwen-plus",  # 或 qwen-max
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        )

    def invoke(self, input, config=None, **kwargs):
        return self.llm.invoke(input, config, **kwargs)

    def with_structured_output(self, schema, **kwargs):
        return self.llm.with_structured_output(schema, **kwargs)

llm = LLM()
```

**关键变更**: 删除多模型路由、故障切换、错误模拟等逻辑
**注意**: 需要保持与原 `LLM` 类相同的 `invoke()` 和 `with_structured_output()` 接口，这样所有节点代码不用改

### Step 4: Embedding封装 `core/embeddings.py`

新增文件，封装 bge-m3：

```python
from langchain_community.embeddings import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    # 自动下载到本地缓存，之后无需联网
)
```

**关键**: 所有需要embedding的地方统一使用此模型

### Step 5: 文档解析 `core/document_parser.py`

用MinerU替代OpenParse，保持输出格式一致：

```python
import magic_pdf.data.data_reader_writer as drw
from magic_pdf.pipe.UNIPipe import UNIPipe

def parse_pdf(pdf_path: str) -> list[dict]:
    """解析PDF，返回文档块列表（格式与原OpenParse输出一致）"""
    # 使用MinerU解析
    # 输出格式: [{"text": "...", "metadata": {"company_name": "...", "year": "...", "page": 1}}, ...]
    ...

def extract_metadata_from_question(question: str, llm) -> dict:
    """从用户问题中提取公司名和年份（保留原逻辑）"""
    ...
```

**关键**: 输出格式必须与原 `CustomOpenParse.__wrapped__` 的返回格式一致，即 `(text, metadata_dict)` 的列表

### Step 6: 向量存储 `core/vector_store.py`

用ChromaDB替代Pathway，保持 `similarity_search` 接口：

```python
import chromadb
from langchain_community.vectorstores import Chroma
from core.embeddings import embedding_model

class VectorStore:
    def __init__(self, persist_directory="./chroma_db"):
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding_model,
        )

    def add_documents(self, texts, metadatas, ids):
        """添加文档到向量库"""
        self.vectorstore.add_texts(texts, metadatas=metadatas, ids=ids)

    def similarity_search(self, query, k=5, metadata_filter=None):
        """语义搜索（与原retriever接口一致）"""
        # 将原jmespath格式的filter转为ChromaDB的where条件
        chroma_filter = self._convert_filter(metadata_filter)
        return self.vectorstore.similarity_search(query, k=k, filter=chroma_filter)

    def _convert_filter(self, metadata_filter):
        """将原jmespath元数据过滤转为ChromaDB where格式"""
        ...

retriever = VectorStore()  # 全局实例，与原 retriever.py 用法一致
```

**关键**:
- `similarity_search()` 接口必须保持与原 `PathwayVectorStoreClient` 一致
- 需要实现 `_convert_filter()` 将原项目的jmespath格式过滤条件转为ChromaDB的 `where` 格式
- 原项目中元数据过滤格式为 `company_name == 'apple' && year == '2023'` 这种jmespath字符串，需要解析并转换

### Step 7: 状态定义 `core/state.py`

从原 `state.py` 精简，只保留核心RAG所需的状态：

- **保留**: `InternalRAGState`（核心RAG工作流状态）
- **删除**: `OverallState`（上层路由状态）、`KPIState`、`PersonaState`、`VisualizerState`、图表相关模型、QuestionNode/QuestionDecomposer等
- **简化**: `InternalRAGState` 中删除 `cache_output`、`send_log_tree_logs` 等非核心字段

### Step 8: Prompts `core/prompts.py`

从原 `prompt.py` 精简，只保留6个核心节点+Web搜索所需的prompt模板：

需要保留的prompt：
- 查询改写prompt（`rewrite_question` / `rewrite_with_hyde`）
- 元数据提取prompt（`extract_metadata`）
- 文档评分prompt（`grade_documents`）
- 答案生成prompt（`generate_answer_with_citation`）
- 幻觉检测prompt（`check_hallucination`）
- 答案评分prompt（`grade_answer`）
- Web搜索相关prompt

### Step 9: LangGraph节点迁移 `nodes/`

从原 `pathway_server/nodes/` 复制并调整以下文件：

| 原文件 | 新文件 | 改动 |
|--------|--------|------|
| `query_refiner.py` | `query_rewriter.py` | import路径改为 `core.*`，删除日志相关 |
| `document_retriever.py` | `document_retriever.py` | `from retriever import retriever` → `from core.vector_store import retriever`；删除jmespath相关，改用ChromaDB过滤 |
| `document_grader.py` | `document_grader.py` | import路径改为 `core.*`，删除日志 |
| `document_reranker.py` | `document_reranker.py` | import路径改为 `core.*`，删除日志 |
| `answer_generator.py` | `answer_generator.py` | import路径改为 `core.*`，删除日志 |
| `hallucination_checker.py` | `hallucination_checker.py` | import路径改为 `core.*`，删除日志 |
| `web_searcher.py` | `web_searcher.py` | import路径改为 `core.*`，删除日志 |
| `extract_metadata` (在document_retriever中) | `metadata.py` | 提取为独立文件 |

**关键改动模式**（适用于所有节点文件）:
1. `import state` → `from core.state import InternalRAGState`
2. `import config` → `from core.config import *`
3. `from llm import llm` → `from core.llm import llm`
4. `from retriever import retriever` → `from core.vector_store import retriever`
5. `from utils import log_message, send_logs` → 删除或替换为简单 `print`
6. `from nodes import convert_metadata_to_jmespath` → 用ChromaDB过滤格式替代
7. `from prompt import prompts` → `from core.prompts import prompts`

**特别注意**: `document_retriever.py` 中的 `convert_metadata_to_jmespath` 和 `retrieve_documents_with_metadata` 函数需要重写元数据过滤逻辑，从jmespath格式转为ChromaDB的where字典格式

### Step 10: LangGraph边迁移 `edges/`

从原 `pathway_server/edges/` 复制并调整路由逻辑：

需要保留的边：
- `assess_metadata_filter` - 检索结果评估
- `assess_graded_documents` - 文档评分后路由
- `assess_hallucination` - 幻觉检测后路由
- `assess_answer` - 答案评估路由

**改动**: import路径更新，删除日志相关代码

### Step 11: 工作流 `workflows/rag_e2e.py`

从原 `pathway_server/workflows/rag_e2e.py` 复制，这是**核心文件**：

**改动**:
- import路径更新（`import state, nodes, edges` → 从 `core.*` 和相对导入）
- 删除 `semantic_cache`、`vision`、`calculator`、`with_site_blocker` 相关的节点和边
- 保留核心流程: query_rewriter → extract_metadata → retriever → grade_documents → rerank → generate_answer → hallucination_check → grade_answer → END
- 保留 web_search 降级路径

**核心流程图（保持不变）**:
```
START → query_rewriter → extract_metadata → retriever
    → (assess_metadata_filter) → grade_documents → (assess_graded_documents)
    → rerank_documents → generate_answer → hallucination_checker
    → (assess_hallucination) → grade_answer → (assess_answer) → END
                                                            ↓ 失败
                                                      query_rewriter (重试)
                                                            ↓ 重试耗尽
                                                        search_web → END
```

### Step 12: Streamlit前端 `app.py`

创建单文件Streamlit界面：

```python
import streamlit as st
from core.document_parser import parse_pdf
from core.vector_store import retriever
from workflows.rag_e2e import rag_e2e

# 页面配置
st.set_page_config(page_title="FinRAG - 金融文档问答", layout="wide")
st.title("FinRAG - 金融文档智能问答系统")

# 侧边栏：文件上传
with st.sidebar:
    uploaded_files = st.file_uploader("上传金融文档(PDF)", type=["pdf"], accept_multiple_files=True)
    if uploaded_files:
        # 解析并入库
        for file in uploaded_files:
            chunks = parse_pdf(file)
            retriever.add_documents(chunks)

# 主区域：聊天界面
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("输入你的问题..."):
    st.chat_message("user").write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("正在分析..."):
            result = rag_e2e.invoke({"question": prompt})
            answer = result.get("answer", "无法生成回答")
            st.write(answer)
            # 显示引用来源
            if result.get("citations"):
                st.write("---")
                st.write("**参考来源:**")
                for cite in result["citations"]:
                    st.write(f"- {cite}")
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": answer})
```

### Step 13: 依赖文件 `requirements.txt`

```
streamlit
langchain
langchain-community
langchain-core
langgraph
chromadb
sentence-transformers  # bge-m3
magic-pdf[full]        # MinerU
dashscope              # Qwen API
langchain-community    # ChatTongyi
tavily-python          # Web搜索
python-dotenv
```

### Step 14: 环境变量 `.env.example`

```
# Qwen API（阿里云百炼平台）
DASHSCOPE_API_KEY=your_key_here

# Web搜索（可选）
TAVILY_API_KEY=your_key_here
```

---

## 检测文件设计

每个检测文件可独立运行（`pytest tests/test_0X_xxx.py` 或 `python tests/test_0X_xxx.py`），按顺序验证。

### test_01_env.py — 环境检测
```python
"""检测所有依赖是否正确安装"""
def test_imports():
    import streamlit
    import langchain
    import langgraph
    import chromadb
    from langchain_community.chat_models import ChatTongyi
    from langchain_community.embeddings import HuggingFaceEmbeddings
    print("所有依赖导入成功")

def test_env_vars():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    assert os.getenv("DASHSCOPE_API_KEY"), "DASHSCOPE_API_KEY 未设置"
    print("环境变量检测通过")
```

### test_02_llm.py — LLM可用性检测
```python
"""检测Qwen LLM是否正常响应"""
def test_llm_invoke():
    from core.llm import llm
    response = llm.invoke("你好，请说OK")
    assert response.content, "LLM返回为空"
    print(f"LLM响应: {response.content[:50]}")

def test_llm_structured_output():
    from core.llm import llm
    from pydantic import BaseModel
    class TestSchema(BaseModel):
        answer: str
    structured_llm = llm.with_structured_output(TestSchema)
    result = structured_llm.invoke("1+1等于几？")
    assert result.answer, "结构化输出失败"
    print(f"结构化输出: {result}")
```

### test_03_embedding.py — Embedding检测
```python
"""检测bge-m3模型是否正常工作"""
def test_embedding():
    from core.embeddings import embedding_model
    vec = embedding_model.embed_query("苹果公司2023年营收")
    assert len(vec) > 0, "Embedding返回为空"
    assert len(vec) == 1024, f"向量维度不对: 期望1024, 实际{len(vec)}"
    print(f"Embedding维度: {len(vec)}")

def test_embedding_similarity():
    from core.embeddings import embedding_model
    import numpy as np
    vec1 = embedding_model.embed_query("苹果公司营收增长")
    vec2 = embedding_model.embed_query("Apple revenue increased")
    vec3 = embedding_model.embed_query("今天天气真好")
    sim_12 = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    sim_13 = np.dot(vec1, vec3) / (np.linalg.norm(vec1) * np.linalg.norm(vec3))
    assert sim_12 > sim_13, "语义相似度计算不对"
    print(f"相关句相似度: {sim_12:.3f}, 无关句相似度: {sim_13:.3f}")
```

### test_04_chromadb.py — 向量存储检测
```python
"""检测ChromaDB存储、检索、过滤功能"""
def test_add_and_search():
    from core.vector_store import retriever
    # 添加测试文档
    retriever.add_documents(
        texts=["苹果公司2023年营收为3832亿美元"],
        metadatas=[{"company_name": "apple", "year": "2023"}],
        ids=["test_doc_1"]
    )
    # 检索
    results = retriever.similarity_search("苹果2023年营收", k=1)
    assert len(results) > 0, "检索结果为空"
    print(f"检索到: {results[0].page_content[:50]}")

def test_metadata_filter():
    from core.vector_store import retriever
    # 带元数据过滤的检索
    results = retriever.similarity_search(
        "营收", k=1,
        metadata_filter={"company_name": "apple", "year": "2023"}
    )
    assert len(results) > 0, "带过滤的检索结果为空"
    print(f"过滤检索到: {results[0].page_content[:50]}")

    # 用不匹配的过滤条件应返回空
    results_empty = retriever.similarity_search(
        "营收", k=1,
        metadata_filter={"company_name": "nonexistent_company"}
    )
    print(f"不匹配过滤结果数量: {len(results_empty)}")
```

### test_05_parser.py — PDF解析检测
```python
"""检测MinerU是否能正确解析PDF并提取元数据"""
def test_parse_pdf():
    from core.document_parser import parse_pdf
    # 需要一个测试PDF文件
    chunks = parse_pdf("data/sample_report.pdf")
    assert len(chunks) > 0, "解析结果为空"
    # 检查输出格式
    first = chunks[0]
    assert "text" in first, "缺少text字段"
    assert "metadata" in first, "缺少metadata字段"
    meta = first["metadata"]
    assert "company_name" in meta, "缺少company_name"
    assert "year" in meta, "缺少year"
    print(f"解析出 {len(chunks)} 个文档块")
    print(f"公司: {meta['company_name']}, 年份: {meta['year']}")
```

### test_06_metadata.py — 元数据过滤检测
```python
"""检测元数据格式转换是否正确"""
def test_chroma_filter_conversion():
    from nodes.format_metadata import convert_to_chroma_filter
    # 测试单个条件
    f1 = convert_to_chroma_filter({"company_name": "apple", "year": "2023"})
    assert f1 == {"company_name": "apple", "year": "2023"}
    print(f"基础过滤: {f1}")

    # 测试None值处理
    f2 = convert_to_chroma_filter({"company_name": None, "year": "2023"})
    assert "company_name" not in f2
    print(f"None过滤: {f2}")

    # 测试空输入
    f3 = convert_to_chroma_filter({})
    assert f3 is None or f3 == {}
    print(f"空过滤: {f3}")
```

### test_07_workflow.py — 工作流编译检测
```python
"""检测LangGraph工作流是否能正确编译"""
def test_workflow_compiles():
    from workflows.rag_e2e import rag_e2e
    assert rag_e2e is not None, "工作流编译失败"
    print("工作流编译成功")

    # 检查图的节点
    nodes = rag_e2e.get_graph().nodes
    required_nodes = [
        "query_rewriter", "extract_metadata", "retriever",
        "grade_documents", "generate_answer_with_citation_state",
        "hallucination_checker", "grade_answer", "search_web"
    ]
    for node in required_nodes:
        assert node in nodes, f"缺少节点: {node}"
    print(f"所有 {len(required_nodes)} 个核心节点存在")
```

### test_08_e2e.py — 端到端检测
```python
"""端到端完整RAG流程检测（需要先上传文档）"""
def test_e2e_with_docs():
    from workflows.rag_e2e import rag_e2e
    result = rag_e2e.invoke({
        "question": "苹果公司2023年营收是多少？"
    })
    assert "answer" in result, "缺少answer字段"
    assert len(result["answer"]) > 0, "答案为空"
    print(f"答案: {result['answer'][:200]}")
    print(f"引用: {result.get('citations', [])}")

def test_e2e_web_fallback():
    """测试Web搜索降级"""
    from workflows.rag_e2e import rag_e2e
    result = rag_e2e.invoke({
        "question": "今天上证指数收盘价是多少？"
    })
    assert "answer" in result
    print(f"Web搜索答案: {result['answer'][:200]}")
```

### 检测运行顺序

```bash
# 逐步检测，哪步失败就修哪步
pytest tests/test_01_env.py -v        # 第一步：环境
pytest tests/test_02_llm.py -v        # 第二步：LLM
pytest tests/test_03_embedding.py -v  # 第三步：Embedding
pytest tests/test_04_chromadb.py -v   # 第四步：向量存储
pytest tests/test_05_parser.py -v     # 第五步：PDF解析（需要测试PDF文件）
pytest tests/test_06_metadata.py -v   # 第六步：元数据格式
pytest tests/test_07_workflow.py -v   # 第七步：工作流编译
pytest tests/test_08_e2e.py -v        # 第八步：端到端（需要先上传文档）

# 或一次全部运行
pytest tests/ -v
```

---

## 关键风险与注意事项

### 1. 元数据过滤格式转换（最大风险）

原项目使用 **jmespath** 格式过滤：
```python
# 原格式
"company_name == 'apple' && year == '2023'"
```

ChromaDB使用 **字典** 格式过滤：
```python
# 新格式
{"company_name": "apple", "year": "2023"}
# 或者
{"$and": [{"company_name": "apple"}, {"year": "2023"}]}
```

需要重写 `convert_metadata_to_jmespath` → `convert_to_chroma_filter`，以及所有调用该函数的地方。

### 2. 检索接口一致性

原 `retriever.similarity_search(query, k, metadata_filter=jmespath_str)` →
新 `retriever.similarity_search(query, k, metadata_filter=dict_or_none)`

所有调用 `retriever.similarity_search` 的地方都需要适配。

### 3. LLM接口兼容性

原 `LLM` 类继承自 `BaseChatModel`，有自定义的 `invoke` 和 `with_structured_output`。
新的Qwen封装也需要保持同样的接口签名，否则所有使用 `llm.invoke()` 和 `llm.with_structured_output()` 的节点都会报错。

### 4. MinerU输出格式

需要确保MinerU解析后的文档块格式与原OpenParse一致：
```python
# 需要保持的格式
{
    "text": "文档内容...",
    "metadata": {
        "company_name": "apple",
        "year": "2023",
        "page_no": 1,
        "variant": "title"
    }
}
```

---

## 验证计划

每个实施步骤完成后立即运行对应的检测文件验证：

| 完成步骤 | 运行检测 | 验证内容 |
|---------|---------|---------|
| Step 1-2 (骨架+配置) | `test_01_env.py` | 依赖导入、环境变量 |
| Step 3 (LLM) | `test_02_llm.py` | Qwen响应、结构化输出 |
| Step 4 (Embedding) | `test_03_embedding.py` | bge-m3向量维度、语义相似度 |
| Step 5-6 (解析+向量存储) | `test_04_chromadb.py` + `test_05_parser.py` | 存储、检索、过滤、PDF解析 |
| Step 7-10 (状态+Prompts+节点+边) | `test_06_metadata.py` | 元数据格式转换 |
| Step 11 (工作流) | `test_07_workflow.py` | 工作流编译、节点完整性 |
| Step 12 (前端) | `test_08_e2e.py` | 端到端完整问答 |

**启动命令**: `streamlit run app.py`
