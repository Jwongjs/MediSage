from adapters.local_model_adapter import LocalModelAdapter
from typing import Dict, Any, Optional, List
import re

##PARSING LOGIC FROM LLMDiagnosisNode for reference
    # # --- Extract Each Diagnosis Block ---
    # diagnosis_pattern = re.compile(
    #     r"-\s*Diagnosis:\s*(.*?)\s*"
    #     r"-\s*Reasoning:\s*(.*?)\s*"
    #     r"-\s*Severity:\s*(.*?)(?=\s*-\s*Diagnosis|\s*$)"
    #     r"-\s*Confidence:\s*([0-9.]+)\s*",

    #     re.IGNORECASE | re.DOTALL
    # )

    # for match in diagnosis_pattern.finditer(raw_response):
    #     diagnosis, reasoning, confidence, severity = match.groups()
    #     result: TextualSymptomAnalysisResult = {
    #         "text_diagnosis": diagnosis.strip(),
    #         "reasoning": reasoning.strip(),
    #         "diagnosis_confidence": float(confidence.strip()),
    #         "severity": severity.strip().lower()
    #     }
    #     results.append(result)

class OverallAnalysisNode:
    def __init__(self, adapter: LocalModelAdapter):
        self.adapter = adapter
    
    async def __call__(self, state):
        return await self.perform_overall_analysis(state)
    
    async def perform_overall_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis using all available data.
        Can handle: text-only, text+image, or any combination of analyses.
        """
        
        try:
            # Gather all available analysis data
            
            #User Input of their symptoms from LLMDiagnosisNode, 
            userInput_symptoms = state.get("userInput_symptoms", "")
            userInput_skin_symptoms = state.get("userInput_skin_symptoms", "")
            followup_qna = state.get("followup_qna", {})
            
            #Text or Image Diagnosis State Results 
            textual_analysis = self._get_primary_textual_analysis(state)
            image_analysis = state.get("skin_lesion_analysis", {})
            
            
            # Determine analysis type and generate comprehensive assessment
            if image_analysis.get('image_diagnosis') and "Error" not in image_analysis.get('image_diagnosis', ""):
                # Combined text + image analysis
                overall_assessment = await self._analyze_text_and_image(textual_analysis, image_analysis)
                analysis_type = "text_and_image"
            else:
                userInput_symptoms = state.get("userInput_symptoms", "")
                # Text-only analysis enhancement
                overall_assessment = await self._enhance_textual_analysis(textual_analysis, userInput_symptoms)
                analysis_type = "text_only_enhanced"
            
            # Parse the overall assessment into structured data
            enhanced_analysis = self._parse_overall_assessment(
                overall_assessment, 
                textual_analysis, 
                image_analysis,
                analysis_type
            )
            
            # Store overall analysis results
            state["overall_analysis"] = {
                "analysis_type": analysis_type,
                "assessment_text": overall_assessment,
                "final_diagnosis": enhanced_analysis["diagnosis"],
                "final_confidence": enhanced_analysis["confidence"],
                "final_severity": enhanced_analysis["severity"],
                "integration_notes": enhanced_analysis["integration_notes"],
                "recommendation_guidance": enhanced_analysis["recommendation_guidance"],
                "key_findings": enhanced_analysis["key_findings"]
            }
            
            state["current_workflow_stage"] = "healthcare_recommendation"
            
        except Exception as e:
            # If overall analysis fails, create fallback analysis
            textual_analysis = self._get_primary_textual_analysis(state)
            state["overall_analysis"] = {
                "analysis_type": "fallback",
                "assessment_text": f"Overall analysis failed: {str(e)}",
                "final_diagnosis": textual_analysis.get("text_diagnosis", "Unknown") if textual_analysis else "Unknown",
                "final_confidence": textual_analysis.get("diagnosis_confidence", 0.0) if textual_analysis else 0.0,
                "final_severity": textual_analysis.get("severity", "unknown") if textual_analysis else "unknown",
                "integration_notes": "Failed to perform comprehensive analysis",
                "recommendation_guidance": "proceed_with_caution",
                "key_findings": ["Analysis incomplete due to technical error"]
            }
            state["current_workflow_stage"] = "healthcare_recommendation"
        
        return state
    
    def _get_primary_textual_analysis(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the best available textual analysis (follow-up takes precedence)"""
        if state.get("followup_analysis"):
            return state["followup_analysis"]
        return state.get("textual_analysis")
    
    async def _analyze_text_and_image(self, textual_analysis: Dict, image_analysis: Dict) -> str:
        """Comprehensive analysis combining text and image data"""
        
        # Use the existing combined analysis method from the adapter
        return await self.adapter.analyze_combined_data(
            textual_analysis=textual_analysis,
            image_analysis=image_analysis
        )
    
    async def _enhance_textual_analysis(self, textual_analysis: Dict, userInput_symptoms) -> str:
        """Enhance text-only analysis with additional insights"""
        
        diagnosis = textual_analysis.get("text_diagnosis", "Unknown")
        confidence = textual_analysis.get("diagnosis_confidence", 0.0)
        
        
        prompt = f"""
        Perform an enhanced analysis of this medical case:
        
        Original Symptoms: {userInput_symptoms}
        CURRENT DIAGNOSIS: {diagnosis}
        CONFIDENCE: {confidence:.2f}
        
        Provide detailed analysis including:
        1. Detailed medical reasoning and justification
        2. Severity assessment (mild/moderate/severe/critical)
        3. Specialist recommendation type
        4. Risk factors and red flags
        5. Enhanced confidence assessment
        6. Treatment guidance
        """
        
        return await self.adapter.analyze_combined_data(prompt)
    
    def _parse_overall_assessment(self, assessment_text: str, textual_analysis: Dict, image_analysis: Dict, analysis_type: str) -> Dict[str, Any]:
        """Parse the LLM's overall assessment into structured data"""
        
        # Extract final diagnosis
        diagnosis_patterns = [
            r"(?:final|enhanced|confirmed|refined)?\s*diagnosis[:\s]+([^\n\.]+)",
            r"primary\s+diagnosis[:\s]+([^\n\.]+)",
            r"most\s+likely\s+diagnosis[:\s]+([^\n\.]+)"
        ]
        
        final_diagnosis = textual_analysis.get("text_diagnosis", "Unknown")
        for pattern in diagnosis_patterns:
            match = re.search(pattern, assessment_text, re.IGNORECASE)
            if match:
                final_diagnosis = match.group(1).strip()
                break
        
        # Extract confidence level
        confidence_match = re.search(r"confidence[:\s]+([0-9]*\.?[0-9]+)", assessment_text, re.IGNORECASE)
        if confidence_match:
            final_confidence = float(confidence_match.group(1))
            if final_confidence > 1:
                final_confidence = final_confidence / 100
        else:
            # Calculate enhanced confidence based on analysis type
            text_conf = textual_analysis.get("diagnosis_confidence", 0.0)
            if analysis_type == "text_and_image":
                image_conf = self._extract_max_image_confidence(image_analysis)
                # Weight combined analysis higher
                final_confidence = min(1.0, (text_conf * 0.6) + (image_conf * 0.4) + 0.1)
            else:
                # Slight boost for enhanced text analysis
                final_confidence = min(1.0, text_conf + 0.05)
        
        # Extract severity
        severity_match = re.search(r"severity[:\s]+(\w+)", assessment_text, re.IGNORECASE)
        final_severity = severity_match.group(1).strip() if severity_match else textual_analysis.get("severity", "unknown")
        
        # Extract integration notes
        integration_notes = self._extract_integration_notes(assessment_text, analysis_type)
        
        # Extract recommendation guidance
        recommendation_guidance = self._extract_recommendation_guidance(assessment_text)
        
        # Extract key findings
        key_findings = self._extract_key_findings(assessment_text)
        
        return {
            "diagnosis": final_diagnosis,
            "confidence": final_confidence,
            "severity": final_severity,
            "integration_notes": integration_notes,
            "recommendation_guidance": recommendation_guidance,
            "key_findings": key_findings
        }
    
    def _extract_max_image_confidence(self, image_analysis: Dict) -> float:
        """Extract the highest confidence score from image analysis"""
        confidence_scores = image_analysis.get("confidence_score", {})
        if confidence_scores:
            return max(confidence_scores.values()) / 100
        return 0.0
    
    def _extract_integration_notes(self, assessment_text: str, analysis_type: str) -> str:
        """Extract notes about the analysis process"""
        
        if analysis_type == "text_and_image":
            # Look for integration-specific notes
            if "discrepan" in assessment_text.lower():
                return "Discrepancies found between textual and image analyses"
            elif "consistent" in assessment_text.lower() or "agree" in assessment_text.lower():
                return "Textual and image analyses are consistent"
            elif "support" in assessment_text.lower() or "confirm" in assessment_text.lower():
                return "Image analysis supports textual diagnosis"
            else:
                return "Combined textual and image analysis performed"
        else:
            # Text-only enhancement notes
            if "enhanced" in assessment_text.lower():
                return "Enhanced textual analysis completed"
            elif "refined" in assessment_text.lower():
                return "Diagnosis refined through comprehensive review"
            else:
                return "Comprehensive textual analysis performed"
    
    def _extract_recommendation_guidance(self, assessment_text: str) -> str:
        """Extract guidance for healthcare recommendations"""
        
        # Check for urgency indicators
        urgency_keywords = ["urgent", "immediate", "emergency", "critical", "seek medical attention"]
        if any(keyword in assessment_text.lower() for keyword in urgency_keywords):
            return "urgent_care_recommended"
        
        # Check for specialist recommendations
        specialist_keywords = ["specialist", "referral", "dermatologist", "cardiologist", "oncologist"]
        if any(keyword in assessment_text.lower() for keyword in specialist_keywords):
            return "specialist_consultation_recommended"
        
        # Check for monitoring recommendations
        monitor_keywords = ["monitor", "follow", "watch", "observe", "track"]
        if any(keyword in assessment_text.lower() for keyword in monitor_keywords):
            return "monitoring_recommended"
        
        # Check for self-care indicators
        selfcare_keywords = ["self-care", "home treatment", "conservative management", "lifestyle"]
        if any(keyword in assessment_text.lower() for keyword in selfcare_keywords):
            return "self_care_appropriate"
        
        return "standard_care_recommended"
    
    def _extract_key_findings(self, assessment_text: str) -> List[str]:
        """Extract key findings from the assessment"""
        
        key_findings = []
        
        # Look for bullet points or numbered lists
        lines = assessment_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or 
                        (len(line) > 0 and line[0].isdigit() and '.' in line[:3])):
                clean_finding = line.lstrip('-•0123456789. ').strip()
                if len(clean_finding) > 10:  # Filter out very short findings
                    key_findings.append(clean_finding)
        
        # If no structured findings found, extract sentences with key medical terms
        if not key_findings:
            medical_keywords = ["diagnosis", "symptom", "risk", "treatment", "prognosis", "finding"]
            sentences = assessment_text.split('.')
            for sentence in sentences:
                sentence = sentence.strip()
                if any(keyword in sentence.lower() for keyword in medical_keywords) and len(sentence) > 20:
                    key_findings.append(sentence)
        
        return key_findings[:5]  # Limit to 5 key findings