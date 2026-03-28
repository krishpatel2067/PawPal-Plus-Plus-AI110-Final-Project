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

Yes, the design of the app specified by the UML changed. In particular, I made it so that the owner can have multiple schedules and allow them to create/remove scheduled tasks and standalone tasks. This allows them to collect tasks into multiple groups while allowing the option of groupless tasks.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

I implemented priority as a constraint since it was the simplest for this project but also the most useful. Pet owners want to ensure they do the urgent tasks first to ensure their pets' wellbeing. Plus, this opens up a nice opportunity for the front end to have a sort-by-priority functionality.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The Scheduler airs on the side of code readibility and not necessarily efficiency. For example, it uses list comprehension to creae a completely new list each time items need to be removed from it. Under a DSA context, this is inefficient due to extra memory allocation. However, I decided this tradeoff was reasonable in this app's scenario since owners would only have a countable number of pets and tasks, so efficiency differences should be minimal with normal use, especially if the code is more robust (e.g. removing all duplicates via list comprehension) and short.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
