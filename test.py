import streamlit as st
import pdfplumber
from sentence_transformers import SentenceTransformer
import requests
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
import pinecone

# pip install pdfplumber sentence-transformers firebase-admin pinecone-client  requests

st.title("IBM Granite Hackathon: Workflow Agent")
st.write("Author: Parin Acharya")

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# module for setting up and interacting with Firebase firestore and Pinecone
# Load Firebase credentials
cred = credentials.Certificate("serviceAccountKey.json")  # Path to Firebase credentials
initialize_app(cred)  # Initialize the Firebase app
db = firestore.client()  # Create a Firestore client

# move these to a separate file
PINECONE_API_KEY = ''
PINECONE_ENVIRONMENT = ''
GRANITE_API_URL = "https://api.watsonx.ibm.com/model-endpoint"
GRANITE_API_KEY = "your-granite-api-key"


pinecone.init(api_key = PINECONE_API_KEY, environment = PINECONE_ENVIRONMENT)
index = pinecone.index('document-embeddings')

def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ' '.join([page.extract_text() or '' for page in pdf.pages])
        print(text)
        return text
    
def generate_embeddings(text):
    return embedding_model.encode(text, convert_to_numpy=True).toList()

def store_document_in_firebase(filename, text, embedding): # the embeddings should also be stored in Firestore
    doc_ref = db.collection('workflow_documents').document()
    doc_data = {
        'filename': filename,
        'text_summary': text[:500],
        'pinecone_id': doc_ref.id
    }
    doc_ref.set(doc_data)
    index.upsert([(doc_ref.id, embedding)])

    return doc_ref.id

def retrieve_relevant_documents(query):
    query_embedding = generate_embeddings(query)
    results = index.query(query_embedding, top_k=5, include_metadata=True)

    retrieved_docs = []
    for match in results['matches']:
        doc_ref = db.collection('workflow-documents').document(match['id']).get()
        if doc_ref.exists:
            retrieved_docs.append(doc_ref.to_dict())

    return retrieved_docs

def analyze_workflow_with_granite(doc_text):
    """Sends document text to Granite for workflow insights."""
    headers = {
        'Authorization': f'Bearer {GRANITE_API_KEY}',
        'Content-Type': 'application/json'
    }

    prompt = f"""
    You are an expert business workflow analyst. Your role is to analyze the workflows provided to you and review them critically to score them and suggest improvements with brief explanations, based on the user's query.
    <document_content>
        {doc_text[:3000]}
    </document_content>

    User Query: {user_query}

    Guidelines for your response:
    1. Analyze the current workflow and provide a sentiment_score of 1 to 10, where 10 indicates highest efficiency with least risk for future processes.
    2. Provide a maximum of three actionable suggestions to improve the workflow. Identify potential risks where identified and appropriate.
    3. Write a brief paragraph of maximum three sentences to provide the reasoning behind your suggestions. 
    4. Always ensure to follow best practices.
    5. Think through each step, verify each step. Do not ever hallucinate - only use the data provided to you as context for your suggestions.
    
    """

    payload = {
        'prompt': prompt,
        'max_tokens': 1000,
        'temperature': 0.2
    }

    try:
        response = requests.post(GRANITE_API_URL, json=payload, headers=headers)
        response.raise_for_status()

        # Parse the API Response
        result = response.json()
        analysis = {
            'sentiment': result.get('sentiment_score', 0),
            'suggestions': result.get('suggestions', []),
            'risks': result.get('risks', []),
            'raw_response': result
        }

        return analysis

    except requests.exceptions.RequestException as e:
        return { 'error': f'API Request Failed: {str(e)}'}
    except json.JSONDecodeError:
        return {'error': 'Failed to parse API Response'}
    

uploaded_file = st.file_uploader("Upload a Workflow Document (PDF)", type=["pdf"])

if uploaded_file:
    with st.spinner("Processing document..."):
        text = extract_text_from_pdf(uploaded_file)
        embedding = generate_embeddings(text)
        doc_id = store_document_in_firebase(uploaded_file.name, text, embedding)
        st.success("Document uploaded & processed!")

query = st.text_input("🔍 Enter a query to analyze workflows:")
if st.button("Analyze"):
    if query:
        with st.spinner("Retrieving relevant workflows..."):
            docs = retrieve_relevant_documents(query)
            if docs:
                st.subheader("🔹 Retrieved Documents:")
                for doc in docs:
                    st.write(f"📜 {doc['filename']}: {doc['text_summary']}")

                st.subheader("💡 Workflow Insights:")
                insights = analyze_workflow_with_granite(docs[0]["text_summary"])
                st.write(insights)
                
                # Store insights back into Firestore
                db.collection("workflow_analysis").add({"query": query, "insights": insights})
                
            else:
                st.warning("No relevant documents found.")






