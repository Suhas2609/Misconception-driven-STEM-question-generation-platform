# Step 1: Test Hybrid CDM-BKT-NLP System

## 🧪 Test Procedure

### 1. Open the Web Application
```
http://localhost:5173
```

### 2. Register/Login
- Create a new account or use existing credentials
- Note down your email for reference

### 3. Upload PDF and Generate Questions
- Upload any educational PDF (physics, chemistry, etc.)
- Select topics from the extracted list
- Generate at least 3-5 questions

### 4. Take the Quiz with Strategic Responses

To test all components of the hybrid system, answer questions with these patterns:

**Question 1: Correct + High Confidence + Deep Reasoning**
- ✅ Select the CORRECT answer
- 🎯 Confidence: 80-100%
- 📝 Reasoning: Write detailed multi-step reasoning, e.g.:
  ```
  I'm confident this is correct because I can trace the causal chain:
  if A causes B and B causes C, then A indirectly causes C.
  I double-checked my logic and considered alternative explanations.
  ```

**Question 2: Incorrect + Low Confidence + Metacognitive Awareness**
- ❌ Select a WRONG answer (misconception or distractor)
- 🎯 Confidence: 20-40%
- 📝 Reasoning: Show uncertainty and monitoring, e.g.:
  ```
  I'm not sure about this one. I think it might be this answer,
  but I'm uncertain because I haven't fully understood the concept.
  What happens if we consider edge cases? I need to review this topic.
  ```

**Question 3: Correct + Overconfident + Shallow Reasoning**
- ✅ Select the CORRECT answer
- 🎯 Confidence: 100%
- 📝 Reasoning: Write minimal reasoning, e.g.:
  ```
  Obviously this.
  ```

**Question 4: Incorrect + High Confidence (if available)**
- ❌ Select a WRONG answer
- 🎯 Confidence: 80-100%
- 📝 Reasoning: Any reasoning

### 5. Monitor Backend Logs

Open a PowerShell terminal and run:
```powershell
docker logs adaptive_api -f
```

Watch for these log messages indicating the hybrid system is active:

✅ **Expected Log Patterns:**
```
🧠 Applying research-grade trait update (CDM + BKT + NLP)
📊 Analyzing reasoning depth with GPT-4o
🔍 Detected metacognitive markers: ['I'm not sure', 'uncertain']
📈 Curiosity boost: +0.05 (detected question markers)
⚖️ Confidence calibration penalty: -0.08 (overconfident)
📊 analytical_depth: 0.500 → 0.548 (Δ+0.048, 2 obs)
📊 metacognition: 0.500 → 0.575 (Δ+0.075, 3 obs)
```

### 6. Check Dashboard

After submitting the quiz:
- Navigate to the Dashboard
- Check if cognitive traits updated
- Look for **differentiated changes** (not all traits changing by ±0.02)

## 🔬 What to Look For

### ✅ SUCCESS Indicators:

1. **Bayesian Updates** (not simple ±0.02):
   - Traits change by different amounts (e.g., +0.048, +0.075, -0.032)
   - Changes reflect evidence strength (more observations = different update)

2. **NLP Analysis Active**:
   - Logs show "Analyzing reasoning depth with GPT-4o"
   - Metacognition increases when you write "I'm not sure"
   - Curiosity increases when you ask questions in reasoning

3. **Confidence Calibration**:
   - Overconfidence (100% but wrong) → negative adjustment
   - Well-calibrated (low confidence + wrong) → smaller penalty

4. **Q-matrix Inference**:
   - Calculation questions → Precision + Analytical Depth updated
   - Hard questions → Cognitive Flexibility + Analytical Depth updated
   - Misconception questions → Pattern Recognition updated

### ❌ FAILURE Indicators:

1. All traits change uniformly (e.g., all +0.02 or all -0.02)
2. No GPT-4o analysis logs
3. No differentiation based on reasoning quality
4. Traits don't respond to metacognitive markers

## 📋 Report Your Findings

After testing, report:
1. Did different traits change by different amounts?
2. Did you see GPT-4o reasoning analysis logs?
3. Did metacognition increase when you wrote "I'm not sure"?
4. Did confidence calibration penalize overconfidence?

**Then we'll proceed to Step 2 (Add explicit Q-matrix tagging)!**
