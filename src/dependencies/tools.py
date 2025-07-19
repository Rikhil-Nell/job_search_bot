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

    Parameters:
    - title: Search in job title
    - min_salary: Minimum salary filter
    - max_salary: Maximum salary filter
    - city: Filter by city name
    - country: Filter by country name
    - job_type: Filter by job type (e.g., "Full-time", "Part-time", "Contract")
    - job_category: Filter by job category
    - currency: Filter by currency name
    """
    
    limit: int = 10
    conn = ctx.deps.conn

    # Optimized base query to select only ID and title.
    # Joins are kept for filtering purposes.
    base_query = """
    SELECT
        jp.id,
        jp.title
    FROM job_posts jp
    LEFT JOIN city ct ON jp.city_id = ct.id AND (ct."isDeleted" = false OR ct."isDeleted" IS NULL)
    LEFT JOIN country cn ON jp.country_id = cn.id AND (cn."isDeleted" = false OR cn."isDeleted" IS NULL)
    LEFT JOIN job_category cat ON jp.category_id = cat.id AND (cat."isDeleted" = false OR cat."isDeleted" IS NULL)
    LEFT JOIN job_type jt ON jp.job_type_id = jt.id AND (jt."isDeleted" = false OR jt."isDeleted" IS NULL)
    LEFT JOIN currency curr ON jp.currency_id = curr.id AND (curr."isDeleted" = false OR curr."isDeleted" IS NULL)
    """

    # Build dynamic WHERE conditions
    conditions = ["jp.\"IsAccepting\" = true"]  # Only show jobs that are accepting applications
    params = []
    param_count = 1

    # Add filters based on provided parameters
    if title:
        conditions.append(f"LOWER(jp.title) LIKE LOWER(${param_count})")
        params.append(f"%{title}%")
        param_count += 1

    if min_salary is not None:
        conditions.append(f"jp.\"MaxSalary\" >= ${param_count}")
        params.append(min_salary)
        param_count += 1

    if max_salary is not None:
        conditions.append(f"jp.\"MinSalary\" <= ${param_count}")
        params.append(max_salary)
        param_count += 1

    if city:
        conditions.append(f"LOWER(ct.name) LIKE LOWER(${param_count})")
        params.append(f"%{city}%")
        param_count += 1

    if country:
        conditions.append(f"LOWER(cn.name) LIKE LOWER(${param_count})")
        params.append(f"%{country}%")
        param_count += 1

    if job_type:
        conditions.append(f"LOWER(jt.name) LIKE LOWER(${param_count})")
        params.append(f"%{job_type}%")
        param_count += 1

    if job_category:
        conditions.append(f"LOWER(cat.name) LIKE LOWER(${param_count})")
        params.append(f"%{job_category}%")
        param_count += 1

    if currency:
        conditions.append(f"LOWER(curr.name) LIKE LOWER(${param_count})")
        params.append(f"%{currency}%")
        param_count += 1

    # Construct final query
    where_clause = " AND ".join(conditions)
    final_query = f"""
    {base_query}
    WHERE {where_clause}
    ORDER BY jp.created_at DESC
    LIMIT ${param_count}
    """

    params.append(limit)

    try:
        # Execute query
        rows = await conn.fetch(final_query, *params)

        # Convert rows to a list of simplified job dictionaries
        jobs = []
        for row in rows:
            job = {
                "job_id": row['id'],
                "title": row['title']
            }
            jobs.append(job)

        # Build result with metadata
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
            },
            "query_info": {
                "conditions_used": len(conditions),
                "showing_accepting_jobs_only": True
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

# Alternative simplified version for basic searches
async def search_jobs_simple(
    ctx: RunContext[AgentDeps],
    search_term: Optional[str] = None,
    location: Optional[str] = None,
    salary_range: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Simplified job search for natural language queries.
    
    Parameters:
    - search_term: Search in job title and description
    - location: Search in city or country 
    - salary_range: Format like "50000-80000" or "50000+" or "80000-"
    - limit: Maximum results
    """
    conn = ctx.deps.conn
    
    # Parse salary range
    min_sal, max_sal = None, None
    if salary_range:
        if '-' in salary_range:
            parts = salary_range.split('-')
            if parts[0]: min_sal = int(parts[0])
            if len(parts) > 1 and parts[1]: max_sal = int(parts[1])
        elif salary_range.endswith('+'):
            min_sal = int(salary_range[:-1])
        elif salary_range.isdigit():
            min_sal = int(salary_range)
    
    # Use the main function
    return await get_jobs(
        ctx,
        title=search_term,
        min_salary=min_sal,
        max_salary=max_sal,
        city=location,
        country=location,  # Search both city and country for location
        limit=limit
    )