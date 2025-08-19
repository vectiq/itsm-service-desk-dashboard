import boto3
import json
import os
import logging
from typing import Dict, List, Optional
import streamlit as st
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedrockClient:
    """AWS Bedrock client for ITSM AI inference capabilities"""

    def __init__(self):
        """Initialize Bedrock client following AWS best practices"""
        self.region = os.getenv('AWS_REGION', 'us-east-1')

        # Get bearer token from environment (this contains the full auth info)
        self.bearer_token = os.getenv('AWS_BEARER_TOKEN_BEDROCK')

        if not self.bearer_token:
            st.error("AWS_BEARER_TOKEN_BEDROCK not found in .env file")
            self.available = False
            return

        try:
            # The bearer token might be a base64 encoded credential or session token
            # Let's try different approaches based on AWS documentation

            # Approach 1: Try using bearer token as session token
            try:
                session = boto3.Session()
                self.bedrock_client = session.client(
                    'bedrock',
                    region_name=self.region,
                    aws_session_token=self.bearer_token
                )

                self.bedrock_runtime = session.client(
                    'bedrock-runtime',
                    region_name=self.region,
                    aws_session_token=self.bearer_token
                )

            except Exception as e1:
                logger.warning(f"Session token approach failed: {str(e1)}")

                # Approach 2: Try decoding bearer token if it's base64
                try:
                    import base64
                    decoded_token = base64.b64decode(self.bearer_token).decode('utf-8')

                    # If it contains credentials, parse them
                    if ':' in decoded_token:
                        parts = decoded_token.split(':')
                        if len(parts) >= 2:
                            access_key = parts[0]
                            secret_key = ':'.join(parts[1:])  # In case secret contains ':'

                            self.bedrock_client = boto3.client(
                                'bedrock',
                                region_name=self.region,
                                aws_access_key_id=access_key,
                                aws_secret_access_key=secret_key
                            )

                            self.bedrock_runtime = boto3.client(
                                'bedrock-runtime',
                                region_name=self.region,
                                aws_access_key_id=access_key,
                                aws_secret_access_key=secret_key
                            )
                        else:
                            raise Exception("Invalid credential format in bearer token")
                    else:
                        raise Exception("Bearer token doesn't contain recognizable credentials")

                except Exception as e2:
                    logger.warning(f"Base64 decode approach failed: {str(e2)}")

                    # Approach 3: Try using bearer token directly as access key (fallback)
                    self.bedrock_client = boto3.client(
                        'bedrock',
                        region_name=self.region,
                        aws_access_key_id=self.bearer_token,
                        aws_secret_access_key=self.bearer_token  # Sometimes tokens work as both
                    )

                    self.bedrock_runtime = boto3.client(
                        'bedrock-runtime',
                        region_name=self.region,
                        aws_access_key_id=self.bearer_token,
                        aws_secret_access_key=self.bearer_token
                    )

            # Test connection and get available models
            self.foundation_models = self._list_foundation_models()
            self.available = True

        except Exception as e:
            st.error(f"Failed to initialize Bedrock client: {str(e)}")
            logger.error(f"Bedrock initialization failed: {str(e)}")
            self.available = False
            self.foundation_models = []
    
    def is_available(self) -> bool:
        """Check if Bedrock client is available"""
        return getattr(self, 'available', False)

    def _list_foundation_models(self) -> List[Dict]:
        """
        Gets a list of available Amazon Bedrock foundation models.
        Following AWS guide implementation.
        """
        try:
            response = self.bedrock_client.list_foundation_models()
            models = response["modelSummaries"]
            logger.info("Got %s foundation models.", len(models))
            return models
        except ClientError as e:
            logger.error("Couldn't list foundation models: %s", str(e))
            st.error(f"Could not list foundation models: {str(e)}")
            return []
        except Exception as e:
            logger.error("Unexpected error listing models: %s", str(e))
            st.error(f"Unexpected error: {str(e)}")
            return []
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available model IDs and their display names from AWS"""
        models_dict = {}

        # Get inference profiles first
        inference_profiles = self._list_inference_profiles()
        profile_models = {}
        for profile in inference_profiles:
            profile_id = profile.get('inferenceProfileId', '')
            profile_name = profile.get('inferenceProfileName', profile_id)
            models = profile.get('models', [])

            # Filter out profiles that don't match our region
            if profile_id and models:
                # Skip APAC profiles if we're in US region
                if self.region == 'us-east-1' and profile_id.startswith('apac.'):
                    continue
                # Skip EU profiles if we're in US region
                if self.region == 'us-east-1' and profile_id.startswith('eu.'):
                    continue
                # Only include US profiles for US region
                if self.region == 'us-east-1' and not profile_id.startswith('us.'):
                    continue

                model_name = models[0].get('modelId', profile_name)
                profile_models[profile_id] = f"{profile_name} (Profile)"

        # Add inference profiles first (preferred)
        models_dict.update(profile_models)

        # Then add foundation models
        for model in self.foundation_models:
            model_id = model.get('modelId', '')
            model_name = model.get('modelName', model_id)

            # Only include models that support text generation
            if self._supports_text_generation(model):
                # Don't duplicate if we already have this as an inference profile
                if not any(model_id in profile_id for profile_id in profile_models.keys()):
                    models_dict[model_id] = model_name

        return models_dict

    def test_model(self, model_id: str) -> bool:
        """Test if a model is actually working"""
        try:
            test_prompt = "Hello"
            response = self.invoke_model(test_prompt, model_id, 10, 0.1)
            return response is not None and len(response.strip()) > 0
        except Exception as e:
            logger.warning(f"Model {model_id} test failed: {str(e)}")
            return False

    def get_working_models(self) -> Dict[str, str]:
        """Get only models that actually work in this region"""
        all_models = self.get_available_models()
        working_models = {}

        for model_id, model_name in all_models.items():
            if self.test_model(model_id):
                working_models[model_id] = model_name
            else:
                logger.warning(f"Model {model_id} ({model_name}) failed test, excluding")

        return working_models

    def _supports_text_generation(self, model: Dict) -> bool:
        """Check if model supports text generation"""
        # Check if model supports text input/output
        input_modalities = model.get('inputModalities', [])
        output_modalities = model.get('outputModalities', [])

        return 'TEXT' in input_modalities and 'TEXT' in output_modalities

    def get_foundation_models(self) -> List[Dict]:
        """Get raw foundation models list for debugging"""
        return self.foundation_models

    def get_model_details(self, model_id: str) -> Optional[Dict]:
        """Get detailed information about a specific model"""
        for model in self.foundation_models:
            if model.get('modelId') == model_id:
                return model
        return None

    def _get_inference_profile_id(self, model_id: str) -> str:
        """
        Convert model ID to inference profile ID if needed.
        Some models require inference profiles for on-demand throughput.
        """
        # Check if this model needs an inference profile
        if "anthropic.claude" in model_id:
            # Try US inference profile for Claude models
            if not model_id.startswith("us."):
                inference_profile_id = f"us.{model_id}"
                logger.info(f"Converting {model_id} to inference profile: {inference_profile_id}")
                return inference_profile_id

        elif "amazon.nova" in model_id:
            # Try US inference profile for Nova models
            if not model_id.startswith("us."):
                inference_profile_id = f"us.{model_id}"
                logger.info(f"Converting {model_id} to inference profile: {inference_profile_id}")
                return inference_profile_id

        # Return original model ID if no conversion needed
        return model_id

    def _list_inference_profiles(self) -> List[Dict]:
        """List available inference profiles"""
        try:
            response = self.bedrock_client.list_inference_profiles()
            profiles = response.get("inferenceProfileSummaries", [])
            logger.info("Got %s inference profiles.", len(profiles))
            return profiles
        except Exception as e:
            logger.warning(f"Could not list inference profiles: {str(e)}")
            return []

    def invoke_model(self, prompt: str, model_id: str, max_tokens: int = 1000, temperature: float = 0.7, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Invoke any supported model for text generation.
        Uses Converse API when available, falls back to InvokeModel.
        Automatically tries inference profiles if direct model ID fails.

        Args:
            prompt: Input prompt for the model
            model_id: The specific model ID to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            system_prompt: Optional system prompt to prepend

        Returns:
            Generated text response or None if error
        """
        if not self.is_available():
            return None

        # Combine system prompt with user prompt if provided
        final_prompt = prompt
        if system_prompt:
            final_prompt = f"{system_prompt}\n\n{prompt}"

        # Try with original model ID first
        for attempt_model_id in [model_id, self._get_inference_profile_id(model_id)]:
            # Try Converse API first (preferred)
            try:
                return self._invoke_with_converse(final_prompt, attempt_model_id, max_tokens, temperature, system_prompt)
            except Exception as e:
                logger.warning(f"Converse API failed for {attempt_model_id}: {str(e)}")

            # Fall back to InvokeModel API
            try:
                return self._invoke_with_native_api(final_prompt, attempt_model_id, max_tokens, temperature)
            except Exception as e:
                logger.warning(f"Native API failed for {attempt_model_id}: {str(e)}")

                # If this was a ValidationException about inference profiles, try the next ID
                if "inference profile" in str(e) and attempt_model_id == model_id:
                    logger.info(f"Trying inference profile for {model_id}")
                    continue

        st.error(f"Error invoking model {model_id}: All attempts failed")
        return None

    def _invoke_with_converse(self, prompt: str, model_id: str, max_tokens: int, temperature: float, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Use the Converse API (preferred method following AWS guide)
        """
        try:
            conversation = [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ]

            # Prepare converse parameters
            converse_params = {
                "modelId": model_id,
                "messages": conversation,
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": 0.9
                },
            }

            # Add system prompt if provided (Converse API supports this properly)
            if system_prompt:
                converse_params["system"] = [{"text": system_prompt}]

            response = self.bedrock_runtime.converse(**converse_params)

            # Extract response text
            response_text = response["output"]["message"]["content"][0]["text"]
            return response_text.strip()

        except ClientError as e:
            logger.error(f"Converse API error for {model_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Converse API: {str(e)}")
            raise

    def _invoke_with_native_api(self, prompt: str, model_id: str, max_tokens: int, temperature: float) -> Optional[str]:
        """
        Use the native InvokeModel API (fallback method)
        """
        try:
            # Determine the correct request format based on model family
            if "anthropic.claude" in model_id:
                return self._invoke_claude_native(prompt, model_id, max_tokens, temperature)
            elif "amazon.titan" in model_id:
                return self._invoke_titan_native(prompt, model_id, max_tokens, temperature)
            elif "amazon.nova" in model_id:
                return self._invoke_nova_native(prompt, model_id, max_tokens, temperature)
            else:
                # Try generic approach
                return self._invoke_generic_native(prompt, model_id, max_tokens, temperature)

        except Exception as e:
            logger.error(f"Native API error for {model_id}: {str(e)}")
            raise

    def _invoke_claude_native(self, prompt: str, model_id: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Invoke Claude models using native API"""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType='application/json'
            )

            response_body = json.loads(response['body'].read())
            return response_body.get('content', [{}])[0].get('text', '').strip()

        except Exception as e:
            logger.error(f"Claude native API error: {str(e)}")
            raise

    def _invoke_titan_native(self, prompt: str, model_id: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Invoke Titan models using native API (following AWS guide)"""
        try:
            native_request = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                    "topP": 0.9
                },
            }

            request = json.dumps(native_request)

            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=request
            )

            model_response = json.loads(response["body"].read())
            response_text = model_response["results"][0]["outputText"]
            return response_text.strip()

        except Exception as e:
            logger.error(f"Titan native API error: {str(e)}")
            raise

    def _invoke_nova_native(self, prompt: str, model_id: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Invoke Nova models using native API"""
        try:
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                    "topP": 0.9
                }
            }

            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType='application/json'
            )

            response_body = json.loads(response['body'].read())
            return response_body.get('results', [{}])[0].get('outputText', '').strip()

        except Exception as e:
            logger.error(f"Nova native API error: {str(e)}")
            raise

    def _invoke_generic_native(self, prompt: str, model_id: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Generic fallback for unknown model types"""
        try:
            # Try Titan format first
            return self._invoke_titan_native(prompt, model_id, max_tokens, temperature)
        except:
            # Try Claude format
            return self._invoke_claude_native(prompt, model_id, max_tokens, temperature)

    def invoke_claude(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """
        Legacy method - invoke first available Claude model
        """
        available_models = self.get_available_models()
        claude_models = [mid for mid in available_models.keys() if "claude" in mid.lower()]

        if claude_models:
            return self.invoke_model(prompt, claude_models[0], max_tokens, temperature)
        else:
            st.error("No Claude models available")
            return None
    
    def invoke_titan(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """
        Invoke Amazon Titan model for text generation
        
        Args:
            prompt: Input prompt for the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Generated text response or None if error
        """
        if not self.is_available():
            return None
        
        try:
            # Prepare request body for Titan
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                    "topP": 0.9,
                    "stopSequences": []
                }
            }
            
            response = self.bedrock_client.invoke_model(
                modelId='amazon.titan-text-express-v1',  # Adjust model ID as needed
                body=json.dumps(body),
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            return response_body.get('results', [{}])[0].get('outputText', '').strip()
            
        except Exception as e:
            st.error(f"Error invoking Titan: {str(e)}")
            return None
    
    def classify_incident_priority(self, title: str, description: str) -> Dict[str, str]:
        """
        UC-02: Classify incident priority using AI

        Args:
            title: Incident title
            description: Incident description

        Returns:
            Dictionary with priority and reasoning
        """
        prompt = f"""
        You are an ITSM expert. Analyze this incident and determine its priority level.

        Incident Title: {title}
        Incident Description: {description}

        Priority Levels:
        - P1: Critical - System down, major business impact
        - P2: High - Significant impact, workaround available
        - P3: Medium - Moderate impact, standard response
        - P4: Low - Minor impact, can be scheduled

        Respond with:
        Priority: [P1/P2/P3/P4]
        Reasoning: [Brief explanation]
        """

        # Use first available model for classification
        available_models = self.get_available_models()
        if not available_models:
            return {"priority": "P3", "reasoning": "No models available"}

        model_id = list(available_models.keys())[0]
        response = self.invoke_model(prompt, model_id, max_tokens=200, temperature=0.3)

        if response:
            lines = response.split('\n')
            priority = "P3"  # Default
            reasoning = "Unable to determine"

            for line in lines:
                if line.startswith('Priority:'):
                    priority = line.split(':')[1].strip()
                elif line.startswith('Reasoning:'):
                    reasoning = line.split(':', 1)[1].strip()

            return {"priority": priority, "reasoning": reasoning}

        return {"priority": "P3", "reasoning": "AI classification failed"}
    
    def generate_kb_article(self, incident_cluster: List[Dict]) -> Dict[str, str]:
        """
        UC-21: Generate KB article from incident cluster
        
        Args:
            incident_cluster: List of similar incidents
            
        Returns:
            Dictionary with title, content, and tags
        """
        # Prepare incident summaries
        incident_summaries = []
        for incident in incident_cluster[:5]:  # Limit to 5 incidents
            summary = f"- {incident.get('short_description', 'No description')}"
            if incident.get('resolution_notes'):
                summary += f" (Resolved: {incident['resolution_notes']})"
            incident_summaries.append(summary)
        
        incidents_text = '\n'.join(incident_summaries)
        
        prompt = f"""
        You are a technical writer creating knowledge base articles for IT support.
        
        Based on these similar incidents, create a comprehensive KB article:
        
        {incidents_text}
        
        Create a KB article with:
        1. Title: Clear, searchable title
        2. Problem: What issue users experience
        3. Solution: Step-by-step resolution
        4. Tags: Relevant keywords for search
        
        Format your response as:
        Title: [Article title]
        Problem: [Problem description]
        Solution: [Step-by-step solution]
        Tags: [comma-separated tags]
        """
        
        # Use first available model for KB generation
        available_models = self.get_available_models()
        if not available_models:
            return {"title": "Generated Article", "problem": "", "solution": "", "tags": ""}

        model_id = list(available_models.keys())[0]
        response = self.invoke_model(prompt, model_id, max_tokens=800, temperature=0.5)
        
        if response:
            sections = {"title": "", "problem": "", "solution": "", "tags": ""}
            current_section = None
            
            for line in response.split('\n'):
                if line.startswith('Title:'):
                    sections['title'] = line.split(':', 1)[1].strip()
                elif line.startswith('Problem:'):
                    sections['problem'] = line.split(':', 1)[1].strip()
                    current_section = 'problem'
                elif line.startswith('Solution:'):
                    sections['solution'] = line.split(':', 1)[1].strip()
                    current_section = 'solution'
                elif line.startswith('Tags:'):
                    sections['tags'] = line.split(':', 1)[1].strip()
                    current_section = None
                elif current_section and line.strip():
                    sections[current_section] += ' ' + line.strip()
            
            return sections
        
        return {"title": "Generated Article", "problem": "", "solution": "", "tags": ""}
    
    def recommend_agent_assignment(self, incident: Dict, available_agents: List[Dict]) -> Dict:
        """
        UC-31: Recommend best agent for incident assignment
        
        Args:
            incident: Incident details
            available_agents: List of available agents with skills/capacity
            
        Returns:
            Dictionary with recommended agent and reasoning
        """
        # Prepare agent information
        agent_info = []
        for agent in available_agents[:10]:  # Limit to 10 agents
            skills = agent.get('skills', [])
            capacity = agent.get('current_capacity', 'Unknown')
            performance = agent.get('performance_score', 'Unknown')
            
            agent_summary = f"- {agent.get('name', 'Unknown')}: Skills: {', '.join(skills)}, Capacity: {capacity}, Performance: {performance}"
            agent_info.append(agent_summary)
        
        agents_text = '\n'.join(agent_info)
        
        prompt = f"""
        You are an ITSM assignment specialist. Recommend the best agent for this incident.
        
        Incident Details:
        - Title: {incident.get('short_description', 'No title')}
        - Category: {incident.get('category_name', 'Unknown')}
        - Priority: {incident.get('priority', 'Unknown')}
        - Required Skills: {incident.get('required_skills', 'None specified')}
        
        Available Agents:
        {agents_text}
        
        Consider:
        1. Skill match for the incident type
        2. Current capacity/workload
        3. Performance history
        4. Priority level urgency
        
        Respond with:
        Recommended Agent: [Agent name]
        Reasoning: [Why this agent is best suited]
        Confidence: [High/Medium/Low]
        """
        
        # Use first available model for agent assignment
        available_models = self.get_available_models()
        if not available_models:
            return {"agent": "No recommendation", "reasoning": "No models available", "confidence": "Low"}

        model_id = list(available_models.keys())[0]
        response = self.invoke_model(prompt, model_id, max_tokens=300, temperature=0.3)
        
        if response:
            lines = response.split('\n')
            agent = "No recommendation"
            reasoning = "Unable to determine"
            confidence = "Low"
            
            for line in lines:
                if line.startswith('Recommended Agent:'):
                    agent = line.split(':', 1)[1].strip()
                elif line.startswith('Reasoning:'):
                    reasoning = line.split(':', 1)[1].strip()
                elif line.startswith('Confidence:'):
                    confidence = line.split(':', 1)[1].strip()
            
            return {"agent": agent, "reasoning": reasoning, "confidence": confidence}
        
        return {"agent": "No recommendation", "reasoning": "AI assignment failed", "confidence": "Low"}

# Global instance
bedrock_client = BedrockClient()
