# agents/manual_agent.py
# Import the actual ManualSearchTool from your existing manual directory
from manual.manual_search_tool import ManualSearchTool

class ManualAgent:
    """
    Manual Agent: Searches technical manuals and troubleshooting procedures.
    """
    def __init__(self):
        self.name = "ManualAgent"
        self.manual_tool = ManualSearchTool() # Instantiate the tool once

    def search(self, user_query: str, top_k: int = 3) -> str:
        """
        Searches the manual knowledge base for information related to the user query.
        The user_query here refers to the specific detail needed for the Manual tool,
        derived from the original overall user input or the current plan step.
        """
        print(f"📖 {self.name}: Searching manuals for '{user_query}' (Top {top_k} results)...")
        try:
            search_results = self.manual_tool.search(user_query, top_k=top_k)
            formatted_results = []
            for i, res in enumerate(search_results, 1):
                content_preview = res['content'][:200] + "..." if len(res['content']) > 200 else res['content']
                source = res['metadata'].get('source', 'Unknown')
                formatted_results.append(f"{i}. {content_preview} (Source: {source})")

            result = "\n".join(formatted_results) if formatted_results else "No relevant information found."
            print(f"✅ {self.name}: Manual search successful.")
            return result
        except Exception as e:
            print(f"❌ {self.name}: Manual search error: {str(e)}")
            return f"Manual search error: {str(e)}"