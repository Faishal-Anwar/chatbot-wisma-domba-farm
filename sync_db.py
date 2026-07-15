import os
import psycopg2
import json
from dotenv import load_dotenv

load_dotenv()

def sync_database_to_rag():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "6543"),
            database=os.getenv("DB_DATABASE"),
            user=os.getenv("DB_USERNAME"),
            password=os.getenv("DB_PASSWORD")
        )
        cur = conn.cursor()
        print("Connected to database successfully.")

        os.makedirs("data", exist_ok=True)

        # 1. Fetch Sheep
        cur.execute("SELECT tag, type, weight, status, price_per_kg, age_string, health, gender FROM sheep;")
        sheep_data = cur.fetchall()
        with open("data/db_sheep.txt", "w", encoding="utf-8") as f:
            f.write("Data Inventaris Domba di Wisma Domba Farm:\n\n")
            for row in sheep_data:
                tag, stype, weight, status, price_per_kg, age_string, health, gender = row
                gender_str = "jantan" if gender == "male" else "betina" if gender == "female" else str(gender)
                price_str = f"Rp {price_per_kg}/kg" if price_per_kg else "harga belum ditentukan"
                f.write(f"Domba {gender_str} dengan tag {tag} (jenis {stype}) saat ini berumur {age_string}, memiliki bobot {weight} kg, dalam kondisi {health}, dan berstatus {status} dengan harga {price_str}.\n")
        print(f"Exported {len(sheep_data)} sheep records.")

        # 2. Fetch Medical Records
        cur.execute("""
            SELECT s.tag, m.diagnosis, m.treatment, m.notes, m.handled_at 
            FROM medical_records m
            JOIN sheep s ON m.sheep_id = s.id;
        """)
        medical_data = cur.fetchall()
        with open("data/db_medical.txt", "w", encoding="utf-8") as f:
            f.write("Data Rekam Medis Domba di Wisma Domba Farm:\n\n")
            for row in medical_data:
                tag, diag, treat, notes, handled_at = row
                f.write(f"Pada tanggal {handled_at}, domba {tag} didiagnosis mengalami {diag}. Perawatan yang diberikan: {treat}. Catatan medis: {notes}.\n")
        print(f"Exported {len(medical_data)} medical records.")

        # 3. Fetch About Sections
        cur.execute("SELECT title, subtitle, content FROM about_sections WHERE is_active = true;")
        about_data = cur.fetchall()
        with open("data/db_about.txt", "w", encoding="utf-8") as f:
            f.write("Informasi Profil dan Layanan Wisma Domba Farm:\n\n")
            for row in about_data:
                title, subtitle, content = row
                f.write(f"== {title} ==\n{subtitle}\n")
                if content:
                    f.write(f"Detail:\n")
                    if isinstance(content, dict):
                        for k, v in content.items():
                            f.write(f"- {k}: {v}\n")
                    elif isinstance(content, list):
                        for item in content:
                            f.write(f"- {item}\n")
                    else:
                        f.write(f"{content}\n")
                f.write("\n")
        print(f"Exported {len(about_data)} about sections.")
        
        # 4. Fetch Stats
        cur.execute("SELECT label, value FROM stats WHERE is_active = true;")
        stats_data = cur.fetchall()
        with open("data/db_stats.txt", "w", encoding="utf-8") as f:
            f.write("Statistik Pencapaian Wisma Domba Farm:\n\n")
            for row in stats_data:
                label, value = row
                f.write(f"- {label}: {value}\n")
        print(f"Exported {len(stats_data)} stats.")

        cur.close()
        conn.close()
        print("Database sync to text files completed successfully.")

    except Exception as e:
        print(f"Error connecting to or querying the database: {e}")

if __name__ == "__main__":
    sync_database_to_rag()
