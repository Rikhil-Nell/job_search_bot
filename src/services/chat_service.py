from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.messages import ModelMessage
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.models.groq import GroqModel, GroqModelName, GroqModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelName, OpenAIModelSettings
from pydantic import BaseModel
from src.dependencies.tools import get_jobs
from src.schemas.user import UserProfile
from src.core.config import settings
from asyncpg.pool import Pool
import json
import logging
import logfire

# MODEL_NAME : GroqModelName = "deepseek-r1-distill-llama-70b"
# model_settings : GroqModelSettings = GroqModelSettings(temperature=0.1, top_p=0.95, groq_reasoning_format="hidden")
# model : GroqModel = GroqModel(model_name=MODEL_NAME, provider=GroqProvider(api_key=settings.groq_api_key))

MODEL_NAME : OpenAIModelName = "gpt-4o-mini"
model_settings : OpenAIModelSettings = OpenAIModelSettings(temperature=0.1, top_p=0.95)
model : OpenAIModel = OpenAIModel(model_name=MODEL_NAME, provider=OpenAIProvider(api_key=settings.openai_api_key))

logger = logging.getLogger(__name__)
logfire.configure(token=settings.logfire_write_token)
logfire.instrument_pydantic_ai()

class AgentDeps(BaseModel):
    user_profile: UserProfile
    conn: object

with open("./src/dependencies/prompt.md", "r", encoding="utf-8") as file:
    prompt = file.read()

agent = Agent(
    model=model,
    instructions=prompt,
    deps_type=AgentDeps,
    tools=[Tool(get_jobs, takes_ctx=True, max_retries=1)],
    instrument=True
)

@agent.instructions
async def get_user_details(ctx : RunContext[AgentDeps]):
    return f"""
            User Details:
                first_name= {ctx.deps.user_profile.first_name},
                last_name= {ctx.deps.user_profile.last_name},
                availability= {ctx.deps.user_profile.availability},
                bio= {ctx.deps.user_profile.bio},
                role= {ctx.deps.user_profile.role},
                city= {ctx.deps.user_profile.city},
                country= {ctx.deps.user_profile.country}
            """

message_history : list[ModelMessage] = []

async def run_chat(user_message: str, user_profile: UserProfile, conn: Pool):
    deps = AgentDeps(user_profile=user_profile, conn=conn)
    try:
        result = await agent.run(user_prompt=user_message, deps=deps)
        text = result.output
        try:
            parsed = json.loads(text)
            return {"response_type": "structured", "data": parsed}
        except json.JSONDecodeError:
            return {"response_type": "chat", "message": text}
    except Exception as e:
        logger.exception("Agent error")
        return {"response_type": "error", "message": f"Internal error: {str(e)}"}

