# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

The initial UML design consists of four classes:
    - `Pet` - Data class. Hold pet attributes such as name, species, age, and notes.
    - `Owner`. Data class. Holds name, budget time, pets, and schedules. Can add and remove tasks.
    - `Scheduler` - Concrete class. Generates plans and manages high-level scheduling.
    - `Task` - Data class. Contains key task atributes such as name, priority (for sorting), and is mandatory. 

There is also an enum called `Priority` to manage task priority and allow sorting by priority.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, the design of the app specified by the UML changed. In particular, I had Claude Code add another enum for `Frequency`, which helped with the smart feature of automatically adding the next ocurrence of a recurring task that is marked as complete. This ensured that frequency appeared as a dropdown with only a select few values and that the internal logic can handle all the choices.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

I implemented priority as a constraint since it was the simplest for this project but also the most useful. Pet owners want to ensure they do the urgent tasks first to ensure their pets' wellbeing. Plus, this opens up a nice opportunity for the front end to have a sort-by-priority functionality.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The scheduler airs on the side of code readibility and not necessarily efficiency. For example, it uses list comprehension to create a completely new list each time items need to be removed from it. Under a DSA context, this is inefficient due to extra memory allocation. However, I decided this tradeoff was reasonable in this app's scenario since owners would only have a countable number of pets and tasks, so efficiency differences should be minimal with normal use, especially if the code is more robust (e.g. removing all duplicates via list comprehension) and short.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI tools to generate and modify most, if not all, of the code. However, I made sure to check each generation (i.e., which lines it removed and which lines it added). I noticed that prompts that were specific and guiding were the most helpful. For example, when addressing an issue in the UI, I made sure to describe the issue, the ocassion that caused it, and a potential culprit to keep the AI on track.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

One time when I did not accent the AI suggestion was when it assumed that entering a non-zero duration should mandate entering a start time for a task (to be symmetric with the requirement that a non-empty start time requires a non-zero duration). However, I placed myself in the user's shoes and imagined that they would like the ability to enter durations for tasks even when they are unsure of the start time. Claude code has a useful feature to amend suggestions (via <kbd>Tab</kbd>) after accepting or rejecting them, so to propose my change, I accepted its code generation and adding something along the lines of "but the user shouldn't have to enter a start time for a task of non-zero duration," and it amended as I expected.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I mostly tested the algorithmic functionality via the unit tests, such as filtering, sorting, and auto-creating the next occurrence for recurring tasks. These tests were important to ensure that the core functionality of the app worked properly, ensuring a good user experience that matches their expectations.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

Thanks to the unit tests paired with my own interface testing from the user's perspective, I'm 90% sure the scheduler works correctly. I already had Claude Code generate edge cases such a creating the next occurrence for a yearly recurring task on 2/29/xxxx (for xxxx being a leap year), which should be 2/28 of the next year since it wouldn't also be a leap year. However, I would test even more edge cases not just in date deltas but also user behaviors that may "break" the app (the famous notion that software developers and designers have to think of all the ways users may enter the wrong input, break the app, etc.)

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with the algorithmnic portion of the app since it forms the bulk of the app's functionality. I'm especially happy with how Claude was able to generate modular and readable code (I even learned what "pluggable" means in programming now!).

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would improve the interface a bit such as the user-facing errors and warnings as well as formattin and style. This depends on Streamlit's customizability, but if I had more time, I would definitely explore the ways in which I can make the interface more friendly since right now, due to a time crunch, I was mainly focused on the algorithmic and backend portion of the app.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The most important thing I learned designing an app from ground up using AI based on given specifications is to *always* check the AI's work, preferably in the code itself and the end product (e.g., UI) afterwards but not just the latter. It helps prevents bugs later down the line (many of which compound if not dealt with early on!) and helps you remain sharp in your coding knowledge. Just like how it's important to learn conversion from binary to decimal (and vice versa) even though computers do it for us, so is learning to code and staying sharp in that skill.

## 6. Prompt Comparison

I used Claude Code for most of the code in the app, but I also tried out Gemini, which couldn't directly read my file system. When I asked both to generate the logic for suggesting next slot for a pet based on current tasks already made for that pet with time and duration info, the difference was clear. While both Claude Code and Gemini adhered to my prompt, Claude's implementation was less Pythonic than Gemini, but it was more modular than Gemini's. This is most likely because I created the project-based agent for Claude Code to specifically focus on readability then code efficiency, so it was able to use that context to err on the side of modularity and readability instead of the most Pythonic or shortest code. Furthermore, the experience of using both was vasly different too. Since Gemini isn't built into the code editor and can't read the project files (unless you use Antigravity), I had to include the necessary context (existing code and desired specifications, etc.), whereas Claude Code could refer to the file system directly as well as its agent memory that persisted across sessions, making it much more seamless coding assistant.