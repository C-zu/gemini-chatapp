from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.schemas import ChatRequest, ImageChatRequest, CSVAnalysisRequest, CSVAnalysisResponse, PlotData
from services.chat_service import ai_service
import json
import pandas as pd
import io

router = APIRouter()

@router.post("/ai/chat")
async def chat_with_ai(request: ChatRequest):
    """Chat with AI - text streaming"""
    try:
        def generate():
            # Call AI service
            response_stream = ai_service.generate_text_response(
                request.user_input, 
                request.chat_history
            )
            
            for chunk in response_stream:
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
                elif hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
                else:
                    yield str(chunk)
        
        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/chat/image")
async def chat_with_image(request: ImageChatRequest):
    """Chat with AI including image (streaming)"""
    try:
        def generate():
            # Call AI service to get stream response
            response_stream = ai_service.generate_image_response(
                request.user_input,
                request.image_data,
                request.chat_history
            )
            
            for chunk in response_stream:
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
                elif hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
                else:
                    yield str(chunk)

        # Stream results to client
        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/chat/csv")
async def chat_with_csv(request: CSVAnalysisRequest):
    """Chat with AI for CSV data analysis with plotting support"""
    try:
        if not request.enhanced_query:
            raise HTTPException(status_code=400, detail="Enhanced query is required")
        
        df = None
        if request.csv_data:
            try:
                if isinstance(request.csv_data, str) and request.csv_data.strip():
                    df = pd.read_csv(io.StringIO(request.csv_data))
                elif isinstance(request.csv_data, list):
                    df = pd.DataFrame(request.csv_data)
                elif isinstance(request.csv_data, dict):
                    df = pd.DataFrame(request.csv_data)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to parse CSV data: {str(e)}")
        
        # Generate response with AI service
        response_text = ai_service.generate_csv_response(
            enhanced_query=request.enhanced_query,
            dataframe=df,
            session_id=request.session_id
        )
        
        # Get plots from AI service
        plots = ai_service.get_plots(request.session_id)
        print(f"📊 Retrieved {len(plots)} plots from AI service")
        
        # Convert plots to serializable format - FIX SERIALIZATION ERROR
        serializable_plots = []
        for i, plot in enumerate(plots):
            try:
                if hasattr(plot, 'to_json'):
                    # Use to_json() instead of to_dict() to avoid serialization errors
                    plot_json = plot.to_json()
                    plot_dict = json.loads(plot_json)
                    
                    serializable_plots.append({
                        "data": plot_dict.get("data", []),
                        "layout": plot_dict.get("layout", {})
                    })
                    print(f"✅ Successfully serialized plot {i+1}")
                else:
                    print(f"⚠️ Plot {i+1} is not a plotly figure")
            except Exception as plot_error:
                print(f"❌ Error serializing plot {i+1}: {plot_error}")
                # Skip error plots to prevent API crash
        
        # Clear plots after sending
        ai_service.clear_plots(request.session_id)
        
        return {
            "content": response_text,
            "plots": serializable_plots
        }
        
    except Exception as e:
        print(f"❌ Error in CSV chat: {str(e)}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))