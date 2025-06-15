# 503B Watch Dashboard 📊

**503B Watch** is an open-source **Streamlit dashboard** for monitoring FDA-registered 503B outsourcing facilities. It tracks weekly changes, highlights compliance flags, and provides visual insight into industry trends using modern Python tools like Streamlit, DuckDB, and Plotly.

---

## 🚀 Features

- ✅ Tracks **new and removed facilities**
- ✅ Supports **period-over-period comparisons**:
  - Weekly
  - Monthly
  - Quarterly
  - Biannually
  - Annually
- ✅ Highlights facilities flagged for:
  - No FDA inspections
  - Recalls
  - Warnings
  - Inspections
- ✅ Clean, widescreen UI with single-page layout
- ✅ DuckDB-powered for easy querying of historical Excel files

---

## 🛠️ Getting Started

### ✅ Requirements

- Python 3.8+
- [pip](https://pip.pypa.io/en/stable/)

### 📦 Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/brittanyvl/503BWatch.git
   cd 503BWatch
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## 🚴 Running the App

To start the Streamlit dashboard locally:

```bash
streamlit run app.py
```

### 🔄 Data Input

- Place `.xlsx` files into:

  ```
  data/excel_files/
  ```

- Filenames must include the date in this format:

  ```
  YYYY-MM-DD_facility_data.xlsx
  ```

---

## 📊 Dashboard Functionality

- Global time filter:
  - Weekly, Monthly, Quarterly, Biannually, or Annually
- Facility metrics:
  - Total active facilities
  - % without FDA inspection
  - % with recalls, warnings, or inspections
- Change highlights:
  - New facilities (this period)
  - Removed facilities (this period)
  - Facilities newly flagged (e.g., first-time recall)

---

## 🧪 Development & Git Workflow

To work safely without impacting the main version:

```bash
git checkout -b streamlit-refactor-v2
# Make changes, then:
git add .
git commit -m "Refactor: added time filters and delta analysis"
git push origin streamlit-refactor-v2
```

Open a pull request on GitHub to merge changes back into `main`.

---

## 🤝 Contributing

Contributions welcome! Feel free to open issues or submit pull requests.

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 🙋 Contact

Created and maintained by [@brittanyvl](https://github.com/brittanyvl)  
Pull requests and collaborations welcome!
