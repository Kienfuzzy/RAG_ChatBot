from openai import OpenAI
import json
from datetime import datetime
from app.services.semantic_cache_service import semantic_cache
from app.services.query_processor import process_query


class QueryAgent:
    """ReAct agent with function calling"""
    
    def __init__(self, openai_client, qdrant_service, es_service, db_service=None):
        self.client = openai_client
        self.qdrant = qdrant_service
        self.es = es_service
        self.db = db_service
        self.model = "gpt-4o"
        self.tools = [
            {
                "type": "function",
                "name": "search_products",
                "description": "Search for products in the internal catalog using hybrid search. Use this for finding specific products we sell.",      
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query provided by the user."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of results to return.",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "type": "function",
                "name": "query_database",
                "description": "Query the structured product database for filtering by price, rating, brand, category, OR searching within product specs. Use for specific filters (under $100, rating above 4.5) or feature searches (USB-C, wireless, ANC, battery).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Product category (e.g., 'headphones', 'laptops', 'accessories')"
                        },
                        "min_price": {
                            "type": "number",
                            "description": "Minimum price filter"
                        },
                        "max_price": {
                            "type": "number",
                            "description": "Maximum price filter"
                        },
                        "brand": {
                            "type": "string",
                            "description": "Brand name filter"
                        },
                        "min_rating": {
                            "type": "number",
                            "description": "Minimum rating filter (0-5)"
                        },
                        "spec_search": {
                            "type": "string",
                            "description": "Search keyword in product specs (e.g., 'usb-c', 'wireless', 'anc', 'bluetooth', 'fast-charge')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "default": 10
                        }
                    }
                }
            },
            {
                "type": "web_search"
            }
        ]
    
    def search_products(self, query: str, limit: int = 5, qdrant_weight: float = 0.5, es_weight: float = 0.5):
        """
        Execute hybrid search with caching and weighted scoring.
        Uses same logic as /search-hybrid endpoint.
        """
        # Step 1: Check semantic cache first
        normalized_query = query.strip()
        cached_results = semantic_cache.get(normalized_query)
        
        if cached_results:
            return cached_results.get("results", [])
        
        # Step 2: Cache miss - process query
        cleaned_query, intent = process_query(normalized_query)
        
        # Step 3: Search both systems
        qdrant_results = self.qdrant.search(text=cleaned_query, limit=limit * 2) or []
        es_results = self.es.search(text=cleaned_query, top_k=limit * 2) or []
        
        # Step 4: Combine and rank using weighted scoring
        combined_results = {}
        
        # Add Qdrant results with weight
        for i, result in enumerate(qdrant_results):
            doc_id = result.get('document_id', '')
            chunk_idx = result.get('chunk_index', 0)
            key = f"{doc_id}_{chunk_idx}"
            
            normalized_score = (len(qdrant_results) - i) / len(qdrant_results) if qdrant_results else 0
            
            combined_results[key] = {
                'content': result.get('content', ''),
                'document_id': doc_id,
                'chunk_index': chunk_idx,
                'title': result.get('title', ''),
                'qdrant_score': normalized_score,
                'es_score': 0.0,
                'combined_score': normalized_score * qdrant_weight
            }
        
        # Add Elasticsearch results with weight
        for i, result in enumerate(es_results):
            doc_id = result['metadata'].get('document_id', '')
            chunk_idx = result['metadata'].get('chunk_index', 0)
            key = f"{doc_id}_{chunk_idx}"
            
            normalized_score = (len(es_results) - i) / len(es_results) if es_results else 0
            
            if key in combined_results:
                combined_results[key]['es_score'] = normalized_score
                combined_results[key]['combined_score'] += normalized_score * es_weight
            else:
                combined_results[key] = {
                    'content': result.get('content', ''),
                    'document_id': doc_id,
                    'chunk_index': chunk_idx,
                    'title': result['metadata'].get('title', ''),
                    'qdrant_score': 0.0,
                    'es_score': normalized_score,
                    'combined_score': normalized_score * es_weight
                }
        
        # Sort by combined score and return top K
        sorted_results = sorted(
            combined_results.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )[:limit]
        
        # Step 5: Cache results (10 minutes TTL)
        cache_data = {
            "query": query,
            "cleaned_query": cleaned_query,
            "intent": intent,
            "results": sorted_results,
            "total_found": len(sorted_results)
        }
        semantic_cache.set(normalized_query, cache_data, ttl=600)
        
        return sorted_results
    
    def query_database(self, category=None, min_price=None, max_price=None, 
                      brand=None, min_rating=None, spec_search=None, limit=10):
        """Query structured database with filters"""
        if not self.db:
            return {"error": "Database service not available"}
        
        try:
            results = self.db.query(
                category=category,
                min_price=min_price,
                max_price=max_price,
                brand=brand,
                min_rating=min_rating,
                spec_search=spec_search,
                limit=limit
            )
            return results
        except Exception as e:
            return {"error": f"Database query failed: {str(e)}"}
    
    def run(self, user_query: str, conversation_history: list = None):
        """
        ReAct loop using OpenAI Responses API:
        1. Build input with conversation history
        2. Call responses.create() with tools
        3. Execute tools when requested
        4. Return final answer with tool trace
        
        Args:
            user_query: Current user question
            conversation_history: Previous messages from ConversationMemory
        """
        # Build input list (conversation context)
        input_list = []
        
        # Add conversation history if provided
        if conversation_history:
            input_list.extend(conversation_history)
        
        # Add current user query
        input_list.append({"role": "user", "content": user_query})
        
        # Get current date
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Sales personality instructions with smart tool usage logic
        instructions = (
            f"Today's date is {current_date}. Use this for any time-related questions.\n\n"
            "You are a friendly, consultative sales assistant. Ask clarifying questions when needed.\n\n"
            "SYNONYMS (CRITICAL - Always map these):\n"
            "- computer = laptop\n"
            "- memory = RAM = ram\n"
            "- storage = SSD = HDD\n"
            "- display = screen\n"
            "- USB-C = Type-C = usb-c\n"
            "- wireless = bluetooth = BT\n"
            "- ANC = noise cancelling = active noise cancelling\n\n"
            "TOOL SELECTION:\n"
            "- search_products: General queries, brand names, product types\n"
            "- query_database: Price filters, rating filters, spec features, brand + filters\n"
            "  * When user says 'computer' → use category='laptops'\n"
            "  * When user mentions RAM/memory → use spec_search='ram' or spec_search='16gb'\n"
            "  * When user mentions storage → use spec_search='ssd' or spec_search='512gb'\n"
            "- web_search: Only when catalog exhausted\n\n"
            "FEATURE SEARCH:\n"
            "- Use query_database with spec_search parameter\n"
            "- Search for LOWERCASE keywords (e.g., 'ram', '16gb', 'usb-c')\n"
            "- Show ALL matching products, not just 1-2\n"
            "- Say 'I have found X products with [feature] in our catalog' before listing\n\n"
            "TOOL RULES:\n\n"
            "1. First query: Use appropriate tool based on query type. Show 2-3 products initially.\n\n"
            "2. When user asks for more/different options:\n"
            "   - Check history: What products already shown?\n"
            "   - CATALOG mode: Call tool again, show ONLY new products\n"
            "   - If no new catalog products: Switch to web_search → Say 'I've shown all catalog matches. Here are options found online:'\n"
            "   - WEB mode: Use web_search again → Say 'Here are more options found online:'\n\n"
            "3. If search returns empty: Use web_search → Say 'Not in our catalog, but here are options found online:'\n\n"
            "4. Web search MUST include clickable links for EVERY product.\n\n"
            "5. NEVER repeat products. NEVER invent data.\n\n"
            "FORMAT RULES (CRITICAL):\n"
            "- Always add spaces between sentences\n"
            "- Add line breaks between paragraphs\n"
            "- Always include links for web results on separate lines\n"
            "- NEVER use asterisks (*) anywhere in your response\n"
            "- NEVER use underscores (_) anywhere in your response\n"
            "- Use numbered lists (1., 2., 3.) or bullet points (- item) for product listings\n"
            "- Example good format:\n"
            "  'I couldn't find any in our catalog. Let me look online for you. Here are some excellent options under 100:'\n"
            "- Example bad format (NEVER DO THIS):\n"
            "  'catalog.Letmelookonline' or 'options*with*long*battery'"
        )
        
        tool_calls_made = []
        max_iterations = 5
        
        try:
            for iteration in range(max_iterations):
                # Call OpenAI Responses API
                response = self.client.responses.create(
                    model=self.model,
                    instructions=instructions,
                    tools=self.tools,
                    input=input_list,
                )
                
                # Save function call outputs for subsequent requests
                input_list += response.output
                
                # Check for function calls and execute them
                has_function_calls = False
                for item in response.output:
                    if item.type == "function_call":
                        has_function_calls = True
                        function_name = item.name
                        function_args = json.loads(item.arguments)
                        
                        # Execute tool
                        if function_name == "search_products":
                            result = self.search_products(**function_args)
                        elif function_name == "query_database":
                            result = self.query_database(**function_args)
                        else:
                            result = {"error": f"Unknown tool: {function_name}"}
                        
                        # Track tool usage
                        tool_calls_made.append({
                            "tool": function_name,
                            "args": function_args,
                            "result_count": len(result) if isinstance(result, list) else 1
                        })
                        
                        # Provide function call results to the model
                        input_list.append({
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(result)
                        })
                
                # If no function calls, we have the final answer
                if not has_function_calls:
                    return {
                        "answer": response.output_text if hasattr(response, 'output_text') else "",
                        "tool_calls": tool_calls_made,
                        "iterations": iteration + 1
                    }
            
            # If we hit max iterations, make one final call to get answer
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                tools=self.tools,
                input=input_list,
            )
            
            return {
                "answer": response.output_text if hasattr(response, 'output_text') else "I apologize, but I'm having trouble processing your request.",
                "tool_calls": tool_calls_made,
                "iterations": max_iterations
            }
            
        except Exception as e:
            return {
                "answer": f"Error processing request: {str(e)}",
                "tool_calls": tool_calls_made,
                "iterations": len(tool_calls_made),
                "error": str(e)
            }