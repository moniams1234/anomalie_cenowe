# 📊 Anomalia Cenowa

Nowoczesna aplikacja webowa do wykrywania anomalii cenowych w danych magazynowych XLSX.

---

## Co robi aplikacja

- **Wgrywa** pliki XLSX z raportów magazynowych (Material stat day stock)
- **Automatycznie wykrywa** arkusz i wiersz nagłówka
- **Oblicza cenę** jednostkową: `Cena = Wartość mag. / Stan mag.`
- **Grupuje** dane po indeksie materiałowym i wylicza medianę ceny
- **Oznacza anomalie**: rekordy z odchyleniem ≥ zadany próg (domyślnie 20%)
- **Umożliwia ręczną korektę** cen referencyjnych per indeks
- **Generuje** gotowy plik XLSX z formułami i raport PDF
- **Przechowuje historię** analiz i cen ręcznych (SQLite)

---

## Uruchomienie lokalne

### Wymagania
- Python 3.11+
- pip

### Instalacja i start

```bash
git clone <twoje-repo>
cd anomalia_cenowa

python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

pip install -r requirements.txt

streamlit run app.py
```

Aplikacja dostępna pod: `http://localhost:8501`

---

## Jak działa interfejs

1. **Sidebar (ciemny)** — nawigacja, próg odchylenia, instrukcja
2. **Zakładka Analiza** — upload pliku, KPI, tabela anomalii, wykresy
3. **Zakładka Korekta cen** — edycja cen referencyjnych per indeks
4. **Zakładka Podsumowanie** — dashboard z wykresami Pareto i tabelami
5. **Historia analiz / cen** — logi sesji z filtrowaniem
6. **Ustawienia** — konfiguracja, czyszczenie sesji

---

## Wdrożenie na Streamlit Community Cloud

1. Wypchnij kod na GitHub
2. Wejdź na [share.streamlit.io](https://share.streamlit.io)
3. Kliknij **New app** → wskaż repo, branch i plik `app.py`
4. Kliknij **Deploy** → link publiczny gotowy

Wymagane pliki: `requirements.txt`, opcjonalnie `.streamlit/config.toml`

---

## Wdrożenie na Render

1. Wypchnij na GitHub
2. Utwórz nowy **Web Service** w [render.com](https://render.com)
3. Ustaw:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
4. Kliknij **Create Web Service**

---

## Wdrożenie w Dockerze

```bash
docker build -t anomalia-cenowa .
docker run -p 8501:8501 anomalia-cenowa
```

Otwórz: `http://localhost:8501`

### Docker Compose (opcjonalnie)

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
```

---

## Ograniczenia i założenia

- Plik wejściowy musi być w formacie `.xlsx`
- Arkusz z danymi powinien nazywać się `MyPrint` lub być pierwszym arkuszem
- Nagłówki mogą zaczynać się od dowolnego wiersza — aplikacja wykrywa automatycznie
- Kolumna `Stan mag.` musi być niezerowa (wiersze z zerem są pomijane)
- Historia analiz przechowywana jest w pliku `anomalia_cenowa.db` (SQLite) — persystuje między restartami lokalnie, ale nie między deploymentami na cloud (każde wdrożenie zaczyna od nowa)
- Pliki XLSX i PDF generowane są w pamięci (BytesIO) — nie są zapisywane na dysku serwera

---

## Struktura projektu

```
anomalia_cenowa/
├── app.py              # Główna aplikacja Streamlit
├── parsing.py          # Wczytywanie i parsowanie XLSX
├── analysis.py         # Logika wykrywania anomalii
├── excel_export.py     # Generowanie pliku XLSX
├── pdf_report.py       # Generowanie raportu PDF
├── database.py         # SQLite — historia analiz i cen
├── utils.py            # Wykresy i pomocnicze funkcje
├── requirements.txt
├── Dockerfile
├── Procfile
├── .streamlit/
│   └── config.toml
└── README.md
```
