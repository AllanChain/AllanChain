import os
import tomllib
from datetime import datetime, timedelta
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader

PROJ_ROOT = Path(__file__).parent
config = tomllib.load((PROJ_ROOT / "pyproject.toml").open("rb"))["tool"]["stats"]
env = Environment(
    loader=FileSystemLoader(PROJ_ROOT / "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
)


def gql(query_name: str, **kwargs):
    token = os.environ.get("GITHUB_TOKEN")
    query_file = PROJ_ROOT / "queries" / f"{query_name}.gql"
    if not query_file.exists():
        raise ValueError(f"Query {query_file} does not exist")
    query = query_file.open().read()
    response = requests.post(
        url="https://api.github.com/graphql",
        json={"query": query, "variables": kwargs},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    if "data" not in data:
        raise RuntimeError(f"GraphQL errors: {data}")
    return data["data"]


def concat_list_with_and(items: list[str]) -> str:
    if len(items) == 0:
        return ""
    elif len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return " and ".join(items)
    else:
        return ", ".join(items[:-1]) + ", and " + items[-1]


def name_and_time(item) -> str:
    if item["hours"] > 0:
        time = f"{item['hours']}h {item['minutes']}m"
    else:
        time = f"{item['minutes']}m"
    return f"**{item['name']}** ({time})"


def language_stats():
    print("  Fetching user languages")
    languages = {}
    user_data = gql("user-language")["viewer"]
    repos = [
        repo
        for repo in user_data["repositories"]["nodes"]
        if repo["nameWithOwner"] not in config["excluded_repos"]
    ]
    for repo_name in config["included_repos"]:
        print("  Fetching repo languages in", repo_name)
        owner, name = repo_name.split("/")
        repos.append(gql("repo-language", owner=owner, name=name)["repository"])

    for repo in repos:
        for repo_lang in repo["languages"]["edges"]:
            language_name = repo_lang["node"]["name"]
            if language_name in config["excluded_languages"]:
                continue
            if language_name not in languages:
                languages[language_name] = {
                    "size": repo_lang["size"],
                    "color": repo_lang["node"]["color"],
                }
            else:
                languages[language_name]["size"] += repo_lang["size"]
    total_size = sum(language["size"] for language in languages.values())
    sorted_languages = sorted(
        ({"name": name, **language} for name, language in languages.items()),
        key=lambda language: language["size"],
        reverse=True,
    )
    template = env.get_template("languages.svg.jinja")
    rendered_text = template.render(
        languages=sorted_languages[:8],
        width=460,
        total_size=total_size,
    )
    print("  Writing languages.svg")
    with open(PROJ_ROOT / "languages.svg", "w", encoding="utf-8") as f:
        f.write(rendered_text)


def contribution_stats():
    user_data = gql("user")["viewer"]
    join_date = datetime.fromisoformat(user_data["createdAt"])
    username = user_data["login"]

    contributions = []
    date = datetime.now(tz=join_date.tzinfo)
    while date > join_date:
        date -= timedelta(days=365)
        print("  Fetching contributions in year", date)
        data = gql("contributions", date=date.isoformat())
        contributions.append(data["viewer"]["contributionsCollection"])

    commit_count = sum(
        contribution["totalCommitContributions"] for contribution in contributions
    )
    contributed_repos: set[str] = set(
        repo["pullRequest"]["repository"]["nameWithOwner"]
        for contribution in contributions
        for repo in contribution["pullRequestContributions"]["nodes"]
        if not repo["pullRequest"]["repository"]["nameWithOwner"].startswith(username)
    )

    print("  Fetching Wakatime stats")
    response = requests.get(
        url="https://wakatime.com/api/v1/users/current/stats",
        params={"api_key": os.environ.get("WAKATIME_TOKEN")},
    )
    wakatime_data = response.json()["data"]

    template = env.get_template("README.md.jinja")
    rendered_text = template.render(
        join_date=join_date.strftime("%d %B %Y"),
        contributed_repos=len(contributed_repos),
        commit_count=commit_count,
        wakatime=wakatime_data,
        waka_editors=concat_list_with_and(
            [name_and_time(editor) for editor in wakatime_data["editors"][:3]]
        ),
        waka_languages=concat_list_with_and(
            [name_and_time(language) for language in wakatime_data["languages"][:3]]
        ),
    )
    print("  Writing README.md")
    with open(PROJ_ROOT / "README.md", "w", encoding="utf-8") as f:
        f.write(rendered_text)


if __name__ == "__main__":
    print("Generating language stats")
    language_stats()
    print("Generating contribution stats")
    contribution_stats()
