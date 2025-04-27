from langchain_core.messages import HumanMessage, AIMessage
import traceback
from api.services.agent_service import get_agent
from api.connection.ws_connection_manager import manager
from fastapi import WebSocket, WebSocketDisconnect

# Active sessions cache for storing conversation state
active_sessions = {}


async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Handle WebSocket connections for individual user chat sessions."""
    agent = get_agent() # Get the agent instance
    session_id = client_id # Use client_id as the session identifier

    await manager.connect(websocket, client_id)
    print(f"Client connected: {client_id}") # Log connection

    try:
        # Send a welcome message or initial state specific to this client
        await manager.send_personal_message(f"Welcome Client {client_id}! Session started.", client_id)

        while True:
            data = await websocket.receive_text()
            print(f"Received message from {client_id}: {data}") # Log received data

            # Prepare messages for the agent
            user_message = HumanMessage(content=data)
            
            # Get existing messages or start new conversation for this client_id
            if session_id in active_sessions:
                messages = active_sessions[session_id]
                messages.append(user_message)
            else:
                messages = [user_message]
                active_sessions[session_id] = messages

            # Create state for agent
            state = {"messages": messages}
            
            # Set up configuration for the agent call
            config = {"configurable": {"thread_id": session_id}}
            
            response_message = "" # Initialize response message

            # Run agent and get the streaming results
            async for event in agent.astream_events(state, config, version="v1"):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        # Send content chunk to the client immediately
                        await manager.send_personal_message(content, client_id)
                        response_message += content # Accumulate the full response
                elif kind == "on_tool_start":
                    print(f"Tool started: {event['name']} with input {event['data'].get('input')}")
                elif kind == "on_tool_end":
                    print(f"Tool finished: {event['name']} with output {event['data'].get('output')}")


            # After streaming is complete, update the session history with the full messages
            # Fetch the final state which should contain the full history
            # Note: Depending on your specific agent setup, you might need to adjust how final state is retrieved
            # For now, we manually add the AI message based on the accumulated streamed response
            if response_message:
                 # Add the AI's final response to the history
                 active_sessions[session_id].append(AIMessage(content=response_message))
            
            print(f"Sent response to {client_id}: {response_message}") # Log sent response


    except WebSocketDisconnect:
        print(f"Client disconnected: {client_id}") # Log disconnection
        # Clean up resources for this session
        if session_id in active_sessions:
            del active_sessions[session_id]
            print(f"Cleared session data for {client_id}")
        manager.disconnect(client_id)
        # Optionally broadcast leave message if needed
        # await manager.broadcast(f"Client {client_id} left.")

    except Exception as e:
        error_message = f"An error occurred for client {client_id}: {str(e)}"
        print(error_message)
        traceback.print_exc() # Print detailed traceback to server logs
        manager.disconnect(client_id)
        # Clean up session data on error as well
        if session_id in active_sessions:
             del active_sessions[session_id]
             print(f"Cleared session data for {client_id} due to error.")
        # Optionally try sending an error message to the client if the connection is still viable
        try:
            await websocket.send_text(f"System Error: {str(e)}. Disconnecting.")
        except Exception:
            pass # Ignore error if sending fails (connection likely already closed)

