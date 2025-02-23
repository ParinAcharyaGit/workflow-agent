<div align="left" style="position: relative;">
<img src="https://raw.githubusercontent.com/PKief/vscode-material-icon-theme/ec559a9f6bfd399b82bb44393651661b08aaf7ba/icons/folder-markdown-open.svg" align="right" width="30%" style="margin: -20px 0 0 20px;">
<h1>WorkwiseAI</h1>
<p align="left">
	<em><code>PARIN ACHARYA</code></em>
</p>
<p>Generative AI Hackathon with IBM Granite</p>
<p align="left">
	<img src="https://img.shields.io/github/license/ParinAcharyaGit/workflow-agent?style=default&logo=opensourceinitiative&logoColor=white&color=0080ff" alt="license">
	<img src="https://img.shields.io/github/last-commit/ParinAcharyaGit/workflow-agent?style=default&logo=git&logoColor=white&color=0080ff" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/ParinAcharyaGit/workflow-agent?style=default&color=0080ff" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/ParinAcharyaGit/workflow-agent?style=default&color=0080ff" alt="repo-language-count">
</p>
<p align="left"><!-- default option, no dependency badges. -->
</p>
<p align="left">
	<!-- default option, no dependency badges. -->
</p>
</div>
<br clear="right">

##  Quick Links

- [ Overview](#-overview)
- [ Features](#-features)
- [ Technology Used](#-technology-used)
- [ Project Structure](#-project-structure)
  - [ Project Index](#-project-index)
- [ Getting Started](#-getting-started)
  - [ Prerequisites](#-prerequisites)
  - [ Installation](#-installation)
  - [ Usage](#-usage)
  - [ Testing](#-testing)
- [ Roadmap of Project Tasks](#-project-roadmap)
- [ Contributing](#-contributing)
- [ License](#-license)
- [ Acknowledgments](#-acknowledgments)

---

##  Overview

<code>WorkwiseAI is an AI Agent framework that pinpoints business workflow inefficiencies and streamlines processes using cutting-edge IBM Granite models.</code>

### Some key use cases of IBM Cloud Services in enhancing business workflows
1. Vodafone, a global communications leader, is using IBM Watson to simulate and analyze digital disucssions with its AI powered virtual agent, reducing testing timelines to under 1 minute. [Read more](https://www.ibm.com/case-studies/vodafone-tobi)
2. Artefact, a leading French Bank uses a portfolio of personas represented by AI identities, allowing professionals to reveal crucial insights from customer behavior.
[Read more](https://www.ibm.com/case-studies/artefact)


---
### Technology Used
---

##  Features

- *Business workflow context grounding* using a knowledge base of company documents, in <code>IBM Vector Indexes</code>.
- *Cutting-edge AI Insights* in generative tasks through the state-of-the-art <code>granite-3-8b-instruct</code> foundation model. [see Model card](https://huggingface.co/ibm-granite/granite-3.1-8b-instruct)
- *Workflow vizualization dashboard* in Streamlit with clear, interactive widgets to represent large data.
- *WorkwiseAI 'S3' Agent* - a ground-up agent pipeline built on top of the LangChain Framework in IBM AgentLab to analyze business workflow inefficiencies. 
This enables powerful support for 3 worker agents:
    * **Summarizer agent**
        - Breaks down business workflow steps from the context of the knowledge base to reveal critical insights and inefficiency factors.
    * **Scorer agent**
        *Evaluates each step in the current workflow using a custom scoring model alongside industry-relevant metrics.
    * **Suggester agent**: Access to tools like WikipediaQuery, GoDuckGoSearch and RAGQuery to suggest actionable improvements to each step in the workflow.
- *Chatbot User Interface* grounded in business context documents with multi-language support.


## Workflow Diagram

##  Project Structure

```sh
└── workflow-agent/
    ├── .github
    │   └── CODEOWNERS
    ├── LICENSE
    ├── README.md
    ├── agents.py
    ├── main.py
    ├── react-agent.py
    ├── requirements.txt
    ├── shared_state.py
    ├── test.py
    └── utils.py
```

---
##  Getting Started

###  Prerequisites

Before getting started with workflow-agent, ensure your runtime environment meets the following requirements:

- **Programming Language:** Python
- **Package Manager:** Pip


###  Installation

Install workflow-agent using one of the following methods:

**Build from source:**

1. Clone the workflow-agent repository:
```sh
❯ git clone https://github.com/ParinAcharyaGit/workflow-agent
```

2. Navigate to the project directory:
```sh
❯ cd workflow-agent
```

3. Install the project dependencies:


**Using `pip`** &nbsp; [<img align="center" src="https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white" />](https://pypi.org/project/pip/)

```sh
❯ pip install -r requirements.txt
```




###  Usage
Run workflow-agent using the following command:
**Using `pip`** &nbsp; [<img align="center" src="https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white" />](https://pypi.org/project/pip/)

```sh
❯ python {entrypoint}
```


###  Testing
Run the test suite using the following command:
**Using `pip`** &nbsp; [<img align="center" src="https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white" />](https://pypi.org/project/pip/)

```sh
❯ pytest
```


---
##  Roadmap of Project Tasks

### Completed

- [X] **`Task 1`**: Implement vector index endpoints and implement document upload feature.
- [x] **`Task 2`**: Implement S3 agent worflow in IBM AgentLab
- [x] **`Task 3`**: Enable key side-by-side vizualizations using Streamlit Widgets for comparison with S3 agent suggestions
- [x] **`Task 4`**: Prototype Documentation and Demo

### In progress

- [ ] **`Task 5`**: Firestore Database and User Authentication
- [ ] **`Task 6`**: Complete user testing and agent pipeline testing
- [ ] **`Task 7`**: Expand tool support for S3 Agent
- [ ] **`Task 8`**: Advanced NLP and vector embedding techniques for user chatbot conversations 

- ---

##  Contributing

- **💬 [Join the Discussions](https://github.com/ParinAcharyaGit/workflow-agent/discussions)**: Share your insights, provide feedback, or ask questions. Feel free to reach out on [LinkedIn](https://www.linkedin.com/in/parinacharya)!
- **🐛 [Report Issues](https://github.com/ParinAcharyaGit/workflow-agent/issues)**: Submit bugs found or log feature requests for the `workflow-agent` project.
- **💡 [Submit Pull Requests](https://github.com/ParinAcharyaGit/workflow-agent/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.


<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your github account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone https://github.com/ParinAcharyaGit/workflow-agent
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to github**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="left">
   <a href="https://github.com{/ParinAcharyaGit/workflow-agent/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=ParinAcharyaGit/workflow-agent">
   </a>
</p>
</details>

---

##  License

This project is protected under the [SELECT-A-LICENSE](https://choosealicense.com/licenses) License. For more details, refer to the [LICENSE](https://choosealicense.com/licenses/) file.

---

##  Acknowledgments

### Resources, guides and support
    1. IBM Documentation
    2. Lablab.ai Discord Channel

### Sources of Inspiration 
[Nosu](https://nosu.io)
