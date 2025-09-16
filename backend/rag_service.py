# rag_service.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import ConversationalRetrievalChain

# 1. Cargar documentos
def load_documents():
    loaders = [
        PyPDFLoader("context_docs/calidad1.pdf"),
        PyPDFLoader("context_docs/calidad2.pdf"),

    ]
    docs = []
    for loader in loaders:
        docs.extend(loader.load())
    return docs

# 2. Crear vectorstore
def create_vectorstore():
    docs = load_documents()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = splitter.split_documents(docs)
    embeddings = OpenAIEmbeddings()
    return FAISS.from_documents(texts, embeddings)

vectorstore = create_vectorstore()
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 3. Configurar el modelo + cadena de recuperación
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    retriever=retriever,
    return_source_documents=True
)

# 4. Función de consulta
def ask_question(question, chat_history=[]):
    response = qa_chain.invoke({"question": question, "chat_history": chat_history})
    return response
