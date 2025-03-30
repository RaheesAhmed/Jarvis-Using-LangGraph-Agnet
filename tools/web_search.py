from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Check if TAVILY_API_KEY is set
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    print("Warning: TAVILY_API_KEY is not set. Web search functionality will not work.")

try:
    # Initialize the search tool with max_results set to 2
    search_on_web = TavilySearchResults(max_results=2)
    
    @tool
    def search_on_web_tool(query: str) -> str:
        """
        Search the web for information about a specific query.
        
        Args:
            query: The search term to look up on the web. Be specific for better results.
            
        Returns:
            Relevant information from web search results.
        """
        try:
            return search_on_web.invoke(query)
        except Exception as e:
            return f"Error searching the web: {str(e)}"
            
except Exception as e:
    print(f"Error initializing web search tool: {str(e)}")
    
    @tool
    def search_on_web_tool(query: str) -> str:
        """
        Search the web for information about a specific query.
        
        Args:
            query: The search term to look up on the web. Be specific for better results.
            
        Returns:
            Relevant information from web search results.
        """
        return "Web search is currently unavailable. Please check your Tavily API key."



