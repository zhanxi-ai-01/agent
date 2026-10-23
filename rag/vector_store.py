# rag/vector_store.py
import sys
import os
import glob  # ⭐⭐⭐ 修改点 1：新增 glob 用于遍历文件夹

# 👇 这三行是核心修复：把项目根目录加入 Python 的搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hashlib
from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from pymilvus import MilvusClient
from config.settings import DASHSCOPE_API_KEY

load_dotenv(override=True)

# --- 配置区 ---
#MILVUS_URI = "http://localhost:19530"
MILVUS_URI = os.getenv("ZILLIZ_URI")
ZILLIZ_TOKEN = os.getenv("ZILLIZ_TOKEN")


DB_NAME = "rag_tutorial"
COLLECTION_NAME = "docs"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

# ⭐⭐⭐ 修改点 2：路径指向新建的文件夹，而不是单个文件
SOURCE_DOCS_DIR = os.path.join(PROJECT_ROOT, "data", "source_documents")

# 阿里云（即千问平台） Embedding 配置
EMBED_MODEL_NAME = "text-embedding-v1"
EMBED_DIM = 1536  # 重要：阿里云这个模型的维度是 1536，不是 3072

# ============ 全局单例 ============
_client = None
_embedding_model = None


def _init_embedding():
    global _embedding_model
    if _embedding_model is None:
        # 改用阿里云 DashScope
        _embedding_model = DashScopeEmbeddings(
            model=EMBED_MODEL_NAME,
            dashscope_api_key=DASHSCOPE_API_KEY
        )
    return _embedding_model


def _init_client():
    global _client
    if _client is None:
        #10月23日添加👇
        _client = MilvusClient(uri=MILVUS_URI, token=ZILLIZ_TOKEN)
        # 10月23日注释👇
        #_client = MilvusClient(MILVUS_URI)
        # existed = _client.list_databases()
        # if DB_NAME not in existed:
        #     _client.create_database(db_name=DB_NAME)
        # _client.use_database(db_name=DB_NAME)
    return _client


def build_knowledge_base(force_rebuild: bool = False):
    """建库：切分 + 向量化 + 写入 Milvus。force_rebuild=True 时重建。"""
    client = _init_client()

    if client.has_collection(COLLECTION_NAME):
        if not force_rebuild:
            print(f"集合 {COLLECTION_NAME} 已存在，跳过重建。")
            return
        client.drop_collection(collection_name=COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        dimension=EMBED_DIM,
        metric_type="COSINE",
    )

    embedding_model = _init_embedding()

    # ⭐⭐⭐ 修改点 3：改为遍历文件夹加载多个 Word 文件
    if not os.path.exists(SOURCE_DOCS_DIR):
        print(f"❌ 找不到知识库文件夹: {SOURCE_DOCS_DIR}，请创建并放入 docx 文件")
        return

    # 获取文件夹下所有的 .docx 文件
    docx_files = glob.glob(os.path.join(SOURCE_DOCS_DIR, "*.docx"))
    if not docx_files:
        print(f"❌ 在 {SOURCE_DOCS_DIR} 下没有找到任何 .docx 文件")
        return

    documents = []
    for file_path in docx_files:
        print(f"正在加载知识库文件: {os.path.basename(file_path)}")
        loader = Docx2txtLoader(file_path)
        docs = loader.load()

        # 动态注入元数据（保留你原有的逻辑）
        for doc in docs:
            file_name = os.path.basename(doc.metadata.get('source', 'unknown'))
            doc.metadata['source'] = file_name
            doc.metadata['chapter'] = file_name.replace('.docx', '')
            documents.append(doc)

    print(f"✅ 所有文档加载完毕，共 {len(documents)} 个原始文档片段")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=["\n█", "\n□□□", "\n【", "\n\n\n", "\n\n", "。", "！", "？", "\n", "，", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"文档共切分为 {len(chunks)} 个 chunk")

    text = [c.page_content for c in chunks]

    # 分批向量化 (保留你原有的逻辑)
    print("开始向量化，请耐心等待...")
    vectors = []
    batch_size = 100
    for i in range(0, len(text), batch_size):
        batch_text = text[i:i + batch_size]
        batch_vectors = embedding_model.embed_documents(batch_text)
        vectors.extend(batch_vectors)
        print(f"已完成向量化 {min(i + batch_size, len(text))}/{len(text)} 条")

    # 使用稳定的 Hash ID (保留你原有的逻辑)
    data = []
    for i, chunk in enumerate(chunks):
        content_hash = hashlib.md5(chunk.page_content.encode('utf-8')).hexdigest()
        source_hash = hashlib.md5(chunk.metadata['source'].encode('utf-8')).hexdigest()[:8]
        stable_id = int(hashlib.md5((source_hash + content_hash).encode('utf-8')).hexdigest()[:15], 16)

        data.append({
            "id": stable_id,
            "vector": vectors[i],
            "text": chunk.page_content,
            "source": chunk.metadata['source'],
            "chapter": chunk.metadata.get('chapter', '未知章节'),
        })

    # 分批 Upsert (保留你原有的逻辑)
    for i in range(0, len(data), batch_size):
        client.upsert(collection_name=COLLECTION_NAME, data=data[i:i + batch_size])
        print(f"已写入 {min(i + batch_size, len(data))}/{len(data)} 条数据")

    client.flush(collection_name=COLLECTION_NAME)
    print("知识库构建完成：", client.get_collection_stats(COLLECTION_NAME))


