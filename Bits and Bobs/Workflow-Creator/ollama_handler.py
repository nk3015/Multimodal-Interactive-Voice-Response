import re
import json
import logging

# Check if Ollama is installed
try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False
    print("Ollama not found. Some features will be disabled.")

class OllamaHandler:
    """Handler for Ollama model interactions"""
    
    @staticmethod
    async def get_available_models():
        """Get list of available Ollama models"""
        try:
            result = await ollama.list()
            if 'models' in result:
                return [model['name'] for model in result['models']]
            return []
        except Exception as e:
            logging.error(f"Error getting Ollama models: {e}")
            return []

    @staticmethod
    def predict_next_node(current_node, input_text, workflow_data, model, conversation=None):
        """Predict the most likely next node based on user input using Ollama"""
        if not HAS_OLLAMA:
            return current_node.get('outputs', [])[0] if current_node.get('outputs', []) else None
            
        try:
            # Get possible next nodes
            outputs = current_node.get('outputs', [])
            next_nodes = []
            
            for output in outputs:
                node = next((n for n in workflow_data.get('nodes', []) if n.get('id') == output), None)
                if node:
                    next_nodes.append(node)
                    
            if not next_nodes:
                return outputs[0] if outputs else None
                
            # Create prompt for intent classification
            context = ""
            if conversation:
                # Format conversation history
                context = "Conversation history:\n"
                for msg in conversation[-3:]:  # Only include last 3 messages for brevity
                    role = "Bot" if msg["role"] == "assistant" else "User"
                    context += f"{role}: {msg['content']}\n"
                    
            prompt = f"""{context}
            Current node: {current_node.get('title', current_node.get('id'))}: {current_node.get('content', '')}
            
            Based on the user message, which of the following nodes should we transition to?

            User message: "{input_text}"
            
            Options:
            """
            
            for i, node in enumerate(next_nodes):
                prompt += f"{i+1}. {node.get('title', node.get('id'))}: {node.get('content', '')}\n"
                
            prompt += "\nReturn only the number of the best matching node."
            
            # Call Ollama
            response = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            if response and 'message' in response and 'content' in response['message']:
                content = response['message']['content']
                
                # Try to extract the number from the response
                match = re.search(r'(\d+)', content)
                if match:
                    index = int(match.group(1)) - 1
                    if 0 <= index < len(next_nodes):
                        return next_nodes[index].get('id')
                        
            return outputs[0]
            
        except Exception as e:
            print(f"Error predicting next node: {e}")
            return outputs[0] if outputs else None
    
    @staticmethod
    def extract_entities_for_test(input_text, entities, model):
        """Extract entities from user input for testing"""
        if not HAS_OLLAMA:
            return {}
            
        try:
            # Create prompt for entity extraction
            prompt = f"""Extract the following entities from the user message: {', '.join(entities)}
            
            User message: "{input_text}"
            
            Return a JSON object with the extracted entities, or null if not found.
            For example: {{"entity1": "value1", "entity2": "value2"}}
            """
            
            # Call Ollama
            response = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            if response and 'message' in response and 'content' in response['message']:
                content = response['message']['content']
                
                # Try to extract JSON from the response
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content
                    
                try:
                    extracted = json.loads(json_str)
                    if isinstance(extracted, dict):
                        # Filter to only requested entities
                        return {k: v for k, v in extracted.items() if k in entities and v}
                except json.JSONDecodeError:
                    pass
                    
            return {}
            
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return {}
    
    @staticmethod
    def extract_entities_with_ollama(message, required_entities):
        """Extract entities from user message using Ollama"""
        try:
            # Create prompt for entity extraction
            prompt = f"""Extract the following entities from the user message: {', '.join(required_entities)}
            
            User message: "{message}"
            
            Return a JSON object with the extracted entities, or null if not found.
            For example: {{"entity1": "value1", "entity2": "value2"}}
            """
            
            # Call Ollama
            response = ollama.chat(
                model="llama3",  # use default model
                messages=[{"role": "user", "content": prompt}]
            )
            
            if response and 'message' in response and 'content' in response['message']:
                content = response['message']['content']
                
                # Try to extract JSON from the response
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content
                    
                try:
                    extracted = json.loads(json_str)
                    if isinstance(extracted, dict):
                        # Return only valid entities
                        return {entity: value for entity, value in extracted.items() 
                                if entity in required_entities and value}
                except json.JSONDecodeError:
                    return {}
            
            return {}
                
        except Exception as e:
            print(f"Error extracting entities with Ollama: {e}")
            return {}
    
    @staticmethod
    def classify_intent_with_ollama(message, outputs, workflow_data):
        """Classify user intent using Ollama to determine next node"""
        try:
            # Get possible next nodes
            next_nodes = []
            for output in outputs:
                node = next((n for n in workflow_data.get('nodes', []) if n.get('id') == output), None)
                if node:
                    next_nodes.append(node)
            
            if not next_nodes:
                return outputs[0] if outputs else None
                
            # Create prompt for intent classification
            prompt = f"""Based on the user message, which of the following intents is the most likely match?

            User message: "{message}"
            
            Options:
            """
            
            for i, node in enumerate(next_nodes):
                prompt += f"{i+1}. {node.get('title', node.get('id'))}: {node.get('content', '')}\n"
                
            prompt += "\nReturn only the number of the matching intent."
            
            # Call Ollama
            response = ollama.chat(
                model="llama3",  # use default model
                messages=[{"role": "user", "content": prompt}]
            )
            
            if response and 'message' in response and 'content' in response['message']:
                content = response['message']['content']
                
                # Try to extract the number from the response
                match = re.search(r'(\d+)', content)
                if match:
                    index = int(match.group(1)) - 1
                    if 0 <= index < len(next_nodes):
                        return next_nodes[index].get('id')
                        
            return outputs[0]
            
        except Exception as e:
            print(f"Error classifying intent with Ollama: {e}")
            return outputs[0] if outputs else None
