from schemas.medical_schemas import AgentState
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class WorkflowStateManager:
    """Centralized workflow state management for all workflow stages"""
    
    def __init__(self):
        self.CONFIDENCE_THRESHOLD = 0.75
    
    def calculate_average_confidence(self, state: AgentState) -> float:
        """Calculate average confidence from textual analysis"""
        textual_analysis = state.get("textual_analysis", [])
        if textual_analysis and isinstance(textual_analysis, list):
            confidence_scores = [
                diagnosis.get("diagnosis_confidence", 0.0) 
                for diagnosis in textual_analysis
            ]
                
        return sum(confidence_scores) / len(confidence_scores)

    
    def update_workflow_stage_and_determine_next(self, state: AgentState, completed_node: str) -> dict[str, Any]:
        """Update workflow stage and determine next endpoint for ALL stages"""
        
        # STAGE 1: Textual Analysis Complete
        if completed_node == "textual_analysis":
            state["current_workflow_stage"] = "textual_analysis_complete"
            
            # Calculate confidence if not already done
            if "average_confidence" not in state:
                state["average_confidence"] = self.calculate_average_confidence(state)
            
            avg_confidence = state.get("average_confidence", 1.0)
            
            # INITIALIZE WORKFLOW PATH IF NOT SET
            if "workflow_path" not in state:
                state["workflow_path"] = [] 
            ## Textual analysis -> skin cancer screening
            if state.get("requires_skin_cancer_screening", False):
                next_endpoint = "/patient/followup_questions"
                needs_user_input = "followup_questions"
                next_step_description = "Skin cancer screening questions needed"
                
                state["workflow_path"] = ["textual_to_skin_screening"]
            ## Textual analysis -> standard follow up 
            elif avg_confidence < self.CONFIDENCE_THRESHOLD:
                next_endpoint = "/patient/followup_questions"
                needs_user_input = "followup_questions"
                next_step_description = "Follow-up questions needed to improve accuracy"
                
                state["workflow_path"] = ["textual_to_followup", "followup_only"]
            ## Textual analysis -> overall analysis 
            else:
                next_endpoint = "/patient/overall_analysis"
                needs_user_input = None
                next_step_description = "Ready for comprehensive analysis"
            
            logger.info(f"✅ Textual analysis complete. Confidence: {avg_confidence:.2f}, Next: {next_step_description}")
            logger.info(f"🔍 Workflow path set to: {state.get('workflow_path')}")

            return {
                "current_stage": "textual_analysis_complete",
                "next_endpoint": next_endpoint,
                "needs_user_input": needs_user_input,
                "next_step_description": next_step_description,
                "workflow_complete": False,
                "show_next_button": True,
                "confidence_score": avg_confidence,
                "image_required": state.get("image_required", False)
            }
        
        #STAGE 2: Follow-up Questions Complete
        elif completed_node == "followup_interaction":
            current_path = state.get("workflow_path", [])
            followup_type = state.get("followup_type", "standard")
                        
            ## skin cancer screening -> standard follow-up
            if state.get("requires_user_input", False) and followup_type == "standard" and "textual_to_skin_screening" in current_path:
                # This happens when standard questions are ready for user input
                next_endpoint = "/patient/followup_questions"
                needs_user_input = "followup_questions"
                next_step_description = "Standard follow-up questions for skin condition analysis"
                
                # Update workflow path to reflect the transition
                state["workflow_path"] = ["textual_to_skin_screening", "skin_to_standard_followup"]
                
                logger.info(f"🔄 Standard follow-up questions ready for user input")
                
                return {
                    "current_stage": "awaiting_followup_responses",
                    "next_endpoint": next_endpoint,
                    "needs_user_input": needs_user_input,
                    "next_step_description": next_step_description,
                    "workflow_complete": False,
                    "show_next_button": True,
                    "confidence_score": state.get("average_confidence", 0.5),
                    "image_required": False,
                }

            ## skin cancer screening only
            if state.get("image_required", False):
                next_endpoint = "/patient/image_analysis"
                needs_user_input = "image_upload"
                next_step_description = "Medical image upload required for enhanced diagnosis"
                
                state["workflow_path"] = ["textual_to_skin_screening", "skin_to_image_analysis"]
            else: 
            ## standard follow-up only
                logger.info("🔄 Standard follow-up analysis complete - no image required")
                next_endpoint = "/patient/overall_analysis"
                needs_user_input = None
                next_step_description = "Ready for comprehensive analysis with follow-up data"
                
            return {
                "current_stage": "followup_analysis_complete",
                "next_endpoint": next_endpoint,
                "needs_user_input": needs_user_input,
                "next_step_description": next_step_description,
                "workflow_complete": False,
                "show_next_button": True,
                "confidence_score": state.get("average_confidence", 0.5),
                "image_required": state.get("image_required", False)
            }
        
        #STAGE 3: Image Analysis Complete
        elif completed_node == "image_analysis":
            #After image analysis, always go to overall analysis
            next_endpoint = "/patient/overall_analysis"
            needs_user_input = None
            next_step_description = "Ready for comprehensive analysis with image data"
            
            #Check if we have image analysis results
            image_analysis = state.get("skin_lesion_analysis", {})
            has_image_results = bool(image_analysis.get("image_diagnosis"))
            
            logger.info(f"✅ Image analysis complete. Has results: {has_image_results}, Next: {next_step_description}")
            
            return {
                "current_stage": "image_analysis_complete",
                "next_endpoint": next_endpoint,
                "needs_user_input": needs_user_input,
                "next_step_description": next_step_description,
                "workflow_complete": False,
                "show_next_button": True,
                "confidence_score": state.get("average_confidence", 0.7),
                "image_required": False,  # Image already processed
                "image_results_available": has_image_results
            }
        
        #STAGE 4: Overall Analysis Complete
        elif completed_node == "overall_analysis":
            #After overall analysis, go to healthcare recommendations
            next_endpoint = "/patient/medical_report"
            needs_user_input = None
            next_step_description = "Generating comprehensive medical report"
            
            #Get final confidence from overall analysis
            overall_analysis = state.get("overall_analysis", {})
            final_confidence = overall_analysis.get("final_confidence", 0.0)
            final_diagnosis = overall_analysis.get("final_diagnosis", "Analysis complete")
            
            logger.info(f"✅ Overall analysis complete. Final diagnosis: {final_diagnosis}, Confidence: {final_confidence:.2f}")
            logger.info(f"🔄 Proceeding directly to medical report generation")
            
            return {
                "current_stage": "overall_analysis_complete",
                "next_endpoint": next_endpoint,
                "needs_user_input": needs_user_input,
                "next_step_description": next_step_description,
                "workflow_complete": False,
                "show_next_button": True,
                "confidence_score": final_confidence,
                "final_diagnosis": final_diagnosis,
                "analysis_complete": True
            }
        
        #Medical Report Complete (Final Stage)
        elif completed_node == "generate_report" or completed_node == "medical_report":
            #Workflow is now complete
            next_endpoint = None
            needs_user_input = None
            next_step_description = "Medical analysis workflow complete"
            
            #Check if report was generated
            medical_report = state.get("medical_report", "")
            has_report = bool(medical_report and len(medical_report.strip()) > 0)
            
            logger.info(f"✅ Medical report generation complete. Report available: {has_report}")
            
            return {
                "current_stage": "workflow_complete",
                "next_endpoint": next_endpoint,
                "needs_user_input": needs_user_input,
                "next_step_description": next_step_description,
                "workflow_complete": True,
                "show_next_button": False,  # No more steps
                "medical_report_available": has_report,
                "workflow_summary": self._generate_workflow_summary(state)
            }
        
        #FALLBACK: Unknown completed node
        else:
            logger.warning(f"⚠️ Unknown completed node: {completed_node}")
            return {
                "current_stage": state.get("current_workflow_stage", "unknown"),
                "next_endpoint": None,
                "needs_user_input": None,
                "next_step_description": f"Unknown stage: {completed_node}",
                "workflow_complete": False,
                "show_next_button": False,
                "error": f"Unknown workflow stage: {completed_node}"
            }
    
    def _generate_workflow_summary(self, state: AgentState) -> Dict[str, Any]:
        """Generate a summary of the completed workflow"""
        
        workflow_path = state.get("workflow_path", [])
        
        summary = {
            "workflow_type": self._determine_workflow_type(workflow_path),
            "stages_completed": [],
            "total_stages": 0,
            "data_sources_used": []
        }
        
        # Track completed stages
        if state.get("textual_analysis"):
            summary["stages_completed"].append("textual_analysis")
            summary["data_sources_used"].append("symptoms")
            
        if state.get("followup_diagnosis"):
            summary["stages_completed"].append("followup_analysis")
            summary["data_sources_used"].append("followup_questions")
            
        if state.get("skin_lesion_analysis"):
            summary["stages_completed"].append("image_analysis")
            summary["data_sources_used"].append("medical_image")
            
        if state.get("overall_analysis"):
            summary["stages_completed"].append("overall_analysis")
            
        if state.get("healthcare_recommendation"):
            summary["stages_completed"].append("healthcare_recommendations")
            
        if state.get("medical_report"):
            summary["stages_completed"].append("medical_report")
        
        summary["total_stages"] = len(summary["stages_completed"])
        
        return summary
    
    def _determine_workflow_type(self, workflow_path: list) -> str:
        """Determine the type of workflow that was completed"""
        if not workflow_path:
            return "basic_analysis"
        
        if workflow_path == ["textual_only"]:
            return "textual_analysis_only"
        elif workflow_path == ["textual_to_image"]:
            return "textual_and_image_analysis"
        elif "followup_only" in workflow_path:
            return "enhanced_textual_analysis"
        elif "followup_to_image" in workflow_path:
            return "comprehensive_analysis"
        else:
            return "custom_workflow"

#Global instance
workflow_state_manager = WorkflowStateManager()