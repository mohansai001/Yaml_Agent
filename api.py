from yaml_agent import YamlAgent
from vida.models.requests.Agents_requests import terraform_agent_request
from fastapi import APIRouter

router = APIRouter()

@router.post("/yaml-agent")
async def yaml_agent_call(request: terraform_agent_request):
    agent= YamlAgent.get_instance()
    session=request.session
    response = await agent.run(
        prompt=request.prompt,
        session=session
    )
    # print(vars(session))
    print(agent._session.session_id)
    return response