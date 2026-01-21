# AI Travel Planner Agent for Students

Welcome to the **AI Travel Planner** — an intelligent assistant powered by **IBM WatsonX** to help users plan trips effortlessly.  
The AI is strictly limited to **travel-related queries**. If asked about anything unrelated, it politely responds:  
> “Sorry, I can only help with travel-related queries.”

---

## Features

-  AI-driven travel planning
-  Trip suggestions based on budget and number of people
-  Powered by IBM WatsonX
-  Friendly and easy-to-use interface

---

## Technologies Used

- **Frontend:** React, TypeScript, Tailwind CSS
- **Backend:** FastAPI
- **AI Model:** IBM WatsonX
  - watsonx.ai Runtime-aw
  - watsonx.ai Studio-kb
  - Cloud Object Storage-yj

---

## How to Run Locally

Make sure to start both frontend and backend for the app to work correctly.

### Frontend Setup

1. Navigate to the main directory and Install the dependencies:
   
   ```bash
   npm install
2. Start the development server:

   ```bash
   npm run dev

> “⚠️ Always run the backend too — the frontend alone won’t function.”

---

### 🔧 Backend Setup

1. Move into the backend folder:
   
   ```bash
   cd backend
2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt

3. Run the backend:

   ```bash
   python -m uvicorn app:app --reload

> “No need to set up .env — all required configurations are pre-set in app.py.”



---

### Testing

1. Example travel query:
   
   ```bash
   Hi, plan a trip to Kolkata for 5 days. My budget is ₹30000 and 3 people are coming with me.
2. Example of a blocked query:

   ```bash
   Tell me about cricket.

Expected reply: “Sorry, I can only help with travel-related queries.”

   ---

### License

This project is open-source and free to use under the MIT License.
---
### Developed by

### Jeet Banik
