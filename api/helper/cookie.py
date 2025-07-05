from fastapi.responses import JSONResponse

content = { "response": "Success." }

def create_cookie(sess_id: str):
    response = JSONResponse(content=content)
    response.set_cookie(
        key="session-id",
        value=sess_id,
        httponly=True,  
        samesite="Lax", 
    )
    return response

def destroy_cookie():
    response = JSONResponse(content=content)
    response.delete_cookie(key="session-id")
    return response