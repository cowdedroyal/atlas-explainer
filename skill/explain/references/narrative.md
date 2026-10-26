# Narrative: one running example

The reader asked several questions. Do not answer each in isolation.

## Find the through-line

Ask: what is the same *thing* in all of these questions? In a pipeline it is usually one unit of data (a row, a request,
a file) seen at different stages. In a class hierarchy it is one object's life. In a protocol it is one message. Choose one concrete
instance and follow it. The question list becomes the chapter list, in the order the thing meets them — not the order the
reader happened to ask.

## Shape of a card

1. **Title** names the journey ("一行样本怎样走完数据流水线"), not the topic.
2. **Lead** (`ex-lead`): one or two sentences — what the thing is and what the card will show. If the reader's mental
   model was off, correct it here in plain words.
3. **Chapters** (`ex-qa`), each starting with the answer in the first paragraph, then the evidence:
   - *what is it* → a real `ex-table` (schema + a few rows);
   - *what happens to it* → an `ex-flow`, each stage with in/out of the **same** instance and a `why`;
   - *what changed* → an `ex-compare` on real values;
   - *what could go wrong* → a small table of cases and their causes.
4. **Pointers** to the code (`tag=` on stages, `atlas://` links) so the reader can go from the picture to the source.

## Writing rules

- Lead with the answer, then the example. "Because X" before "here is how".
- Say **why**, not only what: each stage gets one sentence on the problem it prevents. If the repository does not
  record the reason, write what the code *enforces* and mark any further reason as inference.
- Use the reader's vocabulary first, the code's names second (`parquet 是一张资产清单（代码里叫 …）`). Define a term
  once, where it first matters.
- Correct misconceptions explicitly and kindly: "S3 里存的不是 FBX 标注，而是…". Check each of the reader's stated
  assumptions against the code; wrong ones are the most valuable sentences in the card.
- Numbers: give the unit and the scale ("658 MB → 6.8 MB", "91 万行"), and say whether it was measured by you or quoted.
- Length: a chapter fits in a screen or two. If it needs more, the card is two cards, or the detail belongs in code
  comments.
- Do not narrate your investigation ("I looked at…"). State findings.

## Anti-patterns

- One card per question → the reader gets fragments with no through-line.
- Invented sample that looks real → see SKILL.md rule 1.
- Restating the code line by line → link to it instead.
- A wall of `ex-table`s with no `ex-why` → data without reasons.
- Opinions about the code's quality inside an explainer. Put those in chat.
