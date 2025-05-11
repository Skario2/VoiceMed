# 🩺 MedVoice – Conversational AI for Inclusive Digital Healthcare

---

### 🚀 One-Sentence Pitch

**MedVoice** makes digital healthcare services accessible to everyone and saves patients and medical staff time and improves care quality through a conversational AI-powered phone assistant.

---

### 💡 What Is This Project?

**MedVoice** empowers all demographics to use digital healthcare services.

We improve clinical efficiency by streamlining patient intake and medical report digitalization using real-time conversational and personalized AI phone calls. This approach invites even elderly and digitally averse patients. A voice agent guides patients through medical history and symptom-checking, reducing administrative workload and minimizing errors from incomplete information.

Patients can upload relevant medical documents via SMS links, and we use OCR to process paper reports for seamless database integration. Beyond data collection, our system detects blind spots (e.g., missing prescriptions for chronic conditions) and provides real-time feedback to improve healthcare insights.

---

### 🛠️ How Did We Build It?

We built the system using **GPT-4-realtime** for natural patient interaction and **Twilio** for voice and messaging.

The entire architecture, including the voice agent, backend, and AI logic, is written in **Python**, ensuring flexibility and scalability.

Patients upload documents via SMS links, which are processed with **GPT-4-powered OCR** for seamless integration. Data is stored in a **PostgreSQL** database and made available for future use.

---

### ⚠️ Challenges We Faced

Since a significant user group is averse to using apps and sharing data, we had to come up with a very simple solution to really meet their needs.

On the technical side:
- Combining multiple tools and AI agents was non-trivial.
- The **GPT-4-realtime API** lacks thorough documentation.
- We spent much more time than expected on fine-tuning conversational flows.

---

### 🐳 How to Run the App with Docker

#### 📋 Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)

#### 📦 Setup Steps

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-username/medvoice
   cd medvoice
   ```

2. **Create a `.env` file**  
   Add your credentials and secrets:

   ```env
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   GPT4_API_KEY=your_openai_key
   ```

3. **Build and start the containers**  
   ```bash
   docker-compose build
   docker-compose up
   ```

4. **Access the services**
   - Backend: [http://localhost:8000](http://localhost:8000)
   - PostgreSQL: `localhost:5432` (user: `postgres`, db: `patients`)

---

### ✅ What Should Happen

- 🧠 Patients interact with an AI phone agent powered by GPT-4.
- 📩 SMS links are sent for document uploads.
- 📄 Documents are processed using OCR + GPT.
- 🗃️ Extracted data is stored in the PostgreSQL database.
- 📊 Doctors and staff receive structured insights with reduced manual input.

---

### 📁 Folder Structure

```
├── .env
├── Dockerfile
├── docker-compose.yml
├── backend/
├── voice-agent/
├── db/patients/
├── .view/ai-patient-upload-webapp/
├── static/
├── uploads/
├── requirements.txt
└── README.md
```

---

### 👥 Team

Built with care and innovation by the **MedVoice** team 💙