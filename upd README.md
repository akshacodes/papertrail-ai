# 📄 PaperTrail AI

Ask your PDFs and images anything – an interactive Streamlit app powered by Google Gemini 1.5 Flash.

## 🔍 Features

- 📤 Upload PDFs and scanned images
- 🧠 Extract text using PyMuPDF (PDFs) and pytesseract (OCR for images)
- 💬 Ask questions in natural language and receive AI-generated responses using Google Gemini API
- 📚 Multi-session support: Create, rename, and delete separate chats per document
- 🔐 Secure secret management with `.streamlit/secrets.toml`
- 🧪 Fully tested for local execution with clean UI and smooth UX

## 🚀 How to Run Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/akshacodes/papertrail-ai.git
   cd papertrail-ai
   
2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt

3. **Set up Google Gemini API Key**
   
   Create a file at .streamlit/secrets.toml and add:
     ```bash
   [google]
   api_key = "your_google_gemini_api_key"

 ⚠️ Important: Never commit this file. It is ignored via .gitignore.
 
   
4. **Launch the App**
   ```bash
   streamlit run app.py

## 🧠 Tech Stack
Python

Streamlit

PyMuPDF – for PDF parsing

pytesseract – for OCR on image files

Google Gemini API – for natural language question answering

Session State Management – using st.session_state for chat sessions

## 📸 Screenshots
![Screenshot 2025-05-22 012000](https://github.com/user-attachments/assets/613dc623-4b2f-4ebc-a170-3a5ba7a3b086)

## 🌐 Live Demo
🚧 Deployment in progress – will update when available

## ✍️ Author
**Akshata More**  
🔗 [LinkedIn](https://www.linkedin.com/in/akshata-p-more)  
💻 [GitHub](https://github.com/akshacodes)

## ⭐️ Support
If you like this project, please give it a ⭐ on GitHub!
It helps others discover and use the tool.

## 📜 License
This project is licensed under the MIT License.

   