def search_knowledge(query: str, limit: int = 3):
    """检索函数，供工具调用。"""
    client = _init_client()
    embedding_model = _init_embedding()
    query_vector = embedding_model.embed_query(query)

    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_vector],
        limit=limit,
        output_fields=["text", "source", "chapter"],
    )
    return results[0]


if __name__ == "__main__":
    # 这里是你用来测试的代码，不用管
    print("=" * 50)
    print("🚀 开始 Milvus 建库测试")
    print("=" * 50)
    # 记得测试时把 force_rebuild 设置为 True
    build_knowledge_base(force_rebuild=True)



# rag/vector_store.py
# import sys
# import os
# # 👇 这三行是核心修复：把项目根目录加入 Python 的搜索路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#
# import hashlib
# from dotenv import load_dotenv
# from langchain_community.document_loaders import Docx2txtLoader
#
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import DashScopeEmbeddings
# from pymilvus import MilvusClient
# from config.settings import DASHSCOPE_API_KEY
#
# load_dotenv(override=True)
#
# # --- 配置区 ---
# MILVUS_URI = "http://localhost:19530"
# DB_NAME = "rag_tutorial"
# COLLECTION_NAME = "docs"
#
# # 指向你的 Word 文件
# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
# DATA_PATH = os.path.join(PROJECT_ROOT, "data", "詹曦成交心理学.docx")
#
# # 阿里云（即千问平台） Embedding 配置
# # 模型网址https://www.qianwenai.com/models/text-embedding-v1#api-reference  Qwen-Embedding
# EMBED_MODEL_NAME = "text-embedding-v1"
# EMBED_DIM = 1536  # 重要：阿里云这个模型的维度是 1536，不是 3072
#
# # ============ 全局单例 ============
# _client = None
# _embedding_model = None
#
#
# def _init_embedding():
#     global _embedding_model
#     if _embedding_model is None:
#         # 改用阿里云 DashScope
#         _embedding_model = DashScopeEmbeddings(
#             model=EMBED_MODEL_NAME,
#             dashscope_api_key=DASHSCOPE_API_KEY
#         )
#     return _embedding_model
#
#
# def _init_client():
#     global _client
#     if _client is None:
#         _client = MilvusClient(MILVUS_URI)
#         existed = _client.list_databases()
#         if DB_NAME not in existed:
#             _client.create_database(db_name=DB_NAME)
#         _client.use_database(db_name=DB_NAME)
#     return _client
#
#
# def build_knowledge_base(force_rebuild: bool = False):
#     """建库：切分 + 向量化 + 写入 Milvus。force_rebuild=True 时重建。"""
#     client = _init_client()
#
#     if client.has_collection(COLLECTION_NAME):
#         if not force_rebuild:
#             print(f"集合 {COLLECTION_NAME} 已存在，跳过重建。")
#             return
#         client.drop_collection(collection_name=COLLECTION_NAME)
#
#     client.create_collection(
#         collection_name=COLLECTION_NAME,
#         dimension=EMBED_DIM,
#         metric_type="COSINE",
#     )
#
#     embedding_model = _init_embedding()
#
#     # 改为加载单个 Word 文件
#     if not os.path.exists(DATA_PATH):
#         print(f"❌ 找不到知识库文件: {DATA_PATH}")
#         return
#
#     loader = Docx2txtLoader(DATA_PATH)
#     documents = loader.load()
#
#     # 动态注入元数据
#     for doc in documents:
#         file_name = os.path.basename(doc.metadata.get('source', 'unknown'))
#         doc.metadata['source'] = file_name
#         doc.metadata['chapter'] = file_name.replace('.docx', '')
#
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1200,
#         chunk_overlap=200,
#         separators=["\n█", "\n□□□", "\n【", "\n\n\n", "\n\n", "。", "！", "？", "\n", "，", " ", ""],
#     )
#     chunks = splitter.split_documents(documents)
#     print(f"文档共切分为 {len(chunks)} 个 chunk")
#
#     text = [c.page_content for c in chunks]
#
#     # 分批向量化
#     print("开始向量化，请耐心等待...")
#     vectors = []
#     batch_size = 100
#     for i in range(0, len(text), batch_size):
#         batch_text = text[i:i + batch_size]
#         batch_vectors = embedding_model.embed_documents(batch_text)
#         vectors.extend(batch_vectors)
#         print(f"已完成向量化 {min(i + batch_size, len(text))}/{len(text)} 条")
#
#     # 使用稳定的 Hash ID
#     data = []
#     for i, chunk in enumerate(chunks):
#         content_hash = hashlib.md5(chunk.page_content.encode('utf-8')).hexdigest()
#         source_hash = hashlib.md5(chunk.metadata['source'].encode('utf-8')).hexdigest()[:8]
#         stable_id = int(hashlib.md5((source_hash + content_hash).encode('utf-8')).hexdigest()[:15], 16)
#
#         data.append({
#             "id": stable_id,
#             "vector": vectors[i],
#             "text": chunk.page_content,
#             "source": chunk.metadata['source'],
#             "chapter": chunk.metadata.get('chapter', '未知章节'),
#         })
#
#     # 分批 Upsert
#     for i in range(0, len(data), batch_size):
#         client.upsert(collection_name=COLLECTION_NAME, data=data[i:i + batch_size])
#         print(f"已写入 {min(i + batch_size, len(data))}/{len(data)} 条数据")
#
#     client.flush(collection_name=COLLECTION_NAME)
#     print("知识库构建完成：", client.get_collection_stats(COLLECTION_NAME))
#
#
# def search_knowledge(query: str, limit: int = 3):
#     """检索函数，供工具调用。"""
#     client = _init_client()
#     embedding_model = _init_embedding()
#     query_vector = embedding_model.embed_query(query)
#
#     results = client.search(
#         collection_name=COLLECTION_NAME,
#         data=[query_vector],
#         limit=limit,
#         output_fields=["text", "source", "chapter"],
#     )
#     return results[0]
#
#
# # ==================== 兼容旧接口 ====================
# # 为了不让 app.py 报错，保留这个 get_vector_store 接口
#
# # class MilvusWrapper:
# #     def similarity_search(self, query: str, k: int = 3):
# #         results = search_knowledge(query, limit=k)
# #         from langchain_core.documents import Document
# #         docs = []
# #         for res in results:
# #             docs.append(Document(
# #                 page_content=res['entity']['text'],
# #                 metadata={
# #                     "source": res['entity'].get('source', ''),
# #                     "chapter": res['entity'].get('chapter', '')
# #                 }
# #             ))
# #         return docs
# #
# #
# # def get_vector_store():
# #     _init_client()
# #     _init_embedding()
# #     return MilvusWrapper()
# #
# #
# # if __name__ == "__main__":
# #     print("=" * 50)
# #     print("🚀 开始 Milvus 建库测试")
# #     print("=" * 50)
# #     build_knowledge_base(force_rebuild=True)
# #
# #     print("\n" + "=" * 50)
# #     print("🔍 开始模拟检索")
# #     print("=" * 50)
# #     query = "阻碍成交的第一个心理障碍是什么？"
# #     print(f"🙋‍♂️ 用户提问: {query}")
# #     results = search_knowledge(query, limit=3)
# #     for i, res in enumerate(results):
# #         print(f"\n--- 📄 匹配结果 {i + 1} ---")
# #         print(res['entity']['text'][:300] + "...")
# #         print(f"🏷️ 来源: {res['entity'].get('source')}, 章节: {res['entity'].get('chapter')}")