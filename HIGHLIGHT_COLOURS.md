# Highlight colours

`tools/evidence.py` reads the table below to colour the highlighted papers.
To change a colour, edit the hex value here and re-run the tool. Every row in an
evidence table has a **Category** matching a name in the first column.

**Colour = what the evidence is about.**
**Style = how sure we are:**

- **Plain highlight:** *Stated*. The paper says it directly.
- **Highlight with a dark wavy underline:** *Inferred*. A judgement; click it to read the reasoning and codebook rule.
- *Not found* has no highlight. It appears on the summary page only.

Each highlight also has a **tag** in the page margin, in the same colour (e.g. `O12a`).
The tag is the spreadsheet column code from CODEBOOK.md, and it matches a row in the
paper's checklist (`checklists/paper_XX_checklist.xlsx`).

Clicking any highlight or tag shows the field, the value in the spreadsheet, any
suggested value, the status, the basis and the reasoning. The first page of every highlighted PDF repeats this legend and lists
every field with its page.

| Category | Colour | Hex | Use for |
|---|---|---|---|
| Bibliographic | light grey | `#D9D9D9` | Reference, DOI, Year, Journal |
| Sample & setting | aqua | `#8FE3EE` | Countries, Multi-sport, Sports, Club sample size, Participant sample size |
| Design & methods | lavender | `#CDBEFF` | Approach, Time design, Research method, Data collection, Model families |
| Frameworks & critical elements | lime | `#D4F57A` | Critical elements used, framework statements |
| Human Resources Capacity | yellow | `#FFE94D` | HR column, and HR indicators or themes |
| Financial Capacity | green | `#9BE68A` | Financial column, and financial indicators or themes |
| Infrastructure and Process Capacity | orange | `#FFBE73` | Infrastructure column, and infrastructure, process or culture indicators |
| Planning and Development Capacity | pink | `#FFB3D9` | Planning column, and planning indicators or themes |
| Relationship and Network Capacity | blue | `#8CBFFF` | Relationships column, and relationship indicators or themes |
| External | red | `#FF8C8C` | External column, and environmental, resource-access or historical factors (left of Hall's model) |
| Outputs and outcomes | sand | `#E6CC99` | Outcome variables that are results of capacity (right of Hall's model) |
| Not capacity | silver | `#BFC7CC` | Controls such as club size, sport type, region dummies |
| Limitations & future research | mauve | `#E0B0F0` | Limitations and future-research points |

Indicators are coloured by their **Dimension**, so all of a paper's financial
variables are green, its external factors red, and so on.
