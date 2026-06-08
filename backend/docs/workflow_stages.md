# Workflow Stage Reference Guide

## Complete List of All Workflow Stages

### Stage 1: LLM Diagnosis
- `textual_analysis` - Node processing symptoms
- `textual_analysis_complete` - Analysis finished

### Stage 2: Follow-up Interaction  
- `generating_followup_questions` - Creating questions
- `awaiting_followup_responses` - Waiting for user input
- `processing_followup_responses` - Processing answers
- `followup_analysis_complete` - Follow-up finished

### Stage 3: Image Analysis
- `analyzing_image` - Processing medical image
- `image_analysis_complete` - Image analysis finished
- `image_analysis_error` - Image analysis failed

### Stage 4: Overall Analysis
- `performing_overall_analysis` - Comprehensive analysis
- `overall_analysis_complete` - Overall analysis finished
- `overall_analysis_error` - Overall analysis failed

### Stage 5: Healthcare Recommendations
- `healthcare_recommendation` - Finding recommendations
- `healthcare_recommendation_complete` - Recommendations finished
- `healthcare_recommendation_error` - Recommendations failed

### Stage 6: Medical Report
- `report_generation` - Generating report
- `report_complete` - Report finished
- `report_generation_error` - Report generation failed

## Frontend Page Mapping

Each stage maps to a specific frontend page:
- `textual_analysis*` → DiagnosisFormPage
- `*followup*` → FollowUpQuestionsPage  
- `*image*` → ImageAnalysisPage
- `*overall_analysis*` → OverallAnalysisPage
- `*healthcare_recommendation*` → RecommendationsPage
- `*report*` → FinalReportPage