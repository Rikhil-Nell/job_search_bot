from pydantic import BaseModel, ConfigDict
from pydantic_ai import RunContext
import json
from typing import Optional
from asyncpg.pool import Pool

class AgentDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    user_profile: dict
    conn: Pool

async def get_jobs(
    ctx: RunContext[AgentDeps],
    title: Optional[str] = None,
    min_salary: Optional[int] = None,
    max_salary: Optional[int] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
    job_type: Optional[str] = None,
    job_category: Optional[str] = None,
    currency: Optional[str] = None,
) -> str:
    """
    Optimized dynamic job search tool that returns only job IDs and titles.
    Allows filtering by various job_posts table fields.
    """
    
    limit: int = 10
    pool = ctx.deps.pool

    # Corrected base query with the right table join for job_category -> job_role
    base_query = """
    SELECT
        jp.id,
        jp.title
    FROM job_posts jp
    LEFT JOIN city ct ON jp.city_id = ct.id AND (ct."isDeleted" = false OR ct."isDeleted" IS NULL)
    LEFT JOIN country cn ON jp.country_id = cn.id AND (cn."isDeleted" = false OR cn."isDeleted" IS NULL)
    LEFT JOIN job_role cat ON jp.category_id = cat.id AND (cat."isDeleted" = false OR cat."isDeleted" IS NULL)
    LEFT JOIN job_type jt ON jp.job_type_id = jt.id AND (jt."isDeleted" = false OR jt."isDeleted" IS NULL)
    LEFT JOIN currency curr ON jp.currency_id = curr.id AND (curr."isDeleted" = false OR curr."isDeleted" IS NULL)
    """

    # --- Refactored Query Building ---
    conditions = ["jp.\"IsAccepting\" = true"]
    params = []

    # A more robust way to add filters without manually tracking param counts
    def add_filter(condition: str, value):
        if value is not None:
            params.append(value)
            # The placeholder is determined by the final position in the params list
            conditions.append(condition.format(len(params)))

    add_filter('LOWER(jp.title) LIKE LOWER(${})', f"%{title}%" if title else None)
    add_filter('jp."MaxSalary" >= ${}', min_salary)
    add_filter('jp."MinSalary" <= ${}', max_salary)
    add_filter('LOWER(ct.name) LIKE LOWER(${})', f"%{city}%" if city else None)
    add_filter('LOWER(cn.name) LIKE LOWER(${})', f"%{country}%" if country else None)
    add_filter('LOWER(jt.name) LIKE LOWER(${})', f"%{job_type}%" if job_type else None)
    add_filter('LOWER(cat.name) LIKE LOWER(${})', f"%{job_category}%" if job_category else None)
    add_filter('LOWER(curr.name) LIKE LOWER(${})', f"%{currency}%" if currency else None)

    # Construct final query
    where_clause = " AND ".join(conditions)
    # Add the LIMIT parameter last
    params.append(limit)
    limit_param_index = len(params)
    
    final_query = f"""
    {base_query}
    WHERE {where_clause}
    ORDER BY jp.created_at DESC
    LIMIT ${limit_param_index}
    """

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(final_query, *params)
        
        jobs = [{"job_id": row['id'], "title": row['title']} for row in rows]

        result = {
            "jobs": jobs,
            "total_found": len(jobs),
            "filters_applied": {
                "title": title,
                "min_salary": min_salary,
                "max_salary": max_salary,
                "city": city,
                "country": country,
                "job_type": job_type,
                "job_category": job_category,
                "currency": currency,
                "limit": limit
            }
        }
        return json.dumps(result, default=str)

    except Exception as e:
        # Return error information for debugging
        error_result = {
            "error": str(e),
            "jobs": [],
            "total_found": 0,
            "filters_applied": {
                "title": title,
                "min_salary": min_salary,
                "max_salary": max_salary,
                "city": city,
                "country": country,
                "job_type": job_type,
                "job_category": job_category,
                "currency": currency,
                "limit": limit
            }
        }
        return json.dumps(error_result, default=str)
