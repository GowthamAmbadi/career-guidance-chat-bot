# 🚀 User Guide: Career Guidance Chatbot

## **How Users Access Features**

All 6 features are accessible through **natural conversation** in the chat UI. The bot automatically detects what you want and routes to the appropriate feature!

---

## **📍 Access Methods**

### **1. Resume/CV Parsing** 📄

**Option A: Upload Button**
- Click the "📄 Upload Resume" button at the top of the chat
- Select your resume file (.pdf, .docx, .txt)

**Option B: Paste Text**
- Paste your resume text directly in the chat
- Say: "Here's my resume: [paste text]"
- Or just paste a long resume text (>200 words)

**What Happens:**
- Resume is parsed to extract: name, email, experience, skills
- Profile is automatically saved to database
- Bot confirms and suggests next steps

---

### **2. Career Path Recommendation** 🎯

**Just Ask:**
- "What careers are good for me?"
- "Recommend careers based on my skills"
- "What should I become?"
- "Suggest career paths for me"

**What Happens:**
- Bot reads your saved profile (skills + experience)
- Uses AI to suggest 5 relevant careers
- Shows description, salary range, outlook

**Note:** Requires your resume to be uploaded first!

---

### **3. Skill Gap Analysis** 📊

**Ask with Target Career:**
- "What skills do I need for Data Scientist?"
- "Analyze my skills for Software Engineer"
- "What am I missing to become a Machine Learning Engineer?"
- "Compare my skills with Product Manager requirements"

**What Happens:**
- Bot compares your skills vs required skills for the career
- Shows ✅ Skills You Have
- Shows ❌ Skills You Need to Develop
- Provides recommendations

**Note:** Requires your resume to be uploaded first!

---

### **4. Job Fit Analyzer** 📋

**Paste Job Description:**
- Just paste a full job description (300+ words)
- Or say: "How well do I fit this job? [paste job description]"
- Or ask: "Analyze my fit for this role: [job description]"

**What Happens:**
- Bot analyzes your entire profile against job requirements
- Generates fit score (0-100)
- Shows rationale and insights
- Highlights strengths and gaps

**Note:** Requires your resume to be uploaded first!

---

### **5. Goal Setting & Tracking** 🎯

**Set a Goal:**
- "Set a goal to learn Python"
- "Help me set a goal to master Machine Learning"
- "Create a goal to improve my SQL skills"
- "I want to learn Data Visualization"

**View Goals:**
- "What are my goals?"
- "Show my goals"
- "List all my goals"
- "Tell me about my goals"

**What Happens:**
- Goals are saved to database
- Can view all active goals
- Track your career development

**Note:** Requires `user_id` (automatically set in chat UI)

---

### **6. Knowledge Grounding (RAG)** 📚

**Ask Career Questions:**
- "What is the job outlook for Data Scientists in 2025?"
- "Tell me about Software Engineering career"
- "What's the salary range for Product Managers?"
- "How do I become a Data Analyst?"
- "What is the day-to-day work of a BI Architect?"

**What Happens:**
- Bot searches career knowledge database
- Retrieves relevant career information
- Generates accurate, data-driven answers
- Shows sources of information

**No resume required!** Works for general career questions.

---

## **💡 Example Conversation Flow**

```
User: [Uploads resume via button]
Bot: ✅ Resume parsed! Profile saved.

User: "What careers are good for me?"
Bot: 🎯 Career Recommendations:
     1. Data Scientist
     2. Software Engineer
     ...

User: "What skills do I need for Data Scientist?"
Bot: 📊 Skill Gap Analysis:
     ✅ Skills You Have: Python, SQL
     ❌ Skills to Develop: Machine Learning, Statistics
     ...

User: "Set a goal to learn Machine Learning"
Bot: ✅ Goal Set Successfully!
     🎯 Your New Goal: "learn Machine Learning"

User: "What is the job outlook for Data Scientists?"
Bot: 📚 [RAG-powered answer with sources]
```

---

## **🔧 Technical Details**

### **Intent Detection**
The bot uses pattern matching and keyword detection to automatically route your message to the right feature:
- Resume patterns: "parse resume", "analyze cv", long text with keywords
- Career patterns: "what careers", "recommend", "suggest"
- Skill gap: "skills for X", "analyze skills", "skill gap"
- Job fit: job description keywords, "how well do I fit"
- Goals: "set goal", "help me learn", "create goal"
- RAG: questions, "what is", "tell me about", "outlook"

### **User ID Management**
- User ID is automatically generated and stored in browser localStorage
- Same user ID persists across sessions
- No login required for basic features

---

## **🌐 Access**

**Chat UI:** http://localhost:8000/

**API Docs:** http://localhost:8000/docs

---

## **📝 Notes**

- **Resume Required:** Features 2, 3, 4 require your resume to be uploaded first
- **Natural Language:** No need to remember exact commands - chat naturally!
- **Context Aware:** Bot remembers conversation history (last 10 messages)
- **Always Learning:** RAG knowledge base can be expanded with more career data

