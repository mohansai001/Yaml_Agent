from yaml_agent import YamlAgent
from vida.models.requests.Agents_requests import terraform_agent_request
from fastapi import APIRouter
from vida.utils.preprocess import try_parse_json

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
    # print(agent._session.session_id)
    output, is_json = try_parse_json(response.text)
    return {
        "raw": response,
        "is_json": is_json,
        "output": output
    }