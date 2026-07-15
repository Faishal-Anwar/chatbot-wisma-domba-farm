import os
import psycopg2
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

load_dotenv()

def get_static_documents():
    data_dir = "data"
    static_files = ["investasi.txt", "kesehatan.txt", "produk.txt", "profil.txt"]
    docs = []
    if os.path.exists(data_dir):
        for filename in static_files:
            file_path = os.path.join(data_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    docs.append(Document(page_content=content, metadata={"source": filename}))
    return docs

def fetch_db_documents():
    docs = []
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "6543"),
            database=os.getenv("DB_DATABASE"),
            user=os.getenv("DB_USERNAME"),
            password=os.getenv("DB_PASSWORD")
        )
        cur = conn.cursor()

        # 1. Sheep
        cur.execute("SELECT tag, type, weight, status, price_per_kg, age_string, health, gender FROM sheep;")
        sheep_data = cur.fetchall()
        sheep_text = "Data Inventaris Domba di Wisma Domba Farm:\n\n"
        for row in sheep_data:
            tag, stype, weight, status, price_per_kg, age_string, health, gender = row
            gender_str = "jantan" if gender == "male" else "betina" if gender == "female" else str(gender)
            price_str = f"Rp {price_per_kg}/kg" if price_per_kg else "harga belum ditentukan"
            sheep_text += f"Domba {gender_str} dengan tag {tag} (jenis {stype}) saat ini berumur {age_string}, memiliki bobot {weight} kg, dalam kondisi {health}, dan berstatus {status} dengan harga {price_str}.\n"
        docs.append(Document(page_content=sheep_text, metadata={"source": "db_sheep"}))

        # 2. Medical Records
        cur.execute("""
            SELECT s.tag, m.diagnosis, m.treatment, m.notes, m.handled_at 
            FROM medical_records m
            JOIN sheep s ON m.sheep_id = s.id;
        """)
        medical_data = cur.fetchall()
        medical_text = "Data Rekam Medis Domba di Wisma Domba Farm:\n\n"
        for row in medical_data:
            tag, diag, treat, notes, handled_at = row
            medical_text += f"Pada tanggal {handled_at}, domba {tag} didiagnosis mengalami {diag}. Perawatan yang diberikan: {treat}. Catatan medis: {notes}.\n"
        docs.append(Document(page_content=medical_text, metadata={"source": "db_medical"}))

        # 3. About Sections
        cur.execute("SELECT title, subtitle, content FROM about_sections WHERE is_active = true;")
        about_data = cur.fetchall()
        about_text = "Informasi Profil dan Layanan Wisma Domba Farm:\n\n"
        for row in about_data:
            title, subtitle, content = row
            about_text += f"== {title} ==\n{subtitle}\n"
            if content:
                about_text += f"Detail:\n"
                if isinstance(content, dict):
                    for k, v in content.items():
                        about_text += f"- {k}: {v}\n"
                elif isinstance(content, list):
                    for item in content:
                        about_text += f"- {item}\n"
                else:
                    about_text += f"{content}\n"
            about_text += "\n"
        docs.append(Document(page_content=about_text, metadata={"source": "db_about"}))
        
        # 4. Stats
        cur.execute("SELECT label, value FROM stats WHERE is_active = true;")
        stats_data = cur.fetchall()
        stats_text = "Statistik Pencapaian Wisma Domba Farm:\n\n"
        for row in stats_data:
            label, value = row
            stats_text += f"- {label}: {value}\n"
        docs.append(Document(page_content=stats_text, metadata={"source": "db_stats"}))

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        
    return docs

def run_sync():
    index_name = os.getenv("PINECONE_INDEX_NAME")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not index_name or not pinecone_api_key or not google_api_key:
        return {"success": False, "message": "Missing API keys."}

    # Fetch all documents
    docs = get_static_documents()
    db_docs = fetch_db_documents()
    if db_docs:
        docs.extend(db_docs)
    
    if not docs:
        return {"success": False, "message": "No documents found to ingest."}

    try:
        pc = Pinecone(api_key=pinecone_api_key)
        
        # Clear existing vectors
        index = pc.Index(index_name)
        try:
            index.delete(delete_all=True)
            print("Existing vectors cleared.")
        except Exception as e:
            print(f"Could not clear vectors: {e}")

        # Initialize Embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            task_type="retrieval_document"
        )

        # Ingest to Pinecone
        PineconeVectorStore.from_documents(
            docs, 
            embeddings, 
            index_name=index_name
        )
        return {"success": True, "message": f"Successfully ingested {len(docs)} documents."}
    except Exception as e:
        print(f"Error during Pinecone ingestion: {e}")
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    result = run_sync()
    print(result)
