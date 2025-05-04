import os
from typing import Dict, List
from dotenv import load_dotenv
from tavily import TavilyClient
from langgraph.graph import Graph
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json

# Initialize Tavily client
load_dotenv()
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


class ArticleGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.75)

    def planning_agent(self, content: str, tone: str, length: int) -> Dict:
        """Planning agent to outline the article structure."""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert content planner. Create a detailed outline for an article based on the following parameters:
            - Content: {content}
            - Tone: {tone}
            - Target Length: {length} words
            
            Return a JSON object with the following structure:
            {{
                "title": "Article Title",
                "sections": [
                    {{
                        "heading": "Section Title",
                        "key_points": ["point1", "point2", ...]
                    }},
                    ...
                ]
            }}""",
                ),
                ("human", "Please create an outline for the article."),
            ]
        )

        chain = prompt | self.llm
        response = chain.invoke({"content": content, "tone": tone, "length": length})

        return response.content

    def citation_agent(self, content: str) -> List[Dict]:
        """Citation agent to gather relevant citations using Tavily and Firecrawl."""
        # Search using Tavily
        search_results = tavily_client.search(
            query=content, search_depth="advanced", max_results=5
        )

        citations = []
        if isinstance(search_results, dict) and "results" in search_results:
            for result in search_results["results"]:
                citations.append(
                    {
                        "source": result.get("url", ""),
                        "title": result.get("title", ""),
                        "content": result.get("content", ""),
                    }
                )
        return citations

    def writing_agent(self, outline: Dict, citations: List[Dict]) -> str:
        """Writing agent to generate the article."""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert content writer. Write an article based on the provided outline and citations.
            The article should be well-structured, engaging, and incorporate the citations naturally.
            
            Format the output in Markdown.
            
            Outline:
            {outline}
            
            Citations:
            {citations}""",
                ),
                ("human", "Please write the article."),
            ]
        )

        chain = prompt | self.llm
        response = chain.invoke({"outline": outline, "citations": citations})

        return response.content

    def seo_agent(self, article: str) -> str:
        """SEO agent to optimize the article."""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an SEO expert. Optimize the following article for search engines while maintaining its quality and readability.
            
            Tasks:
            1. Add relevant meta description
            2. Optimize headings and subheadings
            3. Ensure proper keyword placement
            4. Add internal linking suggestions
            5. Format the content for better readability
            
            Return the optimized article in Markdown format.""",
                ),
                ("human", "Please optimize this article: {article}"),
            ]
        )

        chain = prompt | self.llm
        response = chain.invoke({"article": article})

        return response.content


# Create the workflow graph
def create_workflow():
    generator = ArticleGenerator()

    def planning_node(state):
        content = state["content"]
        tone = state["tone"]
        length = state["length"]
        outline = generator.planning_agent(content, tone, length)
        return {**state, "outline": outline}

    def citation_node(state):
        content = state["content"]
        citations = generator.citation_agent(content)
        return {**state, "citations": citations}

    def writing_node(state):
        outline = state["outline"]
        citations = state.get("citations", [])
        article = generator.writing_agent(outline, citations)
        return {**state, "article": article}

    def seo_node(state):
        article = state["article"]
        optimized_article = generator.seo_agent(article)
        return {
            **state,
            "final_article": optimized_article.replace("```markdown", "").replace("```", ""),
        }

    # Define the workflow
    workflow = Graph()

    # Add nodes
    workflow.add_node("planning", planning_node)
    workflow.add_node("citation", citation_node)
    workflow.add_node("writing", writing_node)
    workflow.add_node("seo", seo_node)

    # Add edges
    workflow.add_edge("planning", "citation")
    workflow.add_edge("citation", "writing")
    workflow.add_edge("writing", "seo")

    # Set entry point
    workflow.set_entry_point("planning")

    # Set finish point
    workflow.set_finish_point("seo")

    return workflow.compile()


if __name__ == "__main__":
    workflow = create_workflow()
    result = workflow.invoke(
        {
            "content": "The future of AI",
            "tone": "technical",
            "length": 1000,
            "include_citations": True,
        },
        # debug=True
    )
    print(f"Final result: {json.dumps(result, indent=4)}")
    print("Article:\n", result["final_article"])