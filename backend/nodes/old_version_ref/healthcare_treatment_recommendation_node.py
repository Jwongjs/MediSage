from adapters.local_model_adapter import LocalModelAdapter
from typing import Dict, Any, List, Optional
import googlemaps
import os
import asyncio
from functools import lru_cache
import hashlib

class HealthcareRecommendationNode:
    def __init__(self, adapter: LocalModelAdapter, google_maps_api_key: Optional[str] = None):
        self.adapter = adapter  # Fix: Add the missing adapter
        self.gmaps_client = googlemaps.Client(key=google_maps_api_key) if google_maps_api_key else None
        
        # Add caches for performance optimization
        self._facility_cache = {}  # Cache Google Maps results
        self._advice_cache = {}    # Cache LLM-generated advice
        
        # Define severity thresholds and specialist mappings
        self.severity_mapping = {
            "mild": "self_care",
            "moderate": "see_specialist", 
            "severe": "see_specialist",
            "critical": "emergency_care",
            "emergency": "emergency_care"
        }
        
        self.specialist_mapping = {
            # Skin conditions
            "melanoma": "dermatologist",
            "skin cancer": "dermatologist", 
            "basal cell carcinoma": "dermatologist",
            "dermatitis": "dermatologist",
            "rash": "dermatologist",
            "actinic keratoses": "dermatologist",
            "basal cell carcinoma": "dermatologist",
            "melanocytic nevi": "dermatologist",
            "dermatofibroma": "dermatologist",
            
            # Heart conditions
            "chest pain": "cardiologist",
            "heart": "cardiologist",
            "cardiac": "cardiologist",
            
            # Neurological conditions
            "headache": "neurologist",
            "migraine": "neurologist",
            "neurological": "neurologist",
            
            # General conditions
            "infection": "general_practitioner",
            "fever": "general_practitioner",
            "cold": "general_practitioner",
            "flu": "general_practitioner",
        }

        # Pre-computed self-care advice templates for performance
        self.self_care_templates = {
            "rash": [
                "Keep the affected area clean and dry",
                "Apply a cool, damp cloth to reduce itching",
                "Avoid scratching the rash",
                "Use fragrance-free moisturizers",
                "Seek medical attention if rash spreads or worsens"
            ],
            "headache": [
                "Rest in a quiet, dark room",
                "Apply cold or warm compress to head or neck",
                "Stay hydrated with water",
                "Consider over-the-counter pain relievers as directed",
                "Track headache patterns and triggers"
            ],
            "fever": [
                "Get plenty of rest",
                "Stay hydrated with water and clear fluids",
                "Use fever-reducing medications as directed",
                "Dress in lightweight clothing",
                "Seek medical attention if fever exceeds 103°F (39.4°C)"
            ],
            "chest pain": [
                "Stop any physical activity immediately",
                "Sit down and rest",
                "Take prescribed medications if available (e.g., nitroglycerin)",
                "Call emergency services if pain is severe or persistent",
                "Monitor symptoms closely"
            ],
            "skin lesion": [
                "Avoid picking or scratching the lesion",
                "Keep the area clean and dry",
                "Protect from sun exposure",
                "Monitor for changes in size, color, or shape",
                "Schedule dermatologist appointment for evaluation"
            ]
        }
    
    async def __call__(self, state):
        return await self.generate_healthcare_recommendation(state)
    
    async def generate_healthcare_recommendation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate healthcare recommendations based on overall analysis"""
        try:
            # Get the best available analysis (prioritizes overall analysis)
            analysis = self._get_analysis_for_recommendation(state)
            
            if not analysis:
                state["healthcare_recommendation"] = self._get_default_recommendation()
                state["current_workflow_stage"] = "recommendation_error"
                return state
            
            diagnosis = analysis.get("text_diagnosis", "Unknown")
            severity = analysis.get("severity", "unknown").lower()
            confidence = analysis.get("diagnosis_confidence", 0.0)
            guidance = analysis.get("recommendation_guidance", "standard_care_recommended")
            
            # Enhanced recommendation logic using overall analysis guidance
            recommendation_type = self._determine_recommendation_type(diagnosis, severity, confidence, guidance)
            
            # Initialize recommendation result structure
            recommendation_result = {
                "recommendation_type": recommendation_type,
                "self_care_advice": None,
                "specialist_type": None,
                "nearby_facilities": None,
                "rag_evidence": None
            }
            
            # Generate specific recommendations based on type
            if recommendation_type == "self_care":
                recommendation_result["self_care_advice"] = await self._generate_self_care_advice(
                    diagnosis, severity
                )
                
            elif recommendation_type == "see_specialist":
                specialist_type = self._determine_specialist_type(diagnosis)
                recommendation_result["specialist_type"] = specialist_type
                
                # Run facility search and evidence gathering in parallel for performance
                tasks = []
                
                if state.get("user_location") and self.gmaps_client:
                    tasks.append(self._find_nearby_facilities(state["user_location"], specialist_type))
                
                tasks.append(self._get_rag_evidence(diagnosis))
                
                # Wait for all tasks to complete
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    result_idx = 0
                    if state.get("user_location") and self.gmaps_client:
                        recommendation_result["nearby_facilities"] = results[result_idx] if not isinstance(results[result_idx], Exception) else []
                        result_idx += 1
                    
                    recommendation_result["rag_evidence"] = results[result_idx] if not isinstance(results[result_idx], Exception) else []
                
            elif recommendation_type == "emergency_care":
                # Find nearest emergency rooms
                if state.get("user_location") and self.gmaps_client:
                    recommendation_result["nearby_facilities"] = await self._find_emergency_facilities(
                        state["user_location"]
                    )
            
            state["healthcare_recommendation"] = recommendation_result
            state["current_workflow_stage"] = "generating_report"
            
        except Exception as e:
            state["healthcare_recommendation"] = self._get_default_recommendation()
            state["current_workflow_stage"] = "recommendation_error"
        
        return state
    


    def _get_analysis_for_recommendation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get the best available analysis for making recommendations"""
        
        # Prioritize overall analysis if available
        if state.get("overall_analysis"):
            overall = state["overall_analysis"]
            return {
                "text_diagnosis": overall.get("final_diagnosis", "Unknown"),
                "diagnosis_confidence": overall.get("final_confidence", 0.0),
                "severity": overall.get("final_severity", "unknown"),
                "reasoning": overall.get("integration_notes", ""),
                "recommendation_guidance": overall.get("recommendation_guidance", "standard_care_recommended")
            }
        
        # Fall back to individual analyses
        return self._get_primary_analysis(state)

    def _get_primary_analysis(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the most relevant analysis (follow-up if available, otherwise original)"""
        if state.get("followup_analysis"):
            return state["followup_analysis"]
        return state.get("textual_analysis")
    
    def _get_default_recommendation(self):
        """Default recommendation for error cases"""
        return {
            "recommendation_type": "see_specialist",
            "self_care_advice": ["Consult with a healthcare professional for proper diagnosis"],
            "specialist_type": "general_practitioner",
            "nearby_facilities": [],
            "rag_evidence": []
        }

    def _determine_recommendation_type(self, diagnosis: str, severity: str, confidence: float, guidance: str = "") -> str:
        """Enhanced recommendation logic using overall analysis guidance"""
        
        # Use overall analysis guidance first (highest priority)
        if guidance == "urgent_care_recommended":
            return "emergency_care"
        elif guidance == "specialist_consultation_recommended":
            return "see_specialist"
        elif guidance == "self_care_appropriate":
            return "self_care"
        elif guidance == "monitoring_recommended":
            return "see_specialist"  # Better safe than sorry
        
        # Check for emergency keywords in diagnosis
        emergency_keywords = ["heart attack", "stroke", "severe bleeding", "difficulty breathing", "chest pain"]
        if any(keyword in diagnosis.lower() for keyword in emergency_keywords):
            return "emergency_care"
        
        # Fall back to severity-based logic
        if severity in self.severity_mapping:
            return self.severity_mapping[severity]
        
        # Low confidence cases should see a specialist for safety
        if confidence < 0.4:
            return "see_specialist"
        
        # Default to self-care for mild/unknown cases
        return "self_care"
    
    def _determine_specialist_type(self, diagnosis: str) -> str:
        """Determine appropriate specialist based on diagnosis"""
        diagnosis_lower = diagnosis.lower()
        
        for condition, specialist in self.specialist_mapping.items():
            if condition in diagnosis_lower:
                return specialist
        
        return "general_practitioner"  # Default
    
    @lru_cache(maxsize=100)
    def _cache_key(self, *args) -> str:
        """Generate cache key from arguments"""
        return hashlib.md5(str(args).encode()).hexdigest()
    
    async def _generate_self_care_advice(self, diagnosis: str, severity: str) -> List[str]:
        """Generate self-care advice with template fallback for performance"""
        diagnosis_lower = diagnosis.lower()
        
        # Check for template match first (fastest)
        for condition, advice in self.self_care_templates.items():
            if condition in diagnosis_lower:
                return advice
        
        # Check cache for previously generated advice
        cache_key = self._cache_key(diagnosis, severity)
        if cache_key in self._advice_cache:
            return self._advice_cache[cache_key]
        
        # Fall back to LLM generation for unknown conditions
        try:
            prompt = f"""
            Generate specific self-care advice for a patient with: {diagnosis}
            Severity: {severity}
            
            Provide 5-7 practical, actionable self-care recommendations.
            Focus on:
            1. Immediate relief measures
            2. Lifestyle modifications
            3. When to seek medical attention
            4. What to avoid
            
            Format as a bulleted list.
            """
            
            advice_text = await self.adapter.generate_self_care_advice(prompt)
            advice_list = self._parse_advice_list(advice_text)
            
            # Cache the result
            self._advice_cache[cache_key] = advice_list
            return advice_list
            
        except Exception:
            # Fallback advice
            fallback_advice = [
                "Rest and avoid strenuous activities",
                "Stay hydrated by drinking plenty of water",
                "Monitor your symptoms closely",
                "Seek medical attention if symptoms worsen",
                "Follow up with your healthcare provider"
            ]
            self._advice_cache[cache_key] = fallback_advice
            return fallback_advice
    
    async def _find_nearby_facilities(self, location: Dict[str, float], specialist_type: str) -> List[Dict[str, str]]:
        """Find nearby healthcare facilities with caching"""
        cache_key = self._cache_key(location["lat"], location["lng"], specialist_type)
        
        # Check cache first
        if cache_key in self._facility_cache:
            return self._facility_cache[cache_key]
        
        if not self.gmaps_client:
            return []
        
        try:
            # Map specialist types to search queries
            search_queries = {
                "dermatologist": "dermatologist near me",
                "cardiologist": "cardiologist near me", 
                "neurologist": "neurologist near me",
                "general_practitioner": "family doctor near me"
            }
            
            query = search_queries.get(specialist_type, "clinic near me")
            
            # Search for places
            places_result = self.gmaps_client.places_nearby(
                location=(location["lat"], location["lng"]),
                radius=10000,  # 10km radius
                type="hospital",
                keyword=query
            )
            
            facilities = []
            for place in places_result.get("results", [])[:5]:  # Limit to 5 results
                facility = {
                    "name": place.get("name", "Unknown"),
                    "address": place.get("vicinity", "Address not available"),
                    "rating": str(place.get("rating", "No rating")),
                    "phone": place.get("formatted_phone_number", ""),
                    "distance": self._calculate_distance(location, place.get("geometry", {}).get("location", {}))
                }
                facilities.append(facility)
            
            # Cache the result
            self._facility_cache[cache_key] = facilities
            return facilities
            
        except Exception as e:
            return []
        
    async def _get_rag_evidence(self, diagnosis: str) -> List[str]:
        """Get supporting evidence from RAG system"""
        try:
            # Use the adapter's RAG capabilities if available
            if hasattr(self.adapter, 'retrieve_medical_evidence'):
                evidence = await self.adapter.retrieve_medical_evidence(diagnosis)
                return evidence[:3]  # Limit to 3 pieces of evidence
            else:
                # Fallback: Generate evidence-based recommendations
                prompt = f"""
                Provide 2-3 evidence-based medical recommendations for: {diagnosis}
                Include references to medical guidelines or studies where appropriate.
                Keep each recommendation to 1-2 sentences.
                """
                evidence_text = await self.adapter.generate_medical_evidence(prompt)
                return self._parse_evidence_list(evidence_text)
                
        except Exception:
            return []
    
    async def _find_emergency_facilities(self, location: Dict[str, float]) -> List[Dict[str, str]]:
        """Find nearest emergency rooms"""
        if not self.gmaps_client:
            return []
        
        try:
            places_result = self.gmaps_client.places_nearby(
                location=(location["lat"], location["lng"]),
                radius=15000,  # 15km radius for emergency
                type="hospital",
                keyword="emergency room"
            )
            
            facilities = []
            for place in places_result.get("results", [])[:3]:  # Limit to 3 nearest
                facility = {
                    "name": place.get("name", "Unknown"),
                    "address": place.get("vicinity", "Address not available"),
                    "phone": place.get("formatted_phone_number", "Call 911"),
                    "distance": self._calculate_distance(location, place.get("geometry", {}).get("location", {}))
                }
                facilities.append(facility)
            
            return facilities
            
        except Exception:
            return []
    
    def _parse_advice_list(self, advice_text: str) -> List[str]:
        """Parse advice text into a list"""
        lines = advice_text.strip().split('\n')
        advice = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or 
                        (len(line) > 0 and line[0].isdigit())):
                # Remove bullets and numbering
                clean_line = line.lstrip('-•0123456789. ').strip()
                if clean_line:
                    advice.append(clean_line)
        
        return advice if advice else [advice_text]
    
    def _parse_evidence_list(self, evidence_text: str) -> List[str]:
        """Parse evidence text into a list"""
        return self._parse_advice_list(evidence_text)  # Same parsing logic
    
    def _calculate_distance(self, loc1: Dict[str, float], loc2: Dict[str, float]) -> str:
        """Calculate approximate distance between two coordinates"""
        try:
            from math import radians, cos, sin, asin, sqrt
            
            lat1, lon1 = radians(loc1["lat"]), radians(loc1["lng"])
            lat2, lon2 = radians(loc2["lat"]), radians(loc2["lng"])
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            km = 6371 * c
            
            if km < 1:
                return f"{int(km * 1000)}m"
            else:
                return f"{km:.1f}km"
        except Exception:
            return "Distance unknown"